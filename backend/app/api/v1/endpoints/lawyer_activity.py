"""
律师活跃度跟踪API端点
提升律师活跃度50%的核心接口
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_lawyer
from app.models.user import User
from app.services.lawyer_activity_tracker import LawyerActivityTracker
from app.services.lawyer_points_engine import LawyerPointsEngine
from app.services.lawyer_membership_service import LawyerMembershipService
from app.services.config_service import SystemConfigService
from app.services.payment_service import WeChatPayService

router = APIRouter()


# Pydantic模型
class ActivityTrackRequest(BaseModel):
    activity_type: str = Field(..., description="活动类型")
    context: Dict[str, Any] = Field(default_factory=dict, description="活动上下文")
    quality_score: Optional[int] = Field(None, ge=0, le=100, description="质量得分")
    session_duration: Optional[int] = Field(None, ge=0, description="会话持续时间（秒）")


class ActivitySummaryResponse(BaseModel):
    activity_level: Dict[str, Any]
    today_activity: Dict[str, Any]
    week_activity: Dict[str, Any]
    consecutive_days: int
    task_progress: Dict[str, Any]
    recent_milestones: List[Dict[str, Any]]


class ActivityInsightsResponse(BaseModel):
    insights: List[str]
    recommendations: List[str]
    activity_score: int
    improvement_potential: int
    next_milestone: Optional[Dict[str, Any]]


class LeaderboardResponse(BaseModel):
    rank: int
    lawyer_id: str
    username: str
    full_name: Optional[str]
    total_score: int
    active_days: int
    avg_score: float
    activity_level: str
    activity_level_name: str
    lawyer_level: int
    lawyer_level_name: str


# 依赖注入
def get_activity_tracker(
    db: Session = Depends(get_db)
) -> LawyerActivityTracker:
    """获取律师活跃度跟踪器实例"""
    config_service = SystemConfigService()
    payment_service = WeChatPayService(config_service)
    membership_service = LawyerMembershipService(config_service, payment_service)
    points_engine = LawyerPointsEngine(membership_service)
    
    return LawyerActivityTracker(points_engine, membership_service)


@router.post("/track", summary="跟踪律师活动")
async def track_lawyer_activity(
    request: ActivityTrackRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_lawyer),
    activity_tracker: LawyerActivityTracker = Depends(get_activity_tracker),
    db: Session = Depends(get_db)
):
    """
    跟踪律师活动并更新活跃度
    
    支持的活动类型：
    - daily_login: 每日登录
    - case_response: 案件响应
    - case_completion: 案件完成
    - client_interaction: 客户互动
    - profile_update: 资料更新
    - ai_tool_usage: AI工具使用
    - online_duration: 在线时长
    - quality_feedback: 质量反馈
    """
    try:
        # 添加用户信息到上下文
        context = request.context.copy()
        context.update({
            'user_id': str(current_user.id),
            'username': current_user.username,
            'quality_score': request.quality_score or 0,
            'session_duration': request.session_duration or 0,
            'timestamp': datetime.now().isoformat()
        })
        
        # 跟踪活动
        result = await activity_tracker.track_lawyer_activity(
            current_user.id, request.activity_type, context, db
        )
        
        return {
            "success": True,
            "message": "活动跟踪成功",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"跟踪活动失败: {str(e)}")


@router.get("/summary", response_model=ActivitySummaryResponse, summary="获取活跃度汇总")
async def get_activity_summary(
    current_user: User = Depends(get_current_lawyer),
    activity_tracker: LawyerActivityTracker = Depends(get_activity_tracker),
    db: Session = Depends(get_db)
):
    """获取律师活跃度汇总信息"""
    try:
        summary = await activity_tracker.get_lawyer_activity_summary(current_user.id, db)
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取活跃度汇总失败: {str(e)}")


@router.get("/insights", response_model=ActivityInsightsResponse, summary="获取活跃度洞察")
async def get_activity_insights(
    current_user: User = Depends(get_current_lawyer),
    activity_tracker: LawyerActivityTracker = Depends(get_activity_tracker),
    db: Session = Depends(get_db)
):
    """获取律师活跃度洞察和建议"""
    try:
        insights = await activity_tracker.generate_activity_insights(current_user.id, db)
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取活跃度洞察失败: {str(e)}")


@router.get("/leaderboard", response_model=List[LeaderboardResponse], summary="获取活跃度排行榜")
async def get_activity_leaderboard(
    period: str = Query("week", regex="^(today|week|month)$", description="统计周期"),
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    activity_tracker: LawyerActivityTracker = Depends(get_activity_tracker),
    db: Session = Depends(get_db)
):
    """获取律师活跃度排行榜"""
    try:
        leaderboard = await activity_tracker.get_activity_leaderboard(db, period, limit)
        return leaderboard
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取排行榜失败: {str(e)}")


@router.get("/tasks", summary="获取每日任务")
async def get_daily_tasks(
    current_user: User = Depends(get_current_lawyer),
    db: Session = Depends(get_db)
):
    """获取每日活跃度任务列表和完成情况"""
    try:
        today = date.today()
        
        # 获取任务配置
        from app.services.lawyer_activity_tracker import LawyerActivityTracker
        daily_tasks = LawyerActivityTracker.DAILY_TASKS
        
        # 获取今日完成情况
        completed_tasks = db.execute("""
            SELECT task_type, COUNT(*) as completed_count, SUM(points_earned) as total_points
            FROM lawyer_daily_task_completions 
            WHERE lawyer_id = %s AND completion_date = %s
            GROUP BY task_type
        """, (str(current_user.id), today)).fetchall()
        
        completed_dict = {
            task['task_type']: {
                'completed': task['completed_count'],
                'points': task['total_points']
            }
            for task in completed_tasks
        }
        
        # 构建任务列表
        tasks = []
        total_available_points = 0
        total_earned_points = 0
        
        for task_type, config in daily_tasks.items():
            completed_info = completed_dict.get(task_type, {'completed': 0, 'points': 0})
            max_points = config['points'] * config['max_per_day']
            
            tasks.append({
                'task_type': task_type,
                'description': config['description'],
                'points_per_completion': config['points'],
                'max_per_day': config['max_per_day'],
                'completed_count': completed_info['completed'],
                'earned_points': completed_info['points'],
                'max_points': max_points,
                'progress': min(100, (completed_info['completed'] / config['max_per_day']) * 100),
                'is_completed': completed_info['completed'] >= config['max_per_day']
            })
            
            total_available_points += max_points
            total_earned_points += completed_info['points']
        
        return {
            "tasks": tasks,
            "summary": {
                "total_tasks": len(tasks),
                "completed_tasks": sum(1 for task in tasks if task['is_completed']),
                "total_available_points": total_available_points,
                "total_earned_points": total_earned_points,
                "completion_rate": (sum(1 for task in tasks if task['is_completed']) / len(tasks)) * 100
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取每日任务失败: {str(e)}")


@router.get("/milestones", summary="获取活跃度里程碑")
async def get_activity_milestones(
    current_user: User = Depends(get_current_lawyer),
    db: Session = Depends(get_db)
):
    """获取律师活跃度里程碑达成情况"""
    try:
        # 获取已达成的里程碑
        achieved_milestones = db.execute("""
            SELECT * FROM lawyer_activity_milestones 
            WHERE lawyer_id = %s 
            ORDER BY achieved_date DESC
        """, (str(current_user.id),)).fetchall()
        
        # 获取当前统计数据
        stats = db.execute("""
            SELECT 
                COUNT(DISTINCT activity_date) as total_active_days,
                SUM(total_activity_score) as total_score,
                MAX(total_activity_score) as best_daily_score
            FROM lawyer_daily_activity 
            WHERE lawyer_id = %s
        """, (str(current_user.id),)).fetchone()
        
        # 计算连续活跃天数
        from app.services.lawyer_activity_tracker import LawyerActivityTracker
        activity_tracker = LawyerActivityTracker(None, None)
        consecutive_days = await activity_tracker._get_consecutive_activity_days(current_user.id, db)
        
        # 里程碑配置
        milestone_configs = [
            {'key': 'consecutive_days_7', 'type': 'consecutive_days', 'threshold': 7, 'reward_points': 500, 'title': '连续活跃一周'},
            {'key': 'consecutive_days_30', 'type': 'consecutive_days', 'threshold': 30, 'reward_points': 2000, 'title': '连续活跃一月'},
            {'key': 'total_active_days_100', 'type': 'total_active_days', 'threshold': 100, 'reward_points': 3000, 'title': '累计活跃100天'},
            {'key': 'total_score_10000', 'type': 'total_score', 'threshold': 10000, 'reward_points': 1500, 'title': '累计活跃度10000分'},
            {'key': 'best_daily_score_500', 'type': 'best_daily_score', 'threshold': 500, 'reward_points': 800, 'title': '单日活跃度500分'}
        ]
        
        achieved_keys = {m['milestone_key'] for m in achieved_milestones}
        
        # 构建里程碑状态
        milestones = []
        current_values = {
            'consecutive_days': consecutive_days,
            'total_active_days': stats['total_active_days'] or 0,
            'total_score': stats['total_score'] or 0,
            'best_daily_score': stats['best_daily_score'] or 0
        }
        
        for config in milestone_configs:
            current_value = current_values[config['type']]
            is_achieved = config['key'] in achieved_keys
            
            milestones.append({
                'milestone_key': config['key'],
                'title': config['title'],
                'type': config['type'],
                'threshold': config['threshold'],
                'current_value': current_value,
                'reward_points': config['reward_points'],
                'is_achieved': is_achieved,
                'progress': min(100, (current_value / config['threshold']) * 100),
                'achieved_date': next(
                    (m['achieved_date'].isoformat() for m in achieved_milestones if m['milestone_key'] == config['key']),
                    None
                )
            })
        
        return {
            "milestones": milestones,
            "summary": {
                "total_milestones": len(milestones),
                "achieved_milestones": len(achieved_keys),
                "total_reward_points": sum(m['reward_points'] for m in achieved_milestones),
                "achievement_rate": (len(achieved_keys) / len(milestones)) * 100
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取里程碑失败: {str(e)}")


@router.get("/history", summary="获取活动历史")
async def get_activity_history(
    days: int = Query(30, ge=1, le=90, description="查询天数"),
    activity_type: Optional[str] = Query(None, description="活动类型过滤"),
    current_user: User = Depends(get_current_lawyer),
    db: Session = Depends(get_db)
):
    """获取律师活动历史记录"""
    try:
        start_date = date.today() - timedelta(days=days)
        
        # 构建查询条件
        where_conditions = ["lawyer_id = %s", "activity_date >= %s"]
        params = [str(current_user.id), start_date]
        
        if activity_type:
            where_conditions.append("activity_type = %s")
            params.append(activity_type)
        
        # 获取每日活跃度数据
        daily_activity = db.execute(f"""
            SELECT 
                activity_date,
                total_activity_score,
                activity_count,
                activity_breakdown,
                first_activity_time,
                last_activity_time
            FROM lawyer_daily_activity 
            WHERE {' AND '.join(where_conditions)}
            ORDER BY activity_date DESC
        """, params).fetchall()
        
        # 获取详细活动日志
        activity_logs = db.execute(f"""
            SELECT 
                activity_type,
                activity_date,
                activity_time,
                context,
                quality_score,
                session_duration
            FROM lawyer_activity_logs 
            WHERE {' AND '.join(where_conditions)}
            ORDER BY activity_date DESC, activity_time DESC
            LIMIT 100
        """, params).fetchall()
        
        # 统计数据
        total_score = sum(day['total_activity_score'] for day in daily_activity)
        total_activities = sum(day['activity_count'] for day in daily_activity)
        active_days = len(daily_activity)
        avg_daily_score = total_score / active_days if active_days > 0 else 0
        
        return {
            "daily_activity": [
                {
                    "date": day['activity_date'].isoformat(),
                    "total_score": day['total_activity_score'],
                    "activity_count": day['activity_count'],
                    "activity_breakdown": day['activity_breakdown'] or {},
                    "first_activity": day['first_activity_time'].isoformat() if day['first_activity_time'] else None,
                    "last_activity": day['last_activity_time'].isoformat() if day['last_activity_time'] else None
                }
                for day in daily_activity
            ],
            "recent_activities": [
                {
                    "activity_type": log['activity_type'],
                    "date": log['activity_date'].isoformat(),
                    "time": log['activity_time'].strftime('%H:%M:%S'),
                    "quality_score": log['quality_score'],
                    "session_duration": log['session_duration'],
                    "context": log['context'] or {}
                }
                for log in activity_logs
            ],
            "statistics": {
                "total_score": total_score,
                "total_activities": total_activities,
                "active_days": active_days,
                "avg_daily_score": round(avg_daily_score, 1),
                "query_period_days": days
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取活动历史失败: {str(e)}")


@router.post("/batch-track", summary="批量跟踪活动")
async def batch_track_activities(
    activities: List[ActivityTrackRequest],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_lawyer),
    activity_tracker: LawyerActivityTracker = Depends(get_activity_tracker),
    db: Session = Depends(get_db)
):
    """批量跟踪多个律师活动"""
    try:
        if len(activities) > 50:
            raise HTTPException(status_code=400, detail="单次最多跟踪50个活动")
        
        results = []
        total_points = 0
        
        for activity in activities:
            try:
                # 添加用户信息到上下文
                context = activity.context.copy()
                context.update({
                    'user_id': str(current_user.id),
                    'username': current_user.username,
                    'quality_score': activity.quality_score or 0,
                    'session_duration': activity.session_duration or 0,
                    'timestamp': datetime.now().isoformat(),
                    'batch_tracking': True
                })
                
                # 跟踪活动
                result = await activity_tracker.track_lawyer_activity(
                    current_user.id, activity.activity_type, context, db
                )
                
                results.append({
                    "activity_type": activity.activity_type,
                    "success": True,
                    "result": result
                })
                
                # 累计积分
                if result.get('points_reward', {}).get('points_earned'):
                    total_points += result['points_reward']['points_earned']
                    
            except Exception as e:
                results.append({
                    "activity_type": activity.activity_type,
                    "success": False,
                    "error": str(e)
                })
        
        successful_count = sum(1 for r in results if r['success'])
        
        return {
            "success": True,
            "message": f"批量跟踪完成，成功{successful_count}/{len(activities)}个活动",
            "data": {
                "results": results,
                "summary": {
                    "total_activities": len(activities),
                    "successful_count": successful_count,
                    "failed_count": len(activities) - successful_count,
                    "total_points_earned": total_points
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量跟踪活动失败: {str(e)}")


@router.get("/config", summary="获取活跃度配置")
async def get_activity_config():
    """获取活跃度系统配置信息"""
    try:
        from app.services.lawyer_activity_tracker import LawyerActivityTracker
        
        return {
            "activity_weights": LawyerActivityTracker.ACTIVITY_WEIGHTS,
            "activity_levels": LawyerActivityTracker.ACTIVITY_LEVELS,
            "daily_tasks": LawyerActivityTracker.DAILY_TASKS,
            "supported_activity_types": list(LawyerActivityTracker.ACTIVITY_WEIGHTS.keys()),
            "level_colors": {
                level: config['color'] 
                for level, config in LawyerActivityTracker.ACTIVITY_LEVELS.items()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


# 管理员接口
@router.get("/admin/stats", summary="管理员：获取活跃度统计")
async def get_admin_activity_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """管理员获取全平台活跃度统计"""
    # 检查管理员权限
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    try:
        # 获取活跃度等级分布
        level_distribution = db.execute("""
            SELECT activity_level, COUNT(*) as count
            FROM lawyer_activity_levels 
            GROUP BY activity_level
            ORDER BY 
                CASE activity_level
                    WHEN 'super_active' THEN 6
                    WHEN 'highly_active' THEN 5
                    WHEN 'active' THEN 4
                    WHEN 'moderate' THEN 3
                    WHEN 'low' THEN 2
                    WHEN 'inactive' THEN 1
                    ELSE 0
                END DESC
        """).fetchall()
        
        # 获取每日活跃度趋势（最近30天）
        daily_trends = db.execute("""
            SELECT 
                activity_date,
                COUNT(DISTINCT lawyer_id) as active_lawyers,
                SUM(total_activity_score) as total_score,
                AVG(total_activity_score) as avg_score
            FROM lawyer_daily_activity 
            WHERE activity_date >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY activity_date
            ORDER BY activity_date DESC
        """).fetchall()
        
        # 获取活动类型统计
        activity_type_stats = db.execute("""
            SELECT 
                activity_type,
                COUNT(*) as count,
                COUNT(DISTINCT lawyer_id) as unique_lawyers
            FROM lawyer_activity_logs 
            WHERE activity_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY activity_type
            ORDER BY count DESC
        """).fetchall()
        
        # 获取里程碑达成统计
        milestone_stats = db.execute("""
            SELECT 
                milestone_type,
                COUNT(*) as achieved_count,
                SUM(reward_points) as total_rewards
            FROM lawyer_activity_milestones 
            GROUP BY milestone_type
            ORDER BY achieved_count DESC
        """).fetchall()
        
        return {
            "level_distribution": [
                {
                    "level": row['activity_level'],
                    "count": row['count'],
                    "percentage": 0  # 将在前端计算
                }
                for row in level_distribution
            ],
            "daily_trends": [
                {
                    "date": row['activity_date'].isoformat(),
                    "active_lawyers": row['active_lawyers'],
                    "total_score": row['total_score'] or 0,
                    "avg_score": round(float(row['avg_score'] or 0), 1)
                }
                for row in daily_trends
            ],
            "activity_type_stats": [
                {
                    "activity_type": row['activity_type'],
                    "count": row['count'],
                    "unique_lawyers": row['unique_lawyers']
                }
                for row in activity_type_stats
            ],
            "milestone_stats": [
                {
                    "milestone_type": row['milestone_type'],
                    "achieved_count": row['achieved_count'],
                    "total_rewards": row['total_rewards'] or 0
                }
                for row in milestone_stats
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")