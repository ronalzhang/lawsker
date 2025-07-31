"""
增强的安全中间件
集成多种安全防护功能：IP白名单/黑名单、请求限流、CSRF保护、安全日志记录
"""
import time
import json
import redis
import hashlib
from typing import Callable, Dict, List, Optional, Set
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_logger

logger = get_logger(__name__)

class EnhancedSecurityMiddleware(BaseHTTPMiddleware):
    """增强的安全中间件"""
    
    def __init__(
        self,
        app,
        redis_url: str = "redis://localhost:6379",
        # IP控制配置
        ip_whitelist: Optional[List[str]] = None,
        ip_blacklist: Optional[List[str]] = None,
        auto_blacklist_enabled: bool = True,
        # 限流配置
        rate_limit_enabled: bool = True,
        default_rate_limit: str = "100/hour",
        burst_limit: int = 10,
        # CSRF配置
        csrf_enabled: bool = True,
        csrf_secret: str = "your-csrf-secret",
        # 安全日志配置
        security_logging_enabled: bool = True,
        # 豁免路径
        exempt_paths: Optional[List[str]] = None
    ):
        super().__init__(app)
        
        # Redis连接
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # IP控制配置
        self.ip_whitelist = set(ip_whitelist or [])
        self.ip_blacklist = set(ip_blacklist or [])
        self.auto_blacklist_enabled = auto_blacklist_enabled
        
        # 限流配置
        self.rate_limit_enabled = rate_limit_enabled
        self.default_rate_limit = default_rate_limit
        self.burst_limit = burst_limit
        
        # CSRF配置
        self.csrf_enabled = csrf_enabled
        self.csrf_secret = csrf_secret.encode('utf-8')
        
        # 安全日志配置
        self.security_logging_enabled = security_logging_enabled
        
        # 豁免路径
        self.exempt_paths = exempt_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register"
        ]
        
        # 安全事件类型
        self.security_events = {
            "ip_blocked": "IP地址被阻止",
            "rate_limit_exceeded": "请求频率超限",
            "csrf_validation_failed": "CSRF验证失败",
            "suspicious_request": "可疑请求",
            "brute_force_attempt": "暴力破解尝试"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求的主要逻辑"""
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        
        try:
            # 1. IP白名单/黑名单检查
            if not await self._check_ip_access(request, client_ip):
                return self._create_security_response(
                    "IP_BLOCKED",
                    "Access denied from this IP address",
                    client_ip,
                    request
                )
            
            # 2. 请求限流检查
            if self.rate_limit_enabled and not await self._check_rate_limit(request, client_ip):
                return self._create_security_response(
                    "RATE_LIMIT_EXCEEDED",
                    "Rate limit exceeded",
                    client_ip,
                    request
                )
            
            # 3. CSRF保护检查
            if self.csrf_enabled and not await self._check_csrf_protection(request):
                return self._create_security_response(
                    "CSRF_VALIDATION_FAILED",
                    "CSRF token validation failed",
                    client_ip,
                    request
                )
            
            # 4. 可疑请求检查
            if await self._detect_suspicious_request(request, client_ip):
                await self._handle_suspicious_request(request, client_ip)
            
            # 处理请求
            response = await call_next(request)
            
            # 5. 记录成功的请求
            if self.security_logging_enabled:
                await self._log_request(request, response, client_ip, time.time() - start_time)
            
            # 6. 设置安全响应头
            self._set_security_headers(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}")
            # 记录安全异常
            if self.security_logging_enabled:
                await self._log_security_event("middleware_error", client_ip, request, {"error": str(e)})
            
            # 返回通用错误响应
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal security error"}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host
    
    async def _check_ip_access(self, request: Request, client_ip: str) -> bool:
        """检查IP访问权限"""
        # 检查是否在黑名单中
        if client_ip in self.ip_blacklist:
            await self._log_security_event("ip_blocked", client_ip, request, {"reason": "blacklisted"})
            return False
        
        # 检查Redis中的动态黑名单
        if await self._is_ip_blacklisted(client_ip):
            await self._log_security_event("ip_blocked", client_ip, request, {"reason": "auto_blacklisted"})
            return False
        
        # 如果设置了白名单，检查是否在白名单中
        if self.ip_whitelist and client_ip not in self.ip_whitelist:
            await self._log_security_event("ip_blocked", client_ip, request, {"reason": "not_whitelisted"})
            return False
        
        return True
    
    async def _is_ip_blacklisted(self, client_ip: str) -> bool:
        """检查IP是否在动态黑名单中"""
        try:
            blacklist_key = f"security:blacklist:{client_ip}"
            return await self.redis_client.exists(blacklist_key)
        except Exception:
            return False
    
    async def _check_rate_limit(self, request: Request, client_ip: str) -> bool:
        """检查请求限流"""
        try:
            # 豁免路径不进行限流
            if any(request.url.path.startswith(path) for path in self.exempt_paths):
                return True
            
            # 使用滑动窗口算法进行限流
            current_time = int(time.time())
            window_size = 3600  # 1小时窗口
            limit = 100  # 默认每小时100次请求
            
            # 解析限流配置
            if "/" in self.default_rate_limit:
                limit_str, period_str = self.default_rate_limit.split("/")
                limit = int(limit_str)
                if period_str == "minute":
                    window_size = 60
                elif period_str == "hour":
                    window_size = 3600
                elif period_str == "day":
                    window_size = 86400
            
            # Redis键
            rate_limit_key = f"security:rate_limit:{client_ip}"
            
            # 获取当前窗口内的请求数
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(rate_limit_key, 0, current_time - window_size)
            pipe.zcard(rate_limit_key)
            pipe.zadd(rate_limit_key, {str(current_time): current_time})
            pipe.expire(rate_limit_key, window_size)
            
            results = pipe.execute()
            request_count = results[1]
            
            if request_count >= limit:
                await self._log_security_event(
                    "rate_limit_exceeded", 
                    client_ip, 
                    request, 
                    {"limit": limit, "count": request_count}
                )
                
                # 如果超过限制太多，自动加入黑名单
                if request_count > limit * 2:
                    await self._auto_blacklist_ip(client_ip, "rate_limit_abuse")
                
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
            return True  # 出错时允许请求通过
    
    async def _check_csrf_protection(self, request: Request) -> bool:
        """检查CSRF保护"""
        # 豁免GET请求和豁免路径
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return True
        
        # 获取CSRF token
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            # 尝试从表单数据获取
            try:
                if request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
                    form_data = await request.form()
                    csrf_token = form_data.get("csrf_token")
            except Exception:
                pass
        
        if not csrf_token:
            return False
        
        # 验证CSRF token
        cookie_token = request.cookies.get("csrf_token")
        if not cookie_token:
            return False
        
        return self._validate_csrf_token(csrf_token, cookie_token)
    
    def _validate_csrf_token(self, submitted_token: str, cookie_token: str) -> bool:
        """验证CSRF token"""
        try:
            import hmac
            import hashlib
            
            # 简化的CSRF验证逻辑
            parts = cookie_token.split('.')
            if len(parts) != 3:
                return False
            
            token_value, timestamp_str, signature = parts
            timestamp = int(timestamp_str)
            
            # 检查token是否过期（1小时）
            if time.time() - timestamp > 3600:
                return False
            
            # 验证签名
            message = f"{token_value}.{timestamp}".encode('utf-8')
            expected_signature = hmac.new(self.csrf_secret, message, hashlib.sha256).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return False
            
            # 验证提交的token
            return hmac.compare_digest(submitted_token, token_value)
            
        except Exception:
            return False
    
    async def _detect_suspicious_request(self, request: Request, client_ip: str) -> bool:
        """检测可疑请求"""
        suspicious_indicators = []
        
        # 检查User-Agent
        user_agent = request.headers.get("User-Agent", "")
        if not user_agent or len(user_agent) < 10:
            suspicious_indicators.append("missing_or_short_user_agent")
        
        # 检查常见的攻击模式
        url_path = request.url.path.lower()
        suspicious_patterns = [
            "admin", "wp-admin", "phpmyadmin", ".env", "config",
            "sql", "union", "select", "drop", "insert", "update",
            "../", "..\\", "<script", "javascript:", "eval("
        ]
        
        for pattern in suspicious_patterns:
            if pattern in url_path:
                suspicious_indicators.append(f"suspicious_pattern_{pattern}")
        
        # 检查请求频率异常
        try:
            freq_key = f"security:request_freq:{client_ip}"
            current_minute = int(time.time() / 60)
            
            pipe = self.redis_client.pipeline()
            pipe.hincrby(freq_key, str(current_minute), 1)
            pipe.expire(freq_key, 300)  # 5分钟过期
            pipe.hgetall(freq_key)
            
            results = pipe.execute()
            freq_data = results[2]
            
            # 如果1分钟内请求超过30次，标记为可疑
            current_freq = int(freq_data.get(str(current_minute), 0))
            if current_freq > 30:
                suspicious_indicators.append("high_frequency_requests")
                
        except Exception:
            pass
        
        # 如果有可疑指标，记录并返回True
        if suspicious_indicators:
            await self._log_security_event(
                "suspicious_request",
                client_ip,
                request,
                {"indicators": suspicious_indicators}
            )
            return True
        
        return False
    
    async def _handle_suspicious_request(self, request: Request, client_ip: str):
        """处理可疑请求"""
        # 增加可疑请求计数
        try:
            suspicious_key = f"security:suspicious:{client_ip}"
            count = await self.redis_client.incr(suspicious_key)
            await self.redis_client.expire(suspicious_key, 3600)  # 1小时过期
            
            # 如果可疑请求过多，自动加入黑名单
            if count > 10:
                await self._auto_blacklist_ip(client_ip, "suspicious_activity")
                
        except Exception:
            pass
    
    async def _auto_blacklist_ip(self, client_ip: str, reason: str):
        """自动将IP加入黑名单"""
        if not self.auto_blacklist_enabled:
            return
        
        try:
            blacklist_key = f"security:blacklist:{client_ip}"
            blacklist_data = {
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
                "auto_generated": True
            }
            
            await self.redis_client.setex(
                blacklist_key,
                86400,  # 24小时
                json.dumps(blacklist_data)
            )
            
            logger.warning(f"Auto-blacklisted IP {client_ip} for {reason}")
            
        except Exception as e:
            logger.error(f"Failed to auto-blacklist IP {client_ip}: {str(e)}")
    
    async def _log_security_event(self, event_type: str, client_ip: str, request: Request, details: Dict = None):
        """记录安全事件"""
        if not self.security_logging_enabled:
            return
        
        try:
            event_data = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "client_ip": client_ip,
                "method": request.method,
                "url": str(request.url),
                "user_agent": request.headers.get("User-Agent", ""),
                "referer": request.headers.get("Referer", ""),
                "details": details or {}
            }
            
            # 记录到Redis
            event_key = f"security:events:{int(time.time())}"
            await self.redis_client.setex(event_key, 86400 * 7, json.dumps(event_data))  # 保存7天
            
            # 记录到日志
            logger.warning(f"Security event: {event_type} from {client_ip} - {request.method} {request.url.path}")
            
        except Exception as e:
            logger.error(f"Failed to log security event: {str(e)}")
    
    async def _log_request(self, request: Request, response: Response, client_ip: str, response_time: float):
        """记录正常请求"""
        try:
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "client_ip": client_ip,
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "response_time": response_time,
                "user_agent": request.headers.get("User-Agent", "")
            }
            
            # 记录到Redis（采样记录，避免过多日志）
            if hash(client_ip + str(int(time.time() / 60))) % 10 == 0:  # 10%采样率
                log_key = f"security:access_logs:{int(time.time())}"
                await self.redis_client.setex(log_key, 3600, json.dumps(log_data))  # 保存1小时
                
        except Exception:
            pass
    
    def _create_security_response(self, error_code: str, message: str, client_ip: str, request: Request) -> JSONResponse:
        """创建安全错误响应"""
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": {
                    "code": error_code,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                    "request_id": id(request)
                }
            }
        )
    
    def _set_security_headers(self, response: Response):
        """设置安全响应头"""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value

# 安全事件查询API
class SecurityEventManager:
    """安全事件管理器"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
    
    async def get_security_events(self, hours: int = 24, event_type: str = None) -> List[Dict]:
        """获取安全事件"""
        try:
            current_time = int(time.time())
            start_time = current_time - (hours * 3600)
            
            # 获取时间范围内的所有事件键
            pattern = f"security:events:*"
            keys = await self.redis_client.keys(pattern)
            
            events = []
            for key in keys:
                timestamp = int(key.split(":")[-1])
                if timestamp >= start_time:
                    event_data = await self.redis_client.get(key)
                    if event_data:
                        event = json.loads(event_data)
                        if not event_type or event.get("event_type") == event_type:
                            events.append(event)
            
            # 按时间排序
            events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return events
            
        except Exception as e:
            logger.error(f"Failed to get security events: {str(e)}")
            return []
    
    async def get_blacklisted_ips(self) -> List[Dict]:
        """获取黑名单IP"""
        try:
            pattern = "security:blacklist:*"
            keys = await self.redis_client.keys(pattern)
            
            blacklisted_ips = []
            for key in keys:
                ip = key.split(":")[-1]
                data = await self.redis_client.get(key)
                if data:
                    blacklist_info = json.loads(data)
                    blacklist_info["ip"] = ip
                    blacklisted_ips.append(blacklist_info)
            
            return blacklisted_ips
            
        except Exception as e:
            logger.error(f"Failed to get blacklisted IPs: {str(e)}")
            return []
    
    async def remove_from_blacklist(self, ip: str) -> bool:
        """从黑名单中移除IP"""
        try:
            blacklist_key = f"security:blacklist:{ip}"
            result = await self.redis_client.delete(blacklist_key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to remove IP from blacklist: {str(e)}")
            return False