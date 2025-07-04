"""
案件管理服务
处理案件的CRUD操作、分配逻辑、状态管理等
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

from app.models.case import Case, CaseStatus, Client, CaseLog
from app.models.user import User, LawyerQualification, QualificationStatus


class CaseService:
    """案件服务类"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_case(
        self,
        tenant_id: UUID,
        client_id: UUID,
        case_data: Dict[str, Any],
        creator_id: UUID
    ) -> Case:
        """创建新案件"""
        
        # 生成案件编号
        case_number = await self._generate_case_number(tenant_id)
        
        # 创建案件
        case = Case(
            tenant_id=tenant_id,
            client_id=client_id,
            case_number=case_number,
            debtor_info=case_data.get("debtor_info", {}),
            case_amount=case_data["case_amount"],
            sales_user_id=case_data["sales_user_id"],
            debt_creation_date=case_data["debt_creation_date"],
            description=case_data.get("description"),
            notes=case_data.get("notes"),
            tags=case_data.get("tags", [])
        )
        
        self.db.add(case)
        await self.db.flush()
        
        # 获取生成的ID后记录日志
        await self.db.refresh(case)
        await self._create_case_log(
            case.id,
            creator_id,
            "CREATE_CASE",
            {"message": "案件创建", "case_data": case_data}
        )
        
        await self.db.commit()
        return case
    
    async def get_case_by_id(self, case_id: UUID, tenant_id: UUID) -> Optional[Case]:
        """根据ID获取案件"""
        query = select(Case).where(
            and_(Case.id == case_id, Case.tenant_id == tenant_id)
        ).options(
            joinedload(Case.client),
            joinedload(Case.assigned_user),
            joinedload(Case.sales_user),
            joinedload(Case.logs)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_cases_list(
        self,
        tenant_id: UUID,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """获取案件列表（分页）"""
        
        query = select(Case).where(Case.tenant_id == tenant_id)
        
        # 应用过滤条件
        if filters:
            if filters.get("status"):
                query = query.where(Case.status == filters["status"])
            
            if filters.get("assigned_to"):
                query = query.where(Case.assigned_to_user_id == filters["assigned_to"])
            
            if filters.get("client_id"):
                query = query.where(Case.client_id == filters["client_id"])
            
            if filters.get("amount_min"):
                query = query.where(Case.case_amount >= filters["amount_min"])
            
            if filters.get("amount_max"):
                query = query.where(Case.case_amount <= filters["amount_max"])
            
            if filters.get("keyword"):
                keyword = f"%{filters['keyword']}%"
                query = query.where(
                    or_(
                        Case.case_number.ilike(keyword),
                        Case.description.ilike(keyword),
                        Case.debtor_info["name"].astext.ilike(keyword)
                    )
                )
        
        # 总数查询
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 分页查询
        offset = (page - 1) * page_size
        query = query.options(
            joinedload(Case.client),
            joinedload(Case.assigned_user),
            joinedload(Case.sales_user)
        ).offset(offset).limit(page_size).order_by(Case.created_at.desc())
        
        result = await self.db.execute(query)
        cases = result.scalars().all()
        
        return {
            "items": cases,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    async def assign_case(
        self,
        case_id: UUID,
        lawyer_id: UUID,
        assigner_id: UUID,
        tenant_id: UUID
    ) -> Case:
        """分配案件给律师"""
        
        # 检查案件是否存在
        case = await self.get_case_by_id(case_id, tenant_id)
        if not case:
            raise ValueError("案件不存在")
        
        # 检查律师资格
        lawyer_query = select(User).where(
            and_(User.id == lawyer_id, User.tenant_id == tenant_id)
        ).options(joinedload(User.lawyer_qualification))
        
        lawyer_result = await self.db.execute(lawyer_query)
        lawyer = lawyer_result.scalar_one_or_none()
        
        if not lawyer:
            raise ValueError("律师不存在")
        
        # 检查律师资质是否存在并且已审核通过
        if (lawyer.lawyer_qualification is None or 
            lawyer.lawyer_qualification.qualification_status != QualificationStatus.APPROVED):
            raise ValueError("律师资质未通过审核")
        
        # 记录原值
        old_values = {
            "assigned_to_user_id": str(case.assigned_to_user_id) if case.assigned_to_user_id else None,
            "status": case.status.value
        }
        
        # 更新案件
        update_stmt = update(Case).where(Case.id == case_id).values(
            assigned_to_user_id=lawyer_id,
            status=CaseStatus.ASSIGNED,
            updated_at=datetime.utcnow()
        )
        await self.db.execute(update_stmt)
        
        # 记录日志
        await self._create_case_log(
            case_id,
            assigner_id,
            "ASSIGN_CASE",
            {
                "message": f"案件分配给律师 {lawyer.username}",
                "lawyer_id": str(lawyer_id),
                "lawyer_name": lawyer.username
            },
            old_values,
            {
                "assigned_to_user_id": str(lawyer_id),
                "status": CaseStatus.ASSIGNED.value
            }
        )
        
        await self.db.commit()
        
        # 重新获取更新后的案件
        return await self.get_case_by_id(case_id, tenant_id) or case
    
    async def update_case_status(
        self,
        case_id: UUID,
        new_status: CaseStatus,
        user_id: UUID,
        tenant_id: UUID,
        notes: Optional[str] = None
    ) -> Case:
        """更新案件状态"""
        
        case = await self.get_case_by_id(case_id, tenant_id)
        if not case:
            raise ValueError("案件不存在")
        
        old_status = case.status
        
        # 更新状态
        update_values = {
            "status": new_status,
            "updated_at": datetime.utcnow()
        }
        
        if new_status == CaseStatus.COMPLETED:
            update_values["completed_at"] = datetime.utcnow()
        
        update_stmt = update(Case).where(Case.id == case_id).values(**update_values)
        await self.db.execute(update_stmt)
        
        # 记录日志
        await self._create_case_log(
            case_id,
            user_id,
            "UPDATE_STATUS",
            {
                "message": f"状态从 {old_status.value} 更改为 {new_status.value}",
                "notes": notes
            },
            {"status": old_status.value},
            {"status": new_status.value}
        )
        
        await self.db.commit()
        
        # 重新获取更新后的案件
        return await self.get_case_by_id(case_id, tenant_id) or case
    
    async def get_lawyer_workload(self, lawyer_id: UUID, tenant_id: UUID) -> Dict[str, Any]:
        """获取律师工作负荷"""
        
        # 当前进行中的案件
        active_cases_query = select(func.count()).where(
            and_(
                Case.assigned_to_user_id == lawyer_id,
                Case.tenant_id == tenant_id,
                Case.status.in_([CaseStatus.ASSIGNED, CaseStatus.IN_PROGRESS])
            )
        )
        active_cases_result = await self.db.execute(active_cases_query)
        active_cases = active_cases_result.scalar() or 0
        
        # 本月完成案件
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        completed_cases_query = select(func.count()).where(
            and_(
                Case.assigned_to_user_id == lawyer_id,
                Case.tenant_id == tenant_id,
                Case.status == CaseStatus.COMPLETED,
                Case.completed_at >= month_start
            )
        )
        completed_cases_result = await self.db.execute(completed_cases_query)
        completed_cases = completed_cases_result.scalar() or 0
        
        # 案件总金额
        amount_query = select(func.sum(Case.case_amount)).where(
            and_(
                Case.assigned_to_user_id == lawyer_id,
                Case.tenant_id == tenant_id,
                Case.status.in_([CaseStatus.ASSIGNED, CaseStatus.IN_PROGRESS])
            )
        )
        amount_result = await self.db.execute(amount_query)
        total_amount = amount_result.scalar() or 0
        
        return {
            "active_cases": active_cases,
            "completed_this_month": completed_cases,
            "total_amount": float(total_amount),
            "workload_level": self._calculate_workload_level(active_cases, float(total_amount))
        }
    
    async def get_case_statistics(self, tenant_id: UUID) -> Dict[str, Any]:
        """获取案件统计信息"""
        
        # 各状态案件数量
        status_query = select(
            Case.status,
            func.count().label('count'),
            func.sum(Case.case_amount).label('amount')
        ).where(Case.tenant_id == tenant_id).group_by(Case.status)
        
        status_result = await self.db.execute(status_query)
        status_stats = {}
        total_amount = 0
        
        for row in status_result:
            status_stats[row.status.value] = {
                "count": row.count,
                "amount": float(row.amount or 0)
            }
            total_amount += float(row.amount or 0)
        
        # 今日新增案件
        today = datetime.now().date()
        today_query = select(func.count()).where(
            and_(
                Case.tenant_id == tenant_id,
                func.date(Case.created_at) == today
            )
        )
        today_result = await self.db.execute(today_query)
        today_new = today_result.scalar() or 0
        
        return {
            "status_distribution": status_stats,
            "total_amount": total_amount,
            "today_new_cases": today_new
        }
    
    async def smart_assign_case(self, case_id: UUID, tenant_id: UUID, assigner_id: UUID) -> Case:
        """智能分配案件"""
        
        # 获取可用律师
        lawyers_query = select(User).where(
            and_(
                User.tenant_id == tenant_id,
                User.status == "active"
            )
        ).options(joinedload(User.lawyer_qualification))
        
        lawyers_result = await self.db.execute(lawyers_query)
        lawyers = lawyers_result.scalars().all()
        
        # 过滤有效律师资质
        qualified_lawyers = []
        for lawyer in lawyers:
            if (lawyer.lawyer_qualification is not None and 
                lawyer.lawyer_qualification.qualification_status == QualificationStatus.APPROVED):
                qualified_lawyers.append(lawyer)
        
        if not qualified_lawyers:
            raise ValueError("没有可用的合格律师")
        
        # 计算最佳分配（基于工作负荷）
        best_lawyer = None
        min_workload = float('inf')
        
        for lawyer in qualified_lawyers:
            workload = await self.get_lawyer_workload(lawyer.id, tenant_id)
            score = workload["active_cases"] * 10 + workload["total_amount"] / 10000
            
            if score < min_workload:
                min_workload = score
                best_lawyer = lawyer
        
        if not best_lawyer:
            raise ValueError("无法找到合适的律师")
        
        # 分配案件
        return await self.assign_case(case_id, best_lawyer.id, assigner_id, tenant_id)
    
    async def _generate_case_number(self, tenant_id: UUID) -> str:
        """生成案件编号"""
        today = datetime.now()
        prefix = f"CASE{today.strftime('%Y%m%d')}"
        
        # 查询今日案件数量
        count_query = select(func.count()).where(
            and_(
                Case.tenant_id == tenant_id,
                Case.case_number.like(f"{prefix}%")
            )
        )
        count_result = await self.db.execute(count_query)
        count = count_result.scalar() or 0
        
        return f"{prefix}{(count + 1):04d}"
    
    async def _create_case_log(
        self,
        case_id: UUID,
        user_id: UUID,
        action: str,
        details: Dict[str, Any],
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None
    ):
        """创建案件日志"""
        log = CaseLog(
            case_id=case_id,
            user_id=user_id,
            action=action,
            details=details,
            old_values=old_values,
            new_values=new_values
        )
        self.db.add(log)
    
    def _calculate_workload_level(self, active_cases: int, total_amount: float) -> str:
        """计算工作负荷等级"""
        if active_cases <= 5 and total_amount <= 100000:
            return "low"
        elif active_cases <= 10 and total_amount <= 500000:
            return "medium"
        elif active_cases <= 20 and total_amount <= 1000000:
            return "high"
        else:
            return "overload" 