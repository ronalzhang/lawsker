"""
律师活跃度跟踪服务
实现律师活跃度提升50%的目标，通过积分激励和等级系统
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from decimal import Decimal
from uuid import UUID
import json
import asyncio

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from fastapi import HTTPException

from app.services.lawyer_points_engine import LawyerPointsEngine
from app.services.lawyer_membership_service import LawyerMembershipService
from app.services.notification_channels import EmailNotifier

logger = logging.getLogger(__name__)


class LawyerActivityTracker:
    """律师活跃度跟踪器 - 提升律师活跃度50%"""
    
    # 活跃度指标权重
    ACTIVITY_WEIGHTS = {
        'daily_login': 10,           # 每日登录
        'case_response': 25,         # 案件响应
        'case_completion': 50,       # 案件完成
        'client_interaction': 15,    # 客户互动
        'profile_update': 5,         # 资料更新
        'ai_tool_usage': 8,          # AI工具使用
        'online_duration': 12,       # 在线时长
        'quality_feedback': 30,      # 质量反馈
        'referral_activity': 20,     # 推荐活动
        'training_participation': 15  # 培训参与
    }
    
    # 活跃度等级阈值
    ACTIVITY_LEVELS = {
        'inactive': {'min_score': 0, 'max_score': 100, 'name': '不活跃', 'color': '#ef4444'},
        'low': {'min_score': 101, 'max_score': 300, 'name': '低活跃', 'color': '#f97316'},
        'moderate': {'min_score': 301, 'max_score': 600, 'name': '中等活跃', 'color': '#eab308'},
        'active': {'min_score': 601, 'max_score': 900, 'name': '活跃', 'color': '#22c55e'},
        'highly_active': {'min_score': 901, 'max_score': 1500, 'name': '高度活跃', 'color': '#3b82f6'},
        'super_active': {'min_score': 1501, 'max_score': float('inf'), 'name': '超级活跃', 'color': '#8b5cf6'}
    }
    
    # 每日活跃度任务
    DAILY_TASKS = {
        'login': {'points': 10, 'description': '每日登录', 'max_per_day': 1},
        'respond_to_case': {'points': 25, 'description': '响应案件', 'max_per_day': 5},
        'complete_case': {'points': 50, 'description': '完成案件', 'max_per_day': 3},
        'update_profile': {'points': 15, 'description': '更新个人资料', 'max_per_day': 1},
        'use_ai_tool': {'points': 8, 'description': '使用AI工具', 'max_per_day': 10},
        'online_1hour': {'points': 12, 'description': '在线1小时', 'max_per_day': 8},
        'client_message': {'points': 5, 'description': '回复客户消息', 'max_per_day': 20}
    }
    
    def __init__(
        self, 
        points_engine: LawyerPointsEngine,
        membership_service: LawyerMembershipService,
        notification_service: Optional[EmailNotifier] = None
    ):
        self.points_engine = points_engine
        self.membership_service = membership_service
        self.notification_service = notification_service
    
    async def track_lawyer_activity(
        self, 
        lawyer_id: UUID, 
        activity_type: str, 
        context: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """跟踪律师活动并更新活跃度"""
        try:
            # 1. 记录活动
            activity_record = await self._record_activity(lawyer_id, activity_type, context, db)
            
            # 2. 计算活跃度得分
            activity_score = await self._calculate_activity_score(lawyer_id, activity_type, context, db)
            
            # 3. 更新每日活跃度
            daily_activity = await self._update_daily_activity(lawyer_id, activity_type, activity_score, db)
            
            # 4. 检查每日任务完成情况
            task_rewards = await self._check_daily_tasks(lawyer_id, activity_type, context, db)
            
            # 5. 更新总体活跃度等级
            activity_level = await self._update_activity_level(lawyer_id, db)
            
            # 6. 触发积分奖励
            points_reward = await self._trigger_activity_points(lawyer_id, activity_type, context, db)
            
            # 7. 检查活跃度里程碑
            milestone_rewards = await self._check_activity_milestones(lawyer_id, db)
            
            db.commit()
            
            return {
                'activity_recorded': True,
                'activity_score': activity_score,
                'daily_activity': daily_activity,
                'task_rewards': task_rewards,
                'activity_level': activity_level,
                'points_reward': points_reward,
                'milestone_rewards': milestone_rewards,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"跟踪律师活动失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"跟踪活动失败: {str(e)}")
    
    async def _record_activity(
        self, 
        lawyer_id: UUID, 
        activity_type: str, 
        context: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """记录律师活动"""
        try:
            activity_data = {
                'lawyer_id': str(lawyer_id),
                'activity_type': activity_type,
                'activity_date': date.today(),
                'activity_time': datetime.now().time(),
                'context': context,
                'ip_address': context.get('ip_address'),
                'user_agent': context.get('user_agent'),
                'session_duration': context.get('session_duration', 0),
                'quality_score': context.get('quality_score', 0)
            }
            
            db.execute("""
                INSERT INTO lawyer_activity_logs 
                (lawyer_id, activity_type, activity_date, activity_time, context,
                 ip_address, user_agent, session_duration, quality_score)
                VALUES (%(lawyer_id)s, %(activity_type)s, %(activity_date)s, %(activity_time)s,
                        %(context)s, %(ip_address)s, %(user_agent)s, %(session_duration)s, %(quality_score)s)
            """, activity_data)
            
            return activity_data
            
        except Exception as e:
            logger.error(f"记录律师活动失败: {str(e)}")
            raise
    
    async def _calculate_activity_score(
        self, 
        lawyer_id: UUID, 
        activity_type: str, 
        context: Dict[str, Any],
        db: Session
    ) -> int:
        """计算活动得分"""
        try:
            base_score = self.ACTIVITY_WEIGHTS.get(activity_type, 5)
            
            # 根据上下文调整得分
            multiplier = 1.0
            
            # 质量调整
            quality_score = context.get('quality_score', 0)
            if quality_score >= 90:
                multiplier *= 1.5
            elif quality_score >= 80:
                multiplier *= 1.2
            elif quality_score < 60:
                multiplier *= 0.8
            
            # 时间调整（工作时间内活动得分更高）
            current_hour = datetime.now().hour
            if 9 <= current_hour <= 18:  # 工作时间
                multiplier *= 1.1
            elif 22 <= current_hour or current_hour <= 6:  # 深夜时间
                multiplier *= 0.9
            
            # 连续活动奖励
            consecutive_days = await self._get_consecutive_activity_days(lawyer_id, db)
            if consecutive_days >= 7:
                multiplier *= 1.3
            elif consecutive_days >= 3:
                multiplier *= 1.1
            
            # 会员倍数
            membership = await self.membership_service.get_lawyer_membership(lawyer_id, db)
            membership_multiplier = membership.get('point_multiplier', 1.0)
            multiplier *= membership_multiplier
            
            final_score = int(base_score * multiplier)
            return max(1, final_score)  # 最少1分
            
        except Exception as e:
            logger.error(f"计算活动得分失败: {str(e)}")
            return 5  # 默认得分
    
    async def _update_daily_activity(
        self, 
        lawyer_id: UUID, 
        activity_type: str, 
        activity_score: int,
        db: Session
    ) -> Dict[str, Any]:
        """更新每日活跃度"""
        try:
            today = date.today()
            
            # 检查今日活跃度记录
            existing_record = db.execute("""
                SELECT * FROM lawyer_daily_activity 
                WHERE lawyer_id = %s AND activity_date = %s
            """, (str(lawyer_id), today)).fetchone()
            
            if existing_record:
                # 更新现有记录
                new_total_score = existing_record['total_activity_score'] + activity_score
                activity_count = existing_record['activity_count'] + 1
                
                # 更新活动类型计数
                activity_breakdown = existing_record['activity_breakdown'] or {}
                activity_breakdown[activity_type] = activity_breakdown.get(activity_type, 0) + 1
                
                db.execute("""
                    UPDATE lawyer_daily_activity 
                    SET total_activity_score = %s,
                        activity_count = %s,
                        activity_breakdown = %s,
                        last_activity_time = %s,
                        updated_at = %s
                    WHERE lawyer_id = %s AND activity_date = %s
                """, (
                    new_total_score, activity_count, json.dumps(activity_breakdown),
                    datetime.now(), datetime.now(), str(lawyer_id), today
                ))
                
                return {
                    'total_score': new_total_score,
                    'activity_count': activity_count,
                    'activity_breakdown': activity_breakdown
                }
            else:
                # 创建新记录
                activity_breakdown = {activity_type: 1}
                
                db.execute("""
                    INSERT INTO lawyer_daily_activity 
                    (lawyer_id, activity_date, total_activity_score, activity_count,
                     activity_breakdown, first_activity_time, last_activity_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    str(lawyer_id), today, activity_score, 1,
                    json.dumps(activity_breakdown), datetime.now(), datetime.now()
                ))
                
                return {
                    'total_score': activity_score,
                    'activity_count': 1,
                    'activity_breakdown': activity_breakdown
                }
                
        except Exception as e:
            logger.error(f"更新每日活跃度失败: {str(e)}")
            raise
    
    async def _check_daily_tasks(
        self, 
        lawyer_id: UUID, 
        activity_type: str, 
        context: Dict[str, Any],
        db: Session
    ) -> List[Dict[str, Any]]:
        """检查每日任务完成情况"""
        try:
            today = date.today()
            rewards = []
            
            # 映射活动类型到任务
            activity_to_task = {
                'daily_login': 'login',
                'case_response': 'respond_to_case',
                'case_completion': 'complete_case',
                'profile_update': 'update_profile',
                'ai_tool_usage': 'use_ai_tool',
                'online_duration': 'online_1hour',
                'client_interaction': 'client_message'
            }
            
            task_type = activity_to_task.get(activity_type)
            if not task_type:
                return rewards
            
            task_config = self.DAILY_TASKS.get(task_type)
            if not task_config:
                return rewards
            
            # 检查今日该任务完成次数
            completed_count = db.execute("""
                SELECT COUNT(*) as count
                FROM lawyer_daily_task_completions 
                WHERE lawyer_id = %s AND task_type = %s AND completion_date = %s
            """, (str(lawyer_id), task_type, today)).fetchone()
            
            current_count = completed_count['count'] if completed_count else 0
            
            # 检查是否可以获得奖励
            if current_count < task_config['max_per_day']:
                # 记录任务完成
                db.execute("""
                    INSERT INTO lawyer_daily_task_completions 
                    (lawyer_id, task_type, completion_date, points_earned, context)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    str(lawyer_id), task_type, today, 
                    task_config['points'], json.dumps(context)
                ))
                
                # 给予积分奖励
                await self.points_engine.calculate_points_with_multiplier(
                    lawyer_id, f"daily_task_{task_type}", 
                    {'task_points': task_config['points'], **context}, db
                )
                
                rewards.append({
                    'task_type': task_type,
                    'task_name': task_config['description'],
                    'points_earned': task_config['points'],
                    'completion_count': current_count + 1,
                    'max_per_day': task_config['max_per_day']
                })
            
            return rewards
            
        except Exception as e:
            logger.error(f"检查每日任务失败: {str(e)}")
            return []
    
    async def _update_activity_level(self, lawyer_id: UUID, db: Session) -> Dict[str, Any]:
        """更新律师活跃度等级"""
        try:
            # 计算最近30天的活跃度得分
            thirty_days_ago = date.today() - timedelta(days=30)
            
            activity_stats = db.execute("""
                SELECT 
                    SUM(total_activity_score) as total_score,
                    COUNT(DISTINCT activity_date) as active_days,
                    AVG(total_activity_score) as avg_daily_score,
                    MAX(total_activity_score) as max_daily_score
                FROM lawyer_daily_activity 
                WHERE lawyer_id = %s AND activity_date >= %s
            """, (str(lawyer_id), thirty_days_ago)).fetchone()
            
            total_score = activity_stats['total_score'] or 0
            active_days = activity_stats['active_days'] or 0
            avg_daily_score = float(activity_stats['avg_daily_score'] or 0)
            max_daily_score = activity_stats['max_daily_score'] or 0
            
            # 计算活跃度等级
            activity_level = 'inactive'
            for level, config in self.ACTIVITY_LEVELS.items():
                if config['min_score'] <= total_score <= config['max_score']:
                    activity_level = level
                    break
            
            # 更新或创建活跃度等级记录
            db.execute("""
                INSERT INTO lawyer_activity_levels 
                (lawyer_id, activity_level, total_score, active_days, avg_daily_score, 
                 max_daily_score, calculation_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (lawyer_id) DO UPDATE SET
                    activity_level = EXCLUDED.activity_level,
                    total_score = EXCLUDED.total_score,
                    active_days = EXCLUDED.active_days,
                    avg_daily_score = EXCLUDED.avg_daily_score,
                    max_daily_score = EXCLUDED.max_daily_score,
                    calculation_date = EXCLUDED.calculation_date,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                str(lawyer_id), activity_level, total_score, active_days,
                avg_daily_score, max_daily_score, date.today()
            ))
            
            level_config = self.ACTIVITY_LEVELS[activity_level]
            
            return {
                'activity_level': activity_level,
                'level_name': level_config['name'],
                'level_color': level_config['color'],
                'total_score': total_score,
                'active_days': active_days,
                'avg_daily_score': round(avg_daily_score, 1),
                'max_daily_score': max_daily_score
            }
            
        except Exception as e:
            logger.error(f"更新活跃度等级失败: {str(e)}")
            return {
                'activity_level': 'inactive',
                'level_name': '不活跃',
                'level_color': '#ef4444',
                'total_score': 0,
                'active_days': 0,
                'avg_daily_score': 0,
                'max_daily_score': 0
            }
    
    async def _trigger_activity_points(
        self, 
        lawyer_id: UUID, 
        activity_type: str, 
        context: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """触发活动积分奖励"""
        try:
            # 根据活动类型给予积分
            points_mapping = {
                'daily_login': 'online_hour',
                'case_response': 'case_complete_success',
                'case_completion': 'case_complete_excellent',
                'client_interaction': 'online_hour',
                'profile_update': 'online_hour',
                'ai_tool_usage': 'ai_credit_used',
                'online_duration': 'online_hour',
                'quality_feedback': 'review_5star'
            }
            
            points_action = points_mapping.get(activity_type, 'online_hour')
            
            # 调用积分引擎
            points_result = await self.points_engine.calculate_points_with_multiplier(
                lawyer_id, points_action, context, db
            )
            
            return points_result
            
        except Exception as e:
            logger.error(f"触发活动积分失败: {str(e)}")
            return {'points_earned': 0}
    
    async def _check_activity_milestones(self, lawyer_id: UUID, db: Session) -> List[Dict[str, Any]]:
        """检查活跃度里程碑"""
        try:
            milestones = []
            
            # 获取律师活跃度统计
            stats = db.execute("""
                SELECT 
                    COUNT(DISTINCT activity_date) as total_active_days,
                    SUM(total_activity_score) as total_score,
                    MAX(total_activity_score) as best_daily_score
                FROM lawyer_daily_activity 
                WHERE lawyer_id = %s
            """, (str(lawyer_id),)).fetchone()
            
            total_active_days = stats['total_active_days'] or 0
            total_score = stats['total_score'] or 0
            best_daily_score = stats['best_daily_score'] or 0
            
            # 检查连续活跃天数里程碑
            consecutive_days = await self._get_consecutive_activity_days(lawyer_id, db)
            
            milestone_configs = [
                {'type': 'consecutive_days', 'threshold': 7, 'reward_points': 500, 'title': '连续活跃一周'},
                {'type': 'consecutive_days', 'threshold': 30, 'reward_points': 2000, 'title': '连续活跃一月'},
                {'type': 'total_active_days', 'threshold': 100, 'reward_points': 3000, 'title': '累计活跃100天'},
                {'type': 'total_score', 'threshold': 10000, 'reward_points': 1500, 'title': '累计活跃度10000分'},
                {'type': 'best_daily_score', 'threshold': 500, 'reward_points': 800, 'title': '单日活跃度500分'}
            ]
            
            for milestone in milestone_configs:
                milestone_key = f"{milestone['type']}_{milestone['threshold']}"
                
                # 检查是否已经获得过这个里程碑奖励
                existing_milestone = db.execute("""
                    SELECT * FROM lawyer_activity_milestones 
                    WHERE lawyer_id = %s AND milestone_key = %s
                """, (str(lawyer_id), milestone_key)).fetchone()
                
                if existing_milestone:
                    continue
                
                # 检查是否达到里程碑
                current_value = {
                    'consecutive_days': consecutive_days,
                    'total_active_days': total_active_days,
                    'total_score': total_score,
                    'best_daily_score': best_daily_score
                }.get(milestone['type'], 0)
                
                if current_value >= milestone['threshold']:
                    # 记录里程碑达成
                    db.execute("""
                        INSERT INTO lawyer_activity_milestones 
                        (lawyer_id, milestone_key, milestone_type, threshold_value, 
                         current_value, reward_points, achieved_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        str(lawyer_id), milestone_key, milestone['type'],
                        milestone['threshold'], current_value, milestone['reward_points'],
                        date.today()
                    ))
                    
                    # 给予积分奖励
                    await self.points_engine.calculate_points_with_multiplier(
                        lawyer_id, 'platform_promotion', 
                        {'milestone': milestone['title'], 'bonus_points': milestone['reward_points']}, db
                    )
                    
                    milestones.append({
                        'milestone_key': milestone_key,
                        'title': milestone['title'],
                        'threshold': milestone['threshold'],
                        'current_value': current_value,
                        'reward_points': milestone['reward_points'],
                        'achieved_date': date.today().isoformat()
                    })
            
            return milestones
            
        except Exception as e:
            logger.error(f"检查活跃度里程碑失败: {str(e)}")
            return []
    
    async def _get_consecutive_activity_days(self, lawyer_id: UUID, db: Session) -> int:
        """获取连续活跃天数"""
        try:
            # 获取最近的活跃日期
            recent_activities = db.execute("""
                SELECT activity_date 
                FROM lawyer_daily_activity 
                WHERE lawyer_id = %s 
                ORDER BY activity_date DESC 
                LIMIT 100
            """, (str(lawyer_id),)).fetchall()
            
            if not recent_activities:
                return 0
            
            consecutive_days = 0
            current_date = date.today()
            
            for activity in recent_activities:
                activity_date = activity['activity_date']
                
                if activity_date == current_date:
                    consecutive_days += 1
                    current_date -= timedelta(days=1)
                elif activity_date == current_date:
                    consecutive_days += 1
                    current_date -= timedelta(days=1)
                else:
                    break
            
            return consecutive_days
            
        except Exception as e:
            logger.error(f"获取连续活跃天数失败: {str(e)}")
            return 0
    
    async def get_lawyer_activity_summary(self, lawyer_id: UUID, db: Session) -> Dict[str, Any]:
        """获取律师活跃度汇总"""
        try:
            # 获取活跃度等级
            activity_level = db.execute("""
                SELECT * FROM lawyer_activity_levels WHERE lawyer_id = %s
            """, (str(lawyer_id),)).fetchone()
            
            # 获取今日活跃度
            today_activity = db.execute("""
                SELECT * FROM lawyer_daily_activity 
                WHERE lawyer_id = %s AND activity_date = %s
            """, (str(lawyer_id), date.today())).fetchone()
            
            # 获取本周活跃度
            week_start = date.today() - timedelta(days=date.today().weekday())
            week_activity = db.execute("""
                SELECT 
                    SUM(total_activity_score) as week_score,
                    COUNT(*) as active_days,
                    AVG(total_activity_score) as avg_score
                FROM lawyer_daily_activity 
                WHERE lawyer_id = %s AND activity_date >= %s
            """, (str(lawyer_id), week_start)).fetchone()
            
            # 获取连续活跃天数
            consecutive_days = await self._get_consecutive_activity_days(lawyer_id, db)
            
            # 获取今日任务完成情况
            today_tasks = db.execute("""
                SELECT task_type, COUNT(*) as completed_count
                FROM lawyer_daily_task_completions 
                WHERE lawyer_id = %s AND completion_date = %s
                GROUP BY task_type
            """, (str(lawyer_id), date.today())).fetchall()
            
            task_progress = {}
            for task in today_tasks:
                task_type = task['task_type']
                completed = task['completed_count']
                max_count = self.DAILY_TASKS.get(task_type, {}).get('max_per_day', 1)
                task_progress[task_type] = {
                    'completed': completed,
                    'max': max_count,
                    'progress': min(100, (completed / max_count) * 100)
                }
            
            # 获取最近里程碑
            recent_milestones = db.execute("""
                SELECT * FROM lawyer_activity_milestones 
                WHERE lawyer_id = %s 
                ORDER BY achieved_date DESC 
                LIMIT 5
            """, (str(lawyer_id),)).fetchall()
            
            return {
                'activity_level': {
                    'level': activity_level['activity_level'] if activity_level else 'inactive',
                    'level_name': self.ACTIVITY_LEVELS.get(
                        activity_level['activity_level'] if activity_level else 'inactive', 
                        self.ACTIVITY_LEVELS['inactive']
                    )['name'],
                    'total_score': activity_level['total_score'] if activity_level else 0,
                    'active_days': activity_level['active_days'] if activity_level else 0
                },
                'today_activity': {
                    'score': today_activity['total_activity_score'] if today_activity else 0,
                    'activity_count': today_activity['activity_count'] if today_activity else 0,
                    'breakdown': today_activity['activity_breakdown'] if today_activity else {}
                },
                'week_activity': {
                    'total_score': week_activity['week_score'] or 0,
                    'active_days': week_activity['active_days'] or 0,
                    'avg_score': round(float(week_activity['avg_score'] or 0), 1)
                },
                'consecutive_days': consecutive_days,
                'task_progress': task_progress,
                'recent_milestones': [
                    {
                        'title': self._get_milestone_title(m['milestone_key']),
                        'reward_points': m['reward_points'],
                        'achieved_date': m['achieved_date'].isoformat()
                    }
                    for m in recent_milestones
                ]
            }
            
        except Exception as e:
            logger.error(f"获取律师活跃度汇总失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取活跃度汇总失败: {str(e)}")
    
    def _get_milestone_title(self, milestone_key: str) -> str:
        """获取里程碑标题"""
        milestone_titles = {
            'consecutive_days_7': '连续活跃一周',
            'consecutive_days_30': '连续活跃一月',
            'total_active_days_100': '累计活跃100天',
            'total_score_10000': '累计活跃度10000分',
            'best_daily_score_500': '单日活跃度500分'
        }
        return milestone_titles.get(milestone_key, milestone_key)
    
    async def get_activity_leaderboard(self, db: Session, period: str = 'week', limit: int = 50) -> List[Dict[str, Any]]:
        """获取活跃度排行榜"""
        try:
            if period == 'week':
                start_date = date.today() - timedelta(days=7)
            elif period == 'month':
                start_date = date.today() - timedelta(days=30)
            else:  # today
                start_date = date.today()
            
            leaderboard = db.execute("""
                SELECT 
                    lda.lawyer_id,
                    u.username,
                    p.full_name,
                    SUM(lda.total_activity_score) as total_score,
                    COUNT(lda.activity_date) as active_days,
                    AVG(lda.total_activity_score) as avg_score,
                    lal.activity_level,
                    lld.current_level,
                    ll.name as lawyer_level_name
                FROM lawyer_daily_activity lda
                JOIN users u ON lda.lawyer_id = u.id
                LEFT JOIN profiles p ON u.id = p.user_id
                LEFT JOIN lawyer_activity_levels lal ON lda.lawyer_id = lal.lawyer_id
                LEFT JOIN lawyer_level_details lld ON lda.lawyer_id = lld.lawyer_id
                LEFT JOIN lawyer_levels ll ON lld.current_level = ll.level
                WHERE lda.activity_date >= %s
                GROUP BY lda.lawyer_id, u.username, p.full_name, lal.activity_level, 
                         lld.current_level, ll.name
                ORDER BY total_score DESC, active_days DESC
                LIMIT %s
            """, (start_date, limit)).fetchall()
            
            return [
                {
                    'rank': idx + 1,
                    'lawyer_id': row['lawyer_id'],
                    'username': row['username'],
                    'full_name': row['full_name'],
                    'total_score': row['total_score'] or 0,
                    'active_days': row['active_days'] or 0,
                    'avg_score': round(float(row['avg_score'] or 0), 1),
                    'activity_level': row['activity_level'] or 'inactive',
                    'activity_level_name': self.ACTIVITY_LEVELS.get(
                        row['activity_level'] or 'inactive', 
                        self.ACTIVITY_LEVELS['inactive']
                    )['name'],
                    'lawyer_level': row['current_level'] or 1,
                    'lawyer_level_name': row['lawyer_level_name'] or '见习律师'
                }
                for idx, row in enumerate(leaderboard)
            ]
            
        except Exception as e:
            logger.error(f"获取活跃度排行榜失败: {str(e)}")
            return []
    
    async def generate_activity_insights(self, lawyer_id: UUID, db: Session) -> Dict[str, Any]:
        """生成活跃度洞察和建议"""
        try:
            # 获取律师活跃度数据
            summary = await self.get_lawyer_activity_summary(lawyer_id, db)
            
            insights = []
            recommendations = []
            
            # 分析活跃度等级
            current_level = summary['activity_level']['level']
            if current_level in ['inactive', 'low']:
                insights.append("您的活跃度较低，建议增加平台使用频率")
                recommendations.extend([
                    "每日登录获得基础积分",
                    "及时响应客户案件",
                    "使用AI工具提升效率"
                ])
            elif current_level == 'moderate':
                insights.append("您的活跃度中等，还有提升空间")
                recommendations.extend([
                    "保持每日活跃，争取连续活跃奖励",
                    "提升案件完成质量",
                    "参与平台推广活动"
                ])
            else:
                insights.append("您的活跃度很高，继续保持！")
                recommendations.extend([
                    "帮助其他律师，获得推荐奖励",
                    "参与平台培训和活动",
                    "分享经验，提升影响力"
                ])
            
            # 分析连续活跃天数
            consecutive_days = summary['consecutive_days']
            if consecutive_days >= 30:
                insights.append(f"连续活跃{consecutive_days}天，表现优秀！")
            elif consecutive_days >= 7:
                insights.append(f"连续活跃{consecutive_days}天，继续保持")
            elif consecutive_days > 0:
                insights.append(f"连续活跃{consecutive_days}天，争取达到一周")
                recommendations.append("每日至少完成一项活动，保持连续活跃")
            else:
                insights.append("建议保持每日活跃，获得连续奖励")
                recommendations.append("设置每日提醒，养成活跃习惯")
            
            # 分析任务完成情况
            task_progress = summary['task_progress']
            incomplete_tasks = []
            for task_type, config in self.DAILY_TASKS.items():
                if task_type not in task_progress:
                    incomplete_tasks.append(config['description'])
                elif task_progress[task_type]['progress'] < 100:
                    incomplete_tasks.append(config['description'])
            
            if incomplete_tasks:
                insights.append(f"今日还有{len(incomplete_tasks)}项任务未完成")
                recommendations.extend([f"完成{task}" for task in incomplete_tasks[:3]])
            
            return {
                'insights': insights,
                'recommendations': recommendations,
                'activity_score': summary['activity_level']['total_score'],
                'improvement_potential': self._calculate_improvement_potential(summary),
                'next_milestone': self._get_next_milestone(summary)
            }
            
        except Exception as e:
            logger.error(f"生成活跃度洞察失败: {str(e)}")
            return {
                'insights': ['暂无洞察数据'],
                'recommendations': ['保持平台活跃'],
                'activity_score': 0,
                'improvement_potential': 0,
                'next_milestone': None
            }
    
    def _calculate_improvement_potential(self, summary: Dict[str, Any]) -> int:
        """计算改进潜力百分比"""
        current_score = summary['activity_level']['total_score']
        current_level = summary['activity_level']['level']
        
        # 找到下一个等级的最低分数
        level_order = ['inactive', 'low', 'moderate', 'active', 'highly_active', 'super_active']
        current_index = level_order.index(current_level)
        
        if current_index < len(level_order) - 1:
            next_level = level_order[current_index + 1]
            next_level_min = self.ACTIVITY_LEVELS[next_level]['min_score']
            
            if current_score < next_level_min:
                potential = ((next_level_min - current_score) / next_level_min) * 100
                return min(100, max(0, int(potential)))
        
        return 0
    
    def _get_next_milestone(self, summary: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """获取下一个里程碑"""
        consecutive_days = summary['consecutive_days']
        total_score = summary['activity_level']['total_score']
        
        # 检查连续活跃天数里程碑
        if consecutive_days < 7:
            return {
                'type': 'consecutive_days',
                'target': 7,
                'current': consecutive_days,
                'title': '连续活跃一周',
                'reward_points': 500,
                'progress': (consecutive_days / 7) * 100
            }
        elif consecutive_days < 30:
            return {
                'type': 'consecutive_days',
                'target': 30,
                'current': consecutive_days,
                'title': '连续活跃一月',
                'reward_points': 2000,
                'progress': (consecutive_days / 30) * 100
            }
        
        # 检查总分里程碑
        if total_score < 10000:
            return {
                'type': 'total_score',
                'target': 10000,
                'current': total_score,
                'title': '累计活跃度10000分',
                'reward_points': 1500,
                'progress': (total_score / 10000) * 100
            }
        
        return None


# 服务实例工厂函数
def create_lawyer_activity_tracker(
    points_engine: LawyerPointsEngine,
    membership_service: LawyerMembershipService,
    notification_service: Optional[EmailNotifier] = None
) -> LawyerActivityTracker:
    """创建律师活跃度跟踪器实例"""
    return LawyerActivityTracker(points_engine, membership_service, notification_service)