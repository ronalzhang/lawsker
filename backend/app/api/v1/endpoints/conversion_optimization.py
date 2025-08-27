"""
Conversion Optimization API Endpoints
用户注册转化率优化API端点

Provides endpoints for tracking and optimizing user registration conversion rates.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...core.database import get_db
from ...services.conversion_optimization_service import ConversionOptimizationService
from ...core.deps import get_current_user

router = APIRouter()


class ConversionEventRequest(BaseModel):
    """转化事件请求模型"""
    event_type: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ABTestRequest(BaseModel):
    """A/B测试请求模型"""
    test_name: str
    variant: str
    user_id: str
    converted: bool
    metadata: Optional[Dict[str, Any]] = None


@router.post("/track-event")
async def track_conversion_event(
    request: ConversionEventRequest,
    db: Session = Depends(get_db)
):
    """跟踪转化事件"""
    
    service = ConversionOptimizationService(db)
    
    try:
        result = await service.track_conversion_event(
            event_type=request.event_type,
            user_id=request.user_id,
            session_id=request.session_id,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "message": "转化事件已记录",
            "event_data": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记录转化事件失败: {str(e)}")


@router.get("/metrics")
async def get_conversion_metrics(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取转化率指标"""
    
    # Parse dates
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的开始日期格式")
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的结束日期格式")
    
    service = ConversionOptimizationService(db)
    
    try:
        metrics = await service.get_conversion_metrics(start_dt, end_dt)
        return metrics
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取转化率指标失败: {str(e)}")


@router.get("/recommendations")
async def get_optimization_recommendations(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取优化建议"""
    
    service = ConversionOptimizationService(db)
    
    try:
        recommendations = await service.get_optimization_recommendations()
        return {
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取优化建议失败: {str(e)}")


@router.get("/report")
async def get_conversion_report(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """生成转化率报告"""
    
    service = ConversionOptimizationService(db)
    
    try:
        report = await service.generate_conversion_report()
        return report
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成转化率报告失败: {str(e)}")


@router.post("/ab-test")
async def track_ab_test_result(
    request: ABTestRequest,
    db: Session = Depends(get_db)
):
    """跟踪A/B测试结果"""
    
    service = ConversionOptimizationService(db)
    
    try:
        result = await service.track_ab_test_result(
            test_name=request.test_name,
            variant=request.variant,
            user_id=request.user_id,
            converted=request.converted,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "message": "A/B测试结果已记录",
            "result": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记录A/B测试结果失败: {str(e)}")


@router.get("/funnel-analysis")
async def get_registration_funnel_analysis(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取注册漏斗分析"""
    
    service = ConversionOptimizationService(db)
    
    try:
        analysis = await service.get_registration_funnel_analysis()
        return analysis
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取漏斗分析失败: {str(e)}")


@router.get("/dashboard")
async def get_conversion_dashboard(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取转化率优化仪表盘数据"""
    
    service = ConversionOptimizationService(db)
    
    try:
        # Get all dashboard data
        metrics = await service.get_conversion_metrics()
        recommendations = await service.get_optimization_recommendations()
        funnel = await service.get_registration_funnel_analysis()
        
        # Calculate key insights
        current_rate = metrics['metrics']['registration_conversion_rate']
        target_rate = metrics['targets']['registration_rate_target']
        improvement_needed = target_rate - current_rate
        
        dashboard_data = {
            "overview": {
                "current_conversion_rate": current_rate,
                "target_conversion_rate": target_rate,
                "improvement_needed": round(improvement_needed, 2),
                "target_progress": min((current_rate / target_rate) * 100, 100),
                "status": "on_track" if improvement_needed <= 2 else "needs_attention"
            },
            "metrics": metrics,
            "funnel": funnel,
            "recommendations": recommendations[:3],  # Top 3 recommendations
            "quick_wins": [
                {
                    "title": "启用优化版注册页面",
                    "description": "使用 unified-auth-optimized.html 替换当前注册页面",
                    "impact": "预计提升 15-25% 转化率",
                    "effort": "低"
                },
                {
                    "title": "突出演示账户功能",
                    "description": "将演示按钮放在页面顶部显眼位置",
                    "impact": "预计提升 10-15% 转化率",
                    "effort": "低"
                },
                {
                    "title": "简化注册流程",
                    "description": "将3步注册流程合并为2步",
                    "impact": "预计提升 20-30% 转化率",
                    "effort": "中"
                }
            ],
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return dashboard_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表盘数据失败: {str(e)}")


@router.get("/config")
async def get_optimization_config():
    """获取转化率优化配置"""
    
    from ...services.conversion_optimization_service import get_conversion_optimization_config
    
    config = get_conversion_optimization_config()
    return config


@router.post("/simulate-improvement")
async def simulate_conversion_improvement(
    current_visitors: int = Query(..., description="当前访问者数量"),
    current_rate: float = Query(..., description="当前转化率 (%)"),
    target_improvement: float = Query(40.0, description="目标改进百分比"),
    db: Session = Depends(get_db)
):
    """模拟转化率改进效果"""
    
    try:
        # Calculate projections
        current_conversions = int(current_visitors * (current_rate / 100))
        target_rate = current_rate * (1 + target_improvement / 100)
        target_conversions = int(current_visitors * (target_rate / 100))
        additional_conversions = target_conversions - current_conversions
        
        # Estimate revenue impact (assuming average value per conversion)
        avg_value_per_conversion = 500  # RMB, estimated
        revenue_impact = additional_conversions * avg_value_per_conversion
        
        simulation = {
            "current_state": {
                "visitors": current_visitors,
                "conversion_rate": current_rate,
                "conversions": current_conversions,
                "estimated_revenue": current_conversions * avg_value_per_conversion
            },
            "target_state": {
                "visitors": current_visitors,
                "conversion_rate": round(target_rate, 2),
                "conversions": target_conversions,
                "estimated_revenue": target_conversions * avg_value_per_conversion
            },
            "improvement": {
                "rate_improvement": round(target_rate - current_rate, 2),
                "additional_conversions": additional_conversions,
                "revenue_impact": revenue_impact,
                "percentage_improvement": target_improvement
            },
            "timeline": {
                "phase_1": "优化注册页面 (1-2周)",
                "phase_2": "增强演示体验 (2-3周)",
                "phase_3": "A/B测试优化 (3-4周)",
                "expected_completion": "4-6周内达到目标"
            }
        }
        
        return simulation
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模拟计算失败: {str(e)}")