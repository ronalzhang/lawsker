"""
告警通知渠道实现
包括邮件、短信、WebSocket等通知方式
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl
import httpx
from jinja2 import Template

from app.core.config import settings
from app.services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    """通知渠道基类"""
    
    @abstractmethod
    async def send_notification(self, alert_data) -> bool:
        """发送通知"""
        pass


class EmailNotifier(NotificationChannel):
    """邮件通知器"""
    
    def __init__(self, smtp_host: str, smtp_port: int, smtp_user: str, 
                 smtp_password: str, from_email: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        
        # 邮件模板
        self.email_template = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Lawsker系统告警</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        .alert-container { max-width: 600px; margin: 0 auto; }
        .alert-header { 
            padding: 20px; 
            border-radius: 5px 5px 0 0; 
            color: white;
            text-align: center;
        }
        .critical { background-color: #dc3545; }
        .warning { background-color: #ffc107; color: #212529; }
        .info { background-color: #17a2b8; }
        .alert-body { 
            padding: 20px; 
            border: 1px solid #ddd; 
            border-radius: 0 0 5px 5px;
            background-color: #f8f9fa;
        }
        .alert-field { margin-bottom: 15px; }
        .alert-label { font-weight: bold; color: #495057; }
        .alert-value { margin-top: 5px; }
        .runbook-link { 
            display: inline-block; 
            margin-top: 15px; 
            padding: 10px 20px; 
            background-color: #007bff; 
            color: white; 
            text-decoration: none; 
            border-radius: 3px; 
        }
        .timestamp { color: #6c757d; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="alert-container">
        <div class="alert-header {{ severity }}">
            <h2>🚨 {{ name }}</h2>
            <p>严重级别: {{ severity.upper() }}</p>
        </div>
        <div class="alert-body">
            <div class="alert-field">
                <div class="alert-label">服务:</div>
                <div class="alert-value">{{ service }}</div>
            </div>
            <div class="alert-field">
                <div class="alert-label">消息:</div>
                <div class="alert-value">{{ message }}</div>
            </div>
            <div class="alert-field">
                <div class="alert-label">详细描述:</div>
                <div class="alert-value">{{ description }}</div>
            </div>
            <div class="alert-field">
                <div class="alert-label">状态:</div>
                <div class="alert-value">{{ status.upper() }}</div>
            </div>
            <div class="alert-field">
                <div class="alert-label">时间:</div>
                <div class="alert-value timestamp">{{ timestamp }}</div>
            </div>
            {% if runbook_url %}
            <a href="{{ runbook_url }}" class="runbook-link" target="_blank">
                📖 查看处理手册
            </a>
            {% endif %}
        </div>
    </div>
</body>
</html>
        """)
    
    async def send_notification(self, alert_data) -> bool:
        """发送邮件通知"""
        try:
            # 获取收件人列表
            recipients = await self._get_recipients(alert_data.severity)
            if not recipients:
                logger.warning("没有配置邮件收件人")
                return False
            
            # 生成邮件内容
            subject = f"[Lawsker告警] {alert_data.name} - {alert_data.severity.upper()}"
            html_content = self.email_template.render(
                name=alert_data.name,
                severity=alert_data.severity.value,
                service=alert_data.service,
                message=alert_data.message,
                description=alert_data.description,
                status=alert_data.status.value,
                timestamp=alert_data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                runbook_url=alert_data.runbook_url
            )
            
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(recipients)
            
            # 添加HTML内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 发送邮件
            await self._send_email(msg, recipients)
            
            logger.info(f"邮件告警发送成功: {alert_data.name}")
            return True
            
        except Exception as e:
            logger.error(f"发送邮件告警失败: {e}")
            return False
    
    async def _get_recipients(self, severity) -> List[str]:
        """根据严重级别获取收件人列表"""
        # 从配置中获取收件人
        if severity.value == "critical":
            return getattr(settings, 'ALERT_EMAIL_CRITICAL', [])
        elif severity.value == "warning":
            return getattr(settings, 'ALERT_EMAIL_WARNING', [])
        else:
            return getattr(settings, 'ALERT_EMAIL_INFO', [])
    
    async def _send_email(self, msg: MIMEMultipart, recipients: List[str]):
        """发送邮件"""
        def _send():
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg, to_addrs=recipients)
        
        # 在线程池中执行同步操作
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send)


class SMSNotifier(NotificationChannel):
    """短信通知器"""
    
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_notification(self, alert_data) -> bool:
        """发送短信通知"""
        try:
            # 只有严重告警才发送短信
            if alert_data.severity.value != "critical":
                return True
            
            # 获取短信收件人
            recipients = await self._get_sms_recipients()
            if not recipients:
                logger.warning("没有配置短信收件人")
                return False
            
            # 生成短信内容
            message = self._generate_sms_content(alert_data)
            
            # 发送短信
            for phone in recipients:
                await self._send_sms(phone, message)
            
            logger.info(f"短信告警发送成功: {alert_data.name}")
            return True
            
        except Exception as e:
            logger.error(f"发送短信告警失败: {e}")
            return False
    
    def _generate_sms_content(self, alert_data) -> str:
        """生成短信内容"""
        return (
            f"【Lawsker告警】{alert_data.name}\n"
            f"级别: {alert_data.severity.upper()}\n"
            f"服务: {alert_data.service}\n"
            f"消息: {alert_data.message}\n"
            f"时间: {alert_data.timestamp.strftime('%m-%d %H:%M')}"
        )
    
    async def _get_sms_recipients(self) -> List[str]:
        """获取短信收件人列表"""
        return getattr(settings, 'ALERT_SMS_PHONES', [])
    
    async def _send_sms(self, phone: str, message: str):
        """发送单条短信"""
        payload = {
            "phone": phone,
            "message": message,
            "api_key": self.api_key
        }
        
        response = await self.client.post(self.api_url, json=payload)
        response.raise_for_status()


class WebSocketNotifier(NotificationChannel):
    """WebSocket通知器"""
    
    async def send_notification(self, alert_data) -> bool:
        """通过WebSocket发送实时通知"""
        try:
            # 构造WebSocket消息
            message = {
                "type": "alert",
                "data": {
                    "alert_id": alert_data.alert_id,
                    "name": alert_data.name,
                    "severity": alert_data.severity.value,
                    "status": alert_data.status.value,
                    "message": alert_data.message,
                    "description": alert_data.description,
                    "service": alert_data.service,
                    "timestamp": alert_data.timestamp.isoformat(),
                    "labels": alert_data.labels,
                    "runbook_url": alert_data.runbook_url
                }
            }
            
            # 发送到管理后台
            await websocket_manager.broadcast_to_admins(message)
            
            logger.debug(f"WebSocket告警发送成功: {alert_data.name}")
            return True
            
        except Exception as e:
            logger.error(f"发送WebSocket告警失败: {e}")
            return False


class DingTalkNotifier(NotificationChannel):
    """钉钉通知器"""
    
    def __init__(self, webhook_url: str, secret: Optional[str] = None):
        self.webhook_url = webhook_url
        self.secret = secret
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_notification(self, alert_data) -> bool:
        """发送钉钉通知"""
        try:
            # 生成消息内容
            message = self._generate_dingtalk_message(alert_data)
            
            # 发送到钉钉
            response = await self.client.post(self.webhook_url, json=message)
            response.raise_for_status()
            
            result = response.json()
            if result.get("errcode") == 0:
                logger.info(f"钉钉告警发送成功: {alert_data.name}")
                return True
            else:
                logger.error(f"钉钉告警发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"发送钉钉告警失败: {e}")
            return False
    
    def _generate_dingtalk_message(self, alert_data) -> Dict:
        """生成钉钉消息格式"""
        # 根据严重级别选择颜色
        color_map = {
            "critical": "#FF0000",
            "warning": "#FFA500", 
            "info": "#0000FF"
        }
        
        color = color_map.get(alert_data.severity.value, "#808080")
        
        return {
            "msgtype": "markdown",
            "markdown": {
                "title": f"Lawsker系统告警 - {alert_data.name}",
                "text": f"""
## 🚨 {alert_data.name}

**严重级别**: <font color="{color}">{alert_data.severity.upper()}</font>

**服务**: {alert_data.service}

**状态**: {alert_data.status.upper()}

**消息**: {alert_data.message}

**描述**: {alert_data.description}

**时间**: {alert_data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

{f'[📖 查看处理手册]({alert_data.runbook_url})' if alert_data.runbook_url else ''}
                """
            }
        }


class SlackNotifier(NotificationChannel):
    """Slack通知器"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_notification(self, alert_data) -> bool:
        """发送Slack通知"""
        try:
            # 生成消息内容
            message = self._generate_slack_message(alert_data)
            
            # 发送到Slack
            response = await self.client.post(self.webhook_url, json=message)
            response.raise_for_status()
            
            logger.info(f"Slack告警发送成功: {alert_data.name}")
            return True
            
        except Exception as e:
            logger.error(f"发送Slack告警失败: {e}")
            return False
    
    def _generate_slack_message(self, alert_data) -> Dict:
        """生成Slack消息格式"""
        # 根据严重级别选择颜色和图标
        severity_config = {
            "critical": {"color": "danger", "icon": ":rotating_light:"},
            "warning": {"color": "warning", "icon": ":warning:"},
            "info": {"color": "good", "icon": ":information_source:"}
        }
        
        config = severity_config.get(alert_data.severity.value, 
                                   {"color": "good", "icon": ":question:"})
        
        return {
            "text": f"{config['icon']} Lawsker系统告警",
            "attachments": [
                {
                    "color": config["color"],
                    "title": alert_data.name,
                    "fields": [
                        {
                            "title": "严重级别",
                            "value": alert_data.severity.upper(),
                            "short": True
                        },
                        {
                            "title": "服务",
                            "value": alert_data.service,
                            "short": True
                        },
                        {
                            "title": "状态",
                            "value": alert_data.status.upper(),
                            "short": True
                        },
                        {
                            "title": "时间",
                            "value": alert_data.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            "short": True
                        },
                        {
                            "title": "消息",
                            "value": alert_data.message,
                            "short": False
                        },
                        {
                            "title": "描述",
                            "value": alert_data.description,
                            "short": False
                        }
                    ],
                    "actions": [
                        {
                            "type": "button",
                            "text": "查看处理手册",
                            "url": alert_data.runbook_url
                        }
                    ] if alert_data.runbook_url else []
                }
            ]
        }


class NotificationManager:
    """通知管理器"""
    
    def __init__(self):
        self.channels: List[NotificationChannel] = []
        self._setup_channels()
    
    def _setup_channels(self):
        """设置通知渠道"""
        # 邮件通知
        if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD:
            email_notifier = EmailNotifier(
                smtp_host=settings.SMTP_HOST,
                smtp_port=settings.SMTP_PORT or 587,
                smtp_user=settings.SMTP_USER,
                smtp_password=settings.SMTP_PASSWORD,
                from_email=settings.SMTP_USER
            )
            self.channels.append(email_notifier)
        
        # WebSocket通知
        websocket_notifier = WebSocketNotifier()
        self.channels.append(websocket_notifier)
        
        # 钉钉通知（如果配置了）
        if hasattr(settings, 'DINGTALK_WEBHOOK_URL') and settings.DINGTALK_WEBHOOK_URL:
            dingtalk_notifier = DingTalkNotifier(settings.DINGTALK_WEBHOOK_URL)
            self.channels.append(dingtalk_notifier)
        
        # Slack通知（如果配置了）
        if hasattr(settings, 'SLACK_WEBHOOK_URL') and settings.SLACK_WEBHOOK_URL:
            slack_notifier = SlackNotifier(settings.SLACK_WEBHOOK_URL)
            self.channels.append(slack_notifier)
    
    async def send_notification(self, alert_data) -> bool:
        """发送通知到所有渠道"""
        success_count = 0
        total_channels = len(self.channels)
        
        for channel in self.channels:
            try:
                if await channel.send_notification(alert_data):
                    success_count += 1
            except Exception as e:
                logger.error(f"通知渠道 {channel.__class__.__name__} 发送失败: {e}")
        
        logger.info(f"通知发送完成: {success_count}/{total_channels} 成功")
        return success_count > 0


# 创建全局通知管理器实例
notification_manager = NotificationManager()