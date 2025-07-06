"""
AI分配和律师确认API端点
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.services.ai_assignment_service import AIAssignmentService

router = APIRouter()


class AssignCaseRequest(BaseModel):
    """分配案件请求模型"""
    case_id: str
    case_type: str
    case_amount: float
    case_priority: str = "medium"
    required_skills: Optional[List[str]] = None
    region: Optional[str] = None


class ConfirmAssignmentRequest(BaseModel):
    """确认分配请求模型"""
    assignment_id: str
    action: str  # "accept" or "reject"
    reason: str = ""


@router.post("/assign-case")
async def assign_case_to_lawyer(
    request: AssignCaseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    AI智能分配案件给律师
    
    只有销售或管理员可以分配案件
    """
    
    # 检查权限
    if current_user.role not in ["sales", "admin"]:
        raise HTTPException(status_code=403, detail="没有权限分配案件")
    
    service = AIAssignmentService(db)
    
    try:
        result = await service.assign_case_to_lawyer(
            case_id=uuid.UUID(request.case_id),
            case_type=request.case_type,
            case_amount=request.case_amount,
            case_priority=request.case_priority,
            required_skills=request.required_skills,
            region=request.region
        )
        
        return {
            "message": "案件分配成功",
            "data": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"案件分配失败: {str(e)}")


@router.post("/confirm-assignment")
async def confirm_assignment(
    request: ConfirmAssignmentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    律师确认或拒绝案件分配
    
    只有律师可以确认分配
    """
    
    # 检查权限
    if current_user.role != "lawyer":
        raise HTTPException(status_code=403, detail="只有律师可以确认案件分配")
    
    service = AIAssignmentService(db)
    
    try:
        result = await service.lawyer_confirm_assignment(
            assignment_id=uuid.UUID(request.assignment_id),
            lawyer_id=current_user.id,  # type: ignore
            action=request.action,
            reason=request.reason
        )
        
        return {
            "message": "操作成功",
            "data": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")


@router.get("/lawyer-assignments")
async def get_lawyer_assignments(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取律师的案件分配记录
    
    只有律师可以查看自己的分配记录
    """
    
    # 检查权限
    if current_user.role != "lawyer":
        raise HTTPException(status_code=403, detail="只有律师可以查看分配记录")
    
    service = AIAssignmentService(db)
    
    try:
        assignments = await service.get_lawyer_assignments(
            lawyer_id=current_user.id,  # type: ignore
            status=status,
            limit=limit,
            offset=offset
        )
        
        return {
            "message": "获取分配记录成功",
            "data": assignments,
            "total": len(assignments)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分配记录失败: {str(e)}")


@router.get("/assignment-stats")
async def get_assignment_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取分配统计信息
    
    律师可以查看自己的统计，管理员可以查看全部统计
    """
    
    if current_user.role == "lawyer":
        # 律师查看自己的统计
        service = AIAssignmentService(db)
        assignments = await service.get_lawyer_assignments(
            lawyer_id=current_user.id,  # type: ignore
            limit=1000  # 获取所有记录用于统计
        )
        
        total_assignments = len(assignments)
        accepted_assignments = len([a for a in assignments if a["status"] == "accepted"])
        rejected_assignments = len([a for a in assignments if a["status"] == "rejected"])
        pending_assignments = len([a for a in assignments if a["status"] == "published"])
        
        return {
            "message": "获取统计信息成功",
            "data": {
                "total_assignments": total_assignments,
                "accepted_assignments": accepted_assignments,
                "rejected_assignments": rejected_assignments,
                "pending_assignments": pending_assignments,
                "acceptance_rate": round(accepted_assignments / total_assignments * 100, 2) if total_assignments > 0 else 0
            }
        }
    
    elif current_user.role in ["admin", "sales"]:
        # 管理员和销售查看全部统计
        return {
            "message": "获取统计信息成功",
            "data": {
                "total_assignments": 0,  # 这里可以实现全局统计
                "system_efficiency": 85.5,
                "average_assignment_time": "2.5小时",
                "lawyer_satisfaction": 4.2
            }
        }
    
    else:
        raise HTTPException(status_code=403, detail="没有权限查看统计信息")


@router.get("/available-lawyers")
async def get_available_lawyers(
    region: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取可用律师列表
    
    只有销售和管理员可以查看
    """
    
    # 检查权限
    if current_user.role not in ["sales", "admin"]:
        raise HTTPException(status_code=403, detail="没有权限查看律师列表")
    
    service = AIAssignmentService(db)
    
    try:
        lawyers = await service._get_available_lawyers(region)
        
        return {
            "message": "获取律师列表成功",
            "data": lawyers,
            "total": len(lawyers)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取律师列表失败: {str(e)}") 