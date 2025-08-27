# Lawsker安全开发指南

## 📋 目录

- [安全开发原则](#安全开发原则)
- [认证与授权](#认证与授权)
- [数据保护](#数据保护)
- [输入验证](#输入验证)
- [安全编码规范](#安全编码规范)
- [漏洞防护](#漏洞防护)
- [安全测试](#安全测试)
- [安全监控](#安全监控)
- [应急响应](#应急响应)

## 🛡️ 安全开发原则

### 核心原则
1. **最小权限原则**: 用户和系统只获得完成任务所需的最小权限
2. **深度防御**: 多层安全控制，不依赖单一防护措施
3. **失败安全**: 系统失败时应保持安全状态
4. **默认安全**: 系统默认配置应该是安全的
5. **安全透明**: 安全措施不应影响用户体验

### 安全开发生命周期 (SDLC)
```
需求分析 → 威胁建模 → 安全设计 → 安全编码 → 安全测试 → 安全部署 → 安全监控
    ↓         ↓         ↓         ↓         ↓         ↓         ↓
  安全需求   威胁识别   安全架构   代码审查   渗透测试   安全配置   持续监控
```

## 🔐 认证与授权

### JWT Token安全实现
```python
# app/core/security.py
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

class SecurityManager:
    """安全管理器"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.private_key = self._load_private_key()
        self.public_key = self._load_public_key()
        self.algorithm = "RS256"
    
    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        """创建访问令牌"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=1)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.private_key, 
            algorithm=self.algorithm
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str):
        """验证令牌"""
        try:
            payload = jwt.decode(
                token, 
                self.public_key, 
                algorithms=[self.algorithm]
            )
            
            # 验证令牌类型
            if payload.get("type") != "access":
                raise jwt.InvalidTokenError("Invalid token type")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(401, "Invalid token")
    
    def hash_password(self, password: str) -> str:
        """密码哈希"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)
```

### 权限控制系统
```python
# app/core/permissions.py
from enum import Enum
from functools import wraps
from fastapi import HTTPException, Depends
from app.models.user import User

class Permission(Enum):
    """权限枚举"""
    READ_USER = "read:user"
    WRITE_USER = "write:user"
    READ_CASE = "read:case"
    WRITE_CASE = "write:case"
    ADMIN_ACCESS = "admin:access"

class Role(Enum):
    """角色枚举"""
    USER = "user"
    LAWYER = "lawyer"
    ADMIN = "admin"

# 角色权限映射
ROLE_PERMISSIONS = {
    Role.USER: [
        Permission.READ_USER,
        Permission.WRITE_USER,
        Permission.READ_CASE,
        Permission.WRITE_CASE
    ],
    Role.LAWYER: [
        Permission.READ_USER,
        Permission.WRITE_USER,
        Permission.READ_CASE,
        Permission.WRITE_CASE
    ],
    Role.ADMIN: [
        Permission.READ_USER,
        Permission.WRITE_USER,
        Permission.READ_CASE,
        Permission.WRITE_CASE,
        Permission.ADMIN_ACCESS
    ]
}

def require_permission(permission: Permission):
    """权限装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            user_role = Role(current_user.role)
            user_permissions = ROLE_PERMISSIONS.get(user_role, [])
            
            if permission not in user_permissions:
                raise HTTPException(403, "Insufficient permissions")
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# 使用示例
@app.get("/api/v1/admin/users")
@require_permission(Permission.ADMIN_ACCESS)
async def get_all_users(current_user: User = Depends(get_current_user)):
    """获取所有用户 - 需要管理员权限"""
    pass
```

### 多因素认证 (MFA)
```python
# app/services/mfa_service.py
import pyotp
import qrcode
from io import BytesIO
import base64

class MFAService:
    """多因素认证服务"""
    
    def generate_secret(self, user_email: str) -> str:
        """生成MFA密钥"""
        secret = pyotp.random_base32()
        return secret
    
    def generate_qr_code(self, user_email: str, secret: str) -> str:
        """生成二维码"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name="Lawsker"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 转换为base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """验证TOTP令牌"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    def enable_mfa(self, user_id: int, secret: str):
        """启用MFA"""
        # 保存用户的MFA密钥到数据库
        # 注意：密钥应该加密存储
        pass
```

## 🔒 数据保护

### 敏感数据加密
```python
# app/core/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class DataEncryption:
    """数据加密服务"""
    
    def __init__(self, password: bytes):
        self.key = self._derive_key(password)
        self.cipher = Fernet(self.key)
    
    def _derive_key(self, password: bytes) -> bytes:
        """从密码派生密钥"""
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def encrypt(self, data: str) -> str:
        """加密数据"""
        encrypted_data = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = self.cipher.decrypt(encrypted_bytes)
        return decrypted_data.decode()

# 数据库字段加密
class EncryptedField:
    """加密字段类型"""
    
    def __init__(self, encryption_service: DataEncryption):
        self.encryption = encryption_service
    
    def process_bind_param(self, value, dialect):
        """存储时加密"""
        if value is not None:
            return self.encryption.encrypt(value)
        return value
    
    def process_result_value(self, value, dialect):
        """读取时解密"""
        if value is not None:
            return self.encryption.decrypt(value)
        return value
```

### 数据脱敏
```python
# app/utils/data_masking.py
import re
from typing import Optional

class DataMasking:
    """数据脱敏工具"""
    
    @staticmethod
    def mask_email(email: str) -> str:
        """邮箱脱敏"""
        if not email or '@' not in email:
            return email
        
        local, domain = email.split('@', 1)
        if len(local) <= 2:
            masked_local = '*' * len(local)
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """手机号脱敏"""
        if not phone or len(phone) < 7:
            return phone
        
        return phone[:3] + '*' * (len(phone) - 6) + phone[-3:]
    
    @staticmethod
    def mask_id_card(id_card: str) -> str:
        """身份证号脱敏"""
        if not id_card or len(id_card) < 8:
            return id_card
        
        return id_card[:4] + '*' * (len(id_card) - 8) + id_card[-4:]
    
    @staticmethod
    def mask_bank_card(card_number: str) -> str:
        """银行卡号脱敏"""
        if not card_number or len(card_number) < 8:
            return card_number
        
        return card_number[:4] + '*' * (len(card_number) - 8) + card_number[-4:]
```

## ✅ 输入验证

### 输入验证框架
```python
# app/core/validation.py
from pydantic import BaseModel, validator, Field
from typing import Optional
import re

class UserCreateSchema(BaseModel):
    """用户创建验证模式"""
    
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    
    @validator('email')
    def validate_email(cls, v):
        """邮箱验证"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('邮箱格式不正确')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        """密码强度验证"""
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('密码必须包含大写字母')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('密码必须包含小写字母')
        
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含数字')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('密码必须包含特殊字符')
        
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        """手机号验证"""
        if v is None:
            return v
        
        phone_pattern = r'^1[3-9]\d{9}$'
        if not re.match(phone_pattern, v):
            raise ValueError('手机号格式不正确')
        
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        """姓名验证"""
        # 移除HTML标签
        clean_name = re.sub(r'<[^>]+>', '', v)
        
        # 检查是否包含特殊字符
        if re.search(r'[<>"\']', clean_name):
            raise ValueError('姓名包含非法字符')
        
        return clean_name.strip()
```

### SQL注入防护
```python
# app/core/database.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any

class SafeQuery:
    """安全查询类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def execute_safe_query(self, query: str, params: Dict[str, Any] = None):
        """执行安全查询"""
        # 使用参数化查询防止SQL注入
        if params:
            result = self.db.execute(text(query), params)
        else:
            result = self.db.execute(text(query))
        
        return result
    
    def search_users(self, search_term: str, limit: int = 10):
        """安全的用户搜索"""
        # 错误示例 - 容易SQL注入
        # query = f"SELECT * FROM users WHERE name LIKE '%{search_term}%'"
        
        # 正确示例 - 参数化查询
        query = """
            SELECT id, email, full_name, created_at 
            FROM users 
            WHERE full_name ILIKE :search_term 
            LIMIT :limit
        """
        
        params = {
            "search_term": f"%{search_term}%",
            "limit": limit
        }
        
        return self.execute_safe_query(query, params)
```

### XSS防护
```python
# app/utils/sanitizer.py
import bleach
from markupsafe import Markup

class HTMLSanitizer:
    """HTML内容清理器"""
    
    # 允许的HTML标签
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote'
    ]
    
    # 允许的属性
    ALLOWED_ATTRIBUTES = {
        '*': ['class'],
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'width', 'height']
    }
    
    @classmethod
    def clean_html(cls, content: str) -> str:
        """清理HTML内容"""
        if not content:
            return content
        
        cleaned = bleach.clean(
            content,
            tags=cls.ALLOWED_TAGS,
            attributes=cls.ALLOWED_ATTRIBUTES,
            strip=True
        )
        
        return cleaned
    
    @classmethod
    def escape_html(cls, content: str) -> str:
        """转义HTML内容"""
        if not content:
            return content
        
        return bleach.clean(content, tags=[], strip=True)
    
    @classmethod
    def sanitize_user_input(cls, data: dict) -> dict:
        """清理用户输入数据"""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = cls.escape_html(value)
            else:
                sanitized[key] = value
        
        return sanitized
```

## 🔧 安全编码规范

### 错误处理安全
```python
# app/core/error_handlers.py
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class SecurityError(Exception):
    """安全相关错误"""
    pass

def safe_error_handler(func):
    """安全错误处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SecurityError as e:
            # 记录安全错误但不暴露详细信息
            logger.error(f"Security error: {str(e)}")
            raise HTTPException(403, "Access denied")
        except Exception as e:
            # 记录详细错误但返回通用错误信息
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(500, "Internal server error")
    
    return wrapper

# 使用示例
@safe_error_handler
def sensitive_operation():
    """敏感操作"""
    # 可能抛出SecurityError的代码
    pass
```

### 安全日志记录
```python
# app/core/security_logger.py
import logging
from datetime import datetime
from typing import Optional
from app.models.security_log import SecurityLog

class SecurityLogger:
    """安全日志记录器"""
    
    def __init__(self):
        self.logger = logging.getLogger("security")
    
    def log_login_attempt(self, email: str, ip_address: str, success: bool, user_agent: str = None):
        """记录登录尝试"""
        event_type = "login_success" if success else "login_failure"
        
        self.logger.info(f"{event_type}: {email} from {ip_address}")
        
        # 保存到数据库
        security_log = SecurityLog(
            event_type=event_type,
            user_email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow()
        )
        
        # 如果登录失败，检查是否需要锁定账户
        if not success:
            self._check_brute_force(email, ip_address)
    
    def log_permission_denied(self, user_id: int, resource: str, ip_address: str):
        """记录权限拒绝"""
        self.logger.warning(f"Permission denied: user {user_id} accessing {resource} from {ip_address}")
        
        security_log = SecurityLog(
            event_type="permission_denied",
            user_id=user_id,
            resource=resource,
            ip_address=ip_address,
            timestamp=datetime.utcnow()
        )
    
    def log_suspicious_activity(self, description: str, user_id: int = None, ip_address: str = None):
        """记录可疑活动"""
        self.logger.warning(f"Suspicious activity: {description}")
        
        security_log = SecurityLog(
            event_type="suspicious_activity",
            description=description,
            user_id=user_id,
            ip_address=ip_address,
            timestamp=datetime.utcnow()
        )
    
    def _check_brute_force(self, email: str, ip_address: str):
        """检查暴力破解攻击"""
        # 检查最近5分钟内的失败登录次数
        recent_failures = self._count_recent_failures(email, ip_address)
        
        if recent_failures >= 5:
            self.log_suspicious_activity(
                f"Possible brute force attack: {recent_failures} failed attempts",
                ip_address=ip_address
            )
            
            # 触发账户锁定或IP封禁
            self._trigger_security_measures(email, ip_address)
```

### 文件上传安全
```python
# app/services/file_upload_service.py
import os
import magic
from pathlib import Path
from typing import List
from fastapi import UploadFile, HTTPException

class SecureFileUpload:
    """安全文件上传服务"""
    
    # 允许的文件类型
    ALLOWED_MIME_TYPES = {
        'image/jpeg', 'image/png', 'image/gif',
        'application/pdf', 'text/plain',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.txt', '.doc', '.docx'}
    
    # 最大文件大小 (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def __init__(self, upload_dir: str):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(self, file: UploadFile, user_id: int) -> str:
        """安全上传文件"""
        # 1. 检查文件大小
        if file.size > self.MAX_FILE_SIZE:
            raise HTTPException(400, "文件大小超过限制")
        
        # 2. 检查文件扩展名
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(400, "不支持的文件类型")
        
        # 3. 读取文件内容
        content = await file.read()
        
        # 4. 检查文件MIME类型
        mime_type = magic.from_buffer(content, mime=True)
        if mime_type not in self.ALLOWED_MIME_TYPES:
            raise HTTPException(400, "文件类型验证失败")
        
        # 5. 检查文件内容安全性
        if self._contains_malicious_content(content):
            raise HTTPException(400, "文件包含恶意内容")
        
        # 6. 生成安全的文件名
        safe_filename = self._generate_safe_filename(file.filename, user_id)
        
        # 7. 保存文件
        file_path = self.upload_dir / safe_filename
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return str(file_path)
    
    def _generate_safe_filename(self, original_filename: str, user_id: int) -> str:
        """生成安全的文件名"""
        import uuid
        from datetime import datetime
        
        # 获取文件扩展名
        extension = Path(original_filename).suffix.lower()
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        return f"user_{user_id}_{timestamp}_{unique_id}{extension}"
    
    def _contains_malicious_content(self, content: bytes) -> bool:
        """检查文件是否包含恶意内容"""
        # 检查常见的恶意脚本标签
        malicious_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'onload=',
            b'onerror=',
            b'<?php'
        ]
        
        content_lower = content.lower()
        for pattern in malicious_patterns:
            if pattern in content_lower:
                return True
        
        return False
```

## 🛡️ 漏洞防护

### CSRF防护
```python
# app/middlewares/csrf_middleware.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import secrets
import hmac
import hashlib

class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF防护中间件"""
    
    def __init__(self, app, secret_key: str):
        super().__init__(app)
        self.secret_key = secret_key.encode()
    
    async def dispatch(self, request: Request, call_next):
        # 对于安全的HTTP方法，不需要CSRF检查
        if request.method in ["GET", "HEAD", "OPTIONS", "TRACE"]:
            response = await call_next(request)
            
            # 为GET请求设置CSRF token
            if request.method == "GET":
                csrf_token = self._generate_csrf_token()
                response.set_cookie(
                    "csrf_token",
                    csrf_token,
                    httponly=True,
                    secure=True,
                    samesite="strict"
                )
            
            return response
        
        # 对于不安全的HTTP方法，检查CSRF token
        csrf_token = request.cookies.get("csrf_token")
        csrf_header = request.headers.get("X-CSRF-Token")
        
        if not csrf_token or not csrf_header:
            raise HTTPException(403, "CSRF token missing")
        
        if not self._verify_csrf_token(csrf_token, csrf_header):
            raise HTTPException(403, "CSRF token invalid")
        
        return await call_next(request)
    
    def _generate_csrf_token(self) -> str:
        """生成CSRF token"""
        random_bytes = secrets.token_bytes(32)
        signature = hmac.new(self.secret_key, random_bytes, hashlib.sha256).hexdigest()
        return f"{random_bytes.hex()}.{signature}"
    
    def _verify_csrf_token(self, cookie_token: str, header_token: str) -> bool:
        """验证CSRF token"""
        if cookie_token != header_token:
            return False
        
        try:
            token_data, signature = cookie_token.split('.')
            token_bytes = bytes.fromhex(token_data)
            expected_signature = hmac.new(self.secret_key, token_bytes, hashlib.sha256).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except (ValueError, TypeError):
            return False
```

### 限流防护
```python
# app/middlewares/rate_limit_middleware.py
import time
import redis
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    
    def __init__(self, app, redis_client: redis.Redis, default_limit: int = 100):
        super().__init__(app)
        self.redis = redis_client
        self.default_limit = default_limit
        
        # 不同端点的限流配置
        self.endpoint_limits = {
            "/api/v1/auth/login": 5,  # 登录接口每分钟5次
            "/api/v1/auth/register": 3,  # 注册接口每分钟3次
            "/api/v1/cases": 20,  # 案件接口每分钟20次
        }
    
    async def dispatch(self, request: Request, call_next):
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        
        # 获取请求路径
        path = request.url.path
        
        # 检查限流
        if not await self._check_rate_limit(client_ip, path):
            raise HTTPException(429, "Rate limit exceeded")
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host
    
    async def _check_rate_limit(self, client_ip: str, path: str) -> bool:
        """检查限流"""
        # 获取该端点的限流配置
        limit = self.endpoint_limits.get(path, self.default_limit)
        
        # Redis键
        key = f"rate_limit:{client_ip}:{path}"
        
        # 使用滑动窗口算法
        current_time = int(time.time())
        window_start = current_time - 60  # 1分钟窗口
        
        # 清理过期的请求记录
        self.redis.zremrangebyscore(key, 0, window_start)
        
        # 获取当前窗口内的请求数量
        current_requests = self.redis.zcard(key)
        
        if current_requests >= limit:
            return False
        
        # 记录当前请求
        self.redis.zadd(key, {str(current_time): current_time})
        self.redis.expire(key, 60)  # 设置过期时间
        
        return True
```

## 🧪 安全测试

### 自动化安全测试
```python
# tests/security/test_security_vulnerabilities.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

class TestSecurityVulnerabilities:
    """安全漏洞测试"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_sql_injection_protection(self, client):
        """测试SQL注入防护"""
        # 常见的SQL注入载荷
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --"
        ]
        
        for payload in sql_payloads:
            # 测试搜索接口
            response = client.get(f"/api/v1/users/search?q={payload}")
            
            # 应该返回正常响应，而不是服务器错误
            assert response.status_code in [200, 400, 422]
            
            # 验证没有执行恶意SQL
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
    
    def test_xss_protection(self, client):
        """测试XSS防护"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>"
        ]
        
        for payload in xss_payloads:
            # 测试用户注册
            response = client.post("/api/v1/users", json={
                "email": "test@example.com",
                "password": "Password123!",
                "full_name": payload
            })
            
            if response.status_code == 201:
                user_data = response.json()
                # 验证恶意脚本被过滤或转义
                assert "<script>" not in user_data.get("full_name", "")
                assert "javascript:" not in user_data.get("full_name", "")
    
    def test_authentication_bypass(self, client):
        """测试认证绕过"""
        protected_endpoints = [
            "/api/v1/users/me",
            "/api/v1/cases",
            "/api/v1/admin/users"
        ]
        
        for endpoint in protected_endpoints:
            # 不提供认证信息
            response = client.get(endpoint)
            assert response.status_code == 401
            
            # 提供无效token
            headers = {"Authorization": "Bearer invalid_token"}
            response = client.get(endpoint, headers=headers)
            assert response.status_code == 401
    
    def test_privilege_escalation(self, client):
        """测试权限提升"""
        # 创建普通用户
        user_response = client.post("/api/v1/users", json={
            "email": "user@example.com",
            "password": "Password123!",
            "full_name": "Test User"
        })
        
        # 登录获取token
        login_response = client.post("/api/v1/auth/login", data={
            "username": "user@example.com",
            "password": "Password123!"
        })
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 尝试访问管理员接口
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/cases",
            "/api/v1/admin/settings"
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=headers)
            assert response.status_code == 403  # 应该被拒绝
    
    def test_file_upload_security(self, client):
        """测试文件上传安全"""
        # 恶意文件内容
        malicious_files = [
            ("malicious.php", b"<?php system($_GET['cmd']); ?>", "application/x-php"),
            ("malicious.js", b"<script>alert('XSS')</script>", "application/javascript"),
            ("malicious.html", b"<html><script>alert('XSS')</script></html>", "text/html")
        ]
        
        for filename, content, content_type in malicious_files:
            files = {"file": (filename, content, content_type)}
            response = client.post("/api/v1/files/upload", files=files)
            
            # 应该拒绝恶意文件
            assert response.status_code in [400, 422]
```

### 渗透测试脚本
```python
# scripts/security_scan.py
import requests
import sys
from urllib.parse import urljoin

class SecurityScanner:
    """安全扫描器"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.vulnerabilities = []
    
    def scan_all(self):
        """执行所有安全扫描"""
        print("开始安全扫描...")
        
        self.scan_sql_injection()
        self.scan_xss()
        self.scan_directory_traversal()
        self.scan_sensitive_files()
        
        self.report_results()
    
    def scan_sql_injection(self):
        """扫描SQL注入漏洞"""
        print("扫描SQL注入漏洞...")
        
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT 1,2,3 --"
        ]
        
        test_endpoints = [
            "/api/v1/users/search?q={}",
            "/api/v1/cases?search={}"
        ]
        
        for endpoint_template in test_endpoints:
            for payload in sql_payloads:
                url = urljoin(self.base_url, endpoint_template.format(payload))
                
                try:
                    response = self.session.get(url, timeout=10)
                    
                    # 检查是否有SQL错误信息泄露
                    error_indicators = [
                        "sql", "mysql", "postgresql", "oracle",
                        "syntax error", "database error"
                    ]
                    
                    response_text = response.text.lower()
                    for indicator in error_indicators:
                        if indicator in response_text:
                            self.vulnerabilities.append({
                                "type": "SQL Injection",
                                "url": url,
                                "payload": payload,
                                "severity": "High"
                            })
                            break
                
                except requests.RequestException:
                    continue
    
    def scan_xss(self):
        """扫描XSS漏洞"""
        print("扫描XSS漏洞...")
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')"
        ]
        
        # 测试反射型XSS
        for payload in xss_payloads:
            url = urljoin(self.base_url, f"/search?q={payload}")
            
            try:
                response = self.session.get(url, timeout=10)
                
                if payload in response.text:
                    self.vulnerabilities.append({
                        "type": "Reflected XSS",
                        "url": url,
                        "payload": payload,
                        "severity": "Medium"
                    })
            
            except requests.RequestException:
                continue
    
    def scan_directory_traversal(self):
        """扫描目录遍历漏洞"""
        print("扫描目录遍历漏洞...")
        
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc/passwd"
        ]
        
        for payload in traversal_payloads:
            url = urljoin(self.base_url, f"/api/v1/files/{payload}")
            
            try:
                response = self.session.get(url, timeout=10)
                
                # 检查是否返回了系统文件内容
                if "root:" in response.text or "localhost" in response.text:
                    self.vulnerabilities.append({
                        "type": "Directory Traversal",
                        "url": url,
                        "payload": payload,
                        "severity": "High"
                    })
            
            except requests.RequestException:
                continue
    
    def scan_sensitive_files(self):
        """扫描敏感文件暴露"""
        print("扫描敏感文件...")
        
        sensitive_files = [
            ".env",
            "config.py",
            "database.py",
            ".git/config",
            "backup.sql",
            "admin.php"
        ]
        
        for file_path in sensitive_files:
            url = urljoin(self.base_url, file_path)
            
            try:
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    self.vulnerabilities.append({
                        "type": "Sensitive File Exposure",
                        "url": url,
                        "severity": "Medium"
                    })
            
            except requests.RequestException:
                continue
    
    def report_results(self):
        """报告扫描结果"""
        print("\n" + "="*50)
        print("安全扫描结果")
        print("="*50)
        
        if not self.vulnerabilities:
            print("✅ 未发现安全漏洞")
            return
        
        # 按严重程度分组
        high_severity = [v for v in self.vulnerabilities if v["severity"] == "High"]
        medium_severity = [v for v in self.vulnerabilities if v["severity"] == "Medium"]
        
        if high_severity:
            print(f"\n🚨 高危漏洞 ({len(high_severity)}个):")
            for vuln in high_severity:
                print(f"  - {vuln['type']}: {vuln['url']}")
        
        if medium_severity:
            print(f"\n⚠️  中危漏洞 ({len(medium_severity)}个):")
            for vuln in medium_severity:
                print(f"  - {vuln['type']}: {vuln['url']}")
        
        print(f"\n总计发现 {len(self.vulnerabilities)} 个安全问题")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python security_scan.py <base_url>")
        sys.exit(1)
    
    base_url = sys.argv[1]
    scanner = SecurityScanner(base_url)
    scanner.scan_all()
```

## 📊 安全监控

### 安全事件监控
```python
# app/services/security_monitor.py
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
from app.core.security_logger import SecurityLogger
from app.models.security_log import SecurityLog

class SecurityMonitor:
    """安全监控服务"""
    
    def __init__(self):
        self.security_logger = SecurityLogger()
        self.alert_thresholds = {
            "failed_logins": 10,  # 10分钟内失败登录次数
            "permission_denied": 5,  # 10分钟内权限拒绝次数
            "suspicious_activity": 3  # 10分钟内可疑活动次数
        }
    
    async def monitor_security_events(self):
        """监控安全事件"""
        while True:
            try:
                await self._check_failed_logins()
                await self._check_permission_denials()
                await self._check_suspicious_activities()
                await self._check_brute_force_attacks()
                
                # 每分钟检查一次
                await asyncio.sleep(60)
                
            except Exception as e:
                self.security_logger.logger.error(f"Security monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _check_failed_logins(self):
        """检查失败登录"""
        time_threshold = datetime.utcnow() - timedelta(minutes=10)
        
        # 查询最近10分钟的失败登录
        failed_logins = await self._query_security_logs(
            event_type="login_failure",
            since=time_threshold
        )
        
        # 按IP地址分组
        ip_failures = {}
        for log in failed_logins:
            ip = log.ip_address
            if ip not in ip_failures:
                ip_failures[ip] = []
            ip_failures[ip].append(log)
        
        # 检查是否超过阈值
        for ip, failures in ip_failures.items():
            if len(failures) >= self.alert_thresholds["failed_logins"]:
                await self._trigger_security_alert(
                    "Excessive failed logins",
                    f"IP {ip} has {len(failures)} failed login attempts in 10 minutes",
                    "high",
                    {"ip_address": ip, "failure_count": len(failures)}
                )
    
    async def _check_brute_force_attacks(self):
        """检查暴力破解攻击"""
        time_threshold = datetime.utcnow() - timedelta(minutes=5)
        
        # 查询最近5分钟的失败登录
        recent_failures = await self._query_security_logs(
            event_type="login_failure",
            since=time_threshold
        )
        
        # 按用户邮箱分组
        email_failures = {}
        for log in recent_failures:
            email = log.user_email
            if email not in email_failures:
                email_failures[email] = []
            email_failures[email].append(log)
        
        # 检查单个账户的失败次数
        for email, failures in email_failures.items():
            if len(failures) >= 5:  # 5分钟内5次失败
                await self._trigger_account_lockout(email)
                
                await self._trigger_security_alert(
                    "Possible brute force attack",
                    f"Account {email} has {len(failures)} failed login attempts in 5 minutes",
                    "critical",
                    {"user_email": email, "failure_count": len(failures)}
                )
    
    async def _trigger_account_lockout(self, email: str):
        """触发账户锁定"""
        # 锁定账户30分钟
        lockout_until = datetime.utcnow() + timedelta(minutes=30)
        
        # 更新用户表，设置锁定状态
        # await self.user_service.lock_account(email, lockout_until)
        
        self.security_logger.log_suspicious_activity(
            f"Account locked due to brute force attempt: {email}"
        )
    
    async def _trigger_security_alert(self, title: str, description: str, severity: str, metadata: Dict):
        """触发安全告警"""
        alert_data = {
            "title": title,
            "description": description,
            "severity": severity,
            "timestamp": datetime.utcnow(),
            "metadata": metadata
        }
        
        # 发送告警通知
        await self._send_security_notification(alert_data)
        
        # 记录告警日志
        self.security_logger.log_suspicious_activity(
            f"Security alert: {title} - {description}"
        )
    
    async def _send_security_notification(self, alert_data: Dict):
        """发送安全通知"""
        # 发送邮件通知
        # await self.email_service.send_security_alert(alert_data)
        
        # 发送Slack/钉钉通知
        # await self.notification_service.send_alert(alert_data)
        
        # 记录到监控系统
        # await self.monitoring_service.record_alert(alert_data)
        pass
```

## 🚨 应急响应

### 安全事件响应流程
```python
# app/services/incident_response.py
from enum import Enum
from datetime import datetime
from typing import List, Dict, Optional

class IncidentSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentStatus(Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    CLOSED = "closed"

class SecurityIncidentResponse:
    """安全事件响应服务"""
    
    def __init__(self):
        self.response_team = [
            "security@lawsker.com",
            "devops@lawsker.com",
            "cto@lawsker.com"
        ]
    
    async def handle_security_incident(self, incident_type: str, description: str, 
                                     severity: IncidentSeverity, metadata: Dict = None):
        """处理安全事件"""
        # 1. 创建事件记录
        incident = await self._create_incident_record(
            incident_type, description, severity, metadata
        )
        
        # 2. 立即响应措施
        await self._immediate_response(incident)
        
        # 3. 通知响应团队
        await self._notify_response_team(incident)
        
        # 4. 根据严重程度执行相应措施
        if severity == IncidentSeverity.CRITICAL:
            await self._handle_critical_incident(incident)
        elif severity == IncidentSeverity.HIGH:
            await self._handle_high_incident(incident)
        
        return incident
    
    async def _immediate_response(self, incident: Dict):
        """立即响应措施"""
        incident_type = incident["type"]
        
        if incident_type == "data_breach":
            # 数据泄露响应
            await self._isolate_affected_systems()
            await self._preserve_evidence()
            
        elif incident_type == "brute_force_attack":
            # 暴力破解攻击响应
            await self._block_malicious_ips(incident["metadata"].get("ip_addresses", []))
            await self._lock_targeted_accounts(incident["metadata"].get("user_emails", []))
            
        elif incident_type == "sql_injection":
            # SQL注入攻击响应
            await self._enable_waf_protection()
            await self._review_database_logs()
            
        elif incident_type == "ddos_attack":
            # DDoS攻击响应
            await self._enable_ddos_protection()
            await self._scale_infrastructure()
    
    async def _handle_critical_incident(self, incident: Dict):
        """处理严重安全事件"""
        # 1. 立即通知所有相关人员
        await self._emergency_notification(incident)
        
        # 2. 激活事件响应团队
        await self._activate_incident_response_team()
        
        # 3. 考虑系统隔离
        if incident["type"] in ["data_breach", "ransomware"]:
            await self._consider_system_isolation(incident)
        
        # 4. 联系法律和合规团队
        await self._notify_legal_compliance_team(incident)
        
        # 5. 准备公关声明
        await self._prepare_public_statement(incident)
    
    async def _block_malicious_ips(self, ip_addresses: List[str]):
        """封禁恶意IP"""
        for ip in ip_addresses:
            # 添加到防火墙黑名单
            # await self.firewall_service.block_ip(ip)
            
            # 添加到WAF黑名单
            # await self.waf_service.block_ip(ip)
            
            # 记录封禁操作
            print(f"Blocked malicious IP: {ip}")
    
    async def _lock_targeted_accounts(self, user_emails: List[str]):
        """锁定被攻击的账户"""
        for email in user_emails:
            # 锁定账户
            # await self.user_service.lock_account(email)
            
            # 强制退出所有会话
            # await self.auth_service.revoke_all_sessions(email)
            
            # 发送安全通知
            # await self.email_service.send_security_notification(email)
            
            print(f"Locked targeted account: {email}")
    
    async def _preserve_evidence(self):
        """保存证据"""
        # 1. 创建系统快照
        # await self.backup_service.create_emergency_snapshot()
        
        # 2. 导出相关日志
        # await self.log_service.export_security_logs()
        
        # 3. 保存网络流量数据
        # await self.network_service.capture_traffic_dump()
        
        print("Evidence preservation completed")
    
    async def _emergency_notification(self, incident: Dict):
        """紧急通知"""
        notification_message = f"""
        🚨 CRITICAL SECURITY INCIDENT 🚨
        
        Type: {incident['type']}
        Severity: {incident['severity']}
        Time: {incident['timestamp']}
        
        Description: {incident['description']}
        
        Immediate action required!
        """
        
        # 发送紧急通知到所有渠道
        for contact in self.response_team:
            # await self.notification_service.send_emergency_alert(contact, notification_message)
            print(f"Emergency notification sent to: {contact}")
```

### 安全事件恢复计划
```python
# scripts/security_recovery.py
import asyncio
from datetime import datetime
from typing import List, Dict

class SecurityRecoveryPlan:
    """安全事件恢复计划"""
    
    def __init__(self):
        self.recovery_steps = []
        self.rollback_steps = []
    
    async def execute_recovery_plan(self, incident_type: str):
        """执行恢复计划"""
        print(f"开始执行安全恢复计划: {incident_type}")
        
        if incident_type == "data_breach":
            await self._recover_from_data_breach()
        elif incident_type == "ransomware":
            await self._recover_from_ransomware()
        elif incident_type == "system_compromise":
            await self._recover_from_system_compromise()
        
        print("安全恢复计划执行完成")
    
    async def _recover_from_data_breach(self):
        """数据泄露恢复"""
        steps = [
            "1. 确认泄露范围",
            "2. 修复安全漏洞",
            "3. 重置受影响用户密码",
            "4. 更新安全策略",
            "5. 加强监控",
            "6. 通知用户和监管机构"
        ]
        
        for step in steps:
            print(f"执行: {step}")
            await asyncio.sleep(1)  # 模拟执行时间
    
    async def _recover_from_system_compromise(self):
        """系统入侵恢复"""
        steps = [
            "1. 隔离受感染系统",
            "2. 分析攻击向量",
            "3. 清除恶意软件",
            "4. 修复系统漏洞",
            "5. 从备份恢复数据",
            "6. 重新部署系统",
            "7. 加强安全配置",
            "8. 恢复服务"
        ]
        
        for step in steps:
            print(f"执行: {step}")
            await asyncio.sleep(2)  # 模拟执行时间
```

---

**文档版本**: v1.0
**最后更新**: 2024-01-30
**维护团队**: 安全团队

**重要提醒**: 安全是一个持续的过程，需要定期更新和改进。请确保所有开发人员都熟悉并遵循本指南中的安全实践。