"""
用户相关数据模型
包含用户、角色、权限、用户资料等模型
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum
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