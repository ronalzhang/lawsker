"""
租户相关数据模型
支持多租户架构和配置管理
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
import json

from app.core.database import Base


class TenantMode(enum.Enum):
    """租户模式枚举"""
    SAAS = "saas"              # SaaS在线模式
    ON_PREMISE = "on_premise"  # 独立部署模式


class TenantStatus(enum.Enum):
    """租户状态枚举"""
    TRIAL = "trial"        # 试用期
    ACTIVE = "active"      # 活跃
    SUSPENDED = "suspended"  # 暂停
    EXPIRED = "expired"    # 过期


class Tenant(Base):
    """租户表"""
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)  # 租户/机构名称
    tenant_code = Column(String(50), unique=True, nullable=False, index=True)  # 租户代码
    mode = Column(SQLEnum(TenantMode), nullable=False, default=TenantMode.SAAS)
    status = Column(SQLEnum(TenantStatus), nullable=False, default=TenantStatus.TRIAL)
    
    # 配置信息
    domain = Column(String(255), unique=True, nullable=True)  # 自定义域名
    feature_flags = Column(Text, nullable=True)  # 功能开关配置 (JSON字符串)
    system_config = Column(Text, nullable=True)  # 系统配置 (JSON字符串)
    api_limits = Column(Text, nullable=True)     # API使用限制 (JSON字符串)
    billing_info = Column(Text, nullable=True)   # 计费信息 (JSON字符串)
    
    # 业务配置
    subscription_plan = Column(String(50), nullable=True)  # 订阅计划
    max_users = Column(UUID(as_uuid=True), nullable=True)   # 最大用户数
    max_cases = Column(UUID(as_uuid=True), nullable=True)   # 最大案件数
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    trial_expires_at = Column(DateTime(timezone=True), nullable=True)  # 试用期结束时间
    
    # 关联关系
    users = relationship("User", back_populates="tenant")
    roles = relationship("Role", back_populates="tenant")
    cases = relationship("Case", back_populates="tenant")
    clients = relationship("Client", back_populates="tenant")
    system_configs = relationship("SystemConfig", back_populates="tenant")

    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name}, mode={self.mode.value}, status={self.status.value})>"


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)  # NULL表示全局配置
    category = Column(String(50), nullable=False)  # 配置类别
    key = Column(String(255), nullable=False)      # 配置键
    value = Column(Text, nullable=False)           # 配置值 (JSON字符串)
    description = Column(Text, nullable=True)      # 配置描述
    is_active = Column(Boolean, default=True, nullable=False)
    is_editable = Column(Boolean, default=True, nullable=False)  # 是否可编辑
    
    # 数值范围限制（用于数字类型配置）
    min_value = Column(String(50), nullable=True)
    max_value = Column(String(50), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    tenant = relationship("Tenant", back_populates="system_configs")

    def __repr__(self):
        return f"<SystemConfig(id={self.id}, tenant_id={self.tenant_id}, category={self.category}, key={self.key})>" 