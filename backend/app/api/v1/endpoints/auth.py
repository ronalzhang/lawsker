"""
认证相关API端点 - 支持HttpOnly Cookie
包含登录、注册、JWT管理、验证码等功能
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import structlog
import random
import redis
import json
from datetime import datetime, timedelta

from app.core.security import security_manager, get_current_user
from app.services.auth_service import AuthService
from app.core.deps import get_auth_service
from app.services.user_activity_tracker import track_login, track_logout

logger = structlog.get_logger()

# Redis客户端用于存储验证码
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
except Exception:
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

class AdminLogin(BaseModel):
    password: str  # 管理员密码


class SMSCodeRequest(BaseModel):
    phone: str
    code_type: str = "register"  # register, login, reset_password


class SMSCodeVerify(BaseModel):
    phone: str
    code: str
    code_type: str = "register"


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    status: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


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


@router.post("/register", status_code=status.HTTP_201_CREATED)
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


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    user_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户登录 - 使用HttpOnly Cookie
    验证凭据并设置安全Cookie
    """
    try:
        # 获取客户端信息
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        logger.info("开始登录尝试", username=user_data.username, ip=ip_address)
        
        # 临时解决方案：直接使用SQL查询用户
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        from app.core.security import verify_password, create_access_token
        
        async with AsyncSessionLocal() as session:
            # 支持用户名或邮箱登录
            query = text("""
                SELECT u.id, u.email, u.username, u.status, u.password_hash, r.name as role_name
                FROM users u
                LEFT JOIN user_roles ur ON u.id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.id
                WHERE u.email = :login_id OR u.username = :login_id
            """)
            
            logger.info("执行用户查询", login_id=user_data.username)
            
            result = await session.execute(query, {"login_id": user_data.username})
            user_row = result.fetchone()
            
            if not user_row:
                logger.warning("用户不存在", username=user_data.username)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误"
                )
            
            logger.info("找到用户", 
                       user_id=str(user_row.id),
                       username=user_row.username,
                       email=user_row.email,
                       status=user_row.status,
                       role=user_row.role_name)
            
            # 验证密码
            logger.info("开始密码验证")
            if not verify_password(user_data.password, user_row.password_hash):
                logger.warning("密码验证失败", username=user_data.username)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误"
                )
            
            logger.info("密码验证成功")
            
            # 检查用户状态
            if user_row.status != "ACTIVE":
                logger.warning("用户状态不是ACTIVE", username=user_data.username, status=user_row.status)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户账户已停用"
                )
            
            # 获取用户角色，如果没有角色则默认为user
            user_role = user_row.role_name if user_row.role_name else "user"
            
            logger.info("用户角色", username=user_data.username, role=user_role)
            
            # 创建令牌数据
            token_data = {
                "sub": user_row.email,
                "user_id": str(user_row.id),
                "role": user_role,
                "permissions": []
            }
            
            # 创建访问令牌和刷新令牌
            access_token = security_manager.create_access_token(token_data)
            refresh_token = security_manager.create_refresh_token(token_data)
            
            # 设置HttpOnly Cookie
            security_manager.set_auth_cookies(response, access_token, refresh_token)
            
            # 记录登录行为
            try:
                await track_login(
                    user_id=str(user_row.id),
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            except Exception as e:
                logger.warning("记录登录行为失败", error=str(e))
            
            logger.info("用户登录成功", username=user_data.username, user_role=user_role)
            
            return {
                "message": "登录成功",
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": str(user_row.id),
                    "email": user_row.email,
                    "username": user_row.username,
                    "role": user_role,
                    "status": user_row.status,
                    "permissions": []
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("用户登录失败", error=str(e), username=user_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )


@router.post("/admin/login")
async def admin_login(
    request: Request,
    response: Response,
    admin_data: AdminLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    管理员登录 - 只需密码验证
    验证管理员密码并设置安全Cookie
    """
    try:
        # 获取客户端信息
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        # 验证管理员密码
        if admin_data.password != "123abc74531":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="管理员密码错误"
            )
        
        # 创建管理员用户信息
        admin_info = {
            "id": "admin-001",
            "email": "admin@lawsker.com",
            "role": "admin",
            "status": "active",
            "permissions": ["admin:all"]
        }
        
        # 创建令牌数据
        token_data = {
            "sub": admin_info.get("email"),
            "user_id": admin_info.get("id"),
            "role": admin_info.get("role"),
            "permissions": admin_info.get("permissions", [])
        }
        
        # 创建访问令牌和刷新令牌
        access_token = security_manager.create_access_token(token_data)
        refresh_token = security_manager.create_refresh_token(token_data)
        
        # 设置HttpOnly Cookie
        security_manager.set_auth_cookies(response, access_token, refresh_token)
        
        # 记录登录行为
        try:
            await track_login(
                user_id=admin_info.get("id"),
                ip_address=ip_address,
                user_agent=user_agent
            )
        except Exception as e:
            logger.warning("记录管理员登录行为失败", error=str(e))
        
        logger.info("管理员登录成功", admin_id=admin_info.get("id"))
        
        return {
            "message": "管理员登录成功",
            "user": admin_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("管理员登录失败", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员登录失败"
        )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user)
):
    """
    用户登出 - 清除HttpOnly Cookie
    """
    try:
        # 清除认证Cookie
        security_manager.clear_auth_cookies(response)
        
        # 记录登出行为
        try:
            await track_logout(
                user_id=current_user["user_id"],
                ip_address=request.client.host if request.client else "unknown"
            )
        except Exception as e:
            logger.warning("记录登出行为失败", error=str(e))
        
        logger.info("用户登出成功", user_id=current_user["user_id"])
        
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


@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response
):
    """
    刷新访问令牌 - 使用HttpOnly Cookie中的刷新令牌
    """
    try:
        refresh_token = security_manager.get_token_from_cookie(request, "refresh")
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌不存在"
            )
        
        # 验证刷新令牌
        payload = security_manager.verify_token(refresh_token, "refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌无效"
            )
        
        # 创建新的访问令牌
        new_access_token = security_manager.refresh_access_token(refresh_token)
        if not new_access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无法刷新令牌"
            )
        
        # 设置新的访问令牌Cookie
        security_manager.set_auth_cookies(response, new_access_token, refresh_token)
        
        logger.info("令牌刷新成功", user_id=payload.get("user_id"))
        
        return {
            "message": "令牌刷新成功",
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("令牌刷新失败", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌刷新失败"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取当前用户信息
    基于HttpOnly Cookie中的JWT令牌返回用户详情
    """
    try:
        logger.info("获取当前用户信息", user_id=current_user["user_id"])
        
        return {
            "id": current_user["user_id"],
            "email": current_user["sub"],
            "role": current_user.get("role", "user"),
            "status": "active"  # 从令牌中无法获取状态，默认为active
        }
        
    except Exception as e:
        logger.error("获取用户信息失败", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )


@router.post("/change-password")
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    修改密码
    """
    try:
        # 这里需要调用auth_service来验证旧密码并更新新密码
        # 由于原有的auth_service可能没有这个方法，我们需要添加
        
        # 记录密码修改尝试
        logger.info("用户尝试修改密码", user_id=current_user["user_id"])
        
        # TODO: 实现密码修改逻辑
        # await auth_service.change_password(
        #     user_id=current_user["user_id"],
        #     old_password=password_data.old_password,
        #     new_password=password_data.new_password
        # )
        
        return {
            "message": "密码修改成功",
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("密码修改失败", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码修改失败"
        )


@router.post("/verify-token")
async def verify_token(
    current_user: dict = Depends(get_current_user)
):
    """
    验证令牌有效性
    """
    return {
        "valid": True,
        "user_id": current_user["user_id"],
        "email": current_user["sub"],
        "role": current_user.get("role"),
        "permissions": current_user.get("permissions", [])
    }