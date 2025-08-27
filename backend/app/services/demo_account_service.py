"""
演示账户服务
提供安全的演示数据和功能隔离
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, delete
from fastapi import HTTPException, status
import structlog
import secrets
import hashlib
from datetime import datetime, timedelta
import json

from app.models.unified_auth import DemoAccount, WorkspaceMapping
from app.models.user import User
from app.models.case import Case

logger = structlog.get_logger()


class DemoAccountService:
    """演示账户服务类 - 提供安全的演示数据和功能隔离"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_demo_account_data(self, demo_type: str) -> Dict[str, Any]:
        """
        获取演示账户数据
        
        Args:
            demo_type: 演示类型 ('lawyer' 或 'user')
        
        Returns:
            演示账户数据
        """
        try:
            # 从demo_accounts表获取演示数据
            result = await self.db.execute(
                select(DemoAccount)
                .where(
                    DemoAccount.demo_type == demo_type,
                    DemoAccount.is_active == True
                )
                .limit(1)
            )
            
            demo_account = result.scalar_one_or_none()
            
            if not demo_account:
                # 创建默认演示数据
                demo_account = await self.create_default_demo_account(demo_type)
            
            # 确保演示数据是最新的
            demo_data = await self.refresh_demo_data(demo_account)
            
            return {
                'workspace_id': demo_account.workspace_id,
                'display_name': demo_account.display_name,
                'demo_data': demo_data,
                'is_demo': True,
                'demo_type': demo_type,
                'session_id': self.generate_demo_session_id()
            }
            
        except Exception as e:
            logger.error("获取演示账户数据失败", error=str(e), demo_type=demo_type)
            # 返回默认演示数据作为后备
            return await self.get_fallback_demo_data(demo_type)
    
    async def create_default_demo_account(self, demo_type: str) -> DemoAccount:
        """创建默认演示账户"""
        workspace_id = f"demo-{demo_type}-{secrets.token_hex(4)}"
        default_data = self.get_default_demo_data(demo_type)
        
        demo_account_data = {
            'demo_type': demo_type,
            'workspace_id': workspace_id,
            'display_name': default_data['display_name'],
            'demo_data': default_data['data'],
            'is_active': True
        }
        
        result = await self.db.execute(
            insert(DemoAccount).values(**demo_account_data).returning(DemoAccount)
        )
        
        demo_account = result.scalar_one()
        await self.db.commit()
        
        logger.info("创建默认演示账户", demo_type=demo_type, workspace_id=workspace_id)
        return demo_account
    
    def get_default_demo_data(self, demo_type: str) -> Dict[str, Any]:
        """获取默认演示数据"""
        if demo_type == 'lawyer':
            return {
                'display_name': '张律师（演示）',
                'data': {
                    'profile': {
                        'name': '张律师',
                        'license_number': 'DEMO-LAW-001',
                        'law_firm': '演示律师事务所',
                        'specialties': ['合同纠纷', '债务催收', '公司法务', '劳动争议'],
                        'experience_years': 8,
                        'education': '某知名法学院 法学硕士',
                        'certifications': ['企业法律顾问', '仲裁员资格']
                    },
                    'statistics': {
                        'success_rate': 92.5,
                        'cases_handled': 156,
                        'client_rating': 4.8,
                        'response_time': '2小时内',
                        'total_earnings': 580000,
                        'this_month_cases': 12
                    },
                    'demo_cases': [
                        {
                            'id': 'demo-case-001',
                            'title': '合同违约纠纷案件',
                            'client_name': '某科技公司',
                            'amount': 50000,
                            'status': '进行中',
                            'created_at': '2024-01-15',
                            'description': '因供应商未按时交付产品导致的合同违约纠纷',
                            'progress': 65
                        },
                        {
                            'id': 'demo-case-002',
                            'title': '债务催收案件',
                            'client_name': '某贸易公司',
                            'amount': 120000,
                            'status': '已完成',
                            'created_at': '2024-01-10',
                            'completed_at': '2024-01-20',
                            'description': '应收账款催收，已成功追回全部欠款',
                            'progress': 100
                        },
                        {
                            'id': 'demo-case-003',
                            'title': '劳动争议调解',
                            'client_name': '某制造企业',
                            'amount': 25000,
                            'status': '待接受',
                            'created_at': '2024-01-25',
                            'description': '员工工伤赔偿争议调解',
                            'progress': 0
                        }
                    ],
                    'recent_activities': [
                        {'time': '2小时前', 'action': '提交了案件进展报告'},
                        {'time': '5小时前', 'action': '与客户进行了电话沟通'},
                        {'time': '1天前', 'action': '完成了债务催收案件'},
                        {'time': '2天前', 'action': '接受了新的合同纠纷案件'}
                    ],
                    'earnings': {
                        'this_month': 45000,
                        'last_month': 38000,
                        'pending': 15000,
                        'total_this_year': 420000
                    }
                }
            }
        else:  # user
            return {
                'display_name': '李先生（演示）',
                'data': {
                    'profile': {
                        'name': '李先生',
                        'company': '某科技公司',
                        'position': '法务经理',
                        'industry': '互联网科技',
                        'company_size': '500-1000人'
                    },
                    'statistics': {
                        'cases_published': 5,
                        'total_amount': 280000,
                        'completed_cases': 3,
                        'success_rate': 85.7,
                        'average_response_time': '3小时',
                        'satisfaction_rating': 4.6
                    },
                    'demo_cases': [
                        {
                            'id': 'demo-case-003',
                            'title': '劳动合同纠纷处理',
                            'amount': 30000,
                            'status': '匹配中',
                            'created_at': '2024-01-25',
                            'description': '员工离职补偿争议，需要专业律师协助处理',
                            'applications': 3,
                            'deadline': '2024-02-10'
                        },
                        {
                            'id': 'demo-case-004',
                            'title': '供应商合同审查',
                            'amount': 80000,
                            'status': '进行中',
                            'lawyer_name': '王律师',
                            'created_at': '2024-01-20',
                            'description': '重要供应商合同条款审查和风险评估',
                            'progress': 40
                        },
                        {
                            'id': 'demo-case-005',
                            'title': '知识产权保护咨询',
                            'amount': 120000,
                            'status': '已完成',
                            'lawyer_name': '陈律师',
                            'created_at': '2024-01-05',
                            'completed_at': '2024-01-18',
                            'description': '软件著作权申请和商标注册指导',
                            'rating': 5
                        }
                    ],
                    'recent_activities': [
                        {'time': '1小时前', 'action': '发布了新的法律咨询需求'},
                        {'time': '4小时前', 'action': '查看了律师申请'},
                        {'time': '1天前', 'action': '完成了知识产权案件评价'},
                        {'time': '3天前', 'action': '与律师进行了案件沟通'}
                    ],
                    'budget_info': {
                        'total_budget': 500000,
                        'used_budget': 280000,
                        'remaining_budget': 220000,
                        'this_month_spent': 80000
                    }
                }
            }
    
    async def refresh_demo_data(self, demo_account: DemoAccount) -> Dict[str, Any]:
        """刷新演示数据，确保数据的时效性"""
        try:
            demo_data = demo_account.demo_data.copy()
            
            # 更新时间相关的数据
            if demo_account.demo_type == 'lawyer':
                # 更新最近活动时间
                if 'recent_activities' in demo_data:
                    demo_data['recent_activities'] = self.update_activity_times(
                        demo_data['recent_activities']
                    )
                
                # 更新案件创建时间
                if 'demo_cases' in demo_data:
                    demo_data['demo_cases'] = self.update_case_times(
                        demo_data['demo_cases']
                    )
            
            elif demo_account.demo_type == 'user':
                # 更新用户相关的时间数据
                if 'recent_activities' in demo_data:
                    demo_data['recent_activities'] = self.update_activity_times(
                        demo_data['recent_activities']
                    )
                
                if 'demo_cases' in demo_data:
                    demo_data['demo_cases'] = self.update_case_times(
                        demo_data['demo_cases']
                    )
            
            # 如果数据有更新，保存到数据库
            if demo_data != demo_account.demo_data:
                await self.db.execute(
                    update(DemoAccount)
                    .where(DemoAccount.id == demo_account.id)
                    .values(demo_data=demo_data)
                )
                await self.db.commit()
            
            return demo_data
            
        except Exception as e:
            logger.error("刷新演示数据失败", error=str(e))
            return demo_account.demo_data
    
    def update_activity_times(self, activities: List[Dict]) -> List[Dict]:
        """更新活动时间，使其看起来是最近的"""
        time_offsets = ['2小时前', '5小时前', '1天前', '2天前', '3天前']
        
        for i, activity in enumerate(activities):
            if i < len(time_offsets):
                activity['time'] = time_offsets[i]
        
        return activities
    
    def update_case_times(self, cases: List[Dict]) -> List[Dict]:
        """更新案件时间"""
        now = datetime.now()
        
        for i, case in enumerate(cases):
            if case.get('status') == '待接受' or case.get('status') == '匹配中':
                # 最新的案件
                case['created_at'] = (now - timedelta(days=i)).strftime('%Y-%m-%d')
            elif case.get('status') == '进行中':
                # 进行中的案件
                case['created_at'] = (now - timedelta(days=i+5)).strftime('%Y-%m-%d')
            elif case.get('status') == '已完成':
                # 已完成的案件
                case['created_at'] = (now - timedelta(days=i+10)).strftime('%Y-%m-%d')
                case['completed_at'] = (now - timedelta(days=i+5)).strftime('%Y-%m-%d')
        
        return cases
    
    def generate_demo_session_id(self) -> str:
        """生成演示会话ID"""
        return f"demo-session-{secrets.token_hex(8)}"
    
    async def get_fallback_demo_data(self, demo_type: str) -> Dict[str, Any]:
        """获取后备演示数据"""
        default_data = self.get_default_demo_data(demo_type)
        return {
            'workspace_id': f'demo-{demo_type}-fallback',
            'display_name': default_data['display_name'],
            'demo_data': default_data['data'],
            'is_demo': True,
            'demo_type': demo_type,
            'session_id': self.generate_demo_session_id()
        }
    
    async def is_demo_workspace(self, workspace_id: str) -> bool:
        """检查是否为演示工作台"""
        if workspace_id.startswith('demo-'):
            return True
        
        # 从数据库检查
        result = await self.db.execute(
            select(DemoAccount.id)
            .where(DemoAccount.workspace_id == workspace_id)
        )
        
        return result.scalar_one_or_none() is not None
    
    async def get_demo_restrictions(self, demo_type: str) -> Dict[str, Any]:
        """获取演示账户的功能限制"""
        base_restrictions = {
            'can_create_real_cases': False,
            'can_make_payments': False,
            'can_upload_files': False,
            'can_send_messages': False,
            'can_access_real_data': False,
            'session_timeout': 3600,  # 1小时
            'max_demo_actions': 50
        }
        
        if demo_type == 'lawyer':
            base_restrictions.update({
                'can_accept_cases': False,
                'can_submit_reports': False,
                'can_rate_clients': False
            })
        elif demo_type == 'user':
            base_restrictions.update({
                'can_publish_cases': False,
                'can_hire_lawyers': False,
                'can_rate_lawyers': False
            })
        
        return base_restrictions
    
    async def validate_demo_action(
        self,
        workspace_id: str,
        action: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """验证演示账户操作是否被允许"""
        if not await self.is_demo_workspace(workspace_id):
            return {'allowed': True, 'reason': 'Not a demo account'}
        
        # 获取演示类型
        result = await self.db.execute(
            select(DemoAccount.demo_type)
            .where(DemoAccount.workspace_id == workspace_id)
        )
        
        demo_account = result.scalar_one_or_none()
        if not demo_account:
            return {'allowed': False, 'reason': 'Demo account not found'}
        
        restrictions = await self.get_demo_restrictions(demo_account.demo_type)
        
        # 检查特定操作限制
        restricted_actions = {
            'create_case': not restrictions['can_create_real_cases'],
            'make_payment': not restrictions['can_make_payments'],
            'upload_file': not restrictions['can_upload_files'],
            'send_message': not restrictions['can_send_messages'],
            'accept_case': not restrictions.get('can_accept_cases', True),
            'publish_case': not restrictions.get('can_publish_cases', True)
        }
        
        if action in restricted_actions and restricted_actions[action]:
            return {
                'allowed': False,
                'reason': f'Action "{action}" is not allowed in demo mode',
                'suggestion': '请注册真实账户以使用完整功能'
            }
        
        return {'allowed': True}
    
    async def log_demo_activity(
        self,
        workspace_id: str,
        action: str,
        details: Optional[Dict] = None
    ):
        """记录演示账户活动（用于分析和改进）"""
        try:
            # 这里可以记录到专门的演示活动日志表
            # 或者发送到分析系统
            logger.info(
                "演示账户活动",
                workspace_id=workspace_id,
                action=action,
                details=details
            )
        except Exception as e:
            logger.error("记录演示活动失败", error=str(e))
    
    async def cleanup_expired_demo_sessions(self):
        """清理过期的演示会话（定时任务）"""
        try:
            # 这里可以实现演示会话的清理逻辑
            # 比如清理超过1小时的演示数据
            logger.info("演示会话清理任务执行")
        except Exception as e:
            logger.error("清理演示会话失败", error=str(e))
    
    async def update_demo_data_periodically(self):
        """定期更新演示数据（定时任务）"""
        try:
            # 获取所有活跃的演示账户
            result = await self.db.execute(
                select(DemoAccount)
                .where(DemoAccount.is_active == True)
            )
            
            demo_accounts = result.scalars().all()
            
            for demo_account in demo_accounts:
                await self.refresh_demo_data(demo_account)
            
            logger.info(f"更新了 {len(demo_accounts)} 个演示账户的数据")
            
        except Exception as e:
            logger.error("定期更新演示数据失败", error=str(e))