"""
批量任务滥用分析API端点
实现滥用监控、统计分析、90%减少目标跟踪
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from uuid import UUID

from app.core.deps import get_db, get_current_user
from app.services.batch_abuse_monitor import BatchAbuseMonitor, create_batch_abuse_monitor
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


def get_abuse_monitor() -> BatchAbuseMonitor:
    """获取滥用监控服务实例"""
    return create_batch_abuse_monitor()


@router.get("/abuse-reduction-progress", response_model=Dict[str, Any])
async def get_abuse_reduction_progress(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取批量任务滥用减少进度（90%目标跟踪）
    """
    try:
        # 检查管理员权限
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        abuse_monitor = get_abuse_monitor()
        progress = await abuse_monitor.get_abuse_reduction_progress(db)
        
        return {
            "success": True,
            "data": progress,
            "message": "获取滥用减少进度成功"
        }
        
    except Exception as e:
        logger.error(f"获取滥用减少进度失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取进度失败: {str(e)}")


@router.get("/abuse-metrics", response_model=Dict[str, Any])
async def get_abuse_metrics(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定时期的滥用指标统计
    """
    try:
        # 检查管理员权限
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")
        
        if (end_date - start_date).days > 365:
            raise HTTPException(status_code=400, detail="查询时间范围不能超过365天")
        
        abuse_monitor = get_abuse_monitor()
        metrics = await abuse_monitor.calculate_abuse_metrics(start_date, end_date, db)
        
        return {
            "success": True,
            "data": {
                "period": {
                    "start_date": metrics.period_start.isoformat(),
                    "end_date": metrics.period_end.isoformat(),
                    "days": (metrics.period_end - metrics.period_start).days + 1
                },
                "statistics": {
                    "total_batch_uploads": metrics.total_batch_uploads,
                    "abusive_uploads": metrics.abusive_uploads,
                    "abuse_rate": round(metrics.abuse_rate * 100, 2),  # 转换为百分比
                    "credits_prevented_abuse": metrics.credits_prevented_abuse,
                    "estimated_cost_savings": float(metrics.estimated_cost_savings)
                },
                "analysis": {
                    "abuse_level": self._get_abuse_level(metrics.abuse_rate),
                    "trend": "improving" if metrics.abuse_rate < 0.1 else "concerning",
                    "credits_effectiveness": "high" if metrics.credits_prevented_abuse > 0 else "low"
                }
            },
            "message": "获取滥用指标成功"
        }
        
    except Exception as e:
        logger.error(f"获取滥用指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取指标失败: {str(e)}")


@router.get("/user-abuse-patterns/{user_id}", response_model=Dict[str, Any])
async def get_user_abuse_patterns(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取特定用户的滥用模式分析
    """
    try:
        # 检查权限（管理员或用户本人）
        if not current_user.get("is_admin", False) and current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="权限不足")
        
        abuse_monitor = get_abuse_monitor()
        patterns = await abuse_monitor.detect_abuse_patterns(UUID(user_id), db)
        
        # 转换为可序列化的格式
        pattern_data = []
        for pattern in patterns:
            pattern_data.append({
                "pattern_type": pattern.pattern_type,
                "severity": pattern.severity.value,
                "description": pattern.description,
                "indicators": pattern.indicators,
                "confidence_score": pattern.confidence_score
            })
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "patterns_detected": len(pattern_data),
                "patterns": pattern_data,
                "risk_level": self._calculate_user_risk_level(pattern_data),
                "recommendations": self._get_user_recommendations(pattern_data)
            },
            "message": "获取用户滥用模式成功"
        }
        
    except Exception as e:
        logger.error(f"获取用户滥用模式失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模式失败: {str(e)}")


@router.get("/abuse-trends", response_model=Dict[str, Any])
async def get_abuse_trends(
    days: int = Query(30, ge=7, le=365, description="统计天数"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取滥用趋势分析（按天统计）
    """
    try:
        # 检查管理员权限
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        abuse_monitor = get_abuse_monitor()
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        # 按天计算趋势数据
        trend_data = []
        current_date = start_date
        
        while current_date <= end_date:
            daily_metrics = await abuse_monitor.calculate_abuse_metrics(current_date, current_date, db)
            
            trend_data.append({
                "date": current_date.isoformat(),
                "total_uploads": daily_metrics.total_batch_uploads,
                "abusive_uploads": daily_metrics.abusive_uploads,
                "abuse_rate": round(daily_metrics.abuse_rate * 100, 2),
                "credits_prevented": daily_metrics.credits_prevented_abuse
            })
            
            current_date += timedelta(days=1)
        
        # 计算趋势指标
        recent_7_days = trend_data[-7:]
        previous_7_days = trend_data[-14:-7] if len(trend_data) >= 14 else []
        
        recent_avg_abuse_rate = sum(d["abuse_rate"] for d in recent_7_days) / len(recent_7_days)
        previous_avg_abuse_rate = sum(d["abuse_rate"] for d in previous_7_days) / len(previous_7_days) if previous_7_days else recent_avg_abuse_rate
        
        trend_direction = "improving" if recent_avg_abuse_rate < previous_avg_abuse_rate else "worsening"
        
        return {
            "success": True,
            "data": {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                },
                "trend_data": trend_data,
                "summary": {
                    "recent_7_days_avg_abuse_rate": round(recent_avg_abuse_rate, 2),
                    "previous_7_days_avg_abuse_rate": round(previous_avg_abuse_rate, 2),
                    "trend_direction": trend_direction,
                    "improvement_rate": round(((previous_avg_abuse_rate - recent_avg_abuse_rate) / max(0.01, previous_avg_abuse_rate)) * 100, 2)
                }
            },
            "message": "获取滥用趋势成功"
        }
        
    except Exception as e:
        logger.error(f"获取滥用趋势失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取趋势失败: {str(e)}")


@router.get("/credits-effectiveness", response_model=Dict[str, Any])
async def get_credits_effectiveness(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取Credits系统防滥用效果分析
    """
    try:
        # 检查管理员权限
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        from sqlalchemy import text
        
        # 获取Credits系统统计数据
        stats_query = text("""
            SELECT 
                COUNT(DISTINCT uc.user_id) as total_users_with_credits,
                SUM(uc.credits_purchased) as total_credits_purchased,
                SUM(uc.total_credits_used) as total_credits_used,
                COUNT(CASE WHEN uc.credits_remaining = 0 THEN 1 END) as users_with_zero_credits,
                AVG(uc.credits_remaining) as avg_credits_remaining
            FROM user_credits uc
        """)
        
        stats_result = db.execute(stats_query).fetchone()
        
        # 获取被Credits阻止的上传尝试（估算）
        blocked_attempts_query = text("""
            SELECT COUNT(*) as blocked_attempts
            FROM user_credits uc
            WHERE uc.credits_remaining = 0
            AND uc.updated_at > NOW() - INTERVAL '30 days'
        """)
        
        blocked_attempts = db.execute(blocked_attempts_query).scalar() or 0
        
        # 计算Credits购买转化率
        purchase_query = text("""
            SELECT 
                COUNT(DISTINCT cpr.user_id) as users_purchased,
                SUM(cpr.total_amount) as total_revenue
            FROM credit_purchase_records cpr
            WHERE cpr.status = 'paid'
            AND cpr.created_at > NOW() - INTERVAL '30 days'
        """)
        
        purchase_result = db.execute(purchase_query).fetchone()
        
        if stats_result:
            total_users, total_purchased, total_used, zero_credits_users, avg_remaining = stats_result
            
            # 计算效果指标
            usage_rate = (total_used / max(1, total_purchased + total_users)) * 100  # 使用率
            purchase_conversion = (purchase_result[0] / max(1, total_users)) * 100 if purchase_result else 0  # 购买转化率
            
            return {
                "success": True,
                "data": {
                    "user_statistics": {
                        "total_users_with_credits": total_users,
                        "users_with_zero_credits": zero_credits_users,
                        "zero_credits_percentage": round((zero_credits_users / max(1, total_users)) * 100, 2)
                    },
                    "credits_usage": {
                        "total_credits_purchased": total_purchased,
                        "total_credits_used": total_used,
                        "average_credits_remaining": round(float(avg_remaining or 0), 2),
                        "usage_rate_percentage": round(usage_rate, 2)
                    },
                    "abuse_prevention": {
                        "estimated_blocked_attempts": blocked_attempts,
                        "estimated_abuse_prevented": int(blocked_attempts * 0.25),  # 假设25%的阻止是滥用
                        "cost_savings_estimate": blocked_attempts * 5.0  # 每次阻止节省5元
                    },
                    "revenue_impact": {
                        "users_purchased_credits": purchase_result[0] if purchase_result else 0,
                        "total_credits_revenue": float(purchase_result[1] or 0) if purchase_result else 0,
                        "purchase_conversion_rate": round(purchase_conversion, 2)
                    },
                    "effectiveness_score": self._calculate_effectiveness_score(
                        usage_rate, purchase_conversion, blocked_attempts
                    )
                },
                "message": "获取Credits效果分析成功"
            }
        else:
            return {
                "success": True,
                "data": {
                    "message": "暂无Credits系统数据"
                }
            }
        
    except Exception as e:
        logger.error(f"获取Credits效果分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取效果分析失败: {str(e)}")


@router.post("/manual-abuse-check/{user_id}", response_model=Dict[str, Any])
async def manual_abuse_check(
    user_id: str,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    手动触发用户滥用检查
    """
    try:
        # 检查管理员权限
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        abuse_monitor = get_abuse_monitor()
        
        # 在后台执行滥用检查
        background_tasks.add_task(
            perform_abuse_check,
            UUID(user_id), abuse_monitor, db
        )
        
        return {
            "success": True,
            "message": f"已启动用户 {user_id} 的滥用检查任务"
        }
        
    except Exception as e:
        logger.error(f"手动滥用检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"检查失败: {str(e)}")


async def perform_abuse_check(user_id: UUID, abuse_monitor: BatchAbuseMonitor, db: Session):
    """执行滥用检查（后台任务）"""
    try:
        patterns = await abuse_monitor.detect_abuse_patterns(user_id, db)
        
        if patterns:
            await abuse_monitor.record_abuse_incident(user_id, patterns, db)
            logger.info(f"用户 {user_id} 滥用检查完成，发现 {len(patterns)} 个滥用模式")
        else:
            logger.info(f"用户 {user_id} 滥用检查完成，未发现滥用行为")
            
    except Exception as e:
        logger.error(f"执行滥用检查失败: {str(e)}")


def _get_abuse_level(abuse_rate: float) -> str:
    """根据滥用率确定滥用等级"""
    if abuse_rate < 0.05:
        return "low"
    elif abuse_rate < 0.15:
        return "medium"
    elif abuse_rate < 0.30:
        return "high"
    else:
        return "critical"


def _calculate_user_risk_level(patterns: List[Dict[str, Any]]) -> str:
    """计算用户风险等级"""
    if not patterns:
        return "low"
    
    high_severity_count = sum(1 for p in patterns if p["severity"] == "high")
    critical_severity_count = sum(1 for p in patterns if p["severity"] == "critical")
    
    if critical_severity_count > 0:
        return "critical"
    elif high_severity_count > 1:
        return "high"
    elif high_severity_count > 0 or len(patterns) > 2:
        return "medium"
    else:
        return "low"


def _get_user_recommendations(patterns: List[Dict[str, Any]]) -> List[str]:
    """获取用户改进建议"""
    recommendations = []
    
    pattern_types = [p["pattern_type"] for p in patterns]
    
    if "frequency_abuse_daily" in pattern_types or "frequency_abuse_hourly" in pattern_types:
        recommendations.append("建议减少上传频率，合理安排批量任务")
    
    if "quality_abuse_small_files" in pattern_types:
        recommendations.append("请确保上传的文件包含有效内容，避免空文件或测试文件")
    
    if "duplicate_content_abuse" in pattern_types:
        recommendations.append("避免重复上传相同内容的文件")
    
    if "suspicious_filename_abuse" in pattern_types:
        recommendations.append("使用有意义的文件名，避免测试或垃圾文件名")
    
    if not recommendations:
        recommendations.append("继续保持良好的使用习惯")
    
    return recommendations


def _calculate_effectiveness_score(usage_rate: float, purchase_conversion: float, blocked_attempts: int) -> Dict[str, Any]:
    """计算Credits系统效果评分"""
    # 使用率评分 (0-40分)
    usage_score = min(40, usage_rate * 0.4)
    
    # 购买转化率评分 (0-30分)
    conversion_score = min(30, purchase_conversion * 3)
    
    # 滥用阻止评分 (0-30分)
    prevention_score = min(30, blocked_attempts * 0.1)
    
    total_score = usage_score + conversion_score + prevention_score
    
    if total_score >= 80:
        grade = "A"
        description = "效果优秀"
    elif total_score >= 60:
        grade = "B"
        description = "效果良好"
    elif total_score >= 40:
        grade = "C"
        description = "效果一般"
    else:
        grade = "D"
        description = "需要改进"
    
    return {
        "total_score": round(total_score, 1),
        "grade": grade,
        "description": description,
        "breakdown": {
            "usage_score": round(usage_score, 1),
            "conversion_score": round(conversion_score, 1),
            "prevention_score": round(prevention_score, 1)
        }
    }