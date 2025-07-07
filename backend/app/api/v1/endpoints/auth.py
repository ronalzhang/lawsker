"""
认证相关API端点
包含登录、注册、JWT管理、验证码等功能
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import structlog
import random
import redis
import json
from datetime import datetime, timedelta

from app.services.auth_service import AuthService
from app.core.deps import get_auth_service, get_current_user

logger = structlog.get_logger()
security = HTTPBearer()

# Redis客户端用于存储验证码
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
except:
    redis_client = None

router = APIRouter()


# Pydantic模型
class UserRegister(BaseModel):
    phone: str
    password: str
    role: str
    sms_code: str  # 短信验证码
    email: Optional[EmailStr] = None  # 邮箱改为可选，认证时填写
    full_name: Optional[str] = None   # 真实姓名改为可选，认证时填写


class UserLogin(BaseModel):
    username: str  # 支持用户名或邮箱
    password: str
    role: str      # 添加角色字段


class SMSCodeRequest(BaseModel):
    phone: str
    code_type: str = "register"  # register, login, reset_password


class SMSCodeVerify(BaseModel):
    phone: str
    code: str
    code_type: str = "register"


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    status: str


# 验证码相关API
@router.post("/send-sms-code")
async def send_sms_code(
    request: SMSCodeRequest
):
    """
    发送短信验证码
    支持注册、登录、密码重置等场景
    """
    try:
        # 验证手机号格式
        import re
        if not re.match(r'^1[3-9]\d{9}$', request.phone):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="手机号格式不正确"
            )
        
        # 生成6位验证码
        code = f"{random.randint(100000, 999999)}"
        
        # 构建验证码存储键
        cache_key = f"sms_code:{request.code_type}:{request.phone}"
        
        # 存储验证码到Redis，有效期5分钟
        if redis_client:
            redis_client.setex(cache_key, 300, code)
        else:
            # 如果Redis不可用，使用内存存储（开发环境）
            import app.core.cache as cache
            cache.memory_cache.set(cache_key, {
                "code": code,
                "expires": datetime.now() + timedelta(minutes=5)
            }, expire_seconds=300)
        
        # 构建短信内容
        sms_content = f"【律思客】您的验证码是{code}，5分钟内有效，请勿泄露。"
        
        # TODO: 实际发送短信
        # 这里模拟发送短信，实际应用中需要接入短信服务商
        logger.info(f"模拟发送短信验证码", phone=request.phone, code=code, content=sms_content)
        
        return {
            "message": "验证码发送成功",
            "phone": request.phone,
            "status": "success",
            # 开发环境返回验证码，生产环境应移除
            "debug_code": code if True else None  # 开发模式显示验证码
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("验证码发送失败", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证码发送失败，请稍后重试"
        )


@router.post("/verify-sms-code")
async def verify_sms_code(
    request: SMSCodeVerify
):
    """
    验证短信验证码
    """
    try:
        cache_key = f"sms_code:{request.code_type}:{request.phone}"
        
        # 从Redis获取验证码
        if redis_client:
            stored_code = redis_client.get(cache_key)
        else:
            # 从内存缓存获取
            import app.core.cache as cache
            cache_data = cache.memory_cache.get(cache_key)
            if cache_data and cache_data["expires"] > datetime.now():
                stored_code = cache_data["code"]
            else:
                stored_code = None
        
        if not stored_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码已过期或不存在"
            )
        
        if stored_code != request.code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误"
            )
        
        # 验证成功，删除验证码
        if redis_client:
            redis_client.delete(cache_key)
        else:
            import app.core.cache as cache
            cache.memory_cache.delete(cache_key)
        
        return {
            "message": "验证码验证成功",
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("验证码验证失败", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证码验证失败"
        )


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户注册
    支持律师、销售、机构管理员角色注册
    需要先验证短信验证码
    """
    try:
        # 首先验证短信验证码
        cache_key = f"sms_code:register:{user_data.phone}"
        
        if redis_client:
            stored_code = redis_client.get(cache_key)
        else:
            # 从内存缓存获取
            import app.core.cache as cache
            cache_data = cache.memory_cache.get(cache_key)
            if cache_data and cache_data["expires"] > datetime.now():
                stored_code = cache_data["code"]
            else:
                stored_code = None
        
        if not stored_code or stored_code != user_data.sms_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="短信验证码错误或已过期"
            )
        
        # 验证码正确，删除验证码
        if redis_client:
            redis_client.delete(cache_key)
        else:
            import app.core.cache as cache
            cache.memory_cache.delete(cache_key)
        
        # 默认租户ID（实际应用中应该根据注册来源确定）
        tenant_id = "ba5a72ab-0ba5-4de6-b6a3-989a4225e258"
        
        # 邮箱可以为空，认证时再填写
        email = user_data.email or f"{user_data.phone}@pending.auth"
        
        result = await auth_service.register_user(
            email=email,
            password=user_data.password,
            role=user_data.role,
            tenant_id=tenant_id,
            full_name=user_data.full_name,
            phone_number=user_data.phone
        )
        
        logger.info("用户注册成功", email=user_data.email, role=user_data.role, phone=user_data.phone)
        
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
    支持用户名或邮箱登录，并验证角色
    """
    try:
        # 先尝试演示账号登录
        demo_accounts = {
            "lawyer_demo": {"password": "demo123", "role": "lawyer"},
            "sales_demo": {"password": "demo123", "role": "sales"},
            "institution_demo": {"password": "demo123", "role": "institution"},
            "admin": {"password": "admin123", "role": "admin"}
        }
        
        # 检查是否为演示账号
        if user_data.username in demo_accounts:
            demo_account = demo_accounts[user_data.username]
            if (user_data.password == demo_account["password"] and 
                user_data.role == demo_account["role"]):
                
                # 生成演示用户的JWT令牌
                token_data = {
                    "user_id": f"demo_{user_data.role}",
                    "email": f"{user_data.username}@demo.com",
                    "role": user_data.role,
                    "username": user_data.username
                }
                
                # 创建JWT令牌（简化版本）
                access_token = f"demo_token_{user_data.role}"
                
                logger.info("演示账号登录成功", username=user_data.username, role=user_data.role)
                
                return {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": 3600
                }
        
        # 实际账号登录逻辑
        result = await auth_service.authenticate_and_create_token(
            email=user_data.username,  # 支持用户名或邮箱
            password=user_data.password
        )
        
        logger.info("用户登录成功", username=user_data.username)
        
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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名、密码或角色错误"
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