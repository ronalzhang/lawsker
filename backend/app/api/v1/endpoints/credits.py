"""
用户Credits支付控制API端点
实现Credits管理、购买、使用记录等功能
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user
from app.services.user_credits_service import UserCreditsService, InsufficientCreditsError, create_user_credits_service
from app.services.config_service import SystemConfigService
from app.services.payment_service import create_wechat_pay_service
import logging
from uuid import UUID

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# 请求模型
class PurchaseCreditsRequest(BaseModel):
    credits_count: int
    
class BatchUploadRequest(BaseModel):
    file_count: int = 1
    estimated_records: Optional[int] = None


def get_credits_service() -> UserCreditsService:
    """获取Credits服务实例"""
    config_service = SystemConfigService()
    payment_service = create_wechat_pay_service(config_service)
    return create_user_credits_service(config_service, payment_service)


@router.get("/balance", response_model=Dict[str, Any])
async def get_credits_balance(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户Credits余额和详细信息 - 增强版，提供更清晰的显示
    """
    try:
        credits_service = get_credits_service()
        user_id = UUID(current_user["id"])
        
        credits_info = await credits_service.get_user_credits(user_id, db)
        
        # 增强信息，提供更好的用户理解
        enhanced_info = {
            **credits_info,
            "display_info": {
                "balance_status": _get_balance_status(credits_info['credits_remaining']),
                "reset_countdown": _get_reset_countdown(credits_info['next_reset_date']),
                "usage_summary": _get_usage_summary(credits_info),
                "recommendations": _get_user_recommendations(credits_info),
                "explanation": {
                    "what_are_credits": "Credits是平台资源使用额度，用于批量任务上传等功能",
                    "how_to_get": "每周一免费获得1个Credit，也可以购买更多（50元/个）",
                    "how_to_use": "批量上传消耗1个Credit，无论上传多少文件",
                    "expiry": "购买的Credits永不过期，免费Credits每周重置"
                }
            }
        }
        
        return {
            "success": True,
            "data": enhanced_info,
            "message": "获取Credits余额成功",
            "user_friendly_message": _get_user_friendly_message(credits_info)
        }
        
    except Exception as e:
        logger.error(f"获取Credits余额失败: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "获取余额失败",
                "technical_detail": str(e),
                "user_message": "无法获取Credits信息，请稍后重试或联系客服",
                "suggestions": [
                    "检查网络连接",
                    "刷新页面重试",
                    "如问题持续，请联系技术支持"
                ]
            }
        )


@router.post("/initialize", response_model=Dict[str, Any])
async def initialize_credits(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    初始化用户Credits（新用户注册时调用）
    """
    try:
        credits_service = get_credits_service()
        user_id = UUID(current_user["id"])
        
        result = await credits_service.initialize_user_credits(user_id, db)
        
        return {
            "success": True,
            "data": result,
            "message": "Credits初始化成功"
        }
        
    except Exception as e:
        logger.error(f"初始化Credits失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"初始化失败: {str(e)}")


@router.post("/consume/batch-upload", response_model=Dict[str, Any])
async def consume_credits_for_batch_upload(
    request: BatchUploadRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量上传消耗Credits检查和扣除 - 增强版，提供清晰的反馈和指导
    """
    try:
        credits_service = get_credits_service()
        user_id = UUID(current_user["id"])
        
        # 先检查余额
        credits_info = await credits_service.get_user_credits(user_id, db)
        
        # 提供详细的上传信息
        upload_info = {
            "estimated_files": request.file_count,
            "estimated_records": request.estimated_records or "未知",
            "credits_required": 1,
            "credits_available": credits_info['credits_remaining']
        }
        
        # 消耗Credits
        result = await credits_service.consume_credits_for_batch_upload(user_id, db)
        
        return {
            "success": True,
            "data": {
                **result,
                "upload_info": upload_info,
                "transaction_details": {
                    "credits_before": credits_info['credits_remaining'],
                    "credits_consumed": result['credits_consumed'],
                    "credits_after": result['credits_remaining'],
                    "transaction_time": datetime.now().isoformat()
                }
            },
            "message": "Credits消耗成功，可以开始批量上传",
            "user_message": f"已消耗1个Credit，剩余{result['credits_remaining']}个，您可以继续上传文件",
            "next_steps": [
                "选择要上传的文件",
                "确认文件格式正确",
                "开始批量上传",
                "等待处理完成"
            ]
        }
        
    except InsufficientCreditsError as e:
        # 获取详细的不足信息
        credits_info = await credits_service.get_user_credits(user_id, db)
        reset_info = _get_reset_countdown(credits_info['next_reset_date'])
        
        return {
            "success": False,
            "error": "insufficient_credits",
            "message": "Credits余额不足",
            "user_message": f"您的Credits余额不足。当前余额：{e.current_credits}个，需要：{e.required_credits}个",
            "data": {
                "current_credits": e.current_credits,
                "required_credits": e.required_credits,
                "shortage": e.required_credits - e.current_credits,
                "reset_info": reset_info,
                "upload_blocked": True
            },
            "solutions": [
                {
                    "type": "immediate",
                    "title": "立即购买Credits",
                    "description": "购买Credits立即到账，可马上使用",
                    "action": "purchase",
                    "url": "/api/v1/credits/purchase",
                    "recommended": True
                },
                {
                    "type": "wait",
                    "title": "等待免费重置",
                    "description": f"还有{reset_info['days']}天，免费Credit将重置为1个",
                    "action": "wait",
                    "recommended": reset_info['days'] <= 2
                },
                {
                    "type": "alternative",
                    "title": "使用单一任务上传",
                    "description": "单一任务上传不消耗Credits，但需要逐个处理",
                    "action": "single_upload",
                    "recommended": False
                }
            ],
            "pricing_info": {
                "unit_price": 50,
                "currency": "CNY",
                "bulk_discounts": [
                    {"quantity": 5, "discount": "10%", "price": 225},
                    {"quantity": 10, "discount": "20%", "price": 400}
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"消耗Credits失败: {str(e)}")
        return {
            "success": False,
            "error": "system_error",
            "message": "系统错误",
            "user_message": "处理您的请求时出现问题，请稍后重试",
            "technical_detail": str(e),
            "suggestions": [
                "请刷新页面重试",
                "检查网络连接",
                "如问题持续，请联系技术支持"
            ],
            "fallback_options": [
                "使用单一任务上传功能",
                "稍后重试批量上传",
                "联系客服获得帮助"
            ]
        }


@router.get("/check/batch-upload", response_model=Dict[str, Any])
async def check_credits_for_batch_upload(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    检查用户是否有足够Credits进行批量上传（不实际消耗）
    """
    try:
        credits_service = get_credits_service()
        user_id = UUID(current_user["id"])
        
        credits_info = await credits_service.get_user_credits(user_id, db)
        
        has_sufficient = credits_info['credits_remaining'] >= 1
        
        return {
            "success": True,
            "data": {
                "has_sufficient_credits": has_sufficient,
                "credits_remaining": credits_info['credits_remaining'],
                "required_credits": 1,
                "can_upload": has_sufficient
            },
            "message": "Credits检查完成"
        }
        
    except Exception as e:
        logger.error(f"检查Credits失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"检查Credits失败: {str(e)}")


@router.post("/purchase", response_model=Dict[str, Any])
async def purchase_credits(
    request: PurchaseCreditsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    购买Credits（50元/个）- 增强版，提供清晰的购买流程指导
    """
    try:
        credits_service = get_credits_service()
        user_id = UUID(current_user["id"])
        
        # 验证购买数量
        if request.credits_count <= 0 or request.credits_count > 100:
            return {
                "success": False,
                "error": "invalid_quantity",
                "message": "购买数量无效",
                "user_message": "购买数量必须在1-100之间",
                "data": {
                    "min_quantity": 1,
                    "max_quantity": 100,
                    "requested_quantity": request.credits_count
                },
                "suggestions": [
                    "请选择1-100之间的数量",
                    "推荐购买5个或10个享受折扣优惠"
                ]
            }
        
        # 计算价格和优惠信息
        pricing_info = _calculate_pricing_info(request.credits_count)
        
        result = await credits_service.purchase_credits(user_id, request.credits_count, db)
        
        # 增强返回信息
        enhanced_result = {
            **result,
            "pricing_info": pricing_info,
            "payment_steps": [
                {
                    "step": 1,
                    "title": "订单确认",
                    "description": f"购买{request.credits_count}个Credits，总计¥{pricing_info['total_price']}",
                    "status": "completed"
                },
                {
                    "step": 2,
                    "title": "选择支付方式",
                    "description": "支持微信支付，安全便捷",
                    "status": "current"
                },
                {
                    "step": 3,
                    "title": "完成支付",
                    "description": "扫码支付后Credits将立即到账",
                    "status": "pending"
                }
            ],
            "benefits": [
                "Credits立即到账，无需等待",
                "购买的Credits永不过期",
                "可用于所有批量上传功能",
                "享受平台安全支付保障"
            ]
        }
        
        return {
            "success": True,
            "data": enhanced_result,
            "message": "购买订单创建成功",
            "user_message": f"订单已创建！购买{request.credits_count}个Credits，总计¥{pricing_info['total_price']}，请完成支付",
            "next_steps": [
                "确认订单信息",
                "选择微信支付",
                "扫码完成支付",
                "Credits自动到账"
            ]
        }
        
    except Exception as e:
        logger.error(f"购买Credits失败: {str(e)}")
        return {
            "success": False,
            "error": "purchase_failed",
            "message": "购买失败",
            "user_message": "创建购买订单时出现问题，请稍后重试",
            "technical_detail": str(e),
            "suggestions": [
                "请检查网络连接",
                "稍后重试购买",
                "如问题持续，请联系客服",
                "您也可以等待每周免费Credits重置"
            ],
            "support_info": {
                "contact": "客服微信：lawsker-support",
                "hours": "工作时间：9:00-18:00",
                "response_time": "通常在1小时内回复"
            }
        }


@router.post("/purchase/confirm/{purchase_id}", response_model=Dict[str, Any])
async def confirm_credits_purchase(
    purchase_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    确认Credits购买（支付成功后的回调）
    """
    try:
        credits_service = get_credits_service()
        
        result = await credits_service.confirm_credits_purchase(purchase_id, db)
        
        return {
            "success": True,
            "data": result,
            "message": "Credits购买确认成功"
        }
        
    except Exception as e:
        logger.error(f"确认Credits购买失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"确认购买失败: {str(e)}")


@router.get("/usage-history", response_model=Dict[str, Any])
async def get_credits_usage_history(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="页大小"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取Credits使用历史记录
    """
    try:
        credits_service = get_credits_service()
        user_id = UUID(current_user["id"])
        
        result = await credits_service.get_credits_usage_history(user_id, page, size, db)
        
        return {
            "success": True,
            "data": result,
            "message": "获取使用历史成功"
        }
        
    except Exception as e:
        logger.error(f"获取Credits使用历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取使用历史失败: {str(e)}")


@router.get("/purchase-history", response_model=Dict[str, Any])
async def get_credits_purchase_history(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="页大小"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取Credits购买历史记录
    """
    try:
        credits_service = get_credits_service()
        user_id = UUID(current_user["id"])
        
        result = await credits_service.get_credits_purchase_history(user_id, page, size, db)
        
        return {
            "success": True,
            "data": result,
            "message": "获取购买历史成功"
        }
        
    except Exception as e:
        logger.error(f"获取Credits购买历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取购买历史失败: {str(e)}")


@router.get("/pricing", response_model=Dict[str, Any])
async def get_credits_pricing():
    """
    获取Credits价格信息
    """
    try:
        return {
            "success": True,
            "data": {
                "unit_price": 50.00,
                "currency": "CNY",
                "min_purchase": 1,
                "max_purchase": 100,
                "weekly_free_credits": 1,
                "batch_upload_cost": 1,
                "pricing_tiers": [
                    {"credits": 1, "price": 50.00, "discount": 0},
                    {"credits": 5, "price": 240.00, "discount": 0.04},
                    {"credits": 10, "price": 450.00, "discount": 0.10},
                    {"credits": 20, "price": 800.00, "discount": 0.20},
                    {"credits": 50, "price": 1875.00, "discount": 0.25}
                ]
            },
            "message": "获取价格信息成功"
        }
        
    except Exception as e:
        logger.error(f"获取Credits价格失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取价格信息失败: {str(e)}")


@router.post("/admin/reset-weekly", response_model=Dict[str, Any])
async def admin_reset_weekly_credits(
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    管理员手动触发每周Credits重置（定时任务）
    """
    try:
        # 检查管理员权限
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        credits_service = get_credits_service()
        
        # 在后台执行批量重置
        background_tasks.add_task(credits_service.weekly_credits_reset_batch, db)
        
        return {
            "success": True,
            "message": "每周Credits重置任务已启动"
        }
        
    except Exception as e:
        logger.error(f"管理员重置Credits失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重置失败: {str(e)}")


@router.get("/stats", response_model=Dict[str, Any])
async def get_credits_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户Credits统计信息
    """
    try:
        credits_service = get_credits_service()
        user_id = UUID(current_user["id"])
        
        # 获取基本信息
        credits_info = await credits_service.get_user_credits(user_id, db)
        
        # 计算统计数据
        stats = {
            "current_balance": credits_info['credits_remaining'],
            "total_purchased": credits_info['credits_purchased'],
            "total_used": credits_info['total_credits_used'],
            "weekly_allowance": credits_info['credits_weekly'],
            "last_reset_date": credits_info['last_reset_date'],
            "next_reset_date": credits_info['next_reset_date'],
            "usage_efficiency": {
                "total_available": credits_info['credits_purchased'] + credits_info['total_credits_used'],
                "usage_rate": credits_info['total_credits_used'] / max(1, credits_info['credits_purchased'] + credits_info['total_credits_used'])
            }
        }
        
        return {
            "success": True,
            "data": stats,
            "message": "获取Credits统计成功"
        }
        
    except Exception as e:
        logger.error(f"获取Credits统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")
# Helper functions for enhanced user experience

def _get_balance_status(credits_remaining: int) -> Dict[str, Any]:
    """获取余额状态信息"""
    if credits_remaining == 0:
        return {
            "level": "empty",
            "color": "red",
            "icon": "⚠️",
            "message": "余额已用完",
            "description": "您的Credits已用完，无法进行批量上传",
            "action_needed": True,
            "suggested_action": "购买Credits或等待每周重置"
        }
    elif credits_remaining == 1:
        return {
            "level": "low",
            "color": "orange", 
            "icon": "💡",
            "message": "余额较低",
            "description": "您只剩1个Credit，建议提前购买",
            "action_needed": False,
            "suggested_action": "考虑购买更多Credits"
        }
    elif credits_remaining >= 5:
        return {
            "level": "good",
            "color": "green",
            "icon": "✅",
            "message": "余额充足",
            "description": f"您有{credits_remaining}个Credits，可以安心使用",
            "action_needed": False,
            "suggested_action": None
        }
    else:
        return {
            "level": "normal",
            "color": "blue",
            "icon": "📊",
            "message": "余额正常",
            "description": f"您有{credits_remaining}个Credits可用",
            "action_needed": False,
            "suggested_action": None
        }

def _get_reset_countdown(next_reset_date: str) -> Dict[str, Any]:
    """获取重置倒计时信息"""
    from datetime import datetime, date
    
    next_reset = datetime.fromisoformat(next_reset_date).date()
    today = date.today()
    days_until = (next_reset - today).days
    
    if days_until <= 0:
        return {
            "days": 0,
            "message": "今天重置",
            "description": "免费Credit将在今天重置为1个",
            "urgency": "high"
        }
    elif days_until == 1:
        return {
            "days": 1,
            "message": "明天重置",
            "description": "免费Credit将在明天重置为1个",
            "urgency": "medium"
        }
    elif days_until <= 3:
        return {
            "days": days_until,
            "message": f"{days_until}天后重置",
            "description": f"还有{days_until}天，免费Credit将重置为1个",
            "urgency": "low"
        }
    else:
        return {
            "days": days_until,
            "message": f"{days_until}天后重置",
            "description": f"下次重置时间：{next_reset.strftime('%m月%d日')}",
            "urgency": "none"
        }

def _get_usage_summary(credits_info: Dict[str, Any]) -> Dict[str, Any]:
    """获取使用情况摘要"""
    total_used = credits_info.get('total_credits_used', 0)
    total_purchased = credits_info.get('credits_purchased', 0)
    total_available = total_used + total_purchased
    
    usage_rate = (total_used / max(1, total_available)) * 100 if total_available > 0 else 0
    
    return {
        "total_used": total_used,
        "total_purchased": total_purchased,
        "usage_rate": round(usage_rate, 1),
        "usage_level": "high" if usage_rate > 70 else "medium" if usage_rate > 30 else "low",
        "summary": _get_usage_summary_text(total_used, usage_rate)
    }

def _get_usage_summary_text(total_used: int, usage_rate: float) -> str:
    """获取使用情况文本摘要"""
    if total_used == 0:
        return "新用户，还未使用批量上传功能，每周免费1个Credit"
    elif total_used < 5:
        return f"已完成{total_used}次批量上传，平均每次可处理多个文件"
    elif total_used < 20:
        return f"活跃用户，已完成{total_used}次批量上传，节省大量时间"
    else:
        return f"重度用户，已完成{total_used}次批量上传，建议批量购买享受折扣"

def _get_user_recommendations(credits_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """获取个性化推荐 - 增强版，提供更精准的推荐"""
    recommendations = []
    
    credits_remaining = credits_info.get('credits_remaining', 0)
    total_used = credits_info.get('total_credits_used', 0)
    total_purchased = credits_info.get('credits_purchased', 0)
    
    # 精准匹配不同用户场景
    
    # 场景1: 余额为0的紧急情况
    if credits_remaining == 0:
        recommendations.append({
            "type": "urgent",
            "title": "立即购买Credits",
            "description": "余额为0无法批量上传，建议立即购买或等待重置",
            "action": "purchase",
            "priority": 1,
            "icon": "⚠️",
            "button_text": "立即购买"
        })
    
    # 场景2: 余额为1的预警情况
    elif credits_remaining == 1:
        recommendations.append({
            "type": "suggestion", 
            "title": "余额预警",
            "description": "仅剩1个Credit，建议提前购买避免中断工作",
            "action": "purchase",
            "priority": 2,
            "icon": "💡",
            "button_text": "购买更多"
        })
    
    # 场景3: 新用户引导（精确匹配）
    if total_used == 0 and total_purchased == 0 and credits_remaining > 0:
        recommendations.append({
            "type": "guide",
            "title": "新用户体验指南",
            "description": "您有免费Credit，点击体验批量上传功能",
            "action": "try_upload",
            "priority": 1,
            "icon": "🎯",
            "button_text": "立即体验"
        })
    
    # 场景4: 重度用户优惠（精确匹配）
    elif total_used >= 15:
        recommendations.append({
            "type": "offer",
            "title": "VIP用户专享",
            "description": f"已使用{total_used}次，购买20个享受30%折扣",
            "action": "vip_purchase",
            "priority": 1,
            "icon": "👑",
            "button_text": "VIP优惠"
        })
    
    # 场景5: 活跃用户推荐（精确匹配）
    elif total_used >= 10:
        recommendations.append({
            "type": "offer", 
            "title": "活跃用户优惠",
            "description": f"已使用{total_used}次，购买10个享受20%折扣",
            "action": "active_purchase",
            "priority": 2,
            "icon": "🔥",
            "button_text": "享受优惠"
        })
    
    # 场景6: 中等使用量用户（精确匹配）
    elif 3 <= total_used < 10:
        recommendations.append({
            "type": "suggestion",
            "title": "经济实惠套餐",
            "description": f"已使用{total_used}次，购买5个享受10%折扣",
            "action": "economy_purchase",
            "priority": 3,
            "icon": "💰",
            "button_text": "经济套餐"
        })
    
    # 场景7: 轻度用户鼓励（精确匹配）
    elif 1 <= total_used < 3:
        recommendations.append({
            "type": "encouragement",
            "title": "继续使用批量上传",
            "description": "批量上传可大幅提升效率，建议多多使用",
            "action": "encourage_use",
            "priority": 4,
            "icon": "📈",
            "button_text": "了解更多"
        })
    
    # 场景8: 余额充足的用户
    if credits_remaining >= 5:
        recommendations.append({
            "type": "info",
            "title": "余额充足",
            "description": f"您有{credits_remaining}个Credits，可安心使用批量上传",
            "action": "use_credits",
            "priority": 5,
            "icon": "✅",
            "button_text": "开始上传"
        })
    
    # 场景9: 购买过但用完的用户
    if total_purchased > 0 and credits_remaining == 0:
        recommendations.append({
            "type": "repurchase",
            "title": "续费提醒",
            "description": f"之前购买过{total_purchased}个Credits，建议续费继续使用",
            "action": "repurchase",
            "priority": 1,
            "icon": "🔄",
            "button_text": "续费购买"
        })
    
    # 按优先级排序并限制数量
    sorted_recommendations = sorted(recommendations, key=lambda x: x['priority'])
    return sorted_recommendations[:3]  # 最多返回3个推荐

def _get_user_friendly_message(credits_info: Dict[str, Any]) -> str:
    """获取用户友好的消息"""
    credits_remaining = credits_info.get('credits_remaining', 0)
    
    if credits_remaining == 0:
        return "您的Credits已用完，请购买或等待每周重置"
    elif credits_remaining == 1:
        return "您还有1个Credit可用，建议提前购买更多"
    elif credits_remaining >= 5:
        return f"您有{credits_remaining}个Credits，余额充足"
    else:
        return f"您有{credits_remaining}个Credits可用"

def _calculate_pricing_info(credits_count: int) -> Dict[str, Any]:
    """计算价格信息和优惠详情"""
    base_price = 50.0  # 基础价格50元/个
    total_base_price = credits_count * base_price
    
    # 计算折扣
    discount_rate = 0
    if credits_count >= 20:
        discount_rate = 0.30  # 30% 折扣
    elif credits_count >= 10:
        discount_rate = 0.20  # 20% 折扣
    elif credits_count >= 5:
        discount_rate = 0.10  # 10% 折扣
    
    discount_amount = total_base_price * discount_rate
    final_price = total_base_price - discount_amount
    unit_price = final_price / credits_count
    
    return {
        "credits_count": credits_count,
        "base_unit_price": base_price,
        "total_base_price": total_base_price,
        "discount_rate": discount_rate,
        "discount_amount": discount_amount,
        "final_unit_price": unit_price,
        "total_price": final_price,
        "savings": discount_amount,
        "discount_description": _get_discount_description(credits_count, discount_rate),
        "value_proposition": _get_value_proposition(credits_count, discount_amount)
    }

def _get_discount_description(credits_count: int, discount_rate: float) -> str:
    """获取折扣描述"""
    if discount_rate == 0:
        return "标准价格"
    else:
        percentage = int(discount_rate * 100)
        return f"批量购买{credits_count}个，享受{percentage}%折扣优惠"

def _get_value_proposition(credits_count: int, savings: float) -> str:
    """获取价值主张"""
    if savings == 0:
        return f"购买{credits_count}个Credits，标准价格"
    else:
        return f"批量购买节省¥{savings:.0f}，相当于免费获得{savings/50:.1f}个Credits"