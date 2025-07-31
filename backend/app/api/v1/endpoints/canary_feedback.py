"""
灰度发布反馈收集API
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.feedback import DeploymentFeedback, FeatureUsageStats, ABTestResult, PerformanceMetric
from app.models.user import User
from app.schemas.canary_feedback import (
    FeedbackCreate, FeedbackResponse, FeedbackUpdate,
    FeatureUsageCreate, FeatureUsageResponse,
    ABTestResultCreate, ABTestResultResponse,
    PerformanceMetricCreate, PerformanceMetricResponse,
    FeedbackStats, DeploymentStats
)

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交用户反馈"""
    db_feedback = DeploymentFeedback(
        user_id=current_user.id,
        deployment_phase=feedback.deployment_phase,
        deployment_version=feedback.deployment_version,
        feedback_type=feedback.feedback_type,
        title=feedback.title,
        content=feedback.content,
        rating=feedback.rating,
        severity=feedback.severity,
        affected_module=feedback.affected_module,
        browser_info=feedback.browser_info,
        device_info=feedback.device_info
    )
    
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    return db_feedback


@router.get("/feedback", response_model=List[FeedbackResponse])
async def get_feedback(
    deployment_phase: Optional[str] = Query(None),
    feedback_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取反馈列表"""
    query = db.query(DeploymentFeedback)
    
    if deployment_phase:
        query = query.filter(DeploymentFeedback.deployment_phase == deployment_phase)
    
    if feedback_type:
        query = query.filter(DeploymentFeedback.feedback_type == feedback_type)
    
    if status:
        query = query.filter(DeploymentFeedback.status == status)
    
    # 非管理员只能看到自己的反馈
    if not current_user.is_admin:
        query = query.filter(DeploymentFeedback.user_id == current_user.id)
    
    feedback_list = query.order_by(desc(DeploymentFeedback.created_at)).offset(skip).limit(limit).all()
    return feedback_list


@router.put("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: int,
    feedback_update: FeedbackUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新反馈状态"""
    db_feedback = db.query(DeploymentFeedback).filter(DeploymentFeedback.id == feedback_id).first()
    
    if not db_feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    # 检查权限
    if not current_user.is_admin and db_feedback.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限修改此反馈")
    
    # 更新字段
    for field, value in feedback_update.dict(exclude_unset=True).items():
        setattr(db_feedback, field, value)
    
    if feedback_update.status == "resolved":
        db_feedback.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_feedback)
    
    return db_feedback


@router.get("/feedback/stats", response_model=FeedbackStats)
async def get_feedback_stats(
    deployment_phase: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取反馈统计"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    query = db.query(DeploymentFeedback).filter(DeploymentFeedback.created_at >= start_date)
    
    if deployment_phase:
        query = query.filter(DeploymentFeedback.deployment_phase == deployment_phase)
    
    # 总体统计
    total_feedback = query.count()
    avg_rating = query.filter(DeploymentFeedback.rating.isnot(None)).with_entities(
        func.avg(DeploymentFeedback.rating)
    ).scalar() or 0
    
    # 按类型统计
    feedback_by_type = query.with_entities(
        DeploymentFeedback.feedback_type,
        func.count(DeploymentFeedback.id).label('count')
    ).group_by(DeploymentFeedback.feedback_type).all()
    
    # 按阶段统计
    feedback_by_phase = query.with_entities(
        DeploymentFeedback.deployment_phase,
        func.count(DeploymentFeedback.id).label('count'),
        func.avg(DeploymentFeedback.rating).label('avg_rating')
    ).group_by(DeploymentFeedback.deployment_phase).all()
    
    # 按严重程度统计
    feedback_by_severity = query.with_entities(
        DeploymentFeedback.severity,
        func.count(DeploymentFeedback.id).label('count')
    ).group_by(DeploymentFeedback.severity).all()
    
    return FeedbackStats(
        total_feedback=total_feedback,
        average_rating=round(avg_rating, 2),
        feedback_by_type={item.feedback_type: item.count for item in feedback_by_type},
        feedback_by_phase={item.deployment_phase: {
            'count': item.count,
            'avg_rating': round(item.avg_rating or 0, 2)
        } for item in feedback_by_phase},
        feedback_by_severity={item.severity: item.count for item in feedback_by_severity}
    )


@router.post("/feature-usage", response_model=FeatureUsageResponse)
async def record_feature_usage(
    usage: FeatureUsageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """记录功能使用情况"""
    # 查找现有记录
    existing_usage = db.query(FeatureUsageStats).filter(
        FeatureUsageStats.user_id == current_user.id,
        FeatureUsageStats.feature_name == usage.feature_name,
        FeatureUsageStats.deployment_version == usage.deployment_version
    ).first()
    
    if existing_usage:
        # 更新现有记录
        existing_usage.usage_count += 1
        existing_usage.total_time_spent += usage.time_spent or 0
        existing_usage.last_used_at = datetime.utcnow()
        
        if usage.response_time:
            # 计算平均响应时间
            total_response_time = (existing_usage.avg_response_time or 0) * (existing_usage.usage_count - 1)
            existing_usage.avg_response_time = (total_response_time + usage.response_time) / existing_usage.usage_count
        
        if usage.had_error:
            existing_usage.error_count += 1
        
        # 计算成功率
        existing_usage.success_rate = (existing_usage.usage_count - existing_usage.error_count) / existing_usage.usage_count
        
        db.commit()
        db.refresh(existing_usage)
        return existing_usage
    else:
        # 创建新记录
        db_usage = FeatureUsageStats(
            user_id=current_user.id,
            deployment_version=usage.deployment_version,
            feature_name=usage.feature_name,
            feature_version=usage.feature_version,
            usage_count=1,
            total_time_spent=usage.time_spent or 0,
            last_used_at=datetime.utcnow(),
            avg_response_time=usage.response_time,
            error_count=1 if usage.had_error else 0,
            success_rate=0.0 if usage.had_error else 1.0
        )
        
        db.add(db_usage)
        db.commit()
        db.refresh(db_usage)
        return db_usage


@router.post("/ab-test", response_model=ABTestResultResponse)
async def record_ab_test_result(
    result: ABTestResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """记录A/B测试结果"""
    db_result = ABTestResult(
        user_id=current_user.id,
        test_name=result.test_name,
        variant=result.variant,
        deployment_version=result.deployment_version,
        conversion_event=result.conversion_event,
        converted=result.converted,
        conversion_value=result.conversion_value,
        time_to_conversion=result.time_to_conversion,
        session_duration=result.session_duration,
        page_views=result.page_views,
        clicks=result.clicks,
        bounce_rate=result.bounce_rate
    )
    
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    
    return db_result


@router.post("/performance-metric", response_model=PerformanceMetricResponse)
async def record_performance_metric(
    metric: PerformanceMetricCreate,
    db: Session = Depends(get_db)
):
    """记录性能指标"""
    db_metric = PerformanceMetric(
        deployment_version=metric.deployment_version,
        metric_type=metric.metric_type,
        metric_name=metric.metric_name,
        value=metric.value,
        unit=metric.unit,
        endpoint=metric.endpoint,
        method=metric.method,
        status_code=metric.status_code,
        environment=metric.environment,
        region=metric.region
    )
    
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    
    return db_metric


@router.get("/deployment/stats", response_model=DeploymentStats)
async def get_deployment_stats(
    deployment_version: str,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取部署统计信息"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 用户反馈统计
    feedback_count = db.query(DeploymentFeedback).filter(
        DeploymentFeedback.deployment_version == deployment_version,
        DeploymentFeedback.created_at >= start_date
    ).count()
    
    avg_rating = db.query(func.avg(DeploymentFeedback.rating)).filter(
        DeploymentFeedback.deployment_version == deployment_version,
        DeploymentFeedback.created_at >= start_date,
        DeploymentFeedback.rating.isnot(None)
    ).scalar() or 0
    
    # 功能使用统计
    active_users = db.query(func.count(func.distinct(FeatureUsageStats.user_id))).filter(
        FeatureUsageStats.deployment_version == deployment_version,
        FeatureUsageStats.last_used_at >= start_date
    ).scalar() or 0
    
    total_usage = db.query(func.sum(FeatureUsageStats.usage_count)).filter(
        FeatureUsageStats.deployment_version == deployment_version,
        FeatureUsageStats.last_used_at >= start_date
    ).scalar() or 0
    
    # 性能指标
    avg_response_time = db.query(func.avg(PerformanceMetric.value)).filter(
        PerformanceMetric.deployment_version == deployment_version,
        PerformanceMetric.metric_type == "response_time",
        PerformanceMetric.timestamp >= start_date
    ).scalar() or 0
    
    error_rate = db.query(func.avg(PerformanceMetric.value)).filter(
        PerformanceMetric.deployment_version == deployment_version,
        PerformanceMetric.metric_type == "error_rate",
        PerformanceMetric.timestamp >= start_date
    ).scalar() or 0
    
    return DeploymentStats(
        deployment_version=deployment_version,
        feedback_count=feedback_count,
        average_rating=round(avg_rating, 2),
        active_users=active_users,
        total_usage=total_usage,
        average_response_time=round(avg_response_time, 2),
        error_rate=round(error_rate, 4)
    )