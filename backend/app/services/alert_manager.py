"""
告警管理服务
处理告警通知、状态管理和去重
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import aioredis
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update

from app.core.config import settings
from app.core.database import get_db
from app.models.alert import Alert, AlertStatus, AlertSeverity

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """告警严重级别"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertStatus(str, Enum):
    """告警状态"""
    FIRING = "firing"
    RESOLVED = "resolved"
    SILENCED = "silenced"


@dataclass
class AlertData:
    """告警数据结构"""
    alert_id: str
    name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    description: str
    service: str
    timestamp: datetime
    labels: Dict[str, str]
    annotations: Dict[str, str]
    runbook_url: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.active_alerts: Dict[str, AlertData] = {}
        self.alert_history: List[AlertData] = []
        self.notification_channels = []
        
    async def initialize(self):
        """初始化告警管理器"""
        try:
            # 连接Redis
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            
            # 初始化通知渠道
            await self._initialize_notification_channels()
            
            # 加载活跃告警
            await self._load_active_alerts()
            
            logger.info("告警管理器初始化完成")
            
        except Exception as e:
            logger.error(f"告警管理器初始化失败: {e}")
            raise
    
    async def _initialize_notification_channels(self):
        """初始化通知渠道"""
        # 邮件通知渠道
        if settings.SMTP_HOST:
            email_notifier = EmailNotifier(
                smtp_host=settings.SMTP_HOST,
                smtp_port=settings.SMTP_PORT,
                smtp_user=settings.SMTP_USER,
                smtp_password=settings.SMTP_PASSWORD,
                from_email=settings.ALERT_FROM_EMAIL
            )
            self.notification_channels.append(email_notifier)
        
        # 短信通知渠道
        if settings.SMS_API_URL:
            sms_notifier = SMSNotifier(
                api_url=settings.SMS_API_URL,
                api_key=settings.SMS_API_KEY
            )
            self.notification_channels.append(sms_notifier)
        
        # WebSocket通知渠道
        websocket_notifier = WebSocketNotifier()
        self.notification_channels.append(websocket_notifier)
    
    async def _load_active_alerts(self):
        """从Redis加载活跃告警"""
        try:
            if not self.redis_client:
                return
                
            alert_keys = await self.redis_client.keys("alert:active:*")
            for key in alert_keys:
                alert_data = await self.redis_client.get(key)
                if alert_data:
                    alert = AlertData(**json.loads(alert_data))
                    self.active_alerts[alert.alert_id] = alert
                    
        except Exception as e:
            logger.error(f"加载活跃告警失败: {e}")
    
    async def process_alert(self, alert_data: Dict) -> bool:
        """处理告警"""
        try:
            # 解析告警数据
            alert = self._parse_alert_data(alert_data)
            
            # 检查是否为重复告警
            if await self._is_duplicate_alert(alert):
                logger.debug(f"忽略重复告警: {alert.alert_id}")
                return False
            
            # 更新告警状态
            await self._update_alert_status(alert)
            
            # 发送通知
            await self._send_notifications(alert)
            
            # 记录告警历史
            await self._record_alert_history(alert)
            
            logger.info(f"处理告警完成: {alert.name} ({alert.severity})")
            return True
            
        except Exception as e:
            logger.error(f"处理告警失败: {e}")
            return False
    
    def _parse_alert_data(self, data: Dict) -> AlertData:
        """解析告警数据"""
        # 生成告警ID
        alert_id = f"{data.get('alertname', 'unknown')}_{data.get('instance', 'unknown')}"
        
        # 解析严重级别
        severity = AlertSeverity(data.get('labels', {}).get('severity', 'warning'))
        
        # 解析状态
        status = AlertStatus.FIRING if data.get('status') == 'firing' else AlertStatus.RESOLVED
        
        return AlertData(
            alert_id=alert_id,
            name=data.get('alertname', 'Unknown Alert'),
            severity=severity,
            status=status,
            message=data.get('annotations', {}).get('summary', ''),
            description=data.get('annotations', {}).get('description', ''),
            service=data.get('labels', {}).get('service', 'unknown'),
            timestamp=datetime.now(),
            labels=data.get('labels', {}),
            annotations=data.get('annotations', {}),
            runbook_url=data.get('annotations', {}).get('runbook_url')
        )
    
    async def _is_duplicate_alert(self, alert: AlertData) -> bool:
        """检查是否为重复告警"""
        # 检查活跃告警中是否已存在
        if alert.alert_id in self.active_alerts:
            existing_alert = self.active_alerts[alert.alert_id]
            
            # 如果状态相同且时间间隔小于5分钟，认为是重复告警
            time_diff = alert.timestamp - existing_alert.timestamp
            if (existing_alert.status == alert.status and 
                time_diff < timedelta(minutes=5)):
                return True
        
        return False
    
    async def _update_alert_status(self, alert: AlertData):
        """更新告警状态"""
        if alert.status == AlertStatus.FIRING:
            # 添加到活跃告警
            self.active_alerts[alert.alert_id] = alert
            
            # 保存到Redis
            if self.redis_client:
                await self.redis_client.setex(
                    f"alert:active:{alert.alert_id}",
                    3600,  # 1小时过期
                    json.dumps(alert.to_dict())
                )
        
        elif alert.status == AlertStatus.RESOLVED:
            # 从活跃告警中移除
            if alert.alert_id in self.active_alerts:
                del self.active_alerts[alert.alert_id]
            
            # 从Redis中删除
            if self.redis_client:
                await self.redis_client.delete(f"alert:active:{alert.alert_id}")
    
    async def _send_notifications(self, alert: AlertData):
        """发送告警通知"""
        # 根据严重级别决定通知渠道
        channels_to_notify = []
        
        if alert.severity == AlertSeverity.CRITICAL:
            # 严重告警：所有渠道
            channels_to_notify = self.notification_channels
        elif alert.severity == AlertSeverity.WARNING:
            # 警告告警：邮件和WebSocket
            channels_to_notify = [
                ch for ch in self.notification_channels 
                if not isinstance(ch, SMSNotifier)
            ]
        else:
            # 信息告警：仅WebSocket
            channels_to_notify = [
                ch for ch in self.notification_channels 
                if isinstance(ch, WebSocketNotifier)
            ]
        
        # 并发发送通知
        tasks = []
        for channel in channels_to_notify:
            task = asyncio.create_task(channel.send_notification(alert))
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _record_alert_history(self, alert: AlertData):
        """记录告警历史"""
        # 添加到内存历史
        self.alert_history.append(alert)
        
        # 保持历史记录数量限制
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
        
        # 保存到数据库
        try:
            async with get_db() as db:
                await db.execute(
                    insert(Alert).values(
                        alert_id=alert.alert_id,
                        name=alert.name,
                        severity=alert.severity.value,
                        status=alert.status.value,
                        message=alert.message,
                        description=alert.description,
                        service=alert.service,
                        labels=json.dumps(alert.labels),
                        annotations=json.dumps(alert.annotations),
                        created_at=alert.timestamp
                    )
                )
                await db.commit()
        except Exception as e:
            logger.error(f"保存告警历史失败: {e}")
    
    async def get_active_alerts(self) -> List[AlertData]:
        """获取活跃告警列表"""
        return list(self.active_alerts.values())
    
    async def get_alert_history(self, limit: int = 100) -> List[AlertData]:
        """获取告警历史"""
        return self.alert_history[-limit:]
    
    async def silence_alert(self, alert_id: str, duration_minutes: int = 60) -> bool:
        """静默告警"""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.SILENCED
                
                # 设置静默过期时间
                if self.redis_client:
                    await self.redis_client.setex(
                        f"alert:silenced:{alert_id}",
                        duration_minutes * 60,
                        json.dumps(alert.to_dict())
                    )
                
                logger.info(f"告警已静默: {alert_id} ({duration_minutes}分钟)")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"静默告警失败: {e}")
            return False
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """手动解决告警"""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.timestamp = datetime.now()
                
                # 更新状态
                await self._update_alert_status(alert)
                
                # 记录历史
                await self._record_alert_history(alert)
                
                logger.info(f"告警已解决: {alert_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"解决告警失败: {e}")
            return False


# 全局告警管理器实例
alert_manager = AlertManager()