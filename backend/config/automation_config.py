"""
自动化运维配置管理
包含健康监控、告警自动化、部署等配置
"""
import os
from typing import Dict, List, Any, Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import validator
from pathlib import Path

class AutomationSettings(BaseSettings):
    """自动化运维设置"""
    
    # 健康监控配置
    HEALTH_CHECK_INTERVAL: int = 30  # 健康检查间隔（秒）
    HEALTH_CHECK_TIMEOUT: int = 10   # 健康检查超时（秒）
    HEALTH_MONITOR_ENABLED: bool = True
    
    # 数据库健康检查配置
    DB_HEALTH_CHECK_INTERVAL: int = 30
    DB_SLOW_QUERY_THRESHOLD: float = 1.0  # 慢查询阈值（秒）
    DB_CONNECTION_POOL_WARNING_THRESHOLD: float = 0.8  # 连接池使用率告警阈值
    
    # Redis健康检查配置
    REDIS_HEALTH_CHECK_INTERVAL: int = 30
    REDIS_PING_TIMEOUT: float = 0.1  # Redis ping超时阈值（秒）
    REDIS_HIT_RATE_WARNING_THRESHOLD: float = 80.0  # 命中率告警阈值（%）
    
    # 系统资源监控配置
    SYSTEM_HEALTH_CHECK_INTERVAL: int = 60
    CPU_WARNING_THRESHOLD: float = 80.0  # CPU使用率告警阈值（%）
    MEMORY_WARNING_THRESHOLD: float = 85.0  # 内存使用率告警阈值（%）
    DISK_WARNING_THRESHOLD: float = 90.0  # 磁盘使用率告警阈值（%）
    
    # 应用程序健康检查配置
    APP_HEALTH_CHECK_INTERVAL: int = 30
    APP_HEALTH_ENDPOINT: str = "http://localhost:8000/api/v1/health"
    APP_RESPONSE_TIME_WARNING_THRESHOLD: float = 2.0  # 响应时间告警阈值（秒）
    
    # 自愈配置
    SELF_HEALING_ENABLED: bool = True
    SELF_HEALING_MAX_ATTEMPTS: int = 3
    SELF_HEALING_COOLDOWN_MINUTES: int = 5
    
    # 告警自动化配置
    ALERT_AUTOMATION_ENABLED: bool = True
    ALERT_PROCESSING_INTERVAL: int = 10  # 告警处理间隔（秒）
    DEFAULT_RULE_COOLDOWN_MINUTES: int = 30
    DEFAULT_MAX_EXECUTIONS_PER_HOUR: int = 5
    
    # 部署配置
    DEPLOYMENT_ENABLED: bool = True
    DEPLOYMENT_BACKUP_ENABLED: bool = True
    DEPLOYMENT_ROLLBACK_ON_FAILURE: bool = True
    DEPLOYMENT_HEALTH_CHECK_TIMEOUT: int = 30
    
    # 备份配置
    BACKUP_ENABLED: bool = True
    BACKUP_STORAGE_PATH: str = "/backups"
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_COMPRESSION_ENABLED: bool = True
    BACKUP_ENCRYPTION_ENABLED: bool = True
    
    # 通知配置
    NOTIFICATION_ENABLED: bool = True
    NOTIFICATION_WEBHOOK_URL: Optional[str] = None
    NOTIFICATION_SLACK_CHANNEL: Optional[str] = None
    NOTIFICATION_EMAIL_ENABLED: bool = False
    NOTIFICATION_SMS_ENABLED: bool = False
    
    # 日志配置
    AUTOMATION_LOG_LEVEL: str = "INFO"
    AUTOMATION_LOG_FILE: str = "/var/log/lawsker/automation.log"
    AUTOMATION_LOG_MAX_SIZE: int = 100 * 1024 * 1024  # 100MB
    AUTOMATION_LOG_BACKUP_COUNT: int = 5
    
    # 安全配置
    AUTOMATION_API_KEY: Optional[str] = None
    AUTOMATION_ALLOWED_IPS: List[str] = ["127.0.0.1", "::1"]
    
    @validator('BACKUP_STORAGE_PATH')
    def validate_backup_path(cls, v):
        """验证备份路径"""
        path = Path(v)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        return str(path.absolute())
    
    @validator('CPU_WARNING_THRESHOLD', 'MEMORY_WARNING_THRESHOLD', 'DISK_WARNING_THRESHOLD')
    def validate_percentage_thresholds(cls, v):
        """验证百分比阈值"""
        if not 0 <= v <= 100:
            raise ValueError('Threshold must be between 0 and 100')
        return v
    
    @validator('HEALTH_CHECK_INTERVAL', 'ALERT_PROCESSING_INTERVAL')
    def validate_positive_intervals(cls, v):
        """验证正数间隔"""
        if v <= 0:
            raise ValueError('Interval must be positive')
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_prefix = "AUTOMATION_"

# 全局配置实例
automation_settings = AutomationSettings()

# 健康检查配置
HEALTH_CHECK_CONFIG = {
    "database": {
        "interval": automation_settings.DB_HEALTH_CHECK_INTERVAL,
        "slow_query_threshold": automation_settings.DB_SLOW_QUERY_THRESHOLD,
        "pool_warning_threshold": automation_settings.DB_CONNECTION_POOL_WARNING_THRESHOLD,
        "enabled": automation_settings.HEALTH_MONITOR_ENABLED
    },
    "redis": {
        "interval": automation_settings.REDIS_HEALTH_CHECK_INTERVAL,
        "ping_timeout": automation_settings.REDIS_PING_TIMEOUT,
        "hit_rate_threshold": automation_settings.REDIS_HIT_RATE_WARNING_THRESHOLD,
        "enabled": automation_settings.HEALTH_MONITOR_ENABLED
    },
    "system_resources": {
        "interval": automation_settings.SYSTEM_HEALTH_CHECK_INTERVAL,
        "cpu_threshold": automation_settings.CPU_WARNING_THRESHOLD,
        "memory_threshold": automation_settings.MEMORY_WARNING_THRESHOLD,
        "disk_threshold": automation_settings.DISK_WARNING_THRESHOLD,
        "enabled": automation_settings.HEALTH_MONITOR_ENABLED
    },
    "application": {
        "interval": automation_settings.APP_HEALTH_CHECK_INTERVAL,
        "endpoint": automation_settings.APP_HEALTH_ENDPOINT,
        "response_time_threshold": automation_settings.APP_RESPONSE_TIME_WARNING_THRESHOLD,
        "enabled": automation_settings.HEALTH_MONITOR_ENABLED
    }
}

# 自愈配置
SELF_HEALING_CONFIG = {
    "enabled": automation_settings.SELF_HEALING_ENABLED,
    "max_attempts": automation_settings.SELF_HEALING_MAX_ATTEMPTS,
    "cooldown_minutes": automation_settings.SELF_HEALING_COOLDOWN_MINUTES,
    "actions": {
        "database": [
            {
                "name": "restart_connection_pool",
                "description": "重启数据库连接池",
                "enabled": True
            }
        ],
        "redis": [
            {
                "name": "clear_connections",
                "description": "清理Redis连接",
                "enabled": True
            }
        ],
        "system_resources": [
            {
                "name": "cleanup_memory",
                "description": "清理系统内存",
                "enabled": True
            },
            {
                "name": "cleanup_disk",
                "description": "清理磁盘空间",
                "enabled": True
            }
        ],
        "application": [
            {
                "name": "restart_application",
                "description": "重启应用程序",
                "enabled": False  # 默认禁用，因为风险较高
            }
        ]
    }
}

# 告警自动化配置
ALERT_AUTOMATION_CONFIG = {
    "enabled": automation_settings.ALERT_AUTOMATION_ENABLED,
    "processing_interval": automation_settings.ALERT_PROCESSING_INTERVAL,
    "default_cooldown_minutes": automation_settings.DEFAULT_RULE_COOLDOWN_MINUTES,
    "default_max_executions_per_hour": automation_settings.DEFAULT_MAX_EXECUTIONS_PER_HOUR,
    "notification": {
        "enabled": automation_settings.NOTIFICATION_ENABLED,
        "webhook_url": automation_settings.NOTIFICATION_WEBHOOK_URL,
        "slack_channel": automation_settings.NOTIFICATION_SLACK_CHANNEL,
        "email_enabled": automation_settings.NOTIFICATION_EMAIL_ENABLED,
        "sms_enabled": automation_settings.NOTIFICATION_SMS_ENABLED
    }
}

# 部署配置
DEPLOYMENT_CONFIG = {
    "enabled": automation_settings.DEPLOYMENT_ENABLED,
    "backup_enabled": automation_settings.DEPLOYMENT_BACKUP_ENABLED,
    "rollback_on_failure": automation_settings.DEPLOYMENT_ROLLBACK_ON_FAILURE,
    "health_check_timeout": automation_settings.DEPLOYMENT_HEALTH_CHECK_TIMEOUT,
    "environments": {
        "staging": {
            "servers": ["staging.lawsker.com"],
            "database_url": os.getenv("STAGING_DATABASE_URL", "postgresql://user:pass@staging-db:5432/lawsker"),
            "redis_url": os.getenv("STAGING_REDIS_URL", "redis://staging-redis:6379/0"),
            "backup_retention_days": 7,
            "deployment_strategy": "blue_green"
        },
        "production": {
            "servers": ["prod1.lawsker.com", "prod2.lawsker.com"],
            "database_url": os.getenv("PRODUCTION_DATABASE_URL", "postgresql://user:pass@prod-db:5432/lawsker"),
            "redis_url": os.getenv("PRODUCTION_REDIS_URL", "redis://prod-redis:6379/0"),
            "backup_retention_days": 30,
            "deployment_strategy": "rolling"
        }
    }
}

# 备份配置
BACKUP_CONFIG = {
    "enabled": automation_settings.BACKUP_ENABLED,
    "storage_path": automation_settings.BACKUP_STORAGE_PATH,
    "retention_days": automation_settings.BACKUP_RETENTION_DAYS,
    "compression": automation_settings.BACKUP_COMPRESSION_ENABLED,
    "encryption": automation_settings.BACKUP_ENCRYPTION_ENABLED,
    "schedule": {
        "daily_backup_time": "02:00",  # 每天凌晨2点
        "weekly_backup_day": "sunday",  # 每周日
        "monthly_backup_day": 1  # 每月1号
    }
}

# 监控配置
MONITORING_CONFIG = {
    "metrics": {
        "enabled": True,
        "collection_interval": 60,  # 秒
        "retention_days": 30
    },
    "alerts": {
        "enabled": True,
        "channels": ["webhook", "log"],
        "severity_levels": ["info", "warning", "critical"]
    },
    "dashboards": {
        "enabled": True,
        "refresh_interval": 30,  # 秒
        "auto_refresh": True
    }
}

# 安全配置
SECURITY_CONFIG = {
    "api_authentication": {
        "enabled": True,
        "api_key": automation_settings.AUTOMATION_API_KEY,
        "allowed_ips": automation_settings.AUTOMATION_ALLOWED_IPS
    },
    "encryption": {
        "enabled": True,
        "algorithm": "AES-256-GCM",
        "key_rotation_days": 90
    },
    "audit": {
        "enabled": True,
        "log_all_actions": True,
        "retention_days": 365
    }
}

def get_automation_config() -> Dict[str, Any]:
    """获取完整的自动化配置"""
    return {
        "settings": automation_settings.dict(),
        "health_check": HEALTH_CHECK_CONFIG,
        "self_healing": SELF_HEALING_CONFIG,
        "alert_automation": ALERT_AUTOMATION_CONFIG,
        "deployment": DEPLOYMENT_CONFIG,
        "backup": BACKUP_CONFIG,
        "monitoring": MONITORING_CONFIG,
        "security": SECURITY_CONFIG
    }

def validate_config() -> List[str]:
    """验证配置有效性"""
    errors = []
    
    # 检查必要的目录
    backup_path = Path(automation_settings.BACKUP_STORAGE_PATH)
    if not backup_path.exists():
        try:
            backup_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create backup directory: {str(e)}")
    
    # 检查日志目录
    log_path = Path(automation_settings.AUTOMATION_LOG_FILE).parent
    if not log_path.exists():
        try:
            log_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create log directory: {str(e)}")
    
    # 检查网络连接
    if automation_settings.NOTIFICATION_WEBHOOK_URL:
        try:
            import requests
            response = requests.get(automation_settings.NOTIFICATION_WEBHOOK_URL, timeout=5)
            if response.status_code >= 400:
                errors.append(f"Webhook URL is not accessible: {response.status_code}")
        except Exception as e:
            errors.append(f"Cannot access webhook URL: {str(e)}")
    
    return errors

def update_config(updates: Dict[str, Any]) -> bool:
    """更新配置"""
    try:
        global automation_settings
        
        # 更新设置
        for key, value in updates.items():
            if hasattr(automation_settings, key):
                setattr(automation_settings, key, value)
        
        # 验证更新后的配置
        errors = validate_config()
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update configuration: {str(e)}")
        return False

# 在模块加载时验证配置
if __name__ != "__main__":
    config_errors = validate_config()
    if config_errors:
        import warnings
        warnings.warn(f"Configuration validation warnings: {'; '.join(config_errors)}")