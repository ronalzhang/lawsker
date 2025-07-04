"""
律师审核工作流模型
用于AI生成文档的律师审核、修改和授权流程
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from enum import Enum as PyEnum

from app.core.database import Base


class ReviewStatus(str, PyEnum):
    """审核状态枚举"""
    PENDING = "pending"           # 待审核
    IN_REVIEW = "in_review"       # 审核中
    APPROVED = "approved"         # 已通过
    REJECTED = "rejected"         # 已拒绝
    MODIFICATION_REQUESTED = "modification_requested"  # 要求修改
    MODIFIED = "modified"         # 已修改
    AUTHORIZED = "authorized"     # 已授权发送
    SENT = "sent"                # 已发送
    CANCELLED = "cancelled"       # 已取消


class DocumentReviewTask(Base):
    """文档审核任务表"""
    __tablename__ = "document_review_tasks"
    
    # 基础信息
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_number = Column(String(50), unique=True, index=True, comment="任务编号")
    
    # 关联信息
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True, comment="关联案件ID")
    order_id = Column(UUID(as_uuid=True), ForeignKey("lawyer_letter_orders.id"), nullable=True, comment="关联订单ID")
    lawyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, comment="分配律师ID")
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, comment="创建者ID")
    
    # 文档信息
    document_type = Column(String(50), nullable=False, comment="文档类型")
    original_content = Column(Text, nullable=False, comment="AI生成的原始内容")
    current_content = Column(Text, nullable=False, comment="当前内容（可能经过修改）")
    final_content = Column(Text, nullable=True, comment="最终确认内容")
    
    # 审核信息
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, comment="审核状态")
    priority = Column(Integer, default=1, comment="优先级（1-5，5最高）")
    deadline = Column(DateTime(timezone=True), nullable=True, comment="截止时间")
    
    # AI生成元数据
    ai_metadata = Column(JSON, nullable=True, comment="AI生成元数据")
    generation_prompt = Column(Text, nullable=True, comment="生成提示词")
    ai_providers = Column(JSON, nullable=True, comment="使用的AI提供商")
    
    # 审核记录
    review_notes = Column(Text, nullable=True, comment="审核备注")
    modification_requests = Column(Text, nullable=True, comment="修改要求")
    approval_notes = Column(Text, nullable=True, comment="通过备注")
    rejection_reason = Column(Text, nullable=True, comment="拒绝原因")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    reviewed_at = Column(DateTime(timezone=True), nullable=True, comment="审核时间")
    approved_at = Column(DateTime(timezone=True), nullable=True, comment="通过时间")
    sent_at = Column(DateTime(timezone=True), nullable=True, comment="发送时间")
    
    # 业务配置
    auto_approve = Column(Boolean, default=False, comment="是否自动通过")
    requires_signature = Column(Boolean, default=True, comment="是否需要律师签名")
    
    # 关联关系
    case = relationship("Case", back_populates="review_tasks")
    lawyer_letter_order = relationship("LawyerLetterOrder", back_populates="review_tasks")
    lawyer = relationship("User", foreign_keys=[lawyer_id], back_populates="assigned_review_tasks")
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_review_tasks")
    review_logs = relationship("DocumentReviewLog", back_populates="review_task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DocumentReviewTask(id={self.id}, task_number='{self.task_number}', status='{self.status}')>"


class DocumentReviewLog(Base):
    """文档审核日志表"""
    __tablename__ = "document_review_logs"
    
    # 基础信息
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_task_id = Column(UUID(as_uuid=True), ForeignKey("document_review_tasks.id"), nullable=False, comment="审核任务ID")
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, comment="操作人ID")
    
    # 操作信息
    action = Column(String(50), nullable=False, comment="操作类型")
    old_status = Column(Enum(ReviewStatus), nullable=True, comment="原状态")
    new_status = Column(Enum(ReviewStatus), nullable=False, comment="新状态")
    
    # 详细信息
    comment = Column(Text, nullable=True, comment="操作说明")
    content_changes = Column(JSON, nullable=True, comment="内容变更记录")
    attachment_files = Column(JSON, nullable=True, comment="附件文件")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="操作时间")
    
    # 关联关系
    review_task = relationship("DocumentReviewTask", back_populates="review_logs")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    
    def __repr__(self):
        return f"<DocumentReviewLog(id={self.id}, action='{self.action}', new_status='{self.new_status}')>"


class LawyerWorkload(Base):
    """律师工作负荷表"""
    __tablename__ = "lawyer_workloads"
    
    # 基础信息
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lawyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, comment="律师ID")
    
    # 工作负荷统计
    active_cases = Column(Integer, default=0, comment="活跃案件数")
    pending_reviews = Column(Integer, default=0, comment="待审核文档数")
    daily_capacity = Column(Integer, default=10, comment="日处理能力")
    weekly_capacity = Column(Integer, default=50, comment="周处理能力")
    
    # 质量指标
    average_review_time = Column(Integer, default=0, comment="平均审核时间（分钟）")
    approval_rate = Column(Integer, default=95, comment="通过率（百分比）")
    client_satisfaction = Column(Integer, default=90, comment="客户满意度（百分比）")
    
    # 可用性
    is_available = Column(Boolean, default=True, comment="是否可接新任务")
    max_concurrent_tasks = Column(Integer, default=20, comment="最大并发任务数")
    current_workload_score = Column(Integer, default=0, comment="当前工作负荷评分")
    
    # 专业领域
    specialties = Column(JSON, nullable=True, comment="专业领域")
    preferred_document_types = Column(JSON, nullable=True, comment="偏好文档类型")
    
    # 时间统计
    last_assignment_at = Column(DateTime(timezone=True), nullable=True, comment="最后分配时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    lawyer = relationship("User", back_populates="workload")
    
    def __repr__(self):
        return f"<LawyerWorkload(lawyer_id={self.lawyer_id}, current_score={self.current_workload_score})>" 