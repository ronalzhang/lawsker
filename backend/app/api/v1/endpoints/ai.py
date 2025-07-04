"""
AI文书生成和律师审核工作流API端点
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.services.lawyer_review_service import LawyerReviewService
from app.services.ai_service import AIDocumentService, DocumentType
from app.models.lawyer_review import DocumentReviewTask, ReviewStatus
from app.models.user import User
from app.core.deps import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()


# Pydantic模型定义
class CreateCollectionLetterRequest(BaseModel):
    """创建催收律师函请求"""
    case_id: UUID = Field(..., description="案件ID")
    tone_style: str = Field(default="正式通知", description="语气风格")
    grace_period: int = Field(default=15, description="宽限期天数")
    priority: int = Field(default=2, description="优先级1-5")


class CreateIndependentLetterRequest(BaseModel):
    """创建独立律师函请求"""
    # 客户信息
    client_name: str = Field(..., description="客户姓名")
    client_phone: str = Field(..., description="客户电话")
    client_email: Optional[str] = Field(None, description="客户邮箱")
    client_company: Optional[str] = Field(None, description="客户公司")
    
    # 目标方信息
    target_name: str = Field(..., description="对方姓名/公司名")
    target_phone: Optional[str] = Field(None, description="对方电话")
    target_email: Optional[str] = Field(None, description="对方邮箱")
    target_address: Optional[str] = Field(None, description="对方地址")
    
    # 律师函信息
    letter_type: str = Field(..., description="律师函类型")
    case_background: str = Field(..., description="案件背景")
    legal_basis: Optional[str] = Field(None, description="法律依据")
    demands: List[str] = Field(default=[], description="具体要求")
    content_brief: str = Field(..., description="内容简述")
    urgency: str = Field(default="普通", description="紧急程度")
    priority: int = Field(default=2, description="优先级1-5")


class ReviewTaskResponse(BaseModel):
    """审核任务响应"""
    id: UUID
    task_number: str
    case_id: Optional[UUID]
    order_id: Optional[UUID]
    lawyer_id: UUID
    creator_id: UUID
    document_type: str
    original_content: str
    current_content: str
    final_content: Optional[str]
    status: str
    priority: int
    deadline: Optional[datetime]
    ai_metadata: Optional[Dict[str, Any]]
    review_notes: Optional[str]
    modification_requests: Optional[str]
    approval_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    reviewed_at: Optional[datetime]
    approved_at: Optional[datetime]

    class Config:
        from_attributes = True


class AcceptTaskRequest(BaseModel):
    """接受任务请求"""
    notes: Optional[str] = Field(None, description="备注")


class ApproveDocumentRequest(BaseModel):
    """通过文档审核请求"""
    approval_notes: Optional[str] = Field(None, description="通过备注")
    final_content: Optional[str] = Field(None, description="最终确认内容")


class RequestModificationRequest(BaseModel):
    """要求修改请求"""
    modification_requests: str = Field(..., description="修改要求")
    current_content: Optional[str] = Field(None, description="当前内容")


class AuthorizeSendingRequest(BaseModel):
    """授权发送请求"""
    authorization_notes: Optional[str] = Field(None, description="授权备注")


class TaskStatisticsResponse(BaseModel):
    """任务统计响应"""
    status_counts: Dict[str, int]
    today_created: int
    overdue: int
    total: int


# API端点

@router.post("/documents/collection-letter", response_model=ReviewTaskResponse)
async def create_collection_letter(
    request: CreateCollectionLetterRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    为催收案件创建律师函审核任务
    """
    try:
        service = LawyerReviewService(db)
        task = await service.create_collection_letter_task(
            case_id=request.case_id,
            creator_id=current_user.id,
            tone_style=request.tone_style,
            grace_period=request.grace_period,
            priority=request.priority
        )
        await service.close()
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.post("/documents/independent-letter", response_model=ReviewTaskResponse)
async def create_independent_letter(
    request: CreateIndependentLetterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    为独立律师函服务创建审核任务
    """
    try:
        # 准备订单数据
        order_data = {
            "client_name": request.client_name,
            "client_phone": request.client_phone,
            "client_email": request.client_email,
            "client_company": request.client_company,
            "target_name": request.target_name,
            "target_phone": request.target_phone,
            "target_email": request.target_email,
            "target_address": request.target_address,
            "letter_type": request.letter_type,
            "case_background": request.case_background,
            "legal_basis": request.legal_basis,
            "demands": request.demands,
            "content_brief": request.content_brief,
            "urgency": request.urgency,
            "order_number": f"IND{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
        
        service = LawyerReviewService(db)
        task = await service.create_independent_letter_task(
            order_id=None,  # 暂时不关联订单
            creator_id=current_user.id,
            order_data=order_data,
            priority=request.priority
        )
        await service.close()
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.post("/tasks/{task_id}/accept", response_model=ReviewTaskResponse)
async def accept_task(
    task_id: UUID,
    request: AcceptTaskRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    律师接受审核任务
    """
    try:
        service = LawyerReviewService(db)
        task = await service.lawyer_accept_task(
            task_id=task_id,
            lawyer_id=current_user.id,
            notes=request.notes
        )
        await service.close()
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"接受任务失败: {str(e)}")


@router.post("/tasks/{task_id}/approve", response_model=ReviewTaskResponse)
async def approve_document(
    task_id: UUID,
    request: ApproveDocumentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    律师通过文档审核
    """
    try:
        service = LawyerReviewService(db)
        task = await service.lawyer_approve_document(
            task_id=task_id,
            lawyer_id=current_user.id,
            approval_notes=request.approval_notes,
            final_content=request.final_content
        )
        await service.close()
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"审核通过失败: {str(e)}")


@router.post("/tasks/{task_id}/modify", response_model=ReviewTaskResponse)
async def request_modification(
    task_id: UUID,
    request: RequestModificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    律师要求修改文档
    """
    try:
        service = LawyerReviewService(db)
        task = await service.lawyer_request_modification(
            task_id=task_id,
            lawyer_id=current_user.id,
            modification_requests=request.modification_requests,
            current_content=request.current_content
        )
        await service.close()
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"要求修改失败: {str(e)}")


@router.post("/tasks/{task_id}/authorize", response_model=ReviewTaskResponse)
async def authorize_sending(
    task_id: UUID,
    request: AuthorizeSendingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    律师授权发送文档
    """
    try:
        service = LawyerReviewService(db)
        task = await service.lawyer_authorize_sending(
            task_id=task_id,
            lawyer_id=current_user.id,
            authorization_notes=request.authorization_notes
        )
        await service.close()
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"授权发送失败: {str(e)}")


@router.get("/tasks/pending", response_model=List[ReviewTaskResponse])
async def get_pending_tasks(
    limit: int = Query(20, ge=1, le=100, description="限制数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取律师待处理任务列表
    """
    try:
        service = LawyerReviewService(db)
        tasks = await service.get_lawyer_pending_tasks(
            lawyer_id=current_user.id,
            limit=limit,
            offset=offset
        )
        await service.close()
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.get("/tasks/{task_id}", response_model=ReviewTaskResponse)
async def get_task_detail(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取任务详情
    """
    try:
        service = LawyerReviewService(db)
        task = await service._get_task_by_id(task_id)
        await service.close()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 检查权限：只有分配的律师或创建者可以查看
        if task.lawyer_id != current_user.id and task.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限查看此任务")
        
        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务详情失败: {str(e)}")


@router.get("/statistics", response_model=TaskStatisticsResponse)
async def get_task_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取任务统计信息
    """
    try:
        service = LawyerReviewService(db)
        stats = await service.get_task_statistics(lawyer_id=current_user.id)
        await service.close()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.get("/statistics/all", response_model=TaskStatisticsResponse)
async def get_all_task_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取全部任务统计信息（管理员）
    """
    try:
        # 这里应该添加管理员权限检查
        service = LawyerReviewService(db)
        stats = await service.get_task_statistics()
        await service.close()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.post("/documents/regenerate")
async def regenerate_document(
    original_content: str = Body(..., description="原始内容"),
    modification_requests: str = Body(..., description="修改要求"),
    document_type: str = Body(..., description="文档类型"),
    current_user: User = Depends(get_current_user)
):
    """
    重新生成文档（独立调用AI服务）
    """
    try:
        ai_service = AIDocumentService()
        
        # 将字符串转换为DocumentType枚举
        doc_type = DocumentType(document_type)
        
        regenerated_content = await ai_service.regenerate_document(
            original_content=original_content,
            modification_requests=modification_requests,
            document_type=doc_type
        )
        
        await ai_service.close()
        
        return {
            "content": regenerated_content,
            "regenerated_at": datetime.utcnow(),
            "modification_requests": modification_requests
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新生成文档失败: {str(e)}")


@router.get("/document-types")
async def get_document_types():
    """
    获取支持的文档类型列表
    """
    return {
        "document_types": [
            {
                "value": doc_type.value,
                "name": {
                    "collection_letter": "催收律师函",
                    "demand_letter": "催告函",
                    "warning_letter": "警告函",
                    "cease_desist": "停止侵权函",
                    "breach_notice": "违约通知函",
                    "custom": "自定义"
                }.get(doc_type.value, doc_type.value)
            }
            for doc_type in DocumentType
        ]
    }


@router.get("/review-statuses")
async def get_review_statuses():
    """
    获取审核状态列表
    """
    return {
        "review_statuses": [
            {
                "value": status.value,
                "name": {
                    "pending": "待审核",
                    "in_review": "审核中",
                    "approved": "已通过",
                    "rejected": "已拒绝",
                    "modification_requested": "要求修改",
                    "modified": "已修改",
                    "authorized": "已授权发送",
                    "sent": "已发送",
                    "cancelled": "已取消"
                }.get(status.value, status.value)
            }
            for status in ReviewStatus
        ]
    } 