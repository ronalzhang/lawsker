"""
统计API端点
提供仪表盘和统计数据
"""

from datetime import datetime, date
from typing import Dict, List, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.case import Case, CaseStatus
from app.models.finance import Transaction, CommissionSplit
from app.models.statistics import SystemStatistics, UserActivityLog, DataUploadRecord, TaskPublishRecord
from app.models.lawyer_review import DocumentReviewTask, ReviewStatus

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取仪表盘统计数据"""
    
    user_role = current_user.get("role")
    user_id = UUID(current_user.get("id")) if current_user.get("id") else None
    
    if user_role == "admin":
        return await _get_admin_dashboard_stats(db)
    elif user_role == "lawyer" and user_id:
        return await _get_lawyer_dashboard_stats(db, user_id)
    elif user_role == "sales" and user_id:
        return await _get_sales_dashboard_stats(db, user_id)
    elif user_role == "institution" and user_id:
        return await _get_institution_dashboard_stats(db, user_id)
    else:
        return await _get_general_dashboard_stats(db)


async def _get_admin_dashboard_stats(db: AsyncSession) -> Dict[str, Any]:
    """获取管理员仪表盘统计"""
    
    # 基本统计
    total_cases = await db.scalar(select(func.count(Case.id))) or 0
    active_cases = await db.scalar(
        select(func.count(Case.id)).where(Case.status.in_([CaseStatus.IN_PROGRESS, CaseStatus.ASSIGNED]))
    ) or 0
    completed_cases = await db.scalar(
        select(func.count(Case.id)).where(Case.status == CaseStatus.COMPLETED)
    ) or 0
    
    # 用户统计
    total_users = await db.scalar(select(func.count(User.id))) or 0
    active_lawyers = await db.scalar(
        select(func.count(User.id)).where(User.role == "lawyer")
    ) or 0
    active_sales = await db.scalar(
        select(func.count(User.id)).where(User.role == "sales")
    ) or 0
    
    # 财务统计
    total_transactions = await db.scalar(select(func.count(Transaction.id))) or 0
    total_amount = await db.scalar(select(func.sum(Transaction.amount))) or 0
    total_commissions = await db.scalar(select(func.sum(CommissionSplit.amount))) or 0
    
    # 今日数据
    today = date.today()
    today_cases = await db.scalar(
        select(func.count(Case.id)).where(func.date(Case.created_at) == today)
    ) or 0
    today_transactions = await db.scalar(
        select(func.count(Transaction.id)).where(func.date(Transaction.created_at) == today)
    ) or 0
    
    return {
        "total_cases": total_cases,
        "active_cases": active_cases,
        "completed_cases": completed_cases,
        "total_users": total_users,
        "active_lawyers": active_lawyers,
        "active_sales": active_sales,
        "total_transactions": total_transactions,
        "total_amount": float(total_amount),
        "total_commissions": float(total_commissions),
        "today_cases": today_cases,
        "today_transactions": today_transactions,
        "success_rate": round((completed_cases / total_cases * 100) if total_cases > 0 else 0, 2),
        "avg_case_value": round(float(total_amount) / total_cases if total_cases > 0 else 0, 2),
    }


async def _get_lawyer_dashboard_stats(db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
    """获取律师仪表盘统计"""
    
    # 律师案件统计
    my_cases = await db.scalar(
        select(func.count(Case.id)).where(Case.assigned_to_user_id == user_id)
    ) or 0
    active_cases = await db.scalar(
        select(func.count(Case.id)).where(
            and_(Case.assigned_to_user_id == user_id, Case.status == CaseStatus.IN_PROGRESS)
        )
    ) or 0
    completed_cases = await db.scalar(
        select(func.count(Case.id)).where(
            and_(Case.assigned_to_user_id == user_id, Case.status == CaseStatus.COMPLETED)
        )
    ) or 0
    
    # 收入统计
    total_earnings = await db.scalar(
        select(func.sum(CommissionSplit.amount)).where(
            and_(CommissionSplit.user_id == user_id, CommissionSplit.status == "paid")
        )
    ) or 0
    
    pending_earnings = await db.scalar(
        select(func.sum(CommissionSplit.amount)).where(
            and_(CommissionSplit.user_id == user_id, CommissionSplit.status == "pending")
        )
    ) or 0
    
    # 本月收入
    this_month_start = date.today().replace(day=1)
    this_month_earnings = await db.scalar(
        select(func.sum(CommissionSplit.amount)).where(
            and_(
                CommissionSplit.user_id == user_id,
                CommissionSplit.status == "paid",
                func.date(CommissionSplit.paid_at) >= this_month_start
            )
        )
    ) or 0
    
    # 审核任务统计
    review_tasks = await db.scalar(
        select(func.count(DocumentReviewTask.id)).where(DocumentReviewTask.lawyer_id == user_id)
    ) or 0
    pending_reviews = await db.scalar(
        select(func.count(DocumentReviewTask.id)).where(
            and_(DocumentReviewTask.lawyer_id == user_id, DocumentReviewTask.status == ReviewStatus.PENDING)
        )
    ) or 0
    
    return {
        "my_cases": my_cases,
        "active_cases": active_cases,
        "completed_cases": completed_cases,
        "total_earnings": float(total_earnings),
        "pending_earnings": float(pending_earnings),
        "this_month_earnings": float(this_month_earnings),
        "review_tasks": review_tasks,
        "pending_reviews": pending_reviews,
        "success_rate": round((completed_cases / my_cases * 100) if my_cases > 0 else 0, 2),
        "avg_case_value": round(float(total_earnings) / completed_cases if completed_cases > 0 else 0, 2),
    }


async def _get_sales_dashboard_stats(db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
    """获取销售仪表盘统计"""
    
    # 销售案件统计
    my_cases = await db.scalar(
        select(func.count(Case.id)).where(Case.sales_user_id == user_id)
    ) or 0
    active_cases = await db.scalar(
        select(func.count(Case.id)).where(
            and_(Case.sales_user_id == user_id, Case.status == CaseStatus.IN_PROGRESS)
        )
    ) or 0
    completed_cases = await db.scalar(
        select(func.count(Case.id)).where(
            and_(Case.sales_user_id == user_id, Case.status == CaseStatus.COMPLETED)
        )
    ) or 0
    
    # 收入统计
    total_earnings = await db.scalar(
        select(func.sum(CommissionSplit.amount)).where(
            and_(CommissionSplit.user_id == user_id, CommissionSplit.status == "paid")
        )
    ) or 0
    
    pending_earnings = await db.scalar(
        select(func.sum(CommissionSplit.amount)).where(
            and_(CommissionSplit.user_id == user_id, CommissionSplit.status == "pending")
        )
    ) or 0
    
    # 本月收入
    this_month_start = date.today().replace(day=1)
    this_month_earnings = await db.scalar(
        select(func.sum(CommissionSplit.amount)).where(
            and_(
                CommissionSplit.user_id == user_id,
                CommissionSplit.status == "paid",
                func.date(CommissionSplit.paid_at) >= this_month_start
            )
        )
    ) or 0
    
    # 数据上传统计
    upload_records = await db.scalar(
        select(func.count(DataUploadRecord.id)).where(DataUploadRecord.user_id == user_id)
    ) or 0
    
    # 任务发布统计
    published_tasks = await db.scalar(
        select(func.count(TaskPublishRecord.id)).where(TaskPublishRecord.user_id == user_id)
    ) or 0
    
    return {
        "my_cases": my_cases,
        "active_cases": active_cases,
        "completed_cases": completed_cases,
        "total_earnings": float(total_earnings),
        "pending_earnings": float(pending_earnings),
        "this_month_earnings": float(this_month_earnings),
        "upload_records": upload_records,
        "published_tasks": published_tasks,
        "success_rate": round((completed_cases / my_cases * 100) if my_cases > 0 else 0, 2),
        "avg_case_value": round(float(total_earnings) / completed_cases if completed_cases > 0 else 0, 2),
    }


async def _get_institution_dashboard_stats(db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
    """获取机构仪表盘统计"""
    
    # 机构案件统计
    my_cases = await db.scalar(
        select(func.count(Case.id)).where(Case.sales_user_id == user_id)
    ) or 0
    active_cases = await db.scalar(
        select(func.count(Case.id)).where(
            and_(Case.sales_user_id == user_id, Case.status == CaseStatus.IN_PROGRESS)
        )
    ) or 0
    completed_cases = await db.scalar(
        select(func.count(Case.id)).where(
            and_(Case.sales_user_id == user_id, Case.status == CaseStatus.COMPLETED)
        )
    ) or 0
    
    # 资金统计
    total_amount = await db.scalar(
        select(func.sum(Case.case_amount)).where(Case.sales_user_id == user_id)
    ) or 0
    
    recovered_amount = await db.scalar(
        select(func.sum(Transaction.amount)).where(
            Transaction.case_id.in_(
                select(Case.id).where(Case.sales_user_id == user_id)
            )
        )
    ) or 0
    
    return {
        "my_cases": my_cases,
        "active_cases": active_cases,
        "completed_cases": completed_cases,
        "total_amount": float(total_amount),
        "recovered_amount": float(recovered_amount),
        "recovery_rate": round((recovered_amount / total_amount * 100) if total_amount > 0 else 0, 2),
        "success_rate": round((completed_cases / my_cases * 100) if my_cases > 0 else 0, 2),
    }


async def _get_general_dashboard_stats(db: AsyncSession) -> Dict[str, Any]:
    """获取通用仪表盘统计"""
    
    # 基本统计
    total_cases = await db.scalar(select(func.count(Case.id))) or 0
    active_cases = await db.scalar(
        select(func.count(Case.id)).where(Case.status.in_([CaseStatus.IN_PROGRESS, CaseStatus.ASSIGNED]))
    ) or 0
    completed_cases = await db.scalar(
        select(func.count(Case.id)).where(Case.status == CaseStatus.COMPLETED)
    ) or 0
    
    return {
        "total_cases": total_cases,
        "active_cases": active_cases,
        "completed_cases": completed_cases,
        "success_rate": round((completed_cases / total_cases * 100) if total_cases > 0 else 0, 2),
    }


@router.get("/recent-activities")
async def get_recent_activities(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """获取最近活动"""
    
    # 管理员可以看到所有活动，其他用户只能看到自己的活动
    query = select(UserActivityLog).order_by(UserActivityLog.created_at.desc()).limit(limit)
    
    if current_user.get("role") != "admin":
        user_id = UUID(current_user.get("id")) if current_user.get("id") else None
        if user_id:
            query = query.where(UserActivityLog.user_id == user_id)
    
    result = await db.execute(query)
    activities = result.scalars().all()
    
    return [
        {
            "id": str(activity.id),
            "action": activity.action,
            "resource_type": activity.resource_type,
            "resource_id": str(activity.resource_id) if activity.resource_id else None,
            "details": activity.details,
            "created_at": activity.created_at.isoformat(),
        }
        for activity in activities
    ]


@router.post("/log-activity")
async def log_user_activity(
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[UUID] = None,
    details: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """记录用户活动"""
    
    user_id = UUID(current_user.get("id")) if current_user.get("id") else None
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    activity = UserActivityLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )
    
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    
    return {
        "id": str(activity.id),
        "action": activity.action,
        "resource_type": activity.resource_type,
        "resource_id": str(activity.resource_id) if activity.resource_id else None,
        "details": activity.details,
        "created_at": activity.created_at.isoformat(),
    }


@router.get("/demo-data")
async def get_demo_dashboard_data() -> Dict[str, Any]:
    """获取演示数据（无需认证）"""
    
    return {
        # 通用统计数据
        "total_tasks": 128,
        "completed_tasks": 95,
        "active_users": 42,
        "total_revenue": 285600,
        "monthly_revenue": 68400,
        "completion_rate": 89.5,
        
        # 管理员仪表盘数据
        "total_cases": 1247,
        "active_cases": 89,
        "completed_cases": 1158,
        "total_users": 156,
        "active_lawyers": 23,
        "active_sales": 45,
        "total_transactions": 2341,
        "total_amount": 15680000.00,
        "total_commissions": 1890000.00,
        "today_cases": 12,
        "today_transactions": 34,
        "success_rate": 92.86,
        "avg_case_value": 12586.50,
        
        # 销售工作台数据
        "published_tasks": 15,
        "uploaded_data": 8,
        "total_earnings": 12580,
        "monthly_earnings": 3200,
        "upload_records": 23,
        
        # 律师工作台数据
        "my_cases": 67,
        "monthly_income": 18500,
        "pending_cases": 3,
        "pending_earnings": 45600.00,
        "this_month_earnings": 28900.00,
        "review_tasks": 12,
        "pending_reviews": 3,
        
        # 机构管理端数据
        "registered_lawyers": 28,
        "recovery_rate": 87.5,
        
        "user_type": "demo",
        "recent_activities": [
            {
                "id": "demo-1",
                "action": "案件分配",
                "resource_type": "case",
                "resource_id": "demo-case-1",
                "details": {"case_number": "LAW-2024-001", "assigned_to": "张律师"},
                "created_at": "2024-01-16T10:30:00Z"
            },
            {
                "id": "demo-2", 
                "action": "提现申请",
                "resource_type": "withdrawal",
                "resource_id": "demo-withdrawal-1",
                "details": {"amount": 5000.00, "status": "pending"},
                "created_at": "2024-01-16T09:15:00Z"
            },
            {
                "id": "demo-3",
                "action": "数据上传",
                "resource_type": "upload",
                "resource_id": "demo-upload-1", 
                "details": {"file_name": "client_data_20240116.xlsx", "records": 150},
                "created_at": "2024-01-16T08:45:00Z"
            }
        ]
    } 