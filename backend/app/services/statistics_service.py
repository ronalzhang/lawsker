"""
统计服务
提供系统统计数据和仪表盘数据
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.statistics import SystemStatistics, UserActivityLog, DataUploadRecord, TaskPublishRecord
from app.models.case import Case, CaseStatus
from app.models.user import User, Role
from app.models.finance import Transaction, CommissionSplit, Wallet
from app.models.lawyer_review import DocumentReviewTask, ReviewStatus


class StatisticsService:
    """统计服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_dashboard_stats(self, user_id: Optional[UUID] = None, user_role: Optional[str] = None) -> Dict[str, Any]:
        """获取仪表盘统计数据"""
        
        if user_role == "admin":
            return await self._get_admin_dashboard_stats()
        elif user_role == "lawyer" and user_id:
            return await self._get_lawyer_dashboard_stats(user_id)
        elif user_role == "sales" and user_id:
            return await self._get_sales_dashboard_stats(user_id)
        elif user_role == "institution" and user_id:
            return await self._get_institution_dashboard_stats(user_id)
        else:
            return await self._get_general_dashboard_stats()
    
    async def _get_admin_dashboard_stats(self) -> Dict[str, Any]:
        """获取管理员仪表盘统计"""
        
        # 基本统计
        total_cases = await self.db.scalar(select(func.count(Case.id))) or 0
        active_cases = await self.db.scalar(
            select(func.count(Case.id)).where(Case.status.in_([CaseStatus.IN_PROGRESS, CaseStatus.ASSIGNED]))
        ) or 0
        completed_cases = await self.db.scalar(
            select(func.count(Case.id)).where(Case.status == CaseStatus.COMPLETED)
        ) or 0
        
        # 用户统计
        total_users = await self.db.scalar(select(func.count(User.id))) or 0
        active_lawyers = await self.db.scalar(
            select(func.count(User.id)).where(User.role == "lawyer")
        ) or 0
        active_sales = await self.db.scalar(
            select(func.count(User.id)).where(User.role == "sales")
        ) or 0
        
        # 财务统计
        total_transactions = await self.db.scalar(select(func.count(Transaction.id))) or 0
        total_amount = await self.db.scalar(select(func.sum(Transaction.amount))) or 0
        total_commissions = await self.db.scalar(select(func.sum(CommissionSplit.amount))) or 0
        
        # 今日数据
        today = date.today()
        today_cases = await self.db.scalar(
            select(func.count(Case.id)).where(func.date(Case.created_at) == today)
        ) or 0
        today_transactions = await self.db.scalar(
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
    
    async def _get_lawyer_dashboard_stats(self, user_id: UUID) -> Dict[str, Any]:
        """获取律师仪表盘统计"""
        
        # 律师案件统计
        my_cases = await self.db.scalar(
            select(func.count(Case.id)).where(Case.assigned_to_user_id == user_id)
        ) or 0
        active_cases = await self.db.scalar(
            select(func.count(Case.id)).where(
                and_(Case.assigned_to_user_id == user_id, Case.status == CaseStatus.IN_PROGRESS)
            )
        ) or 0
        completed_cases = await self.db.scalar(
            select(func.count(Case.id)).where(
                and_(Case.assigned_to_user_id == user_id, Case.status == CaseStatus.COMPLETED)
            )
        ) or 0
        
        # 收入统计
        total_earnings = await self.db.scalar(
            select(func.sum(CommissionSplit.amount)).where(
                and_(CommissionSplit.user_id == user_id, CommissionSplit.status == "paid")
            )
        ) or 0
        
        pending_earnings = await self.db.scalar(
            select(func.sum(CommissionSplit.amount)).where(
                and_(CommissionSplit.user_id == user_id, CommissionSplit.status == "pending")
            )
        ) or 0
        
        # 本月收入
        this_month_start = date.today().replace(day=1)
        this_month_earnings = await self.db.scalar(
            select(func.sum(CommissionSplit.amount)).where(
                and_(
                    CommissionSplit.user_id == user_id,
                    CommissionSplit.status == "paid",
                    func.date(CommissionSplit.paid_at) >= this_month_start
                )
            )
        ) or 0
        
        # 审核任务统计
        review_tasks = await self.db.scalar(
            select(func.count(DocumentReviewTask.id)).where(DocumentReviewTask.lawyer_id == user_id)
        ) or 0
        pending_reviews = await self.db.scalar(
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
    
    async def _get_sales_dashboard_stats(self, user_id: UUID) -> Dict[str, Any]:
        """获取销售仪表盘统计"""
        
        # 销售案件统计
        my_cases = await self.db.scalar(
            select(func.count(Case.id)).where(Case.sales_user_id == user_id)
        ) or 0
        active_cases = await self.db.scalar(
            select(func.count(Case.id)).where(
                and_(Case.sales_user_id == user_id, Case.status == CaseStatus.IN_PROGRESS)
            )
        ) or 0
        completed_cases = await self.db.scalar(
            select(func.count(Case.id)).where(
                and_(Case.sales_user_id == user_id, Case.status == CaseStatus.COMPLETED)
            )
        ) or 0
        
        # 收入统计
        total_earnings = await self.db.scalar(
            select(func.sum(CommissionSplit.amount)).where(
                and_(CommissionSplit.user_id == user_id, CommissionSplit.status == "paid")
            )
        ) or 0
        
        pending_earnings = await self.db.scalar(
            select(func.sum(CommissionSplit.amount)).where(
                and_(CommissionSplit.user_id == user_id, CommissionSplit.status == "pending")
            )
        ) or 0
        
        # 本月收入
        this_month_start = date.today().replace(day=1)
        this_month_earnings = await self.db.scalar(
            select(func.sum(CommissionSplit.amount)).where(
                and_(
                    CommissionSplit.user_id == user_id,
                    CommissionSplit.status == "paid",
                    func.date(CommissionSplit.paid_at) >= this_month_start
                )
            )
        ) or 0
        
        # 数据上传统计
        upload_records = await self.db.scalar(
            select(func.count(DataUploadRecord.id)).where(DataUploadRecord.user_id == user_id)
        ) or 0
        
        # 任务发布统计
        published_tasks = await self.db.scalar(
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
    
    async def _get_institution_dashboard_stats(self, user_id: UUID) -> Dict[str, Any]:
        """获取机构仪表盘统计"""
        
        # 机构案件统计（假设机构用户通过sales_user_id关联）
        my_cases = await self.db.scalar(
            select(func.count(Case.id)).where(Case.sales_user_id == user_id)
        ) or 0
        active_cases = await self.db.scalar(
            select(func.count(Case.id)).where(
                and_(Case.sales_user_id == user_id, Case.status == CaseStatus.IN_PROGRESS)
            )
        ) or 0
        completed_cases = await self.db.scalar(
            select(func.count(Case.id)).where(
                and_(Case.sales_user_id == user_id, Case.status == CaseStatus.COMPLETED)
            )
        ) or 0
        
        # 资金统计
        total_amount = await self.db.scalar(
            select(func.sum(Case.case_amount)).where(Case.sales_user_id == user_id)
        ) or 0
        
        recovered_amount = await self.db.scalar(
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
    
    async def _get_general_dashboard_stats(self) -> Dict[str, Any]:
        """获取通用仪表盘统计"""
        
        # 基本统计
        total_cases = await self.db.scalar(select(func.count(Case.id))) or 0
        active_cases = await self.db.scalar(
            select(func.count(Case.id)).where(Case.status.in_([CaseStatus.IN_PROGRESS, CaseStatus.ASSIGNED]))
        ) or 0
        completed_cases = await self.db.scalar(
            select(func.count(Case.id)).where(Case.status == CaseStatus.COMPLETED)
        ) or 0
        
        return {
            "total_cases": total_cases,
            "active_cases": active_cases,
            "completed_cases": completed_cases,
            "success_rate": round((completed_cases / total_cases * 100) if total_cases > 0 else 0, 2),
        }
    
    async def get_recent_activities(self, user_id: Optional[UUID] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近活动"""
        
        query = select(UserActivityLog).order_by(UserActivityLog.created_at.desc()).limit(limit)
        
        if user_id:
            query = query.where(UserActivityLog.user_id == user_id)
        
        result = await self.db.execute(query)
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
    
    async def log_user_activity(
        self,
        user_id: UUID,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> UserActivityLog:
        """记录用户活动"""
        
        activity = UserActivityLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
        )
        
        self.db.add(activity)
        await self.db.commit()
        await self.db.refresh(activity)
        
        return activity
    
    async def update_daily_statistics(self, target_date: Optional[date] = None) -> SystemStatistics:
        """更新每日统计数据"""
        
        if target_date is None:
            target_date = date.today()
        
        # 检查是否已存在该日期的统计
        existing_stat = await self.db.scalar(
            select(SystemStatistics).where(SystemStatistics.stat_date == target_date)
        )
        
        # 计算统计数据
        total_cases = await self.db.scalar(select(func.count(Case.id))) or 0
        active_cases = await self.db.scalar(
            select(func.count(Case.id)).where(Case.status.in_([CaseStatus.IN_PROGRESS, CaseStatus.ASSIGNED]))
        ) or 0
        completed_cases = await self.db.scalar(
            select(func.count(Case.id)).where(Case.status == CaseStatus.COMPLETED)
        ) or 0
        
        total_users = await self.db.scalar(select(func.count(User.id))) or 0
        active_lawyers = await self.db.scalar(
            select(func.count(User.id)).where(User.role == "lawyer")
        ) or 0
        active_sales = await self.db.scalar(
            select(func.count(User.id)).where(User.role == "sales")
        ) or 0
        
        total_transactions = await self.db.scalar(select(func.count(Transaction.id))) or 0
        total_amount = await self.db.scalar(select(func.sum(Transaction.amount))) or 0
        total_commissions = await self.db.scalar(select(func.sum(CommissionSplit.amount))) or 0
        
        if existing_stat:
            # 更新现有统计
            existing_stat.total_cases = total_cases
            existing_stat.active_cases = active_cases
            existing_stat.completed_cases = completed_cases
            existing_stat.total_users = total_users
            existing_stat.active_lawyers = active_lawyers
            existing_stat.active_sales = active_sales
            existing_stat.total_transactions = total_transactions
            existing_stat.total_amount = total_amount
            existing_stat.total_commissions = total_commissions
            existing_stat.updated_at = datetime.now()
            
            await self.db.commit()
            return existing_stat
        else:
            # 创建新统计
            new_stat = SystemStatistics(
                stat_date=target_date,
                total_cases=total_cases,
                active_cases=active_cases,
                completed_cases=completed_cases,
                total_users=total_users,
                active_lawyers=active_lawyers,
                active_sales=active_sales,
                total_transactions=total_transactions,
                total_amount=total_amount,
                total_commissions=total_commissions,
            )
            
            self.db.add(new_stat)
            await self.db.commit()
            await self.db.refresh(new_stat)
            
            return new_stat 