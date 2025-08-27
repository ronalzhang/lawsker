"""
律师证认证服务
处理律师证上传、审核和认证流程
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert
from fastapi import HTTPException, status, UploadFile
import structlog
from datetime import datetime
import json

from app.models.user import User, UserStatus
from app.models.unified_auth import LawyerCertificationRequest
from app.services.file_upload_service import FileUploadService
from app.services.notification_channels import NotificationService
from app.services.lawyer_membership_service import LawyerMembershipService

logger = structlog.get_logger()


class LawyerCertificationService:
    """律师证认证服务类 - 基于现有文件上传扩展"""
    
    def __init__(self, db: AsyncSession, membership_service: Optional[LawyerMembershipService] = None):
        self.db = db
        self.file_service = FileUploadService()
        self.notification_service = NotificationService()
        self.membership_service = membership_service
    
    async def submit_certification_request(
        self,
        user_id: str,
        cert_data: Dict[str, Any],
        certificate_file: UploadFile
    ) -> Dict[str, Any]:
        """
        提交律师证认证申请
        
        Args:
            user_id: 用户ID
            cert_data: 认证数据
            certificate_file: 律师证文件
        
        Returns:
            认证申请结果
        """
        try:
            # 检查用户是否存在且状态正确
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            
            if user.account_type != 'lawyer_pending':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户状态不正确，无法提交律师认证"
                )
            
            # 保存律师证文件
            file_result = await self.file_service.save_certificate_file(
                user_id, certificate_file
            )
            
            # 创建认证申请记录
            certification_data = {
                'user_id': user_id,
                'certificate_file_path': file_result['path'],
                'certificate_file_name': file_result['filename'],
                'lawyer_name': cert_data['lawyer_name'],
                'license_number': cert_data['license_number'],
                'law_firm': cert_data.get('law_firm'),
                'practice_areas': json.dumps(cert_data.get('practice_areas', [])),
                'years_of_experience': cert_data.get('years_of_experience', 0),
                'education_background': cert_data.get('education_background'),
                'specialization_certificates': json.dumps(cert_data.get('specialization_certificates', [])),
                'status': 'pending',
                'submitted_at': datetime.now()
            }
            
            result = await self.db.execute(
                insert(LawyerCertificationRequest)
                .values(**certification_data)
                .returning(LawyerCertificationRequest.id)
            )
            
            certification_id = result.scalar_one()
            await self.db.commit()
            
            # 通知管理员审核
            await self.notification_service.notify_admin_for_review(certification_id)
            
            logger.info(
                "律师认证申请提交成功",
                user_id=user_id,
                certification_id=certification_id,
                license_number=cert_data['license_number']
            )
            
            return {
                'certification_id': str(certification_id),
                'status': 'pending',
                'message': '认证申请已提交，请等待管理员审核'
            }
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error("律师认证申请提交失败", error=str(e), user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="认证申请提交失败，请稍后重试"
            )
    
    async def get_certification_status(self, user_id: str) -> Dict[str, Any]:
        """
        获取认证状态
        
        Args:
            user_id: 用户ID
        
        Returns:
            认证状态信息
        """
        try:
            result = await self.db.execute(
                select(LawyerCertificationRequest)
                .where(LawyerCertificationRequest.user_id == user_id)
                .order_by(LawyerCertificationRequest.submitted_at.desc())
                .limit(1)
            )
            
            certification = result.scalar_one_or_none()
            
            if not certification:
                return {
                    'status': 'not_submitted',
                    'message': '尚未提交认证申请'
                }
            
            return {
                'certification_id': str(certification.id),
                'status': certification.status,
                'lawyer_name': certification.lawyer_name,
                'license_number': certification.license_number,
                'law_firm': certification.law_firm,
                'submitted_at': certification.submitted_at.isoformat(),
                'reviewed_at': certification.reviewed_at.isoformat() if certification.reviewed_at else None,
                'admin_review_notes': certification.admin_review_notes,
                'message': self.get_status_message(certification.status)
            }
            
        except Exception as e:
            logger.error("获取认证状态失败", error=str(e), user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取认证状态失败"
            )
    
    def get_status_message(self, status: str) -> str:
        """获取状态消息"""
        status_messages = {
            'pending': '认证申请审核中，请耐心等待',
            'under_review': '认证材料正在详细审核中',
            'approved': '认证已通过，欢迎使用律师服务',
            'rejected': '认证未通过，请查看审核意见并重新提交'
        }
        return status_messages.get(status, '未知状态')
    
    async def approve_certification(
        self,
        cert_id: str,
        admin_id: str,
        review_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        管理员审核通过
        
        Args:
            cert_id: 认证申请ID
            admin_id: 管理员ID
            review_notes: 审核备注
        
        Returns:
            审核结果
        """
        try:
            # 更新认证状态
            result = await self.db.execute(
                update(LawyerCertificationRequest)
                .where(LawyerCertificationRequest.id == cert_id)
                .values(
                    status='approved',
                    reviewed_by=admin_id,
                    reviewed_at=datetime.now(),
                    admin_review_notes=review_notes
                )
                .returning(LawyerCertificationRequest.user_id)
            )
            
            user_id = result.scalar_one()
            
            # 激活律师账户
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    account_type='lawyer',
                    status=UserStatus.ACTIVE
                )
            )
            
            await self.db.commit()
            
            # 自动分配免费会员
            if self.membership_service:
                try:
                    # 需要转换为同步调用，因为当前是异步环境
                    from sqlalchemy.orm import Session
                    sync_db = Session(bind=self.db.bind)
                    await self.membership_service.assign_free_membership(user_id, sync_db)
                    sync_db.close()
                    logger.info("已为新认证律师分配免费会员", user_id=user_id)
                except Exception as e:
                    logger.error("分配免费会员失败", error=str(e), user_id=user_id)
                    # 不影响认证流程，只记录错误
            
            # 发送通过通知
            await self.notification_service.send_certification_approved_notification(user_id)
            
            logger.info(
                "律师认证审核通过",
                cert_id=cert_id,
                user_id=user_id,
                admin_id=admin_id
            )
            
            return {
                'approved': True,
                'user_id': str(user_id),
                'message': '认证审核通过'
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("认证审核失败", error=str(e), cert_id=cert_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="认证审核失败"
            )
    
    async def reject_certification(
        self,
        cert_id: str,
        admin_id: str,
        review_notes: str
    ) -> Dict[str, Any]:
        """
        管理员审核拒绝
        
        Args:
            cert_id: 认证申请ID
            admin_id: 管理员ID
            review_notes: 拒绝原因
        
        Returns:
            审核结果
        """
        try:
            # 更新认证状态
            result = await self.db.execute(
                update(LawyerCertificationRequest)
                .where(LawyerCertificationRequest.id == cert_id)
                .values(
                    status='rejected',
                    reviewed_by=admin_id,
                    reviewed_at=datetime.now(),
                    admin_review_notes=review_notes
                )
                .returning(LawyerCertificationRequest.user_id)
            )
            
            user_id = result.scalar_one()
            await self.db.commit()
            
            # 发送拒绝通知
            await self.notification_service.send_certification_rejected_notification(
                user_id, review_notes
            )
            
            logger.info(
                "律师认证审核拒绝",
                cert_id=cert_id,
                user_id=user_id,
                admin_id=admin_id
            )
            
            return {
                'rejected': True,
                'user_id': str(user_id),
                'message': '认证审核未通过'
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("认证审核失败", error=str(e), cert_id=cert_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="认证审核失败"
            )
    
    async def get_pending_certifications(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取待审核的认证申请列表
        
        Args:
            limit: 限制数量
            offset: 偏移量
        
        Returns:
            待审核认证申请列表
        """
        try:
            result = await self.db.execute(
                select(LawyerCertificationRequest, User.email, User.full_name)
                .join(User, LawyerCertificationRequest.user_id == User.id)
                .where(LawyerCertificationRequest.status.in_(['pending', 'under_review']))
                .order_by(LawyerCertificationRequest.submitted_at.asc())
                .limit(limit)
                .offset(offset)
            )
            
            certifications = []
            for cert, email, full_name in result.fetchall():
                certifications.append({
                    'certification_id': str(cert.id),
                    'user_id': str(cert.user_id),
                    'user_email': email,
                    'user_full_name': full_name,
                    'lawyer_name': cert.lawyer_name,
                    'license_number': cert.license_number,
                    'law_firm': cert.law_firm,
                    'practice_areas': json.loads(cert.practice_areas) if cert.practice_areas else [],
                    'years_of_experience': cert.years_of_experience,
                    'status': cert.status,
                    'submitted_at': cert.submitted_at.isoformat(),
                    'certificate_file_path': cert.certificate_file_path
                })
            
            return certifications
            
        except Exception as e:
            logger.error("获取待审核认证申请失败", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取待审核认证申请失败"
            )


