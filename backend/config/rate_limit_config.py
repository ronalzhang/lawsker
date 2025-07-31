"""
API限流配置
定义不同API端点的限流策略
"""

# 默认限流配置
DEFAULT_RATE_LIMIT = "100/hour"

# 特定路径的限流规则
RATE_LIMIT_RULES = {
    # 认证相关API - 更严格的限流
    "/api/v1/auth/login": "10/minute",
    "/api/v1/auth/register": "5/minute",
    "/api/v1/auth/forgot-password": "3/minute",
    "/api/v1/auth/reset-password": "3/minute",
    "/api/v1/auth/send-sms-code": "5/minute",
    "/api/v1/auth/verify-sms-code": "10/minute",
    
    # 敏感操作API
    "/api/v1/auth/change-password": "3/minute",
    "/api/v1/admin": "50/hour",
    
    # 文件上传API
    "/api/v1/upload": "20/hour",
    
    # 搜索API
    "/api/v1/search": "200/hour",
    
    # 数据导出API
    "/api/v1/export": "10/hour",
    
    # 公开API - 相对宽松
    "/api/v1/public": "500/hour",
    
    # WebSocket连接
    "/api/v1/ws": "10/minute",
}

# IP白名单 - 这些IP不受限流限制
IP_WHITELIST = [
    "127.0.0.1",
    "::1",
    # 可以添加内部服务器IP
    # "10.0.0.1",
    # "192.168.1.100",
]

# IP黑名单 - 这些IP直接拒绝访问
IP_BLACKLIST = [
    # 可以添加已知的恶意IP
    # "192.168.1.200",
]

# 可疑行为检测配置
SUSPICIOUS_BEHAVIOR_CONFIG = {
    "high_frequency": {
        "threshold": 20,  # 1分钟内超过20次请求
        "window": 60,
        "action": "log"  # log, block, temp_block
    },
    "error_rate": {
        "threshold": 0.7,  # 5分钟内错误率超过70%
        "window": 300,
        "min_requests": 10,  # 最少请求数
        "action": "temp_block"
    },
    "path_scanning": {
        "threshold": 30,  # 10分钟内访问超过30个不同路径
        "window": 600,
        "action": "temp_block"
    },
    "user_agent_anomaly": {
        "suspicious_patterns": [
            "bot", "crawler", "spider", "scraper",
            "python-requests", "curl", "wget"
        ],
        "action": "log"
    }
}

# 自适应限流配置
ADAPTIVE_LIMITING_CONFIG = {
    "enabled": True,
    "cpu_threshold": 80,      # CPU使用率超过80%时启用
    "memory_threshold": 85,   # 内存使用率超过85%时启用
    "response_time_threshold": 2.0,  # 平均响应时间超过2秒时启用
    "error_rate_threshold": 0.1,     # 错误率超过10%时启用
    "adjustment_factor": 0.5,        # 限流调整因子
    "check_interval": 60             # 检查间隔（秒）
}

# Redis配置
REDIS_CONFIG = {
    "url": "redis://localhost:6379/1",  # 使用数据库1存储限流数据
    "max_connections": 20,
    "retry_on_timeout": True,
    "socket_keepalive": True,
    "socket_keepalive_options": {},
    "health_check_interval": 30
}

# 限流响应配置
RATE_LIMIT_RESPONSE_CONFIG = {
    "include_headers": True,
    "custom_message": "请求过于频繁，请稍后再试",
    "retry_after_header": True,
    "detailed_error": False  # 生产环境建议设为False
}

# 日志配置
LOGGING_CONFIG = {
    "log_all_requests": False,      # 是否记录所有请求
    "log_blocked_requests": True,   # 是否记录被阻止的请求
    "log_suspicious_behavior": True, # 是否记录可疑行为
    "retention_days": 7,            # 日志保留天数
    "max_log_entries": 100000       # 最大日志条目数
}

# 性能配置
PERFORMANCE_CONFIG = {
    "use_lua_scripts": True,        # 使用Lua脚本优化Redis操作
    "batch_operations": True,       # 批量操作
    "async_logging": True,          # 异步日志记录
    "cache_rate_limits": True,      # 缓存限流配置
    "cache_ttl": 300               # 缓存TTL（秒）
}