"""
用户管理相关API端点
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class UserProfile(BaseModel):
    full_name: str
    phone_number: str


@router.get("/profile")
async def get_user_profile():
    """获取用户资料"""
    return {"message": "用户资料获取接口"}


@router.put("/profile") 
async def update_user_profile(profile: UserProfile):
    """更新用户资料"""
    return {"message": "用户资料更新接口"} 