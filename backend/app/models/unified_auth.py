"""
统一认证系统数据模型
包含律师认证、工作台映射和演示账户相关模型
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class LawyerCertificationRequest(Base):
    """律师认证申请表"""
    __tablename__ = "lawyer_certification_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    certificate_file_path = Column(String(500), nullable=False)
    certificate_file_name = Column(String(255), nullable=False)
    lawyer_name = Column(String(100), nullable=False)
    license_number = Column(String(50), nullable=False)
    law_firm = Column(String(200), nullable=True)
    practice_areas = Column(JSON, default=list)
    years_of_experience = Column(Integer, default=0)
    education_background = Column(Text, nullable=True)
    specialization_certificates = Column(JSON, default=list)
    status = Column(String(20), default='pending', nullable=False)  # pending, approved, rejected, under_review
    admin_review_notes = Column(Text, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    user = relationship("User", foreign_keys=[user_id], back_populates="certification_requests")
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    def __repr__(self):
        return f"<LawyerCertificationRequest(id={self.id}, user_id={self.user_id}, license_number={self.license_number})>"


class WorkspaceMapping(Base):
    """工作台ID映射表（安全访问）"""
    __tablename__ = "workspace_mappings"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    workspace_id = Column(String(50), nullable=False, unique=True)
    workspace_type = Column(String(20), nullable=False)  # user, lawyer, admin
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关联关系
    user = relationship("User", back_populates="workspace_mapping")

    def __repr__(self):
        return f"<WorkspaceMapping(user_id={self.user_id}, workspace_id={self.workspace_id}, type={self.workspace_type})>"


class DemoAccount(Base):
    """演示账户配置表"""
    __tablename__ = "demo_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    demo_type = Column(String(20), nullable=False)  # lawyer, user
    workspace_id = Column(String(50), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    demo_data = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<DemoAccount(id={self.id}, demo_type={self.demo_type}, display_name={self.display_name})>"