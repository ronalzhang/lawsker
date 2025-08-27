"""
Demo Conversion Optimization API Endpoints
演示账户转化优化API端点

Provides endpoints for tracking and optimizing demo account conversion rates
to achieve the 30% conversion target.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime

from app.core.deps import get_db
from app.services.demo_conversion_optimization_service import DemoConversionOptimizationService

router = APIRouter()


class DemoConversionEventRequest(BaseModel):
    """演示转化事件请求模型"""
    workspace_id: str
    event_type: str
    event_data: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class ConversionSuccessRequest(BaseModel):
    """转化成功请求模型"""
    workspace_id: str
    user_id: str
    conversion_source: str = 'demo'


class ABTestAssignmentRequest(BaseModel):
    """A/B测试分配请求模型"""
    workspace_id: str
    session_id: str
    demo_type: str


@router.post("/track-event")
async def track_demo_conversion_event(
    request: DemoConversionEventRequest,
    db: AsyncSession = Depends(get_db)
):
    """跟踪演示账户转化事件"""
    
    service = DemoConversionOptimizationService(db)
    
    try:
        result = await service.track_demo_conversion_event(
            workspace_id=request.workspace_id,
            event_type=request.event_type,
            event_data=request.event_data,
            session_id=request.session_id
        )
        
        return {
            "success": True,
            "message": "演示转化事件已记录",
            "data": result
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"记录转化事件失败: {str(e)}"
        )


@router.post("/record-conversion")
async def record_conversion_success(
    request: ConversionSuccessRequest,
    db: AsyncSession = Depends(get_db)
):
    """记录转化成功"""
    
    service = DemoConversionOptimizationService(db)
    
    try:
        result = await service.record_conversion_success(
            workspace_id=request.workspace_id,
            user_id=request.user_id,
            conversion_source=request.conversion_source
        )
        
        return {
            "success": True,
            "message": "转化成功已记录",
            "data": result
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"记录转化成功失败: {str(e)}"
        )


@router.get("/metrics")
async def get_demo_conversion_metrics(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    demo_type: Optional[str] = Query(None, description="演示类型 (lawyer/user)"),
    db: AsyncSession = Depends(get_db)
):
    """获取演示账户转化指标"""
    
    # Parse dates
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的开始日期格式"
            )
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的结束日期格式"
            )
    
    service = DemoConversionOptimizationService(db)
    
    try:
        metrics = await service.get_demo_conversion_metrics(
            start_date=start_dt,
            end_date=end_dt,
            demo_type=demo_type
        )
        
        return {
            "success": True,
            "data": metrics
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取转化指标失败: {str(e)}"
        )


@router.get("/recommendations")
async def get_conversion_recommendations(
    current_rate: Optional[float] = Query(None, description="当前转化率"),
    db: AsyncSession = Depends(get_db)
):
    """获取转化优化建议"""
    
    service = DemoConversionOptimizationService(db)
    
    try:
        # If no current rate provided, get it from metrics
        if current_rate is None:
            metrics = await service.get_demo_conversion_metrics()
            current_rate = metrics['metrics']['conversion_rate']
        
        recommendations = await service.get_conversion_optimization_recommendations(
            current_rate
        )
        
        return {
            "success": True,
            "data": {
                "current_rate": current_rate,
                "target_rate": service.conversion_target,
                "recommendations": recommendations
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取优化建议失败: {str(e)}"
        )


@router.get("/ab-test/variants")
async def get_ab_test_variants(
    db: AsyncSession = Depends(get_db)
):
    """获取A/B测试变体"""
    
    service = DemoConversionOptimizationService(db)
    
    try:
        variants = await service.generate_ab_test_variants()
        
        return {
            "success": True,
            "data": {
                "variants": variants,
                "default_variant": "control"
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取A/B测试变体失败: {str(e)}"
        )


@router.post("/ab-test/assign")
async def assign_ab_test_variant(
    request: ABTestAssignmentRequest,
    db: AsyncSession = Depends(get_db)
):
    """分配A/B测试变体"""
    
    try:
        # Simple hash-based assignment for consistent user experience
        import hashlib
        
        hash_input = f"{request.workspace_id}-{request.session_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        variants = ['control', 'aggressive_prompts', 'reward_focused', 'social_proof']
        assigned_variant = variants[hash_value % len(variants)]
        
        return {
            "success": True,
            "data": {
                "assigned_variant": assigned_variant,
                "workspace_id": request.workspace_id,
                "session_id": request.session_id
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分配A/B测试变体失败: {str(e)}"
        )


@router.get("/conversion-prompt/{workspace_id}")
async def get_conversion_prompt(
    workspace_id: str,
    event_type: str = Query(..., description="触发事件类型"),
    session_data: Optional[str] = Query(None, description="会话数据JSON"),
    db: AsyncSession = Depends(get_db)
):
    """获取转化提示"""
    
    service = DemoConversionOptimizationService(db)
    
    try:
        # Parse session data if provided
        event_data = {}
        if session_data:
            import json
            try:
                event_data = json.loads(session_data)
            except json.JSONDecodeError:
                pass
        
        # Evaluate conversion trigger
        conversion_prompt = await service.evaluate_conversion_trigger(
            workspace_id=workspace_id,
            event_type=event_type,
            event_data=event_data
        )
        
        return {
            "success": True,
            "data": {
                "show_prompt": conversion_prompt is not None,
                "prompt": conversion_prompt
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取转化提示失败: {str(e)}"
        )


@router.get("/dashboard")
async def get_demo_conversion_dashboard(
    db: AsyncSession = Depends(get_db)
):
    """获取演示转化仪表盘数据"""
    
    service = DemoConversionOptimizationService(db)
    
    try:
        # Get conversion metrics
        metrics = await service.get_demo_conversion_metrics()
        
        # Get recommendations
        current_rate = metrics['metrics']['conversion_rate']
        recommendations = await service.get_conversion_optimization_recommendations(
            current_rate
        )
        
        # Get A/B test variants
        variants = await service.generate_ab_test_variants()
        
        # Calculate progress towards target
        target_rate = service.conversion_target
        progress = min((current_rate / target_rate) * 100, 100)
        
        dashboard_data = {
            "overview": {
                "current_conversion_rate": current_rate,
                "target_conversion_rate": target_rate,
                "target_progress": round(progress, 1),
                "gap_to_target": round(target_rate - current_rate, 2),
                "status": metrics['performance_status'],
                "target_achieved": metrics['metrics']['target_achieved']
            },
            "metrics": metrics,
            "recommendations": recommendations[:3],  # Top 3 recommendations
            "ab_test_variants": variants,
            "quick_actions": [
                {
                    "title": "启用智能转化提示",
                    "description": "在关键时刻显示个性化转化提示",
                    "impact": "预计提升 8-12% 转化率",
                    "action": "enable_smart_prompts"
                },
                {
                    "title": "实施退出意图检测",
                    "description": "检测用户离开意图并显示挽留提示",
                    "impact": "预计提升 5-8% 转化率",
                    "action": "enable_exit_intent"
                },
                {
                    "title": "增加注册激励",
                    "description": "为演示用户提供注册专属优惠",
                    "impact": "预计提升 10-15% 转化率",
                    "action": "add_registration_incentives"
                }
            ],
            "conversion_funnel": {
                "demo_access": metrics['metrics']['demo_access_count'],
                "engaged_users": int(metrics['metrics']['demo_access_count'] * 0.7),
                "conversion_attempts": int(metrics['metrics']['demo_access_count'] * 0.4),
                "successful_conversions": metrics['metrics']['conversion_count']
            },
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "data": dashboard_data
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取仪表盘数据失败: {str(e)}"
        )


@router.post("/simulate-optimization")
async def simulate_conversion_optimization(
    current_access: int = Query(..., description="当前演示访问量"),
    current_rate: float = Query(..., description="当前转化率 (%)"),
    target_rate: float = Query(30.0, description="目标转化率 (%)"),
    db: AsyncSession = Depends(get_db)
):
    """模拟转化优化效果"""
    
    try:
        # Calculate current and target conversions
        current_conversions = int(current_access * (current_rate / 100))
        target_conversions = int(current_access * (target_rate / 100))
        additional_conversions = target_conversions - current_conversions
        
        # Estimate revenue impact
        avg_value_per_conversion = 800  # RMB, estimated value per converted user
        revenue_impact = additional_conversions * avg_value_per_conversion
        
        # Calculate improvement strategies
        improvement_needed = target_rate - current_rate
        
        strategies = []
        if improvement_needed > 0:
            strategies = [
                {
                    "strategy": "智能转化提示系统",
                    "expected_improvement": min(improvement_needed * 0.4, 8),
                    "implementation_time": "1-2周",
                    "difficulty": "中等"
                },
                {
                    "strategy": "退出意图检测",
                    "expected_improvement": min(improvement_needed * 0.3, 6),
                    "implementation_time": "1周",
                    "difficulty": "简单"
                },
                {
                    "strategy": "注册激励优化",
                    "expected_improvement": min(improvement_needed * 0.5, 10),
                    "implementation_time": "2-3周",
                    "difficulty": "中等"
                },
                {
                    "strategy": "A/B测试优化",
                    "expected_improvement": min(improvement_needed * 0.2, 4),
                    "implementation_time": "3-4周",
                    "difficulty": "复杂"
                }
            ]
        
        simulation = {
            "current_state": {
                "demo_access": current_access,
                "conversion_rate": current_rate,
                "conversions": current_conversions,
                "estimated_revenue": current_conversions * avg_value_per_conversion
            },
            "target_state": {
                "demo_access": current_access,
                "conversion_rate": target_rate,
                "conversions": target_conversions,
                "estimated_revenue": target_conversions * avg_value_per_conversion
            },
            "improvement": {
                "rate_improvement": round(improvement_needed, 2),
                "additional_conversions": additional_conversions,
                "revenue_impact": revenue_impact,
                "percentage_increase": round((additional_conversions / current_conversions * 100) if current_conversions > 0 else 0, 1)
            },
            "optimization_strategies": strategies,
            "timeline": {
                "phase_1": "基础优化 (1-2周)",
                "phase_2": "高级功能 (3-4周)",
                "phase_3": "A/B测试优化 (5-6周)",
                "expected_completion": "6-8周内达到目标"
            },
            "success_probability": min(90, 60 + (10 - improvement_needed) * 3) if improvement_needed <= 10 else 40
        }
        
        return {
            "success": True,
            "data": simulation
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"模拟计算失败: {str(e)}"
        )