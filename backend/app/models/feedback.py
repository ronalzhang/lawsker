"""
用户反馈模型
用于收集灰度发布期间的用户反馈
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class DeploymentFeedback(Base):
    """部署反馈模型"""
    __tablename__ = "deployment_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    deployment_phase = Column(String(50), nullable=False)  # alpha, beta, gamma, production
    deployment_version = Column(String(50), nullable=False)
    
    # 反馈类型
    feedback_type = Column(String(50), nullable=False)  # bug, suggestion, praise, complaint
    
    # 反馈内容
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    
    # 评分 (1-5)
    rating = Column(Float, nullable=True)
    
    # 严重程度 (low, medium, high, critical)
    severity = Column(String(20), default="medium")
    
    # 影响的功能模块
    affected_module = Column(String(100), nullable=True)
    
    # 浏览器和设备信息
    browser_info = Column(Text, nullable=True)
    device_info = Column(Text, nullable=True)
    
    # 状态
    status = Column(String(20), default="open")  # open, in_progress, resolved, closed
    
    # 处理信息
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolution = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关联关系
    user = relationship("User", foreign_keys=[user_id], back_populates="feedback_given")
    assignee = relationship("User", foreign_keys=[assigned_to])


class FeatureUsageStats(Base):
    """功能使用统计"""
    __tablename__ = "feature_usage_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    deployment_version = Column(String(50), nullable=False)
    
    # 功能信息
    feature_name = Column(String(100), nullable=False)
    feature_version = Column(String(50), nullable=False)
    
    # 使用统计
    usage_count = Column(Integer, default=0)
    total_time_spent = Column(Integer, default=0)  # 秒
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # 性能指标
    avg_response_time = Column(Float, nullable=True)
    error_count = Column(Integer, default=0)
    success_rate = Column(Float, nullable=True)
    
    # 用户体验指标
    user_satisfaction = Column(Float, nullable=True)  # 1-5
    ease_of_use = Column(Float, nullable=True)  # 1-5
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    user = relationship("User", back_populates="feature_usage")


class ABTestResult(Base):
    """A/B测试结果"""
    __tablename__ = "ab_test_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 测试信息
    test_name = Column(String(100), nullable=False)
    variant = Column(String(50), nullable=False)  # A, B, control, treatment
    deployment_version = Column(String(50), nullable=False)
    
    # 转化指标
    conversion_event = Column(String(100), nullable=False)
    converted = Column(Boolean, default=False)
    conversion_value = Column(Float, nullable=True)
    
    # 时间指标
    time_to_conversion = Column(Integer, nullable=True)  # 秒
    session_duration = Column(Integer, nullable=True)  # 秒
    
    # 用户行为
    page_views = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    bounce_rate = Column(Float, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    user = relationship("User", back_populates="ab_test_results")


class PerformanceMetric(Base):
    """性能指标记录"""
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    deployment_version = Column(String(50), nullable=False)
    
    # 指标类型
    metric_type = Column(String(50), nullable=False)  # response_time, error_rate, throughput
    metric_name = Column(String(100), nullable=False)
    
    # 指标值
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)  # ms, %, req/s
    
    # 上下文信息
    endpoint = Column(String(200), nullable=True)
    method = Column(String(10), nullable=True)
    status_code = Column(Integer, nullable=True)
    
    # 环境信息
    environment = Column(String(50), default="canary")
    region = Column(String(50), nullable=True)
    
    # 时间戳
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # 索引
    __table_args__ = (
        {"mysql_engine": "InnoDB"},
    )