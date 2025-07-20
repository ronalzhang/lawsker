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
        law_firm_info: Dict[str, Any],
        payment_accounts: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成催收律师函（包含分期还款方案和收款账号）
        
        Args:
            task_info: 任务信息（包含欠款人信息）
            lawyer_info: 律师信息
            law_firm_info: 律所信息
            payment_accounts: 平台收款账号信息
            
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
            
            # 获取默认收款账号信息
            if not payment_accounts:
                payment_accounts = self.get_default_payment_accounts()
            
            # 计算分期还款方案
            payment_plan = self.generate_payment_plan(case_amount)
            
            # 生成还款方式说明
            payment_methods = self.generate_payment_methods(payment_accounts)
            
            # 生成文书内容
            content = f"""
{title}

{debtor_name}先生/女士：

我是{law_firm_info.get('name', 'XX律师事务所')}{lawyer_info.get('name', 'XX律师')}律师，执业证号：{lawyer_info.get('license_number', 'XXXXXXXXX')}，联系电话：{lawyer_info.get('phone', 'XXX-XXXX-XXXX')}。

现受委托人委托，就您所欠债务事宜向您发出本催收函。

一、债务事实
据委托人提供的相关材料显示，您与委托人之间存在债权债务关系，债务金额为人民币{case_amount:,.2f}元。该债务已到期，但您至今未履行还款义务。

二、法律依据
根据《中华人民共和国民法典》第五百七十七条、第五百七十八条等相关规定，债务人应当按照约定履行债务。逾期不履行的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。

三、催收要求
现正式要求您在收到本函之日起十五日内履行还款义务。为便于您履行义务，现提供以下还款方案：

{payment_plan}

四、还款方式
{payment_methods}

五、法律后果
如您在上述期限内既不还款又不提出异议，将面临以下法律后果：
1. 承担违约责任及逾期利息损失；
2. 我方将依法通过诉讼途径解决，由此产生的诉讼费、律师费、保全费等费用均由您承担；
3. 可能被纳入失信被执行人名单，影响您的征信记录；
4. 面临财产保全和强制执行措施。

六、协商解决
如您确有还款意愿但暂时存在困难，请主动与我方联系，我们可以协商制定合理的还款计划。但请注意，协商不免除您的还款义务，也不影响我方采取法律措施的权利。

请您务必重视本催收函，积极配合解决债务问题，避免承担更严重的法律后果。

联系地址：{law_firm_info.get('address', 'XX市XX区XX路XX号')}
联系电话：{lawyer_info.get('phone', 'XXX-XXXX-XXXX')}
传真号码：{law_firm_info.get('fax', '010-XXXX-XXXX')}
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
    
    def get_default_payment_accounts(self) -> Dict[str, Any]:
        """获取默认平台收款账号信息"""
        return {
            'bank_account': {
                'account_name': '北京律思客科技有限公司',
                'account_number': '1234567890123456789',
                'bank_name': '中国工商银行北京分行',
                'bank_code': '102100000001'
            },
            'alipay': {
                'account': 'lawsker@company.com',
                'name': '北京律思客科技有限公司'
            },
            'wechat_pay': {
                'account': 'lawsker_official',
                'name': '律思客官方收款'
            }
        }
    
    def generate_payment_plan(self, amount: float) -> str:
        """生成分期还款方案"""
        if amount <= 0:
            return "请与我方联系确认具体债务金额。"
        
        # 根据金额大小制定不同的分期方案
        if amount <= 5000:
            return f"""
方案一：一次性还款
请于收函后15日内一次性归还全部欠款人民币{amount:,.2f}元。

方案二：分期还款（如确有困难）
首期支付50%（{amount * 0.5:,.2f}元），余款在30日内付清。"""
        
        elif amount <= 20000:
            return f"""
方案一：一次性还款
请于收函后15日内一次性归还全部欠款人民币{amount:,.2f}元。

方案二：分期还款
首期支付30%（{amount * 0.3:,.2f}元），后续分2期在60日内付清。
- 第二期：{amount * 0.35:,.2f}元（30日内）
- 第三期：{amount * 0.35:,.2f}元（60日内）"""
        
        else:
            return f"""
方案一：一次性还款
请于收函后15日内一次性归还全部欠款人民币{amount:,.2f}元。

方案二：分期还款
考虑到债务金额较大，可协商制定合理的分期还款计划：
- 首期支付不少于20%（{amount * 0.2:,.2f}元）
- 剩余款项可分3-6期，在6个月内付清
- 具体分期方案需与我方协商确定"""
    
    def generate_payment_methods(self, payment_accounts: Dict[str, Any]) -> str:
        """生成还款方式说明"""
        bank_info = payment_accounts.get('bank_account', {})
        alipay_info = payment_accounts.get('alipay', {})
        wechat_info = payment_accounts.get('wechat_pay', {})
        
        return f"""
为便于您履行还款义务，现提供以下还款方式：

1. 银行转账
   户名：{bank_info.get('account_name', '北京律思客科技有限公司')}
   账号：{bank_info.get('account_number', '请联系获取')}
   开户行：{bank_info.get('bank_name', '中国工商银行北京分行')}

2. 支付宝转账
   收款账号：{alipay_info.get('account', 'lawsker@company.com')}
   收款人：{alipay_info.get('name', '北京律思客科技有限公司')}

3. 微信转账
   收款账号：{wechat_info.get('account', 'lawsker_official')}
   收款人：{wechat_info.get('name', '律思客官方收款')}

注意事项：
- 转账时请务必在备注中注明债务人姓名和案件编号
- 转账完成后请立即将转账凭证发送至我方邮箱或微信
- 我方收到款项后将及时出具收款确认函"""