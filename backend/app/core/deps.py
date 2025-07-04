"""
依赖注入模块
提供数据库会话、认证等依赖项
"""

from typing import AsyncGenerator, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.services.auth_service import AuthService

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


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """
    获取认证服务实例
    
    Args:
        db: 数据库会话
    
    Returns:
        AuthService: 认证服务实例
    """
    return AuthService(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """
    获取当前认证用户
    
    Args:
        credentials: HTTP Bearer凭据
        auth_service: 认证服务
    
    Returns:
        Dict[str, Any]: 当前用户信息
    
    Raises:
        HTTPException: 认证失败时抛出异常
    """
    try:
        token = credentials.credentials
        user_info = await auth_service.get_current_user_from_token(token)
        return user_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"}
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


def require_roles(*allowed_roles: str):
    """
    角色权限装饰器
    
    Args:
        *allowed_roles: 允许的角色列表
    
    Returns:
        依赖函数
    """
    async def check_user_role(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        user_roles = current_user.get("roles", [])
        
        # 检查用户是否拥有任一允许的角色
        if not any(role in user_roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        return current_user
    
    return check_user_role


def require_tenant_access():
    """
    租户访问权限检查
    
    Returns:
        依赖函数
    """
    async def check_tenant_access(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        if not current_user.get("tenant_id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无租户访问权限"
            )
        
        return current_user
    
    return check_tenant_access


# 常用角色依赖
require_admin = require_roles("admin", "super_admin")
require_lawyer = require_roles("lawyer", "admin", "super_admin") 
require_sales = require_roles("sales", "admin", "super_admin")
require_institution = require_roles("institution_admin", "admin", "super_admin") 