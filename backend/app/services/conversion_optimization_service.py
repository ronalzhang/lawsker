"""
Conversion Optimization Service
用户注册转化率优化服务

This service tracks and optimizes user registration conversion rates
to achieve the 40% improvement target.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import json
import logging

from ..core.database import get_db
from ..models.user import User
from ..models.unified_auth import WorkspaceMapping

logger = logging.getLogger(__name__)


class ConversionOptimizationService:
    """用户注册转化率优化服务"""
    
    def __init__(self, db: Session):
        self.db = db
        
    async def track_conversion_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """跟踪转化事件"""
        
        event_data = {
            'event_type': event_type,
            'user_id': user_id,
            'session_id': session_id,
            'timestamp': datetime.utcnow(),
            'metadata': metadata or {}
        }
        
        # Store in database (you may want to create a conversion_events table)
        # For now, we'll log it
        logger.info(f"Conversion Event: {event_type}", extra=event_data)
        
        return event_data
    
    async def get_conversion_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取转化率指标"""
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Get registration data
        total_visitors = self._get_total_visitors(start_date, end_date)
        total_registrations = self._get_total_registrations(start_date, end_date)
        demo_users = self._get_demo_users(start_date, end_date)
        demo_conversions = self._get_demo_conversions(start_date, end_date)
        
        # Calculate conversion rates
        registration_rate = (total_registrations / total_visitors * 100) if total_visitors > 0 else 0
        demo_to_registration_rate = (demo_conversions / demo_users * 100) if demo_users > 0 else 0
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'metrics': {
                'total_visitors': total_visitors,
                'total_registrations': total_registrations,
                'demo_users': demo_users,
                'demo_conversions': demo_conversions,
                'registration_conversion_rate': round(registration_rate, 2),
                'demo_conversion_rate': round(demo_to_registration_rate, 2)
            },
            'targets': {
                'registration_rate_target': 15.0,  # Assuming baseline of ~10%, target 40% improvement = 14%
                'demo_conversion_target': 30.0
            }
        }
    
    def _get_total_visitors(self, start_date: datetime, end_date: datetime) -> int:
        """获取总访问者数量 (模拟数据，实际应从访问日志获取)"""
        # This would typically come from web analytics or access logs
        # For now, we'll estimate based on registrations
        registrations = self._get_total_registrations(start_date, end_date)
        # Assume ~10% conversion rate as baseline
        return max(registrations * 10, 100)
    
    def _get_total_registrations(self, start_date: datetime, end_date: datetime) -> int:
        """获取总注册数量"""
        return self.db.query(User).filter(
            and_(
                User.created_at >= start_date,
                User.created_at <= end_date,
                User.account_type.in_(['user', 'lawyer'])
            )
        ).count()
    
    def _get_demo_users(self, start_date: datetime, end_date: datetime) -> int:
        """获取演示用户数量 (模拟数据)"""
        # This would come from demo access logs
        # For now, estimate based on registrations
        registrations = self._get_total_registrations(start_date, end_date)
        return registrations * 3  # Assume 3 demo users per registration
    
    def _get_demo_conversions(self, start_date: datetime, end_date: datetime) -> int:
        """获取演示用户转化数量"""
        # Users who registered after using demo
        return self.db.query(User).filter(
            and_(
                User.created_at >= start_date,
                User.created_at <= end_date,
                User.registration_source == 'demo_conversion'
            )
        ).count()
    
    async def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """获取优化建议"""
        
        metrics = await self.get_conversion_metrics()
        recommendations = []
        
        current_rate = metrics['metrics']['registration_conversion_rate']
        target_rate = metrics['targets']['registration_rate_target']
        
        if current_rate < target_rate:
            gap = target_rate - current_rate
            recommendations.extend([
                {
                    'type': 'ui_optimization',
                    'priority': 'high',
                    'title': '简化注册流程',
                    'description': f'当前转化率 {current_rate}%，目标 {target_rate}%，需要提升 {gap:.1f}%',
                    'actions': [
                        '将注册流程从3步简化为2步',
                        '在注册表单中直接选择身份类型',
                        '优化表单字段和验证提示'
                    ]
                },
                {
                    'type': 'demo_optimization',
                    'priority': 'high',
                    'title': '增强演示账户体验',
                    'description': '提升演示账户的可见性和转化率',
                    'actions': [
                        '将演示按钮放在更显眼的位置',
                        '添加演示账户功能介绍',
                        '优化演示到注册的引导流程'
                    ]
                },
                {
                    'type': 'trust_building',
                    'priority': 'medium',
                    'title': '增加信任指标',
                    'description': '通过信任指标提升用户注册意愿',
                    'actions': [
                        '显示用户数量和律师数量',
                        '添加安全认证标识',
                        '展示系统可用性指标'
                    ]
                }
            ])
        
        demo_rate = metrics['metrics']['demo_conversion_rate']
        demo_target = metrics['targets']['demo_conversion_target']
        
        if demo_rate < demo_target:
            recommendations.append({
                'type': 'demo_conversion',
                'priority': 'medium',
                'title': '优化演示转化',
                'description': f'演示转化率 {demo_rate}%，目标 {demo_target}%',
                'actions': [
                    '在演示环境中添加注册引导',
                    '限制演示功能以促进注册',
                    '添加演示结束后的注册提醒'
                ]
            })
        
        return recommendations
    
    async def generate_conversion_report(self) -> Dict[str, Any]:
        """生成转化率报告"""
        
        # Get metrics for different time periods
        current_month = await self.get_conversion_metrics(
            datetime.utcnow().replace(day=1),
            datetime.utcnow()
        )
        
        last_month = await self.get_conversion_metrics(
            (datetime.utcnow().replace(day=1) - timedelta(days=1)).replace(day=1),
            datetime.utcnow().replace(day=1) - timedelta(days=1)
        )
        
        # Calculate improvement
        current_rate = current_month['metrics']['registration_conversion_rate']
        last_rate = last_month['metrics']['registration_conversion_rate']
        improvement = ((current_rate - last_rate) / last_rate * 100) if last_rate > 0 else 0
        
        # Get recommendations
        recommendations = await self.get_optimization_recommendations()
        
        return {
            'report_date': datetime.utcnow().isoformat(),
            'current_month': current_month,
            'last_month': last_month,
            'improvement': {
                'percentage': round(improvement, 2),
                'target_achieved': improvement >= 40.0,
                'target_progress': min(improvement / 40.0 * 100, 100)
            },
            'recommendations': recommendations,
            'next_actions': [
                '实施优化建议',
                '监控转化率变化',
                'A/B测试不同的注册流程',
                '收集用户反馈'
            ]
        }
    
    async def track_ab_test_result(
        self,
        test_name: str,
        variant: str,
        user_id: str,
        converted: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """跟踪A/B测试结果"""
        
        result = {
            'test_name': test_name,
            'variant': variant,
            'user_id': user_id,
            'converted': converted,
            'timestamp': datetime.utcnow(),
            'metadata': metadata or {}
        }
        
        # Log the A/B test result
        logger.info(f"A/B Test Result: {test_name} - {variant}", extra=result)
        
        return result
    
    async def get_registration_funnel_analysis(self) -> Dict[str, Any]:
        """获取注册漏斗分析"""
        
        # Simulate funnel data (in real implementation, this would come from tracking)
        funnel_data = {
            'landing_page_views': 1000,
            'registration_form_views': 600,
            'form_submissions': 180,
            'email_verifications': 150,
            'identity_selections': 140,
            'completed_registrations': 120
        }
        
        # Calculate conversion rates for each step
        funnel_rates = {}
        prev_step = None
        prev_value = None
        
        for step, value in funnel_data.items():
            if prev_step:
                rate = (value / prev_value * 100) if prev_value > 0 else 0
                funnel_rates[f"{prev_step}_to_{step}"] = round(rate, 2)
            prev_step = step
            prev_value = value
        
        # Overall conversion rate
        overall_rate = (funnel_data['completed_registrations'] / funnel_data['landing_page_views'] * 100)
        
        return {
            'funnel_data': funnel_data,
            'conversion_rates': funnel_rates,
            'overall_conversion_rate': round(overall_rate, 2),
            'bottlenecks': [
                {
                    'step': 'landing_to_form',
                    'rate': funnel_rates.get('landing_page_views_to_registration_form_views', 0),
                    'improvement_potential': 'high' if funnel_rates.get('landing_page_views_to_registration_form_views', 0) < 70 else 'medium'
                },
                {
                    'step': 'form_to_submission',
                    'rate': funnel_rates.get('registration_form_views_to_form_submissions', 0),
                    'improvement_potential': 'high' if funnel_rates.get('registration_form_views_to_form_submissions', 0) < 40 else 'medium'
                }
            ]
        }


# Utility functions for conversion optimization
def calculate_conversion_improvement(baseline_rate: float, current_rate: float) -> float:
    """计算转化率改进百分比"""
    if baseline_rate <= 0:
        return 0
    return ((current_rate - baseline_rate) / baseline_rate) * 100


def get_conversion_optimization_config() -> Dict[str, Any]:
    """获取转化率优化配置"""
    return {
        'target_improvement': 40.0,  # 40% improvement target
        'baseline_conversion_rate': 10.0,  # Assumed baseline
        'target_conversion_rate': 14.0,  # 40% improvement
        'demo_conversion_target': 30.0,
        'ab_test_variants': [
            'original',
            'streamlined_2_step',
            'demo_prominent',
            'trust_indicators'
        ],
        'tracking_events': [
            'page_load',
            'demo_start',
            'demo_success',
            'registration_attempt',
            'registration_success',
            'form_field_focus',
            'switch_to_login',
            'switch_to_register'
        ]
    }