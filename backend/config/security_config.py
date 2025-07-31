"""
安全配置文件
集中管理所有安全相关的配置
"""
import os
from typing import Dict, List, Any
from pydantic import BaseSettings, validator

class SecuritySettings(BaseSettings):
    """安全设置"""
    
    # 基础安全设置
    SECRET_KEY: str
    ENCRYPTION_MASTER_KEY: str
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # HTTPS设置
    FORCE_HTTPS: bool = True
    SSL_CERT_FILE: str = ""
    SSL_KEY_FILE: str = ""
    
    # CORS设置
    ALLOWED_ORIGINS: List[str] = ["https://lawsker.com", "https://admin.lawsker.com"]
    ALLOWED_HOSTS: List[str] = ["lawsker.com", "admin.lawsker.com", "localhost", "127.0.0.1"]
    
    # 限流设置
    RATE_LIMIT_PER_MINUTE: int = 60
    LOGIN_RATE_LIMIT: int = 5
    REGISTER_RATE_LIMIT: int = 3
    
    # 会话设置
    SESSION_TIMEOUT: int = 3600  # 1小时
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "strict"
    
    # 密码策略
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    PASSWORD_MAX_AGE_DAYS: int = 90
    
    # 文件上传安全
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [
        "image/jpeg", "image/png", "image/gif",
        "application/pdf", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    UPLOAD_SCAN_MALWARE: bool = True
    
    # 数据库安全
    DB_SSL_REQUIRED: bool = True
    DB_CONNECTION_TIMEOUT: int = 30
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # Redis安全
    REDIS_PASSWORD: str = ""
    REDIS_SSL: bool = False
    REDIS_TIMEOUT: int = 5
    
    # 日志安全
    LOG_SENSITIVE_DATA: bool = False
    LOG_RETENTION_DAYS: int = 90
    SECURITY_LOG_LEVEL: str = "INFO"
    
    # 监控和告警
    ENABLE_SECURITY_MONITORING: bool = True
    ALERT_ON_FAILED_LOGINS: int = 5
    ALERT_ON_SUSPICIOUS_ACTIVITY: bool = True
    
    # 加密设置
    FIELD_ENCRYPTION_ENABLED: bool = True
    KEY_ROTATION_INTERVAL_DAYS: int = 7
    BACKUP_KEY_RETENTION_DAYS: int = 30
    
    # API安全
    API_KEY_REQUIRED: bool = False
    API_RATE_LIMIT: int = 1000  # 每小时
    API_VERSION_HEADER: str = "X-API-Version"
    
    # 内容安全策略
    CSP_SCRIPT_SRC: List[str] = ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"]
    CSP_STYLE_SRC: List[str] = ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"]
    CSP_IMG_SRC: List[str] = ["'self'", "data:", "https:", "blob:"]
    CSP_CONNECT_SRC: List[str] = ["'self'", "wss:", "ws:"]
    
    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters long')
        return v
    
    @validator('ENCRYPTION_MASTER_KEY')
    def validate_encryption_key(cls, v):
        if len(v) < 32:
            raise ValueError('ENCRYPTION_MASTER_KEY must be at least 32 characters long')
        return v
    
    @validator('ENVIRONMENT')
    def validate_environment(cls, v):
        if v not in ['development', 'testing', 'staging', 'production']:
            raise ValueError('ENVIRONMENT must be one of: development, testing, staging, production')
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 安全配置实例
security_settings = SecuritySettings()

# 安全响应头配置
SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": (
        "geolocation=(), microphone=(), camera=(), payment=(), "
        "usb=(), magnetometer=(), gyroscope=(), speaker=()"
    ),
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0"
}

# CSP策略配置
def build_csp_policy() -> str:
    """构建内容安全策略"""
    policy_parts = [
        "default-src 'self'",
        f"script-src {' '.join(security_settings.CSP_SCRIPT_SRC)}",
        f"style-src {' '.join(security_settings.CSP_STYLE_SRC)}",
        f"img-src {' '.join(security_settings.CSP_IMG_SRC)}",
        f"connect-src {' '.join(security_settings.CSP_CONNECT_SRC)}",
        "font-src 'self' https://fonts.gstatic.com",
        "media-src 'self'",
        "object-src 'none'",
        "child-src 'none'",
        "frame-src 'none'",
        "worker-src 'self'",
        "manifest-src 'self'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "upgrade-insecure-requests"
    ]
    
    return "; ".join(policy_parts)

# 输入验证规则
INPUT_VALIDATION_RULES = {
    "username": {
        "pattern": r"^[a-zA-Z0-9_-]{3,50}$",
        "min_length": 3,
        "max_length": 50,
        "description": "Username must be 3-50 characters, alphanumeric, underscore, or dash"
    },
    "email": {
        "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "max_length": 254,
        "description": "Valid email address required"
    },
    "password": {
        "min_length": security_settings.PASSWORD_MIN_LENGTH,
        "max_length": 128,
        "require_uppercase": security_settings.PASSWORD_REQUIRE_UPPERCASE,
        "require_lowercase": security_settings.PASSWORD_REQUIRE_LOWERCASE,
        "require_digits": security_settings.PASSWORD_REQUIRE_DIGITS,
        "require_special": security_settings.PASSWORD_REQUIRE_SPECIAL,
        "description": "Password must meet complexity requirements"
    },
    "phone": {
        "pattern": r"^1[3-9]\d{9}$",
        "description": "Valid Chinese mobile phone number"
    },
    "id_card": {
        "pattern": r"^[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$",
        "description": "Valid Chinese ID card number"
    }
}

# 危险内容检测模式
DANGEROUS_PATTERNS = [
    # SQL注入模式
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
    r"(--|#|/\*|\*/)",
    r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
    
    # XSS模式
    r"(<script[^>]*>.*?</script>)",
    r"(javascript\s*:)",
    r"(on\w+\s*=)",
    r"(<iframe[^>]*>)",
    r"(<object[^>]*>)",
    r"(<embed[^>]*>)",
    
    # 路径遍历模式
    r"(\.\./|\.\.\\)",
    r"(/etc/passwd|/etc/shadow)",
    r"(\\windows\\system32)",
    
    # 命令注入模式
    r"(;|\||&|`|\$\(|\$\{)",
    r"(\b(cat|ls|pwd|whoami|id|uname)\b)",
]

# 敏感端点配置
SENSITIVE_ENDPOINTS = {
    "/api/v1/auth/login": {
        "rate_limit": security_settings.LOGIN_RATE_LIMIT,
        "require_csrf": True,
        "log_attempts": True
    },
    "/api/v1/auth/register": {
        "rate_limit": security_settings.REGISTER_RATE_LIMIT,
        "require_csrf": True,
        "log_attempts": True
    },
    "/api/v1/auth/reset-password": {
        "rate_limit": 2,
        "require_csrf": True,
        "log_attempts": True
    },
    "/api/v1/admin/*": {
        "rate_limit": 30,
        "require_admin": True,
        "log_access": True
    },
    "/api/v1/users/profile": {
        "rate_limit": 20,
        "require_auth": True,
        "mask_response": True
    }
}

# 文件上传安全配置
FILE_UPLOAD_CONFIG = {
    "max_size": security_settings.MAX_FILE_SIZE,
    "allowed_types": security_settings.ALLOWED_FILE_TYPES,
    "scan_malware": security_settings.UPLOAD_SCAN_MALWARE,
    "quarantine_suspicious": True,
    "allowed_extensions": [
        ".jpg", ".jpeg", ".png", ".gif",
        ".pdf", ".doc", ".docx"
    ],
    "forbidden_extensions": [
        ".exe", ".bat", ".cmd", ".com", ".pif", ".scr",
        ".vbs", ".js", ".jar", ".php", ".asp", ".jsp"
    ]
}

# 数据库安全配置
DATABASE_SECURITY_CONFIG = {
    "ssl_required": security_settings.DB_SSL_REQUIRED,
    "connection_timeout": security_settings.DB_CONNECTION_TIMEOUT,
    "pool_size": security_settings.DB_POOL_SIZE,
    "max_overflow": security_settings.DB_MAX_OVERFLOW,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
    "echo": False,  # 生产环境不输出SQL
    "isolation_level": "READ_COMMITTED"
}

# Redis安全配置
REDIS_SECURITY_CONFIG = {
    "password": security_settings.REDIS_PASSWORD,
    "ssl": security_settings.REDIS_SSL,
    "socket_timeout": security_settings.REDIS_TIMEOUT,
    "socket_connect_timeout": security_settings.REDIS_TIMEOUT,
    "retry_on_timeout": True,
    "health_check_interval": 30,
    "max_connections": 50
}

# 监控和告警配置
MONITORING_CONFIG = {
    "enable_security_monitoring": security_settings.ENABLE_SECURITY_MONITORING,
    "alert_on_failed_logins": security_settings.ALERT_ON_FAILED_LOGINS,
    "alert_on_suspicious_activity": security_settings.ALERT_ON_SUSPICIOUS_ACTIVITY,
    "log_retention_days": security_settings.LOG_RETENTION_DAYS,
    "security_log_level": security_settings.SECURITY_LOG_LEVEL,
    "alert_channels": ["email", "webhook"],
    "alert_thresholds": {
        "failed_logins_per_minute": 10,
        "suspicious_requests_per_minute": 20,
        "error_rate_threshold": 0.05
    }
}

# 加密配置
ENCRYPTION_CONFIG = {
    "field_encryption_enabled": security_settings.FIELD_ENCRYPTION_ENABLED,
    "key_rotation_interval_days": security_settings.KEY_ROTATION_INTERVAL_DAYS,
    "backup_key_retention_days": security_settings.BACKUP_KEY_RETENTION_DAYS,
    "encryption_algorithm": "AES-256-GCM",
    "key_derivation_iterations": 100000,
    "encrypted_fields": [
        "full_name",
        "id_card_number",
        "lawyer_name",
        "phone_number",
        "email"
    ]
}

# 会话安全配置
SESSION_CONFIG = {
    "timeout": security_settings.SESSION_TIMEOUT,
    "cookie_secure": security_settings.SESSION_COOKIE_SECURE,
    "cookie_httponly": security_settings.SESSION_COOKIE_HTTPONLY,
    "cookie_samesite": security_settings.SESSION_COOKIE_SAMESITE,
    "regenerate_on_login": True,
    "invalidate_on_logout": True,
    "track_ip_changes": True,
    "max_concurrent_sessions": 3
}

def get_security_config() -> Dict[str, Any]:
    """获取完整的安全配置"""
    return {
        "settings": security_settings.dict(),
        "headers": SECURITY_HEADERS,
        "csp_policy": build_csp_policy(),
        "input_validation": INPUT_VALIDATION_RULES,
        "dangerous_patterns": DANGEROUS_PATTERNS,
        "sensitive_endpoints": SENSITIVE_ENDPOINTS,
        "file_upload": FILE_UPLOAD_CONFIG,
        "database": DATABASE_SECURITY_CONFIG,
        "redis": REDIS_SECURITY_CONFIG,
        "monitoring": MONITORING_CONFIG,
        "encryption": ENCRYPTION_CONFIG,
        "session": SESSION_CONFIG
    }

def validate_security_config():
    """验证安全配置"""
    errors = []
    
    # 检查生产环境配置
    if security_settings.ENVIRONMENT == "production":
        if security_settings.DEBUG:
            errors.append("DEBUG must be False in production")
        
        if not security_settings.FORCE_HTTPS:
            errors.append("HTTPS must be enforced in production")
        
        if not security_settings.SSL_CERT_FILE:
            errors.append("SSL certificate must be configured in production")
        
        if not security_settings.DB_SSL_REQUIRED:
            errors.append("Database SSL must be required in production")
    
    # 检查密钥强度
    if len(security_settings.SECRET_KEY) < 32:
        errors.append("SECRET_KEY is too short")
    
    if len(security_settings.ENCRYPTION_MASTER_KEY) < 32:
        errors.append("ENCRYPTION_MASTER_KEY is too short")
    
    if errors:
        raise ValueError(f"Security configuration errors: {'; '.join(errors)}")
    
    return True