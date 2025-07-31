"""
告警管理API端点
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.core.database import get_db
from app.core.auth import get_current_admin_user
from app.models.alert import Alert, AlertSilence
from app.services.alert_manager import alert_manager, AlertData
from app.schemas.alert import (
    AlertResponse, AlertListResponse, AlertSilenceRequest,
    AlertSilenceResponse, AlertStatsResponse
)

router = APIRouter()


@router.get("/", response_model=AlertListResponse)
async def get_alerts(
    status: Optional[str] = Query(None, description="告警状态过滤"),
    severity: Optional[str] = Query(None, description="严重级别过滤"),
    service: Optional[str] = Query(None, description="服务过滤"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """获取告警列表"""
    try:
        # 构建查询条件
        conditions = []
        if status:
            conditions.append(Alert.status == status)
        if severity:
            conditions.append(Alert.severity == severity)
        if service:
            conditions.append(Alert.service == service)
        
        # 查询告警
        query = select(Alert).where(and_(*conditions) if conditions else True)
        query = query.order_by(desc(Alert.created_at)).offset(offset).limit(limit)
        
        result = await db.execute(query)
        alerts = result.scalars().all()
        
        # 查询总数
        count_query = select(Alert).where(and_(*conditions) if conditions else True)
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())
        
        return AlertListResponse(
            alerts=[AlertResponse.from_orm(alert) for alert in alerts],
            total=total,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警列表失败: {str(e)}")


@router.get("/active", response_model=List[AlertResponse])
async def get_active_alerts(
    current_user = Depends(get_current_admin_user)
):
    """获取活跃告警列表"""
    try:
        active_alerts = await alert_manager.get_active_alerts()
        return [
            AlertResponse(
                id=alert.alert_id,
                alert_id=alert.alert_id,
                name=alert.name,
                severity=alert.severity.value,
                status=alert.status.value,
                message=alert.message,
                description=alert.description,
                service=alert.service,
                labels=alert.labels,
                annotations=alert.annotations,
                created_at=alert.timestamp
            )
            for alert in active_alerts
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取活跃告警失败: {str(e)}")


@router.get("/stats", response_model=AlertStatsResponse)
async def get_alert_stats(
    hours: int = Query(24, ge=1, le=168, description="统计时间范围(小时)"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """获取告警统计信息"""
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # 查询指定时间范围内的告警
        query = select(Alert).where(Alert.created_at >= start_time)
        result = await db.execute(query)
        alerts = result.scalars().all()
        
        # 统计各种指标
        total_alerts = len(alerts)
        critical_alerts = len([a for a in alerts if a.severity == 'critical'])
        warning_alerts = len([a for a in alerts if a.severity == 'warning'])
        info_alerts = len([a for a in alerts if a.severity == 'info'])
        
        resolved_alerts = len([a for a in alerts if a.status == 'resolved'])
        active_alerts = len(await alert_manager.get_active_alerts())
        
        # 按服务统计
        service_stats = {}
        for alert in alerts:
            service = alert.service or 'unknown'
            if service not in service_stats:
                service_stats[service] = 0
            service_stats[service] += 1
        
        return AlertStatsResponse(
            total_alerts=total_alerts,
            active_alerts=active_alerts,
            resolved_alerts=resolved_alerts,
            critical_alerts=critical_alerts,
            warning_alerts=warning_alerts,
            info_alerts=info_alerts,
            service_stats=service_stats,
            time_range_hours=hours
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警统计失败: {str(e)}")


@router.post("/webhook")
async def alert_webhook(
    alerts: List[dict] = Body(..., description="Prometheus告警数据")
):
    """接收Prometheus告警webhook"""
    try:
        processed_count = 0
        
        for alert_data in alerts:
            success = await alert_manager.process_alert(alert_data)
            if success:
                processed_count += 1
        
        return {
            "message": f"处理完成，成功处理 {processed_count}/{len(alerts)} 个告警",
            "processed": processed_count,
            "total": len(alerts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理告警webhook失败: {str(e)}")


@router.post("/{alert_id}/silence", response_model=AlertSilenceResponse)
async def silence_alert(
    alert_id: str,
    silence_request: AlertSilenceRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """静默告警"""
    try:
        # 静默告警
        success = await alert_manager.silence_alert(
            alert_id, 
            silence_request.duration_minutes
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="告警不存在或已解决")
        
        # 记录静默信息
        silence = AlertSilence(
            alert_id=alert_id,
            comment=silence_request.comment,
            created_by=current_user.username,
            starts_at=datetime.utcnow(),
            ends_at=datetime.utcnow() + timedelta(minutes=silence_request.duration_minutes)
        )
        
        db.add(silence)
        await db.commit()
        await db.refresh(silence)
        
        return AlertSilenceResponse.from_orm(silence)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"静默告警失败: {str(e)}")


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user = Depends(get_current_admin_user)
):
    """手动解决告警"""
    try:
        success = await alert_manager.resolve_alert(alert_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="告警不存在或已解决")
        
        return {"message": f"告警 {alert_id} 已手动解决"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解决告警失败: {str(e)}")


@router.get("/silences", response_model=List[AlertSilenceResponse])
async def get_alert_silences(
    active_only: bool = Query(True, description="仅显示活跃的静默"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """获取告警静默列表"""
    try:
        query = select(AlertSilence)
        
        if active_only:
            now = datetime.utcnow()
            query = query.where(
                and_(
                    AlertSilence.starts_at <= now,
                    AlertSilence.ends_at > now
                )
            )
        
        query = query.order_by(desc(AlertSilence.created_at))
        
        result = await db.execute(query)
        silences = result.scalars().all()
        
        return [AlertSilenceResponse.from_orm(silence) for silence in silences]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取静默列表失败: {str(e)}")


@router.delete("/silences/{silence_id}")
async def delete_alert_silence(
    silence_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """删除告警静默"""
    try:
        # 查找静默记录
        query = select(AlertSilence).where(AlertSilence.id == silence_id)
        result = await db.execute(query)
        silence = result.scalar_one_or_none()
        
        if not silence:
            raise HTTPException(status_code=404, detail="静默记录不存在")
        
        # 删除静默记录
        await db.delete(silence)
        await db.commit()
        
        return {"message": f"静默记录 {silence_id} 已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除静默记录失败: {str(e)}")


@router.get("/history", response_model=List[AlertResponse])
async def get_alert_history(
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    current_user = Depends(get_current_admin_user)
):
    """获取告警历史"""
    try:
        history = await alert_manager.get_alert_history(limit)
        
        return [
            AlertResponse(
                id=alert.alert_id,
                alert_id=alert.alert_id,
                name=alert.name,
                severity=alert.severity.value,
                status=alert.status.value,
                message=alert.message,
                description=alert.description,
                service=alert.service,
                labels=alert.labels,
                annotations=alert.annotations,
                created_at=alert.timestamp
            )
            for alert in history
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警历史失败: {str(e)}")