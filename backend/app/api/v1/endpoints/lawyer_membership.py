"""
律师会员系统API端点
实现免费引流模式和付费会员管理
"""

import logging
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.lawyer_membership_service import LawyerMembershipService, create_lawyer_membership_service
from app.services.lawyer_points_engine import LawyerPointsEngine, create_lawyer_points_engine
from app.services.payment_service import WeChatPayService, create_wechat_pay_service
from app.services.config_service import SystemConfigService
from app.services.notification_channels import EmailNotifier

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic模型
class MembershipUpgradeRequest(BaseModel):
    target_tier: str = Field(..., description="目标会员类型", regex="^(professional|enterprise)$")


class PointsActionRequest(BaseModel):
    action: str = Field(..., description="积分行为类型")
    context: Dict[str, Any] = Field(default_factory=dict, description="行为上下文")


class MembershipResponse(BaseModel):
    membership_type: str
    tier_info: Dict[str, Any]
    start_date: str
    end_date: str
    ai_credits_remaining: int
    daily_case_limit: int
    point_multiplier: float


class PointsSummaryResponse(BaseModel):
    current_level: int
    level_name: str
    current_points: int
    next_level: Optional[int]
    next_level_name: Optional[str]
    points_needed: int
    cases_needed: int
    progress_percentage: float
    membership_type: str
    point_multiplier: float
    statistics: Dict[str, Any]
    recent_transactions: List[Dict[str, Any]]


# 依赖注入
def get_membership_service(db: Session = Depends(get_db)) -> LawyerMembershipService:
    config_service = SystemConfigService()
    payment_service = create_wechat_pay_service(config_service)
    return create_lawyer_membership_service(config_service, payment_service)


def get_points_engine(
    membership_service: LawyerMembershipService = Depends(get_membership_service)
) -> LawyerPointsEngine:
    return create_lawyer_points_engine(membership_service, None)


@router.get("/membership", response_model=MembershipResponse)
async def get_lawyer_membership(
    current_user: User = Depends(get_current_user),
    membership_service: LawyerMembershipService = Depends(get_membership_service),
    db: Session = Depends(get_db)
):
    """获取律师会员信息"""
    try:
        # 检查用户是否为律师
        if not await _is_lawyer(current_user.id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有律师用户可以访问会员信息"
            )
        
        membership = await membership_service.get_lawyer_membership(current_user.id, db)
        return MembershipResponse(**membership)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取律师会员信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会员信息失败"
        )


@router.get("/membership/tiers")
async def get_membership_tiers(
    membership_service: LawyerMembershipService = Depends(get_membership_service)
):
    """获取所有会员套餐信息"""
    try:
        tiers = await membership_service.get_membership_tiers()
        return tiers
        
    except Exception as e:
        logger.error(f"获取会员套餐信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取套餐信息失败"
        )


@router.post("/membership/upgrade")
async def upgrade_membership(
    request: MembershipUpgradeRequest,
    current_user: User = Depends(get_current_user),
    membership_service: LawyerMembershipService = Depends(get_membership_service),
    db: Session = Depends(get_db)
):
    """升级会员"""
    try:
        # 检查用户是否为律师
        if not await _is_lawyer(current_user.id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有律师用户可以升级会员"
            )
        
        upgrade_result = await membership_service.upgrade_membership(
            current_user.id, request.target_tier, db
        )
        
        return {
            "success": True,
            "message": f"会员升级请求已创建",
            "data": upgrade_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"会员升级失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="会员升级失败"
        )


@router.post("/membership/payment/success")
async def process_membership_payment_success(
    membership_type: str,
    payment_amount: float,
    current_user: User = Depends(get_current_user),
    membership_service: LawyerMembershipService = Depends(get_membership_service),
    db: Session = Depends(get_db)
):
    """处理会员支付成功回调"""
    try:
        # 检查用户是否为律师
        if not await _is_lawyer(current_user.id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有律师用户可以处理支付"
            )
        
        result = await membership_service.process_membership_payment_success(
            current_user.id, membership_type, payment_amount, db
        )
        
        return {
            "success": True,
            "message": "会员升级成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理会员支付成功失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="处理支付成功失败"
        )


@router.get("/points/summary", response_model=PointsSummaryResponse)
async def get_points_summary(
    current_user: User = Depends(get_current_user),
    points_engine: LawyerPointsEngine = Depends(get_points_engine),
    db: Session = Depends(get_db)
):
    """获取律师积分汇总"""
    try:
        # 检查用户是否为律师
        if not await _is_lawyer(current_user.id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有律师用户可以查看积分信息"
            )
        
        summary = await points_engine.get_lawyer_points_summary(current_user.id, db)
        return PointsSummaryResponse(**summary)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取积分汇总失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取积分汇总失败"
        )


@router.post("/points/action")
async def record_points_action(
    request: PointsActionRequest,
    current_user: User = Depends(get_current_user),
    points_engine: LawyerPointsEngine = Depends(get_points_engine),
    db: Session = Depends(get_db)
):
    """记录积分行为"""
    try:
        # 检查用户是否为律师
        if not await _is_lawyer(current_user.id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有律师用户可以记录积分行为"
            )
        
        result = await points_engine.calculate_points_with_multiplier(
            current_user.id, request.action, request.context, db
        )
        
        return {
            "success": True,
            "message": "积分记录成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"记录积分行为失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="记录积分行为失败"
        )


@router.get("/points/leaderboard")
async def get_points_leaderboard(
    limit: int = Query(50, ge=1, le=100, description="排行榜数量限制"),
    points_engine: LawyerPointsEngine = Depends(get_points_engine),
    db: Session = Depends(get_db)
):
    """获取积分排行榜"""
    try:
        leaderboard = await points_engine.get_points_leaderboard(db, limit)
        
        return {
            "success": True,
            "data": {
                "leaderboard": leaderboard,
                "total_count": len(leaderboard),
                "updated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"获取积分排行榜失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取排行榜失败"
        )


@router.get("/points/transactions")
async def get_points_transactions(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取律师积分变动记录"""
    try:
        # 检查用户是否为律师
        if not await _is_lawyer(current_user.id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有律师用户可以查看积分记录"
            )
        
        offset = (page - 1) * size
        
        # 查询积分变动记录
        transactions = db.execute("""
            SELECT 
                transaction_type,
                points_change,
                points_before,
                points_after,
                description,
                metadata,
                created_at
            FROM lawyer_point_transactions 
            WHERE lawyer_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s OFFSET %s
        """, (str(current_user.id), size, offset)).fetchall()
        
        # 查询总数
        total = db.execute("""
            SELECT COUNT(*) as count
            FROM lawyer_point_transactions 
            WHERE lawyer_id = %s
        """, (str(current_user.id),)).fetchone()['count']
        
        return {
            "success": True,
            "data": {
                "transactions": [
                    {
                        "type": t['transaction_type'],
                        "points_change": t['points_change'],
                        "points_before": t['points_before'],
                        "points_after": t['points_after'],
                        "description": t['description'],
                        "metadata": t['metadata'],
                        "created_at": t['created_at'].isoformat() if t['created_at'] else None
                    }
                    for t in transactions
                ],
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": total,
                    "pages": (total + size - 1) // size
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取积分变动记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取积分记录失败"
        )


@router.get("/statistics")
async def get_membership_statistics(
    membership_service: LawyerMembershipService = Depends(get_membership_service),
    db: Session = Depends(get_db)
):
    """获取会员统计数据（管理员接口）"""
    try:
        # 这里应该添加管理员权限检查
        # if not await _is_admin(current_user.id, db):
        #     raise HTTPException(status_code=403, detail="需要管理员权限")
        
        stats = await membership_service.get_membership_statistics(db)
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"获取会员统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计数据失败"
        )


@router.post("/admin/assign-free-membership")
async def admin_assign_free_membership(
    lawyer_id: UUID,
    membership_service: LawyerMembershipService = Depends(get_membership_service),
    db: Session = Depends(get_db)
):
    """管理员为律师分配免费会员"""
    try:
        # 这里应该添加管理员权限检查
        # if not await _is_admin(current_user.id, db):
        #     raise HTTPException(status_code=403, detail="需要管理员权限")
        
        result = await membership_service.assign_free_membership(lawyer_id, db)
        
        return {
            "success": True,
            "message": "免费会员分配成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分配免费会员失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分配免费会员失败"
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


async def _is_admin(user_id: UUID, db: Session) -> bool:
    """检查用户是否为管理员"""
    try:
        result = db.execute("""
            SELECT 1 FROM user_roles ur 
            JOIN roles r ON ur.role_id = r.id 
            WHERE ur.user_id = %s AND r.name = 'Admin'
        """, (str(user_id),)).fetchone()
        
        return result is not None
        
    except Exception as e:
        logger.error(f"检查管理员身份失败: {str(e)}")
        return False