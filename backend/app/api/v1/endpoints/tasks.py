"""
任务管理API
支持匿名用户发起任务、注册用户管理任务等功能
"""

import logging
import json
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update, func
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.lawyer_review import DocumentReviewTask, ReviewStatus
from app.models.statistics import TaskPublishRecord, LawyerDailyLimit, UserDailyPublishLimit
from app.models.user import User
from app.services.lawyer_review_service import LawyerReviewService
from app.services.ai_service import AIDocumentService
from app.services.config_service import SystemConfigService
from app.services.sms_service import SMSService, create_sms_service

logger = logging.getLogger(__name__)
router = APIRouter()


# 真实认证依赖
from app.core.deps import get_current_user


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


class UserTaskRequest(BaseModel):
    """用户任务发布请求"""
    task_type: str = Field(..., description="任务类型")
    title: str = Field(..., description="任务标题")
    description: str = Field(..., description="任务描述")
    budget: float = Field(..., description="预算金额")
    urgency: str = Field("normal", description="紧急程度")
    target_info: dict = Field(default_factory=dict, description="目标对象信息")


class LawyerGrabRequest(BaseModel):
    """律师抢单请求"""
    task_id: str = Field(..., description="任务ID")
    notes: Optional[str] = Field(None, description="抢单备注")


class ContactExchangeRequest(BaseModel):
    """联系方式交换请求"""
    task_id: str = Field(..., description="任务ID")
    my_contact: dict = Field(..., description="我的联系方式")
    message: Optional[str] = Field(None, description="附加消息")


class TaskStatusUpdateRequest(BaseModel):
    """任务状态更新请求"""
    task_id: str = Field(..., description="任务ID")
    new_status: str = Field(..., description="新状态")
    notes: Optional[str] = Field(None, description="备注说明")
    completion_data: Optional[dict] = Field(None, description="完成数据")


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
    """公开任务响应（用于跟踪）"""
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
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的任务列表
    """
    try:
        # 构建查询条件
        conditions = [DocumentReviewTask.creator_id == current_user["id"]]
        
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
    current_user: Dict[str, Any] = Depends(get_current_user),
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
        task.creator_id = current_user["id"]
        
        # 更新metadata标记
        if task_metadata:
            task_metadata["converted_to_user"] = True
            task_metadata["converted_at"] = datetime.now().isoformat()
            task_metadata["converted_user_id"] = str(current_user["id"])
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


@router.get("/", response_model=List[dict])
async def get_tasks(
    user_type: Optional[str] = Query(None, description="用户类型过滤: sales, lawyer, institution"),
    limit: int = Query(20, ge=1, le=100, description="返回任务数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    status_filter: Optional[str] = Query(None, description="状态过滤"),
    db: AsyncSession = Depends(get_db)
) -> List[dict]:
    """
    获取任务列表
    支持按用户类型过滤
    """
    try:
        # 构建查询条件
        query = select(DocumentReviewTask)
        
        # 根据用户类型过滤
        if user_type == "sales":
            # 销售相关任务 - 获取匿名任务或销售创建的任务
            query = query.where(
                or_(
                    DocumentReviewTask.creator_id.is_(None),  # 匿名任务
                    DocumentReviewTask.ai_metadata.has_key("sales_related")  # 销售相关任务
                )
            )
        elif user_type == "lawyer":
            # 律师相关任务 - 分配给律师的任务
            query = query.where(DocumentReviewTask.lawyer_id.is_not(None))
        elif user_type == "institution":
            # 机构相关任务
            query = query.where(DocumentReviewTask.ai_metadata.has_key("institution_related"))
        
        # 状态过滤
        if status_filter:
            if status_filter == "pending":
                query = query.where(DocumentReviewTask.status == ReviewStatus.PENDING)
            elif status_filter == "in_progress":
                query = query.where(DocumentReviewTask.status == ReviewStatus.IN_PROGRESS)
            elif status_filter == "completed":
                query = query.where(DocumentReviewTask.status == ReviewStatus.COMPLETED)
        
        # 添加排序和限制
        query = query.order_by(DocumentReviewTask.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        # 执行查询
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        # 转换为响应格式
        task_list = []
        for task in tasks:
            task_data = {
                "id": str(task.id),
                "task_number": task.task_number,
                "document_type": task.document_type,
                "status": task.status.value,
                "priority": task.priority,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                "lawyer_id": str(task.lawyer_id) if task.lawyer_id else None,
                "creator_id": str(task.creator_id) if task.creator_id else None,
                "estimated_completion": task.estimated_completion.isoformat() if task.estimated_completion else None,
                "ai_metadata": task.ai_metadata or {}
            }
            task_list.append(task_data)
        
        return task_list
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取任务列表失败: {str(e)}"
        ) 

@router.post("/user/publish", response_model=dict)
async def publish_user_task(
    request: UserTaskRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    用户发布任务 - 包含每日发单限制检查
    """
    try:
        today = date.today()
        
        # 检查用户每日发单限制
        daily_limit_query = select(UserDailyPublishLimit).where(
            and_(
                UserDailyPublishLimit.user_id == current_user["id"],
                UserDailyPublishLimit.date == today
            )
        )
        daily_limit_result = await db.execute(daily_limit_query)
        daily_limit = daily_limit_result.scalar_one_or_none()
        
        # 如果没有今日记录，创建一个
        if not daily_limit:
            # 从系统配置获取每日限制
            config_service = SystemConfigService(db)
            user_config = await config_service.get_config("business", "user_daily_limit")
            default_limit = user_config.get("default_limit", 5) if user_config else 5
            
            daily_limit = UserDailyPublishLimit(
                user_id=current_user["id"],
                date=today,
                published_count=0,
                max_daily_limit=default_limit
            )
            db.add(daily_limit)
            await db.flush()  # 刷新以获取ID，但不提交事务
        
        # 检查是否已达到每日限制
        if daily_limit.published_count >= daily_limit.max_daily_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"您今日已达到发单上限（{daily_limit.max_daily_limit}单），请明日再试。"
            )
        
        # 创建任务记录
        task_record = TaskPublishRecord(
            user_id=current_user["id"],
            task_type=request.task_type,
            title=request.title,
            description=request.description,
            target_info=request.target_info,
            amount=request.budget,
            urgency=request.urgency,
            status="published"  # 已发布，等待律师抢单
        )
        
        db.add(task_record)
        
        # 更新用户每日发单计数
        daily_limit.published_count += 1
        daily_limit.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(task_record)
        
        return {
            "success": True,
            "task_id": str(task_record.id),
            "message": f"任务发布成功！今日还可发布 {daily_limit.max_daily_limit - daily_limit.published_count} 个任务",
            "status": "published",
            "daily_remaining": daily_limit.max_daily_limit - daily_limit.published_count,
            "daily_limit": daily_limit.max_daily_limit
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"发布任务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发布任务失败: {str(e)}"
        )


@router.get("/user/daily-publish-limit/status", response_model=dict)
async def get_user_daily_publish_limit_status(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户每日发单限制状态
    """
    try:
        today = date.today()
        
        # 查询今日限制记录
        daily_limit_query = select(UserDailyPublishLimit).where(
            and_(
                UserDailyPublishLimit.user_id == current_user["id"],
                UserDailyPublishLimit.date == today
            )
        )
        daily_limit_result = await db.execute(daily_limit_query)
        daily_limit = daily_limit_result.scalar_one_or_none()
        
        # 如果没有记录，创建默认记录
        if not daily_limit:
            # 从系统配置获取每日限制
            config_service = SystemConfigService(db)
            user_config = await config_service.get_config("business", "user_daily_limit")
            default_limit = user_config.get("default_limit", 5) if user_config else 5
            
            daily_limit = UserDailyPublishLimit(
                user_id=current_user["id"],
                date=today,
                published_count=0,
                max_daily_limit=default_limit
            )
            db.add(daily_limit)
            await db.commit()
            await db.refresh(daily_limit)
        
        # 检查今日已发布的任务数量（以实际任务记录为准）
        actual_published_query = select(func.count(TaskPublishRecord.id)).where(
            and_(
                TaskPublishRecord.user_id == current_user["id"],
                func.date(TaskPublishRecord.created_at) == today,
                TaskPublishRecord.status.in_(["published", "grabbed", "in_progress", "completed"])
            )
        )
        actual_published_count = await db.scalar(actual_published_query)
        
        # 同步计数（防止数据不一致）
        if actual_published_count != daily_limit.published_count:
            daily_limit.published_count = actual_published_count
            await db.commit()
        
        return {
            "date": today.isoformat(),
            "published_count": daily_limit.published_count,
            "max_daily_limit": daily_limit.max_daily_limit,
            "remaining": max(0, daily_limit.max_daily_limit - daily_limit.published_count),
            "can_publish_more": daily_limit.published_count < daily_limit.max_daily_limit,
            "status": "available" if daily_limit.published_count < daily_limit.max_daily_limit else "limit_reached"
        }
        
    except Exception as e:
        logger.error(f"获取用户每日发单限制状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取发单限制状态失败"
        )


@router.get("/available", response_model=List[dict])
async def get_available_tasks(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    task_type: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取可抢单的任务列表（供律师查看）
    """
    try:
        # 构建查询条件
        conditions = [
            TaskPublishRecord.status == "published",  # 已发布，未被抢单
            TaskPublishRecord.assigned_to.is_(None)   # 未分配律师
        ]
        
        if task_type:
            conditions.append(TaskPublishRecord.task_type == task_type)
        
        # 查询可抢单任务
        query = select(TaskPublishRecord).where(
            and_(*conditions)
        ).order_by(
            TaskPublishRecord.created_at.desc()
        ).limit(limit).offset(offset)
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        # 格式化响应
        task_list = []
        for task in tasks:
            # 获取发布者信息（保护隐私）
            user_query = select(User).where(User.id == task.user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            task_data = {
                "task_id": str(task.id),
                "task_type": task.task_type,
                "title": task.title,
                "description": task.description,
                "budget": float(task.amount) if task.amount else 0,
                "urgency": task.urgency,
                "created_at": task.created_at.isoformat(),
                "publisher_name": user.username[:2] + "***" if user and user.username else "匿名用户",
                "target_info": task.target_info
            }
            task_list.append(task_data)
        
        return task_list
        
    except Exception as e:
        logger.error(f"获取可抢单任务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务列表失败: {str(e)}"
        )


@router.post("/grab/{task_id}", response_model=dict)
async def grab_task(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    律师抢单 - 匹配前端API调用
    """
    try:
        task_uuid = UUID(task_id)
        today = date.today()
        
        # 检查律师每日接单限制
        daily_limit_query = select(LawyerDailyLimit).where(
            and_(
                LawyerDailyLimit.lawyer_id == current_user["id"],
                LawyerDailyLimit.date == today
            )
        )
        daily_limit_result = await db.execute(daily_limit_query)
        daily_limit = daily_limit_result.scalar_one_or_none()
        
        # 如果没有今日记录，创建一个
        if not daily_limit:
            # 从系统配置获取每日限制
            config_service = SystemConfigService(db)
            lawyer_config = await config_service.get_config("business", "lawyer_daily_limit")
            default_limit = lawyer_config.get("default_limit", 3) if lawyer_config else 3
            
            daily_limit = LawyerDailyLimit(
                lawyer_id=current_user["id"],
                date=today,
                grabbed_count=0,
                max_daily_limit=default_limit
            )
            db.add(daily_limit)
            await db.flush()  # 刷新以获取ID，但不提交事务
        
        # 检查是否已达到每日限制
        if daily_limit.grabbed_count >= daily_limit.max_daily_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"您今日已达到接单上限（{daily_limit.max_daily_limit}单），请明日再试。完成已接单任务后才能接新单。"
            )
        
        # 查询任务
        query = select(TaskPublishRecord).where(
            and_(
                TaskPublishRecord.id == task_uuid,
                TaskPublishRecord.status == "published",
                TaskPublishRecord.assigned_to.is_(None)
            )
        )
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在或已被其他律师抢单"
            )
        
        # 更新任务状态
        task.assigned_to = current_user["id"]
        task.status = "grabbed"
        task.updated_at = datetime.now()
        
        # 更新律师每日抢单计数
        daily_limit.grabbed_count += 1
        daily_limit.updated_at = datetime.now()
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"抢单成功！今日还可接单 {daily_limit.max_daily_limit - daily_limit.grabbed_count} 次",
            "task_id": str(task.id),
            "status": "grabbed",
            "daily_remaining": daily_limit.max_daily_limit - daily_limit.grabbed_count,
            "daily_limit": daily_limit.max_daily_limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"抢单失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"抢单失败: {str(e)}"
        )


@router.get("/daily-limit/status", response_model=dict)
async def get_daily_limit_status(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取律师每日接单限制状态
    """
    try:
        today = date.today()
        
        # 查询今日限制记录
        daily_limit_query = select(LawyerDailyLimit).where(
            and_(
                LawyerDailyLimit.lawyer_id == current_user["id"],
                LawyerDailyLimit.date == today
            )
        )
        daily_limit_result = await db.execute(daily_limit_query)
        daily_limit = daily_limit_result.scalar_one_or_none()
        
        # 如果没有记录，创建默认记录
        if not daily_limit:
            # 暂时使用硬编码默认值，避免配置服务问题
            default_limit = 3
            
            daily_limit = LawyerDailyLimit(
                lawyer_id=current_user["id"],
                date=today,
                grabbed_count=0,
                max_daily_limit=default_limit
            )
            db.add(daily_limit)
            await db.commit()
            await db.refresh(daily_limit)
        
        # 检查今日已接单的任务数量（以实际任务记录为准）
        actual_grabbed_query = select(func.count(TaskPublishRecord.id)).where(
            and_(
                TaskPublishRecord.assigned_to == current_user["id"],
                func.date(TaskPublishRecord.updated_at) == today,
                TaskPublishRecord.status.in_(["grabbed", "in_progress", "completed"])
            )
        )
        actual_grabbed_count = await db.scalar(actual_grabbed_query)
        
        # 同步计数（防止数据不一致）
        if actual_grabbed_count != daily_limit.grabbed_count:
            daily_limit.grabbed_count = actual_grabbed_count
            await db.commit()
        
        return {
            "date": today.isoformat(),
            "grabbed_count": daily_limit.grabbed_count,
            "max_daily_limit": daily_limit.max_daily_limit,
            "remaining": max(0, daily_limit.max_daily_limit - daily_limit.grabbed_count),
            "can_grab_more": daily_limit.grabbed_count < daily_limit.max_daily_limit,
            "status": "available" if daily_limit.grabbed_count < daily_limit.max_daily_limit else "limit_reached"
        }
        
    except Exception as e:
        logger.error(f"获取每日限制状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取状态失败: {str(e)}"
        )


@router.post("/contact/exchange", response_model=dict)
async def exchange_contact_info(
    request: ContactExchangeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    联系方式交换
    """
    try:
        task_id = UUID(request.task_id)
        
        # 查询任务
        query = select(TaskPublishRecord).where(TaskPublishRecord.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        # 检查权限（只有任务发布者或接单律师可以交换联系方式）
        if task.user_id != current_user["id"] and task.assigned_to != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限交换联系方式"
            )
        
        # 更新任务状态和联系方式
        if not hasattr(task, 'contact_exchange_data'):
            task.target_info = task.target_info or {}
        
        # 添加联系方式交换记录
        if "contact_exchanges" not in task.target_info:
            task.target_info["contact_exchanges"] = []
        
        task.target_info["contact_exchanges"].append({
            "user_id": str(current_user["id"]),
            "contact_info": request.my_contact,
            "message": request.message,
            "timestamp": datetime.now().isoformat()
        })
        
        # 如果双方都已交换，更新状态
        exchanges = task.target_info.get("contact_exchanges", [])
        user_ids = {exchange["user_id"] for exchange in exchanges}
        
        if str(task.user_id) in user_ids and str(task.assigned_to) in user_ids:
            task.status = "contact_exchanged"
        
        await db.commit()
        
        return {
            "success": True,
            "message": "联系方式已交换",
            "exchange_status": task.status,
            "can_proceed_offline": task.status == "contact_exchanged"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"联系方式交换失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"联系方式交换失败: {str(e)}"
        )


@router.post("/status/update", response_model=dict)
async def update_task_status(
    request: TaskStatusUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新任务状态
    """
    try:
        task_id = UUID(request.task_id)
        
        # 查询任务
        query = select(TaskPublishRecord).where(TaskPublishRecord.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        # 检查权限
        if task.user_id != current_user["id"] and task.assigned_to != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限更新任务状态"
            )
        
        old_status = task.status
        task.status = request.new_status
        task.updated_at = datetime.now()
        
        if request.notes:
            task.completion_notes = request.notes
        
        # 如果任务完成，记录完成时间和数据
        if request.new_status == "completed":
            task.completed_at = datetime.now()
            
            # 记录完成数据（包括是否通过平台收费、线下交易金额等）
            if request.completion_data:
                task.target_info = task.target_info or {}
                task.target_info["completion_data"] = request.completion_data
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"任务状态已从 {old_status} 更新为 {request.new_status}",
            "task_id": str(task.id),
            "new_status": request.new_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"更新任务状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新任务状态失败: {str(e)}"
        )


@router.get("/my-tasks/user", response_model=List[dict])
async def get_user_tasks(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户发布的任务列表
    """
    try:
        conditions = [TaskPublishRecord.user_id == current_user["id"]]
        
        if status_filter:
            conditions.append(TaskPublishRecord.status == status_filter)
        
        query = select(TaskPublishRecord).where(
            and_(*conditions)
        ).order_by(
            TaskPublishRecord.created_at.desc()
        ).limit(limit).offset(offset)
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        task_list = []
        for task in tasks:
            lawyer_info = None
            if task.assigned_to:
                lawyer_query = select(User).where(User.id == task.assigned_to)
                lawyer_result = await db.execute(lawyer_query)
                lawyer = lawyer_result.scalar_one_or_none()
                if lawyer:
                    lawyer_info = {
                        "name": lawyer.username,
                        "phone": lawyer.phone_number
                    }
            
            task_data = {
                "task_id": str(task.id),
                "task_type": task.task_type,
                "title": task.title,
                "description": task.description,
                "budget": float(task.amount) if task.amount else 0,
                "status": task.status,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "lawyer_info": lawyer_info,
                "contact_exchanges": task.target_info.get("contact_exchanges", []) if task.target_info else [],
                "completion_data": task.target_info.get("completion_data") if task.target_info else None
            }
            task_list.append(task_data)
        
        return task_list
        
    except Exception as e:
        logger.error(f"获取用户任务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务列表失败: {str(e)}"
        )


@router.get("/my-tasks/lawyer", response_model=List[dict])
async def get_lawyer_tasks(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取律师接单的任务列表
    """
    try:
        conditions = [TaskPublishRecord.assigned_to == current_user["id"]]
        
        if status_filter:
            conditions.append(TaskPublishRecord.status == status_filter)
        
        query = select(TaskPublishRecord).where(
            and_(*conditions)
        ).order_by(
            TaskPublishRecord.created_at.desc()
        ).limit(limit).offset(offset)
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        task_list = []
        for task in tasks:
            client_info = None
            if task.user_id:
                client_query = select(User).where(User.id == task.user_id)
                client_result = await db.execute(client_query)
                client = client_result.scalar_one_or_none()
                if client:
                    client_info = {
                        "name": client.username,
                        "phone": client.phone_number
                    }
            
            task_data = {
                "task_id": str(task.id),
                "task_type": task.task_type,
                "title": task.title,
                "description": task.description,
                "budget": float(task.amount) if task.amount else 0,
                "status": task.status,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "client_info": client_info,
                "contact_exchanges": task.target_info.get("contact_exchanges", []) if task.target_info else [],
                "completion_data": task.target_info.get("completion_data") if task.target_info else None
            }
            task_list.append(task_data)
        
        return task_list
        
    except Exception as e:
        logger.error(f"获取律师任务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务列表失败: {str(e)}"
        )


@router.get("/feedback", response_model=List[dict])
async def get_task_feedback(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取任务反馈信息
    """
    try:
        # 查询与当前用户相关的已完成任务
        conditions = [
            TaskPublishRecord.status == "completed",
            or_(
                TaskPublishRecord.user_id == current_user["id"],  # 用户发布的任务
                TaskPublishRecord.assigned_to == current_user["id"]  # 律师接单的任务
            )
        ]
        
        query = select(TaskPublishRecord).where(
            and_(*conditions)
        ).order_by(
            TaskPublishRecord.updated_at.desc()
        ).limit(limit).offset(offset)
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        feedback_list = []
        for task in tasks:
            # 获取对方信息
            other_user_id = task.assigned_to if task.user_id == current_user["id"] else task.user_id
            if other_user_id:
                user_query = select(User).where(User.id == other_user_id)
                user_result = await db.execute(user_query)
                other_user = user_result.scalar_one_or_none()
            else:
                other_user = None
            
            feedback_data = {
                "task_id": str(task.id),
                "task_title": task.title,
                "task_type": task.task_type,
                "status": task.status,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "my_role": "client" if task.user_id == current_user["id"] else "lawyer",
                "other_party": {
                    "name": other_user.username if other_user else "匿名用户",
                    "role": "lawyer" if task.user_id == current_user["id"] else "client"
                },
                "budget": float(task.amount) if task.amount else 0,
                "feedback_available": True,
                "rating": None,  # 实际项目中可以添加评分功能
                "comments": task.completion_notes or ""
            }
            feedback_list.append(feedback_data)
        
        return feedback_list
        
    except Exception as e:
        logger.error(f"获取任务反馈失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务反馈失败: {str(e)}"
        )


@router.post("/convert-cases-to-tasks")
async def convert_cases_to_tasks(
    db: AsyncSession = Depends(get_db)
):
    """
    将案件数据转换为任务数据（供律师抢单）
    """
    try:
        # 从案件表导入数据
        from app.models.case import Case
        
        # 查询未分配律师或状态为PENDING的案件
        cases_query = select(Case).where(
            or_(
                Case.assigned_to_user_id.is_(None),
                Case.status == "PENDING"
            )
        ).limit(50)  # 限制数量避免一次性转换太多
        
        cases_result = await db.execute(cases_query)
        cases = cases_result.scalars().all()
        
        converted_count = 0
        
        for case in cases:
            # 检查是否已经转换过
            existing_task = await db.scalar(
                select(TaskPublishRecord).where(
                    TaskPublishRecord.source_case_id == case.id
                )
            )
            
            if existing_task:
                continue  # 已转换过，跳过
            
            # 解析债务人信息
            debtor_info = {}
            if case.debtor_info:
                if isinstance(case.debtor_info, str):
                    try:
                        debtor_info = json.loads(case.debtor_info)
                    except:
                        debtor_info = {"raw": case.debtor_info}
                else:
                    debtor_info = case.debtor_info
            
            # 根据案件信息推断任务类型
            task_type = "debt_collection"  # 默认债务催收
            if case.description:
                desc_lower = case.description.lower()
                if "合同" in desc_lower:
                    task_type = "contract_review"
                elif "咨询" in desc_lower:
                    task_type = "legal_consultation"
                elif "律师函" in desc_lower:
                    task_type = "lawyer_letter"
            
            # 生成任务标题
            debtor_name = debtor_info.get("name", "未知债务人")
            case_amount = float(case.case_amount) if case.case_amount else 0
            
            if case_amount > 0:
                title = f"{debtor_name}债务催收案 - ¥{case_amount:,.0f}"
                budget = min(max(case_amount * 0.02, 500), 5000)  # 2%佣金，最低500，最高5000
            else:
                title = f"{debtor_name}法律服务案"
                budget = 800  # 默认预算
            
            # 生成详细描述
            description = f"""
案件编号：{case.case_number}
债务人：{debtor_name}
联系方式：{debtor_info.get('phone', '待提供')}
地址：{debtor_info.get('address', '待提供')}
案件金额：¥{case_amount:,.2f}

案件描述：
{case.description or '详细信息请与委托人沟通'}

要求：
1. 专业处理债务催收事务
2. 按法律程序发送催收函件
3. 及时反馈处理进度
4. 确保符合相关法律法规
""".strip()
            
            # 设置紧急程度
            urgency = "normal"
            if case.legal_status == "EXPIRING_SOON":
                urgency = "urgent"
            elif case_amount and case_amount > 100000:
                urgency = "high"
            
            # 创建任务记录
            task_record = TaskPublishRecord(
                user_id=None,  # 系统生成的任务，暂时不分配用户
                task_type=task_type,
                title=title,
                description=description,
                target_info={
                    "debtor_info": debtor_info,
                    "case_number": case.case_number,
                    "source": "case_conversion",
                    "original_case_id": str(case.id)
                },
                amount=budget,
                urgency=urgency,
                status="published",  # 立即可抢单
                source_case_id=case.id,  # 关联原案件ID
                created_at=case.created_at or datetime.now()
            )
            
            db.add(task_record)
            converted_count += 1
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"成功转换 {converted_count} 个案件为可抢单任务",
            "converted_count": converted_count,
            "total_available_tasks": await db.scalar(
                select(func.count(TaskPublishRecord.id)).where(
                    and_(
                        TaskPublishRecord.status == "published",
                        TaskPublishRecord.assigned_to.is_(None)
                    )
                )
            )
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"案件转换失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"案件转换失败: {str(e)}"
        )


@router.get("/statistics/platform", response_model=dict)
async def get_platform_statistics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    获取平台业务统计数据（供管理后台使用）
    """
    try:
        from datetime import datetime, timedelta
        
        # 计算时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 总任务数
        total_query = select(TaskPublishRecord).where(
            TaskPublishRecord.created_at >= start_date
        )
        total_result = await db.execute(total_query)
        total_tasks = len(total_result.scalars().all())
        
        # 已完成任务数
        completed_query = select(TaskPublishRecord).where(
            and_(
                TaskPublishRecord.created_at >= start_date,
                TaskPublishRecord.status == "completed"
            )
        )
        completed_result = await db.execute(completed_query)
        completed_tasks = len(completed_result.scalars().all())
        
        # 联系方式交换数
        exchange_query = select(TaskPublishRecord).where(
            and_(
                TaskPublishRecord.created_at >= start_date,
                TaskPublishRecord.status.in_(["contact_exchanged", "completed"])
            )
        )
        exchange_result = await db.execute(exchange_query)
        exchanges = len(exchange_result.scalars().all())
        
        # 总交易金额（预估）
        amount_query = select(TaskPublishRecord).where(
            and_(
                TaskPublishRecord.created_at >= start_date,
                TaskPublishRecord.status == "completed"
            )
        )
        amount_result = await db.execute(amount_query)
        amount_tasks = amount_result.scalars().all()
        total_amount = sum(float(task.amount or 0) for task in amount_tasks)
        
        return {
            "period_days": days,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "contact_exchanges": exchanges,
            "completion_rate": round(completed_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0,
            "exchange_rate": round(exchanges / total_tasks * 100, 2) if total_tasks > 0 else 0,
            "estimated_transaction_volume": total_amount,
            "platform_activity_score": min(100, total_tasks * 2 + exchanges * 5)
        }
        
    except Exception as e:
        logger.error(f"获取平台统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计数据失败: {str(e)}"
        ) 