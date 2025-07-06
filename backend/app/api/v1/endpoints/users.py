"""
用户管理相关API端点
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()


class UserProfile(BaseModel):
    full_name: str
    phone_number: str


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "name": current_user.full_name,
        "role": current_user.role,
        "phone": current_user.phone_number,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }


@router.get("/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """获取用户资料"""
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone_number": current_user.phone_number,
        "role": current_user.role,
        "is_active": current_user.is_active
    }


@router.put("/profile") 
async def update_user_profile(
    profile: UserProfile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户资料"""
    current_user.full_name = profile.full_name
    current_user.phone_number = profile.phone_number
    
    await db.commit()
    await db.refresh(current_user)
    
    return {
        "message": "用户资料更新成功",
        "user": {
            "id": str(current_user.id),
            "full_name": current_user.full_name,
            "phone_number": current_user.phone_number
        }
    } 