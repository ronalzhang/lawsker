"""
多渠道发送API接口
支持法律文书和通知的多渠道发送
"""

from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user, get_config_service
from app.models.user import User
from app.services.delivery_service import (
    MultiChannelDeliveryService, 
    DeliveryChannel, 
    DeliveryStatus,
    create_delivery_service
)
from app.services.config_service import SystemConfigService

router = APIRouter()


# Pydantic 模型定义
class EmailDeliveryRequest(BaseModel):
    """邮件发送请求"""
    to_email: EmailStr = Field(..., description="收件人邮箱")
    subject: str = Field(..., max_length=200, description="邮件主题")
    content: str = Field(..., description="邮件内容")
    is_html: bool = Field(True, description="是否为HTML格式")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="附件列表")


class SMSDeliveryRequest(BaseModel):
    """短信发送请求"""
    phone_number: str = Field(..., regex=r"^1[3-9]\d{9}$", description="手机号码")
    content: str = Field(..., max_length=500, description="短信内容")
    template_id: Optional[str] = Field(None, description="短信模板ID")
    template_params: Optional[Dict[str, Any]] = Field(None, description="模板参数")


class ExpressAddress(BaseModel):
    """快递地址信息"""
    name: str = Field(..., max_length=50, description="收件人姓名")
    phone: str = Field(..., description="联系电话")
    province: str = Field(..., description="省份")
    city: str = Field(..., description="城市")
    area: str = Field(..., description="区县")
    detail_address: str = Field(..., description="详细地址")


class ExpressDeliveryRequest(BaseModel):
    """快递发送请求"""
    recipient_address: ExpressAddress = Field(..., description="收件人地址")
    content_description: str = Field(..., max_length=100, description="快递物品描述")
    express_company: str = Field("SF", description="快递公司代码")
    urgent: bool = Field(False, description="是否加急")
    sender_address: Optional[ExpressAddress] = Field(None, description="发件人地址")


class WeChatDeliveryRequest(BaseModel):
    """微信发送请求"""
    openid: str = Field(..., description="用户OpenID")
    template_id: str = Field(..., description="模板消息ID")
    template_data: Dict[str, Any] = Field(..., description="模板数据")
    url: Optional[str] = Field(None, description="跳转链接")


class DocumentDeliveryRequest(BaseModel):
    """文书发送请求"""
    case_id: UUID = Field(..., description="案件ID")
    document_type: str = Field(..., description="文书类型")
    channels: List[DeliveryChannel] = Field(..., description="发送渠道列表")
    
    # 邮件配置
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    
    # 短信配置
    phone: Optional[str] = Field(None, description="手机号码")
    
    # 快递配置
    express_address: Optional[ExpressAddress] = Field(None, description="快递地址")
    express_urgent: bool = Field(False, description="是否加急快递")
    
    # 微信配置
    wechat_openid: Optional[str] = Field(None, description="微信OpenID")
    wechat_template_id: Optional[str] = Field(None, description="微信模板ID")
    
    # 通用配置
    priority: int = Field(0, ge=0, le=10, description="发送优先级")
    custom_content: Optional[str] = Field(None, description="自定义内容")


class BatchDeliveryRequest(BaseModel):
    """批量发送请求"""
    recipients: List[Dict[str, Any]] = Field(..., description="收件人列表")
    template_type: str = Field(..., description="模板类型")
    template_data: Dict[str, Any] = Field(..., description="模板数据")
    channels: List[DeliveryChannel] = Field(..., description="发送渠道")


class DeliveryResponse(BaseModel):
    """发送响应"""
    success: bool = Field(..., description="是否成功")
    request_id: str = Field(..., description="请求ID")
    message: str = Field(..., description="响应消息")
    status: DeliveryStatus = Field(..., description="发送状态")
    external_id: Optional[str] = Field(None, description="外部系统ID")
    cost: Optional[float] = Field(None, description="发送成本")
    delivered_at: Optional[str] = Field(None, description="发送时间")


class BatchDeliveryResponse(BaseModel):
    """批量发送响应"""
    total_count: int = Field(..., description="总发送数量")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    results: List[DeliveryResponse] = Field(..., description="详细结果")
    total_cost: Optional[float] = Field(None, description="总成本")


class DeliveryStatusResponse(BaseModel):
    """发送状态响应"""
    external_id: str = Field(..., description="外部ID")
    status: DeliveryStatus = Field(..., description="当前状态")
    last_updated: str = Field(..., description="最后更新时间")


# API接口实现
@router.post("/email", response_model=DeliveryResponse)
async def send_email(
    request: EmailDeliveryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """发送邮件"""
    try:
        delivery_service = create_delivery_service(config_service)
        
        result = await delivery_service.email_service.send_email(
            to_email=str(request.to_email),
            subject=request.subject,
            content=request.content,
            attachments=request.attachments,
            is_html=request.is_html
        )
        
        return DeliveryResponse(
            success=result.status != DeliveryStatus.FAILED,
            request_id=result.request_id,
            message=result.message,
            status=result.status,
            external_id=result.external_id,
            cost=result.cost,
            delivered_at=result.delivered_at.isoformat() if result.delivered_at else None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"邮件发送失败: {str(e)}"
        )


@router.post("/sms", response_model=DeliveryResponse)
async def send_sms(
    request: SMSDeliveryRequest,
    current_user: User = Depends(get_current_user),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """发送短信"""
    try:
        delivery_service = create_delivery_service(config_service)
        
        result = await delivery_service.sms_service.send_sms(
            phone_number=request.phone_number,
            content=request.content,
            template_id=request.template_id,
            params=request.template_params
        )
        
        return DeliveryResponse(
            success=result.status != DeliveryStatus.FAILED,
            request_id=result.request_id,
            message=result.message,
            status=result.status,
            external_id=result.external_id,
            cost=result.cost,
            delivered_at=result.delivered_at.isoformat() if result.delivered_at else None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"短信发送失败: {str(e)}"
        )


@router.post("/express", response_model=DeliveryResponse)
async def send_express(
    request: ExpressDeliveryRequest,
    current_user: User = Depends(get_current_user),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """发送快递"""
    try:
        delivery_service = create_delivery_service(config_service)
        
        # 转换地址格式
        recipient_address = request.recipient_address.dict()
        sender_address = request.sender_address.dict() if request.sender_address else None
        
        result = await delivery_service.express_service.send_express(
            recipient_address=recipient_address,
            content_description=request.content_description,
            sender_address=sender_address,
            express_company=request.express_company,
            urgent=request.urgent
        )
        
        return DeliveryResponse(
            success=result.status != DeliveryStatus.FAILED,
            request_id=result.request_id,
            message=result.message,
            status=result.status,
            external_id=result.external_id,
            cost=result.cost,
            delivered_at=result.delivered_at.isoformat() if result.delivered_at else None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"快递发送失败: {str(e)}"
        )


@router.post("/wechat", response_model=DeliveryResponse)
async def send_wechat(
    request: WeChatDeliveryRequest,
    current_user: User = Depends(get_current_user),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """发送微信消息"""
    try:
        delivery_service = create_delivery_service(config_service)
        
        result = await delivery_service.wechat_service.send_wechat_message(
            openid=request.openid,
            template_id=request.template_id,
            data=request.template_data,
            url=request.url
        )
        
        return DeliveryResponse(
            success=result.status != DeliveryStatus.FAILED,
            request_id=result.request_id,
            message=result.message,
            status=result.status,
            external_id=result.external_id,
            cost=result.cost,
            delivered_at=result.delivered_at.isoformat() if result.delivered_at else None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"微信消息发送失败: {str(e)}"
        )


@router.post("/document", response_model=BatchDeliveryResponse)
async def send_document(
    request: DocumentDeliveryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """发送法律文书（多渠道）"""
    try:
        delivery_service = create_delivery_service(config_service)
        
        # 获取案件信息
        from app.models.case import Case
        from sqlalchemy import select
        
        case_query = select(Case).where(Case.id == request.case_id)
        case_result = await db.execute(case_query)
        case = case_result.scalar_one_or_none()
        
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="案件不存在"
            )
        
        # 生成文书内容（这里应该调用AI生成服务）
        document_content = request.custom_content or f"""
        【律思客法律文书】
        
        案件编号：{getattr(case, 'case_number', '未知')}
        文书类型：{request.document_type}
        生成时间：{datetime.now().strftime('%Y年%m月%d日')}
        
        {request.custom_content or '文书内容由AI智能生成...'}
        
        ——————————————————————
        本文书由律思客平台自动生成
        如有疑问，请联系客服
        """
        
        # 构建发送请求列表
        delivery_requests = []
        
        for channel in request.channels:
            if channel == DeliveryChannel.EMAIL and request.email:
                delivery_requests.append({
                    "channel": channel,
                    "recipient": str(request.email),
                    "content": document_content,
                    "subject": f"【律思客】{request.document_type}",
                    "priority": request.priority
                })
            
            elif channel == DeliveryChannel.SMS and request.phone:
                # 短信内容需要精简
                sms_content = f"【律思客】您的{request.document_type}已生成，请查收。详情请登录平台查看。"
                delivery_requests.append({
                    "channel": channel,
                    "recipient": request.phone,
                    "content": sms_content,
                    "priority": request.priority
                })
            
            elif channel == DeliveryChannel.EXPRESS and request.express_address:
                import json
                delivery_requests.append({
                    "channel": channel,
                    "recipient": json.dumps(request.express_address.dict()),
                    "content": document_content,
                    "subject": request.document_type,
                    "priority": request.priority,
                    "metadata": {"urgent": request.express_urgent}
                })
            
            elif channel == DeliveryChannel.WECHAT and request.wechat_openid and request.wechat_template_id:
                delivery_requests.append({
                    "channel": channel,
                    "recipient": request.wechat_openid,
                    "content": document_content,
                    "priority": request.priority,
                    "metadata": {
                        "template_id": request.wechat_template_id,
                        "template_data": {
                            "first": {"value": f"您的{request.document_type}已生成"},
                            "keyword1": {"value": getattr(case, 'case_number', '未知')},
                            "keyword2": {"value": request.document_type},
                            "keyword3": {"value": datetime.now().strftime('%Y年%m月%d日')},
                            "remark": {"value": "请及时查收文书内容"}
                        }
                    }
                })
        
        if not delivery_requests:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请至少配置一种发送方式"
            )
        
        # 批量发送
        from app.services.delivery_service import DeliveryRequest
        formatted_requests = [
            DeliveryRequest(**req) for req in delivery_requests
        ]
        
        results = await delivery_service.batch_send(formatted_requests)
        
        # 统计结果
        success_count = sum(1 for r in results if r.status != DeliveryStatus.FAILED)
        failed_count = len(results) - success_count
        total_cost = sum(r.cost or 0 for r in results)
        
        response_results = [
            DeliveryResponse(
                success=r.status != DeliveryStatus.FAILED,
                request_id=r.request_id,
                message=r.message,
                status=r.status,
                external_id=r.external_id,
                cost=r.cost,
                delivered_at=r.delivered_at.isoformat() if r.delivered_at else None
            ) for r in results
        ]
        
        return BatchDeliveryResponse(
            total_count=len(results),
            success_count=success_count,
            failed_count=failed_count,
            results=response_results,
            total_cost=total_cost
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文书发送失败: {str(e)}"
        )


@router.post("/batch", response_model=BatchDeliveryResponse)
async def batch_send(
    request: BatchDeliveryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """批量发送通知"""
    try:
        delivery_service = create_delivery_service(config_service)
        
        # 构建发送请求
        delivery_requests = []
        
        for recipient in request.recipients:
            for channel in request.channels:
                recipient_info = recipient.get(channel.value)
                if recipient_info:
                    delivery_requests.append({
                        "channel": channel,
                        "recipient": recipient_info,
                        "content": request.template_data.get("content", ""),
                        "subject": request.template_data.get("subject", "通知"),
                        "metadata": {
                            "template_type": request.template_type,
                            "template_data": request.template_data
                        }
                    })
        
        # 执行批量发送
        from app.services.delivery_service import DeliveryRequest
        formatted_requests = [
            DeliveryRequest(**req) for req in delivery_requests
        ]
        
        results = await delivery_service.batch_send(formatted_requests)
        
        # 统计结果
        success_count = sum(1 for r in results if r.status != DeliveryStatus.FAILED)
        failed_count = len(results) - success_count
        total_cost = sum(r.cost or 0 for r in results)
        
        response_results = [
            DeliveryResponse(
                success=r.status != DeliveryStatus.FAILED,
                request_id=r.request_id,
                message=r.message,
                status=r.status,
                external_id=r.external_id,
                cost=r.cost,
                delivered_at=r.delivered_at.isoformat() if r.delivered_at else None
            ) for r in results
        ]
        
        return BatchDeliveryResponse(
            total_count=len(results),
            success_count=success_count,
            failed_count=failed_count,
            results=response_results,
            total_cost=total_cost
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量发送失败: {str(e)}"
        )


@router.get("/status/{external_id}")
async def get_delivery_status(
    external_id: str,
    channel: DeliveryChannel,
    config_service: SystemConfigService = Depends(get_config_service)
):
    """查询发送状态"""
    try:
        delivery_service = create_delivery_service(config_service)
        
        status = await delivery_service.get_delivery_status(external_id, channel)
        
        return DeliveryStatusResponse(
            external_id=external_id,
            status=status,
            last_updated=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询状态失败: {str(e)}"
        )


@router.get("/channels")
async def get_available_channels(
    current_user: User = Depends(get_current_user),
    config_service: SystemConfigService = Depends(get_config_service)
):
    """获取可用的发送渠道"""
    try:
        # 检查各个渠道的配置状态
        channels_status = {}
        
        # 检查邮件配置
        email_config = await config_service.get_config("third_party_apis", "email")
        channels_status["email"] = {
            "available": bool(email_config),
            "name": "邮件发送",
            "cost_per_message": 0.0,
            "description": "支持HTML邮件和附件"
        }
        
        # 检查短信配置
        sms_config = await config_service.get_config("third_party_apis", "sms")
        channels_status["sms"] = {
            "available": bool(sms_config),
            "name": "短信发送",
            "cost_per_message": sms_config.get("cost_per_message", 0.05) if sms_config else 0.05,
            "description": "支持模板短信和普通短信"
        }
        
        # 检查快递配置
        express_config = await config_service.get_config("third_party_apis", "express")
        channels_status["express"] = {
            "available": bool(express_config),
            "name": "快递发送",
            "cost_per_message": 15.0,
            "description": "法律文书快递发送"
        }
        
        # 检查微信配置
        wechat_config = await config_service.get_config("third_party_apis", "wechat")
        channels_status["wechat"] = {
            "available": bool(wechat_config),
            "name": "微信发送",
            "cost_per_message": 0.0,
            "description": "微信模板消息推送"
        }
        
        return {
            "channels": channels_status,
            "total_available": sum(1 for c in channels_status.values() if c["available"])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取渠道信息失败: {str(e)}"
        ) 