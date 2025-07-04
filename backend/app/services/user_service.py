"""
用户服务
包含用户相关的业务逻辑和数据库操作
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
import structlog
import uuid

from app.models.user import User, Role, UserRole, Profile, UserStatus
from app.models.tenant import Tenant
from app.core.security import get_password_hash, verify_password

logger = structlog.get_logger()


class UserService:
    """用户服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_user(
        self,
        email: str,
        password: str,
        role_name: str,
        tenant_id: str,
        full_name: Optional[str] = None,
        phone_number: Optional[str] = None
    ) -> User:
        """
        创建新用户
        
        Args:
            email: 用户邮箱
            password: 密码
            role_name: 角色名称
            tenant_id: 租户ID
            full_name: 全名
            phone_number: 电话号码
        
        Returns:
            创建的用户对象
        
        Raises:
            HTTPException: 创建失败时抛出异常
        """
        try:
            # 检查邮箱是否已存在
            existing_user = await self.get_user_by_email(email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已被注册"
                )
            
            # 检查角色是否存在
            role = await self.get_role_by_name(role_name)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"角色'{role_name}'不存在"
                )
            
            # 创建用户
            hashed_password = get_password_hash(password)
            user = User(
                id=str(uuid.uuid4()),
                email=email,
                username=email.split('@')[0],  # 使用邮箱前缀作为用户名
                password_hash=hashed_password,
                tenant_id=tenant_id,
                status=UserStatus.ACTIVE
            )
            
            self.db.add(user)
            await self.db.flush()
            
            # 分配角色
            user_role = UserRole(
                user_id=user.id,
                role_id=role.id
            )
            self.db.add(user_role)
            
            # 创建用户档案
            if full_name or phone_number:
                profile = Profile(
                    user_id=user.id,
                    full_name=full_name
                )
                self.db.add(profile)
            
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info("用户创建成功", user_id=user.id, email=email)
            return user
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error("用户创建失败", error=str(e), email=email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="用户创建失败"
            )
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        根据邮箱获取用户
        
        Args:
            email: 用户邮箱
        
        Returns:
            用户对象或None
        """
        try:
            stmt = select(User).where(User.email == email)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("获取用户失败", error=str(e), email=email)
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        根据ID获取用户
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户对象或None
        """
        try:
            stmt = (
                select(User)
                .options(selectinload(User.user_roles))
                .where(User.id == user_id)
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("获取用户失败", error=str(e), user_id=user_id)
            return None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        验证用户凭据
        
        Args:
            email: 用户邮箱
            password: 密码
        
        Returns:
            验证成功返回用户对象，否则返回None
        """
        try:
            user = await self.get_user_by_email(email)
            if not user:
                return None
            
            if not verify_password(password, user.password_hash):
                return None
            
            if user.status != UserStatus.ACTIVE:
                return None
            
            logger.info("用户认证成功", user_id=user.id, email=email)
            return user
            
        except Exception as e:
            logger.error("用户认证失败", error=str(e), email=email)
            return None
    
    async def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            **kwargs: 更新字段
        
        Returns:
            更新后的用户对象
        """
        try:
            # 如果包含密码，需要哈希处理
            if 'password' in kwargs:
                kwargs['password_hash'] = get_password_hash(kwargs.pop('password'))
            
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(**kwargs)
                .returning(User)
            )
            
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                await self.db.commit()
                logger.info("用户更新成功", user_id=user_id)
            
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error("用户更新失败", error=str(e), user_id=user_id)
            return None
    
    async def delete_user(self, user_id: str) -> bool:
        """
        删除用户（软删除）
        
        Args:
            user_id: 用户ID
        
        Returns:
            删除是否成功
        """
        try:
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(status="deleted")
            )
            
            await self.db.execute(stmt)
            await self.db.commit()
            
            logger.info("用户删除成功", user_id=user_id)
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error("用户删除失败", error=str(e), user_id=user_id)
            return False
    
    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """
        根据名称获取角色
        
        Args:
            name: 角色名称
        
        Returns:
            角色对象或None
        """
        try:
            stmt = select(Role).where(Role.name == name)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("获取角色失败", error=str(e), name=name)
            return None
    
    async def get_user_roles(self, user_id: str) -> List[str]:
        """
        获取用户角色列表
        
        Args:
            user_id: 用户ID
        
        Returns:
            角色名称列表
        """
        try:
            stmt = (
                select(Role.name)
                .join(UserRole, Role.id == UserRole.role_id)
                .where(UserRole.user_id == user_id)
            )
            result = await self.db.execute(stmt)
            return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error("获取用户角色失败", error=str(e), user_id=user_id)
            return []
    
    async def get_user_profile(self, user_id: str) -> Optional[Profile]:
        """
        获取用户档案
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户档案对象或None
        """
        try:
            stmt = select(Profile).where(Profile.user_id == user_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("获取用户档案失败", error=str(e), user_id=user_id)
            return None
    
    async def update_last_login(self, user_id: str) -> None:
        """
        更新用户最后登录时间
        
        Args:
            user_id: 用户ID
        """
        try:
            from datetime import datetime
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(last_login=datetime.utcnow())
            )
            await self.db.execute(stmt)
            await self.db.commit()
            
            logger.info("更新最后登录时间", user_id=user_id)
            
        except Exception as e:
            logger.error("更新最后登录时间失败", error=str(e), user_id=user_id) 