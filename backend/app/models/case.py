"""
案件相关数据模型
包含案件、客户、案件日志、保险等模型
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum, Integer, Date, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class CaseStatus(enum.Enum):
    """案件状态枚举"""
    PENDING = "pending"           # 待处理
    ASSIGNED = "assigned"         # 已分配
    IN_PROGRESS = "in_progress"   # 处理中
    COMPLETED = "completed"       # 已完成
    CLOSED = "closed"            # 已关闭
    EXPIRED = "expired"          # 已过期


class LegalStatus(enum.Enum):
    """法律时效状态枚举"""
    VALID = "valid"               # 有效
    EXPIRING_SOON = "expiring_soon"  # 即将到期
    EXPIRED = "expired"           # 已过时效


class InsuranceStatus(enum.Enum):
    """保险状态枚举"""
    PENDING = "pending"   # 待生效
    ACTIVE = "active"     # 生效中
    CLAIMED = "claimed"   # 已理赔
    EXPIRED = "expired"   # 已过期


class Case(Base):
    """案件表"""
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    
    # 案件基本信息
    case_number = Column(String(100), unique=True, nullable=False, index=True)  # 案件编号
    debtor_info = Column(JSONB, nullable=False)  # 债务人信息JSON
    case_amount = Column(DECIMAL(18, 2), nullable=False)  # 案件金额
    status = Column(SQLEnum(CaseStatus), default=CaseStatus.PENDING, nullable=False)
    
    # 分配信息
    assigned_to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    sales_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # AI评分
    ai_risk_score = Column(Integer, nullable=True)         # AI风险评分 (0-100)
    data_quality_score = Column(Integer, nullable=True)    # 数据质量评分 (0-100)
    data_freshness_score = Column(Integer, nullable=True)  # 数据新鲜度评分 (0-100)
    
    # 法律时效相关
    debt_creation_date = Column(Date, nullable=False)      # 债权形成日期
    last_follow_up_date = Column(Date, nullable=True)      # 最近跟进日期
    legal_status = Column(SQLEnum(LegalStatus), default=LegalStatus.VALID, nullable=False)
    limitation_expires_at = Column(Date, nullable=True)    # 诉讼时效到期日期
    
    # 业务字段
    description = Column(Text, nullable=True)              # 案件描述
    notes = Column(Text, nullable=True)                    # 备注
    tags = Column(JSONB, nullable=True)                    # 标签
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)  # 完成时间
    
    # 关联关系
    tenant = relationship("Tenant", back_populates="cases")
    client = relationship("Client", back_populates="cases")
    assigned_user = relationship("User", foreign_keys=[assigned_to_user_id], back_populates="cases_assigned")
    sales_user = relationship("User", foreign_keys=[sales_user_id], back_populates="cases_uploaded")
    logs = relationship("CaseLog", back_populates="case")
    insurance = relationship("Insurance", back_populates="case", uselist=False)
    transactions = relationship("Transaction", back_populates="case")
    review_tasks = relationship("DocumentReviewTask", back_populates="case")

    def __repr__(self):
        return f"<Case(id={self.id}, case_number={self.case_number}, status={self.status.value}, amount={self.case_amount})>"


class Client(Base):
    """客户表"""
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    
    # 客户信息
    client_type = Column(String(50), nullable=True)        # 客户类型（银行、消费金融等）
    business_license = Column(String(100), nullable=True)  # 营业执照号
    contact_person = Column(String(100), nullable=True)    # 联系人
    contact_phone = Column(String(20), nullable=True)      # 联系电话
    contact_email = Column(String(255), nullable=True)     # 联系邮箱
    address = Column(Text, nullable=True)                  # 地址
    
    # 业务信息
    sales_owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    cooperation_level = Column(String(20), nullable=True)  # 合作等级
    credit_rating = Column(String(10), nullable=True)      # 信用评级
    
    # 统计信息
    total_cases = Column(Integer, default=0)               # 总案件数
    total_amount = Column(DECIMAL(18, 2), default=0)       # 总金额
    success_rate = Column(DECIMAL(5, 4), nullable=True)    # 成功率
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    tenant = relationship("Tenant", back_populates="clients")
    sales_owner = relationship("User", back_populates="clients_owned")
    cases = relationship("Case", back_populates="client")

    def __repr__(self):
        return f"<Client(id={self.id}, name={self.name}, total_cases={self.total_cases})>"


class CaseLog(Base):
    """案件日志表"""
    __tablename__ = "case_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # 日志内容
    action = Column(String(255), nullable=False)    # 操作类型
    details = Column(JSONB, nullable=True)          # 详细信息JSON
    old_values = Column(JSONB, nullable=True)       # 变更前的值
    new_values = Column(JSONB, nullable=True)       # 变更后的值
    ip_address = Column(String(45), nullable=True)  # IP地址
    user_agent = Column(Text, nullable=True)        # 用户代理
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关联关系
    case = relationship("Case", back_populates="logs")
    user = relationship("User")

    def __repr__(self):
        return f"<CaseLog(id={self.id}, case_id={self.case_id}, action={self.action})>"


class Insurance(Base):
    """保险记录表"""
    __tablename__ = "insurances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), unique=True, nullable=False)
    
    # 保险信息
    policy_number = Column(String(255), nullable=False)     # 保单号
    insurance_company = Column(String(255), nullable=False) # 保险公司
    premium_amount = Column(DECIMAL(18, 2), nullable=False) # 保费金额
    coverage_amount = Column(DECIMAL(18, 2), nullable=False) # 保额
    status = Column(SQLEnum(InsuranceStatus), default=InsuranceStatus.PENDING, nullable=False)
    
    # 保险期限
    effective_date = Column(Date, nullable=True)    # 生效日期
    expiry_date = Column(Date, nullable=True)       # 到期日期
    
    # 理赔信息
    claim_amount = Column(DECIMAL(18, 2), nullable=True)    # 理赔金额
    claim_date = Column(Date, nullable=True)                # 理赔日期
    claim_details = Column(JSONB, nullable=True)            # 理赔详情
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    case = relationship("Case", back_populates="insurance")

    def __repr__(self):
        return f"<Insurance(id={self.id}, case_id={self.case_id}, policy_number={self.policy_number}, status={self.status.value})>" 