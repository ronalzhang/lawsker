"""
统计和日志相关数据模型
"""

from sqlalchemy import Column, String, Integer, BigInteger, Date, DateTime, Text, DECIMAL, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


# CaseLog 已在 app.models.case 中定义，这里不重复定义


class SystemStatistics(Base):
    """系统统计表"""
    __tablename__ = "system_statistics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stat_date = Column(Date, nullable=False, unique=True)
    total_cases = Column(Integer, default=0, nullable=False)
    active_cases = Column(Integer, default=0, nullable=False)
    completed_cases = Column(Integer, default=0, nullable=False)
    total_users = Column(Integer, default=0, nullable=False)
    active_lawyers = Column(Integer, default=0, nullable=False)
    active_sales = Column(Integer, default=0, nullable=False)
    total_transactions = Column(Integer, default=0, nullable=False)
    total_amount = Column(DECIMAL(18, 2), default=0, nullable=False)
    total_commissions = Column(DECIMAL(18, 2), default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class UserActivityLog(Base):
    """用户活动日志表"""
    __tablename__ = "user_activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(UUID(as_uuid=True))
    details = Column(JSONB)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    session_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 关联关系
    user = relationship("User")


class DataUploadRecord(Base):
    """销售数据上传记录表"""
    __tablename__ = "data_upload_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_type = Column(String(50), nullable=False)
    file_path = Column(String(500))
    data_type = Column(String(50), nullable=False)  # debt_collection, client_data, etc.
    total_records = Column(Integer, nullable=False)
    processed_records = Column(Integer, default=0, nullable=False)
    failed_records = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default='pending', nullable=False)
    error_details = Column(JSONB)
    processing_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True))

    # 关联关系
    user = relationship("User")


class TaskPublishRecord(Base):
    """任务发布记录表"""
    __tablename__ = "task_publish_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # 允许为空，系统生成的任务
    task_type = Column(String(50), nullable=False)  # lawyer_letter, debt_collection, contract_review
    title = Column(String(200), nullable=False)
    description = Column(Text)
    target_info = Column(JSONB, nullable=False)  # 目标对象信息
    amount = Column(DECIMAL(18, 2))
    urgency = Column(String(20), default='normal', nullable=False)
    status = Column(String(20), default='pending', nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    completion_notes = Column(Text)
    source_case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True)  # 关联的案件ID
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True))

    # 关联关系
    user = relationship("User", foreign_keys=[user_id])
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    source_case = relationship("Case", foreign_keys=[source_case_id])


class LawyerDailyLimit(Base):
    """律师每日接单限制记录表"""
    __tablename__ = "lawyer_daily_limits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lawyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    grabbed_count = Column(Integer, default=0, nullable=False)  # 当日已抢单数量
    max_daily_limit = Column(Integer, default=3, nullable=False)  # 每日最大接单数量（可配置）
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    lawyer = relationship("User")
    
    # 创建复合索引，确保每个律师每天只有一条记录
    __table_args__ = (
        {'schema': None},
        # 在这里可以添加更多的索引
    )


class UserDailyPublishLimit(Base):
    """用户每日发单限制记录表"""
    __tablename__ = "user_daily_publish_limits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    published_count = Column(Integer, default=0, nullable=False)  # 当日已发单数量
    max_daily_limit = Column(Integer, default=5, nullable=False)  # 每日最大发单数量（可配置）
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    user = relationship("User")
    
    # 创建复合索引，确保每个用户每天只有一条记录
    __table_args__ = (
        {'schema': None},
        # 在这里可以添加更多的索引
    ) 