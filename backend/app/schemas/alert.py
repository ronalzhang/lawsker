"""
告警相关的数据模式
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AlertResponse(BaseModel):
    """告警响应模式"""
    id: str
    alert_id: str
    name: str
    severity: str
    status: str
    message: str
    description: Optional[str] = None
    service: Optional[str] = None
    labels: Optional[Dict[str, Any]] = None
    annotations: Optional[Dict[str, Any]] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    """告警列表响应模式"""
    alerts: List[AlertResponse]
    total: int
    limit: int
    offset: int


class AlertStatsResponse(BaseModel):
    """告警统计响应模式"""
    total_alerts: int = Field(description="总告警数")
    active_alerts: int = Field(description="活跃告警数")
    resolved_alerts: int = Field(description="已解决告警数")
    critical_alerts: int = Field(description="严重告警数")
    warning_alerts: int = Field(description="警告告警数")
    info_alerts: int = Field(description="信息告警数")
    service_stats: Dict[str, int] = Field(description="按服务统计")
    time_range_hours: int = Field(description="统计时间范围(小时)")


class AlertSilenceRequest(BaseModel):
    """告警静默请求模式"""
    duration_minutes: int = Field(ge=1, le=10080, description="静默时长(分钟)")
    comment: Optional[str] = Field(None, description="静默原因")


class AlertSilenceResponse(BaseModel):
    """告警静默响应模式"""
    id: str
    alert_id: Optional[str] = None
    comment: Optional[str] = None
    created_by: Optional[str] = None
    starts_at: datetime
    ends_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class AlertRuleRequest(BaseModel):
    """告警规则请求模式"""
    name: str = Field(description="规则名称")
    expression: str = Field(description="告警表达式")
    severity: str = Field(description="严重级别")
    duration: Optional[str] = Field(None, description="持续时间")
    labels: Optional[Dict[str, str]] = Field(None, description="标签")
    annotations: Optional[Dict[str, str]] = Field(None, description="注释")
    enabled: bool = Field(True, description="是否启用")


class AlertRuleResponse(BaseModel):
    """告警规则响应模式"""
    id: str
    name: str
    expression: str
    severity: str
    duration: Optional[str] = None
    labels: Optional[Dict[str, Any]] = None
    annotations: Optional[Dict[str, Any]] = None
    enabled: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AlertNotificationResponse(BaseModel):
    """告警通知响应模式"""
    id: str
    alert_id: str
    channel: str
    recipient: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    sent_at: datetime
    
    class Config:
        from_attributes = True


class WebhookAlertData(BaseModel):
    """Webhook告警数据模式"""
    receiver: str
    status: str
    alerts: List[Dict[str, Any]]
    groupLabels: Dict[str, str]
    commonLabels: Dict[str, str]
    commonAnnotations: Dict[str, str]
    externalURL: str
    version: str
    groupKey: str


class AlertMetrics(BaseModel):
    """告警指标模式"""
    timestamp: datetime
    alert_count: int
    critical_count: int
    warning_count: int
    info_count: int
    resolved_count: int
    avg_resolution_time: Optional[float] = None


class AlertTrend(BaseModel):
    """告警趋势模式"""
    date: str
    total: int
    critical: int
    warning: int
    info: int
    resolved: int


class AlertServiceStats(BaseModel):
    """服务告警统计模式"""
    service: str
    total_alerts: int
    critical_alerts: int
    warning_alerts: int
    info_alerts: int
    avg_resolution_time: Optional[float] = None
    last_alert_time: Optional[datetime] = None