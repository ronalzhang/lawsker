"""
SMS短信服务
支持验证码发送、通知短信等功能
"""

import random
import string
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from uuid import UUID

import httpx

# 可选依赖的导入
try:
    from aliyunsdkcore.client import AcsClient
    from aliyunsdkcore.request import CommonRequest
    ALIYUN_AVAILABLE = True
except ImportError:
    AcsClient = None
    CommonRequest = None
    ALIYUN_AVAILABLE = False

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TwilioClient = None
    TWILIO_AVAILABLE = False

from app.services.config_service import SystemConfigService
from app.core.cache import cache_service

logger = logging.getLogger(__name__)


class SMSError(Exception):
    """SMS发送异常"""
    pass


class SMSService:
    """SMS短信服务"""
    
    def __init__(self, config_service: SystemConfigService):
        self.config_service = config_service
        
    async def send_verification_code(
        self,
        phone_number: str,
        code_type: str = "task",
        expires_in: int = 300  # 5分钟
    ) -> Dict[str, Any]:
        """
        发送验证码
        
        Args:
            phone_number: 手机号
            code_type: 验证码类型 (task, login, register等)
            expires_in: 过期时间（秒）
            
        Returns:
            发送结果
        """
        try:
            # 生成验证码
            code = self._generate_verification_code()
            
            # 获取SMS配置
            sms_config = await self.config_service.get_config("third_party_apis", "sms_provider")
            if not sms_config or not sms_config.get("enabled"):
                # 如果SMS服务未配置，返回模拟成功（用于开发测试）
                logger.warning("SMS服务未配置，使用模拟发送")
                await self._store_verification_code(phone_number, code_type, code, expires_in)
                return {
                    "success": True,
                    "message": f"验证码发送成功（模拟）: {code}",  # 开发环境显示验证码
                    "code_length": len(code),
                    "expires_in": expires_in,
                    "dev_code": code  # 开发环境返回验证码
                }
            
            # 构建消息内容
            message = f"【律思客】您的验证码是{code}，{expires_in//60}分钟内有效。如非本人操作，请忽略此消息。"
            
            # 发送短信
            result = await self._send_sms(phone_number, message, sms_config)
            
            if result["success"]:
                # 将验证码存储到缓存
                await self._store_verification_code(phone_number, code_type, code, expires_in)
                
                return {
                    "success": True,
                    "message": "验证码发送成功",
                    "code_length": len(code),
                    "expires_in": expires_in
                }
            else:
                return {
                    "success": False,
                    "message": result.get("message", "发送失败"),
                    "error_code": result.get("error_code")
                }
                
        except Exception as e:
            logger.error(f"发送验证码失败: {str(e)}")
            raise SMSError(f"发送验证码失败: {str(e)}")
    
    async def _store_verification_code(
        self,
        phone_number: str,
        code_type: str,
        code: str,
        expires_in: int
    ):
        """存储验证码到缓存"""
        cache_key = f"sms_code:{code_type}:{phone_number}"
        
        cache_data = {
            "code": code,
            "phone": phone_number,
            "type": code_type,
            "created_at": datetime.now().isoformat()
        }
        
        await cache_service.setex(cache_key, expires_in, cache_data)
    
    async def verify_code(
        self,
        phone_number: str,
        code: str,
        code_type: str = "task",
        remove_after_verify: bool = True
    ) -> bool:
        """
        验证验证码
        
        Args:
            phone_number: 手机号
            code: 验证码
            code_type: 验证码类型
            remove_after_verify: 验证成功后是否删除验证码
            
        Returns:
            验证结果
        """
        try:
            cache_key = f"sms_code:{code_type}:{phone_number}"
            
            # 从缓存获取验证码数据
            cache_data = await cache_service.get(cache_key)
            
            if not cache_data:
                return False
            
            # 提取验证码
            if isinstance(cache_data, dict):
                stored_code = cache_data.get("code")
            else:
                # 兼容旧格式（直接存储验证码字符串）
                stored_code = cache_data
            
            if stored_code and str(stored_code) == str(code):
                if remove_after_verify:
                    # 删除验证码
                    await cache_service.delete(cache_key)
                
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"验证验证码失败: {str(e)}")
            return False
    
    async def send_notification(
        self,
        phone_number: str,
        message: str,
        template_code: Optional[str] = None,
        template_params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        发送通知短信
        
        Args:
            phone_number: 手机号
            message: 消息内容
            template_code: 模板代码
            template_params: 模板参数
            
        Returns:
            发送结果
        """
        try:
            # 获取SMS配置
            sms_config = await self.config_service.get_config("third_party_apis", "sms_provider")
            if not sms_config or not sms_config.get("enabled"):
                # 如果SMS服务未配置，返回模拟成功
                logger.warning(f"SMS服务未配置，模拟发送通知到 {phone_number}: {message}")
                return {
                    "success": True,
                    "message": "通知发送成功（模拟）",
                    "phone": phone_number,
                    "content": message
                }
            
            # 如果有模板，使用模板发送
            if template_code and template_params:
                result = await self._send_template_sms(
                    phone_number, 
                    template_code, 
                    template_params, 
                    sms_config
                )
            else:
                # 直接发送消息
                result = await self._send_sms(phone_number, message, sms_config)
            
            return result
            
        except Exception as e:
            logger.error(f"发送通知短信失败: {str(e)}")
            raise SMSError(f"发送通知短信失败: {str(e)}")
    
    async def _send_sms(
        self,
        phone_number: str,
        message: str,
        sms_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送短信（根据配置选择不同的服务提供商）
        """
        provider = sms_config.get("provider", "aliyun")
        
        if provider == "aliyun":
            if not ALIYUN_AVAILABLE:
                return {
                    "success": False,
                    "message": "阿里云SMS SDK未安装"
                }
            return await self._send_aliyun_sms(phone_number, message, sms_config)
        elif provider == "twilio":
            if not TWILIO_AVAILABLE:
                return {
                    "success": False,
                    "message": "Twilio SDK未安装"
                }
            return await self._send_twilio_sms(phone_number, message, sms_config)
        else:
            raise SMSError(f"不支持的SMS服务提供商: {provider}")
    
    async def _send_template_sms(
        self,
        phone_number: str,
        template_code: str,
        template_params: Dict[str, str],
        sms_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送模板短信
        """
        provider = sms_config.get("provider", "aliyun")
        
        if provider == "aliyun":
            if not ALIYUN_AVAILABLE:
                return {
                    "success": False,
                    "message": "阿里云SMS SDK未安装"
                }
            return await self._send_aliyun_template_sms(
                phone_number, 
                template_code, 
                template_params, 
                sms_config
            )
        elif provider == "twilio":
            # Twilio 不支持模板，直接发送消息
            message = self._format_template_message(template_code, template_params)
            if not TWILIO_AVAILABLE:
                return {
                    "success": False,
                    "message": "Twilio SDK未安装"
                }
            return await self._send_twilio_sms(phone_number, message, sms_config)
        else:
            raise SMSError(f"不支持的SMS服务提供商: {provider}")
    
    async def _send_aliyun_sms(
        self,
        phone_number: str,
        message: str,
        sms_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        使用阿里云发送短信
        """
        if not ALIYUN_AVAILABLE:
            return {
                "success": False,
                "message": "阿里云SMS SDK未安装"
            }
        
        try:
            # 初始化阿里云客户端
            client = AcsClient(
                sms_config["access_key"],
                sms_config["secret_key"],
                'cn-hangzhou'
            )
            
            # 构建请求
            request = CommonRequest()
            request.set_accept_format('json')
            request.set_domain('dysmsapi.aliyuncs.com')
            request.set_method('POST')
            request.set_protocol_type('https')
            request.set_version('2017-05-25')
            request.set_action_name('SendSms')
            
            # 设置参数
            request.add_query_param('RegionId', "cn-hangzhou")
            request.add_query_param('PhoneNumbers', phone_number)
            request.add_query_param('SignName', sms_config.get("sign_name", "律思客"))
            request.add_query_param('TemplateCode', sms_config.get("template_code", "SMS_123456"))
            request.add_query_param('TemplateParam', f'{{"content":"{message}"}}')
            
            # 发送请求
            response = client.do_action(request)
            result = response.decode('utf-8')
            
            import json
            result_dict = json.loads(result)
            
            if result_dict.get('Code') == 'OK':
                return {
                    "success": True,
                    "message": "短信发送成功",
                    "message_id": result_dict.get('BizId'),
                    "cost": sms_config.get("cost_per_message", 0.05)
                }
            else:
                return {
                    "success": False,
                    "message": result_dict.get('Message', '未知错误'),
                    "error_code": result_dict.get('Code')
                }
                
        except Exception as e:
            logger.error(f"阿里云短信发送失败: {str(e)}")
            return {
                "success": False,
                "message": f"阿里云短信发送失败: {str(e)}"
            }
    
    async def _send_aliyun_template_sms(
        self,
        phone_number: str,
        template_code: str,
        template_params: Dict[str, str],
        sms_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        使用阿里云发送模板短信
        """
        if not ALIYUN_AVAILABLE:
            return {
                "success": False,
                "message": "阿里云SMS SDK未安装"
            }
        
        try:
            # 初始化阿里云客户端
            client = AcsClient(
                sms_config["access_key"],
                sms_config["secret_key"],
                'cn-hangzhou'
            )
            
            # 构建请求
            request = CommonRequest()
            request.set_accept_format('json')
            request.set_domain('dysmsapi.aliyuncs.com')
            request.set_method('POST')
            request.set_protocol_type('https')
            request.set_version('2017-05-25')
            request.set_action_name('SendSms')
            
            # 设置参数
            request.add_query_param('RegionId', "cn-hangzhou")
            request.add_query_param('PhoneNumbers', phone_number)
            request.add_query_param('SignName', sms_config.get("sign_name", "律思客"))
            request.add_query_param('TemplateCode', template_code)
            
            # 构建模板参数
            import json
            template_param_str = json.dumps(template_params, ensure_ascii=False)
            request.add_query_param('TemplateParam', template_param_str)
            
            # 发送请求
            response = client.do_action(request)
            result = response.decode('utf-8')
            result_dict = json.loads(result)
            
            if result_dict.get('Code') == 'OK':
                return {
                    "success": True,
                    "message": "模板短信发送成功",
                    "message_id": result_dict.get('BizId'),
                    "cost": sms_config.get("cost_per_message", 0.05)
                }
            else:
                return {
                    "success": False,
                    "message": result_dict.get('Message', '未知错误'),
                    "error_code": result_dict.get('Code')
                }
                
        except Exception as e:
            logger.error(f"阿里云模板短信发送失败: {str(e)}")
            return {
                "success": False,
                "message": f"阿里云模板短信发送失败: {str(e)}"
            }
    
    async def _send_twilio_sms(
        self,
        phone_number: str,
        message: str,
        sms_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        使用Twilio发送短信
        """
        if not TWILIO_AVAILABLE:
            return {
                "success": False,
                "message": "Twilio SDK未安装"
            }
        
        try:
            # 初始化Twilio客户端
            client = TwilioClient(
                sms_config["account_sid"],
                sms_config["auth_token"]
            )
            
            # 发送短信
            message_obj = client.messages.create(
                body=message,
                from_=sms_config["from_number"],
                to=phone_number
            )
            
            return {
                "success": True,
                "message": "短信发送成功",
                "message_id": message_obj.sid,
                "cost": sms_config.get("cost_per_message", 0.10)
            }
            
        except Exception as e:
            logger.error(f"Twilio短信发送失败: {str(e)}")
            return {
                "success": False,
                "message": f"Twilio短信发送失败: {str(e)}"
            }
    
    def _generate_verification_code(self, length: int = 6) -> str:
        """
        生成验证码
        
        Args:
            length: 验证码长度
            
        Returns:
            验证码
        """
        return ''.join(random.choices(string.digits, k=length))
    
    def _format_template_message(
        self,
        template_code: str,
        template_params: Dict[str, str]
    ) -> str:
        """
        格式化模板消息（用于不支持模板的服务商）
        """
        # 这里可以根据template_code来格式化不同的消息
        if template_code == "verification":
            code = template_params.get("code", "")
            return f"【律思客】您的验证码是{code}，5分钟内有效。如非本人操作，请忽略此消息。"
        elif template_code == "task_update":
            task_number = template_params.get("task_number", "")
            status = template_params.get("status", "")
            return f"【律思客】您的任务{task_number}状态已更新为{status}。"
        elif template_code == "task_created":
            task_number = template_params.get("task_number", "")
            track_url = template_params.get("track_url", "")
            return f"【律思客】您的任务已提交成功，任务编号：{task_number}，我们将在24小时内处理。查询进度：{track_url}"
        else:
            # 默认格式
            return f"【律思客】{template_params.get('content', '通知消息')}"


# 创建服务实例
def create_sms_service(config_service: SystemConfigService) -> SMSService:
    """创建SMS服务实例"""
    return SMSService(config_service) 