"""
律师会员订阅服务
实现免费引流模式和付费会员升级系统
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException

from app.core.database import get_db
from app.models.user import User
from app.services.payment_service import WeChatPayService
from app.services.config_service import SystemConfigService

logger = logging.getLogger(__name__)


class LawyerMembershipService:
    """律师会员服务 - 免费引流 + 付费升级"""
    
    # 会员套餐配置
    MEMBERSHIP_TIERS = {
        'free': {
            'name': '基础律师版（免费）',
            'monthly_fee': 0,
            'ai_credits_monthly': 20,
            'daily_case_limit': 2,
            'point_multiplier': 1.0,
            'features': ['基础案件', '基础AI工具', '邮件支持'],
            'description': '免费版本，适合新手律师体验平台功能'
        },
        'professional': {
            'name': '专业律师版',
            'monthly_fee': 899,
            'ai_credits_monthly': 500,
            'daily_case_limit': 15,
            'point_multiplier': 2.0,
            'features': ['所有案件类型', '高级AI工具', '优先支持', '数据分析'],
            'description': '专业版本，适合活跃律师提升效率和收入'
        },
        'enterprise': {
            'name': '企业律师版',
            'monthly_fee': 2999,
            'ai_credits_monthly': 2000,
            'daily_case_limit': -1,  # 无限制
            'point_multiplier': 3.0,
            'features': ['企业客户案件', '全部AI工具', '专属支持', 'API接入'],
            'description': '企业版本，适合律师事务所和高级律师'
        }
    }
    
    def __init__(self, config_service: SystemConfigService, payment_service: WeChatPayService):
        self.config_service = config_service
        self.payment_service = payment_service
    
    async def assign_free_membership(self, lawyer_id: UUID, db: Session) -> Dict[str, Any]:
        """律师认证通过后自动分配免费会员"""
        try:
            # 检查律师是否已有会员记录
            existing_membership = db.execute(
                "SELECT * FROM lawyer_memberships WHERE lawyer_id = %s",
                (str(lawyer_id),)
            ).fetchone()
            
            if existing_membership:
                logger.info(f"律师 {lawyer_id} 已有会员记录，跳过分配")
                return self._format_membership_response(existing_membership)
            
            # 创建免费会员记录
            membership_data = {
                'lawyer_id': str(lawyer_id),
                'membership_type': 'free',
                'start_date': date.today(),
                'end_date': date.today() + timedelta(days=365*10),  # 10年有效期
                'benefits': self.MEMBERSHIP_TIERS['free'],
                'daily_case_limit': self.MEMBERSHIP_TIERS['free']['daily_case_limit'],
                'monthly_amount_limit': 50000,  # 5万元月限额
                'ai_credits_monthly': self.MEMBERSHIP_TIERS['free']['ai_credits_monthly'],
                'ai_credits_remaining': self.MEMBERSHIP_TIERS['free']['ai_credits_monthly'],
                'ai_credits_used': 0,
                'auto_renewal': True,
                'payment_amount': 0
            }
            
            # 插入数据库
            db.execute("""
                INSERT INTO lawyer_memberships 
                (lawyer_id, membership_type, start_date, end_date, benefits, 
                 daily_case_limit, monthly_amount_limit, ai_credits_monthly, 
                 ai_credits_remaining, ai_credits_used, auto_renewal, payment_amount)
                VALUES (%(lawyer_id)s, %(membership_type)s, %(start_date)s, %(end_date)s, 
                        %(benefits)s, %(daily_case_limit)s, %(monthly_amount_limit)s, 
                        %(ai_credits_monthly)s, %(ai_credits_remaining)s, %(ai_credits_used)s, 
                        %(auto_renewal)s, %(payment_amount)s)
            """, membership_data)
            
            # 初始化律师等级数据
            await self._initialize_lawyer_level_details(lawyer_id, db)
            
            db.commit()
            
            logger.info(f"成功为律师 {lawyer_id} 分配免费会员")
            
            return {
                'membership_type': 'free',
                'tier_info': self.MEMBERSHIP_TIERS['free'],
                'start_date': membership_data['start_date'].isoformat(),
                'end_date': membership_data['end_date'].isoformat(),
                'ai_credits_remaining': membership_data['ai_credits_remaining'],
                'daily_case_limit': membership_data['daily_case_limit']
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"分配免费会员失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"分配免费会员失败: {str(e)}")
    
    async def _initialize_lawyer_level_details(self, lawyer_id: UUID, db: Session):
        """初始化律师等级详情"""
        try:
            # 检查是否已有等级记录
            existing_level = db.execute(
                "SELECT * FROM lawyer_level_details WHERE lawyer_id = %s",
                (str(lawyer_id),)
            ).fetchone()
            
            if existing_level:
                return
            
            # 创建初始等级记录
            level_data = {
                'lawyer_id': str(lawyer_id),
                'current_level': 1,
                'level_points': 0,
                'experience_points': 0,
                'cases_completed': 0,
                'cases_won': 0,
                'cases_failed': 0,
                'success_rate': 0,
                'client_rating': 0,
                'total_revenue': 0,
                'total_online_hours': 0,
                'total_cases_amount': 0,
                'total_ai_credits_used': 0,
                'total_paid_amount': 0,
                'response_time_avg': 0,
                'case_completion_speed': 0,
                'quality_score': 0,
                'upgrade_eligible': False,
                'downgrade_risk': False,
                'level_change_history': []
            }
            
            db.execute("""
                INSERT INTO lawyer_level_details 
                (lawyer_id, current_level, level_points, experience_points, cases_completed,
                 cases_won, cases_failed, success_rate, client_rating, total_revenue,
                 total_online_hours, total_cases_amount, total_ai_credits_used, 
                 total_paid_amount, response_time_avg, case_completion_speed, 
                 quality_score, upgrade_eligible, downgrade_risk, level_change_history)
                VALUES (%(lawyer_id)s, %(current_level)s, %(level_points)s, %(experience_points)s,
                        %(cases_completed)s, %(cases_won)s, %(cases_failed)s, %(success_rate)s,
                        %(client_rating)s, %(total_revenue)s, %(total_online_hours)s,
                        %(total_cases_amount)s, %(total_ai_credits_used)s, %(total_paid_amount)s,
                        %(response_time_avg)s, %(case_completion_speed)s, %(quality_score)s,
                        %(upgrade_eligible)s, %(downgrade_risk)s, %(level_change_history)s)
            """, level_data)
            
        except Exception as e:
            logger.error(f"初始化律师等级详情失败: {str(e)}")
            raise
    
    async def get_lawyer_membership(self, lawyer_id: UUID, db: Session) -> Dict[str, Any]:
        """获取律师会员信息"""
        try:
            membership = db.execute(
                "SELECT * FROM lawyer_memberships WHERE lawyer_id = %s",
                (str(lawyer_id),)
            ).fetchone()
            
            if not membership:
                # 如果没有会员记录，自动分配免费会员
                return await self.assign_free_membership(lawyer_id, db)
            
            return self._format_membership_response(membership)
            
        except Exception as e:
            logger.error(f"获取律师会员信息失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取会员信息失败: {str(e)}")
    
    def _format_membership_response(self, membership) -> Dict[str, Any]:
        """格式化会员信息响应"""
        membership_type = membership['membership_type'] if isinstance(membership, dict) else membership.membership_type
        tier_config = self.MEMBERSHIP_TIERS.get(membership_type, self.MEMBERSHIP_TIERS['free'])
        
        return {
            'membership_type': membership_type,
            'tier_info': tier_config,
            'start_date': membership['start_date'] if isinstance(membership, dict) else membership.start_date.isoformat(),
            'end_date': membership['end_date'] if isinstance(membership, dict) else membership.end_date.isoformat(),
            'ai_credits_monthly': membership['ai_credits_monthly'] if isinstance(membership, dict) else membership.ai_credits_monthly,
            'ai_credits_remaining': membership['ai_credits_remaining'] if isinstance(membership, dict) else membership.ai_credits_remaining,
            'ai_credits_used': membership['ai_credits_used'] if isinstance(membership, dict) else membership.ai_credits_used,
            'daily_case_limit': membership['daily_case_limit'] if isinstance(membership, dict) else membership.daily_case_limit,
            'monthly_amount_limit': membership['monthly_amount_limit'] if isinstance(membership, dict) else membership.monthly_amount_limit,
            'auto_renewal': membership['auto_renewal'] if isinstance(membership, dict) else membership.auto_renewal,
            'payment_amount': float(membership['payment_amount']) if isinstance(membership, dict) else float(membership.payment_amount),
            'point_multiplier': tier_config['point_multiplier']
        }
    
    async def upgrade_membership(self, lawyer_id: UUID, target_tier: str, db: Session) -> Dict[str, Any]:
        """会员升级"""
        try:
            if target_tier not in self.MEMBERSHIP_TIERS:
                raise HTTPException(status_code=400, detail="无效的会员类型")
            
            if target_tier == 'free':
                raise HTTPException(status_code=400, detail="不能升级到免费版")
            
            tier_config = self.MEMBERSHIP_TIERS[target_tier]
            
            # 获取当前会员信息
            current_membership = await self.get_lawyer_membership(lawyer_id, db)
            
            if current_membership['membership_type'] == target_tier:
                raise HTTPException(status_code=400, detail="已经是该会员类型")
            
            # 创建支付订单
            payment_order = await self._create_membership_payment_order(
                lawyer_id, tier_config['monthly_fee'], target_tier, db
            )
            
            return {
                'payment_order': payment_order,
                'target_tier': target_tier,
                'tier_info': tier_config,
                'upgrade_benefits': self._get_upgrade_benefits(current_membership['membership_type'], target_tier)
            }
            
        except Exception as e:
            logger.error(f"会员升级失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"会员升级失败: {str(e)}")
    
    async def _create_membership_payment_order(
        self, 
        lawyer_id: UUID, 
        amount: float, 
        membership_type: str, 
        db: Session
    ) -> Dict[str, Any]:
        """创建会员支付订单"""
        try:
            # 这里简化处理，实际应该调用支付服务
            order_data = {
                'order_id': f"membership_{lawyer_id}_{int(datetime.now().timestamp())}",
                'lawyer_id': str(lawyer_id),
                'membership_type': membership_type,
                'amount': amount,
                'description': f"律师会员升级 - {self.MEMBERSHIP_TIERS[membership_type]['name']}",
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            
            # 实际项目中应该调用支付服务创建订单
            # payment_order = await self.payment_service.create_membership_order(...)
            
            return order_data
            
        except Exception as e:
            logger.error(f"创建会员支付订单失败: {str(e)}")
            raise
    
    def _get_upgrade_benefits(self, current_tier: str, target_tier: str) -> Dict[str, Any]:
        """获取升级收益对比"""
        current_config = self.MEMBERSHIP_TIERS[current_tier]
        target_config = self.MEMBERSHIP_TIERS[target_tier]
        
        return {
            'ai_credits_increase': target_config['ai_credits_monthly'] - current_config['ai_credits_monthly'],
            'case_limit_increase': target_config['daily_case_limit'] - current_config['daily_case_limit'] if target_config['daily_case_limit'] != -1 else '无限制',
            'point_multiplier_increase': target_config['point_multiplier'] - current_config['point_multiplier'],
            'new_features': list(set(target_config['features']) - set(current_config['features']))
        }
    
    async def process_membership_payment_success(
        self, 
        lawyer_id: UUID, 
        membership_type: str, 
        payment_amount: float,
        db: Session
    ) -> Dict[str, Any]:
        """处理会员支付成功"""
        try:
            tier_config = self.MEMBERSHIP_TIERS[membership_type]
            
            # 更新会员记录
            update_data = {
                'membership_type': membership_type,
                'start_date': date.today(),
                'end_date': date.today() + timedelta(days=30),  # 月付
                'benefits': tier_config,
                'daily_case_limit': tier_config['daily_case_limit'],
                'monthly_amount_limit': self._get_monthly_amount_limit(membership_type),
                'ai_credits_monthly': tier_config['ai_credits_monthly'],
                'ai_credits_remaining': tier_config['ai_credits_monthly'],
                'payment_amount': payment_amount,
                'updated_at': datetime.now()
            }
            
            db.execute("""
                UPDATE lawyer_memberships 
                SET membership_type = %(membership_type)s,
                    start_date = %(start_date)s,
                    end_date = %(end_date)s,
                    benefits = %(benefits)s,
                    daily_case_limit = %(daily_case_limit)s,
                    monthly_amount_limit = %(monthly_amount_limit)s,
                    ai_credits_monthly = %(ai_credits_monthly)s,
                    ai_credits_remaining = %(ai_credits_remaining)s,
                    payment_amount = %(payment_amount)s,
                    updated_at = %(updated_at)s
                WHERE lawyer_id = %(lawyer_id)s
            """, {**update_data, 'lawyer_id': str(lawyer_id)})
            
            db.commit()
            
            logger.info(f"律师 {lawyer_id} 成功升级到 {membership_type} 会员")
            
            return {
                'success': True,
                'membership_type': membership_type,
                'tier_info': tier_config,
                'upgrade_date': update_data['start_date'].isoformat(),
                'next_billing_date': update_data['end_date'].isoformat()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"处理会员支付成功失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"处理支付成功失败: {str(e)}")
    
    def _get_monthly_amount_limit(self, membership_type: str) -> float:
        """根据会员类型获取月限额"""
        limits = {
            'free': 50000,      # 5万
            'professional': 200000,  # 20万
            'enterprise': 1000000    # 100万
        }
        return limits.get(membership_type, 50000)
    
    async def get_membership_tiers(self) -> Dict[str, Any]:
        """获取所有会员套餐信息"""
        return {
            'tiers': self.MEMBERSHIP_TIERS,
            'comparison': self._generate_tier_comparison()
        }
    
    def _generate_tier_comparison(self) -> List[Dict[str, Any]]:
        """生成会员套餐对比表"""
        comparison_features = [
            {'feature': '月费', 'free': '免费', 'professional': '¥899', 'enterprise': '¥2999'},
            {'feature': 'AI Credits', 'free': '20/月', 'professional': '500/月', 'enterprise': '2000/月'},
            {'feature': '每日案件限制', 'free': '2个', 'professional': '15个', 'enterprise': '无限制'},
            {'feature': '积分倍数', 'free': '1倍', 'professional': '2倍', 'enterprise': '3倍'},
            {'feature': '客服支持', 'free': '邮件支持', 'professional': '优先支持', 'enterprise': '专属支持'},
            {'feature': 'API接入', 'free': '❌', 'professional': '❌', 'enterprise': '✅'},
            {'feature': '数据分析', 'free': '❌', 'professional': '✅', 'enterprise': '✅'},
        ]
        return comparison_features
    
    async def check_membership_expiry(self, db: Session) -> List[Dict[str, Any]]:
        """检查会员到期情况"""
        try:
            # 查询即将到期的会员（7天内）
            expiring_soon = db.execute("""
                SELECT lawyer_id, membership_type, end_date, auto_renewal
                FROM lawyer_memberships 
                WHERE end_date <= %s AND membership_type != 'free'
            """, (date.today() + timedelta(days=7),)).fetchall()
            
            expiring_members = []
            for member in expiring_soon:
                expiring_members.append({
                    'lawyer_id': member['lawyer_id'],
                    'membership_type': member['membership_type'],
                    'end_date': member['end_date'].isoformat(),
                    'auto_renewal': member['auto_renewal'],
                    'days_remaining': (member['end_date'] - date.today()).days
                })
            
            return expiring_members
            
        except Exception as e:
            logger.error(f"检查会员到期失败: {str(e)}")
            return []
    
    async def downgrade_expired_memberships(self, db: Session) -> int:
        """降级过期会员到免费版"""
        try:
            # 查询已过期的付费会员
            expired_members = db.execute("""
                SELECT lawyer_id FROM lawyer_memberships 
                WHERE end_date < %s AND membership_type != 'free'
            """, (date.today(),)).fetchall()
            
            downgraded_count = 0
            for member in expired_members:
                # 降级到免费版
                await self._downgrade_to_free(member['lawyer_id'], db)
                downgraded_count += 1
            
            db.commit()
            logger.info(f"成功降级 {downgraded_count} 个过期会员到免费版")
            
            return downgraded_count
            
        except Exception as e:
            db.rollback()
            logger.error(f"降级过期会员失败: {str(e)}")
            return 0
    
    async def _downgrade_to_free(self, lawyer_id: str, db: Session):
        """降级律师到免费版"""
        free_config = self.MEMBERSHIP_TIERS['free']
        
        db.execute("""
            UPDATE lawyer_memberships 
            SET membership_type = 'free',
                start_date = %s,
                end_date = %s,
                benefits = %s,
                daily_case_limit = %s,
                monthly_amount_limit = 50000,
                ai_credits_monthly = %s,
                ai_credits_remaining = %s,
                payment_amount = 0,
                updated_at = %s
            WHERE lawyer_id = %s
        """, (
            date.today(),
            date.today() + timedelta(days=365*10),
            free_config,
            free_config['daily_case_limit'],
            free_config['ai_credits_monthly'],
            free_config['ai_credits_monthly'],
            datetime.now(),
            lawyer_id
        ))
    
    async def get_membership_statistics(self, db: Session) -> Dict[str, Any]:
        """获取会员统计数据"""
        try:
            # 各类型会员数量统计
            stats = db.execute("""
                SELECT membership_type, COUNT(*) as count
                FROM lawyer_memberships 
                GROUP BY membership_type
            """).fetchall()
            
            membership_stats = {stat['membership_type']: stat['count'] for stat in stats}
            
            # 收入统计
            revenue_stats = db.execute("""
                SELECT 
                    SUM(CASE WHEN membership_type = 'professional' THEN payment_amount ELSE 0 END) as professional_revenue,
                    SUM(CASE WHEN membership_type = 'enterprise' THEN payment_amount ELSE 0 END) as enterprise_revenue,
                    SUM(payment_amount) as total_revenue
                FROM lawyer_memberships 
                WHERE membership_type != 'free'
            """).fetchone()
            
            # 转化率计算
            total_lawyers = sum(membership_stats.values())
            paid_lawyers = membership_stats.get('professional', 0) + membership_stats.get('enterprise', 0)
            conversion_rate = (paid_lawyers / total_lawyers * 100) if total_lawyers > 0 else 0
            
            return {
                'membership_distribution': membership_stats,
                'total_lawyers': total_lawyers,
                'paid_lawyers': paid_lawyers,
                'free_lawyers': membership_stats.get('free', 0),
                'conversion_rate': round(conversion_rate, 2),
                'monthly_revenue': {
                    'professional': float(revenue_stats['professional_revenue'] or 0),
                    'enterprise': float(revenue_stats['enterprise_revenue'] or 0),
                    'total': float(revenue_stats['total_revenue'] or 0)
                }
            }
            
        except Exception as e:
            logger.error(f"获取会员统计失败: {str(e)}")
            return {
                'membership_distribution': {},
                'total_lawyers': 0,
                'paid_lawyers': 0,
                'free_lawyers': 0,
                'conversion_rate': 0,
                'monthly_revenue': {'professional': 0, 'enterprise': 0, 'total': 0}
            }


# 服务实例工厂函数
def create_lawyer_membership_service(
    config_service: SystemConfigService, 
    payment_service: WeChatPayService
) -> LawyerMembershipService:
    """创建律师会员服务实例"""
    return LawyerMembershipService(config_service, payment_service)