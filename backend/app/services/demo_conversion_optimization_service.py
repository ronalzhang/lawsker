"""
Demo Conversion Optimization Service
演示账户转化率优化服务

This service specifically focuses on optimizing demo account to registration conversion
to achieve the 30% conversion rate target.
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, delete, func, and_, or_
from fastapi import HTTPException, status
import structlog
import secrets
import json
from datetime import datetime, timedelta
from enum import Enum

from app.models.unified_auth import DemoAccount, WorkspaceMapping
from app.models.user import User

logger = structlog.get_logger()


class ConversionTriggerType(str, Enum):
    """转化触发类型"""
    TIME_BASED = "time_based"           # 基于时间的触发
    ACTION_BASED = "action_based"       # 基于行为的触发
    FEATURE_LIMIT = "feature_limit"     # 功能限制触发
    EXIT_INTENT = "exit_intent"         # 退出意图触发
    COMPLETION_REWARD = "completion_reward"  # 完成奖励触发


class DemoConversionOptimizationService:
    """演示账户转化率优化服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.conversion_target = 30.0  # 30% conversion rate target
    
    async def track_demo_conversion_event(
        self,
        workspace_id: str,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """跟踪演示账户转化事件"""
        try:
            # Verify this is a demo workspace
            if not await self.is_demo_workspace(workspace_id):
                raise ValueError("Not a demo workspace")
            
            # Get demo account info
            demo_account = await self.get_demo_account_by_workspace(workspace_id)
            if not demo_account:
                raise ValueError("Demo account not found")
            
            # Create conversion event record
            conversion_event = {
                'workspace_id': workspace_id,
                'demo_type': demo_account.demo_type,
                'event_type': event_type,
                'event_data': event_data or {},
                'session_id': session_id,
                'timestamp': datetime.utcnow(),
                'converted': False  # Will be updated when actual conversion happens
            }
            
            # Log the event for analytics
            logger.info(
                "Demo conversion event tracked",
                workspace_id=workspace_id,
                event_type=event_type,
                demo_type=demo_account.demo_type
            )
            
            # Check if this event should trigger a conversion prompt
            conversion_prompt = await self.evaluate_conversion_trigger(
                workspace_id, event_type, event_data
            )
            
            return {
                'event_recorded': True,
                'conversion_prompt': conversion_prompt,
                'event_id': f"demo-event-{secrets.token_hex(8)}"
            }
            
        except Exception as e:
            logger.error("Failed to track demo conversion event", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to track conversion event"
            )
    
    async def evaluate_conversion_trigger(
        self,
        workspace_id: str,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """评估是否应该触发转化提示"""
        try:
            demo_account = await self.get_demo_account_by_workspace(workspace_id)
            if not demo_account:
                return None
            
            # Get demo session data
            session_data = await self.get_demo_session_data(workspace_id)
            
            # Evaluate different trigger conditions
            triggers = []
            
            # 1. Time-based triggers
            if session_data.get('session_duration', 0) > 300:  # 5 minutes
                triggers.append({
                    'type': ConversionTriggerType.TIME_BASED,
                    'priority': 'medium',
                    'message': '您已体验了5分钟，注册账户解锁更多功能！',
                    'incentive': '注册即可获得免费AI咨询额度'
                })
            
            # 2. Action-based triggers
            if event_type == 'case_view_complete':
                triggers.append({
                    'type': ConversionTriggerType.ACTION_BASED,
                    'priority': 'high',
                    'message': '看起来您对我们的案件管理很感兴趣！',
                    'incentive': '注册后可以发布真实案件需求'
                })
            
            # 3. Feature limit triggers
            if event_type == 'feature_restricted':
                triggers.append({
                    'type': ConversionTriggerType.FEATURE_LIMIT,
                    'priority': 'high',
                    'message': '此功能需要注册账户才能使用',
                    'incentive': '注册免费，立即解锁所有功能'
                })
            
            # 4. Completion reward triggers
            actions_completed = session_data.get('actions_completed', 0)
            if actions_completed >= 3:
                triggers.append({
                    'type': ConversionTriggerType.COMPLETION_REWARD,
                    'priority': 'high',
                    'message': '恭喜！您已完成演示体验',
                    'incentive': '注册账户获得专属新用户礼包'
                })
            
            # Return the highest priority trigger
            if triggers:
                return max(triggers, key=lambda x: 
                    {'high': 3, 'medium': 2, 'low': 1}[x['priority']]
                )
            
            return None
            
        except Exception as e:
            logger.error("Failed to evaluate conversion trigger", error=str(e))
            return None
    
    async def get_demo_session_data(self, workspace_id: str) -> Dict[str, Any]:
        """获取演示会话数据"""
        # In a real implementation, this would fetch from a session store
        # For now, return simulated data
        return {
            'session_duration': 420,  # 7 minutes
            'actions_completed': 4,
            'pages_viewed': 8,
            'features_explored': ['cases', 'dashboard', 'profile'],
            'last_activity': datetime.utcnow().isoformat()
        }
    
    async def record_conversion_success(
        self,
        workspace_id: str,
        user_id: str,
        conversion_source: str = 'demo'
    ) -> Dict[str, Any]:
        """记录转化成功"""
        try:
            # Verify this was a demo workspace
            if not await self.is_demo_workspace(workspace_id):
                return {'recorded': False, 'reason': 'Not a demo workspace'}
            
            demo_account = await self.get_demo_account_by_workspace(workspace_id)
            if not demo_account:
                return {'recorded': False, 'reason': 'Demo account not found'}
            
            # Record the conversion
            conversion_record = {
                'demo_workspace_id': workspace_id,
                'demo_type': demo_account.demo_type,
                'converted_user_id': user_id,
                'conversion_source': conversion_source,
                'conversion_timestamp': datetime.utcnow(),
                'session_data': await self.get_demo_session_data(workspace_id)
            }
            
            # Update user record to mark as demo conversion
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(registration_source='demo_conversion')
            )
            
            await self.db.commit()
            
            logger.info(
                "Demo conversion recorded",
                workspace_id=workspace_id,
                user_id=user_id,
                demo_type=demo_account.demo_type
            )
            
            return {
                'recorded': True,
                'conversion_id': f"conv-{secrets.token_hex(8)}",
                'demo_type': demo_account.demo_type
            }
            
        except Exception as e:
            logger.error("Failed to record conversion success", error=str(e))
            return {'recorded': False, 'reason': str(e)}
    
    async def get_demo_conversion_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        demo_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取演示账户转化指标"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get demo account access count
            demo_access_count = await self.get_demo_access_count(
                start_date, end_date, demo_type
            )
            
            # Get conversion count
            conversion_count = await self.get_demo_conversion_count(
                start_date, end_date, demo_type
            )
            
            # Calculate conversion rate
            conversion_rate = (
                (conversion_count / demo_access_count * 100) 
                if demo_access_count > 0 else 0
            )
            
            # Get conversion by demo type
            conversion_by_type = await self.get_conversion_by_demo_type(
                start_date, end_date
            )
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'metrics': {
                    'demo_access_count': demo_access_count,
                    'conversion_count': conversion_count,
                    'conversion_rate': round(conversion_rate, 2),
                    'target_conversion_rate': self.conversion_target,
                    'target_gap': round(self.conversion_target - conversion_rate, 2),
                    'target_achieved': conversion_rate >= self.conversion_target
                },
                'conversion_by_type': conversion_by_type,
                'performance_status': self.get_performance_status(conversion_rate)
            }
            
        except Exception as e:
            logger.error("Failed to get demo conversion metrics", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get conversion metrics"
            )
    
    async def get_demo_access_count(
        self,
        start_date: datetime,
        end_date: datetime,
        demo_type: Optional[str] = None
    ) -> int:
        """获取演示账户访问次数"""
        # In a real implementation, this would query access logs
        # For now, simulate based on demo accounts
        base_count = 150  # Simulated daily demo access
        days = (end_date - start_date).days
        return base_count * max(days, 1)
    
    async def get_demo_conversion_count(
        self,
        start_date: datetime,
        end_date: datetime,
        demo_type: Optional[str] = None
    ) -> int:
        """获取演示账户转化次数"""
        query = select(func.count(User.id)).where(
            and_(
                User.registration_source == 'demo_conversion',
                User.created_at >= start_date,
                User.created_at <= end_date
            )
        )
        
        if demo_type:
            # In a real implementation, we'd join with conversion records
            # For now, estimate based on account type
            pass
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def get_conversion_by_demo_type(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Dict[str, Any]]:
        """获取按演示类型分组的转化数据"""
        # Simulate conversion data by demo type
        return {
            'lawyer': {
                'access_count': 80,
                'conversion_count': 18,
                'conversion_rate': 22.5
            },
            'user': {
                'access_count': 70,
                'conversion_count': 25,
                'conversion_rate': 35.7
            }
        }
    
    def get_performance_status(self, conversion_rate: float) -> str:
        """获取性能状态"""
        if conversion_rate >= self.conversion_target:
            return 'excellent'
        elif conversion_rate >= self.conversion_target * 0.8:
            return 'good'
        elif conversion_rate >= self.conversion_target * 0.6:
            return 'needs_improvement'
        else:
            return 'critical'
    
    async def get_conversion_optimization_recommendations(
        self,
        current_rate: float
    ) -> List[Dict[str, Any]]:
        """获取转化优化建议"""
        recommendations = []
        
        gap = self.conversion_target - current_rate
        
        if gap > 0:
            if gap > 15:
                recommendations.extend([
                    {
                        'priority': 'critical',
                        'title': '实施紧急转化优化',
                        'description': f'当前转化率 {current_rate}%，距离目标 {self.conversion_target}% 还有 {gap:.1f}% 差距',
                        'actions': [
                            '立即启用智能转化提示系统',
                            '增加演示功能限制以促进注册',
                            '实施退出意图检测和挽留',
                            '添加注册激励和奖励机制'
                        ],
                        'expected_impact': '10-15% 转化率提升'
                    }
                ])
            elif gap > 5:
                recommendations.extend([
                    {
                        'priority': 'high',
                        'title': '优化演示体验流程',
                        'description': f'需要提升 {gap:.1f}% 转化率达到目标',
                        'actions': [
                            '优化演示引导流程',
                            '增加个性化转化提示',
                            '实施A/B测试不同转化策略',
                            '改进演示完成奖励机制'
                        ],
                        'expected_impact': '5-8% 转化率提升'
                    }
                ])
            else:
                recommendations.extend([
                    {
                        'priority': 'medium',
                        'title': '微调转化细节',
                        'description': f'接近目标，需要精细优化提升 {gap:.1f}%',
                        'actions': [
                            '优化转化提示文案',
                            '调整转化触发时机',
                            '个性化用户体验',
                            '增强信任指标展示'
                        ],
                        'expected_impact': '2-5% 转化率提升'
                    }
                ])
        
        return recommendations
    
    async def generate_ab_test_variants(self) -> List[Dict[str, Any]]:
        """生成A/B测试变体"""
        return [
            {
                'variant_id': 'control',
                'name': '对照组',
                'description': '当前默认演示体验',
                'changes': []
            },
            {
                'variant_id': 'aggressive_prompts',
                'name': '积极提示组',
                'description': '更频繁的转化提示',
                'changes': [
                    '2分钟后显示第一个转化提示',
                    '每完成一个操作显示转化提示',
                    '增加紧迫感文案'
                ]
            },
            {
                'variant_id': 'reward_focused',
                'name': '奖励导向组',
                'description': '强调注册奖励和优惠',
                'changes': [
                    '突出显示注册奖励',
                    '添加限时优惠信息',
                    '展示新用户专属权益'
                ]
            },
            {
                'variant_id': 'social_proof',
                'name': '社会证明组',
                'description': '展示用户数量和成功案例',
                'changes': [
                    '显示平台用户数量',
                    '展示成功案例',
                    '添加用户评价和推荐'
                ]
            }
        ]
    
    async def is_demo_workspace(self, workspace_id: str) -> bool:
        """检查是否为演示工作台"""
        if workspace_id.startswith('demo-'):
            return True
        
        result = await self.db.execute(
            select(DemoAccount.id)
            .where(DemoAccount.workspace_id == workspace_id)
        )
        
        return result.scalar_one_or_none() is not None
    
    async def get_demo_account_by_workspace(self, workspace_id: str) -> Optional[DemoAccount]:
        """根据工作台ID获取演示账户"""
        result = await self.db.execute(
            select(DemoAccount)
            .where(DemoAccount.workspace_id == workspace_id)
        )
        
        return result.scalar_one_or_none()