"""
律师推广API端点
用于实现300%律师注册率提升目标的推广功能
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import logging

from app.core.database import get_db
from app.core.deps import get_current_admin_user
from app.services.lawyer_promotion_service import LawyerPromotionService
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)
router = APIRouter()


class PromotionCampaignRequest(BaseModel):
    """推广活动请求模型"""
    campaign_name: str
    target_emails: Optional[List[EmailStr]] = None
    use_potential_lawyers: bool = True


class ReferralProgramRequest(BaseModel):
    """推荐计划请求模型"""
    referrer_lawyer_id: str
    bonus_points: int = 500


class ConversionTrackingRequest(BaseModel):
    """转化跟踪请求模型"""
    source: str
    campaign: Optional[str] = None
    referral_code: Optional[str] = None


@router.post("/campaigns/send-promotion-emails")
async def send_promotion_emails(
    request: PromotionCampaignRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """
    发送律师推广邮件活动
    
    需要管理员权限
    """
    try:
        email_service = EmailService()
        promotion_service = LawyerPromotionService(email_service)
        
        # 获取目标邮箱列表
        if request.use_potential_lawyers:
            target_emails = await promotion_service.get_potential_lawyer_emails(db)
        else:
            target_emails = request.target_emails or []
        
        if not target_emails:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有找到目标邮箱"
            )
        
        # 后台发送邮件
        background_tasks.add_task(
            promotion_service.send_lawyer_promotion_campaign,
            target_emails,
            request.campaign_name
        )
        
        return {
            "message": "推广邮件发送任务已启动",
            "campaign_name": request.campaign_name,
            "target_count": len(target_emails)
        }
        
    except Exception as e:
        logger.error(f"发送推广邮件失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送推广邮件失败: {str(e)}"
        )


@router.get("/statistics")
async def get_promotion_statistics(
    days: int = 30,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """
    获取律师推广统计数据
    
    需要管理员权限
    """
    try:
        email_service = EmailService()
        promotion_service = LawyerPromotionService(email_service)
        
        stats = await promotion_service.get_promotion_statistics(days)
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"获取推广统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取推广统计失败: {str(e)}"
        )


@router.post("/referral-program")
async def create_referral_program(
    request: ReferralProgramRequest,
    db: Session = Depends(get_db)
):
    """
    创建律师推荐计划
    
    律师可以创建推荐链接，推荐其他律师注册
    """
    try:
        email_service = EmailService()
        promotion_service = LawyerPromotionService(email_service)
        
        result = await promotion_service.create_lawyer_referral_program(
            request.referrer_lawyer_id,
            request.bonus_points
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"创建推荐计划失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建推荐计划失败: {str(e)}"
        )


@router.post("/track-conversion")
async def track_conversion(
    request: ConversionTrackingRequest
):
    """
    跟踪注册转化
    
    用于跟踪不同渠道的注册转化率
    """
    try:
        email_service = EmailService()
        promotion_service = LawyerPromotionService(email_service)
        
        result = await promotion_service.track_registration_conversion(
            request.source,
            request.campaign,
            request.referral_code
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"跟踪转化失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"跟踪转化失败: {str(e)}"
        )


@router.get("/optimization-recommendations")
async def get_optimization_recommendations(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """
    获取注册漏斗优化建议
    
    基于数据分析提供优化建议，帮助实现300%增长目标
    """
    try:
        email_service = EmailService()
        promotion_service = LawyerPromotionService(email_service)
        
        recommendations = await promotion_service.optimize_registration_funnel()
        
        return {
            "success": True,
            "data": recommendations
        }
        
    except Exception as e:
        logger.error(f"获取优化建议失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取优化建议失败: {str(e)}"
        )


@router.get("/potential-lawyers")
async def get_potential_lawyers(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """
    获取潜在律师邮箱列表
    
    用于推广活动的目标用户筛选
    """
    try:
        email_service = EmailService()
        promotion_service = LawyerPromotionService(email_service)
        
        emails = await promotion_service.get_potential_lawyer_emails(db)
        
        # 限制返回数量
        limited_emails = emails[:limit] if emails else []
        
        return {
            "success": True,
            "data": {
                "total_count": len(emails),
                "returned_count": len(limited_emails),
                "emails": limited_emails
            }
        }
        
    except Exception as e:
        logger.error(f"获取潜在律师列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取潜在律师列表失败: {str(e)}"
        )


@router.get("/campaign-performance/{campaign_name}")
async def get_campaign_performance(
    campaign_name: str,
    days: int = 30,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """
    获取特定推广活动的效果数据
    """
    try:
        # 这里可以添加具体的活动效果查询逻辑
        # 暂时返回模拟数据
        
        return {
            "success": True,
            "data": {
                "campaign_name": campaign_name,
                "period_days": days,
                "emails_sent": 1000,
                "emails_opened": 350,
                "links_clicked": 120,
                "registrations": 45,
                "certifications": 32,
                "open_rate": 35.0,
                "click_rate": 12.0,
                "conversion_rate": 4.5,
                "certification_rate": 3.2
            }
        }
        
    except Exception as e:
        logger.error(f"获取活动效果失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取活动效果失败: {str(e)}"
        )


@router.post("/test-promotion-email")
async def test_promotion_email(
    test_email: EmailStr,
    current_admin = Depends(get_current_admin_user)
):
    """
    发送测试推广邮件
    
    用于测试邮件模板和发送功能
    """
    try:
        email_service = EmailService()
        
        template_vars = {
            'registration_url': 'https://lawsker.com/lawyer-registration-landing.html?test=true',
            'unsubscribe_url': 'https://lawsker.com/unsubscribe',
            'campaign_name': 'test_campaign',
            'timestamp': '2025-01-01T00:00:00'
        }
        
        success = await email_service.send_lawyer_promotion_email(
            test_email,
            template_vars
        )
        
        if success:
            return {
                "success": True,
                "message": f"测试邮件已发送到 {test_email}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="测试邮件发送失败"
            )
        
    except Exception as e:
        logger.error(f"发送测试邮件失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送测试邮件失败: {str(e)}"
        )