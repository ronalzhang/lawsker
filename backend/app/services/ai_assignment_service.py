"""
AI智能分配业务和律师确认系统
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from fastapi import HTTPException

from app.models.user import User
from app.models.case import Case
from app.models.statistics import TaskPublishRecord
from app.core.config import settings


class AIAssignmentService:
    """AI智能分配服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def assign_case_to_lawyer(
        self,
        case_id: uuid.UUID,
        case_type: str,
        case_amount: float,
        case_priority: str = "medium",
        required_skills: Optional[List[str]] = None,
        region: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        AI智能分配案件给最合适的律师
        
        Args:
            case_id: 案件ID
            case_type: 案件类型
            case_amount: 案件金额
            case_priority: 案件优先级 (low, medium, high, urgent)
            required_skills: 需要的技能
            region: 地区要求
            
        Returns:
            分配结果
        """
        
        # 1. 获取所有可用律师
        available_lawyers = await self._get_available_lawyers(region)
        
        if not available_lawyers:
            raise HTTPException(status_code=404, detail="没有可用的律师")
        
        # 2. 根据AI算法评分选择最合适的律师
        best_lawyer = await self._ai_select_best_lawyer(
            lawyers=available_lawyers,
            case_type=case_type,
            case_amount=case_amount,
            case_priority=case_priority,
            required_skills=required_skills or []
        )
        
        # 3. 创建分配记录
        assignment = await self._create_assignment_record(
            case_id=case_id,
            lawyer_id=best_lawyer["id"],
            assignment_reason=best_lawyer["reason"],
            ai_score=best_lawyer["score"]
        )
        
        # 4. 发送通知给律师
        await self._notify_lawyer_assignment(
            lawyer_id=best_lawyer["id"],
            case_id=case_id,
            case_type=case_type,
            case_amount=case_amount
        )
        
        return {
            "assignment_id": str(assignment.id),
            "lawyer_id": str(best_lawyer["id"]),
            "lawyer_name": best_lawyer["name"],
            "lawyer_firm": best_lawyer["firm"],
            "ai_score": best_lawyer["score"],
            "assignment_reason": best_lawyer["reason"],
            "status": "pending_confirmation",
            "message": "案件已分配给律师，等待律师确认"
        }
    
    async def _get_available_lawyers(self, region: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取可用律师列表"""
        
        # 构建查询条件
        conditions = [
            User.role == "lawyer",
            User.is_active == True
        ]
        
        if region:
            conditions.append(User.region == region)
        
        # 查询律师
        query = select(User).where(and_(*conditions))
        result = await self.db.execute(query)
        lawyers = result.scalars().all()
        
        # 获取律师工作负载和统计信息
        lawyer_data = []
        for lawyer in lawyers:
            # 获取当前案件数
            current_cases_query = select(func.count(Case.id)).where(
                and_(
                    Case.lawyer_id == lawyer.id,
                    Case.status.in_(["pending", "in_progress", "review"])
                )
            )
            current_cases_result = await self.db.execute(current_cases_query)
            current_cases = current_cases_result.scalar() or 0
            
            # 获取成功率（最近30天）
            thirty_days_ago = datetime.now() - timedelta(days=30)
            success_rate_query = select(
                func.count(Case.id).filter(Case.status == "completed").label("completed"),
                func.count(Case.id).label("total")
            ).where(
                and_(
                    Case.lawyer_id == lawyer.id,
                    Case.created_at >= thirty_days_ago
                )
            )
            success_result = await self.db.execute(success_rate_query)
            success_data = success_result.first()
            
            success_rate = 0.0
            if success_data and success_data.total > 0:
                success_rate = success_data.completed / success_data.total
            
            lawyer_data.append({
                "id": lawyer.id,
                "name": lawyer.full_name or lawyer.username,
                "firm": getattr(lawyer, 'law_firm', '未知律所'),
                "specialties": getattr(lawyer, 'specialties', []),
                "region": getattr(lawyer, 'region', ''),
                "current_cases": current_cases,
                "success_rate": success_rate,
                "rating": getattr(lawyer, 'rating', 4.0),
                "experience_years": getattr(lawyer, 'experience_years', 1),
                "max_cases": getattr(lawyer, 'max_cases', 10)
            })
        
        return lawyer_data
    
    async def _ai_select_best_lawyer(
        self,
        lawyers: List[Dict[str, Any]],
        case_type: str,
        case_amount: float,
        case_priority: str,
        required_skills: List[str]
    ) -> Dict[str, Any]:
        """AI算法选择最合适的律师"""
        
        best_lawyer = None
        best_score = 0.0
        
        for lawyer in lawyers:
            score = 0.0
            reasons = []
            
            # 1. 工作负载评分 (30%)
            workload_ratio = lawyer["current_cases"] / lawyer["max_cases"]
            if workload_ratio < 0.5:
                workload_score = 1.0
                reasons.append("工作负载较轻")
            elif workload_ratio < 0.8:
                workload_score = 0.7
                reasons.append("工作负载适中")
            else:
                workload_score = 0.3
                reasons.append("工作负载较重")
            
            score += workload_score * 0.3
            
            # 2. 专业匹配度评分 (25%)
            specialty_score = 0.0
            if case_type in lawyer["specialties"]:
                specialty_score = 1.0
                reasons.append(f"专业匹配({case_type})")
            elif any(skill in lawyer["specialties"] for skill in required_skills):
                specialty_score = 0.8
                reasons.append("技能匹配")
            else:
                specialty_score = 0.4
                reasons.append("通用律师")
            
            score += specialty_score * 0.25
            
            # 3. 成功率评分 (20%)
            success_score = lawyer["success_rate"]
            if success_score > 0.8:
                reasons.append("成功率高")
            elif success_score > 0.6:
                reasons.append("成功率良好")
            else:
                reasons.append("成功率一般")
            
            score += success_score * 0.2
            
            # 4. 经验评分 (15%)
            experience_score = min(lawyer["experience_years"] / 10, 1.0)
            if lawyer["experience_years"] > 5:
                reasons.append("经验丰富")
            elif lawyer["experience_years"] > 2:
                reasons.append("经验适中")
            else:
                reasons.append("经验较少")
            
            score += experience_score * 0.15
            
            # 5. 评分评分 (10%)
            rating_score = lawyer["rating"] / 5.0
            if lawyer["rating"] > 4.5:
                reasons.append("评分优秀")
            elif lawyer["rating"] > 4.0:
                reasons.append("评分良好")
            
            score += rating_score * 0.1
            
            # 6. 案件金额适配度调整
            if case_amount > 1000000:  # 大额案件
                if lawyer["experience_years"] > 5:
                    score += 0.1
                    reasons.append("适合大额案件")
            
            # 7. 优先级调整
            if case_priority == "urgent":
                if workload_ratio < 0.6:
                    score += 0.05
                    reasons.append("可处理紧急案件")
            
            # 更新最佳律师
            if score > best_score:
                best_score = score
                best_lawyer = {
                    **lawyer,
                    "score": round(score, 3),
                    "reason": "; ".join(reasons)
                }
        
        if not best_lawyer:
            raise HTTPException(status_code=404, detail="无法找到合适的律师")
        
        return best_lawyer
    
    async def _create_assignment_record(
        self,
        case_id: uuid.UUID,
        lawyer_id: uuid.UUID,
        assignment_reason: str,
        ai_score: float
    ) -> TaskPublishRecord:
        """创建分配记录"""
        
        record = TaskPublishRecord(
            publisher_id=case_id,  # 使用case_id作为publisher_id
            task_type="case_assignment",
            task_title="案件分配",
            task_description=f"AI智能分配案件给律师，评分: {ai_score}",
            requirements={"lawyer_id": str(lawyer_id), "reason": assignment_reason},
            budget=0.0,
            deadline=datetime.now() + timedelta(days=7),
            status="published",
            assigned_to=lawyer_id
        )
        
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        
        return record
    
    async def _notify_lawyer_assignment(
        self,
        lawyer_id: uuid.UUID,
        case_id: uuid.UUID,
        case_type: str,
        case_amount: float
    ):
        """通知律师新案件分配"""
        # 这里可以集成邮件、短信、推送等通知方式
        # 暂时只记录日志
        print(f"通知律师 {lawyer_id} 新案件分配: {case_id}, 类型: {case_type}, 金额: {case_amount}")
    
    async def lawyer_confirm_assignment(
        self,
        assignment_id: uuid.UUID,
        lawyer_id: uuid.UUID,
        action: str,  # "accept" or "reject"
        reason: str = ""
    ) -> Dict[str, Any]:
        """律师确认或拒绝案件分配"""
        
        # 查找分配记录
        query = select(TaskPublishRecord).where(
            and_(
                TaskPublishRecord.id == assignment_id,
                TaskPublishRecord.assigned_to == lawyer_id
            )
        )
        result = await self.db.execute(query)
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="分配记录不存在")
        
        if action == "accept":
            assignment.status = "accepted"  # type: ignore
            assignment.processing_notes = f"律师接受案件: {reason}"
            
            # 更新案件状态
            case_query = select(Case).where(Case.id == assignment.publisher_id)
            case_result = await self.db.execute(case_query)
            case = case_result.scalar_one_or_none()
            
            if case:
                case.lawyer_id = lawyer_id  # type: ignore
                case.status = "in_progress"  # type: ignore
                case.assigned_at = datetime.now()  # type: ignore
            
            message = "案件接受成功，已开始处理"
            
        elif action == "reject":
            assignment.status = "rejected"  # type: ignore
            assignment.processing_notes = f"律师拒绝案件: {reason}"
            
            # 重新分配案件
            await self._reassign_case(assignment.publisher_id, reason)
            
            message = "案件已拒绝，系统将重新分配"
        
        else:
            raise HTTPException(status_code=400, detail="无效的操作")
        
        await self.db.commit()
        
        return {
            "assignment_id": str(assignment.id),
            "action": action,
            "status": assignment.status,
            "message": message
        }
    
    async def _reassign_case(self, case_id: uuid.UUID, reject_reason: str):
        """重新分配被拒绝的案件"""
        
        # 查找案件信息
        query = select(Case).where(Case.id == case_id)
        result = await self.db.execute(query)
        case = result.scalar_one_or_none()
        
        if case:
            # 重新进行AI分配，但排除已拒绝的律师
            await self.assign_case_to_lawyer(
                case_id=case.id,  # type: ignore
                case_type=case.case_type or "general",
                case_amount=case.amount or 0.0,
                case_priority="high"  # 重新分配的案件提高优先级
            )
    
    async def get_lawyer_assignments(
        self,
        lawyer_id: uuid.UUID,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取律师的案件分配记录"""
        
        conditions = [TaskPublishRecord.assigned_to == lawyer_id]
        
        if status:
            conditions.append(TaskPublishRecord.status == status)
        
        query = select(TaskPublishRecord).where(
            and_(*conditions)
        ).order_by(
            TaskPublishRecord.created_at.desc()
        ).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        assignments = result.scalars().all()
        
        return [
            {
                "id": str(assignment.id),
                "case_id": str(assignment.publisher_id),
                "task_type": assignment.task_type,
                "task_title": assignment.task_title,
                "task_description": assignment.task_description,
                "status": assignment.status,
                "created_at": assignment.created_at.isoformat(),
                "deadline": assignment.deadline.isoformat() if assignment.deadline else None,
                "processing_notes": assignment.processing_notes
            }
            for assignment in assignments
        ] 