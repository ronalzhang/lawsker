"""
安全认证模块 - HttpOnly Cookie 实现
"""
import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Request, Response
from fastapi.security import HTTPBearer
from passlib.context import CryptContext
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置
JWT_ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1小时
REFRESH_TOKEN_EXPIRE_DAYS = 30    # 30天

# Cookie配置
COOKIE_SETTINGS = {
    "httponly": True,
    "secure": True,  # 生产环境必须为True
    "samesite": "strict",
    "path": "/",
    "domain": None  # 根据环境配置
}

class SecurityManager:
    """安全管理器"""
    
    def __init__(self):
        self.private_key = self._load_or_generate_private_key()
        self.public_key = self.private_key.public_key()
        
    def _load_or_generate_private_key(self):
        """加载或生成RSA私钥"""
        key_path = "jwt_private_key.pem"
        
        if os.path.exists(key_path):
            with open(key_path, "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None
                )
        else:
            # 生成新的RSA密钥对
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # 保存私钥
            pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            with open(key_path, "wb") as key_file:
                key_file.write(pem)
                
        return private_key
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "type": "access"})
        
        private_key_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        encoded_jwt = jwt.encode(to_encode, private_key_pem, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        private_key_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        encoded_jwt = jwt.encode(to_encode, private_key_pem, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            public_key_pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            payload = jwt.decode(token, public_key_pem, algorithms=[JWT_ALGORITHM])
            
            # 验证令牌类型
            if payload.get("type") != token_type:
                return None
                
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    def set_auth_cookies(self, response: Response, access_token: str, refresh_token: str):
        """设置认证Cookie"""
        # 设置访问令牌Cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            **COOKIE_SETTINGS
        )
        
        # 设置刷新令牌Cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            **COOKIE_SETTINGS
        )
    
    def clear_auth_cookies(self, response: Response):
        """清除认证Cookie"""
        response.delete_cookie(
            key="access_token",
            path=COOKIE_SETTINGS["path"],
            domain=COOKIE_SETTINGS["domain"]
        )
        response.delete_cookie(
            key="refresh_token", 
            path=COOKIE_SETTINGS["path"],
            domain=COOKIE_SETTINGS["domain"]
        )
    
    def get_token_from_cookie(self, request: Request, token_type: str = "access") -> Optional[str]:
        """从Cookie获取令牌"""
        cookie_name = f"{token_type}_token"
        return request.cookies.get(cookie_name)
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """刷新访问令牌"""
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            return None
        
        # 创建新的访问令牌
        new_payload = {
            "sub": payload["sub"],
            "user_id": payload.get("user_id"),
            "role": payload.get("role"),
            "permissions": payload.get("permissions", [])
        }
        
        return self.create_access_token(new_payload)

# 全局安全管理器实例
security_manager = SecurityManager()

class CookieHTTPBearer(HTTPBearer):
    """基于Cookie的HTTP Bearer认证"""
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Optional[str]:
        # 首先尝试从Cookie获取令牌
        token = security_manager.get_token_from_cookie(request, "access")
        
        if not token:
            # 如果Cookie中没有，尝试从Authorization头获取
            authorization = request.headers.get("Authorization")
            if authorization:
                scheme, token = authorization.split()
                if scheme.lower() != "bearer":
                    if self.auto_error:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid authentication scheme"
                        )
                    return None
            else:
                if self.auto_error:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Not authenticated"
                    )
                return None
        
        return token

# Cookie认证实例
cookie_bearer = CookieHTTPBearer()

async def get_current_user(request: Request) -> Dict[str, Any]:
    """获取当前用户"""
    token = await cookie_bearer(request)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    payload = security_manager.verify_token(token)
    if not payload:
        # 尝试刷新令牌
        refresh_token = security_manager.get_token_from_cookie(request, "refresh")
        if refresh_token:
            new_access_token = security_manager.refresh_access_token(refresh_token)
            if new_access_token:
                payload = security_manager.verify_token(new_access_token)
                if payload:
                    # 这里需要在响应中设置新的访问令牌
                    # 但由于这是依赖注入，无法直接访问response对象
                    # 需要在中间件中处理令牌刷新
                    pass
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
    
    return payload

async def get_current_active_user(request: Request) -> Dict[str, Any]:
    """获取当前活跃用户"""
    current_user = await get_current_user(request)
    
    # 这里可以添加用户状态检查逻辑
    # 例如检查用户是否被禁用、是否需要重新验证等
    
    return current_user

def require_permissions(required_permissions: list):
    """权限验证装饰器"""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            current_user = await get_current_user(request)
            user_permissions = current_user.get("permissions", [])
            
            # 检查用户是否具有所需权限
            if not all(perm in user_permissions for perm in required_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

def require_role(required_role: str):
    """角色验证装饰器"""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            current_user = await get_current_user(request)
            user_role = current_user.get("role")
            
            if user_role != required_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{required_role}' required"
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

# 创建全局安全管理器实例
security_manager = SecurityManager()

# 导出便捷函数
def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return security_manager.get_password_hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return security_manager.verify_password(plain_password, hashed_password)

def create_access_token(data: Dict[str, Any]) -> str:
    """创建访问令牌"""
    return security_manager.create_access_token(data)

def create_refresh_token(data: Dict[str, Any]) -> str:
    """创建刷新令牌"""
    return security_manager.create_refresh_token(data)

def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """验证令牌"""
    return security_manager.verify_token(token, token_type)