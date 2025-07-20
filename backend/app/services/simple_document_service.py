"""
简化文书生成服务
避免数据库依赖，直接生成催收律师函
"""

import json
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SimpleDocumentService:
    """简化文书生成服务"""
    
    def __init__(self):
        pass
    
    async def generate_lawyer_letter(
        self,
        task_info: Dict[str, Any],
        lawyer_info: Dict[str, Any],
        law_firm_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成催收律师函
        
        Args:
            task_info: 任务信息（包含欠款人信息）
            lawyer_info: 律师信息
            law_firm_info: 律所信息
            
        Returns:
            生成的文书内容
        """
        try:
            # 从任务信息中提取债务人信息
            debtor_name = task_info.get('title', '').split('债务催收案')[0] if '债务催收案' in task_info.get('title', '') else '债务人'
            case_amount = 0
            
            # 从描述中提取金额
            description = task_info.get('description', '')
            if '案件金额：¥' in description:
                try:
                    amount_str = description.split('案件金额：¥')[1].split('\n')[0].replace(',', '')
                    case_amount = float(amount_str)
                except:
                    case_amount = task_info.get('budget', 0)
            
            # 从描述中提取联系方式和地址
            debtor_phone = '待核实'
            debtor_address = '待核实'
            
            if '联系方式：' in description:
                try:
                    debtor_phone = description.split('联系方式：')[1].split('\n')[0]
                except:
                    pass
                    
            if '地址：' in description:
                try:
                    debtor_address = description.split('地址：')[1].split('\n')[0]
                except:
                    pass
            
            # 生成文书标题
            title = f"致{debtor_name}催收律师函"
            
            # 生成文书内容
            content = f"""
{title}

{debtor_name}先生/女士：

我是{law_firm_info.get('name', 'XX律师事务所')}{lawyer_info.get('name', 'XX律师')}律师，执业证号：{lawyer_info.get('license_number', 'XXXXXXXXX')}，联系电话：{lawyer_info.get('phone', 'XXX-XXXX-XXXX')}。

现受委托人委托，就您所欠债务事宜向您发出本催收函。

据委托人提供的相关材料显示，您与委托人之间存在债权债务关系，债务金额为人民币{case_amount:,.2f}元。该债务已到期，但您至今未履行还款义务。

根据《中华人民共和国民法典》相关规定，债务人应当按照约定履行债务。现正式要求您：

一、自收到本函之日起十五日内，向委托人归还全部欠款人民币{case_amount:,.2f}元。

二、如您对上述债务有异议，请在收到本函后十五日内提供相关证据材料。

三、如您在上述期限内既不还款又不提出异议，我方将依法通过诉讼途径解决，由此产生的诉讼费、律师费等费用将由您承担。

请您重视本催收函，及时履行还款义务，避免诉讼风险。

联系地址：{law_firm_info.get('address', 'XX市XX区XX路XX号')}
联系电话：{lawyer_info.get('phone', 'XXX-XXXX-XXXX')}
邮政编码：{law_firm_info.get('postal_code', 'XXXXXX')}

此致
敬礼！

{law_firm_info.get('name', 'XX律师事务所')}
{lawyer_info.get('name', 'XX律师')}

{datetime.now().strftime('%Y年%m月%d日')}
""".strip()

            return {
                'title': title,
                'content': content,
                'quality_score': 95,
                'generation_method': 'template',
                'document_type': 'lawyer_letter',
                'success': True
            }
            
        except Exception as e:
            logger.error(f"生成律师函失败: {str(e)}")
            return {
                'title': '催收律师函',
                'content': '生成失败，请稍后重试。',
                'quality_score': 0,
                'generation_method': 'error',
                'success': False,
                'error': str(e)
            }
    
    def get_default_lawyer_info(self) -> Dict[str, Any]:
        """获取默认律师信息"""
        return {
            'name': '张律师',
            'license_number': '11010201234567890',
            'phone': '138-0000-0000',
            'email': 'lawyer@lawfirm.com'
        }
    
    def get_default_law_firm_info(self) -> Dict[str, Any]:
        """获取默认律所信息"""
        return {
            'name': '北京XX律师事务所',
            'address': '北京市朝阳区建国路XX号XX大厦XX层',
            'postal_code': '100000',
            'phone': '010-8888-8888',
            'fax': '010-8888-8889'
        }