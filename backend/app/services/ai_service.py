"""
AI文书生成服务
集成ChatGPT和Deepseek双引擎，从统一配置管理系统获取API配置
"""

import asyncio
import json
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
import aiohttp
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.config_service import SystemConfigService
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """AI服务异常"""
    pass


class AIDocumentService:
    """AI文书生成服务"""
    
    def __init__(self, db: AsyncSession, tenant_id: Optional[UUID] = None):
        self.db = db
        self.tenant_id = tenant_id
        self.config_service = SystemConfigService(db)
        
        # 文档类型模板映射
        self.document_templates = {
            "collection_letter": {
                "name": "催收律师函",
                "tone_options": ["friendly_reminder", "formal_notice", "stern_warning"],
                "required_fields": ["debtor_name", "debt_amount", "due_date", "creditor_name"]
            },
            "demand_letter": {
                "name": "催告函", 
                "tone_options": ["formal", "urgent"],
                "required_fields": ["debtor_name", "debt_amount", "deadline"]
            },
            "warning_letter": {
                "name": "警告函",
                "tone_options": ["moderate", "stern"],
                "required_fields": ["target_name", "violation_description", "legal_basis"]
            },
            "cease_desist": {
                "name": "停止侵权函",
                "tone_options": ["formal", "stern"],
                "required_fields": ["infringing_party", "infringement_description", "rights_holder"]
            },
            "breach_notice": {
                "name": "违约通知函",
                "tone_options": ["formal", "urgent"],
                "required_fields": ["breaching_party", "contract_details", "breach_description"]
            }
        }
    
    async def get_ai_config(self, provider: str) -> Optional[Dict[str, Any]]:
        """从配置管理系统获取AI配置"""
        try:
            config = await self.config_service.get_config(
                category="ai_api_keys",
                key=provider,
                tenant_id=self.tenant_id,
                decrypt_sensitive=True
            )
            
            if not config or not config.get("api_key"):
                logger.warning(f"未找到 {provider} 的有效配置")
                return None
            
            return config
        except Exception as e:
            logger.error(f"获取AI配置失败 - provider: {provider}, error: {str(e)}")
            return None
    
    async def generate_document_with_chatgpt(
        self,
        document_type: str,
        case_info: Dict[str, Any],
        tone: str = "formal",
        additional_requirements: str = ""
    ) -> Optional[Dict[str, Any]]:
        """使用ChatGPT生成文书"""
        try:
            # 获取OpenAI配置
            config = await self.get_ai_config("openai")
            if not config:
                raise AIServiceError("OpenAI配置未设置或无效")
            
            # 构建提示词
            prompt = self._build_prompt(document_type, case_info, tone, additional_requirements)
            
            # 调用OpenAI API
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {config['api_key']}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": config.get("model", "gpt-4"),
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一位资深律师，专精于起草各类法律文书。请根据提供的信息，生成专业、准确、符合法律要求的法律文书。"
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
                
                timeout = aiohttp.ClientTimeout(total=config.get("timeout", 60))
                
                async with session.post(
                    f"{config.get('base_url', 'https://api.openai.com/v1')}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=timeout
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenAI API错误: {response.status} - {error_text}")
                        raise AIServiceError(f"OpenAI API调用失败: {response.status}")
                    
                    result = await response.json()
                    
                    if "choices" not in result or not result["choices"]:
                        raise AIServiceError("OpenAI返回结果格式错误")
                    
                    content = result["choices"][0]["message"]["content"]
                    
                    return {
                        "success": True,
                        "content": content,
                        "engine": "chatgpt",
                        "model": config.get("model", "gpt-4"),
                        "usage": result.get("usage", {}),
                        "generated_at": datetime.utcnow().isoformat()
                    }
                    
        except asyncio.TimeoutError:
            logger.error("OpenAI API调用超时")
            raise AIServiceError("AI服务调用超时")
        except Exception as e:
            logger.error(f"ChatGPT文书生成失败: {str(e)}")
            raise AIServiceError(f"文书生成失败: {str(e)}")
    
    async def optimize_with_deepseek(
        self,
        original_content: str,
        document_type: str,
        optimization_requirements: str = ""
    ) -> Optional[Dict[str, Any]]:
        """使用Deepseek优化文书内容"""
        try:
            # 获取Deepseek配置
            config = await self.get_ai_config("deepseek")
            if not config or not config.get("api_key"):
                logger.warning("Deepseek配置未设置，跳过优化步骤")
                return {
                    "success": True,
                    "content": original_content,
                    "engine": "none",
                    "optimized": False
                }
            
            # 构建优化提示词
            optimize_prompt = f"""
请对以下{self.document_templates.get(document_type, {}).get('name', '法律文书')}进行优化：

原始内容：
{original_content}

优化要求：
1. 确保法律用词准确、专业
2. 逻辑结构清晰，条理分明
3. 语言简洁有力，避免冗余
4. {optimization_requirements}

请直接返回优化后的完整文书内容，不要添加额外说明。
"""
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {config['api_key']}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": config.get("model", "deepseek-chat"),
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一位经验丰富的法律文书专家，擅长优化和完善各类法律文书的表达。"
                        },
                        {
                            "role": "user",
                            "content": optimize_prompt
                        }
                    ],
                    "temperature": 0.2,
                    "max_tokens": 2500
                }
                
                timeout = aiohttp.ClientTimeout(total=config.get("timeout", 60))
                
                async with session.post(
                    f"{config.get('base_url', 'https://api.deepseek.com/v1')}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=timeout
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.warning(f"Deepseek API错误，使用原始内容: {response.status} - {error_text}")
                        return {
                            "success": True,
                            "content": original_content,
                            "engine": "fallback",
                            "optimized": False
                        }
                    
                    result = await response.json()
                    
                    if "choices" not in result or not result["choices"]:
                        logger.warning("Deepseek返回结果格式错误，使用原始内容")
                        return {
                            "success": True,
                            "content": original_content,
                            "engine": "fallback",
                            "optimized": False
                        }
                    
                    optimized_content = result["choices"][0]["message"]["content"]
                    
                    return {
                        "success": True,
                        "content": optimized_content,
                        "engine": "deepseek",
                        "model": config.get("model", "deepseek-chat"),
                        "usage": result.get("usage", {}),
                        "optimized": True,
                        "optimized_at": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            logger.warning(f"Deepseek优化失败，使用原始内容: {str(e)}")
            return {
                "success": True,
                "content": original_content,
                "engine": "fallback",
                "optimized": False,
                "error": str(e)
            }
    
    async def generate_document(
        self,
        document_type: str,
        case_info: Dict[str, Any],
        tone: str = "formal",
        additional_requirements: str = "",
        use_optimization: bool = True
    ) -> Dict[str, Any]:
        """生成法律文书（双引擎）"""
        try:
            # 验证文档类型
            if document_type not in self.document_templates:
                raise AIServiceError(f"不支持的文档类型: {document_type}")
            
            # 验证必需字段
            template = self.document_templates[document_type]
            missing_fields = []
            for field in template["required_fields"]:
                if field not in case_info or not case_info[field]:
                    missing_fields.append(field)
            
            if missing_fields:
                raise AIServiceError(f"缺少必需字段: {', '.join(missing_fields)}")
            
            # 第一步：使用ChatGPT生成初稿
            logger.info(f"开始生成{template['name']} - 使用ChatGPT引擎")
            chatgpt_result = await self.generate_document_with_chatgpt(
                document_type, case_info, tone, additional_requirements
            )
            
            if not chatgpt_result or not chatgpt_result.get("success"):
                raise AIServiceError("ChatGPT文书生成失败")
            
            initial_content = chatgpt_result["content"]
            
            # 第二步：使用Deepseek优化（如果启用）
            final_content = initial_content
            optimization_result = None
            
            if use_optimization:
                logger.info("使用Deepseek引擎优化文书内容")
                optimization_result = await self.optimize_with_deepseek(
                    initial_content, document_type, additional_requirements
                )
                
                if optimization_result and optimization_result.get("success"):
                    final_content = optimization_result["content"]
            
            # 返回完整结果
            return {
                "success": True,
                "document_type": document_type,
                "document_name": template["name"],
                "content": final_content,
                "generation_info": {
                    "chatgpt_result": chatgpt_result,
                    "optimization_result": optimization_result,
                    "use_optimization": use_optimization,
                    "tone": tone,
                    "generated_at": datetime.utcnow().isoformat()
                },
                "case_info": case_info
            }
            
        except AIServiceError:
            raise
        except Exception as e:
            logger.error(f"文书生成失败: {str(e)}")
            raise AIServiceError(f"文书生成服务异常: {str(e)}")
    
    def _build_prompt(
        self,
        document_type: str,
        case_info: Dict[str, Any],
        tone: str,
        additional_requirements: str
    ) -> str:
        """构建AI提示词"""
        template = self.document_templates[document_type]
        
        # 基础提示词模板
        base_prompts = {
            "collection_letter": self._get_collection_letter_prompt,
            "demand_letter": self._get_demand_letter_prompt,
            "warning_letter": self._get_warning_letter_prompt,
            "cease_desist": self._get_cease_desist_prompt,
            "breach_notice": self._get_breach_notice_prompt
        }
        
        prompt_builder = base_prompts.get(document_type, self._get_generic_prompt)
        return prompt_builder(case_info, tone, additional_requirements)
    
    def _get_collection_letter_prompt(self, case_info: Dict[str, Any], tone: str, additional_requirements: str) -> str:
        """催收律师函提示词"""
        tone_mapping = {
            "friendly_reminder": "友好提醒",
            "formal_notice": "正式通知", 
            "stern_warning": "严厉警告"
        }
        
        tone_desc = tone_mapping.get(tone, "正式通知")
        
        return f"""
请根据以下信息生成一份{tone_desc}语气的催收律师函：

债务人信息：
- 姓名：{case_info.get('debtor_name', '')}
- 身份证号：{case_info.get('debtor_id', '***')}
- 联系地址：{case_info.get('debtor_address', '')}

债权信息：
- 债权人：{case_info.get('creditor_name', '')}
- 债务金额：{case_info.get('debt_amount', '')}元
- 债务形成日期：{case_info.get('debt_date', '')}
- 约定还款日期：{case_info.get('due_date', '')}
- 逾期天数：{case_info.get('overdue_days', '')}天

案件详情：
{case_info.get('case_description', '')}

特殊要求：
{additional_requirements}

请生成格式规范、内容完整的律师函，包含：
1. 函件抬头和编号
2. 债务事实陈述
3. 法律依据
4. 催收要求和期限
5. 法律后果提醒
6. 律师署名
"""
    
    def _get_demand_letter_prompt(self, case_info: Dict[str, Any], tone: str, additional_requirements: str) -> str:
        """催告函提示词"""
        return f"""
请生成一份催告函，要求{tone}语气：

基本信息：
- 被催告方：{case_info.get('debtor_name', '')}
- 债务金额：{case_info.get('debt_amount', '')}元
- 催告期限：{case_info.get('deadline', '')}

详细说明：
{case_info.get('description', '')}

附加要求：
{additional_requirements}

请确保包含催告的法律效力说明和后果提醒。
"""
    
    def _get_warning_letter_prompt(self, case_info: Dict[str, Any], tone: str, additional_requirements: str) -> str:
        """警告函提示词"""
        return f"""
请生成一份{tone}语气的警告函：

目标对象：{case_info.get('target_name', '')}
违法行为描述：{case_info.get('violation_description', '')}
法律依据：{case_info.get('legal_basis', '')}
要求停止的行为：{case_info.get('stop_behavior', '')}

附加要求：
{additional_requirements}

请明确指出违法行为、法律后果和整改要求。
"""
    
    def _get_cease_desist_prompt(self, case_info: Dict[str, Any], tone: str, additional_requirements: str) -> str:
        """停止侵权函提示词"""
        return f"""
请生成一份停止侵权函：

侵权方：{case_info.get('infringing_party', '')}
权利人：{case_info.get('rights_holder', '')}
侵权行为描述：{case_info.get('infringement_description', '')}
被侵犯的权利：{case_info.get('violated_rights', '')}

附加要求：
{additional_requirements}

请明确要求停止侵权行为，并说明法律后果。
"""
    
    def _get_breach_notice_prompt(self, case_info: Dict[str, Any], tone: str, additional_requirements: str) -> str:
        """违约通知函提示词"""
        return f"""
请生成一份违约通知函：

违约方：{case_info.get('breaching_party', '')}
合同信息：{case_info.get('contract_details', '')}
违约行为：{case_info.get('breach_description', '')}
违约时间：{case_info.get('breach_date', '')}

附加要求：
{additional_requirements}

请明确说明违约事实、合同条款和法律后果。
"""
    
    def _get_generic_prompt(self, case_info: Dict[str, Any], tone: str, additional_requirements: str) -> str:
        """通用提示词"""
        return f"""
请根据以下信息生成法律文书：

案件信息：
{json.dumps(case_info, ensure_ascii=False, indent=2)}

语气要求：{tone}
附加要求：{additional_requirements}

请生成格式规范、内容完整的法律文书。
"""
    
    async def regenerate_document(
        self,
        original_content: str,
        modification_requests: str,
        document_type: str
    ) -> Dict[str, Any]:
        """重新生成文书（基于修改要求）"""
        try:
            # 获取OpenAI配置
            config = await self.get_ai_config("openai")
            if not config:
                raise AIServiceError("OpenAI配置未设置或无效")
            
            regenerate_prompt = f"""
请根据以下修改要求，重新生成法律文书：

原始文书内容：
{original_content}

修改要求：
{modification_requests}

请生成符合修改要求的完整法律文书，保持原有的结构和格式。
"""
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {config['api_key']}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": config.get("model", "gpt-4"),
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一位专业律师，擅长根据客户要求修改和完善法律文书。"
                        },
                        {
                            "role": "user",
                            "content": regenerate_prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
                
                timeout = aiohttp.ClientTimeout(total=config.get("timeout", 60))
                
                async with session.post(
                    f"{config.get('base_url', 'https://api.openai.com/v1')}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=timeout
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"文书重新生成失败: {response.status} - {error_text}")
                        raise AIServiceError(f"重新生成失败: {response.status}")
                    
                    result = await response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    return {
                        "success": True,
                        "content": content,
                        "engine": "chatgpt",
                        "regenerated": True,
                        "modification_requests": modification_requests,
                        "regenerated_at": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"文书重新生成失败: {str(e)}")
            raise AIServiceError(f"重新生成失败: {str(e)}")
    
    def get_supported_document_types(self) -> List[Dict[str, Any]]:
        """获取支持的文档类型列表"""
        return [
            {
                "type": doc_type,
                "name": template["name"],
                "tone_options": template["tone_options"],
                "required_fields": template["required_fields"]
            }
            for doc_type, template in self.document_templates.items()
        ] 