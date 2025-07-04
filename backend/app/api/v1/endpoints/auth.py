"""
认证相关API端点
包含登录、注册、JWT管理等功能
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import structlog

from app.services.auth_service import AuthService
from app.core.deps import get_auth_service, get_current_user

logger = structlog.get_logger()
security = HTTPBearer()

router = APIRouter()


# Pydantic模型
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    role: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    status: str


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户注册
    支持律师、销售、机构管理员角色注册
    """
    try:
        # 默认租户ID（实际应用中应该根据注册来源确定）
        tenant_id = "ba5a72ab-0ba5-4de6-b6a3-989a4225e258"
        
        result = await auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            role=user_data.role,
            tenant_id=tenant_id,
            full_name=user_data.full_name
        )
        
        logger.info("用户注册成功", email=user_data.email, role=user_data.role)
        
        return {
            "message": "注册成功",
            "user_id": result["user_id"],
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("用户注册失败", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户登录
    验证凭据并返回JWT令牌
    """
    try:
        result = await auth_service.authenticate_and_create_token(
            email=user_data.email,
            password=user_data.password
        )
        
        logger.info("用户登录成功", email=user_data.email)
        
        return {
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("用户登录失败", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    用户登出
    可选择性撤销JWT令牌
    """
    try:
        # TODO: 实现登出逻辑
        # 1. 验证JWT令牌
        # 2. 将令牌加入黑名单（可选）
        # 3. 清理会话信息
        
        logger.info("用户登出")
        
        return {
            "message": "登出成功",
            "status": "success"
        }
    except Exception as e:
        logger.error("用户登出失败", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="登出失败"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取当前用户信息
    基于JWT令牌返回用户详情
    """
    try:
        logger.info("获取当前用户信息", user_id=current_user["id"])
        
        # 获取主要角色（第一个角色）
        primary_role = current_user["roles"][0] if current_user["roles"] else "user"
        
        return {
            "id": current_user["id"],
            "email": current_user["email"],
            "role": primary_role,
            "status": current_user["status"]
        }
    except Exception as e:
        logger.error("获取用户信息失败", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )


@router.post("/refresh")
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    刷新JWT令牌
    获取新的访问令牌
    """
    try:
        result = await auth_service.refresh_access_token(credentials.credentials)
        
        logger.info("JWT令牌刷新成功")
        
        return {
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("令牌刷新失败", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌刷新失败"
        ) 