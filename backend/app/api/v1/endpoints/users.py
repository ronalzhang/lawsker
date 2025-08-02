"""
用户管理相关API端点
"""

from datetime import datetime, date
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.case import Case
from app.models.finance import Payment
from app.models.statistics import DataUploadRecord, TaskPublishRecord

router = APIRouter()


class UserProfile(BaseModel):
    full_name: str
    phone_number: str


@router.get("/stats")
async def get_user_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户统计信息"""
    
    user_id = current_user["id"]
    user_role = current_user.get("roles", [])
    # 从roles列表中提取主要角色，兼容旧的单一role字段
    if isinstance(user_role, list) and user_role:
        user_role = user_role[0]  # 取第一个角色作为主要角色
    elif not user_role:
        user_role = "user"  # 默认角色
    
    try:
        if user_role == "sales":
            # 销售用户统计
            # 发布的任务数
            published_tasks = await db.scalar(
                select(func.count(TaskPublishRecord.id)).where(TaskPublishRecord.user_id == user_id)
            ) or 0
            
            # 上传的数据数
            uploaded_data = await db.scalar(
                select(func.count(DataUploadRecord.id)).where(DataUploadRecord.user_id == user_id)
            ) or 0
            
            # 总收入
            total_earnings = await db.scalar(
                select(func.sum(Payment.amount)).where(
                    and_(Payment.user_id == user_id, Payment.status == "success")
                )
            ) or 0
            
            # 本月收入
            this_month_start = date.today().replace(day=1)
            monthly_earnings = await db.scalar(
                select(func.sum(Payment.amount)).where(
                    and_(
                        Payment.user_id == user_id,
                        Payment.status == "success",
                        func.date(Payment.paid_at) >= this_month_start
                    )
                )
            ) or 0
            
            # 业务量（可以根据实际需求调整）
            business_volume = published_tasks * 100 + uploaded_data * 50
            
            return {
                "user_id": str(user_id),
                "user_role": user_role,
                "published_tasks": published_tasks,
                "uploaded_data": uploaded_data,
                "total_earnings": float(total_earnings),
                "monthly_earnings": float(monthly_earnings),
                "business_volume": business_volume,
                "current_balance": float(total_earnings) * 0.8,  # 假设80%为可用余额
                "stats_updated_at": datetime.now().isoformat()
            }
        
        elif user_role == "lawyer":
            # 律师用户统计
            # 处理的案件数
            total_cases = await db.scalar(
                select(func.count(Case.id)).where(Case.assigned_to_user_id == user_id)
            ) or 0
            
            # 完成的案件数
            completed_cases = await db.scalar(
                select(func.count(Case.id)).where(
                    and_(Case.assigned_to_user_id == user_id, Case.status == "completed")
                )
            ) or 0
            
            # 总收入
            total_earnings = await db.scalar(
                select(func.sum(Payment.amount)).where(
                    and_(Payment.user_id == user_id, Payment.status == "success")
                )
            ) or 0
            
            # 本月收入
            this_month_start = date.today().replace(day=1)
            monthly_earnings = await db.scalar(
                select(func.sum(Payment.amount)).where(
                    and_(
                        Payment.user_id == user_id,
                        Payment.status == "success",
                        func.date(Payment.paid_at) >= this_month_start
                    )
                )
            ) or 0
            
            return {
                "user_id": str(user_id),
                "user_role": user_role,
                "total_cases": total_cases,
                "completed_cases": completed_cases,
                "total_earnings": float(total_earnings),
                "monthly_earnings": float(monthly_earnings),
                "success_rate": round((completed_cases / total_cases * 100) if total_cases > 0 else 0, 2),
                "stats_updated_at": datetime.now().isoformat()
            }
        
        else:
            # 其他用户类型的通用统计
            return {
                "user_id": str(user_id),
                "user_role": user_role,
                "basic_stats": True,
                "stats_updated_at": datetime.now().isoformat()
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户统计信息失败: {str(e)}"
        )


@router.get("/me")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """获取当前用户信息"""
    return {
        "id": str(current_user["id"]),
        "username": current_user.get("username"),
        "email": current_user.get("email"),
        "name": current_user.get("full_name"),
        "role": current_user.get("roles", ["user"])[0] if current_user.get("roles") else "user",
        "phone": current_user.get("phone_number"),
        "is_active": current_user.get("status") == "active",
        "created_at": current_user.get("created_at")
    }


@router.get("/profile")
async def get_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """获取用户资料"""
    return {
        "id": str(current_user["id"]),
        "username": current_user.get("username"),
        "email": current_user.get("email"),
        "full_name": current_user.get("full_name"),
        "phone_number": current_user.get("phone_number"),
        "role": current_user.get("roles", ["user"])[0] if current_user.get("roles") else "user",
        "is_active": current_user.get("status") == "active"
    }


@router.put("/profile") 
async def update_user_profile(
    profile: UserProfile,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """更新用户资料"""
    # 注意：此功能需要重新设计，因为current_user现在是字典而不是数据库对象
    # 暂时返回错误，需要通过service层来更新用户信息
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="用户资料更新功能需要重新实现，请联系管理员"
    ) 