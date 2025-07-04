"""
律师审核工作流服务
管理AI文档生成、律师审核、修改和发送的完整流程
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
from sqlalchemy.orm import selectinload

from app.models.lawyer_review import DocumentReviewTask, DocumentReviewLog, LawyerWorkload, ReviewStatus
from app.models.case import Case
from app.models.lawyer_letter import LawyerLetterOrder
from app.models.user import User
from app.services.ai_service import AIDocumentService, DocumentType
from app.services.case_service import CaseService


class LawyerAssignmentStrategy:
    """律师分配策略"""
    
    @staticmethod
    async def calculate_workload_score(lawyer: User, workload: LawyerWorkload) -> int:
        """
        计算律师工作负荷评分
        评分越低表示工作负荷越轻，越适合分配新任务
        """
        if not workload.is_available:
            return 9999  # 不可用律师得分最高，不会被分配
        
        # 基础评分：当前任务数占最大并发任务数的比例
        base_score = (workload.pending_reviews / workload.max_concurrent_tasks) * 100
        
        # 质量调整：通过率和满意度影响
        quality_bonus = (workload.approval_rate + workload.client_satisfaction) / 20
        
        # 专业匹配度（暂时使用固定权重）
        specialty_bonus = 0
        
        # 最终评分
        final_score = base_score - quality_bonus - specialty_bonus
        
        return max(0, int(final_score))


class LawyerReviewService:
    """律师审核服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIDocumentService()
        self.case_service = CaseService(db)
        self.assignment_strategy = LawyerAssignmentStrategy()
    
    async def create_collection_letter_task(
        self,
        case_id: UUID,
        creator_id: UUID,
        tone_style: str = "正式通知",
        grace_period: int = 15,
        priority: int = 2
    ) -> DocumentReviewTask:
        """
        为催收案件创建律师函审核任务
        
        Args:
            case_id: 案件ID
            creator_id: 创建者ID
            tone_style: 语气风格
            grace_period: 宽限期天数
            priority: 优先级
            
        Returns:
            创建的审核任务
        """
        
        # 获取案件信息
        case = await self.case_service.get_case_by_id(case_id)
        if not case:
            raise ValueError(f"案件 {case_id} 不存在")
        
        # 获取委托方信息
        client_info = {
            "name": case.client.name if case.client else "委托方",
            "contact_person": case.client.contact_person if case.client else "",
            "contact_phone": case.client.contact_phone if case.client else ""
        }
        
        # 使用AI生成律师函
        ai_result = await self.ai_service.generate_collection_letter(
            case=case,
            client_info=client_info,
            tone_style=tone_style,
            grace_period=grace_period
        )
        
        # 分配律师
        assigned_lawyer = await self._assign_best_lawyer(DocumentType.COLLECTION_LETTER)
        
        # 创建审核任务
        task = DocumentReviewTask(
            task_number=await self._generate_task_number(),
            case_id=case_id,
            creator_id=creator_id,
            lawyer_id=assigned_lawyer.id,
            document_type=ai_result["metadata"]["document_type"],
            original_content=ai_result["content"],
            current_content=ai_result["content"],
            priority=priority,
            deadline=datetime.utcnow() + timedelta(hours=24),  # 24小时内完成
            ai_metadata=ai_result["metadata"],
            generation_prompt=f"催收律师函生成 - 语气: {tone_style}, 宽限期: {grace_period}天",
            ai_providers=ai_result["metadata"]["ai_providers"]
        )
        
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        
        # 记录日志
        await self._create_review_log(
            task_id=task.id,
            reviewer_id=creator_id,
            action="CREATE_TASK",
            new_status=ReviewStatus.PENDING,
            comment=f"为案件 {case.case_number} 创建催收律师函审核任务"
        )
        
        # 更新律师工作负荷
        await self._update_lawyer_workload(assigned_lawyer.id, pending_reviews_delta=1)
        
        return task
    
    async def create_independent_letter_task(
        self,
        order_id: UUID,
        creator_id: UUID,
        order_data: Dict[str, Any],
        priority: int = 2
    ) -> DocumentReviewTask:
        """
        为独立律师函服务创建审核任务
        
        Args:
            order_id: 订单ID
            creator_id: 创建者ID
            order_data: 订单数据
            priority: 优先级
            
        Returns:
            创建的审核任务
        """
        
        # 使用AI生成律师函
        ai_result = await self.ai_service.generate_independent_letter(order_data)
        
        # 根据紧急程度和文档类型分配律师
        document_type = ai_result["metadata"]["document_type"]
        assigned_lawyer = await self._assign_best_lawyer(document_type)
        
        # 根据紧急程度设置截止时间
        urgency = order_data.get("urgency", "普通")
        deadline_hours = {
            "紧急": 1,
            "加急": 24,
            "普通": 48
        }.get(urgency, 48)
        
        # 创建审核任务
        task = DocumentReviewTask(
            task_number=await self._generate_task_number(),
            order_id=order_id,
            creator_id=creator_id,
            lawyer_id=assigned_lawyer.id,
            document_type=document_type,
            original_content=ai_result["content"],
            current_content=ai_result["content"],
            priority=priority,
            deadline=datetime.utcnow() + timedelta(hours=deadline_hours),
            ai_metadata=ai_result["metadata"],
            generation_prompt=f"独立律师函生成 - 类型: {order_data.get('letter_type')}, 紧急程度: {urgency}",
            ai_providers=ai_result["metadata"]["ai_providers"]
        )
        
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        
        # 记录日志
        await self._create_review_log(
            task_id=task.id,
            reviewer_id=creator_id,
            action="CREATE_TASK",
            new_status=ReviewStatus.PENDING,
            comment=f"为订单 {order_data.get('order_number')} 创建独立律师函审核任务"
        )
        
        # 更新律师工作负荷
        await self._update_lawyer_workload(assigned_lawyer.id, pending_reviews_delta=1)
        
        return task
    
    async def lawyer_accept_task(
        self,
        task_id: UUID,
        lawyer_id: UUID,
        notes: Optional[str] = None
    ) -> DocumentReviewTask:
        """
        律师接受审核任务
        
        Args:
            task_id: 任务ID
            lawyer_id: 律师ID
            notes: 备注
            
        Returns:
            更新后的任务
        """
        
        task = await self._get_task_by_id(task_id)
        if not task:
            raise ValueError(f"任务 {task_id} 不存在")
        
        if task.lawyer_id != lawyer_id:
            raise ValueError("只能接受分配给自己的任务")
        
        if task.status != ReviewStatus.PENDING:
            raise ValueError(f"任务状态 {task.status} 不允许接受")
        
        # 更新任务状态
        old_status = task.status
        task.status = ReviewStatus.IN_REVIEW
        task.review_notes = notes
        task.reviewed_at = datetime.utcnow()
        
        await self.db.commit()
        
        # 记录日志
        await self._create_review_log(
            task_id=task_id,
            reviewer_id=lawyer_id,
            action="ACCEPT_TASK",
            old_status=old_status,
            new_status=task.status,
            comment=notes or "律师接受任务开始审核"
        )
        
        return task
    
    async def lawyer_approve_document(
        self,
        task_id: UUID,
        lawyer_id: UUID,
        approval_notes: Optional[str] = None,
        final_content: Optional[str] = None
    ) -> DocumentReviewTask:
        """
        律师通过文档审核
        
        Args:
            task_id: 任务ID
            lawyer_id: 律师ID
            approval_notes: 通过备注
            final_content: 最终确认内容（如果有修改）
            
        Returns:
            更新后的任务
        """
        
        task = await self._get_task_by_id(task_id)
        if not task:
            raise ValueError(f"任务 {task_id} 不存在")
        
        if task.lawyer_id != lawyer_id:
            raise ValueError("只能审核分配给自己的任务")
        
        if task.status not in [ReviewStatus.IN_REVIEW, ReviewStatus.MODIFIED]:
            raise ValueError(f"任务状态 {task.status} 不允许审核通过")
        
        # 更新任务状态
        old_status = task.status
        task.status = ReviewStatus.APPROVED
        task.approval_notes = approval_notes
        task.final_content = final_content or task.current_content
        task.approved_at = datetime.utcnow()
        
        await self.db.commit()
        
        # 记录日志
        await self._create_review_log(
            task_id=task_id,
            reviewer_id=lawyer_id,
            action="APPROVE_DOCUMENT",
            old_status=old_status,
            new_status=task.status,
            comment=approval_notes or "律师审核通过",
            content_changes={"final_content": task.final_content} if final_content else None
        )
        
        # 更新律师工作负荷
        await self._update_lawyer_workload(lawyer_id, pending_reviews_delta=-1)
        
        return task
    
    async def lawyer_request_modification(
        self,
        task_id: UUID,
        lawyer_id: UUID,
        modification_requests: str,
        current_content: Optional[str] = None
    ) -> DocumentReviewTask:
        """
        律师要求修改文档
        
        Args:
            task_id: 任务ID
            lawyer_id: 律师ID
            modification_requests: 修改要求
            current_content: 当前修改的内容
            
        Returns:
            更新后的任务
        """
        
        task = await self._get_task_by_id(task_id)
        if not task:
            raise ValueError(f"任务 {task_id} 不存在")
        
        if task.lawyer_id != lawyer_id:
            raise ValueError("只能修改分配给自己的任务")
        
        if task.status != ReviewStatus.IN_REVIEW:
            raise ValueError(f"任务状态 {task.status} 不允许要求修改")
        
        # 使用AI重新生成内容
        document_type = DocumentType(task.document_type)
        modified_content = await self.ai_service.regenerate_document(
            original_content=current_content or task.current_content,
            modification_requests=modification_requests,
            document_type=document_type
        )
        
        # 更新任务状态
        old_status = task.status
        task.status = ReviewStatus.MODIFICATION_REQUESTED
        task.modification_requests = modification_requests
        task.current_content = modified_content
        
        await self.db.commit()
        
        # 记录日志
        await self._create_review_log(
            task_id=task_id,
            reviewer_id=lawyer_id,
            action="REQUEST_MODIFICATION",
            old_status=old_status,
            new_status=task.status,
            comment=f"要求修改: {modification_requests}",
            content_changes={
                "old_content": current_content or task.original_content,
                "new_content": modified_content
            }
        )
        
        return task
    
    async def lawyer_authorize_sending(
        self,
        task_id: UUID,
        lawyer_id: UUID,
        authorization_notes: Optional[str] = None
    ) -> DocumentReviewTask:
        """
        律师授权发送文档
        
        Args:
            task_id: 任务ID
            lawyer_id: 律师ID
            authorization_notes: 授权备注
            
        Returns:
            更新后的任务
        """
        
        task = await self._get_task_by_id(task_id)
        if not task:
            raise ValueError(f"任务 {task_id} 不存在")
        
        if task.lawyer_id != lawyer_id:
            raise ValueError("只能授权自己审核的任务")
        
        if task.status != ReviewStatus.APPROVED:
            raise ValueError(f"任务状态 {task.status} 不允许授权发送")
        
        # 更新任务状态
        old_status = task.status
        task.status = ReviewStatus.AUTHORIZED
        task.approval_notes = (task.approval_notes or "") + f"\n授权发送: {authorization_notes or ''}"
        
        await self.db.commit()
        
        # 记录日志
        await self._create_review_log(
            task_id=task_id,
            reviewer_id=lawyer_id,
            action="AUTHORIZE_SENDING",
            old_status=old_status,
            new_status=task.status,
            comment=authorization_notes or "律师授权发送"
        )
        
        return task
    
    async def get_lawyer_pending_tasks(
        self,
        lawyer_id: UUID,
        limit: int = 20,
        offset: int = 0
    ) -> List[DocumentReviewTask]:
        """获取律师待处理任务列表"""
        
        query = select(DocumentReviewTask).where(
            and_(
                DocumentReviewTask.lawyer_id == lawyer_id,
                DocumentReviewTask.status.in_([
                    ReviewStatus.PENDING,
                    ReviewStatus.IN_REVIEW,
                    ReviewStatus.MODIFICATION_REQUESTED
                ])
            )
        ).order_by(
            DocumentReviewTask.priority.desc(),
            DocumentReviewTask.deadline.asc()
        ).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_task_statistics(self, lawyer_id: Optional[UUID] = None) -> Dict[str, Any]:
        """获取任务统计信息"""
        
        base_query = select(DocumentReviewTask)
        if lawyer_id:
            base_query = base_query.where(DocumentReviewTask.lawyer_id == lawyer_id)
        
        # 按状态统计
        status_counts = {}
        for status in ReviewStatus:
            count_query = base_query.where(DocumentReviewTask.status == status)
            result = await self.db.execute(select(func.count()).select_from(count_query.subquery()))
            status_counts[status.value] = result.scalar() or 0
        
        # 今日任务统计
        today = datetime.utcnow().date()
        today_query = base_query.where(
            func.date(DocumentReviewTask.created_at) == today
        )
        today_result = await self.db.execute(select(func.count()).select_from(today_query.subquery()))
        today_count = today_result.scalar() or 0
        
        # 逾期任务统计
        overdue_query = base_query.where(
            and_(
                DocumentReviewTask.deadline < datetime.utcnow(),
                DocumentReviewTask.status.in_([
                    ReviewStatus.PENDING,
                    ReviewStatus.IN_REVIEW,
                    ReviewStatus.MODIFICATION_REQUESTED
                ])
            )
        )
        overdue_result = await self.db.execute(select(func.count()).select_from(overdue_query.subquery()))
        overdue_count = overdue_result.scalar() or 0
        
        return {
            "status_counts": status_counts,
            "today_created": today_count,
            "overdue": overdue_count,
            "total": sum(status_counts.values())
        }
    
    async def _assign_best_lawyer(self, document_type: DocumentType) -> User:
        """分配最合适的律师"""
        
        # 查询所有可用律师及其工作负荷
        query = select(User).join(LawyerWorkload).where(
            and_(
                LawyerWorkload.is_available == True,
                LawyerWorkload.pending_reviews < LawyerWorkload.max_concurrent_tasks
            )
        ).options(selectinload(User.workload))
        
        result = await self.db.execute(query)
        available_lawyers = result.scalars().all()
        
        if not available_lawyers:
            raise ValueError("没有可用的律师")
        
        # 计算每个律师的工作负荷评分
        lawyer_scores = []
        for lawyer in available_lawyers:
            score = await self.assignment_strategy.calculate_workload_score(
                lawyer, lawyer.workload
            )
            lawyer_scores.append((lawyer, score))
        
        # 选择评分最低（工作负荷最轻）的律师
        lawyer_scores.sort(key=lambda x: x[1])
        best_lawyer = lawyer_scores[0][0]
        
        return best_lawyer
    
    async def _get_task_by_id(self, task_id: UUID) -> Optional[DocumentReviewTask]:
        """根据ID获取任务"""
        query = select(DocumentReviewTask).where(DocumentReviewTask.id == task_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _generate_task_number(self) -> str:
        """生成任务编号"""
        now = datetime.utcnow()
        prefix = f"RT{now.strftime('%Y%m%d')}"
        
        # 查询当日任务数量
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        query = select(func.count(DocumentReviewTask.id)).where(
            and_(
                DocumentReviewTask.created_at >= today_start,
                DocumentReviewTask.created_at < today_end
            )
        )
        result = await self.db.execute(query)
        count = result.scalar() or 0
        
        return f"{prefix}{count + 1:04d}"
    
    async def _create_review_log(
        self,
        task_id: UUID,
        reviewer_id: UUID,
        action: str,
        new_status: ReviewStatus,
        old_status: Optional[ReviewStatus] = None,
        comment: Optional[str] = None,
        content_changes: Optional[Dict[str, Any]] = None
    ):
        """创建审核日志"""
        
        log = DocumentReviewLog(
            review_task_id=task_id,
            reviewer_id=reviewer_id,
            action=action,
            old_status=old_status,
            new_status=new_status,
            comment=comment,
            content_changes=content_changes
        )
        
        self.db.add(log)
        await self.db.commit()
    
    async def _update_lawyer_workload(
        self,
        lawyer_id: UUID,
        pending_reviews_delta: int = 0,
        active_cases_delta: int = 0
    ):
        """更新律师工作负荷"""
        
        query = select(LawyerWorkload).where(LawyerWorkload.lawyer_id == lawyer_id)
        result = await self.db.execute(query)
        workload = result.scalar_one_or_none()
        
        if workload:
            workload.pending_reviews = max(0, workload.pending_reviews + pending_reviews_delta)
            workload.active_cases = max(0, workload.active_cases + active_cases_delta)
            workload.last_assignment_at = datetime.utcnow()
            
            # 重新计算工作负荷评分
            total_score = (workload.pending_reviews * 2) + workload.active_cases
            workload.current_workload_score = total_score
            
            await self.db.commit()
    
    async def close(self):
        """关闭AI服务连接"""
        await self.ai_service.close() 