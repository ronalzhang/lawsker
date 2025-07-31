"""
告警系统配置
"""

from typing import List, Dict, Optional
from pydantic import BaseSettings, Field


class AlertConfig(BaseSettings):
    """告警配置"""
    
    # 基础配置
    ALERT_ENABLED: bool = Field(True, description="是否启用告警系统")
    ALERT_BATCH_SIZE: int = Field(100, description="批量处理告警数量")
    ALERT_BATCH_TIMEOUT: int = Field(5, description="批量处理超时时间(秒)")
    ALERT_HISTORY_LIMIT: int = Field(1000, description="内存中保存的告警历史数量")
    
    # 邮件通知配置
    SMTP_HOST: Optional[str] = Field(None, description="SMTP服务器地址")
    SMTP_PORT: int = Field(587, description="SMTP服务器端口")
    SMTP_USER: Optional[str] = Field(None, description="SMTP用户名")
    SMTP_PASSWORD: Optional[str] = Field(None, description="SMTP密码")
    SMTP_USE_TLS: bool = Field(True, description="是否使用TLS")
    ALERT_FROM_EMAIL: Optional[str] = Field(None, description="告警发送邮箱")
    
    # 邮件收件人配置
    ALERT_EMAIL_CRITICAL: List[str] = Field([], description="严重告警邮件收件人")
    ALERT_EMAIL_WARNING: List[str] = Field([], description="警告告警邮件收件人")
    ALERT_EMAIL_INFO: List[str] = Field([], description="信息告警邮件收件人")
    
    # 短信通知配置
    SMS_API_URL: Optional[str] = Field(None, description="短信API地址")
    SMS_API_KEY: Optional[str] = Field(None, description="短信API密钥")
    ALERT_SMS_PHONES: List[str] = Field([], description="告警短信收件人")
    
    # 钉钉通知配置
    DINGTALK_WEBHOOK_URL: Optional[str] = Field(None, description="钉钉Webhook地址")
    DINGTALK_SECRET: Optional[str] = Field(None, description="钉钉签名密钥")
    
    # Slack通知配置
    SLACK_WEBHOOK_URL: Optional[str] = Field(None, description="Slack Webhook地址")
    
    # 企业微信通知配置
    WECHAT_WEBHOOK_URL: Optional[str] = Field(None, description="企业微信Webhook地址")
    
    # 告警去重配置
    ALERT_DEDUP_WINDOW: int = Field(300, description="告警去重时间窗口(秒)")
    ALERT_SILENCE_DEFAULT_DURATION: int = Field(60, description="默认静默时长(分钟)")
    
    # 告警升级配置
    ALERT_ESCALATION_ENABLED: bool = Field(False, description="是否启用告警升级")
    ALERT_ESCALATION_TIMEOUT: int = Field(1800, description="告警升级超时时间(秒)")
    
    # 告警抑制配置
    ALERT_INHIBIT_RULES: List[Dict] = Field([], description="告警抑制规则")
    
    # 通知限流配置
    NOTIFICATION_RATE_LIMIT: Dict[str, int] = Field(
        {
            "email": 10,    # 每分钟最多10封邮件
            "sms": 5,       # 每分钟最多5条短信
            "webhook": 100  # 每分钟最多100个webhook
        },
        description="通知限流配置"
    )
    
    # 告警模板配置
    ALERT_TEMPLATES: Dict[str, str] = Field(
        {
            "email_subject": "[Lawsker告警] {alert_name} - {severity}",
            "sms_template": "【Lawsker告警】{alert_name}\n级别: {severity}\n服务: {service}\n消息: {message}",
            "webhook_template": "告警: {alert_name}\n级别: {severity}\n消息: {message}"
        },
        description="告警模板配置"
    )
    
    # 告警标签配置
    ALERT_LABELS: Dict[str, str] = Field(
        {
            "environment": "production",
            "cluster": "lawsker-main",
            "team": "platform"
        },
        description="默认告警标签"
    )
    
    # 告警路由配置
    ALERT_ROUTING_RULES: List[Dict] = Field(
        [
            {
                "match": {"severity": "critical"},
                "channels": ["email", "sms", "webhook"],
                "continue": True
            },
            {
                "match": {"severity": "warning"},
                "channels": ["email", "webhook"],
                "continue": True
            },
            {
                "match": {"severity": "info"},
                "channels": ["webhook"],
                "continue": False
            }
        ],
        description="告警路由规则"
    )
    
    # 告警统计配置
    ALERT_STATS_RETENTION_DAYS: int = Field(30, description="告警统计数据保留天数")
    ALERT_METRICS_INTERVAL: int = Field(60, description="告警指标收集间隔(秒)")
    
    # 告警恢复配置
    ALERT_AUTO_RESOLVE_TIMEOUT: int = Field(3600, description="告警自动恢复超时时间(秒)")
    ALERT_RESOLVE_NOTIFICATION: bool = Field(True, description="是否发送恢复通知")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 默认告警规则配置
DEFAULT_ALERT_RULES = [
    {
        "name": "HighErrorRate",
        "expression": 'rate(http_requests_total{status=~"5.."}[5m]) > 0.1',
        "severity": "critical",
        "duration": "2m",
        "labels": {"service": "lawsker-api"},
        "annotations": {
            "summary": "系统错误率过高",
            "description": "过去5分钟内错误率为 {{ $value | humanizePercentage }}，超过10%阈值",
            "runbook_url": "https://docs.lawsker.com/runbooks/high-error-rate"
        }
    },
    {
        "name": "DatabaseConnectionHigh",
        "expression": "database_connections_active > 80",
        "severity": "warning",
        "duration": "1m",
        "labels": {"service": "lawsker-db"},
        "annotations": {
            "summary": "数据库连接数过高",
            "description": "当前数据库连接数: {{ $value }}，接近最大连接数限制",
            "runbook_url": "https://docs.lawsker.com/runbooks/db-connections"
        }
    },
    {
        "name": "DiskSpaceLow",
        "expression": '(node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.1',
        "severity": "critical",
        "duration": "5m",
        "labels": {"service": "lawsker-system"},
        "annotations": {
            "summary": "磁盘空间不足",
            "description": "根分区可用空间低于10%，当前可用: {{ $value | humanizePercentage }}",
            "runbook_url": "https://docs.lawsker.com/runbooks/disk-space"
        }
    },
    {
        "name": "HighResponseTime",
        "expression": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 3",
        "severity": "warning",
        "duration": "3m",
        "labels": {"service": "lawsker-api"},
        "annotations": {
            "summary": "API响应时间过长",
            "description": "95%分位数响应时间为 {{ $value }}秒，超过3秒阈值",
            "runbook_url": "https://docs.lawsker.com/runbooks/slow-api"
        }
    },
    {
        "name": "HighMemoryUsage",
        "expression": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) > 0.9",
        "severity": "warning",
        "duration": "5m",
        "labels": {"service": "lawsker-system"},
        "annotations": {
            "summary": "内存使用率过高",
            "description": "内存使用率为 {{ $value | humanizePercentage }}，超过90%阈值",
            "runbook_url": "https://docs.lawsker.com/runbooks/high-memory"
        }
    }
]

# 告警抑制规则配置
DEFAULT_INHIBIT_RULES = [
    {
        "source_match": {"severity": "critical"},
        "target_match": {"severity": "warning"},
        "equal": ["service", "instance"]
    },
    {
        "source_match": {"alertname": "NodeDown"},
        "target_match_re": {"alertname": ".*"},
        "equal": ["instance"]
    }
]

# 告警分组规则配置
DEFAULT_GROUP_RULES = [
    {
        "group_by": ["alertname", "service"],
        "group_wait": "10s",
        "group_interval": "5m",
        "repeat_interval": "1h"
    }
]