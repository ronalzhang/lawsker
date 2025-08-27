"""
用户相关数据模型
支持多租户用户管理和权限控制
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class UserStatus(enum.Enum):
    """用户状态枚举"""
    PENDING = "pending"      # 待审核
    ACTIVE = "active"        # 活跃
    SUSPENDED = "suspended"  # 暂停
    BANNED = "banned"        # 封禁


class UserRole(enum.Enum):
    """用户角色枚举"""
    ADMIN = "admin"          # 管理员
    LAWYER = "lawyer"        # 律师
    SALES = "sales"          # 律客用户
    INSTITUTION = "institution"  # 机构用户


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone_number = Column(String(20), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # 基本信息
    full_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # 状态和角色
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.PENDING)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.SALES)
    
    # 权限和配置
    permissions = Column(Text, nullable=True)  # 权限配置JSON (字符串)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)
    
    # 用户哈希（用于URL）
    user_hash = Column(String(10), unique=True, nullable=True, index=True)
    
    # 统一认证系统字段
    workspace_id = Column(String(50), unique=True, nullable=True)
    account_type = Column(String(20), default='pending', nullable=False)  # pending, user, lawyer, lawyer_pending, admin
    email_verified = Column(Boolean, default=False, nullable=False)
    registration_source = Column(String(20), default='web', nullable=False)
    
    # 统计信息
    login_count = Column(Integer, default=0, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    tenant = relationship("Tenant", back_populates="users")
    lawyer_qualifications = relationship("LawyerQualification", back_populates="user", foreign_keys="LawyerQualification.user_id")
    # assigned_review_tasks = relationship("DocumentReviewTask", foreign_keys="DocumentReviewTask.lawyer_id", back_populates="lawyer")
    # created_review_tasks = relationship("DocumentReviewTask", foreign_keys="DocumentReviewTask.creator_id", back_populates="creator")
    # workload = relationship("LawyerWorkload", back_populates="lawyer", uselist=False)
    
    # 统一认证系统关联
    certification_requests = relationship("LawyerCertificationRequest", foreign_keys="LawyerCertificationRequest.user_id", back_populates="user")
    workspace_mapping = relationship("WorkspaceMapping", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role.value})>"


class Role(Base):
    """角色表"""
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)  # NULL表示全局角色
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(Text, nullable=True)  # 权限配置JSON (字符串)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    tenant = relationship("Tenant", back_populates="roles")

    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


class LawyerQualification(Base):
    """律师资质认证表"""
    __tablename__ = "lawyer_qualifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 基本信息
    license_number = Column(String(100), unique=True, nullable=False, index=True)
    law_firm = Column(String(200), nullable=True)
    practice_years = Column(Integer, nullable=True)
    
    # 资质详情
    qualification_details = Column(Text, nullable=True)  # 资质详情JSON (字符串)
    
    # 认证状态
    verification_status = Column(String(20), default="pending", nullable=False)  # pending, approved, rejected
    verification_notes = Column(Text, nullable=True)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # 执业信息
    practice_areas = Column(Text, nullable=True)        # 执业领域JSON数组 (字符串)
    specializations = Column(Text, nullable=True)       # 专业特长JSON数组 (字符串)
    
    # 文件信息
    license_image_url = Column(String(500), nullable=True)
    license_image_metadata = Column(Text, nullable=True)   # 图片元数据（AI识别结果）(字符串)
    certification_documents = Column(Text, nullable=True)  # 其他认证文件JSON (字符串)
    
    # AI识别结果
    ai_extraction_result = Column(Text, nullable=True)   # AI提取结果JSON (字符串)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    user = relationship("User", back_populates="lawyer_qualifications", foreign_keys=[user_id])
    verifier = relationship("User", foreign_keys=[verified_by])

    def __repr__(self):
        return f"<LawyerQualification(id={self.id}, user_id={self.user_id}, license_number={self.license_number})>" 