"""
安全模块
包含JWT令牌管理、密码哈希等安全功能
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# 密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    
    Args:
        data: 令牌载荷数据
        expires_delta: 过期时间增量
    
    Returns:
        JWT令牌字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        logger.info("JWT令牌创建成功", user_id=data.get("sub"))
        return encoded_jwt
    except Exception as e:
        logger.error("JWT令牌创建失败", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌创建失败"
        )


def verify_token(token: str) -> Dict[str, Any]:
    """
    验证JWT令牌
    
    Args:
        token: JWT令牌字符串
    
    Returns:
        解码后的令牌载荷
    
    Raises:
        HTTPException: 令牌无效或过期
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        # 检查令牌是否过期
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌已过期"
            )
        
        logger.info("JWT令牌验证成功", user_id=payload.get("sub"))
        return payload
        
    except jwt.PyJWTError as e:
        logger.error("JWT令牌验证失败", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌无效"
        )


def get_password_hash(password: str) -> str:
    """
    生成密码哈希值
    
    Args:
        password: 明文密码
    
    Returns:
        密码哈希值
    """
    try:
        hashed = pwd_context.hash(password)
        logger.info("密码哈希生成成功")
        return hashed
    except Exception as e:
        logger.error("密码哈希生成失败", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码处理失败"
        )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 密码哈希值
    
    Returns:
        验证结果
    """
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        logger.info("密码验证完成", result=result)
        return result
    except Exception as e:
        logger.error("密码验证失败", error=str(e))
        return False


def generate_token_data(user_id: str, email: str, role: str, tenant_id: str) -> Dict[str, Any]:
    """
    生成JWT令牌载荷数据
    
    Args:
        user_id: 用户ID
        email: 用户邮箱
        role: 用户角色
        tenant_id: 租户ID
    
    Returns:
        令牌载荷数据
    """
    return {
        "sub": user_id,  # subject - 用户ID
        "email": email,
        "role": role,
        "tenant_id": tenant_id,
        "type": "access"
    }


def extract_user_from_token(token: str) -> Dict[str, Any]:
    """
    从JWT令牌中提取用户信息
    
    Args:
        token: JWT令牌
    
    Returns:
        用户信息字典
    """
    payload = verify_token(token)
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role"),
        "tenant_id": payload.get("tenant_id")
    }


# 密码强度验证
def validate_password_strength(password: str) -> bool:
    """
    验证密码强度
    
    Args:
        password: 密码字符串
    
    Returns:
        验证结果
    """
    if len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    return has_upper and has_lower and has_digit


def generate_reset_token(email: str) -> str:
    """
    生成密码重置令牌
    
    Args:
        email: 用户邮箱
    
    Returns:
        重置令牌
    """
    data = {
        "email": email,
        "type": "reset",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)  # 1小时有效期
    }
    return jwt.encode(data, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_reset_token(token: str) -> str:
    """
    验证密码重置令牌
    
    Args:
        token: 重置令牌
    
    Returns:
        用户邮箱
    
    Raises:
        HTTPException: 令牌无效或过期
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        if payload.get("type") != "reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的重置令牌"
            )
        
        return payload.get("email")
        
    except jwt.PyJWTError as e:
        logger.error("重置令牌验证失败", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="重置令牌无效或已过期"
        ) 