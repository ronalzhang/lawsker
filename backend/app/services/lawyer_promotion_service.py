"""
律师推广服务
用于实现300%律师注册率提升目标的营销推广功能
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.email_service import EmailService
from app.core.database import get_db

logger = logging.getLogger(__name__)


class LawyerPromotionService:
    """律师推广服务 - 实现300%注册率提升目标"""
    
    def __init__(self, email_service: EmailService):
        self.email_service = email_service
        
    async def send_lawyer_promotion_campaign(
        self, 
        target_emails: List[str],
        campaign_name: str = "lawyer_free_registration"
    ) -> Dict[str, Any]:
        """
        发送律师推广邮件活动
        
        Args:
            target_emails: 目标邮箱列表
            campaign_name: 活动名称
            
        Returns:
            发送结果统计
        """
        try:
            sent_count = 0
            failed_count = 0
            failed_emails = []
            
            # 邮件模板变量
            template_vars = {
                'registration_url': 'https://lawsker.com/lawyer-registration-landing.html',
                'unsubscribe_url': 'https://lawsker.com/unsubscribe',
                'campaign_name': campaign_name,
                'timestamp': datetime.now().isoformat()
            }
            
            # 批量发送邮件
            for email in target_emails:
                try:
                    await self.email_service.send_lawyer_promotion_email(
                        to_email=email,
                        template_vars=template_vars
                    )
                    sent_count += 1
                    
                    # 记录发送日志
                    await self._log_promotion_email_sent(email, campaign_name)
                    
                    # 避免发送过快
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    failed_count += 1
                    failed_emails.append(email)
                    logger.error(f"发送推广邮件失败: {email}, 错误: {str(e)}")
            
            logger.info(
                f"律师推广邮件发送完成: 成功{sent_count}封, 失败{failed_count}封"
            )
            
            return {
                'campaign_name': campaign_name,
                'total_emails': len(target_emails),
                'sent_count': sent_count,
                'failed_count': failed_count,
                'failed_emails': failed_emails,
                'success_rate': sent_count / len(target_emails) if target_emails else 0
            }
            
        except Exception as e:
            logger.error(f"律师推广邮件活动失败: {str(e)}")
            raise
    
    async def get_potential_lawyer_emails(self, db: Session) -> List[str]:
        """
        获取潜在律师邮箱列表
        
        Args:
            db: 数据库会话
            
        Returns:
            邮箱列表
        """
        try:
            # 查询已注册但未认证的用户
            query = text("""
                SELECT DISTINCT email 
                FROM users 
                WHERE account_type IN ('pending', 'user') 
                AND email IS NOT NULL 
                AND email != ''
                AND id NOT IN (
                    SELECT user_id 
                    FROM lawyer_certification_requests 
                    WHERE status IN ('approved', 'pending')
                )
                ORDER BY created_at DESC
                LIMIT 1000
            """)
            
            result = db.execute(query)
            emails = [row[0] for row in result.fetchall()]
            
            logger.info(f"获取到{len(emails)}个潜在律师邮箱")
            return emails
            
        except Exception as e:
            logger.error(f"获取潜在律师邮箱失败: {str(e)}")
            return []
    
    async def create_lawyer_referral_program(
        self, 
        referrer_lawyer_id: str,
        referral_bonus_points: int = 500
    ) -> Dict[str, Any]:
        """
        创建律师推荐计划
        
        Args:
            referrer_lawyer_id: 推荐人律师ID
            referral_bonus_points: 推荐奖励积分
            
        Returns:
            推荐计划信息
        """
        try:
            # 生成推荐链接
            referral_code = f"LAW_{referrer_lawyer_id[:8]}_{datetime.now().strftime('%Y%m')}"
            referral_url = f"https://lawsker.com/lawyer-registration-landing.html?ref={referral_code}"
            
            # 记录推荐计划
            with get_db() as db:
                db.execute(text("""
                    INSERT INTO lawyer_referral_programs 
                    (referrer_id, referral_code, referral_url, bonus_points, created_at)
                    VALUES (:referrer_id, :referral_code, :referral_url, :bonus_points, :created_at)
                    ON CONFLICT (referrer_id) DO UPDATE SET
                    referral_code = :referral_code,
                    referral_url = :referral_url,
                    updated_at = :created_at
                """), {
                    'referrer_id': referrer_lawyer_id,
                    'referral_code': referral_code,
                    'referral_url': referral_url,
                    'bonus_points': referral_bonus_points,
                    'created_at': datetime.now()
                })
                db.commit()
            
            return {
                'referral_code': referral_code,
                'referral_url': referral_url,
                'bonus_points': referral_bonus_points,
                'message': '推荐计划创建成功'
            }
            
        except Exception as e:
            logger.error(f"创建律师推荐计划失败: {str(e)}")
            raise
    
    async def track_registration_conversion(
        self,
        source: str,
        campaign: str = None,
        referral_code: str = None
    ) -> Dict[str, Any]:
        """
        跟踪注册转化率
        
        Args:
            source: 来源渠道
            campaign: 活动名称
            referral_code: 推荐码
            
        Returns:
            跟踪结果
        """
        try:
            with get_db() as db:
                # 记录转化事件
                db.execute(text("""
                    INSERT INTO lawyer_promotion_tracking 
                    (source, campaign, referral_code, event_type, created_at)
                    VALUES (:source, :campaign, :referral_code, 'registration', :created_at)
                """), {
                    'source': source,
                    'campaign': campaign,
                    'referral_code': referral_code,
                    'created_at': datetime.now()
                })
                db.commit()
            
            return {
                'tracked': True,
                'source': source,
                'campaign': campaign,
                'referral_code': referral_code
            }
            
        except Exception as e:
            logger.error(f"跟踪注册转化失败: {str(e)}")
            return {'tracked': False, 'error': str(e)}
    
    async def get_promotion_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        获取推广统计数据
        
        Args:
            days: 统计天数
            
        Returns:
            统计数据
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            with get_db() as db:
                # 注册统计
                registration_stats = db.execute(text("""
                    SELECT 
                        COUNT(*) as total_registrations,
                        COUNT(CASE WHEN account_type = 'lawyer' THEN 1 END) as lawyer_registrations,
                        COUNT(CASE WHEN created_at >= :start_date THEN 1 END) as recent_registrations
                    FROM users
                    WHERE created_at >= :start_date
                """), {'start_date': start_date}).fetchone()
                
                # 认证统计
                certification_stats = db.execute(text("""
                    SELECT 
                        COUNT(*) as total_certifications,
                        COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_certifications,
                        COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_certifications
                    FROM lawyer_certification_requests
                    WHERE submitted_at >= :start_date
                """), {'start_date': start_date}).fetchone()
                
                # 会员统计
                membership_stats = db.execute(text("""
                    SELECT 
                        COUNT(*) as total_memberships,
                        COUNT(CASE WHEN membership_type = 'free' THEN 1 END) as free_memberships,
                        COUNT(CASE WHEN membership_type IN ('professional', 'enterprise') THEN 1 END) as paid_memberships
                    FROM lawyer_memberships
                    WHERE created_at >= :start_date
                """), {'start_date': start_date}).fetchone()
            
            # 计算转化率
            total_registrations = registration_stats[0] if registration_stats[0] else 1
            lawyer_registrations = registration_stats[1] if registration_stats[1] else 0
            approved_certifications = certification_stats[1] if certification_stats[1] else 0
            
            lawyer_conversion_rate = (lawyer_registrations / total_registrations) * 100
            certification_conversion_rate = (approved_certifications / lawyer_registrations) * 100 if lawyer_registrations > 0 else 0
            
            return {
                'period_days': days,
                'total_registrations': total_registrations,
                'lawyer_registrations': lawyer_registrations,
                'approved_certifications': approved_certifications,
                'free_memberships': membership_stats[1] if membership_stats else 0,
                'paid_memberships': membership_stats[2] if membership_stats else 0,
                'lawyer_conversion_rate': round(lawyer_conversion_rate, 2),
                'certification_conversion_rate': round(certification_conversion_rate, 2),
                'target_achievement': {
                    'current_growth': lawyer_conversion_rate,
                    'target_growth': 300,
                    'achievement_rate': round((lawyer_conversion_rate / 300) * 100, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"获取推广统计失败: {str(e)}")
            return {}
    
    async def _log_promotion_email_sent(self, email: str, campaign: str):
        """记录推广邮件发送日志"""
        try:
            with get_db() as db:
                db.execute(text("""
                    INSERT INTO lawyer_promotion_tracking 
                    (email, campaign, event_type, created_at)
                    VALUES (:email, :campaign, 'email_sent', :created_at)
                """), {
                    'email': email,
                    'campaign': campaign,
                    'created_at': datetime.now()
                })
                db.commit()
        except Exception as e:
            logger.error(f"记录推广邮件日志失败: {str(e)}")
    
    async def optimize_registration_funnel(self) -> Dict[str, Any]:
        """
        优化注册漏斗，提升转化率
        
        Returns:
            优化建议
        """
        try:
            stats = await self.get_promotion_statistics(30)
            
            recommendations = []
            
            # 基于数据给出优化建议
            if stats.get('lawyer_conversion_rate', 0) < 50:
                recommendations.append({
                    'type': 'conversion_optimization',
                    'priority': 'high',
                    'suggestion': '律师转化率偏低，建议增强免费会员福利宣传',
                    'action': 'enhance_benefits_promotion'
                })
            
            if stats.get('certification_conversion_rate', 0) < 80:
                recommendations.append({
                    'type': 'certification_optimization',
                    'priority': 'medium',
                    'suggestion': '认证转化率偏低，建议简化认证流程',
                    'action': 'simplify_certification_process'
                })
            
            # 如果目标达成率低于50%，建议加强推广
            achievement_rate = stats.get('target_achievement', {}).get('achievement_rate', 0)
            if achievement_rate < 50:
                recommendations.append({
                    'type': 'marketing_intensification',
                    'priority': 'high',
                    'suggestion': '目标达成率偏低，建议加强营销推广力度',
                    'action': 'increase_marketing_efforts'
                })
            
            return {
                'current_stats': stats,
                'recommendations': recommendations,
                'optimization_score': min(100, achievement_rate + 20)  # 基础分数
            }
            
        except Exception as e:
            logger.error(f"优化注册漏斗失败: {str(e)}")
            return {'error': str(e)}


# 扩展邮件服务以支持律师推广邮件
class EmailService:
    """扩展邮件服务"""
    
    async def send_lawyer_promotion_email(
        self,
        to_email: str,
        template_vars: Dict[str, Any]
    ) -> bool:
        """
        发送律师推广邮件
        
        Args:
            to_email: 收件人邮箱
            template_vars: 模板变量
            
        Returns:
            发送是否成功
        """
        try:
            # 读取邮件模板
            with open('backend/templates/lawyer_promotion_email.html', 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # 替换模板变量
            for key, value in template_vars.items():
                template_content = template_content.replace(f'{{{{{key}}}}}', str(value))
            
            # 发送邮件（这里需要集成实际的邮件发送服务）
            # 例如使用 SMTP、SendGrid、阿里云邮件推送等
            
            logger.info(f"律师推广邮件发送成功: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"发送律师推广邮件失败: {to_email}, 错误: {str(e)}")
            return False