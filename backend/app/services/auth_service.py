"""
认证服务
整合JWT令牌管理和用户验证功能
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import structlog

from app.services.user_service import UserService
from app.core.security import (
    create_access_token,
    verify_token,
    generate_token_data,
    extract_user_from_token,
    validate_password_strength
)

logger = structlog.get_logger()


class AuthService:
    """认证服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)
    
    async def register_user(
        self,
        email: str,
        password: str,
        role: str,
        tenant_id: str,
        full_name: Optional[str] = None,
        phone_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        用户注册
        
        Args:
            email: 用户邮箱
            password: 密码
            role: 角色
            tenant_id: 租户ID
            full_name: 全名
            phone_number: 电话号码
        
        Returns:
            注册结果
        
        Raises:
            HTTPException: 注册失败时抛出异常
        """
        try:
            # 验证密码强度
            if not validate_password_strength(password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="密码强度不足，需包含大小写字母和数字，至少8位"
                )
            
            # 创建用户
            user = await self.user_service.create_user(
                email=email,
                password=password,
                role_name=role,
                tenant_id=tenant_id,
                full_name=full_name,
                phone_number=phone_number
            )
            
            logger.info("用户注册成功", user_id=user.id, email=email)
            
            return {
                "message": "注册成功",
                "user_id": user.id,
                "email": user.email,
                "status": "success"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("用户注册失败", error=str(e), email=email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="注册失败，请稍后重试"
            )
    
    async def authenticate_and_create_token(
        self,
        username_or_email: str,
        password: str
    ) -> Dict[str, Any]:
        """
        用户认证并创建令牌
        
        Args:
            username_or_email: 用户名或邮箱
            password: 密码
        
        Returns:
            包含令牌和用户信息的字典
        
        Raises:
            HTTPException: 认证失败时抛出异常
        """
        try:
            # 验证用户凭据
            user = await self.user_service.authenticate_user(username_or_email, password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误"
                )
            
            # 获取用户角色
            roles = await self.user_service.get_user_roles(user.id)
            primary_role = roles[0] if roles else "user"
            
            # 生成JWT令牌
            token_data = generate_token_data(
                user_id=str(user.id),
                email=user.email,
                role=primary_role,
                tenant_id=str(user.tenant_id)
            )
            
            access_token = create_access_token(token_data)
            
            # 更新最后登录时间
            await self.user_service.update_last_login(user.id)
            
            logger.info("用户登录成功", user_id=user.id, username_or_email=username_or_email)
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 1800,  # 30分钟
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "role": primary_role,
                    "status": user.status.value if hasattr(user.status, 'value') else str(user.status)
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("用户登录失败", error=str(e), username_or_email=username_or_email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="登录失败，请稍后重试"
            )
    
    async def get_current_user_from_token(self, token: str) -> Dict[str, Any]:
        """
        从令牌获取当前用户信息
        
        Args:
            token: JWT令牌
        
        Returns:
            用户信息字典
        
        Raises:
            HTTPException: 令牌无效时抛出异常
        """
        try:
            # 提取用户信息
            user_info = extract_user_from_token(token)
            
            # 从数据库获取最新用户信息
            user = await self.user_service.get_user_by_id(user_info["user_id"])
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户不存在"
                )
            
            if user.status.value != "active":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户账户已停用"
                )
            
            # 获取用户角色
            roles = await self.user_service.get_user_roles(user.id)
            
            return {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "roles": roles,
                "status": user.status.value,
                "tenant_id": str(user.tenant_id),
                "profile": {
                    "full_name": user.full_name,
                    "phone_number": user.phone_number
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("获取当前用户失败", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌验证失败"
            )
    
    async def refresh_access_token(self, current_token: str) -> Dict[str, Any]:
        """
        刷新访问令牌
        
        Args:
            current_token: 当前令牌
        
        Returns:
            新的令牌信息
        
        Raises:
            HTTPException: 刷新失败时抛出异常
        """
        try:
            # 验证当前令牌
            user_info = extract_user_from_token(current_token)
            
            # 检查用户状态
            user = await self.user_service.get_user_by_id(user_info["user_id"])
            if not user or user.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户状态异常"
                )
            
            # 生成新令牌
            token_data = generate_token_data(
                user_id=str(user.id),
                email=user.email,
                role=user_info["role"],
                tenant_id=str(user.tenant_id)
            )
            
            new_access_token = create_access_token(token_data)
            
            logger.info("令牌刷新成功", user_id=user.id)
            
            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": 1800
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("令牌刷新失败", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌刷新失败"
            )
    
    def validate_token_format(self, authorization: str) -> str:
        """
        验证并提取令牌格式
        
        Args:
            authorization: Authorization头部值
        
        Returns:
            提取的令牌
        
        Raises:
            HTTPException: 格式无效时抛出异常
        """
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="缺少Authorization头部"
            )
        
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的认证方案，需要Bearer令牌"
                )
            return token
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的Authorization头部格式"
            ) 