"""
案件相关数据模型
支持案件管理、任务分配、进度跟踪等功能
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer, Enum as SQLEnum, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class CaseStatus(enum.Enum):
    """案件状态枚举"""
    PENDING = "pending"      # 待处理
    ASSIGNED = "assigned"    # 已分配
    IN_PROGRESS = "in_progress"  # 处理中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class CasePriority(enum.Enum):
    """案件优先级枚举"""
    LOW = "low"              # 低优先级
    NORMAL = "normal"        # 普通优先级
    HIGH = "high"            # 高优先级
    URGENT = "urgent"        # 紧急


class Case(Base):
    """案件表"""
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 基本信息
    case_number = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # 案件类型和状态
    case_type = Column(String(50), nullable=False)  # 案件类型
    status = Column(SQLEnum(CaseStatus), nullable=False, default=CaseStatus.PENDING)
    priority = Column(SQLEnum(CasePriority), nullable=False, default=CasePriority.NORMAL)
    
    # 债务人信息
    debtor_name = Column(String(100), nullable=False)
    debtor_phone = Column(String(20), nullable=True)
    debtor_email = Column(String(255), nullable=True)
    debtor_address = Column(Text, nullable=True)
    debtor_info = Column(Text, nullable=False)  # 债务人信息JSON (字符串)
    
    # 债务信息
    debt_amount = Column(Numeric(15, 2), nullable=False)
    debt_currency = Column(String(3), default="CNY", nullable=False)
    debt_origin = Column(String(100), nullable=True)  # 债务来源
    debt_date = Column(DateTime(timezone=True), nullable=True)  # 债务发生日期
    
    # 案件详情
    case_details = Column(Text, nullable=True)  # 案件详情
    evidence_files = Column(Text, nullable=True)  # 证据文件列表JSON (字符串)
    
    # 标签和分类
    tags = Column(Text, nullable=True)  # 标签JSON (字符串)
    
    # 时间信息
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=True)  # 截止日期
    completed_at = Column(DateTime(timezone=True), nullable=True)  # 完成时间
    
    # 关联关系
    tenant = relationship("Tenant", back_populates="cases")
    user = relationship("User", back_populates="cases")
    tasks = relationship("Task", back_populates="case")
    lawyer_letters = relationship("LawyerLetter", back_populates="case")

    def __repr__(self):
        return f"<Case(id={self.id}, case_number={self.case_number}, status={self.status.value})>"


class Task(Base):
    """任务表"""
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 任务信息
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String(50), nullable=False)  # 任务类型
    
    # 状态和优先级
    status = Column(String(20), default="pending", nullable=False)  # pending, in_progress, completed, cancelled
    priority = Column(String(20), default="normal", nullable=False)  # low, normal, high, urgent
    
    # 任务详情
    details = Column(Text, nullable=True)  # 详细信息JSON (字符串)
    old_values = Column(Text, nullable=True)  # 变更前的值JSON (字符串)
    new_values = Column(Text, nullable=True)  # 变更后的值JSON (字符串)
    
    # 时间信息
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)  # 截止日期
    completed_at = Column(DateTime(timezone=True), nullable=True)  # 完成时间
    
    # 关联关系
    case = relationship("Case", back_populates="tasks")
    user = relationship("User", back_populates="tasks")

    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"


class Client(Base):
    """客户表"""
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    sales_owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # 客户信息
    name = Column(String(100), nullable=False)
    contact_person = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    
    # 业务信息
    industry = Column(String(50), nullable=True)  # 行业
    company_size = Column(String(20), nullable=True)  # 公司规模
    total_cases = Column(Integer, default=0, nullable=False)  # 总案件数
    total_revenue = Column(Numeric(15, 2), default=0, nullable=False)  # 总收入
    
    # 状态信息
    status = Column(String(20), default="active", nullable=False)  # active, inactive, potential
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    tenant = relationship("Tenant", back_populates="clients")
    sales_owner = relationship("User")

    def __repr__(self):
        return f"<Client(id={self.id}, name={self.name}, status={self.status})>"


class Claim(Base):
    """理赔表"""
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    
    # 理赔信息
    claim_number = Column(String(100), unique=True, nullable=False, index=True)
    claim_type = Column(String(50), nullable=False)  # 理赔类型
    claim_amount = Column(Numeric(15, 2), nullable=False)  # 理赔金额
    claim_currency = Column(String(3), default="CNY", nullable=False)
    
    # 理赔详情
    claim_details = Column(Text, nullable=True)  # 理赔详情JSON (字符串)
    
    # 状态信息
    status = Column(String(20), default="pending", nullable=False)  # pending, approved, rejected, paid
    
    # 时间信息
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)  # 处理时间
    
    # 关联关系
    case = relationship("Case")

    def __repr__(self):
        return f"<Claim(id={self.id}, claim_number={self.claim_number}, status={self.status})>" 