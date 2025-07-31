"""
CSRF保护中间件
防止跨站请求伪造攻击
"""
import secrets
import hmac
import hashlib
import time
import redis
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_logger

logger = get_logger(__name__)

# Redis客户端用于IP黑名单和限流
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF保护中间件"""
    
    def __init__(
        self,
        app,
        secret_key: str,
        token_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        cookie_name: str = "csrf_token",
        exempt_methods: list = None,
        exempt_paths: list = None,
        token_lifetime: int = 3600  # 1小时
    ):
        super().__init__(app)
        self.secret_key = secret_key.encode('utf-8')
        self.token_name = token_name
        self.header_name = header_name
        self.cookie_name = cookie_name
        self.exempt_methods = exempt_methods or ["GET", "HEAD", "OPTIONS", "TRACE"]
        self.exempt_paths = exempt_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/forgot-password",
            "/api/v1/auth/reset-password",
            "/api/v1/auth/send-sms-code",
            "/api/v1/auth/verify-sms-code"
        ]
        self.token_lifetime = token_lifetime
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查是否需要CSRF保护
        if self._should_exempt(request):
            response = await call_next(request)
            # 为豁免的请求也设置CSRF token（如登录页面）
            if request.method == "GET" and any(path in request.url.path for path in ["/login", "/register"]):
                self._set_csrf_token(response)
            return response
        
        # 验证CSRF token
        if not await self._verify_csrf_token(request):
            logger.warning(
                f"CSRF token validation failed - "
                f"IP: {request.client.host} - "
                f"URL: {request.url.path} - "
                f"Method: {request.method}"
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token validation failed"}
            )
        
        # 处理请求
        response = await call_next(request)
        
        # 为响应设置新的CSRF token
        self._set_csrf_token(response)
        
        return response
    
    def _should_exempt(self, request: Request) -> bool:
        """检查请求是否应该豁免CSRF保护"""
        # 豁免的HTTP方法
        if request.method in self.exempt_methods:
            return True
        
        # 豁免的路径
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return True
        
        return False
    
    async def _verify_csrf_token(self, request: Request) -> bool:
        """验证CSRF token"""
        # 从请求头获取token
        token_from_header = request.headers.get(self.header_name)
        
        # 从表单数据获取token（如果是表单提交）
        token_from_form = None
        if request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
            try:
                form_data = await request.form()
                token_from_form = form_data.get(self.token_name)
            except Exception:
                pass
        
        # 从JSON数据获取token
        token_from_json = None
        if request.headers.get("content-type", "").startswith("application/json"):
            try:
                # 由于request.json()只能调用一次，我们需要读取原始body
                body = await request.body()
                if body:
                    import json
                    json_data = json.loads(body.decode('utf-8'))
                    token_from_json = json_data.get(self.token_name)
            except Exception:
                pass
        
        # 获取提交的token
        submitted_token = token_from_header or token_from_form or token_from_json
        
        if not submitted_token:
            return False
        
        # 从Cookie获取token进行比较
        cookie_token = request.cookies.get(self.cookie_name)
        if not cookie_token:
            return False
        
        # 验证token
        return self._validate_token(submitted_token, cookie_token)
    
    def _validate_token(self, submitted_token: str, cookie_token: str) -> bool:
        """验证token的有效性"""
        try:
            # 解析cookie中的token
            parts = cookie_token.split('.')
            if len(parts) != 3:
                return False
            
            token_value, timestamp_str, signature = parts
            timestamp = int(timestamp_str)
            
            # 检查token是否过期
            if time.time() - timestamp > self.token_lifetime:
                return False
            
            # 验证签名
            expected_signature = self._generate_signature(token_value, timestamp)
            if not hmac.compare_digest(signature, expected_signature):
                return False
            
            # 验证提交的token是否与cookie中的token匹配
            return hmac.compare_digest(submitted_token, token_value)
            
        except Exception as e:
            logger.error(f"CSRF token validation error: {str(e)}")
            return False
    
    def _generate_token(self) -> tuple[str, str]:
        """生成CSRF token"""
        # 生成随机token
        token_value = secrets.token_urlsafe(32)
        timestamp = int(time.time())
        
        # 生成签名
        signature = self._generate_signature(token_value, timestamp)
        
        # 组合完整的cookie token
        cookie_token = f"{token_value}.{timestamp}.{signature}"
        
        return token_value, cookie_token
    
    def _generate_signature(self, token_value: str, timestamp: int) -> str:
        """生成token签名"""
        message = f"{token_value}.{timestamp}".encode('utf-8')
        signature = hmac.new(self.secret_key, message, hashlib.sha256).hexdigest()
        return signature
    
    def _set_csrf_token(self, response: Response):
        """设置CSRF token到响应中"""
        token_value, cookie_token = self._generate_token()
        
        # 设置Cookie
        response.set_cookie(
            key=self.cookie_name,
            value=cookie_token,
            max_age=self.token_lifetime,
            httponly=False,  # CSRF token需要被JavaScript访问
            secure=True,     # 生产环境必须为True
            samesite="strict"
        )
        
        # 设置响应头，方便前端获取
        response.headers[f"X-{self.token_name.replace('_', '-').title()}"] = token_value

class CSRFTokenGenerator:
    """CSRF Token生成器"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode('utf-8')
    
    def generate_token(self) -> dict:
        """生成CSRF token"""
        token_value = secrets.token_urlsafe(32)
        timestamp = int(time.time())
        
        # 生成签名
        message = f"{token_value}.{timestamp}".encode('utf-8')
        signature = hmac.new(self.secret_key, message, hashlib.sha256).hexdigest()
        
        # 组合完整的cookie token
        cookie_token = f"{token_value}.{timestamp}.{signature}"
        
        return {
            "token": token_value,
            "cookie_token": cookie_token,
            "timestamp": timestamp
        }
    
    def validate_token(self, submitted_token: str, cookie_token: str, max_age: int = 3600) -> bool:
        """验证CSRF token"""
        try:
            # 解析cookie中的token
            parts = cookie_token.split('.')
            if len(parts) != 3:
                return False
            
            token_value, timestamp_str, signature = parts
            timestamp = int(timestamp_str)
            
            # 检查token是否过期
            if time.time() - timestamp > max_age:
                return False
            
            # 验证签名
            message = f"{token_value}.{timestamp}".encode('utf-8')
            expected_signature = hmac.new(self.secret_key, message, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected_signature):
                return False
            
            # 验证提交的token是否与cookie中的token匹配
            return hmac.compare_digest(submitted_token, token_value)
            
        except Exception:
            return False

# 全局CSRF token生成器
csrf_generator = CSRFTokenGenerator("your-csrf-secret-key-here")

def get_csrf_token() -> dict:
    """获取CSRF token"""
    return csrf_generator.generate_token()

def verify_csrf_token(submitted_token: str, cookie_token: str) -> bool:
    """验证CSRF token"""
    return csrf_generator.validate_token(submitted_token, cookie_token)