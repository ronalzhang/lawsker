"""
文书库服务
智能文书管理：优先使用库存，按需生成，学习优化
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, text
from sqlalchemy.orm import selectinload

from app.services.ai_service import AIDocumentService
from app.services.config_service import SystemConfigService
import logging

logger = logging.getLogger(__name__)


class DocumentLibraryService:
    """文书库服务"""
    
    def __init__(self, config_service: SystemConfigService = None, ai_service: AIDocumentService = None):
        self.config_service = config_service
        self.ai_service = ai_service
        
        # 文书类型映射
        self.document_types = {
            'lawyer_letter': '律师函',
            'debt_collection': '债务催收通知书', 
            'contract_review': '合同审查意见书',
            'legal_consultation': '法律咨询意见书',
            'general_legal': '通用法律文书'
        }
    
    async def get_or_generate_document(
        self, 
        db: AsyncSession,
        task_info: Dict[str, Any],
        user_id: UUID,
        case_id: Optional[UUID] = None,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        获取或生成文书内容
        
        Args:
            db: 数据库会话
            task_info: 任务信息
            user_id: 用户ID
            case_id: 案件ID（可选）
            force_regenerate: 是否强制重新生成
            
        Returns:
            包含文书内容和来源信息的字典
        """
        try:
            document_type = task_info.get('taskType', 'general_legal')
            
            # 如果不是强制重新生成，先查找已有文书
            if not force_regenerate:
                existing_doc = await self._find_matching_document(db, task_info, document_type)
                if existing_doc:
                    # 记录使用历史
                    await self._record_document_usage(
                        db, existing_doc['id'], user_id, case_id, 
                        task_info.get('taskId'), 'direct_use'
                    )
                    
                    return {
                        'success': True,
                        'source': 'library',
                        'document_id': existing_doc['id'],
                        'document_content': existing_doc['content'],
                        'document_title': existing_doc['title'],
                        'usage_count': existing_doc['usage_count'],
                        'success_rate': existing_doc['success_rate'],
                        'quality_score': existing_doc['ai_quality_score'],
                        'message': f'使用库存文书（已使用{existing_doc["usage_count"]}次，成功率{existing_doc["success_rate"]}%）'
                    }
            
            # 没有找到合适的文书或强制重新生成，创建新文书
            generated_content = await self._generate_new_document(task_info, document_type)
            
            # 保存到文书库
            document_id = await self._save_to_library(
                db, document_type, task_info, generated_content, user_id, case_id
            )
            
            # 记录使用历史
            await self._record_document_usage(
                db, document_id, user_id, case_id, 
                task_info.get('taskId'), 'regenerated' if force_regenerate else 'generated'
            )
            
            return {
                'success': True,
                'source': 'generated',
                'document_id': document_id,
                'document_content': generated_content['content'],
                'document_title': generated_content['title'],
                'usage_count': 1,
                'success_rate': 0,
                'quality_score': generated_content.get('quality_score', 85),
                'message': '新生成文书并已保存到库'
            }
            
        except Exception as e:
            logger.error(f"获取或生成文书失败: {str(e)}")
            return {
                'success': False,
                'error': f'文书处理失败: {str(e)}',
                'source': 'error'
            }
    
    async def _find_matching_document(
        self, 
        db: AsyncSession, 
        task_info: Dict[str, Any], 
        document_type: str
    ) -> Optional[Dict[str, Any]]:
        """查找匹配的文书"""
        try:
            # 提取任务关键词
            keywords = self._extract_keywords(task_info)
            
            # 构建查询
            query = text("""
                SELECT 
                    id, document_title as title, document_content as content,
                    usage_count, success_rate, ai_quality_score,
                    template_tags, case_keywords
                FROM document_library 
                WHERE document_type = :doc_type 
                    AND is_active = true
                    AND (
                        template_tags && :keywords
                        OR case_keywords && :keywords
                        OR (:amount_range IS NULL OR debtor_amount_range = :amount_range)
                        OR (:overdue_range IS NULL OR overdue_days_range = :overdue_range)
                    )
                ORDER BY 
                    (usage_count * 0.3 + success_rate * 0.4 + ai_quality_score * 0.3) DESC,
                    usage_count DESC
                LIMIT 1
            """)
            
            # 提取金额和逾期天数范围
            amount_range = self._get_amount_range(task_info.get('amount', 0))
            overdue_range = self._get_overdue_range(task_info.get('overdue_days', 0))
            
            result = await db.execute(query, {
                'doc_type': document_type,
                'keywords': keywords,
                'amount_range': amount_range,
                'overdue_range': overdue_range
            })
            
            row = result.fetchone()
            if row:
                return {
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'usage_count': row[3],
                    'success_rate': float(row[4]) if row[4] else 0,
                    'ai_quality_score': row[5]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"查找匹配文书失败: {str(e)}")
            return None
    
    def _extract_keywords(self, task_info: Dict[str, Any]) -> List[str]:
        """从任务信息中提取关键词"""
        keywords = []
        
        title = task_info.get('title', '')
        description = task_info.get('description', '')
        task_type = task_info.get('taskType', '')
        
        # 基于任务类型的关键词
        type_keywords = {
            'lawyer_letter': ['律师函', '催收', '债务'],
            'debt_collection': ['债务', '清收', '催收', '逾期'],
            'contract_review': ['合同', '审查', '法律风险'],
            'legal_consultation': ['法律', '咨询', '建议'],
            'general_legal': ['法律', '文书']
        }
        
        keywords.extend(type_keywords.get(task_type, []))
        
        # 从标题和描述中提取关键词
        text_content = f"{title} {description}".lower()
        
        keyword_patterns = [
            '债务', '催收', '律师函', '逾期', '还款', '欠款',
            '合同', '协议', '审查', '咨询', '法律', '通知'
        ]
        
        for pattern in keyword_patterns:
            if pattern in text_content:
                keywords.append(pattern)
        
        return list(set(keywords))  # 去重
    
    def _get_amount_range(self, amount: float) -> Optional[str]:
        """获取金额范围"""
        if amount <= 0:
            return None
        elif amount <= 10000:
            return '0-1万'
        elif amount <= 50000:
            return '1-5万'
        elif amount <= 100000:
            return '5-10万'
        elif amount <= 500000:
            return '10-50万'
        else:
            return '50万以上'
    
    def _get_overdue_range(self, days: int) -> Optional[str]:
        """获取逾期天数范围"""
        if days <= 0:
            return None
        elif days <= 30:
            return '0-30天'
        elif days <= 90:
            return '30-90天'
        elif days <= 180:
            return '90-180天'
        else:
            return '180天以上'
    
    async def _generate_new_document(
        self, 
        task_info: Dict[str, Any], 
        document_type: str
    ) -> Dict[str, Any]:
        """生成新文书"""
        try:
            # 如果有AI服务，使用AI生成
            if self.ai_service and self.config_service:
                ai_content = await self._generate_with_ai(task_info, document_type)
                if ai_content:
                    return ai_content
            
            # 回退到模板生成
            return self._generate_with_template(task_info, document_type)
            
        except Exception as e:
            logger.error(f"生成新文书失败: {str(e)}")
            return self._generate_fallback_content(task_info, document_type)
    
    async def _generate_with_ai(
        self, 
        task_info: Dict[str, Any], 
        document_type: str
    ) -> Optional[Dict[str, Any]]:
        """使用AI生成文书"""
        try:
            # 构建AI提示词
            prompt = self._build_ai_prompt(task_info, document_type)
            
            # 调用AI服务
            response = await self.ai_service.generate_text(prompt)
            
            if response and response.get('success'):
                content = response.get('content', '')
                return {
                    'title': self._generate_title(task_info, document_type),
                    'content': content,
                    'quality_score': 90,
                    'generation_method': 'ai'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"AI生成文书失败: {str(e)}")
            return None
    
    def _build_ai_prompt(self, task_info: Dict[str, Any], document_type: str) -> str:
        """构建AI提示词"""
        base_prompt = f"""
请为以下任务生成一份专业的{self.document_types.get(document_type, '法律文书')}：

任务信息：
- 标题：{task_info.get('title', '未知任务')}
- 描述：{task_info.get('description', '无描述')}
- 任务类型：{document_type}

要求：
1. 格式规范，符合法律文书标准
2. 语言严谨，逻辑清晰
3. 包含必要的法律条款引用
4. 结构完整，内容具体
5. 使用中文书写

请直接输出文书内容，不需要额外说明。
"""
        return base_prompt
    
    def _generate_with_template(
        self, 
        task_info: Dict[str, Any], 
        document_type: str
    ) -> Dict[str, Any]:
        """使用模板生成文书"""
        templates = {
            'lawyer_letter': self._generate_lawyer_letter_template(task_info),
            'debt_collection': self._generate_debt_collection_template(task_info),
            'contract_review': self._generate_contract_review_template(task_info),
            'legal_consultation': self._generate_consultation_template(task_info),
            'general_legal': self._generate_general_template(task_info)
        }
        
        content = templates.get(document_type, templates['general_legal'])
        
        return {
            'title': self._generate_title(task_info, document_type),
            'content': content,
            'quality_score': 85,
            'generation_method': 'template'
        }
    
    def _generate_title(self, task_info: Dict[str, Any], document_type: str) -> str:
        """生成文书标题"""
        base_title = self.document_types.get(document_type, '法律文书')
        task_title = task_info.get('title', '')
        
        if task_title and not task_title.startswith('未知'):
            return f"{task_title} - {base_title}"
        else:
            return f"{base_title}"
    
    def _generate_lawyer_letter_template(self, task_info: Dict[str, Any]) -> str:
        """生成律师函模板"""
        current_date = datetime.now().strftime('%Y年%m月%d日')
        
        return f"""律师函

致：[债务人姓名]

您好！

本律师受委托人委托，就相关债务事宜向您发出此函。

根据委托人提供的材料显示，您与委托人之间存在债权债务关系，现债务已到期但您尚未履行还款义务。

根据《中华人民共和国民法典》的相关规定，您应当按约履行还款义务。现郑重要求：

请您在收到本函后7日内，主动联系委托人协商解决债务问题，并尽快履行还款义务。

如您在规定期限内仍不履行，我们将建议委托人通过法律途径解决，由此产生的一切法律后果及费用损失，均由您承担。

特此函告！

律师：[律师姓名]
律师事务所：[事务所名称]
联系电话：[联系电话]
{current_date}"""
    
    def _generate_debt_collection_template(self, task_info: Dict[str, Any]) -> str:
        """生成债务催收通知书模板"""
        current_date = datetime.now().strftime('%Y年%m月%d日')
        
        return f"""债务催收通知书

[债务人姓名]：

根据相关记录显示，您存在逾期债务尚未清偿。现根据相关法律法规，特向您发出此催收通知：

一、债务情况
根据记录，您的债务详情如下：
- 债务本金：[金额]元
- 逾期费用：[费用]元
- 合计应还：[总金额]元

二、催收要求
请您务必在收到本通知后立即处理上述债务，具体要求如下：
1. 立即联系我方协商还款事宜
2. 制定合理的还款计划
3. 按时履行还款义务

三、法律后果提醒
如您继续拖欠债务，可能面临以下后果：
1. 信用记录受损
2. 承担法律责任
3. 承担相关费用

请您高度重视此事，及时主动联系处理。

联系电话：[联系电话]
{current_date}"""
    
    def _generate_contract_review_template(self, task_info: Dict[str, Any]) -> str:
        """生成合同审查意见书模板"""
        current_date = datetime.now().strftime('%Y年%m月%d日')
        
        return f"""合同审查意见书

一、审查概况
合同名称：[合同名称]
合同当事人：[甲方] 与 [乙方]
审查时间：{current_date}

二、合同主要条款审查

1. 合同主体
[审查意见]

2. 合同标的
[审查意见]

3. 权利义务条款
[审查意见]

4. 违约责任条款
[审查意见]

三、法律风险提示

1. 主要风险点
[风险分析]

2. 建议措施
[建议内容]

四、总体评价
[综合评价]

五、修改建议
[具体建议]

审查律师：[律师姓名]
律师事务所：[事务所名称]
{current_date}"""
    
    def _generate_consultation_template(self, task_info: Dict[str, Any]) -> str:
        """生成法律咨询意见书模板"""
        current_date = datetime.now().strftime('%Y年%m月%d日')
        
        return f"""法律咨询意见书

一、咨询事项
{task_info.get('description', '[请描述具体咨询事项]')}

二、事实认定
根据您提供的材料和陈述，现将相关事实梳理如下：
[事实梳理]

三、法律分析

1. 适用法律
[相关法律条文]

2. 法律关系分析
[法律关系说明]

3. 权利义务分析
[权利义务内容]

四、法律意见

1. 主要观点
[核心观点]

2. 操作建议
[具体建议]

3. 注意事项
[风险提示]

五、结论
[总结性意见]

咨询律师：[律师姓名]
律师事务所：[事务所名称]
{current_date}"""
    
    def _generate_general_template(self, task_info: Dict[str, Any]) -> str:
        """生成通用法律文书模板"""
        current_date = datetime.now().strftime('%Y年%m月%d日')
        
        return f"""法律文书

标题：{task_info.get('title', '法律事务处理')}

一、基本情况
[基本情况说明]

二、相关事实
[事实描述]

三、法律依据
[法律条文引用]

四、处理意见
[具体意见]

五、建议措施
[操作建议]

六、其他事项
[补充说明]

起草人：[姓名]
起草时间：{current_date}"""
    
    def _generate_fallback_content(
        self, 
        task_info: Dict[str, Any], 
        document_type: str
    ) -> Dict[str, Any]:
        """生成备用内容"""
        return {
            'title': f"{self.document_types.get(document_type, '法律文书')} - 简化版",
            'content': f"""简化版{self.document_types.get(document_type, '法律文书')}

任务：{task_info.get('title', '未知任务')}
描述：{task_info.get('description', '无描述')}

请根据具体情况完善此文书内容。

生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}""",
            'quality_score': 60,
            'generation_method': 'fallback'
        }
    
    async def _save_to_library(
        self,
        db: AsyncSession,
        document_type: str,
        task_info: Dict[str, Any],
        document_content: Dict[str, Any],
        user_id: UUID,
        case_id: Optional[UUID] = None
    ) -> UUID:
        """保存文书到库"""
        try:
            # 获取租户ID
            tenant_result = await db.execute(text("SELECT tenant_id FROM users WHERE id = :user_id"), 
                                           {'user_id': user_id})
            tenant_id = tenant_result.scalar()
            
            if not tenant_id:
                # 获取默认租户
                tenant_result = await db.execute(text("SELECT id FROM tenants LIMIT 1"))
                tenant_id = tenant_result.scalar()
            
            # 提取元数据
            keywords = self._extract_keywords(task_info)
            amount_range = self._get_amount_range(task_info.get('amount', 0))
            overdue_range = self._get_overdue_range(task_info.get('overdue_days', 0))
            
            # 插入文书记录
            insert_sql = text("""
                INSERT INTO document_library (
                    tenant_id, document_type, document_title, document_content,
                    template_tags, case_keywords, debtor_amount_range, overdue_days_range,
                    ai_quality_score, created_by, source_case_id, generation_method,
                    usage_count, created_at
                ) VALUES (
                    :tenant_id, :doc_type, :title, :content, :tags, :keywords,
                    :amount_range, :overdue_range, :quality_score, :user_id, :case_id,
                    :method, 1, CURRENT_TIMESTAMP
                ) RETURNING id
            """)
            
            result = await db.execute(insert_sql, {
                'tenant_id': tenant_id,
                'doc_type': document_type,
                'title': document_content['title'],
                'content': document_content['content'],
                'tags': keywords,
                'keywords': keywords,
                'amount_range': amount_range,
                'overdue_range': overdue_range,
                'quality_score': document_content.get('quality_score', 85),
                'user_id': user_id,
                'case_id': case_id,
                'method': document_content.get('generation_method', 'ai')
            })
            
            document_id = result.scalar()
            await db.commit()
            
            logger.info(f"文书已保存到库: {document_id}")
            return document_id
            
        except Exception as e:
            logger.error(f"保存文书到库失败: {str(e)}")
            await db.rollback()
            raise
    
    async def _record_document_usage(
        self,
        db: AsyncSession,
        document_id: UUID,
        user_id: UUID,
        case_id: Optional[UUID],
        task_id: Optional[str],
        usage_type: str,
        modifications: Optional[str] = None,
        final_content: Optional[str] = None
    ):
        """记录文书使用历史"""
        try:
            insert_sql = text("""
                INSERT INTO document_usage_history (
                    document_id, case_id, task_id, user_id, usage_type,
                    modifications_made, final_content, used_at
                ) VALUES (
                    :doc_id, :case_id, :task_id, :user_id, :usage_type,
                    :modifications, :final_content, CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute(insert_sql, {
                'doc_id': document_id,
                'case_id': case_id,
                'task_id': task_id,
                'user_id': user_id,
                'usage_type': usage_type,
                'modifications': modifications,
                'final_content': final_content
            })
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"记录文书使用历史失败: {str(e)}")
            # 不抛出异常，因为这不应该影响主流程
    
    async def get_document_library_stats(self, db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        """获取文书库统计信息"""
        try:
            stats_sql = text("""
                SELECT 
                    document_type,
                    COUNT(*) as total_count,
                    AVG(usage_count) as avg_usage,
                    AVG(success_rate) as avg_success_rate,
                    MAX(ai_quality_score) as max_quality
                FROM document_library
                WHERE created_by = :user_id AND is_active = true
                GROUP BY document_type
            """)
            
            result = await db.execute(stats_sql, {'user_id': user_id})
            
            stats = {}
            for row in result:
                stats[row[0]] = {
                    'total_count': row[1],
                    'avg_usage': float(row[2]) if row[2] else 0,
                    'avg_success_rate': float(row[3]) if row[3] else 0,
                    'max_quality': row[4]
                }
            
            return {
                'success': True,
                'stats': stats,
                'total_documents': sum(s['total_count'] for s in stats.values())
            }
            
        except Exception as e:
            logger.error(f"获取文书库统计失败: {str(e)}")
            return {'success': False, 'error': str(e)}