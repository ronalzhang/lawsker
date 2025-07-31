"""
告警数据模型
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.core.database import Base


class Alert(Base):
    """告警记录表"""
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(String(255), nullable=False, comment="告警唯一标识")
    name = Column(String(255), nullable=False, comment="告警名称")
    severity = Column(String(50), nullable=False, comment="严重级别")
    status = Column(String(50), nullable=False, comment="告警状态")
    message = Column(Text, comment="告警消息")
    description = Column(Text, comment="详细描述")
    service = Column(String(100), comment="相关服务")
    labels = Column(JSON, comment="标签信息")
    annotations = Column(JSON, comment="注释信息")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    resolved_at = Column(DateTime, comment="解决时间")
    
    # 创建索引
    __table_args__ = (
        Index('idx_alerts_alert_id', 'alert_id'),
        Index('idx_alerts_severity', 'severity'),
        Index('idx_alerts_status', 'status'),
        Index('idx_alerts_service', 'service'),
        Index('idx_alerts_created_at', 'created_at'),
        Index('idx_alerts_severity_created', 'severity', 'created_at'),
    )


class AlertRule(Base):
    """告警规则表"""
    __tablename__ = "alert_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, comment="规则名称")
    expression = Column(Text, nullable=False, comment="告警表达式")
    severity = Column(String(50), nullable=False, comment="严重级别")
    duration = Column(String(50), comment="持续时间")
    labels = Column(JSON, comment="标签")
    annotations = Column(JSON, comment="注释")
    enabled = Column(String(10), default="true", comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 创建索引
    __table_args__ = (
        Index('idx_alert_rules_name', 'name'),
        Index('idx_alert_rules_enabled', 'enabled'),
        Index('idx_alert_rules_severity', 'severity'),
    )


class AlertNotification(Base):
    """告警通知记录表"""
    __tablename__ = "alert_notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(String(255), nullable=False, comment="告警ID")
    channel = Column(String(50), nullable=False, comment="通知渠道")
    recipient = Column(String(255), comment="收件人")
    status = Column(String(50), nullable=False, comment="发送状态")
    error_message = Column(Text, comment="错误信息")
    sent_at = Column(DateTime, default=datetime.utcnow, comment="发送时间")
    
    # 创建索引
    __table_args__ = (
        Index('idx_alert_notifications_alert_id', 'alert_id'),
        Index('idx_alert_notifications_channel', 'channel'),
        Index('idx_alert_notifications_status', 'status'),
        Index('idx_alert_notifications_sent_at', 'sent_at'),
    )


class AlertSilence(Base):
    """告警静默表"""
    __tablename__ = "alert_silences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(String(255), comment="告警ID")
    matcher_labels = Column(JSON, comment="匹配标签")
    comment = Column(Text, comment="静默原因")
    created_by = Column(String(255), comment="创建人")
    starts_at = Column(DateTime, nullable=False, comment="开始时间")
    ends_at = Column(DateTime, nullable=False, comment="结束时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 创建索引
    __table_args__ = (
        Index('idx_alert_silences_alert_id', 'alert_id'),
        Index('idx_alert_silences_starts_at', 'starts_at'),
        Index('idx_alert_silences_ends_at', 'ends_at'),
        Index('idx_alert_silences_created_by', 'created_by'),
    )