"""
律师会员转化优化服务
专门用于实现20%付费会员转化率目标
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from decimal import Decimal
from uuid import UUID
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException

from app.core.database import get_db
from app.models.user import User
from app.services.lawyer_membership_service import LawyerMembershipService
from app.services.lawyer_points_engine import LawyerPointsEngine

logger = logging.getLogger(__name__)


class LawyerMembershipConversionService:
    """律师会员转化优化服务 - 实现20%转化率目标"""
    
    def __init__(self, membership_service: LawyerMembershipService, points_engine: LawyerPointsEngine):
        self.membership_service = membership_service
        self.points_engine = points_engine
    
    async def track_conversion_event(
        self, 
        lawyer_id: UUID, 
        event_type: str, 
        context: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """跟踪转化事件"""
        try:
            event_data = {
                'lawyer_id': str(lawyer_id),
                'event_type': event_type,
                'event_context': json.dumps(context),
                'timestamp': datetime.now(),
                'session_id': context.get('session_id'),
                'user_agent': context.get('user_agent'),
                'referrer': context.get('referrer')
            }
            
            # 记录转化事件
            db.execute("""
                INSERT INTO lawyer_conversion_events 
                (lawyer_id, event_type, event_context, timestamp, session_id, user_agent, referrer)
                VALUES (%(lawyer_id)s, %(event_type)s, %(event_context)s, %(timestamp)s, 
                        %(session_id)s, %(user_agent)s, %(referrer)s)
            """, event_data)
            
            db.commit()
            
            logger.info(f"转化事件记录成功: {event_type} for lawyer {lawyer_id}")
            
            return {
                'success': True,
                'event_type': event_type,
                'timestamp': event_data['timestamp'].isoformat()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"跟踪转化事件失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"跟踪转化事件失败: {str(e)}")
    
    async def get_conversion_metrics(self, db: Session, days: int = 30) -> Dict[str, Any]:
        """获取转化率指标"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # 获取基础数据
            stats = db.execute("""
                SELECT 
                    COUNT(DISTINCT lm.lawyer_id) as total_lawyers,
                    COUNT(DISTINCT CASE WHEN lm.membership_type != 'free' THEN lm.lawyer_id END) as paid_lawyers,
                    COUNT(DISTINCT CASE WHEN lm.membership_type = 'free' THEN lm.lawyer_id END) as free_lawyers,
                    COUNT(DISTINCT CASE WHEN lm.membership_type = 'professional' THEN lm.lawyer_id END) as professional_lawyers,
                    COUNT(DISTINCT CASE WHEN lm.membership_type = 'enterprise' THEN lm.lawyer_id END) as enterprise_lawyers
                FROM lawyer_memberships lm
                WHERE lm.created_at >= %s
            """, (start_date,)).fetchone()
            
            total_lawyers = stats['total_lawyers'] or 0
            paid_lawyers = stats['paid_lawyers'] or 0
            free_lawyers = stats['free_lawyers'] or 0
            
            # 计算转化率
            conversion_rate = (paid_lawyers / total_lawyers * 100) if total_lawyers > 0 else 0
            
            # 获取转化趋势数据
            trend_data = await self._get_conversion_trend(db, days)
            
            # 获取转化漏斗数据
            funnel_data = await self._get_conversion_funnel(db, days)
            
            # 计算目标达成情况
            target_achievement = {
                'current_rate': round(conversion_rate, 2),
                'target_rate': 20.0,
                'achievement_percentage': min(100, round(conversion_rate / 20 * 100, 2)),
                'gap_to_target': max(0, 20 - conversion_rate),
                'status': 'on_track' if conversion_rate >= 15 else 'needs_attention' if conversion_rate >= 10 else 'critical'
            }
            
            return {
                'period': f'{days}天',
                'total_lawyers': total_lawyers,
                'paid_lawyers': paid_lawyers,
                'free_lawyers': free_lawyers,
                'professional_lawyers': stats['professional_lawyers'] or 0,
                'enterprise_lawyers': stats['enterprise_lawyers'] or 0,
                'conversion_rate': round(conversion_rate, 2),
                'target_achievement': target_achievement,
                'trend_data': trend_data,
                'funnel_data': funnel_data,
                'updated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取转化率指标失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取转化率指标失败: {str(e)}")
    
    async def _get_conversion_trend(self, db: Session, days: int) -> List[Dict[str, Any]]:
        """获取转化率趋势数据"""
        try:
            trend_data = []
            
            for i in range(days):
                check_date = date.today() - timedelta(days=i)
                
                # 获取当日数据
                daily_stats = db.execute("""
                    SELECT 
                        COUNT(DISTINCT lm.lawyer_id) as total_lawyers,
                        COUNT(DISTINCT CASE WHEN lm.membership_type != 'free' THEN lm.lawyer_id END) as paid_lawyers
                    FROM lawyer_memberships lm
                    WHERE DATE(lm.created_at) = %s
                """, (check_date,)).fetchone()
                
                total = daily_stats['total_lawyers'] or 0
                paid = daily_stats['paid_lawyers'] or 0
                rate = (paid / total * 100) if total > 0 else 0
                
                trend_data.append({
                    'date': check_date.isoformat(),
                    'total_lawyers': total,
                    'paid_lawyers': paid,
                    'conversion_rate': round(rate, 2)
                })
            
            return list(reversed(trend_data))
            
        except Exception as e:
            logger.error(f"获取转化趋势失败: {str(e)}")
            return []
    
    async def _get_conversion_funnel(self, db: Session, days: int) -> Dict[str, Any]:
        """获取转化漏斗数据"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # 转化漏斗步骤
            funnel_steps = db.execute("""
                SELECT 
                    COUNT(DISTINCT CASE WHEN lce.event_type = 'membership_page_view' THEN lce.lawyer_id END) as viewed_membership,
                    COUNT(DISTINCT CASE WHEN lce.event_type = 'upgrade_button_click' THEN lce.lawyer_id END) as clicked_upgrade,
                    COUNT(DISTINCT CASE WHEN lce.event_type = 'payment_initiated' THEN lce.lawyer_id END) as initiated_payment,
                    COUNT(DISTINCT CASE WHEN lce.event_type = 'payment_completed' THEN lce.lawyer_id END) as completed_payment,
                    COUNT(DISTINCT lm.lawyer_id) as total_free_lawyers
                FROM lawyer_memberships lm
                LEFT JOIN lawyer_conversion_events lce ON lm.lawyer_id = lce.lawyer_id 
                    AND lce.timestamp >= %s
                WHERE lm.membership_type = 'free'
                    AND lm.created_at >= %s
            """, (start_date, start_date)).fetchone()
            
            total_free = funnel_steps['total_free_lawyers'] or 0
            viewed = funnel_steps['viewed_membership'] or 0
            clicked = funnel_steps['clicked_upgrade'] or 0
            initiated = funnel_steps['initiated_payment'] or 0
            completed = funnel_steps['completed_payment'] or 0
            
            return {
                'total_free_lawyers': total_free,
                'viewed_membership_page': viewed,
                'clicked_upgrade_button': clicked,
                'initiated_payment': initiated,
                'completed_payment': completed,
                'conversion_rates': {
                    'view_rate': round(viewed / total_free * 100, 2) if total_free > 0 else 0,
                    'click_rate': round(clicked / viewed * 100, 2) if viewed > 0 else 0,
                    'initiation_rate': round(initiated / clicked * 100, 2) if clicked > 0 else 0,
                    'completion_rate': round(completed / initiated * 100, 2) if initiated > 0 else 0,
                    'overall_rate': round(completed / total_free * 100, 2) if total_free > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"获取转化漏斗失败: {str(e)}")
            return {}
    
    async def get_personalized_upgrade_recommendation(
        self, 
        lawyer_id: UUID, 
        db: Session
    ) -> Dict[str, Any]:
        """获取个性化升级推荐"""
        try:
            # 获取律师当前状态
            membership = await self.membership_service.get_lawyer_membership(lawyer_id, db)
            points_summary = await self.points_engine.get_lawyer_points_summary(lawyer_id, db)
            
            if membership['membership_type'] != 'free':
                return {
                    'recommendation': 'already_paid',
                    'message': '您已经是付费会员，感谢您的支持！'
                }
            
            # 分析律师使用情况
            usage_analysis = await self._analyze_lawyer_usage(lawyer_id, db)
            
            # 生成个性化推荐
            recommendation = await self._generate_upgrade_recommendation(
                membership, points_summary, usage_analysis
            )
            
            return recommendation
            
        except Exception as e:
            logger.error(f"获取个性化升级推荐失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取升级推荐失败: {str(e)}")
    
    async def _analyze_lawyer_usage(self, lawyer_id: UUID, db: Session) -> Dict[str, Any]:
        """分析律师使用情况"""
        try:
            # 获取最近30天的使用数据
            usage_stats = db.execute("""
                SELECT 
                    lld.cases_completed,
                    lld.total_ai_credits_used,
                    lld.total_online_hours,
                    lld.client_rating,
                    lld.current_level,
                    lm.ai_credits_remaining,
                    lm.ai_credits_monthly
                FROM lawyer_level_details lld
                JOIN lawyer_memberships lm ON lld.lawyer_id = lm.lawyer_id
                WHERE lld.lawyer_id = %s
            """, (str(lawyer_id),)).fetchone()
            
            if not usage_stats:
                return {}
            
            # 计算使用强度
            ai_usage_rate = (usage_stats['ai_credits_monthly'] - usage_stats['ai_credits_remaining']) / usage_stats['ai_credits_monthly'] if usage_stats['ai_credits_monthly'] > 0 else 0
            
            return {
                'cases_completed': usage_stats['cases_completed'] or 0,
                'ai_credits_used': usage_stats['total_ai_credits_used'] or 0,
                'ai_usage_rate': round(ai_usage_rate * 100, 2),
                'online_hours': usage_stats['total_online_hours'] or 0,
                'client_rating': float(usage_stats['client_rating'] or 0),
                'current_level': usage_stats['current_level'] or 1,
                'credits_remaining': usage_stats['ai_credits_remaining'] or 0
            }
            
        except Exception as e:
            logger.error(f"分析律师使用情况失败: {str(e)}")
            return {}
    
    async def _generate_upgrade_recommendation(
        self, 
        membership: Dict[str, Any], 
        points_summary: Dict[str, Any], 
        usage_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成升级推荐"""
        try:
            recommendations = []
            
            # 基于AI使用情况推荐
            if usage_analysis.get('ai_usage_rate', 0) > 80:
                recommendations.append({
                    'type': 'high_ai_usage',
                    'priority': 'high',
                    'title': 'AI工具使用频繁',
                    'message': '您的AI Credits使用率已达80%以上，升级专业版可获得500个月度Credits',
                    'recommended_tier': 'professional',
                    'benefits': ['500个AI Credits/月', '2倍积分奖励', '优先客服支持']
                })
            
            # 基于案件数量推荐
            if usage_analysis.get('cases_completed', 0) > 15:
                recommendations.append({
                    'type': 'high_case_volume',
                    'priority': 'high',
                    'title': '案件处理量大',
                    'message': '您已完成多个案件，升级可获得更高的每日案件限制',
                    'recommended_tier': 'professional',
                    'benefits': ['每日15个案件', '2倍积分奖励', '数据分析工具']
                })
            
            # 基于律师等级推荐
            current_level = usage_analysis.get('current_level', 1)
            if current_level >= 5:
                recommendations.append({
                    'type': 'high_level',
                    'priority': 'medium',
                    'title': '律师等级较高',
                    'message': f'您已达到{current_level}级律师，升级企业版可获得3倍积分奖励',
                    'recommended_tier': 'enterprise',
                    'benefits': ['无限案件处理', '3倍积分奖励', 'API接入权限']
                })
            
            # 基于客户评分推荐
            if usage_analysis.get('client_rating', 0) >= 4.5:
                recommendations.append({
                    'type': 'high_rating',
                    'priority': 'medium',
                    'title': '客户评价优秀',
                    'message': '您的客户评分很高，升级可获得更多优质案件推荐',
                    'recommended_tier': 'professional',
                    'benefits': ['优质案件优先推荐', '专业认证标识', '营销工具支持']
                })
            
            # 如果没有特定推荐，给出通用推荐
            if not recommendations:
                recommendations.append({
                    'type': 'general',
                    'priority': 'low',
                    'title': '解锁更多功能',
                    'message': '升级专业版，享受更多专业功能和服务',
                    'recommended_tier': 'professional',
                    'benefits': ['500个AI Credits/月', '每日15个案件', '2倍积分奖励']
                })
            
            # 排序推荐（按优先级）
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
            
            # 选择最佳推荐
            best_recommendation = recommendations[0]
            
            # 添加优惠信息
            discount_info = await self._get_current_discount_info(best_recommendation['recommended_tier'])
            
            return {
                'recommendation_type': best_recommendation['type'],
                'priority': best_recommendation['priority'],
                'recommended_tier': best_recommendation['recommended_tier'],
                'title': best_recommendation['title'],
                'message': best_recommendation['message'],
                'benefits': best_recommendation['benefits'],
                'discount_info': discount_info,
                'all_recommendations': recommendations,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"生成升级推荐失败: {str(e)}")
            return {
                'recommendation_type': 'error',
                'message': '暂时无法生成推荐，请稍后再试'
            }
    
    async def _get_current_discount_info(self, tier: str) -> Dict[str, Any]:
        """获取当前优惠信息"""
        # 这里可以集成实际的优惠系统
        # 目前返回模拟数据
        discounts = {
            'professional': {
                'has_discount': True,
                'discount_percentage': 15,
                'original_price': 899,
                'discounted_price': 764,
                'discount_reason': '新用户首月优惠',
                'expires_at': (datetime.now() + timedelta(days=7)).isoformat()
            },
            'enterprise': {
                'has_discount': True,
                'discount_percentage': 10,
                'original_price': 2999,
                'discounted_price': 2699,
                'discount_reason': '高级律师专享优惠',
                'expires_at': (datetime.now() + timedelta(days=14)).isoformat()
            }
        }
        
        return discounts.get(tier, {'has_discount': False})
    
    async def simulate_conversion_improvement(
        self, 
        db: Session,
        improvement_strategies: List[str]
    ) -> Dict[str, Any]:
        """模拟转化率改进效果"""
        try:
            # 获取当前转化率
            current_metrics = await self.get_conversion_metrics(db, 30)
            current_rate = current_metrics['conversion_rate']
            
            # 预定义改进策略效果
            strategy_effects = {
                'personalized_recommendations': 2.5,  # 个性化推荐 +2.5%
                'discount_campaigns': 3.0,           # 优惠活动 +3.0%
                'email_marketing': 1.8,              # 邮件营销 +1.8%
                'in_app_notifications': 1.5,         # 应用内通知 +1.5%
                'social_proof': 2.0,                 # 社会证明 +2.0%
                'free_trial_extension': 2.2,         # 免费试用延长 +2.2%
                'onboarding_optimization': 1.3,      # 入门优化 +1.3%
                'ui_ux_improvements': 1.0            # UI/UX改进 +1.0%
            }
            
            # 计算总改进效果（有递减效应）
            total_improvement = 0
            for i, strategy in enumerate(improvement_strategies):
                effect = strategy_effects.get(strategy, 0)
                # 递减效应：后续策略效果递减
                diminishing_factor = 0.8 ** i
                total_improvement += effect * diminishing_factor
            
            # 计算预期转化率
            projected_rate = min(25, current_rate + total_improvement)  # 最高25%
            
            # 计算业务影响
            total_lawyers = current_metrics['total_lawyers']
            current_paid = current_metrics['paid_lawyers']
            projected_paid = int(total_lawyers * projected_rate / 100)
            additional_paid = projected_paid - current_paid
            
            # 收入影响（假设平均客单价）
            avg_monthly_revenue_per_lawyer = 1500  # 平均每个付费律师月收入
            additional_monthly_revenue = additional_paid * avg_monthly_revenue_per_lawyer
            annual_revenue_impact = additional_monthly_revenue * 12
            
            return {
                'current_conversion_rate': current_rate,
                'projected_conversion_rate': round(projected_rate, 2),
                'improvement': round(projected_rate - current_rate, 2),
                'target_achievement': round(projected_rate / 20 * 100, 2),
                'business_impact': {
                    'additional_paid_lawyers': additional_paid,
                    'additional_monthly_revenue': additional_monthly_revenue,
                    'annual_revenue_impact': annual_revenue_impact,
                    'roi_estimate': round(annual_revenue_impact / 100000, 2)  # 假设投入10万
                },
                'strategies_applied': improvement_strategies,
                'strategy_effects': {
                    strategy: strategy_effects.get(strategy, 0) 
                    for strategy in improvement_strategies
                },
                'simulation_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"模拟转化率改进失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"模拟转化率改进失败: {str(e)}")
    
    async def get_conversion_optimization_suggestions(self, db: Session) -> List[Dict[str, Any]]:
        """获取转化率优化建议"""
        try:
            # 获取当前指标
            metrics = await self.get_conversion_metrics(db, 30)
            current_rate = metrics['conversion_rate']
            
            suggestions = []
            
            # 基于当前转化率给出建议
            if current_rate < 10:
                suggestions.extend([
                    {
                        'priority': 'critical',
                        'category': 'user_experience',
                        'title': '优化会员页面体验',
                        'description': '当前转化率较低，建议重新设计会员升级页面，突出价值主张',
                        'expected_impact': '+3-5%',
                        'effort': 'high',
                        'timeline': '2-3周'
                    },
                    {
                        'priority': 'critical',
                        'category': 'pricing',
                        'title': '推出限时优惠活动',
                        'description': '通过首月折扣或免费试用期吸引用户升级',
                        'expected_impact': '+2-4%',
                        'effort': 'medium',
                        'timeline': '1周'
                    }
                ])
            elif current_rate < 15:
                suggestions.extend([
                    {
                        'priority': 'high',
                        'category': 'personalization',
                        'title': '实施个性化推荐',
                        'description': '基于律师使用行为和等级推荐合适的会员套餐',
                        'expected_impact': '+2-3%',
                        'effort': 'medium',
                        'timeline': '1-2周'
                    },
                    {
                        'priority': 'high',
                        'category': 'communication',
                        'title': '优化邮件营销',
                        'description': '发送个性化的升级邮件，展示升级后的具体收益',
                        'expected_impact': '+1-2%',
                        'effort': 'low',
                        'timeline': '1周'
                    }
                ])
            else:
                suggestions.extend([
                    {
                        'priority': 'medium',
                        'category': 'retention',
                        'title': '提升用户粘性',
                        'description': '通过积分系统和等级奖励增加用户活跃度',
                        'expected_impact': '+1-2%',
                        'effort': 'medium',
                        'timeline': '2-3周'
                    },
                    {
                        'priority': 'medium',
                        'category': 'social_proof',
                        'title': '添加社会证明元素',
                        'description': '展示其他律师升级后的成功案例和收益',
                        'expected_impact': '+1%',
                        'effort': 'low',
                        'timeline': '1周'
                    }
                ])
            
            # 通用建议
            suggestions.extend([
                {
                    'priority': 'low',
                    'category': 'analytics',
                    'title': '加强数据分析',
                    'description': '深入分析用户行为，识别转化瓶颈',
                    'expected_impact': '+0.5-1%',
                    'effort': 'low',
                    'timeline': '持续进行'
                },
                {
                    'priority': 'low',
                    'category': 'testing',
                    'title': '进行A/B测试',
                    'description': '测试不同的页面设计、文案和价格策略',
                    'expected_impact': '+0.5-2%',
                    'effort': 'medium',
                    'timeline': '持续进行'
                }
            ])
            
            return suggestions
            
        except Exception as e:
            logger.error(f"获取转化率优化建议失败: {str(e)}")
            return []


# 服务实例工厂函数
def create_lawyer_membership_conversion_service(
    membership_service: LawyerMembershipService,
    points_engine: LawyerPointsEngine
) -> LawyerMembershipConversionService:
    """创建律师会员转化优化服务实例"""
    return LawyerMembershipConversionService(membership_service, points_engine)