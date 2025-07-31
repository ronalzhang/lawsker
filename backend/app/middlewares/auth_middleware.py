"""
认证中间件 - 处理令牌自动刷新和安全检查
"""
import time
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.security import security_manager
from app.core.logging import get_logger

logger = get_logger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件"""
    
    def __init__(self, app, excluded_paths: list = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/forgot-password",
            "/api/v1/auth/reset-password"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 跳过不需要认证的路径
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            response = await call_next(request)
            return response
        
        # 检查访问令牌
        access_token = security_manager.get_token_from_cookie(request, "access")
        refresh_token = security_manager.get_token_from_cookie(request, "refresh")
        
        token_refreshed = False
        
        if access_token:
            # 验证访问令牌
            payload = security_manager.verify_token(access_token, "access")
            if not payload and refresh_token:
                # 访问令牌过期，尝试刷新
                new_access_token = security_manager.refresh_access_token(refresh_token)
                if new_access_token:
                    # 将新令牌添加到请求上下文中
                    request.state.new_access_token = new_access_token
                    token_refreshed = True
                    logger.info(f"Token refreshed for user: {payload.get('user_id') if payload else 'unknown'}")
                else:
                    # 刷新令牌也无效，返回未授权
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Authentication required"}
                    )
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 如果令牌被刷新，设置新的Cookie
            if token_refreshed and hasattr(request.state, 'new_access_token'):
                security_manager.set_auth_cookies(
                    response,
                    request.state.new_access_token,
                    refresh_token
                )
            
            # 添加安全响应头
            self._add_security_headers(response)
            
            # 记录请求日志
            process_time = time.time() - start_time
            logger.info(
                f"Request: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Request processing error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
    
    def _add_security_headers(self, response: Response):
        """添加安全响应头"""
        # 防止XSS攻击
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # HSTS (仅在HTTPS环境下)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSP (内容安全策略)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https: wss:; "
            "frame-ancestors 'none';"
        )
        
        # 引用策略
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # 权限策略
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=()"
        )

class SecurityEventMiddleware(BaseHTTPMiddleware):
    """安全事件监控中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        self.suspicious_patterns = [
            "union select",
            "drop table",
            "insert into",
            "delete from",
            "<script",
            "javascript:",
            "onload=",
            "onerror=",
            "../",
            "..\\",
            "cmd.exe",
            "/etc/passwd",
            "eval(",
            "exec("
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查可疑请求模式
        await self._check_suspicious_patterns(request)
        
        # 检查请求频率
        await self._check_request_rate(request)
        
        response = await call_next(request)
        return response
    
    async def _check_suspicious_patterns(self, request: Request):
        """检查可疑请求模式"""
        # 检查URL参数
        query_string = str(request.url.query).lower()
        for pattern in self.suspicious_patterns:
            if pattern in query_string:
                logger.warning(
                    f"Suspicious pattern detected in query: {pattern} - "
                    f"IP: {request.client.host} - "
                    f"URL: {request.url.path}"
                )
                break
        
        # 检查请求体（如果是POST/PUT请求）
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                body_str = body.decode('utf-8').lower()
                for pattern in self.suspicious_patterns:
                    if pattern in body_str:
                        logger.warning(
                            f"Suspicious pattern detected in body: {pattern} - "
                            f"IP: {request.client.host} - "
                            f"URL: {request.url.path}"
                        )
                        break
            except Exception:
                pass  # 忽略解码错误
    
    async def _check_request_rate(self, request: Request):
        """检查请求频率"""
        # 这里可以实现基于IP的请求频率检查
        # 可以使用Redis来存储IP请求计数
        client_ip = request.client.host
        
        # 简单的内存存储示例（生产环境应使用Redis）
        if not hasattr(self, '_request_counts'):
            self._request_counts = {}
        
        current_time = int(time.time())
        minute_key = f"{client_ip}:{current_time // 60}"
        
        if minute_key not in self._request_counts:
            self._request_counts[minute_key] = 0
        
        self._request_counts[minute_key] += 1
        
        # 清理旧的计数
        keys_to_remove = [
            key for key in self._request_counts.keys()
            if int(key.split(':')[1]) < (current_time // 60) - 5
        ]
        for key in keys_to_remove:
            del self._request_counts[key]
        
        # 检查是否超过限制（每分钟100个请求）
        if self._request_counts[minute_key] > 100:
            logger.warning(
                f"High request rate detected - "
                f"IP: {client_ip} - "
                f"Count: {self._request_counts[minute_key]}/min"
            )