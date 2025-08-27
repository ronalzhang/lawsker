"""
企业客户满意度API

提供企业客户满意度跟踪、分析和改进功能
目标：提升企业客户满意度至95%
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
import logging

from app.core.deps import get_db, get_current_user
from app.services.enterprise_customer_satisfaction_service import EnterpriseCustomerSatisfactionService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/satisfaction/record", response_model=Dict[str, Any])
async def record_customer_satisfaction(
    customer_id: str,
    service_type: str,
    satisfaction_score: float = Query(..., ge=1.0, le=5.0, description="满意度评分 (1-5)"),
    feedback_text: Optional[str] = None,
    service_quality_metrics: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    记录企业客户满意度评分
    
    用于跟踪和分析企业客户对各项服务的满意度
    目标：通过数据驱动的方式提升满意度至95%
    """
    try:
        # 权限检查：只有管理员和客户成功团队可以记录满意度
        if current_user.get("user_type") not in ["admin", "customer_success", "institution"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限记录客户满意度"
            )
        
        # 如果是机构用户，只能记录自己的满意度
        if current_user.get("user_type") == "institution":
            customer_id = current_user.get("id")
        
        service = EnterpriseCustomerSatisfactionService(db)
        result = await service.track_customer_satisfaction(
            customer_id=customer_id,
            service_type=service_type,
            satisfaction_score=satisfaction_score,
            feedback_text=feedback_text,
            service_quality_metrics=service_quality_metrics
        )
        
        return {
            "success": True,
            "data": result,
            "message": "客户满意度记录成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"记录客户满意度失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="记录满意度失败"
        )

@router.get("/satisfaction/analytics", response_model=Dict[str, Any])
async def get_satisfaction_analytics(
    customer_id: Optional[str] = Query(None, description="特定客户ID（可选）"),
    service_type: Optional[str] = Query(None, description="服务类型（可选）"),
    date_range: int = Query(30, ge=1, le=365, description="统计天数范围"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取企业客户满意度分析数据
    
    提供详细的满意度统计、趋势分析和改进建议
    支持按客户、服务类型和时间范围筛选
    """
    try:
        # 权限检查
        if current_user.get("user_type") not in ["admin", "customer_success", "institution"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限查看满意度分析"
            )
        
        # 如果是机构用户，只能查看自己的数据
        if current_user.get("user_type") == "institution":
            customer_id = current_user.get("id")
        
        service = EnterpriseCustomerSatisfactionService(db)
        analytics = await service.get_satisfaction_analytics(
            customer_id=customer_id,
            service_type=service_type,
            date_range=date_range
        )
        
        # 添加API级别的说明
        analytics["api_info"] = {
            "purpose": "企业客户满意度数据分析",
            "target": "提升企业客户满意度至95%",
            "data_usage": "用于服务改进和客户关系管理",
            "disclaimer": [
                "满意度数据基于客户主动反馈",
                "分析结果用于内部服务优化",
                "不构成服务质量承诺或保证"
            ]
        }
        
        return {
            "success": True,
            "data": analytics,
            "message": "满意度分析数据获取成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取满意度分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取分析数据失败"
        )

@router.get("/satisfaction/trends/{customer_id}", response_model=Dict[str, Any])
async def get_customer_satisfaction_trends(
    customer_id: str,
    months: int = Query(6, ge=1, le=24, description="分析月数"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取特定企业客户的满意度趋势分析
    
    提供客户满意度的历史趋势、变化分析和预测建议
    """
    try:
        # 权限检查
        if current_user.get("user_type") not in ["admin", "customer_success"]:
            # 机构用户只能查看自己的趋势
            if current_user.get("user_type") == "institution" and current_user.get("id") != customer_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只能查看自己的满意度趋势"
                )
            elif current_user.get("user_type") not in ["institution"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限查看客户满意度趋势"
                )
        
        service = EnterpriseCustomerSatisfactionService(db)
        trends = await service.get_customer_feedback_trends(
            customer_id=customer_id,
            months=months
        )
        
        return {
            "success": True,
            "data": trends,
            "message": "客户满意度趋势获取成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取客户满意度趋势失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取趋势数据失败"
        )

@router.post("/satisfaction/improve", response_model=Dict[str, Any])
async def implement_satisfaction_improvement(
    customer_id: str,
    improvement_actions: List[Dict[str, Any]],
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    实施客户满意度改进措施
    
    基于分析结果制定和执行具体的改进行动计划
    """
    try:
        # 权限检查：只有管理员和客户成功团队可以实施改进措施
        if current_user.get("user_type") not in ["admin", "customer_success"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限实施改进措施"
            )
        
        service = EnterpriseCustomerSatisfactionService(db)
        result = await service.implement_satisfaction_improvement(
            customer_id=customer_id,
            improvement_actions=improvement_actions
        )
        
        return {
            "success": True,
            "data": result,
            "message": "满意度改进措施实施成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"实施满意度改进措施失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="实施改进措施失败"
        )

@router.get("/satisfaction/dashboard", response_model=Dict[str, Any])
async def get_satisfaction_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取企业客户满意度仪表盘数据
    
    提供整体满意度概览、关键指标和改进进展
    """
    try:
        # 权限检查
        if current_user.get("user_type") not in ["admin", "customer_success"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限查看满意度仪表盘"
            )
        
        service = EnterpriseCustomerSatisfactionService(db)
        
        # 获取整体分析数据
        overall_analytics = await service.get_satisfaction_analytics(date_range=30)
        
        # 获取各服务类型的分析
        service_types = ["data_analysis", "legal_consultation", "document_review"]
        service_analytics = {}
        
        for service_type in service_types:
            service_analytics[service_type] = await service.get_satisfaction_analytics(
                service_type=service_type,
                date_range=30
            )
        
        dashboard_data = {
            "overview": {
                "current_satisfaction_rate": overall_analytics["overall_metrics"]["satisfaction_rate_percent"],
                "target_satisfaction_rate": 95.0,
                "gap_to_target": 95.0 - overall_analytics["overall_metrics"]["satisfaction_rate_percent"],
                "total_responses_this_month": overall_analytics["overall_metrics"]["total_responses"],
                "unique_customers": overall_analytics["overall_metrics"]["unique_customers"]
            },
            "service_performance": service_analytics,
            "improvement_priorities": overall_analytics["improvement_suggestions"],
            "target_achievement": overall_analytics["target_achievement"],
            "key_metrics": {
                "high_satisfaction_rate": overall_analytics["overall_metrics"]["high_satisfaction_rate_percent"],
                "dissatisfaction_rate": overall_analytics["overall_metrics"]["dissatisfaction_rate_percent"],
                "avg_satisfaction_score": overall_analytics["overall_metrics"]["avg_satisfaction_score"]
            }
        }
        
        return {
            "success": True,
            "data": dashboard_data,
            "message": "满意度仪表盘数据获取成功",
            "last_updated": overall_analytics["period"]["end_date"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取满意度仪表盘失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取仪表盘数据失败"
        )

@router.get("/satisfaction/alerts", response_model=Dict[str, Any])
async def get_satisfaction_alerts(
    status_filter: Optional[str] = Query(None, description="警报状态筛选"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取客户满意度警报
    
    显示需要关注的低满意度客户和紧急改进事项
    """
    try:
        # 权限检查
        if current_user.get("user_type") not in ["admin", "customer_success"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限查看满意度警报"
            )
        
        # 构建查询条件
        where_conditions = []
        params = {"limit": limit}
        
        if status_filter:
            where_conditions.append("status = :status")
            params["status"] = status_filter
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = f"""
        SELECT 
            customer_id, service_type, avg_satisfaction_score,
            alert_type, alert_message, created_at, status
        FROM customer_satisfaction_alerts
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit
        """
        
        result = await db.execute(text(query), params)
        rows = result.fetchall()
        
        alerts = [
            {
                "customer_id": row[0],
                "service_type": row[1],
                "avg_satisfaction_score": row[2],
                "alert_type": row[3],
                "alert_message": row[4],
                "created_at": row[5].isoformat() if row[5] else None,
                "status": row[6]
            }
            for row in rows
        ]
        
        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "total_count": len(alerts),
                "active_alerts": len([a for a in alerts if a["status"] == "active"])
            },
            "message": "满意度警报获取成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取满意度警报失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取警报数据失败"
        )