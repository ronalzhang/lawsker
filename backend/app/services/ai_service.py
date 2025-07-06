"""
AI文书生成服务
集成ChatGPT和Deepseek双引擎，从统一配置管理系统获取API配置
"""

import asyncio
import json
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum
import aiohttp
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.config_service import SystemConfigService
from app.core.config import settings

logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    """文档类型枚举"""
    COLLECTION_LETTER = "collection_letter"
    DEMAND_LETTER = "demand_letter" 
    WARNING_LETTER = "warning_letter"
    CEASE_DESIST = "cease_desist"
    BREACH_NOTICE = "breach_notice"


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
    
    def _generate_installment_plan(self, debt_amount: float) -> str:
        """根据债务金额生成智能分期方案"""
        if debt_amount <= 0:
            return "- 请联系我方协商具体还款方案"
        
        plans = []
        
        # 3期方案
        period_3 = debt_amount / 3
        plans.append(f"- 3期方案：每期还款 {period_3:.2f}元")
        
        # 6期方案
        period_6 = debt_amount / 6
        plans.append(f"- 6期方案：每期还款 {period_6:.2f}元")
        
        # 9期方案
        period_9 = debt_amount / 9
        plans.append(f"- 9期方案：每期还款 {period_9:.2f}元")
        
        # 12期方案（仅当金额较大时）
        if debt_amount >= 10000:
            period_12 = debt_amount / 12
            plans.append(f"- 12期方案：每期还款 {period_12:.2f}元")
        
        # 特殊大额方案（超过50万）
        if debt_amount >= 500000:
            period_18 = debt_amount / 18
            plans.append(f"- 18期方案（特殊）：每期还款 {period_18:.2f}元")
        
        return "\n   ".join(plans)

    def _get_legal_basis_by_type(self, debt_type: str, amount: float) -> str:
        """根据债务类型和金额获取法律依据"""
        legal_basis = {
            "loan": "《民法典》第六百七十一条（借款合同）、第六百七十六条（还款义务）",
            "contract": "《民法典》第五百七十七条（违约责任）、第五百八十四条（损失赔偿）",
            "service": "《民法典》第五百零九条（合同履行）、第五百七十八条（预期违约）",
            "rent": "《民法典》第七百二十一条（租金支付）、第七百二十二条（逾期责任）",
            "default": "《民法典》第一百一十八条（债权保护）、第一百一十九条（债务履行）"
        }
        
        base_law = legal_basis.get(debt_type, legal_basis["default"])
        
        # 大额债务补充相关法条
        if amount >= 100000:
            base_law += "、《民事诉讼法》第二百三十六条（强制执行）"
        
        return base_law

    def _get_jurisdiction_info(self, debtor_location: Optional[str] = None) -> Dict[str, str]:
        """获取管辖法院信息"""
        if not debtor_location:
            return {
                "court": "有管辖权的人民法院",
                "procedure": "根据《民事诉讼法》相关规定"
            }
        
        # 简化的地域匹配逻辑
        location_mapping = {
            "北京": "北京市人民法院",
            "上海": "上海市人民法院", 
            "广州": "广州市人民法院",
            "深圳": "深圳市人民法院",
            "杭州": "杭州市人民法院",
            "南京": "南京市人民法院"
        }
        
        court = location_mapping.get(debtor_location, f"{debtor_location}人民法院")
        
        return {
            "court": court,
            "procedure": "根据《民事诉讼法》第二十一条（一般地域管辖）规定"
        }

    def _get_tone_prompt_enhancement(self, tone: str) -> Dict[str, str]:
        """获取语气增强提示"""
        tone_enhancements = {
            "friendly_reminder": {
                "style": "采用温和友善的语气，强调合作解决问题的态度",
                "phrases": "建议使用'希望'、'请您'、'我们理解'等词汇",
                "approach": "以协商和理解为主，避免过于强硬的表述"
            },
            "formal_notice": {
                "style": "使用正式严肃的法律语言，保持专业性和权威性",
                "phrases": "使用'特此通知'、'依法要求'、'法律责任'等正式用词",
                "approach": "条理清晰，逻辑严密，体现法律文书的严肃性"
            },
            "stern_warning": {
                "style": "采用严厉警告的语气，强调法律后果的严重性",
                "phrases": "使用'严正警告'、'立即停止'、'承担法律后果'等强硬用词",
                "approach": "明确指出违法性质，强调不合作的严重后果"
            }
        }
        
        return tone_enhancements.get(tone, tone_enhancements["formal_notice"])

    def _get_collection_letter_prompt(self, case_info: Dict[str, Any], tone: str, additional_requirements: str) -> str:
        """催收律师函提示词 - 专业优化版本"""
        tone_mapping = {
            "friendly_reminder": "友好提醒",
            "formal_notice": "正式通知", 
            "stern_warning": "严厉警告"
        }
        
        tone_desc = tone_mapping.get(tone, "正式通知")
        debt_amount = float(case_info.get('debt_amount', 0))
        
        # 根据债务金额智能推荐分期方案
        installment_plan = self._generate_installment_plan(debt_amount)
        
        # 获取法律依据
        debt_type = case_info.get('debt_type', 'default')
        legal_basis = self._get_legal_basis_by_type(debt_type, debt_amount)
        
        # 获取管辖信息
        jurisdiction = self._get_jurisdiction_info(case_info.get('debtor_location'))
        
        # 获取语气增强提示
        tone_enhancement = self._get_tone_prompt_enhancement(tone)
        
        return f"""
你是一位资深执业律师，专精债务催收和分期还款协商。请根据以下信息生成一份专业、有效、符合法律规范的催收律师函。

【案件基本信息】
债务人：{case_info.get('debtor_name', '')}
身份证号：{case_info.get('debtor_id', '***')}
联系地址：{case_info.get('debtor_address', '')}
债权人：{case_info.get('creditor_name', '')}
债务本金：{case_info.get('debt_amount', '')}元
债务形成日期：{case_info.get('debt_date', '')}
约定还款日期：{case_info.get('due_date', '')}
逾期天数：{case_info.get('overdue_days', '')}天

【语气要求】：{tone_desc}
【语气指导】：{tone_enhancement['style']}
【用词建议】：{tone_enhancement['phrases']}
【表达方式】：{tone_enhancement['approach']}

【法律依据】：{legal_basis}
【管辖法院】：{jurisdiction['court']}
【程序依据】：{jurisdiction['procedure']}

【核心要求】
1. 必须提供3-4种分期还款方案供债务人选择：
   {installment_plan}

2. 分期方案特点：
   - 优先推荐3期、6期、9期、12期方案
   - 一般不超过12个月，除非债务金额巨大（超过50万）
   - 每期金额要具体计算并明确标注
   - 首期可适当减少以降低还款压力

3. 法律威慑要素：
   - 引用《民法典》相关条款
   - 明确逾期的法律后果
   - 提及可能采取的法律措施（起诉、强制执行等）

4. 格式要求：
   - 函件编号：[年份]-[机构简称]-催字第[编号]号
   - 正式的律师函格式
   - 条理清晰，逻辑严密
   - 专业术语准确

5. 时间期限：
   - 给出明确的回复期限（通常7-15天）
   - 说明超期后果

【特殊要求】
{additional_requirements}

【案件详情】
{case_info.get('case_description', '')}

请生成完整的律师函内容，确保：
- 语言专业且有威慑力
- 分期方案实用且有吸引力
- 法律依据准确充分
- 格式规范标准
- 逻辑清晰易懂
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