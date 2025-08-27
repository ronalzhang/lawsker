"""
律师会员转化优化API端点
专门用于实现20%付费会员转化率目标
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.lawyer_membership_conversion_service import (
    LawyerMembershipConversionService, 
    create_lawyer_membership_conversion_service
)
from app.services.lawyer_membership_service import LawyerMembershipService, create_lawyer_membership_service
from app.services.lawyer_points_engine import LawyerPointsEngine, create_lawyer_points_engine
from app.services.payment_service import WeChatPayService, create_wechat_pay_service
from app.services.config_service import SystemConfigService

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic模型
class ConversionEventRequest(BaseModel):
    event_type: str = Field(..., description="转化事件类型")
    context: Dict[str, Any] = Field(default_factory=dict, description="事件上下文")


class ConversionMetricsResponse(BaseModel):
    period: str
    total_lawyers: int
    paid_lawyers: int
    free_lawyers: int
    conversion_rate: float
    target_achievement: Dict[str, Any]
    trend_data: List[Dict[str, Any]]
    funnel_data: Dict[str, Any]


class UpgradeRecommendationResponse(BaseModel):
    recommendation_type: str
    priority: str
    recommended_tier: str
    title: str
    message: str
    benefits: List[str]
    discount_info: Dict[str, Any]


class ConversionSimulationRequest(BaseModel):
    improvement_strategies: List[str] = Field(..., description="改进策略列表")


# 依赖注入
def get_conversion_service(db: Session = Depends(get_db)) -> LawyerMembershipConversionService:
    config_service = SystemConfigService()
    payment_service = create_wechat_pay_service(config_service)
    membership_service = create_lawyer_membership_service(config_service, payment_service)
    points_engine = create_lawyer_points_engine(membership_service, None)
    return create_lawyer_membership_conversion_service(membership_service, points_engine)


@router.post("/track-event")
async def track_conversion_event(
    request: ConversionEventRequest,
    current_user: User = Depends(get_current_user),
    conversion_service: LawyerMembershipConversionService = Depends(get_conversion_service),
    db: Session = Depends(get_db)
):
    """跟踪律师会员转化事件"""
    try:
        # 检查用户是否为律师
        if not await _is_lawyer(current_user.id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有律师用户可以跟踪转化事件"
            )
        
        result = await conversion_service.track_conversion_event(
            current_user.id, request.event_type, request.context, db
        )
        
        return {
            "success": True,
            "message": "转化事件跟踪成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"跟踪转化事件失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="跟踪转化事件失败"
        )


@router.get("/metrics", response_model=ConversionMetricsResponse)
async def get_conversion_metrics(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    conversion_service: LawyerMembershipConversionService = Depends(get_conversion_service),
    db: Session = Depends(get_db)
):
    """获取律师会员转化率指标"""
    try:
        metrics = await conversion_service.get_conversion_metrics(db, days)
        return ConversionMetricsResponse(**metrics)
        
    except Exception as e:
        logger.error(f"获取转化率指标失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取转化率指标失败"
        )


@router.get("/recommendation", response_model=UpgradeRecommendationResponse)
async def get_upgrade_recommendation(
    current_user: User = Depends(get_current_user),
    conversion_service: LawyerMembershipConversionService = Depends(get_conversion_service),
    db: Session = Depends(get_db)
):
    """获取个性化升级推荐"""
    try:
        # 检查用户是否为律师
        if not await _is_lawyer(current_user.id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有律师用户可以获取升级推荐"
            )
        
        recommendation = await conversion_service.get_personalized_upgrade_recommendation(
            current_user.id, db
        )
        
        return UpgradeRecommendationResponse(**recommendation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取升级推荐失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取升级推荐失败"
        )


@router.get("/dashboard")
async def get_conversion_dashboard(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    conversion_service: LawyerMembershipConversionService = Depends(get_conversion_service),
    db: Session = Depends(get_db)
):
    """获取转化率仪表盘数据"""
    try:
        # 获取核心指标
        metrics = await conversion_service.get_conversion_metrics(db, days)
        
        # 获取优化建议
        suggestions = await conversion_service.get_conversion_optimization_suggestions(db)
        
        # 计算关键KPI
        current_rate = metrics['conversion_rate']
        target_rate = 20.0
        gap_to_target = max(0, target_rate - current_rate)
        
        # 状态评估
        if current_rate >= target_rate:
            status = "target_achieved"
            status_message = "🎉 恭喜！已达成20%转化率目标"
            status_color = "success"
        elif current_rate >= 15:
            status = "on_track"
            status_message = f"📈 进展良好，距离目标还差{gap_to_target:.1f}%"
            status_color = "warning"
        elif current_rate >= 10:
            status = "needs_attention"
            status_message = f"⚠️ 需要关注，距离目标还差{gap_to_target:.1f}%"
            status_color = "warning"
        else:
            status = "critical"
            status_message = f"🚨 紧急处理，距离目标还差{gap_to_target:.1f}%"
            status_color = "danger"
        
        return {
            "success": True,
            "data": {
                "overview": {
                    "current_conversion_rate": current_rate,
                    "target_conversion_rate": target_rate,
                    "gap_to_target": gap_to_target,
                    "achievement_percentage": min(100, round(current_rate / target_rate * 100, 2)),
                    "status": status,
                    "status_message": status_message,
                    "status_color": status_color
                },
                "metrics": metrics,
                "optimization_suggestions": suggestions[:5],  # 前5个建议
                "quick_actions": [
                    {
                        "title": "发送升级邮件",
                        "description": "向活跃的免费律师发送个性化升级邮件",
                        "action": "send_upgrade_emails",
                        "estimated_impact": "+1-2%"
                    },
                    {
                        "title": "推出限时优惠",
                        "description": "为专业版推出15%首月优惠",
                        "action": "create_discount_campaign",
                        "estimated_impact": "+2-3%"
                    },
                    {
                        "title": "优化升级页面",
                        "description": "改进会员升级页面的用户体验",
                        "action": "optimize_upgrade_page",
                        "estimated_impact": "+1-2%"
                    }
                ],
                "updated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"获取转化率仪表盘失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取仪表盘数据失败"
        )


@router.post("/simulate-improvement")
async def simulate_conversion_improvement(
    request: ConversionSimulationRequest,
    conversion_service: LawyerMembershipConversionService = Depends(get_conversion_service),
    db: Session = Depends(get_db)
):
    """模拟转化率改进效果"""
    try:
        simulation = await conversion_service.simulate_conversion_improvement(
            db, request.improvement_strategies
        )
        
        return {
            "success": True,
            "message": "转化率改进模拟完成",
            "data": simulation
        }
        
    except Exception as e:
        logger.error(f"模拟转化率改进失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="模拟转化率改进失败"
        )


@router.get("/suggestions")
async def get_optimization_suggestions(
    conversion_service: LawyerMembershipConversionService = Depends(get_conversion_service),
    db: Session = Depends(get_db)
):
    """获取转化率优化建议"""
    try:
        suggestions = await conversion_service.get_conversion_optimization_suggestions(db)
        
        return {
            "success": True,
            "data": {
                "suggestions": suggestions,
                "total_count": len(suggestions),
                "categories": list(set(s['category'] for s in suggestions)),
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"获取优化建议失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取优化建议失败"
        )


@router.get("/funnel-analysis")
async def get_conversion_funnel_analysis(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    conversion_service: LawyerMembershipConversionService = Depends(get_conversion_service),
    db: Session = Depends(get_db)
):
    """获取转化漏斗分析"""
    try:
        metrics = await conversion_service.get_conversion_metrics(db, days)
        funnel_data = metrics.get('funnel_data', {})
        
        # 计算漏斗步骤
        steps = [
            {
                "step": 1,
                "name": "免费律师",
                "description": "注册的免费律师用户",
                "count": funnel_data.get('total_free_lawyers', 0),
                "conversion_rate": 100.0
            },
            {
                "step": 2,
                "name": "查看会员页面",
                "description": "访问会员升级页面",
                "count": funnel_data.get('viewed_membership_page', 0),
                "conversion_rate": funnel_data.get('conversion_rates', {}).get('view_rate', 0)
            },
            {
                "step": 3,
                "name": "点击升级按钮",
                "description": "点击会员升级按钮",
                "count": funnel_data.get('clicked_upgrade_button', 0),
                "conversion_rate": funnel_data.get('conversion_rates', {}).get('click_rate', 0)
            },
            {
                "step": 4,
                "name": "发起支付",
                "description": "开始支付流程",
                "count": funnel_data.get('initiated_payment', 0),
                "conversion_rate": funnel_data.get('conversion_rates', {}).get('initiation_rate', 0)
            },
            {
                "step": 5,
                "name": "完成支付",
                "description": "成功完成支付升级",
                "count": funnel_data.get('completed_payment', 0),
                "conversion_rate": funnel_data.get('conversion_rates', {}).get('completion_rate', 0)
            }
        ]
        
        # 识别瓶颈步骤
        bottleneck_step = None
        min_conversion_rate = 100
        for i, step in enumerate(steps[1:], 1):  # 跳过第一步
            if step['conversion_rate'] < min_conversion_rate:
                min_conversion_rate = step['conversion_rate']
                bottleneck_step = step
        
        return {
            "success": True,
            "data": {
                "funnel_steps": steps,
                "overall_conversion_rate": funnel_data.get('conversion_rates', {}).get('overall_rate', 0),
                "bottleneck_step": bottleneck_step,
                "improvement_opportunities": [
                    {
                        "step": bottleneck_step['name'] if bottleneck_step else "无",
                        "current_rate": bottleneck_step['conversion_rate'] if bottleneck_step else 0,
                        "improvement_potential": "提升该步骤转化率可显著改善整体效果",
                        "suggested_actions": [
                            "优化页面设计和用户体验",
                            "添加更有说服力的价值主张",
                            "简化操作流程",
                            "增加社会证明元素"
                        ]
                    }
                ] if bottleneck_step else [],
                "period": f"{days}天",
                "updated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"获取转化漏斗分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取转化漏斗分析失败"
        )


@router.get("/ab-test-config")
async def get_ab_test_config():
    """获取A/B测试配置"""
    try:
        # 返回A/B测试配置
        ab_tests = [
            {
                "test_id": "upgrade_page_v1",
                "name": "会员升级页面优化",
                "description": "测试不同的页面设计对转化率的影响",
                "status": "active",
                "variants": [
                    {
                        "variant_id": "control",
                        "name": "原版页面",
                        "traffic_percentage": 50,
                        "description": "当前的会员升级页面设计"
                    },
                    {
                        "variant_id": "variant_a",
                        "name": "优化版页面",
                        "traffic_percentage": 50,
                        "description": "突出价值主张和优惠信息的新设计"
                    }
                ],
                "metrics": [
                    "conversion_rate",
                    "click_through_rate",
                    "time_on_page"
                ],
                "start_date": "2025-01-01",
                "end_date": "2025-01-31"
            },
            {
                "test_id": "pricing_strategy_v1",
                "name": "定价策略测试",
                "description": "测试不同的定价和优惠策略",
                "status": "planned",
                "variants": [
                    {
                        "variant_id": "control",
                        "name": "标准定价",
                        "traffic_percentage": 33,
                        "description": "专业版899元，企业版2999元"
                    },
                    {
                        "variant_id": "variant_a",
                        "name": "首月优惠",
                        "traffic_percentage": 33,
                        "description": "首月15%折扣"
                    },
                    {
                        "variant_id": "variant_b",
                        "name": "年付优惠",
                        "traffic_percentage": 34,
                        "description": "年付享受2个月免费"
                    }
                ],
                "metrics": [
                    "conversion_rate",
                    "revenue_per_user",
                    "customer_lifetime_value"
                ],
                "start_date": "2025-02-01",
                "end_date": "2025-02-28"
            }
        ]
        
        return {
            "success": True,
            "data": {
                "ab_tests": ab_tests,
                "total_tests": len(ab_tests),
                "active_tests": len([t for t in ab_tests if t['status'] == 'active']),
                "planned_tests": len([t for t in ab_tests if t['status'] == 'planned'])
            }
        }
        
    except Exception as e:
        logger.error(f"获取A/B测试配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取A/B测试配置失败"
        )


# 辅助函数
async def _is_lawyer(user_id: UUID, db: Session) -> bool:
    """检查用户是否为律师"""
    try:
        result = db.execute("""
            SELECT 1 FROM user_roles ur 
            JOIN roles r ON ur.role_id = r.id 
            WHERE ur.user_id = %s AND r.name = 'Lawyer'
        """, (str(user_id),)).fetchone()
        
        return result is not None
        
    except Exception as e:
        logger.error(f"检查律师身份失败: {str(e)}")
        return False