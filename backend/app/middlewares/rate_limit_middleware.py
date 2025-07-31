"""
API限流中间件
防止API滥用和DDoS攻击
"""
import time
import json
import redis
from typing import Callable, Dict, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_logger

logger = get_logger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """API限流中间件"""
    
    def __init__(
        self,
        app,
        redis_url: str = "redis://localhost:6379/0",
        default_rate_limit: str = "100/hour",
        rate_limit_rules: Dict[str, str] = None,
        ip_whitelist: list = None,
        ip_blacklist: list = None,
        enable_adaptive_limiting: bool = True
    ):
        super().__init__(app)
        
        # Redis连接
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()  # 测试连接
        except Exception as e:
            logger.error(f"Redis connection failed: {str(e)}")
            self.redis_client = None
        
        # 限流配置
        self.default_rate_limit = self._parse_rate_limit(default_rate_limit)
        self.rate_limit_rules = {}
        
        # 解析限流规则
        if rate_limit_rules:
            for pattern, limit in rate_limit_rules.items():
                self.rate_limit_rules[pattern] = self._parse_rate_limit(limit)
        
        # IP白名单和黑名单
        self.ip_whitelist = set(ip_whitelist or [])
        self.ip_blacklist = set(ip_blacklist or [])
        
        # 自适应限流
        self.enable_adaptive_limiting = enable_adaptive_limiting
        
        # 内存存储（Redis不可用时的备选方案）
        self.memory_store = {}
        
        # 可疑行为检测
        self.suspicious_patterns = {
            "high_frequency": {"threshold": 10, "window": 60},  # 1分钟内超过10次请求
            "error_rate": {"threshold": 0.5, "window": 300},    # 5分钟内错误率超过50%
            "path_scanning": {"threshold": 20, "window": 600}   # 10分钟内访问超过20个不同路径
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self._get_client_ip(request)
        
        # 检查IP黑名单
        if client_ip in self.ip_blacklist:
            logger.warning(f"Blocked request from blacklisted IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Access denied"}
            )
        
        # 检查IP白名单
        if client_ip in self.ip_whitelist:
            return await call_next(request)
        
        # 检查限流
        rate_limit_result = await self._check_rate_limit(request, client_ip)
        if not rate_limit_result["allowed"]:
            logger.warning(
                f"Rate limit exceeded - IP: {client_ip} - "
                f"Path: {request.url.path} - "
                f"Limit: {rate_limit_result['limit']} - "
                f"Remaining: {rate_limit_result['remaining']}"
            )
            
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": rate_limit_result["retry_after"]
                }
            )
            response.headers["Retry-After"] = str(rate_limit_result["retry_after"])
            response.headers["X-RateLimit-Limit"] = str(rate_limit_result["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_limit_result["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_limit_result["reset_time"])
            return response
        
        # 检查可疑行为
        await self._check_suspicious_behavior(request, client_ip)
        
        # 处理请求
        start_time = time.time()
        response = await call_next(request)
        response_time = time.time() - start_time
        
        # 记录请求信息
        await self._record_request(request, client_ip, response.status_code, response_time)
        
        # 添加限流信息到响应头
        response.headers["X-RateLimit-Limit"] = str(rate_limit_result["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_limit_result["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_limit_result["reset_time"])
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _parse_rate_limit(self, rate_limit_str: str) -> Dict[str, int]:
        """解析限流字符串，如 '100/hour' -> {'requests': 100, 'window': 3600}"""
        parts = rate_limit_str.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid rate limit format: {rate_limit_str}")
        
        requests = int(parts[0])
        period = parts[1].lower()
        
        period_seconds = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 86400
        }
        
        if period not in period_seconds:
            raise ValueError(f"Invalid period: {period}")
        
        return {
            "requests": requests,
            "window": period_seconds[period]
        }
    
    def _get_rate_limit_for_path(self, path: str) -> Dict[str, int]:
        """获取路径对应的限流配置"""
        # 检查特定路径规则
        for pattern, limit in self.rate_limit_rules.items():
            if pattern in path:
                return limit
        
        # 返回默认限流配置
        return self.default_rate_limit
    
    async def _check_rate_limit(self, request: Request, client_ip: str) -> Dict:
        """检查限流"""
        path = request.url.path
        method = request.method
        
        # 获取限流配置
        rate_limit = self._get_rate_limit_for_path(path)
        
        # 构建Redis键
        window = rate_limit["window"]
        current_window = int(time.time()) // window
        key = f"rate_limit:{client_ip}:{method}:{path}:{current_window}"
        
        try:
            if self.redis_client:
                # 使用Redis存储
                current_requests = await self._redis_increment(key, window)
            else:
                # 使用内存存储
                current_requests = self._memory_increment(key, window)
            
            allowed = current_requests <= rate_limit["requests"]
            remaining = max(0, rate_limit["requests"] - current_requests)
            reset_time = (current_window + 1) * window
            retry_after = reset_time - int(time.time()) if not allowed else 0
            
            return {
                "allowed": allowed,
                "limit": rate_limit["requests"],
                "remaining": remaining,
                "reset_time": reset_time,
                "retry_after": retry_after
            }
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            # 出错时允许请求通过
            return {
                "allowed": True,
                "limit": rate_limit["requests"],
                "remaining": rate_limit["requests"],
                "reset_time": int(time.time()) + window,
                "retry_after": 0
            }
    
    async def _redis_increment(self, key: str, ttl: int) -> int:
        """Redis计数器递增"""
        pipe = self.redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, ttl)
        results = pipe.execute()
        return results[0]
    
    def _memory_increment(self, key: str, ttl: int) -> int:
        """内存计数器递增"""
        current_time = time.time()
        
        # 清理过期的键
        expired_keys = [
            k for k, v in self.memory_store.items()
            if v["expires"] < current_time
        ]
        for k in expired_keys:
            del self.memory_store[k]
        
        # 递增计数器
        if key not in self.memory_store:
            self.memory_store[key] = {
                "count": 1,
                "expires": current_time + ttl
            }
        else:
            self.memory_store[key]["count"] += 1
        
        return self.memory_store[key]["count"]
    
    async def _check_suspicious_behavior(self, request: Request, client_ip: str):
        """检查可疑行为"""
        try:
            # 高频请求检测
            await self._check_high_frequency(client_ip)
            
            # 路径扫描检测
            await self._check_path_scanning(client_ip, request.url.path)
            
        except Exception as e:
            logger.error(f"Suspicious behavior check failed: {str(e)}")
    
    async def _check_high_frequency(self, client_ip: str):
        """检查高频请求"""
        pattern = self.suspicious_patterns["high_frequency"]
        key = f"suspicious:high_freq:{client_ip}"
        window = pattern["window"]
        threshold = pattern["threshold"]
        
        current_window = int(time.time()) // window
        window_key = f"{key}:{current_window}"
        
        try:
            if self.redis_client:
                count = await self._redis_increment(window_key, window)
            else:
                count = self._memory_increment(window_key, window)
            
            if count > threshold:
                logger.warning(
                    f"High frequency requests detected - "
                    f"IP: {client_ip} - "
                    f"Count: {count} in {window}s"
                )
                
                # 可以选择将IP加入临时黑名单
                # self._add_to_temp_blacklist(client_ip, 300)  # 5分钟
                
        except Exception as e:
            logger.error(f"High frequency check failed: {str(e)}")
    
    async def _check_path_scanning(self, client_ip: str, path: str):
        """检查路径扫描"""
        pattern = self.suspicious_patterns["path_scanning"]
        key = f"suspicious:path_scan:{client_ip}"
        window = pattern["window"]
        threshold = pattern["threshold"]
        
        current_window = int(time.time()) // window
        window_key = f"{key}:{current_window}"
        
        try:
            if self.redis_client:
                # 使用Redis Set存储访问的路径
                self.redis_client.sadd(window_key, path)
                self.redis_client.expire(window_key, window)
                path_count = self.redis_client.scard(window_key)
            else:
                # 使用内存存储
                if window_key not in self.memory_store:
                    self.memory_store[window_key] = {
                        "paths": set(),
                        "expires": time.time() + window
                    }
                
                self.memory_store[window_key]["paths"].add(path)
                path_count = len(self.memory_store[window_key]["paths"])
            
            if path_count > threshold:
                logger.warning(
                    f"Path scanning detected - "
                    f"IP: {client_ip} - "
                    f"Unique paths: {path_count} in {window}s"
                )
                
        except Exception as e:
            logger.error(f"Path scanning check failed: {str(e)}")
    
    async def _record_request(self, request: Request, client_ip: str, status_code: int, response_time: float):
        """记录请求信息"""
        try:
            request_info = {
                "ip": client_ip,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "response_time": response_time,
                "timestamp": time.time(),
                "user_agent": request.headers.get("user-agent", ""),
                "referer": request.headers.get("referer", "")
            }
            
            # 记录到Redis或内存
            key = f"request_log:{client_ip}:{int(time.time())}"
            
            if self.redis_client:
                self.redis_client.setex(key, 3600, json.dumps(request_info))  # 保存1小时
            else:
                # 简单的内存记录，避免内存泄漏
                if len(self.memory_store) < 10000:  # 限制内存使用
                    self.memory_store[key] = {
                        "data": request_info,
                        "expires": time.time() + 3600
                    }
            
        except Exception as e:
            logger.error(f"Request recording failed: {str(e)}")
    
    def _add_to_temp_blacklist(self, ip: str, duration: int):
        """添加IP到临时黑名单"""
        try:
            if self.redis_client:
                key = f"temp_blacklist:{ip}"
                self.redis_client.setex(key, duration, "1")
            
            logger.info(f"Added IP {ip} to temporary blacklist for {duration} seconds")
            
        except Exception as e:
            logger.error(f"Failed to add IP to blacklist: {str(e)}")

class IPBlacklistManager:
    """IP黑名单管理器"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        except Exception:
            self.redis_client = None
        
        self.memory_blacklist = set()
    
    def add_ip(self, ip: str, duration: Optional[int] = None, reason: str = ""):
        """添加IP到黑名单"""
        try:
            if self.redis_client:
                key = f"blacklist:{ip}"
                if duration:
                    self.redis_client.setex(key, duration, reason or "blocked")
                else:
                    self.redis_client.set(key, reason or "blocked")
            else:
                self.memory_blacklist.add(ip)
            
            logger.info(f"Added IP {ip} to blacklist. Reason: {reason}")
            
        except Exception as e:
            logger.error(f"Failed to add IP to blacklist: {str(e)}")
    
    def remove_ip(self, ip: str):
        """从黑名单移除IP"""
        try:
            if self.redis_client:
                key = f"blacklist:{ip}"
                self.redis_client.delete(key)
            else:
                self.memory_blacklist.discard(ip)
            
            logger.info(f"Removed IP {ip} from blacklist")
            
        except Exception as e:
            logger.error(f"Failed to remove IP from blacklist: {str(e)}")
    
    def is_blacklisted(self, ip: str) -> bool:
        """检查IP是否在黑名单中"""
        try:
            if self.redis_client:
                key = f"blacklist:{ip}"
                return self.redis_client.exists(key) > 0
            else:
                return ip in self.memory_blacklist
                
        except Exception as e:
            logger.error(f"Failed to check blacklist: {str(e)}")
            return False
    
    def get_blacklisted_ips(self) -> list:
        """获取所有黑名单IP"""
        try:
            if self.redis_client:
                keys = self.redis_client.keys("blacklist:*")
                return [key.replace("blacklist:", "") for key in keys]
            else:
                return list(self.memory_blacklist)
                
        except Exception as e:
            logger.error(f"Failed to get blacklisted IPs: {str(e)}")
            return []

# 全局黑名单管理器
ip_blacklist_manager = IPBlacklistManager()