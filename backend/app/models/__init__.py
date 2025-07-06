"""
Lawsker 数据模型包
包含所有数据库表模型定义
"""

from app.models.user import User, Role, UserRole, Profile, LawyerQualification, CollectionRecord
from app.models.tenant import Tenant, SystemConfig
from app.models.case import Case, Client, CaseLog, Insurance
from app.models.finance import Transaction, CommissionSplit, Wallet
from app.models.lawyer_letter import LawyerLetterOrder, LawyerLetterTemplate, LetterSendRecord
from app.models.lawyer_review import DocumentReviewTask, DocumentReviewLog, LawyerWorkload, ReviewStatus
from app.models.statistics import SystemStatistics, UserActivityLog, DataUploadRecord, TaskPublishRecord

__all__ = [
    # 用户相关模型
    "User",
    "Role", 
    "UserRole",
    "Profile",
    "LawyerQualification",
    "CollectionRecord",
    
    # 租户相关模型
    "Tenant",
    "SystemConfig",
    
    # 业务相关模型
    "Case",
    "Client",
    "CaseLog",
    "Insurance",
    
    # 财务相关模型
    "Transaction",
    "CommissionSplit",
    "Wallet",
    
    # 律师函服务模型
    "LawyerLetterOrder",
    "LawyerLetterTemplate", 
    "LetterSendRecord",
    
    # 律师审核工作流模型
    "DocumentReviewTask",
    "DocumentReviewLog",
    "LawyerWorkload",
    "ReviewStatus",
    
    # 统计和日志模型
    "SystemStatistics",
    "UserActivityLog",
    "DataUploadRecord",
    "TaskPublishRecord",
] 