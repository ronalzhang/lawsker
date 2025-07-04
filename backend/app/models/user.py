"""
用户相关数据模型
包含用户、角色、权限、用户资料等模型
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum, Date, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class UserStatus(enum.Enum):
    """用户状态枚举"""
    PENDING = "pending"        # 待审核
    ACTIVE = "active"          # 活跃
    INACTIVE = "inactive"      # 非活跃
    BANNED = "banned"          # 被禁用


class VerificationStatus(enum.Enum):
    """认证状态枚举"""
    UNVERIFIED = "unverified"  # 未认证
    PENDING = "pending"        # 认证中
    VERIFIED = "verified"      # 已认证
    FAILED = "failed"          # 认证失败


class LawyerLevel(enum.Enum):
    """律师等级枚举"""
    JUNIOR = "junior"          # 初级律师
    INTERMEDIATE = "intermediate"  # 中级律师
    SENIOR = "senior"          # 高级律师
    PARTNER = "partner"        # 合伙人级别


class QualificationStatus(enum.Enum):
    """资质状态枚举"""
    DRAFT = "draft"            # 草稿
    SUBMITTED = "submitted"    # 已提交
    REVIEWING = "reviewing"    # 审核中
    APPROVED = "approved"      # 已通过
    REJECTED = "rejected"      # 已拒绝
    EXPIRED = "expired"        # 已过期


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    username = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True, index=True)
    phone_number = Column(String(20), unique=True, nullable=True, index=True)
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # 关联关系
    tenant = relationship("Tenant", back_populates="users")
    profile = relationship("Profile", back_populates="user", uselist=False)
    user_roles = relationship("UserRole", back_populates="user")
    cases_assigned = relationship("Case", foreign_keys="Case.assigned_to_user_id", back_populates="assigned_user")
    cases_uploaded = relationship("Case", foreign_keys="Case.sales_user_id", back_populates="sales_user")
    clients_owned = relationship("Client", back_populates="sales_owner")
    wallet = relationship("Wallet", back_populates="user", uselist=False)
    lawyer_qualification = relationship("LawyerQualification", foreign_keys="LawyerQualification.user_id", back_populates="user", uselist=False)
    workload = relationship("LawyerWorkload", back_populates="lawyer", uselist=False)
    assigned_review_tasks = relationship("DocumentReviewTask", foreign_keys="DocumentReviewTask.lawyer_id", back_populates="lawyer")
    created_review_tasks = relationship("DocumentReviewTask", foreign_keys="DocumentReviewTask.creator_id", back_populates="creator")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, status={self.status.value})>"


class Role(Base):
    """角色表"""
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)  # NULL表示全局角色
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(JSONB, nullable=True)  # 权限配置JSON
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    tenant = relationship("Tenant", back_populates="roles")
    user_roles = relationship("UserRole", back_populates="role")

    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name}, tenant_id={self.tenant_id})>"


class UserRole(Base):
    """用户角色关联表"""
    __tablename__ = "user_roles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)
    
    # 时间戳
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关联关系
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")

    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


class Profile(Base):
    """用户资料表"""
    __tablename__ = "profiles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    full_name = Column(String(255), nullable=True)
    id_card_number = Column(String(18), nullable=True, index=True)
    qualification_details = Column(JSONB, nullable=True)  # 资质详情JSON
    did = Column(String(255), unique=True, nullable=True)  # Web3去中心化身份
    verification_status = Column(SQLEnum(VerificationStatus), default=VerificationStatus.UNVERIFIED, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    user = relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<Profile(user_id={self.user_id}, full_name={self.full_name}, verification_status={self.verification_status.value})>"


class LawyerQualification(Base):
    """律师资质表"""
    __tablename__ = "lawyer_qualifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # 执业证书信息
    license_number = Column(String(50), unique=True, nullable=False, index=True)  # 执业证书编号
    license_authority = Column(String(100), nullable=False)  # 发证机关
    license_issued_date = Column(Date, nullable=False)  # 发证日期
    license_expiry_date = Column(Date, nullable=True)   # 到期日期
    
    # 律师事务所信息
    law_firm_name = Column(String(200), nullable=False)  # 律师事务所名称
    law_firm_license = Column(String(50), nullable=True)  # 律师事务所执业许可证号
    law_firm_address = Column(Text, nullable=True)        # 律师事务所地址
    
    # 专业信息
    practice_areas = Column(JSONB, nullable=True)        # 执业领域JSON数组
    lawyer_level = Column(SQLEnum(LawyerLevel), default=LawyerLevel.JUNIOR, nullable=False)
    years_of_practice = Column(Integer, default=0)       # 执业年限
    specializations = Column(JSONB, nullable=True)       # 专业特长JSON数组
    
    # 认证信息
    qualification_status = Column(SQLEnum(QualificationStatus), default=QualificationStatus.DRAFT, nullable=False)
    certification_documents = Column(JSONB, nullable=True)  # 认证文件JSON
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # 审核人ID
    review_notes = Column(Text, nullable=True)            # 审核备注
    reviewed_at = Column(DateTime(timezone=True), nullable=True)  # 审核时间
    
    # 统计信息
    total_cases_handled = Column(Integer, default=0)      # 处理案件总数
    success_rate = Column(Integer, default=0)             # 成功率（百分比）
    average_rating = Column(Integer, default=0)           # 平均评分（1-5分）
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    user = relationship("User", foreign_keys=[user_id], back_populates="lawyer_qualification")
    reviewer = relationship("User", foreign_keys=[reviewer_id])

    def __repr__(self):
        return f"<LawyerQualification(id={self.id}, user_id={self.user_id}, license_number={self.license_number}, status={self.qualification_status.value})>"


class CollectionRecord(Base):
    """催收记录表"""
    __tablename__ = "collection_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    lawyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 催收信息
    action_type = Column(String(50), nullable=False)     # 催收方式：电话、短信、邮件、律师函等
    contact_method = Column(String(50), nullable=True)   # 联系方式
    content = Column(Text, nullable=True)                # 催收内容
    response = Column(Text, nullable=True)               # 债务人回应
    result = Column(String(50), nullable=True)           # 催收结果
    
    # AI辅助信息
    ai_template_used = Column(String(100), nullable=True)  # 使用的AI模板
    ai_generated_content = Column(Text, nullable=True)     # AI生成的内容
    ai_success_prediction = Column(Integer, nullable=True) # AI预测成功率（百分比）
    
    # 时间和状态
    scheduled_time = Column(DateTime(timezone=True), nullable=True)  # 预定时间
    completed_time = Column(DateTime(timezone=True), nullable=True)  # 完成时间
    is_successful = Column(Boolean, default=False)        # 是否成功
    follow_up_required = Column(Boolean, default=False)   # 是否需要跟进
    next_follow_up_date = Column(DateTime(timezone=True), nullable=True)  # 下次跟进时间
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    case = relationship("Case")
    lawyer = relationship("User")

    def __repr__(self):
        return f"<CollectionRecord(id={self.id}, case_id={self.case_id}, action_type={self.action_type}, is_successful={self.is_successful})>" 