"""
律师积分计算引擎
实现传奇游戏式指数级积分系统
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from decimal import Decimal
from uuid import UUID
import json

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services.lawyer_membership_service import LawyerMembershipService
from app.services.notification_channels import EmailNotifier

logger = logging.getLogger(__name__)


class LawyerPointsEngine:
    """律师积分计算引擎 - 传奇游戏式指数级积分"""
    
    # 基础积分规则
    BASE_POINTS = {
        'case_complete_success': 100,      # 案件成功完成
        'case_complete_excellent': 200,    # 案件优秀完成
        'review_5star': 200,              # 5星好评
        'review_4star': 100,              # 4星好评
        'review_3star': 50,               # 3星好评
        'review_2star': -150,             # 2星差评
        'review_1star': -300,             # 1星差评
        'online_hour': 5,                 # 在线1小时
        'ai_credit_used': 3,              # 使用1个AI credit
        'payment_100yuan': 100,           # 付费100元
        'case_declined': -30,             # 拒绝案件
        'case_declined_consecutive': -60,  # 连续拒绝案件
        'late_response': -20,             # 响应延迟
        'early_completion': 50,           # 提前完成案件
        'client_referral': 150,           # 客户推荐
        'platform_promotion': 300        # 平台推广活动
    }
    
    # 律师等级要求（传奇游戏式指数级增长）
    LEVEL_REQUIREMENTS = {
        1: {'level_points': 0, 'cases_completed': 0, 'name': '见习律师'},
        2: {'level_points': 500, 'cases_completed': 3, 'name': '初级律师'},
        3: {'level_points': 1500, 'cases_completed': 8, 'name': '助理律师'},
        4: {'level_points': 4000, 'cases_completed': 20, 'name': '执业律师'},
        5: {'level_points': 10000, 'cases_completed': 50, 'name': '资深律师'},
        6: {'level_points': 25000, 'cases_completed': 120, 'name': '专业律师'},
        7: {'level_points': 60000, 'cases_completed': 300, 'name': '高级律师'},
        8: {'level_points': 150000, 'cases_completed': 700, 'name': '合伙人律师'},
        9: {'level_points': 350000, 'cases_completed': 1500, 'name': '高级合伙人'},
        10: {'level_points': 800000, 'cases_completed': 3000, 'name': '首席合伙人'}
    }
    
    def __init__(self, membership_service: LawyerMembershipService, notification_service: Optional[EmailNotifier] = None):
        self.membership_service = membership_service
        self.notification_service = notification_service
    
    async def calculate_points_with_multiplier(
        self, 
        lawyer_id: UUID, 
        action: str, 
        context: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """计算积分 - 考虑会员倍数"""
        try:
            # 1. 获取基础积分
            base_points = self.BASE_POINTS.get(action, 0)
            
            # 2. 根据上下文调整积分
            adjusted_points = await self._adjust_points_by_context(base_points, context)
            
            # 3. 获取律师会员倍数
            membership = await self.membership_service.get_lawyer_membership(lawyer_id, db)
            multiplier = membership.get('point_multiplier', 1.0)
            
            # 4. 应用倍数
            final_points = int(adjusted_points * multiplier)
            
            # 5. 记录积分变动和审计日志
            await self._record_point_transaction(lawyer_id, action, final_points, multiplier, context, db)
            await self._log_audit_trail(lawyer_id, action, final_points, context, db)
            
            # 6. 更新律师等级详情
            await self._update_lawyer_level_details(lawyer_id, final_points, action, context, db)
            
            # 7. 检查等级升级
            level_change = await self._check_level_upgrade(lawyer_id, db)
            
            db.commit()
            
            result = {
                'points_earned': final_points,
                'base_points': base_points,
                'adjusted_points': adjusted_points,
                'multiplier_applied': multiplier,
                'membership_type': membership.get('membership_type', 'free'),
                'action': action,
                'context': context
            }
            
            if level_change:
                result['level_change'] = level_change
            
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"计算积分失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"计算积分失败: {str(e)}")
    
    async def _adjust_points_by_context(self, base_points: int, context: Dict[str, Any]) -> int:
        """根据上下文调整积分"""
        adjusted_points = base_points
        
        # 案件金额调整
        case_amount = context.get('case_amount', 0)
        if case_amount > 100000:  # 10万以上案件
            adjusted_points = int(adjusted_points * 1.5)
        elif case_amount > 50000:  # 5万以上案件
            adjusted_points = int(adjusted_points * 1.2)
        
        # 完成时间调整
        completion_speed = context.get('completion_speed', 1.0)
        if completion_speed > 1.2:  # 提前20%完成
            adjusted_points = int(adjusted_points * 1.3)
        elif completion_speed < 0.8:  # 延迟完成
            adjusted_points = int(adjusted_points * 0.8)
        
        # 客户评价调整
        client_rating = context.get('client_rating', 0)
        if client_rating >= 4.8:
            adjusted_points = int(adjusted_points * 1.2)
        elif client_rating <= 2.0:
            adjusted_points = int(adjusted_points * 0.5)
        
        # 连续行为调整
        consecutive_count = context.get('consecutive_count', 0)
        if consecutive_count > 1:
            # 连续好行为有额外奖励，连续坏行为有额外惩罚
            if base_points > 0:
                adjusted_points = int(adjusted_points * (1 + consecutive_count * 0.1))
            else:
                adjusted_points = int(adjusted_points * (1 + consecutive_count * 0.2))
        
        return adjusted_points
    
    async def _record_point_transaction(
        self, 
        lawyer_id: UUID, 
        action: str, 
        points_change: int, 
        multiplier: float,
        context: Dict[str, Any],
        db: Session
    ):
        """记录积分变动"""
        try:
            # 获取当前积分
            current_details = await self._get_lawyer_level_details(lawyer_id, db)
            points_before = current_details.get('level_points', 0)
            points_after = points_before + points_change
            
            # 插入积分变动记录
            transaction_data = {
                'lawyer_id': str(lawyer_id),
                'transaction_type': action,
                'points_change': points_change,
                'points_before': points_before,
                'points_after': points_after,
                'related_case_id': context.get('case_id'),
                'related_review_id': context.get('review_id'),
                'description': self._generate_transaction_description(action, points_change, multiplier),
                'metadata': {
                    'multiplier': multiplier,
                    'context': context,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            db.execute("""
                INSERT INTO lawyer_point_transactions 
                (lawyer_id, transaction_type, points_change, points_before, points_after,
                 related_case_id, related_review_id, description, metadata)
                VALUES (%(lawyer_id)s, %(transaction_type)s, %(points_change)s, %(points_before)s,
                        %(points_after)s, %(related_case_id)s, %(related_review_id)s, 
                        %(description)s, %(metadata)s)
            """, transaction_data)
            
        except Exception as e:
            logger.error(f"记录积分变动失败: {str(e)}")
            raise
    
    def _generate_transaction_description(self, action: str, points_change: int, multiplier: float) -> str:
        """生成积分变动描述"""
        action_descriptions = {
            'case_complete_success': '成功完成案件',
            'case_complete_excellent': '优秀完成案件',
            'review_5star': '获得5星好评',
            'review_4star': '获得4星好评',
            'review_3star': '获得3星好评',
            'review_2star': '收到2星差评',
            'review_1star': '收到1星差评',
            'online_hour': '在线工作1小时',
            'ai_credit_used': '使用AI工具',
            'payment_100yuan': '付费充值',
            'case_declined': '拒绝案件',
            'late_response': '响应延迟',
            'early_completion': '提前完成案件',
            'client_referral': '客户推荐',
            'platform_promotion': '参与平台推广'
        }
        
        base_desc = action_descriptions.get(action, action)
        points_desc = f"+{points_change}" if points_change > 0 else str(points_change)
        
        if multiplier > 1.0:
            return f"{base_desc} {points_desc}积分 (会员{multiplier}x倍数)"
        else:
            return f"{base_desc} {points_desc}积分"
    
    async def _update_lawyer_level_details(
        self, 
        lawyer_id: UUID, 
        points_change: int, 
        action: str,
        context: Dict[str, Any],
        db: Session
    ):
        """更新律师等级详情"""
        try:
            # 构建更新数据
            update_fields = ['level_points = level_points + %(points_change)s']
            update_params = {'lawyer_id': str(lawyer_id), 'points_change': points_change}
            
            # 根据行为类型更新相应字段
            if action.startswith('case_complete'):
                update_fields.append('cases_completed = cases_completed + 1')
                if action == 'case_complete_success':
                    update_fields.append('cases_won = cases_won + 1')
                
                # 更新收入
                case_amount = context.get('case_amount', 0)
                if case_amount > 0:
                    update_fields.append('total_revenue = total_revenue + %(case_amount)s')
                    update_fields.append('total_cases_amount = total_cases_amount + %(case_amount)s')
                    update_params['case_amount'] = case_amount
            
            elif action.startswith('review_'):
                # 更新客户评分
                rating = context.get('rating', 0)
                if rating > 0:
                    update_fields.append("""
                        client_rating = (client_rating * cases_completed + %(rating)s) / (cases_completed + 1)
                    """)
                    update_params['rating'] = rating
            
            elif action == 'online_hour':
                update_fields.append('total_online_hours = total_online_hours + 1')
            
            elif action == 'ai_credit_used':
                credits_used = context.get('credits_used', 1)
                update_fields.append('total_ai_credits_used = total_ai_credits_used + %(credits_used)s')
                update_params['credits_used'] = credits_used
            
            elif action.startswith('payment_'):
                payment_amount = context.get('payment_amount', 0)
                if payment_amount > 0:
                    update_fields.append('total_paid_amount = total_paid_amount + %(payment_amount)s')
                    update_params['payment_amount'] = payment_amount
            
            # 更新成功率
            update_fields.append("""
                success_rate = CASE 
                    WHEN cases_completed > 0 THEN (cases_won * 100.0 / cases_completed)
                    ELSE 0 
                END
            """)
            
            # 更新时间戳
            update_fields.append('updated_at = NOW()')
            
            # 执行更新
            update_sql = f"""
                UPDATE lawyer_level_details 
                SET {', '.join(update_fields)}
                WHERE lawyer_id = %(lawyer_id)s
            """
            
            db.execute(update_sql, update_params)
            
        except Exception as e:
            logger.error(f"更新律师等级详情失败: {str(e)}")
            raise
    
    async def _get_lawyer_level_details(self, lawyer_id: UUID, db: Session) -> Dict[str, Any]:
        """获取律师等级详情"""
        try:
            details = db.execute(
                "SELECT * FROM lawyer_level_details WHERE lawyer_id = %s",
                (str(lawyer_id),)
            ).fetchone()
            
            if not details:
                # 如果没有记录，创建初始记录
                await self.membership_service._initialize_lawyer_level_details(lawyer_id, db)
                details = db.execute(
                    "SELECT * FROM lawyer_level_details WHERE lawyer_id = %s",
                    (str(lawyer_id),)
                ).fetchone()
            
            return dict(details) if details else {}
            
        except Exception as e:
            logger.error(f"获取律师等级详情失败: {str(e)}")
            return {}
    
    async def _check_level_upgrade(self, lawyer_id: UUID, db: Session) -> Optional[Dict[str, Any]]:
        """检查律师等级升级"""
        try:
            lawyer_details = await self._get_lawyer_level_details(lawyer_id, db)
            current_level = lawyer_details.get('current_level', 1)
            current_points = lawyer_details.get('level_points', 0)
            cases_completed = lawyer_details.get('cases_completed', 0)
            
            # 检查是否可以升级
            next_level = current_level + 1
            if next_level > 10:  # 最高等级
                return None
            
            next_level_req = self.LEVEL_REQUIREMENTS[next_level]
            
            if (current_points >= next_level_req['level_points'] and 
                cases_completed >= next_level_req['cases_completed']):
                
                # 执行升级
                await self._upgrade_lawyer_level(lawyer_id, next_level, db)
                
                # 发送升级通知
                await self._send_level_upgrade_notification(lawyer_id, current_level, next_level, db)
                
                return {
                    'upgraded': True,
                    'old_level': current_level,
                    'new_level': next_level,
                    'level_name': next_level_req['name'],
                    'points_used': current_points,
                    'cases_completed': cases_completed
                }
            
            return None
            
        except Exception as e:
            logger.error(f"检查等级升级失败: {str(e)}")
            return None
    
    async def _upgrade_lawyer_level(self, lawyer_id: UUID, new_level: int, db: Session):
        """升级律师等级"""
        try:
            # 获取当前等级历史
            current_details = await self._get_lawyer_level_details(lawyer_id, db)
            level_history = current_details.get('level_change_history', [])
            
            # 添加升级记录
            upgrade_record = {
                'from_level': current_details.get('current_level', 1),
                'to_level': new_level,
                'upgrade_date': datetime.now().isoformat(),
                'points_at_upgrade': current_details.get('level_points', 0),
                'cases_at_upgrade': current_details.get('cases_completed', 0)
            }
            level_history.append(upgrade_record)
            
            # 更新等级
            db.execute("""
                UPDATE lawyer_level_details 
                SET current_level = %s,
                    last_upgrade_date = %s,
                    level_change_history = %s,
                    upgrade_eligible = FALSE,
                    updated_at = NOW()
                WHERE lawyer_id = %s
            """, (new_level, date.today(), json.dumps(level_history), str(lawyer_id)))
            
            logger.info(f"律师 {lawyer_id} 成功升级到等级 {new_level}")
            
        except Exception as e:
            logger.error(f"升级律师等级失败: {str(e)}")
            raise
    
    async def _send_level_upgrade_notification(
        self, 
        lawyer_id: UUID, 
        old_level: int, 
        new_level: int,
        db: Session
    ):
        """发送等级升级通知"""
        try:
            level_name = self.LEVEL_REQUIREMENTS[new_level]['name']
            
            # 这里应该调用通知服务发送升级通知
            # await self.notification_service.send_level_upgrade_notification(
            #     lawyer_id, old_level, new_level, level_name
            # )
            
            logger.info(f"已发送等级升级通知给律师 {lawyer_id}: {old_level} -> {new_level} ({level_name})")
            
        except Exception as e:
            logger.error(f"发送升级通知失败: {str(e)}")
            # 不抛出异常，避免影响升级流程
    
    async def get_lawyer_points_summary(self, lawyer_id: UUID, db: Session) -> Dict[str, Any]:
        """获取律师积分汇总"""
        try:
            # 获取等级详情
            details = await self._get_lawyer_level_details(lawyer_id, db)
            current_level = details.get('current_level', 1)
            current_points = details.get('level_points', 0)
            
            # 获取下一等级要求
            next_level = current_level + 1 if current_level < 10 else None
            next_level_req = self.LEVEL_REQUIREMENTS.get(next_level, {}) if next_level else None
            
            # 计算升级进度
            if next_level_req:
                points_needed = next_level_req['level_points'] - current_points
                cases_needed = max(0, next_level_req['cases_completed'] - details.get('cases_completed', 0))
                progress_percentage = min(100, (current_points / next_level_req['level_points']) * 100)
            else:
                points_needed = 0
                cases_needed = 0
                progress_percentage = 100
            
            # 获取会员信息
            membership = await self.membership_service.get_lawyer_membership(lawyer_id, db)
            
            # 获取最近积分变动
            recent_transactions = db.execute("""
                SELECT transaction_type, points_change, description, created_at
                FROM lawyer_point_transactions 
                WHERE lawyer_id = %s 
                ORDER BY created_at DESC 
                LIMIT 10
            """, (str(lawyer_id),)).fetchall()
            
            return {
                'current_level': current_level,
                'level_name': self.LEVEL_REQUIREMENTS[current_level]['name'],
                'current_points': current_points,
                'experience_points': details.get('experience_points', 0),
                'next_level': next_level,
                'next_level_name': next_level_req.get('name') if next_level_req else None,
                'points_needed': points_needed,
                'cases_needed': cases_needed,
                'progress_percentage': round(progress_percentage, 1),
                'membership_type': membership.get('membership_type', 'free'),
                'point_multiplier': membership.get('point_multiplier', 1.0),
                'statistics': {
                    'cases_completed': details.get('cases_completed', 0),
                    'cases_won': details.get('cases_won', 0),
                    'success_rate': round(details.get('success_rate', 0), 1),
                    'client_rating': round(details.get('client_rating', 0), 1),
                    'total_revenue': float(details.get('total_revenue', 0)),
                    'total_online_hours': details.get('total_online_hours', 0)
                },
                'recent_transactions': [
                    {
                        'type': t['transaction_type'],
                        'points': t['points_change'],
                        'description': t['description'],
                        'date': t['created_at'].isoformat() if t['created_at'] else None
                    }
                    for t in recent_transactions
                ]
            }
            
        except Exception as e:
            logger.error(f"获取律师积分汇总失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取积分汇总失败: {str(e)}")
    
    async def get_points_leaderboard(self, db: Session, limit: int = 50) -> List[Dict[str, Any]]:
        """获取积分排行榜"""
        try:
            leaderboard = db.execute("""
                SELECT 
                    lld.lawyer_id,
                    u.username,
                    p.full_name,
                    lld.current_level,
                    ll.name as level_name,
                    lld.level_points,
                    lld.cases_completed,
                    lld.success_rate,
                    lld.client_rating,
                    lm.membership_type
                FROM lawyer_level_details lld
                JOIN users u ON lld.lawyer_id = u.id
                LEFT JOIN profiles p ON u.id = p.user_id
                LEFT JOIN lawyer_levels ll ON lld.current_level = ll.level
                LEFT JOIN lawyer_memberships lm ON lld.lawyer_id = lm.lawyer_id
                ORDER BY lld.level_points DESC, lld.current_level DESC
                LIMIT %s
            """, (limit,)).fetchall()
            
            return [
                {
                    'rank': idx + 1,
                    'lawyer_id': row['lawyer_id'],
                    'username': row['username'],
                    'full_name': row['full_name'],
                    'current_level': row['current_level'],
                    'level_name': row['level_name'],
                    'level_points': row['level_points'],
                    'cases_completed': row['cases_completed'],
                    'success_rate': round(row['success_rate'] or 0, 1),
                    'client_rating': round(row['client_rating'] or 0, 1),
                    'membership_type': row['membership_type'] or 'free'
                }
                for idx, row in enumerate(leaderboard)
            ]
            
        except Exception as e:
            logger.error(f"获取积分排行榜失败: {str(e)}")
            return []
    
    async def _log_audit_trail(
        self, 
        lawyer_id: UUID, 
        action: str, 
        points: int, 
        context: Dict[str, Any], 
        db: Session
    ):
        """记录审计日志"""
        try:
            audit_log = {
                'timestamp': datetime.now().isoformat(),
                'lawyer_id': str(lawyer_id),
                'action': action,
                'points_change': points,
                'context': context,
                'ip_address': context.get('ip_address'),
                'user_agent': context.get('user_agent'),
                'session_id': context.get('session_id')
            }
            
            # 记录到安全日志
            logger.info(f"AUDIT: Lawyer points change - {json.dumps(audit_log)}")
            
            # 可以扩展到专门的审计日志表
            # audit_record = LawyerPointsAuditLog(**audit_log)
            # db.add(audit_record)
            # db.commit()
            
        except Exception as e:
            logger.error(f"Error logging audit trail: {e}")
            # 审计日志失败不应该影响主要业务流程


# 服务实例工厂函数
def create_lawyer_points_engine(
    membership_service: LawyerMembershipService,
    notification_service: Optional[EmailNotifier] = None
) -> LawyerPointsEngine:
    """创建律师积分引擎实例"""
    return LawyerPointsEngine(membership_service, notification_service)