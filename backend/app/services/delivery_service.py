"""
多渠道发送服务
支持邮件、短信、快递等多种发送方式
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass

import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import ssl

from app.services.config_service import ConfigService

logger = logging.getLogger(__name__)


class DeliveryChannel(str, Enum):
    """发送渠道枚举"""
    EMAIL = "email"
    SMS = "sms"
    EXPRESS = "express"
    WECHAT = "wechat"


class DeliveryStatus(str, Enum):
    """发送状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class DeliveryRequest:
    """发送请求数据类"""
    channel: DeliveryChannel
    recipient: str  # 收件人（邮箱、手机号、地址等）
    content: str
    subject: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    priority: int = 0  # 优先级，0为最高
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class DeliveryResult:
    """发送结果数据类"""
    request_id: str
    status: DeliveryStatus
    message: str
    external_id: Optional[str] = None  # 第三方服务返回的ID
    delivered_at: Optional[datetime] = None
    cost: Optional[float] = None


class EmailService:
    """邮件发送服务"""
    
    def __init__(self, config_service: ConfigService):
        self.config_service = config_service
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        content: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
        is_html: bool = True
    ) -> DeliveryResult:
        """发送邮件"""
        try:
            # 获取邮件配置
            email_config = await self.config_service.get_config("third_party_apis", "email")
            if not email_config:
                raise Exception("邮件服务未配置")
            
            # 创建邮件消息
            msg = MIMEMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 添加邮件内容
            if is_html:
                msg.attach(MIMEText(content, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(content, 'plain', 'utf-8'))
            
            # 添加附件
            if attachments:
                for attachment in attachments:
                    file_data = attachment.get('data')
                    filename = attachment.get('filename', 'attachment')
                    
                    if file_data:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(file_data)
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {filename}'
                        )
                        msg.attach(part)
            
            # 发送邮件
            context = ssl.create_default_context()
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls(context=context)
                server.login(email_config['username'], email_config['password'])
                server.sendmail(email_config['from_email'], to_email, msg.as_string())
            
            return DeliveryResult(
                request_id=f"email_{datetime.now().timestamp()}",
                status=DeliveryStatus.SENT,
                message="邮件发送成功",
                delivered_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}")
            return DeliveryResult(
                request_id=f"email_{datetime.now().timestamp()}",
                status=DeliveryStatus.FAILED,
                message=f"邮件发送失败: {str(e)}"
            )


class SMSService:
    """短信发送服务"""
    
    def __init__(self, config_service: ConfigService):
        self.config_service = config_service
    
    async def send_sms(
        self,
        phone_number: str,
        content: str,
        template_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> DeliveryResult:
        """发送短信"""
        try:
            # 获取短信配置
            sms_config = await self.config_service.get_config("third_party_apis", "sms")
            if not sms_config:
                raise Exception("短信服务未配置")
            
            # 构建请求参数
            data = {
                "PhoneNumbers": phone_number,
                "SignName": sms_config.get('sign_name', 'Lawsker'),
                "TemplateCode": template_id or sms_config.get('default_template'),
                "TemplateParam": params or {}
            }
            
            # 如果没有模板ID，使用通用内容发送
            if not template_id:
                data["Content"] = content
            
            # 调用短信API（这里使用阿里云短信API示例）
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    sms_config['api_url'],
                    json=data,
                    headers={
                        'Authorization': f"Bearer {sms_config['access_token']}",
                        'Content-Type': 'application/json'
                    }
                )
            
            result = response.json()
            
            if result.get('Code') == 'OK':
                return DeliveryResult(
                    request_id=f"sms_{datetime.now().timestamp()}",
                    status=DeliveryStatus.SENT,
                    message="短信发送成功",
                    external_id=result.get('BizId'),
                    delivered_at=datetime.now(),
                    cost=sms_config.get('cost_per_message', 0.05)
                )
            else:
                return DeliveryResult(
                    request_id=f"sms_{datetime.now().timestamp()}",
                    status=DeliveryStatus.FAILED,
                    message=f"短信发送失败: {result.get('Message', '未知错误')}"
                )
                
        except Exception as e:
            logger.error(f"短信发送失败: {str(e)}")
            return DeliveryResult(
                request_id=f"sms_{datetime.now().timestamp()}",
                status=DeliveryStatus.FAILED,
                message=f"短信发送失败: {str(e)}"
            )


class ExpressService:
    """快递发送服务"""
    
    def __init__(self, config_service: ConfigService):
        self.config_service = config_service
    
    async def send_express(
        self,
        recipient_address: Dict[str, str],
        content_description: str,
        sender_address: Optional[Dict[str, str]] = None,
        express_company: str = "SF",  # 顺丰
        urgent: bool = False
    ) -> DeliveryResult:
        """发送快递"""
        try:
            # 获取快递配置
            express_config = await self.config_service.get_config("third_party_apis", "express")
            if not express_config:
                raise Exception("快递服务未配置")
            
            # 使用默认发件地址
            if not sender_address:
                sender_address = express_config.get('default_sender_address', {})
            
            # 构建快递订单数据
            order_data = {
                "orderId": f"LW_EXPRESS_{int(datetime.now().timestamp())}",
                "expressType": 1 if urgent else 0,  # 0=标准快递, 1=加急
                "payMethod": 1,  # 1=寄方付
                "expCode": express_company,
                "sender": {
                    "name": sender_address.get('name', '律思客'),
                    "tel": sender_address.get('phone', ''),
                    "mobile": sender_address.get('mobile', ''),
                    "province": sender_address.get('province', ''),
                    "city": sender_address.get('city', ''),
                    "area": sender_address.get('area', ''),
                    "address": sender_address.get('detail_address', '')
                },
                "receiver": {
                    "name": recipient_address.get('name', ''),
                    "tel": recipient_address.get('phone', ''),
                    "mobile": recipient_address.get('mobile', ''),
                    "province": recipient_address.get('province', ''),
                    "city": recipient_address.get('city', ''),
                    "area": recipient_address.get('area', ''),
                    "address": recipient_address.get('detail_address', '')
                },
                "cargo": content_description,
                "weight": 0.1,  # 默认重量0.1kg
                "remark": "法律文书快递"
            }
            
            # 调用快递API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    express_config['api_url'],
                    json=order_data,
                    headers={
                        'Authorization': f"Bearer {express_config['access_token']}",
                        'Content-Type': 'application/json'
                    }
                )
            
            result = response.json()
            
            if result.get('success'):
                return DeliveryResult(
                    request_id=f"express_{datetime.now().timestamp()}",
                    status=DeliveryStatus.PROCESSING,
                    message="快递订单创建成功",
                    external_id=result.get('data', {}).get('kuaidiNo'),
                    cost=result.get('data', {}).get('fee', 15.0)
                )
            else:
                return DeliveryResult(
                    request_id=f"express_{datetime.now().timestamp()}",
                    status=DeliveryStatus.FAILED,
                    message=f"快递订单创建失败: {result.get('reason', '未知错误')}"
                )
                
        except Exception as e:
            logger.error(f"快递发送失败: {str(e)}")
            return DeliveryResult(
                request_id=f"express_{datetime.now().timestamp()}",
                status=DeliveryStatus.FAILED,
                message=f"快递发送失败: {str(e)}"
            )


class WeChatService:
    """微信发送服务"""
    
    def __init__(self, config_service: ConfigService):
        self.config_service = config_service
    
    async def send_wechat_message(
        self,
        openid: str,
        template_id: str,
        data: Dict[str, Any],
        url: Optional[str] = None
    ) -> DeliveryResult:
        """发送微信模板消息"""
        try:
            # 获取微信配置
            wechat_config = await self.config_service.get_config("third_party_apis", "wechat")
            if not wechat_config:
                raise Exception("微信服务未配置")
            
            # 获取Access Token
            access_token = await self._get_access_token(wechat_config)
            
            # 构建模板消息数据
            message_data = {
                "touser": openid,
                "template_id": template_id,
                "url": url or "",
                "data": data
            }
            
            # 发送模板消息
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}",
                    json=message_data
                )
            
            result = response.json()
            
            if result.get('errcode') == 0:
                return DeliveryResult(
                    request_id=f"wechat_{datetime.now().timestamp()}",
                    status=DeliveryStatus.SENT,
                    message="微信消息发送成功",
                    external_id=result.get('msgid'),
                    delivered_at=datetime.now()
                )
            else:
                return DeliveryResult(
                    request_id=f"wechat_{datetime.now().timestamp()}",
                    status=DeliveryStatus.FAILED,
                    message=f"微信消息发送失败: {result.get('errmsg', '未知错误')}"
                )
                
        except Exception as e:
            logger.error(f"微信消息发送失败: {str(e)}")
            return DeliveryResult(
                request_id=f"wechat_{datetime.now().timestamp()}",
                status=DeliveryStatus.FAILED,
                message=f"微信消息发送失败: {str(e)}"
            )
    
    async def _get_access_token(self, wechat_config: Dict[str, Any]) -> str:
        """获取微信Access Token"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.weixin.qq.com/cgi-bin/token",
                params={
                    "grant_type": "client_credential",
                    "appid": wechat_config['app_id'],
                    "secret": wechat_config['app_secret']
                }
            )
        
        result = response.json()
        if 'access_token' in result:
            return result['access_token']
        else:
            raise Exception(f"获取Access Token失败: {result.get('errmsg', '未知错误')}")


class MultiChannelDeliveryService:
    """多渠道发送服务主类"""
    
    def __init__(self, config_service: ConfigService):
        self.config_service = config_service
        self.email_service = EmailService(config_service)
        self.sms_service = SMSService(config_service)
        self.express_service = ExpressService(config_service)
        self.wechat_service = WeChatService(config_service)
        
        # 发送队列
        self.delivery_queue: List[DeliveryRequest] = []
        self.processing = False
    
    async def send_document(
        self,
        channel: DeliveryChannel,
        recipient: str,
        document_content: str,
        document_name: str = "法律文书",
        attachments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        priority: int = 0
    ) -> DeliveryResult:
        """发送法律文书"""
        
        request = DeliveryRequest(
            channel=channel,
            recipient=recipient,
            content=document_content,
            subject=f"【律思客】{document_name}",
            attachments=attachments,
            metadata=metadata,
            priority=priority
        )
        
        return await self._process_delivery_request(request)
    
    async def send_notification(
        self,
        channel: DeliveryChannel,
        recipient: str,
        title: str,
        content: str,
        template_id: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None
    ) -> DeliveryResult:
        """发送通知消息"""
        
        request = DeliveryRequest(
            channel=channel,
            recipient=recipient,
            content=content,
            subject=title,
            metadata={
                "template_id": template_id,
                "template_data": template_data
            }
        )
        
        return await self._process_delivery_request(request)
    
    async def _process_delivery_request(self, request: DeliveryRequest) -> DeliveryResult:
        """处理发送请求"""
        try:
            if request.channel == DeliveryChannel.EMAIL:
                return await self.email_service.send_email(
                    to_email=request.recipient,
                    subject=request.subject or "通知",
                    content=request.content,
                    attachments=request.attachments
                )
            
            elif request.channel == DeliveryChannel.SMS:
                template_id = request.metadata.get('template_id') if request.metadata else None
                template_data = request.metadata.get('template_data') if request.metadata else None
                
                return await self.sms_service.send_sms(
                    phone_number=request.recipient,
                    content=request.content,
                    template_id=template_id,
                    params=template_data
                )
            
            elif request.channel == DeliveryChannel.EXPRESS:
                # 假设recipient是JSON格式的地址信息
                import json
                try:
                    address = json.loads(request.recipient)
                except:
                    address = {"name": "收件人", "detail_address": request.recipient}
                
                return await self.express_service.send_express(
                    recipient_address=address,
                    content_description=request.subject or "法律文书",
                    urgent=request.priority > 5
                )
            
            elif request.channel == DeliveryChannel.WECHAT:
                template_id = request.metadata.get('template_id') if request.metadata else None
                template_data = request.metadata.get('template_data') if request.metadata else {}
                
                if not template_id:
                    raise Exception("微信发送需要template_id")
                
                return await self.wechat_service.send_wechat_message(
                    openid=request.recipient,
                    template_id=template_id,
                    data=template_data,
                    url=request.metadata.get('url') if request.metadata else None
                )
            
            else:
                return DeliveryResult(
                    request_id=f"unknown_{datetime.now().timestamp()}",
                    status=DeliveryStatus.FAILED,
                    message=f"不支持的发送渠道: {request.channel}"
                )
                
        except Exception as e:
            logger.error(f"发送请求处理失败: {str(e)}")
            return DeliveryResult(
                request_id=f"error_{datetime.now().timestamp()}",
                status=DeliveryStatus.FAILED,
                message=f"发送失败: {str(e)}"
            )
    
    async def batch_send(
        self,
        requests: List[DeliveryRequest]
    ) -> List[DeliveryResult]:
        """批量发送"""
        results = []
        
        # 按优先级排序
        sorted_requests = sorted(requests, key=lambda x: x.priority, reverse=True)
        
        # 并发发送（限制并发数）
        semaphore = asyncio.Semaphore(5)  # 最多5个并发
        
        async def send_with_semaphore(request: DeliveryRequest) -> DeliveryResult:
            async with semaphore:
                return await self._process_delivery_request(request)
        
        tasks = [send_with_semaphore(req) for req in sorted_requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(DeliveryResult(
                    request_id=f"batch_error_{i}",
                    status=DeliveryStatus.FAILED,
                    message=f"批量发送异常: {str(result)}"
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def get_delivery_status(self, external_id: str, channel: DeliveryChannel) -> DeliveryStatus:
        """查询发送状态"""
        try:
            if channel == DeliveryChannel.EXPRESS:
                # 查询快递状态
                express_config = await self.config_service.get_config("third_party_apis", "express")
                if express_config:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            f"{express_config['track_url']}/{external_id}",
                            headers={'Authorization': f"Bearer {express_config['access_token']}"}
                        )
                    
                    result = response.json()
                    if result.get('delivered'):
                        return DeliveryStatus.DELIVERED
                    elif result.get('in_transit'):
                        return DeliveryStatus.PROCESSING
                    else:
                        return DeliveryStatus.SENT
            
            # 其他渠道的状态查询...
            return DeliveryStatus.SENT
            
        except Exception as e:
            logger.error(f"查询发送状态失败: {str(e)}")
            return DeliveryStatus.FAILED


# 创建服务实例
def create_delivery_service(config_service: ConfigService) -> MultiChannelDeliveryService:
    """创建多渠道发送服务实例"""
    return MultiChannelDeliveryService(config_service) 