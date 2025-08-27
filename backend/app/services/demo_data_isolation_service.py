"""
演示数据隔离服务
确保演示数据与真实数据的完全隔离和安全
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import structlog
import json
from datetime import datetime, timedelta

logger = structlog.get_logger()


class DemoDataIsolationService:
    """演示数据隔离服务 - 确保演示环境的数据安全"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # 定义需要隔离的敏感表
        self.sensitive_tables = [
            'users',
            'cases',
            'payments',
            'documents',
            'user_credits',
            'lawyer_memberships',
            'lawyer_certification_requests'
        ]
        
        # 演示数据前缀
        self.demo_prefix = 'demo_'
    
    async def create_demo_data_views(self):
        """创建演示数据视图，确保数据隔离"""
        try:
            # 为演示账户创建安全的数据视图
            demo_views = {
                'demo_cases_view': """
                    CREATE OR REPLACE VIEW demo_cases_view AS
                    SELECT 
                        'demo-case-' || generate_random_uuid()::text as id,
                        '演示案件' as title,
                        '这是一个演示案件，用于展示平台功能' as description,
                        50000 as amount,
                        '进行中' as status,
                        NOW() - INTERVAL '5 days' as created_at,
                        '演示客户' as client_name
                    WHERE FALSE; -- 确保不返回真实数据
                """,
                
                'demo_users_view': """
                    CREATE OR REPLACE VIEW demo_users_view AS
                    SELECT 
                        'demo-user-' || generate_random_uuid()::text as id,
                        '演示用户' as full_name,
                        'demo@example.com' as email,
                        'demo' as account_type,
                        TRUE as email_verified
                    WHERE FALSE; -- 确保不返回真实数据
                """,
                
                'demo_payments_view': """
                    CREATE OR REPLACE VIEW demo_payments_view AS
                    SELECT 
                        'demo-payment-' || generate_random_uuid()::text as id,
                        50000 as amount,
                        '已完成' as status,
                        NOW() - INTERVAL '2 days' as created_at,
                        '演示支付' as description
                    WHERE FALSE; -- 确保不返回真实数据
                """
            }
            
            for view_name, view_sql in demo_views.items():
                await self.db.execute(text(view_sql))
            
            await self.db.commit()
            logger.info("演示数据视图创建成功")
            
        except Exception as e:
            await self.db.rollback()
            logger.error("创建演示数据视图失败", error=str(e))
            raise
    
    async def get_isolated_demo_data(
        self,
        workspace_id: str,
        data_type: str,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        获取隔离的演示数据
        
        Args:
            workspace_id: 演示工作台ID
            data_type: 数据类型
            filters: 过滤条件
        
        Returns:
            隔离的演示数据
        """
        try:
            # 验证是否为演示工作台
            if not workspace_id.startswith('demo-'):
                raise ValueError("非演示工作台不能访问演示数据")
            
            # 根据数据类型返回相应的演示数据
            demo_data_generators = {
                'cases': self._generate_demo_cases,
                'users': self._generate_demo_users,
                'payments': self._generate_demo_payments,
                'statistics': self._generate_demo_statistics,
                'documents': self._generate_demo_documents
            }
            
            if data_type not in demo_data_generators:
                return {'data': [], 'total': 0, 'message': '不支持的数据类型'}
            
            # 生成演示数据
            demo_data = await demo_data_generators[data_type](workspace_id, filters)
            
            # 添加演示标识
            demo_data['is_demo'] = True
            demo_data['workspace_id'] = workspace_id
            demo_data['generated_at'] = datetime.now().isoformat()
            
            return demo_data
            
        except Exception as e:
            logger.error("获取演示数据失败", error=str(e), workspace_id=workspace_id)
            return {
                'data': [],
                'total': 0,
                'error': str(e),
                'is_demo': True
            }
    
    async def _generate_demo_cases(
        self,
        workspace_id: str,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """生成演示案件数据"""
        demo_cases = [
            {
                'id': 'demo-case-001',
                'title': '合同违约纠纷案件',
                'description': '因供应商未按时交付产品导致的合同违约纠纷，需要专业律师协助处理',
                'amount': 50000,
                'status': '进行中',
                'client_name': '某科技公司',
                'lawyer_name': '张律师',
                'created_at': (datetime.now() - timedelta(days=5)).isoformat(),
                'updated_at': (datetime.now() - timedelta(hours=2)).isoformat(),
                'progress': 65,
                'category': '合同纠纷',
                'priority': '高',
                'estimated_duration': '30天'
            },
            {
                'id': 'demo-case-002',
                'title': '债务催收案件',
                'description': '应收账款催收，涉及金额较大，需要采取法律手段',
                'amount': 120000,
                'status': '已完成',
                'client_name': '某贸易公司',
                'lawyer_name': '王律师',
                'created_at': (datetime.now() - timedelta(days=20)).isoformat(),
                'completed_at': (datetime.now() - timedelta(days=5)).isoformat(),
                'progress': 100,
                'category': '债务催收',
                'priority': '中',
                'success_rate': 95
            },
            {
                'id': 'demo-case-003',
                'title': '劳动争议调解',
                'description': '员工工伤赔偿争议，需要进行调解和法律咨询',
                'amount': 25000,
                'status': '待接受',
                'client_name': '某制造企业',
                'created_at': datetime.now().isoformat(),
                'progress': 0,
                'category': '劳动争议',
                'priority': '中',
                'deadline': (datetime.now() + timedelta(days=15)).isoformat()
            }
        ]
        
        # 应用过滤条件
        if filters:
            if 'status' in filters:
                demo_cases = [case for case in demo_cases if case['status'] == filters['status']]
            if 'category' in filters:
                demo_cases = [case for case in demo_cases if case['category'] == filters['category']]
        
        return {
            'data': demo_cases,
            'total': len(demo_cases),
            'page': 1,
            'per_page': 10
        }
    
    async def _generate_demo_users(
        self,
        workspace_id: str,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """生成演示用户数据"""
        demo_users = [
            {
                'id': 'demo-user-001',
                'full_name': '张律师',
                'email': 'zhang.lawyer@demo.com',
                'account_type': 'lawyer',
                'specialties': ['合同纠纷', '债务催收', '公司法务'],
                'experience_years': 8,
                'success_rate': 92.5,
                'cases_handled': 156,
                'rating': 4.8,
                'status': 'active',
                'created_at': (datetime.now() - timedelta(days=365)).isoformat()
            },
            {
                'id': 'demo-user-002',
                'full_name': '李先生',
                'email': 'li.client@demo.com',
                'account_type': 'user',
                'company': '某科技公司',
                'position': '法务经理',
                'cases_published': 5,
                'total_spent': 280000,
                'satisfaction_rating': 4.6,
                'status': 'active',
                'created_at': (datetime.now() - timedelta(days=180)).isoformat()
            }
        ]
        
        return {
            'data': demo_users,
            'total': len(demo_users),
            'page': 1,
            'per_page': 10
        }
    
    async def _generate_demo_payments(
        self,
        workspace_id: str,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """生成演示支付数据"""
        demo_payments = [
            {
                'id': 'demo-payment-001',
                'amount': 50000,
                'status': '已完成',
                'method': '银行转账',
                'case_id': 'demo-case-001',
                'case_title': '合同违约纠纷案件',
                'created_at': (datetime.now() - timedelta(days=10)).isoformat(),
                'completed_at': (datetime.now() - timedelta(days=8)).isoformat(),
                'description': '案件服务费支付'
            },
            {
                'id': 'demo-payment-002',
                'amount': 120000,
                'status': '已完成',
                'method': '在线支付',
                'case_id': 'demo-case-002',
                'case_title': '债务催收案件',
                'created_at': (datetime.now() - timedelta(days=25)).isoformat(),
                'completed_at': (datetime.now() - timedelta(days=20)).isoformat(),
                'description': '债务催收服务费'
            }
        ]
        
        return {
            'data': demo_payments,
            'total': len(demo_payments),
            'page': 1,
            'per_page': 10
        }
    
    async def _generate_demo_statistics(
        self,
        workspace_id: str,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """生成演示统计数据"""
        demo_stats = {
            'overview': {
                'total_cases': 156,
                'active_cases': 12,
                'completed_cases': 144,
                'success_rate': 92.5,
                'total_earnings': 580000,
                'this_month_earnings': 45000,
                'client_satisfaction': 4.8
            },
            'monthly_data': [
                {'month': '2024-01', 'cases': 15, 'earnings': 75000},
                {'month': '2024-02', 'cases': 18, 'earnings': 90000},
                {'month': '2024-03', 'cases': 12, 'earnings': 60000},
                {'month': '2024-04', 'cases': 20, 'earnings': 100000},
                {'month': '2024-05', 'cases': 16, 'earnings': 80000}
            ],
            'case_categories': [
                {'category': '合同纠纷', 'count': 45, 'percentage': 28.8},
                {'category': '债务催收', 'count': 38, 'percentage': 24.4},
                {'category': '劳动争议', 'count': 32, 'percentage': 20.5},
                {'category': '公司法务', 'count': 25, 'percentage': 16.0},
                {'category': '其他', 'count': 16, 'percentage': 10.3}
            ]
        }
        
        return {
            'data': demo_stats,
            'total': 1,
            'generated_at': datetime.now().isoformat()
        }
    
    async def _generate_demo_documents(
        self,
        workspace_id: str,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """生成演示文档数据"""
        demo_documents = [
            {
                'id': 'demo-doc-001',
                'name': '合同违约纠纷起诉书.pdf',
                'type': '法律文书',
                'size': '2.5MB',
                'case_id': 'demo-case-001',
                'case_title': '合同违约纠纷案件',
                'created_at': (datetime.now() - timedelta(days=3)).isoformat(),
                'status': '已完成',
                'download_url': '/demo/documents/demo-doc-001'
            },
            {
                'id': 'demo-doc-002',
                'name': '债务催收律师函.pdf',
                'type': '律师函',
                'size': '1.8MB',
                'case_id': 'demo-case-002',
                'case_title': '债务催收案件',
                'created_at': (datetime.now() - timedelta(days=15)).isoformat(),
                'status': '已发送',
                'download_url': '/demo/documents/demo-doc-002'
            }
        ]
        
        return {
            'data': demo_documents,
            'total': len(demo_documents),
            'page': 1,
            'per_page': 10
        }
    
    async def validate_demo_data_access(
        self,
        workspace_id: str,
        requested_data: str
    ) -> Dict[str, Any]:
        """验证演示数据访问权限"""
        try:
            # 检查是否为演示工作台
            if not workspace_id.startswith('demo-'):
                return {
                    'allowed': False,
                    'reason': '非演示工作台不能访问演示数据'
                }
            
            # 检查请求的数据类型是否被允许
            allowed_data_types = [
                'cases', 'users', 'payments', 'statistics', 
                'documents', 'profile', 'activities'
            ]
            
            if requested_data not in allowed_data_types:
                return {
                    'allowed': False,
                    'reason': f'数据类型 "{requested_data}" 不被允许访问'
                }
            
            return {
                'allowed': True,
                'data_type': requested_data,
                'workspace_id': workspace_id
            }
            
        except Exception as e:
            logger.error("验证演示数据访问失败", error=str(e))
            return {
                'allowed': False,
                'reason': '访问验证失败'
            }
    
    async def cleanup_demo_data(self):
        """清理过期的演示数据（定时任务）"""
        try:
            # 这里可以实现演示数据的清理逻辑
            # 比如清理超过24小时的临时演示数据
            logger.info("演示数据清理任务执行")
            
            # 清理演示会话数据
            cleanup_sql = """
                DELETE FROM demo_sessions 
                WHERE created_at < NOW() - INTERVAL '24 hours'
            """
            
            # 注意：这里不会删除demo_accounts表中的基础演示数据
            # 只清理临时的会话数据
            
        except Exception as e:
            logger.error("清理演示数据失败", error=str(e))
    
    async def ensure_data_isolation(self):
        """确保数据隔离的完整性"""
        try:
            # 检查是否有演示数据泄露到真实数据中
            isolation_checks = [
                "SELECT COUNT(*) FROM users WHERE email LIKE '%demo%'",
                "SELECT COUNT(*) FROM cases WHERE title LIKE '%演示%'",
                "SELECT COUNT(*) FROM payments WHERE description LIKE '%演示%'"
            ]
            
            for check_sql in isolation_checks:
                result = await self.db.execute(text(check_sql))
                count = result.scalar()
                
                if count > 0:
                    logger.warning(
                        "发现可能的演示数据泄露",
                        sql=check_sql,
                        count=count
                    )
            
            logger.info("数据隔离检查完成")
            
        except Exception as e:
            logger.error("数据隔离检查失败", error=str(e))