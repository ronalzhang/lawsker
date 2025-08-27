"""
统一认证服务
整合邮箱验证、律师证认证和演示账户功能
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert
from fastapi import HTTPException, status
import structlog
import secrets
import hashlib
from datetime import datetime, timedelta

from app.models.user import User, UserStatus, UserRole
from app.models.unified_auth import WorkspaceMapping, DemoAccount
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.core.security import hash_password, verify_password

logger = structlog.get_logger()


class UnifiedAuthService:
    """统一认证服务类 - 基于现有AuthService扩展"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.auth_service = AuthService(db)
        self.email_service = EmailService()
    
    def generate_secure_workspace_id(self) -> str:
        """生成安全的工作台ID"""
        random_bytes = secrets.token_bytes(16)
        hash_object = hashlib.md5(random_bytes)
        return f"ws-{hash_object.hexdigest()[:12]}"
    
    async def register_with_email_verification(
        self,
        email: str,
        password: str,
        full_name: str,
        tenant_id: str,
        phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        邮箱验证注册 - 扩展现有注册功能
        
        Args:
            email: 用户邮箱
            password: 密码
            full_name: 全名
            tenant_id: 租户ID
        
        Returns:
            注册结果
        """
        try:
            # 检查邮箱是否已存在
            existing_user = await self.db.execute(
                select(User).where(User.email == email)
            )
            if existing_user.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已被注册"
                )
            
            # 生成工作台ID
            workspace_id = self.generate_secure_workspace_id()
            
            # 创建用户记录
            user_data = {
                'username': email,  # 使用邮箱作为用户名
                'email': email,
                'password_hash': hash_password(password),
                'full_name': full_name,
                'phone': phone,
                'tenant_id': tenant_id,
                'status': UserStatus.PENDING,
                'workspace_id': workspace_id,
                'account_type': 'pending',
                'email_verified': False,
                'registration_source': 'web'
            }
            
            result = await self.db.execute(
                insert(User).values(**user_data).returning(User.id)
            )
            user_id = result.scalar_one()
            await self.db.commit()
            
            # 发送验证邮件
            verification_token = secrets.token_urlsafe(32)
            await self.email_service.send_verification_email(email, verification_token)
            
            logger.info("用户注册成功，等待邮箱验证", user_id=user_id, email=email)
            
            return {
                'user_id': str(user_id),
                'workspace_id': workspace_id,
                'verification_required': True,
                'message': '注册成功，请检查邮箱完成验证'
            }
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error("用户注册失败", error=str(e), email=email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="注册失败，请稍后重试"
            )
    
    async def verify_email(self, verification_token: str) -> Dict[str, Any]:
        """
        验证邮箱
        
        Args:
            verification_token: 验证令牌
        
        Returns:
            验证结果
        """
        try:
            # 这里应该从缓存或数据库中验证token
            # 简化实现，实际应该有token存储机制
            
            # 更新用户邮箱验证状态
            result = await self.db.execute(
                update(User)
                .where(User.email_verified == False)
                .values(email_verified=True)
                .returning(User.id, User.email)
            )
            
            user_data = result.fetchone()
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="验证令牌无效或已过期"
                )
            
            await self.db.commit()
            
            logger.info("邮箱验证成功", user_id=user_data.id, email=user_data.email)
            
            return {
                'verified': True,
                'user_id': str(user_data.id),
                'message': '邮箱验证成功，请选择身份类型'
            }
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error("邮箱验证失败", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="验证失败，请稍后重试"
            )
    
    async def set_user_identity_and_redirect(
        self,
        user_id: str,
        identity_type: str
    ) -> Dict[str, Any]:
        """
        身份设置和工作台重定向
        
        Args:
            user_id: 用户ID
            identity_type: 身份类型 ('lawyer' 或 'user')
        
        Returns:
            重定向信息
        """
        try:
            # 获取用户信息
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            
            if identity_type == 'lawyer':
                # 律师身份：需要认证
                await self.db.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(account_type='lawyer_pending')
                )
                
                # 创建工作台映射
                await self.create_workspace_mapping(user_id, user.workspace_id, 'lawyer')
                
                await self.db.commit()
                
                return {
                    'redirect_url': f'/lawyer/{user.workspace_id}',
                    'requires_certification': True,
                    'message': '请上传律师证完成认证'
                }
            else:
                # 普通用户：直接激活
                await self.db.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(
                        account_type='user',
                        status=UserStatus.ACTIVE
                    )
                )
                
                # 创建工作台映射
                await self.create_workspace_mapping(user_id, user.workspace_id, 'user')
                
                await self.db.commit()
                
                return {
                    'redirect_url': f'/user/{user.workspace_id}',
                    'requires_certification': False,
                    'message': '账户激活成功'
                }
                
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error("身份设置失败", error=str(e), user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="身份设置失败，请稍后重试"
            )
    
    async def create_workspace_mapping(
        self,
        user_id: str,
        workspace_id: str,
        workspace_type: str
    ):
        """创建工作台映射"""
        await self.db.execute(
            insert(WorkspaceMapping).values(
                user_id=user_id,
                workspace_id=workspace_id,
                workspace_type=workspace_type,
                is_demo=False
            )
        )
    
    async def get_demo_account_data(self, demo_type: str) -> Dict[str, Any]:
        """
        获取演示账户数据 - 委托给专门的演示账户服务
        
        Args:
            demo_type: 演示类型 ('lawyer' 或 'user')
        
        Returns:
            演示账户数据
        """
        try:
            from app.services.demo_account_service import DemoAccountService
            demo_service = DemoAccountService(self.db)
            return await demo_service.get_demo_account_data(demo_type)
            
        except Exception as e:
            logger.error("获取演示账户数据失败", error=str(e), demo_type=demo_type)
            # 返回默认演示数据作为后备
            default_data = self.get_default_demo_data(demo_type)
            return {
                'workspace_id': f'demo-{demo_type}-default',
                'display_name': default_data['display_name'],
                'demo_data': default_data['data'],
                'is_demo': True
            }
    
    def get_default_demo_data(self, demo_type: str) -> Dict[str, Any]:
        """获取默认演示数据"""
        if demo_type == 'lawyer':
            return {
                'display_name': '张律师（演示）',
                'data': {
                    'specialties': ['合同纠纷', '债务催收', '公司法务'],
                    'experience_years': 8,
                    'success_rate': 92.5,
                    'cases_handled': 156,
                    'client_rating': 4.8,
                    'demo_cases': [
                        {'id': 'demo-case-001', 'title': '合同违约纠纷', 'amount': 50000, 'status': '进行中'},
                        {'id': 'demo-case-002', 'title': '债务催收案件', 'amount': 120000, 'status': '已完成'}
                    ]
                }
            }
        else:
            return {
                'display_name': '李先生（演示）',
                'data': {
                    'company': '某科技公司',
                    'cases_published': 3,
                    'total_amount': 180000,
                    'demo_cases': [
                        {'id': 'demo-case-003', 'title': '劳动合同纠纷', 'amount': 30000, 'status': '匹配中'}
                    ]
                }
            }
    
    async def authenticate_and_redirect(
        self,
        username_or_email: str,
        password: str
    ) -> Dict[str, Any]:
        """
        用户认证并返回重定向信息
        
        Args:
            username_or_email: 用户名或邮箱
            password: 密码
        
        Returns:
            认证结果和重定向信息
        """
        try:
            # 使用现有认证服务进行认证
            auth_result = await self.auth_service.authenticate_and_create_token(
                username_or_email, password
            )
            
            # 获取用户工作台信息
            result = await self.db.execute(
                select(User.workspace_id, User.account_type, User.status, User.email_verified)
                .where(User.email == username_or_email)
            )
            
            user_data = result.fetchone()
            
            if user_data:
                # 检查账户状态
                if not user_data.email_verified:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="邮箱尚未验证，请先验证邮箱"
                    )
                
                # 根据账户类型确定重定向URL
                redirect_url = self.determine_redirect_url(user_data.account_type, user_data.workspace_id)
                
                auth_result.update({
                    'redirect_url': redirect_url,
                    'workspace_id': user_data.workspace_id,
                    'account_type': user_data.account_type,
                    'auto_redirect': True,
                    'message': f'登录成功，正在跳转到{self.get_workspace_display_name(user_data.account_type)}...'
                })
                
                logger.info(
                    "用户登录成功，准备重定向", 
                    user_email=username_or_email,
                    account_type=user_data.account_type,
                    redirect_url=redirect_url
                )
            
            return auth_result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("认证失败", error=str(e), username_or_email=username_or_email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="认证失败，请稍后重试"
            )
    
    def determine_redirect_url(self, account_type: str, workspace_id: str) -> str:
        """
        根据账户类型确定重定向URL
        
        Args:
            account_type: 账户类型
            workspace_id: 工作台ID
        
        Returns:
            重定向URL
        """
        redirect_mapping = {
            'lawyer': f'/lawyer/{workspace_id}',
            'lawyer_pending': f'/lawyer/{workspace_id}?certification_required=true',
            'admin': f'/admin/{workspace_id}',
            'user': f'/user/{workspace_id}',
            'pending': '/auth/verify-email'  # 未验证用户重定向到验证页面
        }
        
        return redirect_mapping.get(account_type, f'/user/{workspace_id}')
    
    def get_workspace_display_name(self, account_type: str) -> str:
        """
        获取工作台显示名称
        
        Args:
            account_type: 账户类型
        
        Returns:
            显示名称
        """
        display_names = {
            'lawyer': '律师工作台',
            'lawyer_pending': '律师工作台（待认证）',
            'admin': '管理后台',
            'user': '用户工作台'
        }
        
        return display_names.get(account_type, '工作台')
    
    async def register_optimized(
        self,
        email: str,
        password: str,
        full_name: str,
        identity_type: str,
        tenant_id: str,
        phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        优化的2步注册流程 - 合并注册和身份选择
        
        Args:
            email: 用户邮箱
            password: 密码
            full_name: 全名
            identity_type: 身份类型 ('lawyer' 或 'user')
            tenant_id: 租户ID
            phone: 手机号（可选）
        
        Returns:
            注册结果
        """
        try:
            # 检查邮箱是否已存在
            existing_user = await self.db.execute(
                select(User).where(User.email == email)
            )
            if existing_user.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已被注册"
                )
            
            # 生成工作台ID
            workspace_id = self.generate_secure_workspace_id()
            
            # 根据身份类型设置账户类型
            if identity_type == 'lawyer':
                account_type = 'lawyer_pending'  # 律师需要认证
                status = UserStatus.PENDING
            else:
                account_type = 'user'
                status = UserStatus.PENDING  # 等待邮箱验证
            
            # 创建用户记录
            user_data = {
                'username': email,
                'email': email,
                'password_hash': hash_password(password),
                'full_name': full_name,
                'phone': phone,
                'tenant_id': tenant_id,
                'status': status,
                'workspace_id': workspace_id,
                'account_type': account_type,
                'email_verified': False,
                'registration_source': 'web_optimized'
            }
            
            result = await self.db.execute(
                insert(User).values(**user_data).returning(User.id)
            )
            user_id = result.scalar_one()
            
            # 创建工作台映射
            await self.create_workspace_mapping(user_id, workspace_id, identity_type)
            
            await self.db.commit()
            
            # 发送验证邮件
            verification_token = secrets.token_urlsafe(32)
            await self.email_service.send_verification_email(email, verification_token)
            
            # 如果是律师，自动分配免费会员（邮箱验证后激活）
            if identity_type == 'lawyer':
                from app.services.lawyer_membership_service import LawyerMembershipService
                membership_service = LawyerMembershipService(self.db)
                await membership_service.prepare_free_membership(user_id)
            
            # 如果是普通用户，初始化Credits（邮箱验证后激活）
            if identity_type == 'user':
                from app.services.user_credits_service import UserCreditsService
                credits_service = UserCreditsService(self.db)
                await credits_service.prepare_initial_credits(user_id)
            
            logger.info(
                "优化注册成功，等待邮箱验证", 
                user_id=user_id, 
                email=email, 
                identity_type=identity_type
            )
            
            return {
                'user_id': str(user_id),
                'workspace_id': workspace_id,
                'identity_type': identity_type,
                'verification_required': True,
                'redirect_url': f'/{identity_type}/{workspace_id}',
                'message': '注册成功，请检查邮箱完成验证'
            }
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error("优化注册失败", error=str(e), email=email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="注册失败，请稍后重试"
            )
    
    async def check_email_verification(self, email: str) -> Dict[str, Any]:
        """
        检查邮箱验证状态
        
        Args:
            email: 用户邮箱
        
        Returns:
            验证状态
        """
        try:
            result = await self.db.execute(
                select(User.id, User.email_verified, User.workspace_id, User.account_type)
                .where(User.email == email)
            )
            
            user_data = result.fetchone()
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            
            if user_data.email_verified:
                # 邮箱已验证，激活账户
                await self.db.execute(
                    update(User)
                    .where(User.email == email)
                    .values(status=UserStatus.ACTIVE)
                )
                await self.db.commit()
                
                # 确定重定向URL
                if user_data.account_type == 'lawyer_pending':
                    redirect_url = f'/lawyer/{user_data.workspace_id}'
                else:
                    redirect_url = f'/user/{user_data.workspace_id}'
                
                return {
                    'verified': True,
                    'user_id': str(user_data.id),
                    'redirect_url': redirect_url,
                    'message': '验证成功，账户已激活'
                }
            else:
                return {
                    'verified': False,
                    'message': '邮箱尚未验证，请检查邮件'
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error("检查邮箱验证失败", error=str(e), email=email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="检查验证状态失败"
            )
    
    async def resend_verification_email(self, email: str) -> Dict[str, Any]:
        """
        重新发送验证邮件
        
        Args:
            email: 用户邮箱
        
        Returns:
            发送结果
        """
        try:
            # 检查用户是否存在且未验证
            result = await self.db.execute(
                select(User.id, User.email_verified)
                .where(User.email == email)
            )
            
            user_data = result.fetchone()
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            
            if user_data.email_verified:
                return {
                    'sent': False,
                    'message': '邮箱已验证，无需重复发送'
                }
            
            # 重新发送验证邮件
            verification_token = secrets.token_urlsafe(32)
            await self.email_service.send_verification_email(email, verification_token)
            
            logger.info("重新发送验证邮件", email=email)
            
            return {
                'sent': True,
                'message': '验证邮件已重新发送'
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("重新发送验证邮件失败", error=str(e), email=email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="发送失败，请稍后重试"
            )
    
    async def get_user_redirect_info(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户重定向信息
        
        Args:
            user_id: 用户ID
        
        Returns:
            重定向信息
        """
        try:
            result = await self.db.execute(
                select(User.workspace_id, User.account_type, User.email_verified, User.status)
                .where(User.id == user_id)
            )
            
            user_data = result.fetchone()
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            
            # 检查邮箱验证状态
            if not user_data.email_verified:
                return {
                    'redirect_url': '/auth/verify-email',
                    'message': '请先验证邮箱',
                    'requires_verification': True
                }
            
            # 确定重定向URL
            redirect_url = self.determine_redirect_url(user_data.account_type, user_data.workspace_id)
            
            return {
                'redirect_url': redirect_url,
                'workspace_id': user_data.workspace_id,
                'account_type': user_data.account_type,
                'message': f'正在跳转到{self.get_workspace_display_name(user_data.account_type)}...',
                'requires_verification': False
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("获取用户重定向信息失败", error=str(e), user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取重定向信息失败"
            )


