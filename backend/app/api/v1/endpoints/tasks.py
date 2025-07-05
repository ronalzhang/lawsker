"""
任务管理API
支持匿名用户发起任务、注册用户管理任务等功能
"""

import logging
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.user import User
from app.models.lawyer_review import DocumentReviewTask, ReviewStatus
from app.services.lawyer_review_service import LawyerReviewService
from app.services.ai_service import AIDocumentService
from app.services.config_service import SystemConfigService
from app.services.sms_service import SMSService, create_sms_service

logger = logging.getLogger(__name__)
router = APIRouter()


# Mock auth dependencies for testing
def get_current_user(db: AsyncSession = Depends(get_db)):
    """Mock current user dependency"""
    # TODO: Replace with actual auth implementation
    user = User()
    user.id = UUID("12345678-1234-5678-9012-123456789012")
    user.phone_number = "13800138000"
    return user


def get_current_user_optional(db: AsyncSession = Depends(get_db)):
    """Mock optional current user dependency"""
    return None


class VerificationCodeRequest(BaseModel):
    """验证码请求"""
    phone: str = Field(..., description="手机号", min_length=11, max_length=11)


class AnonymousTaskRequest(BaseModel):
    """匿名任务请求"""
    # 联系信息
    contact_name: str = Field(..., description="联系人姓名")
    contact_phone: str = Field(..., description="联系人电话")
    contact_email: Optional[str] = Field(None, description="联系人邮箱")
    
    # 服务信息
    service_type: str = Field(..., description="服务类型: collection_letter, demand_letter, legal_consultation")
    urgency: str = Field("普通", description="紧急程度: 紧急, 加急, 普通")
    
    # 案件信息
    case_title: str = Field(..., description="案件标题")
    case_description: str = Field(..., description="案件描述")
    target_name: Optional[str] = Field(None, description="目标对象姓名")
    target_phone: Optional[str] = Field(None, description="目标对象电话")
    target_address: Optional[str] = Field(None, description="目标对象地址")
    amount: Optional[float] = Field(None, description="涉及金额")
    
    # 验证码
    verification_code: str = Field(..., description="短信验证码")


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    task_number: str
    status: str
    created_at: datetime
    estimated_completion: Optional[datetime]
    progress: int  # 0-100
    message: str


class PublicTaskResponse(BaseModel):
    """公开任务响应（匿名用户可见）"""
    task_id: str
    task_number: str
    service_type: str
    status: str
    created_at: datetime
    progress: int
    status_message: str


@router.post("/send-verification-code")
async def send_task_verification_code(
    request: VerificationCodeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    发送任务提交验证码
    """
    try:
        # 创建配置服务和SMS服务
        config_service = SystemConfigService(db)
        sms_service = create_sms_service(config_service)
        
        # 发送验证码
        result = await sms_service.send_verification_code(
            phone_number=request.phone,
            code_type="task",
            expires_in=300  # 5分钟
        )
        
        return {
            "success": result["success"],
            "message": result["message"],
            "expires_in": result.get("expires_in", 300)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送验证码失败: {str(e)}"
        )


@router.post("/anonymous/submit", response_model=dict)
async def submit_anonymous_task(
    request: AnonymousTaskRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    匿名用户提交任务
    """
    try:
        # 创建配置服务和SMS服务
        config_service = SystemConfigService(db)
        sms_service = create_sms_service(config_service)
        
        # 验证短信验证码
        is_valid = await sms_service.verify_code(
            phone_number=request.contact_phone,
            code=request.verification_code,
            code_type="task",
            remove_after_verify=True
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="短信验证码错误或已过期"
            )
        
        # 创建匿名任务（先创建简单版本，然后再生成AI内容）
        task_number = f"ANO{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid4())[:4].upper()}"
        
        # 构建任务数据
        task_data = {
            "contact_name": request.contact_name,
            "contact_phone": request.contact_phone,
            "contact_email": request.contact_email,
            "service_type": request.service_type,
            "case_title": request.case_title,
            "case_description": request.case_description,
            "target_name": request.target_name,
            "target_phone": request.target_phone,
            "target_address": request.target_address,
            "amount": request.amount,
            "urgency": request.urgency
        }
        
        # 创建基础内容（如果AI服务不可用）
        basic_content = f"""
        服务类型：{request.service_type}
        案件标题：{request.case_title}
        案件描述：{request.case_description}
        委托人：{request.contact_name}
        联系电话：{request.contact_phone}
        """
        
        if request.target_name:
            basic_content += f"目标对象：{request.target_name}\n"
        if request.amount:
            basic_content += f"涉及金额：{request.amount}元\n"
        
        # 创建任务记录
        task = DocumentReviewTask(
            task_number=task_number,
            creator_id=None,  # 匿名任务
            lawyer_id=None,   # 稍后分配
            document_type=request.service_type,
            original_content=basic_content,
            current_content=basic_content,
            status=ReviewStatus.PENDING,
            priority=3 if request.urgency == "紧急" else 2,
            ai_metadata={
                "anonymous_task": True,
                "contact_info": {
                    "name": request.contact_name,
                    "phone": request.contact_phone,
                    "email": request.contact_email
                },
                "task_data": task_data
            },
            generation_prompt=f"匿名任务: {request.service_type} - {request.case_title}"
        )
        
        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        # 发送确认短信
        try:
            track_url = f"http://app.lawsker.com/track/{task.task_number}"
            await sms_service.send_notification(
                phone_number=request.contact_phone,
                message=f"【律思客】您的任务已提交成功，任务编号：{task.task_number}，我们将在24小时内处理。查询进度：{track_url}",
                template_code="task_created",
                template_params={
                    "task_number": str(task.task_number),
                    "track_url": track_url
                }
            )
        except Exception as e:
            # 短信发送失败不影响任务创建
            logger.warning(f"任务确认短信发送失败: {str(e)}")
        
        return {
            "success": True,
            "task_id": str(task.id),
            "task_number": task.task_number,
            "message": "任务提交成功，我们将在24小时内处理",
            "estimated_completion": "1-3个工作日",
            "tracking_url": f"/api/v1/tasks/track/{task.task_number}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"任务提交失败: {str(e)}"
        )


@router.get("/track/{task_number}", response_model=PublicTaskResponse)
async def track_task_public(
    task_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    公开任务跟踪（无需登录）
    """
    try:
        # 查询任务
        query = select(DocumentReviewTask).where(
            DocumentReviewTask.task_number == task_number
        )
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        # 计算进度
        progress_map = {
            ReviewStatus.PENDING: 10,
            ReviewStatus.IN_REVIEW: 30,
            ReviewStatus.MODIFICATION_REQUESTED: 50,
            ReviewStatus.APPROVED: 80,
            ReviewStatus.AUTHORIZED: 90,
            ReviewStatus.SENT: 100,
            ReviewStatus.REJECTED: 0,
            ReviewStatus.CANCELLED: 0
        }
        
        status_message_map = {
            ReviewStatus.PENDING: "任务已接收，正在分配律师",
            ReviewStatus.IN_REVIEW: "律师正在审核中",
            ReviewStatus.MODIFICATION_REQUESTED: "律师要求修改内容",
            ReviewStatus.APPROVED: "律师已审核通过",
            ReviewStatus.AUTHORIZED: "已授权发送",
            ReviewStatus.SENT: "文书已发送完成",
            ReviewStatus.REJECTED: "任务被拒绝",
            ReviewStatus.CANCELLED: "任务已取消"
        }
        
        # 安全地获取状态值
        task_status = task.status
        
        return PublicTaskResponse(
            task_id=str(task.id),
            task_number=str(task.task_number),
            service_type=str(task.document_type),
            status=task_status.value if hasattr(task_status, 'value') else str(task_status),
            created_at=task.created_at,
            progress=progress_map.get(task_status, 0),
            status_message=status_message_map.get(task_status, "处理中")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询任务失败: {str(e)}"
        )


@router.get("/my-tasks", response_model=List[dict])
async def get_my_tasks(
    limit: int = 20,
    offset: int = 0,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的任务列表
    """
    try:
        # 构建查询条件
        conditions = [DocumentReviewTask.creator_id == current_user.id]
        
        if status_filter:
            conditions.append(DocumentReviewTask.status == status_filter)
        
        # 查询任务
        query = select(DocumentReviewTask).where(
            and_(*conditions)
        ).order_by(
            DocumentReviewTask.created_at.desc()
        ).limit(limit).offset(offset)
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        # 构建响应数据
        task_list = []
        for task in tasks:
            task_data = {
                "task_id": str(task.id),
                "task_number": str(task.task_number),
                "document_type": str(task.document_type),
                "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "priority": task.priority
            }
            
            # 添加匿名任务的联系信息
            task_metadata = task.ai_metadata or {}
            if task_metadata and task_metadata.get("anonymous_task"):
                contact_info = task_metadata.get("contact_info", {})
                task_data["contact_info"] = contact_info
            
            task_list.append(task_data)
        
        return task_list
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务列表失败: {str(e)}"
        )


@router.post("/convert-anonymous")
async def convert_anonymous_task(
    task_number: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    将匿名任务转换为用户任务
    """
    try:
        # 查询匿名任务
        query = select(DocumentReviewTask).where(
            and_(
                DocumentReviewTask.task_number == task_number,
                DocumentReviewTask.creator_id.is_(None)  # 匿名任务
            )
        )
        
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="匿名任务不存在或已被转换"
            )
        
        # 检查任务是否可以转换（比如联系电话匹配等）
        task_metadata = task.ai_metadata or {}
        if task_metadata and task_metadata.get("contact_info"):
            contact_phone = task_metadata["contact_info"].get("phone")
            user_phone = getattr(current_user, 'phone_number', None)
            if contact_phone and user_phone and contact_phone != user_phone:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只能转换与您手机号匹配的任务"
                )
        
        # 转换任务
        task.creator_id = current_user.id
        
        # 更新metadata标记
        if task_metadata:
            task_metadata["converted_to_user"] = True
            task_metadata["converted_at"] = datetime.now().isoformat()
            task_metadata["converted_user_id"] = str(current_user.id)
            task.ai_metadata = task_metadata
        
        await db.commit()
        
        return {
            "success": True,
            "message": "任务转换成功",
            "task_id": str(task.id),
            "task_number": str(task.task_number)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"任务转换失败: {str(e)}"
        ) 