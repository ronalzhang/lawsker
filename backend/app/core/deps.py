"""
依赖注入模块
包含数据库、认证、服务等依赖
"""

from typing import AsyncGenerator, Dict, Any, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import logging

from app.core.database import AsyncSessionLocal, get_db
from app.core.config import settings
from app.services.auth_service import AuthService
from app.services.config_service import SystemConfigService
from app.services.ai_service import AIDocumentService

logger = logging.getLogger(__name__)

# HTTPBearer安全方案
security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    
    Yields:
        AsyncSession: 异步数据库会话
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_auth_service() -> AuthService:
    """
    获取认证服务实例
    
    Returns:
        AuthService: 认证服务实例
    """
    async with AsyncSessionLocal() as session:
        return AuthService(session)


def require_roles(*required_roles: str):
    """
    创建角色权限检查依赖
    
    Args:
        *required_roles: 允许的角色列表
    
    Returns:
        依赖函数
    """
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_roles = current_user.get("roles", [])
        
        # 检查是否有任何一个允许的角色
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下角色之一: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return role_checker


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    获取当前用户
    从JWT令牌中解析用户信息
    """
    try:
        # 解析JWT令牌
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌"
            )
        
        # 返回用户信息
        return {
            "id": user_id,
            "email": payload.get("email"),
            "roles": payload.get("roles", []),
            "tenant_id": payload.get("tenant_id"),
            "status": payload.get("status", "active")
        }
        
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已过期"
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌"
        )


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取当前活跃用户
    
    Args:
        current_user: 当前用户信息
    
    Returns:
        Dict[str, Any]: 活跃用户信息
    
    Raises:
        HTTPException: 用户非活跃状态时抛出异常
    """
    if current_user.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户未激活"
        )
    return current_user


# 预定义角色权限依赖
require_admin = require_roles("admin", "super_admin")
require_lawyer = require_roles("lawyer", "admin", "super_admin") 
require_sales = require_roles("sales", "admin", "super_admin")
require_institution = require_roles("institution_admin", "admin", "super_admin")


async def get_config_service(db: AsyncSession = Depends(get_db)) -> SystemConfigService:
    """获取配置管理服务"""
    return SystemConfigService(db)


async def get_ai_service(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> AIDocumentService:
    """获取AI文书生成服务"""
    tenant_id = None
    if current_user.get("tenant_id"):
        try:
            tenant_id = UUID(current_user["tenant_id"])
        except (ValueError, TypeError):
            logger.warning(f"无效的tenant_id格式: {current_user.get('tenant_id')}")
    
    return AIDocumentService(db, tenant_id)


async def require_lawyer_role(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """要求律师角色权限"""
    if "lawyer" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要律师权限"
        )
    return current_user


async def require_admin_role(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """要求管理员角色权限"""
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def get_current_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取当前管理员用户"""
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user 