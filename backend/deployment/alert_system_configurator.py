"""
告警系统配置器
自动化配置Prometheus告警规则、Alertmanager通知和告警历史记录
"""
import os
import json
import yaml
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)

class AlertSeverity(Enum):
    """告警严重级别"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class NotificationChannel(Enum):
    """通知渠道"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    WECHAT = "wechat"
    SMS = "sms"

@dataclass
class AlertRule:
    """告警规则"""
    name: str
    expr: str
    for_duration: str
    severity: AlertSeverity
    summary: str
    description: str
    labels: Optional[Dict[str, str]] = None
    annotations: Optional[Dict[str, str]] = None

@dataclass
class NotificationConfig:
    """通知配置"""
    channel: NotificationChannel
    config: Dict[str, Any]
    enabled: bool = True

@dataclass
class AlertManagerConfig:
    """AlertManager配置"""
    global_config: Dict[str, Any]
    route_config: Dict[str, Any]
    receivers: List[Dict[str, Any]]
    inhibit_rules: List[Dict[str, Any]]

class AlertSystemConfigurator:
    """告警系统配置器"""
    
    def __init__(self, prometheus_url: str = "http://localhost:9090",
                 alertmanager_url: str = "http://localhost:9093"):
        self.prometheus_url = prometheus_url.rstrip('/')
        self.alertmanager_url = alertmanager_url.rstrip('/')
        self.logger = get_logger(__name__)
        self.rules_dir = Path("monitoring/prometheus/rules")
        self.alertmanager_dir = Path("monitoring/alertmanager")
        self.templates_dir = Path("monitoring/alertmanager/templates")
        self.history_dir = Path("monitoring/alerts/history")
        
    async def setup_alert_system(self) -> Dict[str, Any]:
        """设置告警系统"""
        self.logger.info("Setting up alert system")
        
        setup_results = {
            "alert_rules": [],
            "notification_channels": [],
            "alertmanager_config": {},
            "templates": [],
            "history_config": {},
            "status": "success",
            "errors": []
        }
        
        try:
            # 1. 创建目录结构
            await self._create_directories()
            
            # 2. 创建告警规则
            rules_result = await self._create_alert_rules()
            setup_results["alert_rules"] = rules_result
            
            # 3. 配置通知渠道
            channels_result = await self._configure_notification_channels()
            setup_results["notification_channels"] = channels_result
            
            # 4. 配置AlertManager
            alertmanager_result = await self._configure_alertmanager()
            setup_results["alertmanager_config"] = alertmanager_result
            
            # 5. 创建通知模板
            templates_result = await self._create_notification_templates()
            setup_results["templates"] = templates_result
            
            # 6. 配置告警历史记录
            history_result = await self._setup_alert_history()
            setup_results["history_config"] = history_result
            
            # 7. 验证告警系统
            verification_result = await self._verify_alert_system()
            setup_results["verification"] = verification_result
            
            self.logger.info("Alert system setup completed")
            return setup_results
            
        except Exception as e:
            self.logger.error(f"Alert system setup failed: {str(e)}")
            setup_results["status"] = "error"
            setup_results["errors"].append(str(e))
            return setup_results
    
    async def _create_directories(self):
        """创建目录结构"""
        directories = [
            self.rules_dir,
            self.alertmanager_dir,
            self.templates_dir,
            self.history_dir,
            Path("monitoring/alerts/logs"),
            Path("monitoring/alerts/reports")
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def _create_alert_rules(self) -> List[Dict[str, Any]]:
        """创建告警规则"""
        self.logger.info("Creating alert rules")
        
        # 定义告警规则
        alert_rules = [
            # 系统级告警
            AlertRule(
                name="HighCPUUsage",
                expr="100 - (avg by(instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100) > 80",
                for_duration="10m",
                severity=AlertSeverity.WARNING,
                summary="CPU使用率过高",
                description="CPU使用率: {{ $value }}%",
                labels={"service": "system"}
            ),
            AlertRule(
                name="HighMemoryUsage",
                expr="(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) > 0.9",
                for_duration="10m",
                severity=AlertSeverity.WARNING,
                summary="内存使用率过高",
                description="内存使用率: {{ $value | humanizePercentage }}",
                labels={"service": "system"}
            ),
            AlertRule(
                name="DiskSpaceLow",
                expr="(node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1",
                for_duration="5m",
                severity=AlertSeverity.CRITICAL,
                summary="磁盘空间不足",
                description="磁盘使用率超过90%，剩余空间: {{ $value | humanizePercentage }}",
                labels={"service": "system"}
            ),
            
            # 应用级告警
            AlertRule(
                name="HighErrorRate",
                expr="rate(http_requests_total{status=~\"5..\"}[5m]) > 0.1",
                for_duration="2m",
                severity=AlertSeverity.CRITICAL,
                summary="高错误率检测到",
                description="错误率为 {{ $value }} 错误/秒，超过阈值",
                labels={"service": "lawsker-backend"}
            ),
            AlertRule(
                name="HighResponseTime",
                expr="histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 3",
                for_duration="5m",
                severity=AlertSeverity.WARNING,
                summary="API响应时间过长",
                description="95%分位数响应时间为 {{ $value }}秒",
                labels={"service": "lawsker-backend"}
            ),
            AlertRule(
                name="ServiceDown",
                expr="up == 0",
                for_duration="1m",
                severity=AlertSeverity.CRITICAL,
                summary="服务不可用",
                description="{{ $labels.job }} 服务已停止",
                labels={"service": "monitoring"}
            ),
            
            # 数据库告警
            AlertRule(
                name="DatabaseConnectionHigh",
                expr="pg_stat_database_numbackends > 80",
                for_duration="1m",
                severity=AlertSeverity.WARNING,
                summary="数据库连接数过高",
                description="当前连接数: {{ $value }}",
                labels={"service": "postgres"}
            ),
            AlertRule(
                name="DatabaseDeadlocks",
                expr="increase(pg_stat_database_deadlocks[5m]) > 0",
                for_duration="0m",
                severity=AlertSeverity.CRITICAL,
                summary="数据库死锁检测",
                description="检测到 {{ $value }} 个死锁",
                labels={"service": "postgres"}
            ),
            
            # 业务告警
            AlertRule(
                name="LowUserRegistration",
                expr="increase(user_registrations_total[1h]) < 5",
                for_duration="0m",
                severity=AlertSeverity.INFO,
                summary="用户注册量过低",
                description="过去1小时用户注册量: {{ $value }}",
                labels={"service": "business"}
            ),
            AlertRule(
                name="HighPaymentFailureRate",
                expr="rate(payment_failures_total[5m]) / rate(payment_attempts_total[5m]) > 0.1",
                for_duration="5m",
                severity=AlertSeverity.WARNING,
                summary="支付失败率过高",
                description="支付失败率: {{ $value | humanizePercentage }}",
                labels={"service": "business"}
            ),
            
            # 安全告警
            AlertRule(
                name="SuspiciousLoginAttempts",
                expr="increase(failed_login_attempts_total[5m]) > 10",
                for_duration="0m",
                severity=AlertSeverity.WARNING,
                summary="可疑登录尝试",
                description="5分钟内失败登录尝试: {{ $value }} 次",
                labels={"service": "security"}
            ),
            AlertRule(
                name="RateLimitExceeded",
                expr="increase(rate_limit_exceeded_total[1m]) > 100",
                for_duration="0m",
                severity=AlertSeverity.WARNING,
                summary="限流触发频繁",
                description="1分钟内限流触发: {{ $value }} 次",
                labels={"service": "security"}
            )
        ]
        
        # 按服务分组创建规则文件
        rules_by_service = {}
        for rule in alert_rules:
            service = rule.labels.get("service", "general") if rule.labels else "general"
            if service not in rules_by_service:
                rules_by_service[service] = []
            rules_by_service[service].append(rule)
        
        results = []
        
        for service, rules in rules_by_service.items():
            try:
                result = await self._create_rules_file(service, rules)
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Failed to create rules for service {service}: {str(e)}")
                results.append({
                    "service": service,
                    "status": "error",
                    "message": str(e)
                })
        
        return results
    
    async def _create_rules_file(self, service: str, rules: List[AlertRule]) -> Dict[str, Any]:
        """创建规则文件"""
        rules_config = {
            "groups": [
                {
                    "name": f"{service}.rules",
                    "rules": []
                }
            ]
        }
        
        for rule in rules:
            rule_config = {
                "alert": rule.name,
                "expr": rule.expr,
                "for": rule.for_duration,
                "labels": {
                    "severity": rule.severity.value,
                    **(rule.labels or {})
                },
                "annotations": {
                    "summary": rule.summary,
                    "description": rule.description,
                    **(rule.annotations or {})
                }
            }
            
            rules_config["groups"][0]["rules"].append(rule_config)
        
        # 保存规则文件
        rules_file = self.rules_dir / f"{service}-alerts.yml"
        
        with open(rules_file, 'w', encoding='utf-8') as f:
            yaml.dump(rules_config, f, default_flow_style=False, allow_unicode=True)
        
        return {
            "service": service,
            "rules_count": len(rules),
            "rules_file": str(rules_file),
            "status": "created",
            "message": f"Created {len(rules)} alert rules for {service}"
        }
    
    async def _configure_notification_channels(self) -> List[Dict[str, Any]]:
        """配置通知渠道"""
        self.logger.info("Configuring notification channels")
        
        # 定义通知渠道配置
        notification_configs = [
            NotificationConfig(
                channel=NotificationChannel.WEBHOOK,
                config={
                    "url": "http://localhost:8000/api/v1/alerts/webhook",
                    "send_resolved": True,
                    "http_config": {
                        "basic_auth": {
                            "username": "alert_user",
                            "password": "alert_password"
                        }
                    }
                }
            ),
            NotificationConfig(
                channel=NotificationChannel.EMAIL,
                config={
                    "to": ["admin@lawsker.com", "ops@lawsker.com"],
                    "from": "alerts@lawsker.com",
                    "smarthost": "localhost:587",
                    "subject": "Lawsker Alert: {{ .GroupLabels.alertname }}",
                    "body": "{{ range .Alerts }}{{ .Annotations.description }}{{ end }}"
                }
            ),
            NotificationConfig(
                channel=NotificationChannel.SLACK,
                config={
                    "api_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
                    "channel": "#alerts",
                    "username": "Lawsker Alerts",
                    "title": "Alert: {{ .GroupLabels.alertname }}",
                    "text": "{{ range .Alerts }}{{ .Annotations.description }}{{ end }}"
                },
                enabled=False  # 默认禁用，需要配置Slack webhook
            )
        ]
        
        results = []
        
        for config in notification_configs:
            try:
                result = await self._validate_notification_config(config)
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Failed to configure {config.channel.value}: {str(e)}")
                results.append({
                    "channel": config.channel.value,
                    "status": "error",
                    "message": str(e)
                })
        
        return results
    
    async def _validate_notification_config(self, config: NotificationConfig) -> Dict[str, Any]:
        """验证通知配置"""
        if not config.enabled:
            return {
                "channel": config.channel.value,
                "status": "disabled",
                "message": "Notification channel is disabled"
            }
        
        # 基本配置验证
        if config.channel == NotificationChannel.WEBHOOK:
            if "url" not in config.config:
                return {
                    "channel": config.channel.value,
                    "status": "error",
                    "message": "Webhook URL is required"
                }
            
            # 测试webhook连接
            try:
                async with aiohttp.ClientSession() as session:
                    test_payload = {
                        "alerts": [{
                            "status": "firing",
                            "labels": {"alertname": "test", "severity": "info"},
                            "annotations": {"description": "Test alert"}
                        }]
                    }
                    
                    async with session.post(
                        config.config["url"],
                        json=test_payload,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status in [200, 202, 204]:
                            return {
                                "channel": config.channel.value,
                                "status": "validated",
                                "message": "Webhook endpoint is reachable"
                            }
                        else:
                            return {
                                "channel": config.channel.value,
                                "status": "warning",
                                "message": f"Webhook returned status {response.status}"
                            }
                            
            except Exception as e:
                return {
                    "channel": config.channel.value,
                    "status": "warning",
                    "message": f"Webhook validation failed: {str(e)}"
                }
        
        elif config.channel == NotificationChannel.EMAIL:
            required_fields = ["to", "from", "smarthost"]
            for field in required_fields:
                if field not in config.config:
                    return {
                        "channel": config.channel.value,
                        "status": "error",
                        "message": f"Email configuration missing required field: {field}"
                    }
        
        return {
            "channel": config.channel.value,
            "status": "configured",
            "message": "Notification channel configured successfully"
        }
    
    async def _configure_alertmanager(self) -> Dict[str, Any]:
        """配置AlertManager"""
        self.logger.info("Configuring AlertManager")
        
        try:
            # 生成AlertManager配置
            alertmanager_config = {
                "global": {
                    "smtp_smarthost": "localhost:587",
                    "smtp_from": "alerts@lawsker.com",
                    "smtp_auth_username": "alerts@lawsker.com",
                    "smtp_auth_password": "your_email_password"
                },
                "templates": [
                    str(self.templates_dir / "*.tmpl")
                ],
                "route": {
                    "group_by": ["alertname", "cluster", "service"],
                    "group_wait": "10s",
                    "group_interval": "10s",
                    "repeat_interval": "1h",
                    "receiver": "default-receiver",
                    "routes": [
                        {
                            "match": {"severity": "critical"},
                            "receiver": "critical-alerts",
                            "repeat_interval": "30m"
                        },
                        {
                            "match": {"service": "business"},
                            "receiver": "business-alerts",
                            "repeat_interval": "2h"
                        },
                        {
                            "match": {"service": "security"},
                            "receiver": "security-alerts",
                            "repeat_interval": "15m"
                        }
                    ]
                },
                "receivers": [
                    {
                        "name": "default-receiver",
                        "webhook_configs": [
                            {
                                "url": "http://localhost:8000/api/v1/alerts/webhook",
                                "send_resolved": True
                            }
                        ]
                    },
                    {
                        "name": "critical-alerts",
                        "email_configs": [
                            {
                                "to": "admin@lawsker.com",
                                "subject": "CRITICAL: {{ .GroupLabels.alertname }}",
                                "body": "{{ template \"email.default.html\" . }}"
                            }
                        ],
                        "webhook_configs": [
                            {
                                "url": "http://localhost:8000/api/v1/alerts/webhook",
                                "send_resolved": True
                            }
                        ]
                    },
                    {
                        "name": "business-alerts",
                        "email_configs": [
                            {
                                "to": "business@lawsker.com",
                                "subject": "Business Alert: {{ .GroupLabels.alertname }}",
                                "body": "{{ template \"email.business.html\" . }}"
                            }
                        ]
                    },
                    {
                        "name": "security-alerts",
                        "email_configs": [
                            {
                                "to": "security@lawsker.com",
                                "subject": "SECURITY ALERT: {{ .GroupLabels.alertname }}",
                                "body": "{{ template \"email.security.html\" . }}"
                            }
                        ],
                        "webhook_configs": [
                            {
                                "url": "http://localhost:8000/api/v1/alerts/security-webhook",
                                "send_resolved": True
                            }
                        ]
                    }
                ],
                "inhibit_rules": [
                    {
                        "source_match": {"severity": "critical"},
                        "target_match": {"severity": "warning"},
                        "equal": ["alertname", "instance"]
                    },
                    {
                        "source_match": {"alertname": "ServiceDown"},
                        "target_match_re": {"alertname": ".*"},
                        "equal": ["instance"]
                    }
                ]
            }
            
            # 保存配置文件
            config_file = self.alertmanager_dir / "alertmanager.yml"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(alertmanager_config, f, default_flow_style=False, allow_unicode=True)
            
            return {
                "status": "success",
                "config_file": str(config_file),
                "receivers_count": len(alertmanager_config["receivers"]),
                "routes_count": len(alertmanager_config["route"]["routes"]),
                "message": "AlertManager configuration created successfully"
            }
            
        except Exception as e:
            self.logger.error(f"AlertManager configuration failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _create_notification_templates(self) -> List[Dict[str, Any]]:
        """创建通知模板"""
        self.logger.info("Creating notification templates")
        
        templates = {
            "email.default.tmpl": self._get_default_email_template(),
            "email.business.tmpl": self._get_business_email_template(),
            "email.security.tmpl": self._get_security_email_template(),
            "slack.default.tmpl": self._get_slack_template(),
            "webhook.default.tmpl": self._get_webhook_template()
        }
        
        results = []
        
        for template_name, template_content in templates.items():
            try:
                template_file = self.templates_dir / template_name
                
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(template_content)
                
                results.append({
                    "template": template_name,
                    "file": str(template_file),
                    "status": "created",
                    "message": "Template created successfully"
                })
                
            except Exception as e:
                self.logger.error(f"Failed to create template {template_name}: {str(e)}")
                results.append({
                    "template": template_name,
                    "status": "error",
                    "message": str(e)
                })
        
        return results
    
    def _get_default_email_template(self) -> str:
        """获取默认邮件模板"""
        return """{{ define "email.default.html" }}
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Lawsker Alert</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .alert { padding: 15px; margin: 10px 0; border-radius: 5px; }
        .critical { background-color: #ffebee; border-left: 5px solid #f44336; }
        .warning { background-color: #fff3e0; border-left: 5px solid #ff9800; }
        .info { background-color: #e3f2fd; border-left: 5px solid #2196f3; }
        .resolved { background-color: #e8f5e8; border-left: 5px solid #4caf50; }
        .timestamp { color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <h2>Lawsker System Alert</h2>
    
    {{ range .Alerts }}
    <div class="alert {{ .Labels.severity }}">
        <h3>{{ .Annotations.summary }}</h3>
        <p><strong>Description:</strong> {{ .Annotations.description }}</p>
        <p><strong>Severity:</strong> {{ .Labels.severity }}</p>
        <p><strong>Service:</strong> {{ .Labels.service }}</p>
        <p><strong>Instance:</strong> {{ .Labels.instance }}</p>
        <p class="timestamp"><strong>Started:</strong> {{ .StartsAt.Format "2006-01-02 15:04:05" }}</p>
        {{ if .EndsAt }}
        <p class="timestamp"><strong>Ended:</strong> {{ .EndsAt.Format "2006-01-02 15:04:05" }}</p>
        {{ end }}
    </div>
    {{ end }}
    
    <hr>
    <p><small>This alert was generated by Lawsker monitoring system at {{ now.Format "2006-01-02 15:04:05" }}</small></p>
</body>
</html>
{{ end }}"""
    
    def _get_business_email_template(self) -> str:
        """获取业务邮件模板"""
        return """{{ define "email.business.html" }}
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Lawsker Business Alert</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #1976d2; color: white; padding: 15px; border-radius: 5px; }
        .content { padding: 20px; background-color: #f5f5f5; margin: 10px 0; border-radius: 5px; }
        .metric { background-color: white; padding: 10px; margin: 5px 0; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="header">
        <h2>Lawsker Business Metrics Alert</h2>
    </div>
    
    <div class="content">
        {{ range .Alerts }}
        <div class="metric">
            <h3>{{ .Annotations.summary }}</h3>
            <p>{{ .Annotations.description }}</p>
            <p><strong>Time:</strong> {{ .StartsAt.Format "2006-01-02 15:04:05" }}</p>
        </div>
        {{ end }}
    </div>
    
    <p><small>Please review business metrics dashboard for more details.</small></p>
</body>
</html>
{{ end }}"""
    
    def _get_security_email_template(self) -> str:
        """获取安全邮件模板"""
        return """{{ define "email.security.html" }}
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Lawsker Security Alert</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .security-header { background-color: #d32f2f; color: white; padding: 15px; border-radius: 5px; }
        .alert-content { background-color: #ffebee; padding: 15px; margin: 10px 0; border: 2px solid #f44336; border-radius: 5px; }
        .action-required { background-color: #fff3e0; padding: 10px; margin: 10px 0; border-left: 5px solid #ff9800; }
    </style>
</head>
<body>
    <div class="security-header">
        <h2>🚨 SECURITY ALERT 🚨</h2>
    </div>
    
    {{ range .Alerts }}
    <div class="alert-content">
        <h3>{{ .Annotations.summary }}</h3>
        <p><strong>Description:</strong> {{ .Annotations.description }}</p>
        <p><strong>Severity:</strong> {{ .Labels.severity }}</p>
        <p><strong>Source:</strong> {{ .Labels.instance }}</p>
        <p><strong>Time:</strong> {{ .StartsAt.Format "2006-01-02 15:04:05" }}</p>
    </div>
    {{ end }}
    
    <div class="action-required">
        <h4>Action Required:</h4>
        <ul>
            <li>Review security logs immediately</li>
            <li>Check for suspicious activities</li>
            <li>Consider implementing additional security measures</li>
        </ul>
    </div>
    
    <p><strong>This is an automated security alert. Please investigate immediately.</strong></p>
</body>
</html>
{{ end }}"""
    
    def _get_slack_template(self) -> str:
        """获取Slack模板"""
        return """{{ define "slack.default" }}
{
    "channel": "#alerts",
    "username": "Lawsker Alerts",
    "icon_emoji": ":warning:",
    "attachments": [
        {{ range .Alerts }}
        {
            "color": "{{ if eq .Labels.severity "critical" }}danger{{ else if eq .Labels.severity "warning" }}warning{{ else }}good{{ end }}",
            "title": "{{ .Annotations.summary }}",
            "text": "{{ .Annotations.description }}",
            "fields": [
                {
                    "title": "Severity",
                    "value": "{{ .Labels.severity }}",
                    "short": true
                },
                {
                    "title": "Service",
                    "value": "{{ .Labels.service }}",
                    "short": true
                },
                {
                    "title": "Instance",
                    "value": "{{ .Labels.instance }}",
                    "short": true
                },
                {
                    "title": "Time",
                    "value": "{{ .StartsAt.Format "2006-01-02 15:04:05" }}",
                    "short": true
                }
            ]
        }{{ if not (last $) }},{{ end }}
        {{ end }}
    ]
}
{{ end }}"""
    
    def _get_webhook_template(self) -> str:
        """获取Webhook模板"""
        return """{{ define "webhook.default" }}
{
    "alerts": [
        {{ range .Alerts }}
        {
            "status": "{{ .Status }}",
            "labels": {
                {{ range $k, $v := .Labels }}
                "{{ $k }}": "{{ $v }}"{{ if not (last $) }},{{ end }}
                {{ end }}
            },
            "annotations": {
                {{ range $k, $v := .Annotations }}
                "{{ $k }}": "{{ $v }}"{{ if not (last $) }},{{ end }}
                {{ end }}
            },
            "startsAt": "{{ .StartsAt.Format "2006-01-02T15:04:05Z07:00" }}",
            "endsAt": "{{ .EndsAt.Format "2006-01-02T15:04:05Z07:00" }}",
            "generatorURL": "{{ .GeneratorURL }}"
        }{{ if not (last $) }},{{ end }}
        {{ end }}
    ],
    "groupLabels": {
        {{ range $k, $v := .GroupLabels }}
        "{{ $k }}": "{{ $v }}"{{ if not (last $) }},{{ end }}
        {{ end }}
    },
    "commonLabels": {
        {{ range $k, $v := .CommonLabels }}
        "{{ $k }}": "{{ $v }}"{{ if not (last $) }},{{ end }}
        {{ end }}
    },
    "commonAnnotations": {
        {{ range $k, $v := .CommonAnnotations }}
        "{{ $k }}": "{{ $v }}"{{ if not (last $) }},{{ end }}
        {{ end }}
    },
    "externalURL": "{{ .ExternalURL }}",
    "version": "4",
    "groupKey": "{{ .GroupKey }}",
    "truncatedAlerts": {{ .TruncatedAlerts }}
}
{{ end }}"""
    
    async def _setup_alert_history(self) -> Dict[str, Any]:
        """设置告警历史记录"""
        self.logger.info("Setting up alert history")
        
        try:
            # 创建历史记录配置
            history_config = {
                "enabled": True,
                "retention_days": 90,
                "storage_path": str(self.history_dir),
                "log_file": str(self.history_dir.parent / "logs" / "alerts.log"),
                "report_schedule": "daily",
                "report_recipients": ["admin@lawsker.com"]
            }
            
            # 保存配置
            config_file = self.history_dir.parent / "history_config.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(history_config, f, indent=2)
            
            # 创建历史记录处理脚本
            script_result = await self._create_history_script()
            
            return {
                "status": "success",
                "config_file": str(config_file),
                "history_directory": str(self.history_dir),
                "script": script_result,
                "retention_days": history_config["retention_days"],
                "message": "Alert history configuration completed"
            }
            
        except Exception as e:
            self.logger.error(f"Alert history setup failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _create_history_script(self) -> str:
        """创建历史记录处理脚本"""
        script_content = f"""#!/usr/bin/env python3
# Alert History Processor
# Generated automatically by AlertSystemConfigurator

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

class AlertHistoryProcessor:
    def __init__(self):
        self.db_path = "{self.history_dir}/alerts.db"
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_name TEXT NOT NULL,
                severity TEXT NOT NULL,
                service TEXT,
                instance TEXT,
                status TEXT NOT NULL,
                starts_at TIMESTAMP,
                ends_at TIMESTAMP,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_alert_name ON alerts(alert_name);
            CREATE INDEX IF NOT EXISTS idx_severity ON alerts(severity);
            CREATE INDEX IF NOT EXISTS idx_service ON alerts(service);
            CREATE INDEX IF NOT EXISTS idx_starts_at ON alerts(starts_at);
        ''')
        
        conn.commit()
        conn.close()
    
    def record_alert(self, alert_data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for alert in alert_data.get('alerts', []):
            cursor.execute('''
                INSERT INTO alerts (
                    alert_name, severity, service, instance, status,
                    starts_at, ends_at, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert['labels'].get('alertname'),
                alert['labels'].get('severity'),
                alert['labels'].get('service'),
                alert['labels'].get('instance'),
                alert['status'],
                alert.get('startsAt'),
                alert.get('endsAt'),
                alert['annotations'].get('description')
            ))
        
        conn.commit()
        conn.close()
    
    def cleanup_old_records(self, retention_days=90):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cursor.execute('DELETE FROM alerts WHERE created_at < ?', (cutoff_date,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count
    
    def generate_report(self, days=7):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        # 获取统计数据
        cursor.execute('''
            SELECT 
                severity,
                COUNT(*) as count,
                COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_count
            FROM alerts 
            WHERE starts_at >= ? 
            GROUP BY severity
        ''', (start_date,))
        
        severity_stats = cursor.fetchall()
        
        cursor.execute('''
            SELECT 
                service,
                COUNT(*) as count
            FROM alerts 
            WHERE starts_at >= ? 
            GROUP BY service
            ORDER BY count DESC
        ''', (start_date,))
        
        service_stats = cursor.fetchall()
        
        conn.close()
        
        return {{
            'period': f'Last {{days}} days',
            'severity_stats': severity_stats,
            'service_stats': service_stats
        }}

if __name__ == '__main__':
    processor = AlertHistoryProcessor()
    
    # 清理旧记录
    deleted = processor.cleanup_old_records()
    print(f"Cleaned up {{deleted}} old alert records")
    
    # 生成报告
    report = processor.generate_report()
    print(f"Alert report: {{report}}")
"""
        
        script_file = Path("scripts/alert-history-processor.py")
        script_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_file, 0o755)
        
        return str(script_file)
    
    async def _verify_alert_system(self) -> Dict[str, Any]:
        """验证告警系统"""
        self.logger.info("Verifying alert system")
        
        verification_results = {
            "prometheus_rules": await self._verify_prometheus_rules(),
            "alertmanager_config": await self._verify_alertmanager_config(),
            "notification_channels": await self._verify_notification_channels()
        }
        
        all_healthy = all(
            result.get("status") == "success" 
            for result in verification_results.values()
        )
        
        return {
            "overall_status": "healthy" if all_healthy else "unhealthy",
            "components": verification_results
        }
    
    async def _verify_prometheus_rules(self) -> Dict[str, Any]:
        """验证Prometheus规则"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.prometheus_url}/api/v1/rules") as response:
                    if response.status == 200:
                        rules_data = await response.json()
                        groups = rules_data.get("data", {}).get("groups", [])
                        
                        total_rules = sum(len(group.get("rules", [])) for group in groups)
                        
                        return {
                            "status": "success",
                            "groups_count": len(groups),
                            "rules_count": total_rules,
                            "message": f"Found {total_rules} alert rules in {len(groups)} groups"
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"Failed to get rules: HTTP {response.status}"
                        }
                        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Prometheus rules verification failed: {str(e)}"
            }
    
    async def _verify_alertmanager_config(self) -> Dict[str, Any]:
        """验证AlertManager配置"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.alertmanager_url}/api/v1/status") as response:
                    if response.status == 200:
                        status_data = await response.json()
                        config_hash = status_data.get("data", {}).get("configHash", "")
                        
                        return {
                            "status": "success",
                            "config_hash": config_hash,
                            "message": "AlertManager is running with valid configuration"
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"Failed to get AlertManager status: HTTP {response.status}"
                        }
                        
        except Exception as e:
            return {
                "status": "error",
                "message": f"AlertManager verification failed: {str(e)}"
            }
    
    async def _verify_notification_channels(self) -> Dict[str, Any]:
        """验证通知渠道"""
        try:
            # 发送测试告警
            test_alert = {
                "alerts": [{
                    "status": "firing",
                    "labels": {
                        "alertname": "TestAlert",
                        "severity": "info",
                        "service": "monitoring"
                    },
                    "annotations": {
                        "summary": "Test alert for verification",
                        "description": "This is a test alert to verify notification channels"
                    },
                    "startsAt": datetime.now().isoformat(),
                    "generatorURL": f"{self.prometheus_url}/graph"
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.alertmanager_url}/api/v1/alerts",
                    json=test_alert["alerts"],
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return {
                            "status": "success",
                            "message": "Test alert sent successfully"
                        }
                    else:
                        return {
                            "status": "warning",
                            "message": f"Test alert failed: HTTP {response.status}"
                        }
                        
        except Exception as e:
            return {
                "status": "warning",
                "message": f"Notification channels verification failed: {str(e)}"
            }
    
    async def test_alert_rule(self, rule_name: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """测试告警规则"""
        self.logger.info(f"Testing alert rule: {rule_name}")
        
        try:
            # 构造测试查询
            test_query = test_data.get("expr", "")
            
            async with aiohttp.ClientSession() as session:
                params = {
                    "query": test_query,
                    "time": datetime.now().isoformat()
                }
                
                async with session.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params=params
                ) as response:
                    if response.status == 200:
                        query_result = await response.json()
                        result_data = query_result.get("data", {})
                        
                        return {
                            "rule_name": rule_name,
                            "status": "success",
                            "query_result": result_data,
                            "message": "Alert rule test completed"
                        }
                    else:
                        return {
                            "rule_name": rule_name,
                            "status": "error",
                            "message": f"Query failed: HTTP {response.status}"
                        }
                        
        except Exception as e:
            return {
                "rule_name": rule_name,
                "status": "error",
                "message": f"Alert rule test failed: {str(e)}"
            }
    
    async def get_alert_system_status(self) -> Dict[str, Any]:
        """获取告警系统状态"""
        try:
            verification_result = await self._verify_alert_system()
            
            # 获取规则文件统计
            rules_files = list(self.rules_dir.glob("*.yml"))
            
            # 获取模板文件统计
            template_files = list(self.templates_dir.glob("*.tmpl"))
            
            return {
                "status": "success",
                "verification": verification_result,
                "configuration": {
                    "rules_directory": str(self.rules_dir),
                    "alertmanager_directory": str(self.alertmanager_dir),
                    "templates_directory": str(self.templates_dir),
                    "history_directory": str(self.history_dir)
                },
                "statistics": {
                    "rules_files": len(rules_files),
                    "template_files": len(template_files)
                },
                "urls": {
                    "prometheus": self.prometheus_url,
                    "alertmanager": self.alertmanager_url
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get alert system status: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }