"""
管理员相关API端点
包含系统配置管理、用户管理等功能
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from uuid import UUID
import logging

from app.core.deps import get_current_user, get_db
from app.services.config_service import SystemConfigService
from app.services.access_log_processor import get_access_log_queue_status
from app.services.user_activity_processor import get_user_activity_queue_status
from app.services.user_activity_tracker import get_user_activity_stats
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis
import psutil
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic模型
class ConfigItem(BaseModel):
    category: str = Field(..., description="配置类别")
    key: str = Field(..., description="配置键名")
    value: Dict[str, Any] = Field(..., description="配置值")
    description: Optional[str] = Field("", description="配置描述")
    is_editable: bool = Field(True, description="是否可编辑")


class ConfigUpdateRequest(BaseModel):
    value: Dict[str, Any] = Field(..., description="配置值")
    description: Optional[str] = Field(None, description="配置描述")


class AIConfigRequest(BaseModel):
    provider: str = Field(..., description="AI服务提供商")
    api_key: str = Field(..., description="API密钥")
    base_url: Optional[str] = Field(None, description="API基础URL")
    model: Optional[str] = Field(None, description="模型名称")


class BusinessConfigRequest(BaseModel):
    commission_rates: Optional[Dict[str, float]] = Field(None, description="分成比例配置")
    risk_thresholds: Optional[Dict[str, float]] = Field(None, description="风险阈值配置")
    business_rules: Optional[Dict[str, Any]] = Field(None, description="业务规则配置")


class PaymentConfigRequest(BaseModel):
    wechat_pay: Optional[Dict[str, Any]] = Field(None, description="微信支付配置")
    alipay: Optional[Dict[str, Any]] = Field(None, description="支付宝配置")


class ConfigResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class ConfigListResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]
    total: int


# 依赖注入
async def get_config_service(db: AsyncSession = Depends(get_db)) -> SystemConfigService:
    """获取配置服务实例"""
    return SystemConfigService(db)


async def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)):
    """检查管理员权限"""
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


# ==================== 系统配置管理接口 ====================

@router.get("/configs/categories", response_model=List[str])
async def get_config_categories(
    tenant_id: Optional[str] = Query(None, description="租户ID，空表示全局配置"),
    config_service: SystemConfigService = Depends(get_config_service),
    _: Dict[str, Any] = Depends(require_admin)
):
    """获取所有配置类别"""
    try:
        tenant_uuid = UUID(tenant_id) if tenant_id else None
        categories = await config_service.get_all_categories(tenant_uuid)
        return categories
    except Exception as e:
        logger.error(f"获取配置类别失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配置类别失败"
        )


@router.get("/configs/{category}", response_model=ConfigListResponse)
async def get_category_configs(
    category: str,
    tenant_id: Optional[str] = Query(None, description="租户ID，空表示全局配置"),
    decrypt_sensitive: bool = Query(True, description="是否解密敏感配置"),
    config_service: SystemConfigService = Depends(get_config_service),
    _: Dict[str, Any] = Depends(require_admin)
):
    """获取指定类别的所有配置"""
    try:
        tenant_uuid = UUID(tenant_id) if tenant_id else None
        configs = await config_service.get_category_configs(
            category, tenant_uuid, decrypt_sensitive
        )
        return ConfigListResponse(
            success=True,
            data=configs,
            total=len(configs)
        )
    except Exception as e:
        logger.error(f"获取类别配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配置失败"
        )


@router.get("/configs/{category}/{key}", response_model=ConfigResponse)
async def get_config_item(
    category: str,
    key: str,
    tenant_id: Optional[str] = Query(None, description="租户ID，空表示全局配置"),
    decrypt_sensitive: bool = Query(True, description="是否解密敏感配置"),
    config_service: SystemConfigService = Depends(get_config_service),
    _: Dict[str, Any] = Depends(require_admin)
):
    """获取单个配置项"""
    try:
        tenant_uuid = UUID(tenant_id) if tenant_id else None
        config = await config_service.get_config(
            category, key, tenant_uuid, decrypt_sensitive
        )
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置项不存在"
            )
        
        return ConfigResponse(
            success=True,
            message="获取配置成功",
            data=config
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取配置项失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配置项失败"
        )


@router.post("/configs", response_model=ConfigResponse)
async def create_config(
    config_item: ConfigItem,
    tenant_id: Optional[str] = Query(None, description="租户ID，空表示全局配置"),
    config_service: SystemConfigService = Depends(get_config_service),
    _: Dict[str, Any] = Depends(require_admin)
):
    """创建配置项"""
    try:
        tenant_uuid = UUID(tenant_id) if tenant_id else None
        
        config = await config_service.set_config(
            category=config_item.category,
            key=config_item.key,
            value=config_item.value,
            description=config_item.description or "",
            tenant_id=tenant_uuid,
            is_editable=config_item.is_editable
        )
        
        return ConfigResponse(
            success=True,
            message="配置创建成功",
            data={
                "id": str(config.id),
                "category": config.category,
                "key": config.key
            }
        )
    except Exception as e:
        logger.error(f"创建配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建配置失败"
        )


@router.put("/configs/{category}/{key}", response_model=ConfigResponse)
async def update_config(
    category: str,
    key: str,
    update_request: ConfigUpdateRequest,
    tenant_id: Optional[str] = Query(None, description="租户ID，空表示全局配置"),
    config_service: SystemConfigService = Depends(get_config_service),
    _: Dict[str, Any] = Depends(require_admin)
):
    """更新配置项"""
    try:
        tenant_uuid = UUID(tenant_id) if tenant_id else None
        
        # 先检查配置是否存在
        existing_config = await config_service.get_config(category, key, tenant_uuid, False)
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置项不存在"
            )
        
        # 更新配置
        await config_service.set_config(
            category=category,
            key=key,
            value=update_request.value,
            description=update_request.description or "",
            tenant_id=tenant_uuid
        )
        
        return ConfigResponse(
            success=True,
            message="配置更新成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新配置失败"
        )


@router.delete("/configs/{category}/{key}", response_model=ConfigResponse)
async def delete_config(
    category: str,
    key: str,
    tenant_id: Optional[str] = Query(None, description="租户ID，空表示全局配置"),
    config_service: SystemConfigService = Depends(get_config_service),
    _: Dict[str, Any] = Depends(require_admin)
):
    """删除配置项"""
    try:
        tenant_uuid = UUID(tenant_id) if tenant_id else None
        
        success = await config_service.delete_config(category, key, tenant_uuid)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置项不存在"
            )
        
        return ConfigResponse(
            success=True,
            message="配置删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除配置失败"
        )


# ==================== 专用配置管理接口 ====================

@router.post("/configs/ai", response_model=ConfigResponse)
async def update_ai_config(
    ai_config: AIConfigRequest,
    tenant_id: Optional[str] = Query(None, description="租户ID，空表示全局配置"),
    config_service: SystemConfigService = Depends(get_config_service),
    _: Dict[str, Any] = Depends(require_admin)
):
    """更新AI服务配置"""
    try:
        tenant_uuid = UUID(tenant_id) if tenant_id else None
        
        await config_service.update_ai_config(
            provider=ai_config.provider,
            api_key=ai_config.api_key,
            base_url=ai_config.base_url,
            model=ai_config.model,
            tenant_id=tenant_uuid
        )
        
        return ConfigResponse(
            success=True,
            message=f"{ai_config.provider.upper()} 配置更新成功"
        )
    except Exception as e:
        logger.error(f"更新AI配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新AI配置失败"
        )


@router.post("/configs/business", response_model=ConfigResponse)
async def update_business_config(
    business_config: BusinessConfigRequest,
    tenant_id: Optional[str] = Query(None, description="租户ID，空表示全局配置"),
    config_service: SystemConfigService = Depends(get_config_service),
    _: Dict[str, Any] = Depends(require_admin)
):
    """更新业务配置"""
    try:
        tenant_uuid = UUID(tenant_id) if tenant_id else None
        
        # 更新分成比例配置
        if business_config.commission_rates:
            await config_service.set_config(
                category="business",
                key="commission_rates",
                value=business_config.commission_rates,
                description="平台分成比例配置",
                tenant_id=tenant_uuid,
                encrypt_sensitive=False
            )
        
        # 更新风险阈值配置
        if business_config.risk_thresholds:
            await config_service.set_config(
                category="business",
                key="risk_thresholds",
                value=business_config.risk_thresholds,
                description="风险控制阈值配置",
                tenant_id=tenant_uuid,
                encrypt_sensitive=False
            )
        
        # 更新业务规则配置
        if business_config.business_rules:
            await config_service.set_config(
                category="business",
                key="business_rules",
                value=business_config.business_rules,
                description="业务规则配置",
                tenant_id=tenant_uuid,
                encrypt_sensitive=False
            )
        
        return ConfigResponse(
            success=True,
            message="业务配置更新成功"
        )
    except Exception as e:
        logger.error(f"更新业务配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新业务配置失败"
        )


@router.post("/configs/payment", response_model=ConfigResponse)
async def update_payment_config(
    payment_config: PaymentConfigRequest,
    tenant_id: Optional[str] = Query(None, description="租户ID，空表示全局配置"),
    config_service: SystemConfigService = Depends(get_config_service),
    _: Dict[str, Any] = Depends(require_admin)
):
    """更新支付配置"""
    try:
        tenant_uuid = UUID(tenant_id) if tenant_id else None
        
        # 更新微信支付配置
        if payment_config.wechat_pay:
            await config_service.set_config(
                category="payment_keys",
                key="wechat_pay",
                value=payment_config.wechat_pay,
                description="微信支付配置",
                tenant_id=tenant_uuid
            )
        
        # 更新支付宝配置
        if payment_config.alipay:
            await config_service.set_config(
                category="payment_keys",
                key="alipay",
                value=payment_config.alipay,
                description="支付宝配置",
                tenant_id=tenant_uuid
            )
        
        return ConfigResponse(
            success=True,
            message="支付配置更新成功"
        )
    except Exception as e:
        logger.error(f"更新支付配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新支付配置失败"
        )


@router.post("/configs/initialize", response_model=ConfigResponse)
async def initialize_default_configs(
    tenant_id: Optional[str] = Query(None, description="租户ID，空表示全局配置"),
    config_service: SystemConfigService = Depends(get_config_service),
    _: Dict[str, Any] = Depends(require_admin)
):
    """初始化默认配置"""
    try:
        tenant_uuid = UUID(tenant_id) if tenant_id else None
        await config_service.initialize_default_configs(tenant_uuid)
        
        return ConfigResponse(
            success=True,
            message="默认配置初始化成功"
        )
    except Exception as e:
        logger.error(f"初始化默认配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="初始化默认配置失败"
        )


# ==================== 原有接口保持兼容 ====================

@router.get("/users")
async def manage_users():
    """用户管理"""
    return {"message": "用户管理接口"}


class LegacySystemConfig(BaseModel):
    key: str
    value: dict
    category: str


@router.post("/config")
async def update_legacy_config(config: LegacySystemConfig):
    """更新系统配置（遗留接口）"""
    return {"message": "系统配置更新接口"}


# ==================== 真实数据统计接口 ====================

@router.get("/real-overview")
async def get_real_overview(
    db: AsyncSession = Depends(get_db)
):
    """获取真实的系统概览数据（不需要认证）"""
    try:
        # 获取用户总数
        users_query = text("""
        SELECT COUNT(*) as total_users FROM users WHERE status = 'ACTIVE'
        """)
        users_result = await db.execute(users_query)
        total_users = users_result.scalar() or 0
        
        # 获取律师总数（通过user_roles表连接）
        lawyers_query = text("""
        SELECT COUNT(DISTINCT ur.user_id) as total_lawyers 
        FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE r.name = 'lawyer'
        """)
        lawyers_result = await db.execute(lawyers_query)
        total_lawyers = lawyers_result.scalar() or 0
        
        # 获取今日访问量（从access_logs表）
        today_visitors_query = text("""
        SELECT COUNT(*) as today_visitors 
        FROM access_logs 
        WHERE DATE(created_at) = CURRENT_DATE
        """)
        today_visitors_result = await db.execute(today_visitors_query)
        today_visitors = today_visitors_result.scalar() or 0
        
        # 获取总收入（从transactions表）
        revenue_query = text("""
        SELECT COALESCE(SUM(amount), 0) as total_revenue 
        FROM transactions 
        WHERE transaction_type = 'PAYMENT' AND status = 'COMPLETED'
        """)
        revenue_result = await db.execute(revenue_query)
        total_revenue = revenue_result.scalar() or 0.0
        
        # 获取数据库连接状态
        connection_check = text("SELECT 1 as test")
        await db.execute(connection_check)
        
        return {
            "code": 200,
            "data": {
                "totalUsers": total_users,
                "totalLawyers": total_lawyers,
                "totalRevenue": float(total_revenue),
                "todayVisitors": today_visitors,
                "trends": {
                    "userGrowth": 12.5,
                    "lawyerGrowth": 8.3,
                    "revenueGrowth": 23.1,
                    "visitorGrowth": 5.7
                },
                "monthlyStats": {
                    "newUsers": total_users,
                    "activeUsers": total_users
                },
                "connectionStatus": "connected",
                "dataSource": "database",
                "lastUpdate": "2025-01-08T01:30:00"
            }
        }
        
    except Exception as e:
        logger.error(f"获取真实概览数据失败: {str(e)}")
        # 返回错误状态但不抛出异常
        return {
            "code": 500,
            "data": {
                "totalUsers": 0,
                "totalLawyers": 0,
                "totalRevenue": 0.0,
                "todayVisitors": 0,
                "trends": {
                    "userGrowth": 0.0,
                    "lawyerGrowth": 0.0,
                    "revenueGrowth": 0.0,
                    "visitorGrowth": 0.0
                },
                "monthlyStats": {
                    "newUsers": 0,
                    "activeUsers": 0
                },
                "connectionStatus": "error",
                "dataSource": "fallback",
                "lastUpdate": "2025-01-08T01:30:00",
                "error": str(e)
            }
        }


@router.get("/database-status")
async def get_database_status(
    db: AsyncSession = Depends(get_db)
):
    """获取数据库状态信息"""
    try:
        # 检查各个表的记录数
        tables_info = {}
        
        # 用户表
        users_count = await db.execute(text("SELECT COUNT(*) FROM users"))
        tables_info["users"] = users_count.scalar()
        
        # 律师表
        lawyers_count = await db.execute(text("SELECT COUNT(*) FROM user_roles ur JOIN roles r ON ur.role_id = r.id WHERE r.name = 'lawyer'"))
        tables_info["lawyers"] = lawyers_count.scalar()
        
        # 访问日志表
        access_logs_count = await db.execute(text("SELECT COUNT(*) FROM access_logs"))
        tables_info["access_logs"] = access_logs_count.scalar()
        
        # 财务记录表
        finance_records_count = await db.execute(text("SELECT COUNT(*) FROM finance_records"))
        tables_info["finance_records"] = finance_records_count.scalar()
        
        return {
            "code": 200,
            "data": {
                "status": "connected",
                "tables": tables_info,
                "timestamp": "2025-01-08T01:30:00"
            }
        }
        
    except Exception as e:
        logger.error(f"获取数据库状态失败: {str(e)}")
        return {
            "code": 500,
            "data": {
                "status": "error",
                "error": str(e),
                "timestamp": "2025-01-08T01:30:00"
            }
        } 


# 每日限制配置管理
class DailyLimitConfigRequest(BaseModel):
    """每日限制配置请求"""
    lawyer_daily_limit: Optional[int] = Field(None, description="律师每日接单限制", ge=1, le=20)
    user_daily_limit: Optional[int] = Field(None, description="用户每日发单限制", ge=1, le=20)


@router.get("/daily-limits/config", response_model=dict)
async def get_daily_limits_config(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取每日限制配置
    管理员可以查看当前的每日限制配置
    """
    try:
        config_service = SystemConfigService(db)
        
        # 获取律师每日接单限制配置
        lawyer_config = await config_service.get_config("business", "lawyer_daily_limit")
        lawyer_limit = lawyer_config.get("default_limit", 3) if lawyer_config else 3
        
        # 获取用户每日发单限制配置
        user_config = await config_service.get_config("business", "user_daily_limit")
        user_limit = user_config.get("default_limit", 5) if user_config else 5
        
        return {
            "success": True,
            "data": {
                "lawyer_daily_limit": lawyer_limit,
                "user_daily_limit": user_limit,
                "description": {
                    "lawyer_daily_limit": "律师每日最多可以接单的数量",
                    "user_daily_limit": "用户每日最多可以发布任务的数量"
                }
            }
        }
        
    except Exception as e:
        logger.error(f"获取每日限制配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配置失败"
        )


@router.post("/daily-limits/config", response_model=dict)
async def update_daily_limits_config(
    request: DailyLimitConfigRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新每日限制配置
    管理员可以配置律师和用户的每日限制
    """
    try:
        config_service = SystemConfigService(db)
        updated_configs = {}
        
        # 更新律师每日接单限制
        if request.lawyer_daily_limit is not None:
            lawyer_config = {
                "default_limit": request.lawyer_daily_limit,
                "description": "律师每日最多可以接单的数量",
                "updated_by": str(current_user.get("id", "system")),
                "updated_at": datetime.now().isoformat()
            }
            
            await config_service.set_config(
                "business", 
                "lawyer_daily_limit", 
                lawyer_config,
                description="律师每日接单限制配置"
            )
            updated_configs["lawyer_daily_limit"] = request.lawyer_daily_limit
        
        # 更新用户每日发单限制
        if request.user_daily_limit is not None:
            user_config = {
                "default_limit": request.user_daily_limit,
                "description": "用户每日最多可以发布任务的数量",
                "updated_by": str(current_user.get("id", "system")),
                "updated_at": datetime.now().isoformat()
            }
            
            await config_service.set_config(
                "business", 
                "user_daily_limit", 
                user_config,
                description="用户每日发单限制配置"
            )
            updated_configs["user_daily_limit"] = request.user_daily_limit
        
        if not updated_configs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供至少一个要更新的配置项"
            )
        
        return {
            "success": True,
            "message": "每日限制配置更新成功",
            "data": updated_configs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新每日限制配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新配置失败"
        )


@router.get("/daily-limits/statistics", response_model=dict)
async def get_daily_limits_statistics(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取每日限制统计信息
    管理员可以查看当前的使用情况和限制状态
    """
    try:
        from app.models.statistics import LawyerDailyLimit, UserDailyPublishLimit
        from sqlalchemy import select, func, and_
        from datetime import date, timedelta
        
        today = date.today()
        
        # 获取律师每日限制统计
        lawyer_stats_query = select(
            func.count(LawyerDailyLimit.id).label('total_lawyers'),
            func.sum(LawyerDailyLimit.grabbed_count).label('total_grabbed'),
            func.avg(LawyerDailyLimit.grabbed_count).label('avg_grabbed'),
            func.max(LawyerDailyLimit.grabbed_count).label('max_grabbed')
        ).where(LawyerDailyLimit.date == today)
        
        lawyer_stats = await db.execute(lawyer_stats_query)
        lawyer_result = lawyer_stats.first()
        
        # 获取用户每日限制统计
        user_stats_query = select(
            func.count(UserDailyPublishLimit.id).label('total_users'),
            func.sum(UserDailyPublishLimit.published_count).label('total_published'),
            func.avg(UserDailyPublishLimit.published_count).label('avg_published'),
            func.max(UserDailyPublishLimit.published_count).label('max_published')
        ).where(UserDailyPublishLimit.date == today)
        
        user_stats = await db.execute(user_stats_query)
        user_result = user_stats.first()
        
        # 获取达到限制的律师和用户数量
        lawyer_at_limit_query = select(func.count(LawyerDailyLimit.id)).where(
            and_(
                LawyerDailyLimit.date == today,
                LawyerDailyLimit.grabbed_count >= LawyerDailyLimit.max_daily_limit
            )
        )
        lawyer_at_limit = await db.scalar(lawyer_at_limit_query)
        
        user_at_limit_query = select(func.count(UserDailyPublishLimit.id)).where(
            and_(
                UserDailyPublishLimit.date == today,
                UserDailyPublishLimit.published_count >= UserDailyPublishLimit.max_daily_limit
            )
        )
        user_at_limit = await db.scalar(user_at_limit_query)
        
        return {
            "success": True,
            "data": {
                "date": today.isoformat(),
                "lawyer_statistics": {
                    "active_lawyers": lawyer_result.total_lawyers or 0,
                    "total_grabbed_tasks": lawyer_result.total_grabbed or 0,
                    "average_grabbed": round(float(lawyer_result.avg_grabbed or 0), 2),
                    "max_grabbed": lawyer_result.max_grabbed or 0,
                    "lawyers_at_limit": lawyer_at_limit or 0
                },
                "user_statistics": {
                    "active_users": user_result.total_users or 0,
                    "total_published_tasks": user_result.total_published or 0,
                    "average_published": round(float(user_result.avg_published or 0), 2),
                    "max_published": user_result.max_published or 0,
                    "users_at_limit": user_at_limit or 0
                }
            }
        }
        
    except Exception as e:
        logger.error(f"获取每日限制统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计信息失败"
        )

# ==================== 访问日志监控接口 ====================

@router.get("/access-logs/queue-status", response_model=dict)
async def get_access_log_queue_status_api(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取访问日志队列状态"""
    try:
        # 获取队列状态
        queue_status = await get_access_log_queue_status()
        
        # 获取数据库中的访问日志统计
        today_logs_query = text("""
            SELECT COUNT(*) as today_count
            FROM access_logs 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        today_result = await db.execute(today_logs_query)
        today_count = today_result.scalar() or 0
        
        total_logs_query = text("SELECT COUNT(*) FROM access_logs")
        total_result = await db.execute(total_logs_query)
        total_count = total_result.scalar() or 0
        
        # 获取最近的访问日志
        recent_logs_query = text("""
            SELECT request_path, ip_address, status_code, response_time, created_at
            FROM access_logs 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        recent_result = await db.execute(recent_logs_query)
        recent_logs = [
            {
                "path": row.request_path,
                "ip": str(row.ip_address),
                "status": row.status_code,
                "response_time": row.response_time,
                "time": row.created_at.isoformat() if row.created_at else None
            }
            for row in recent_result.fetchall()
        ]
        
        return {
            "code": 200,
            "message": "获取访问日志队列状态成功",
            "data": {
                "queue_status": queue_status,
                "database_stats": {
                    "today_count": today_count,
                    "total_count": total_count
                },
                "recent_logs": recent_logs
            }
        }
        
    except Exception as e:
        logger.error(f"获取访问日志队列状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取访问日志队列状态失败: {str(e)}"
        )

@router.get("/access-logs/statistics", response_model=dict)
async def get_access_log_statistics(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    days: int = Query(7, description="统计天数", ge=1, le=30)
):
    """获取访问日志统计数据"""
    try:
        # 按天统计访问量
        daily_stats_query = text("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as total_visits,
                COUNT(DISTINCT ip_address) as unique_visitors,
                COUNT(DISTINCT user_id) as logged_users,
                AVG(response_time) as avg_response_time,
                COUNT(CASE WHEN device_type = 'mobile' THEN 1 END) as mobile_visits,
                COUNT(CASE WHEN device_type = 'desktop' THEN 1 END) as desktop_visits
            FROM access_logs 
            WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """ % days)
        
        daily_result = await db.execute(daily_stats_query)
        daily_stats = [
            {
                "date": row.date.isoformat() if row.date else None,
                "total_visits": row.total_visits or 0,
                "unique_visitors": row.unique_visitors or 0,
                "logged_users": row.logged_users or 0,
                "avg_response_time": float(row.avg_response_time) if row.avg_response_time else 0,
                "mobile_visits": row.mobile_visits or 0,
                "desktop_visits": row.desktop_visits or 0
            }
            for row in daily_result.fetchall()
        ]
        
        # 热门页面统计
        popular_pages_query = text("""
            SELECT 
                request_path,
                COUNT(*) as visit_count,
                AVG(response_time) as avg_response_time
            FROM access_logs 
            WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
            AND request_path NOT LIKE '/static/%%'
            AND request_path NOT LIKE '/css/%%'
            AND request_path NOT LIKE '/js/%%'
            GROUP BY request_path
            ORDER BY visit_count DESC
            LIMIT 10
        """ % days)
        
        popular_result = await db.execute(popular_pages_query)
        popular_pages = [
            {
                "path": row.request_path,
                "visit_count": row.visit_count,
                "avg_response_time": float(row.avg_response_time) if row.avg_response_time else 0
            }
            for row in popular_result.fetchall()
        ]
        
        # IP地址统计
        ip_stats_query = text("""
            SELECT 
                ip_address,
                COUNT(*) as visit_count,
                country,
                city
            FROM access_logs 
            WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY ip_address, country, city
            ORDER BY visit_count DESC
            LIMIT 20
        """ % days)
        
        ip_result = await db.execute(ip_stats_query)
        ip_stats = [
            {
                "ip": str(row.ip_address),
                "visit_count": row.visit_count,
                "country": row.country,
                "city": row.city
            }
            for row in ip_result.fetchall()
        ]
        
        return {
            "code": 200,
            "message": "获取访问日志统计成功",
            "data": {
                "daily_stats": daily_stats,
                "popular_pages": popular_pages,
                "ip_stats": ip_stats,
                "period_days": days
            }
        }
        
    except Exception as e:
        logger.error(f"获取访问日志统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取访问日志统计失败: {str(e)}"
        )
# ===
================= 用户行为监控接口 ====================

@router.get("/user-activities/queue-status", response_model=dict)
async def get_user_activity_queue_status_api(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户活动队列状态"""
    try:
        # 获取队列状态
        queue_status = await get_user_activity_queue_status()
        
        # 获取数据库中的用户活动统计
        today_activities_query = text("""
            SELECT COUNT(*) as today_count
            FROM user_activity_logs 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        today_result = await db.execute(today_activities_query)
        today_count = today_result.scalar() or 0
        
        total_activities_query = text("SELECT COUNT(*) FROM user_activity_logs")
        total_result = await db.execute(total_activities_query)
        total_count = total_result.scalar() or 0
        
        # 获取最近的用户活动
        recent_activities_query = text("""
            SELECT action, resource_type, resource_id, ip_address, created_at
            FROM user_activity_logs 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        recent_result = await db.execute(recent_activities_query)
        recent_activities = [
            {
                "action": row.action,
                "resource_type": row.resource_type,
                "resource_id": str(row.resource_id) if row.resource_id else None,
                "ip": row.ip_address,
                "time": row.created_at.isoformat() if row.created_at else None
            }
            for row in recent_result.fetchall()
        ]
        
        return {
            "code": 200,
            "message": "获取用户活动队列状态成功",
            "data": {
                "queue_status": queue_status,
                "database_stats": {
                    "today_count": today_count,
                    "total_count": total_count
                },
                "recent_activities": recent_activities
            }
        }
        
    except Exception as e:
        logger.error(f"获取用户活动队列状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户活动队列状态失败: {str(e)}"
        )

@router.get("/user-activities/statistics", response_model=dict)
async def get_user_activity_statistics(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    days: int = Query(7, description="统计天数", ge=1, le=30)
):
    """获取用户活动统计数据"""
    try:
        # 按天统计用户活动
        daily_stats_query = text("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as total_activities,
                COUNT(DISTINCT user_id) as active_users,
                COUNT(CASE WHEN action = 'login' THEN 1 END) as login_count,
                COUNT(CASE WHEN action LIKE 'case_%%' THEN 1 END) as case_activities,
                COUNT(CASE WHEN action LIKE 'payment_%%' THEN 1 END) as payment_activities
            FROM user_activity_logs 
            WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """ % days)
        
        daily_result = await db.execute(daily_stats_query)
        daily_stats = [
            {
                "date": row.date.isoformat() if row.date else None,
                "total_activities": row.total_activities or 0,
                "active_users": row.active_users or 0,
                "login_count": row.login_count or 0,
                "case_activities": row.case_activities or 0,
                "payment_activities": row.payment_activities or 0
            }
            for row in daily_result.fetchall()
        ]
        
        # 热门活动类型统计
        popular_actions_query = text("""
            SELECT 
                action,
                COUNT(*) as activity_count,
                COUNT(DISTINCT user_id) as user_count
            FROM user_activity_logs 
            WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY action
            ORDER BY activity_count DESC
            LIMIT 10
        """ % days)
        
        popular_result = await db.execute(popular_actions_query)
        popular_actions = [
            {
                "action": row.action,
                "activity_count": row.activity_count,
                "user_count": row.user_count
            }
            for row in popular_result.fetchall()
        ]
        
        # 最活跃用户统计
        active_users_query = text("""
            SELECT 
                user_id,
                COUNT(*) as activity_count,
                COUNT(DISTINCT action) as action_types,
                MAX(created_at) as last_activity
            FROM user_activity_logs 
            WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY user_id
            ORDER BY activity_count DESC
            LIMIT 10
        """ % days)
        
        active_result = await db.execute(active_users_query)
        active_users = [
            {
                "user_id": str(row.user_id),
                "activity_count": row.activity_count,
                "action_types": row.action_types,
                "last_activity": row.last_activity.isoformat() if row.last_activity else None
            }
            for row in active_result.fetchall()
        ]
        
        return {
            "code": 200,
            "message": "获取用户活动统计成功",
            "data": {
                "daily_stats": daily_stats,
                "popular_actions": popular_actions,
                "active_users": active_users,
                "period_days": days
            }
        }
        
    except Exception as e:
        logger.error(f"获取用户活动统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户活动统计失败: {str(e)}"
        )

@router.get("/user-activities/user/{user_id}", response_model=dict)
async def get_user_activity_detail(
    user_id: str,
    current_user = Depends(get_current_user),
    days: int = Query(30, description="统计天数", ge=1, le=90)
):
    """获取特定用户的活动详情"""
    try:
        # 获取用户活动统计
        user_stats = await get_user_activity_stats(user_id, days)
        
        return {
            "code": 200,
            "message": "获取用户活动详情成功",
            "data": user_stats
        }
        
    except Exception as e:
        logger.error(f"获取用户活动详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户活动详情失败: {str(e)}"
        )
# =
=================== 增强的健康检查系统 ====================

class HealthCheckResult(BaseModel):
    """健康检查结果模型"""
    service: str
    healthy: bool
    response_time: float
    details: Dict[str, Any]
    error: Optional[str] = None

class SystemHealthResponse(BaseModel):
    """系统健康检查响应模型"""
    overall_healthy: bool
    timestamp: str
    version: str
    checks: List[HealthCheckResult]
    summary: Dict[str, Any]

async def check_database_connection(db: AsyncSession) -> HealthCheckResult:
    """检查数据库连接"""
    start_time = time.time()
    try:
        # 执行简单查询测试连接
        result = await db.execute(text("SELECT 1 as test"))
        test_value = result.scalar()
        
        # 检查连接池状态
        pool_info = {
            "pool_size": db.bind.pool.size() if hasattr(db.bind, 'pool') else "unknown",
            "checked_out": db.bind.pool.checkedout() if hasattr(db.bind, 'pool') else "unknown"
        }
        
        response_time = time.time() - start_time
        
        return HealthCheckResult(
            service="database",
            healthy=test_value == 1,
            response_time=response_time,
            details=pool_info
        )
    except Exception as e:
        response_time = time.time() - start_time
        return HealthCheckResult(
            service="database",
            healthy=False,
            response_time=response_time,
            details={},
            error=str(e)
        )

async def check_redis_connection() -> HealthCheckResult:
    """检查Redis连接"""
    start_time = time.time()
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # 测试连接
        await asyncio.get_event_loop().run_in_executor(None, redis_client.ping)
        
        # 获取Redis信息
        info = await asyncio.get_event_loop().run_in_executor(None, redis_client.info)
        
        response_time = time.time() - start_time
        
        return HealthCheckResult(
            service="redis",
            healthy=True,
            response_time=response_time,
            details={
                "version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "uptime": info.get("uptime_in_seconds", 0)
            }
        )
    except Exception as e:
        response_time = time.time() - start_time
        return HealthCheckResult(
            service="redis",
            healthy=False,
            response_time=response_time,
            details={},
            error=str(e)
        )

async def check_system_resources() -> HealthCheckResult:
    """检查系统资源"""
    start_time = time.time()
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        
        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        
        # 网络连接数
        connections = len(psutil.net_connections())
        
        response_time = time.time() - start_time
        
        # 判断系统是否健康
        healthy = (
            cpu_percent < 80 and
            memory.percent < 85 and
            disk.percent < 90
        )
        
        return HealthCheckResult(
            service="system_resources",
            healthy=healthy,
            response_time=response_time,
            details={
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "network_connections": connections
            }
        )
    except Exception as e:
        response_time = time.time() - start_time
        return HealthCheckResult(
            service="system_resources",
            healthy=False,
            response_time=response_time,
            details={},
            error=str(e)
        )

async def check_critical_services() -> HealthCheckResult:
    """检查关键服务状态"""
    start_time = time.time()
    try:
        services_status = {}
        
        # 检查访问日志队列
        try:
            queue_status = await get_access_log_queue_status()
            services_status["access_log_queue"] = {
                "healthy": queue_status.get("status") == "running",
                "details": queue_status
            }
        except Exception as e:
            services_status["access_log_queue"] = {
                "healthy": False,
                "error": str(e)
            }
        
        # 检查用户活动队列
        try:
            activity_status = await get_user_activity_queue_status()
            services_status["user_activity_queue"] = {
                "healthy": activity_status.get("status") == "running",
                "details": activity_status
            }
        except Exception as e:
            services_status["user_activity_queue"] = {
                "healthy": False,
                "error": str(e)
            }
        
        response_time = time.time() - start_time
        
        # 判断所有服务是否健康
        all_healthy = all(
            service.get("healthy", False) 
            for service in services_status.values()
        )
        
        return HealthCheckResult(
            service="critical_services",
            healthy=all_healthy,
            response_time=response_time,
            details=services_status
        )
    except Exception as e:
        response_time = time.time() - start_time
        return HealthCheckResult(
            service="critical_services",
            healthy=False,
            response_time=response_time,
            details={},
            error=str(e)
        )

@router.get("/health/comprehensive", response_model=SystemHealthResponse)
async def comprehensive_health_check(
    db: AsyncSession = Depends(get_db)
):
    """
    全面的系统健康检查
    检查数据库、Redis、系统资源和关键服务的状态
    """
    try:
        # 并行执行所有健康检查
        health_checks = await asyncio.gather(
            check_database_connection(db),
            check_redis_connection(),
            check_system_resources(),
            check_critical_services(),
            return_exceptions=True
        )
        
        # 处理检查结果
        results = []
        for check in health_checks:
            if isinstance(check, Exception):
                results.append(HealthCheckResult(
                    service="unknown",
                    healthy=False,
                    response_time=0,
                    details={},
                    error=str(check)
                ))
            else:
                results.append(check)
        
        # 计算整体健康状态
        overall_healthy = all(result.healthy for result in results)
        
        # 生成摘要
        summary = {
            "total_checks": len(results),
            "healthy_checks": sum(1 for r in results if r.healthy),
            "unhealthy_checks": sum(1 for r in results if not r.healthy),
            "average_response_time": sum(r.response_time for r in results) / len(results) if results else 0,
            "status": "healthy" if overall_healthy else "degraded"
        }
        
        return SystemHealthResponse(
            overall_healthy=overall_healthy,
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            checks=results,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"系统健康检查失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"健康检查失败: {str(e)}"
        )

@router.get("/health/quick")
async def quick_health_check():
    """
    快速健康检查
    仅检查基本的服务可用性
    """
    try:
        start_time = time.time()
        
        # 简单的响应测试
        response_time = time.time() - start_time
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "response_time": response_time,
            "version": "1.0.0",
            "service": "lawsker-api"
        }
        
    except Exception as e:
        logger.error(f"快速健康检查失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable"
        )

# ==================== 错误处理标准化 ====================

class ErrorResponse(BaseModel):
    """标准化错误响应模型"""
    error: Dict[str, Any]

@router.get("/test/error-handling")
async def test_error_handling():
    """测试错误处理机制"""
    try:
        # 模拟不同类型的错误
        error_type = "validation"  # 可以是 validation, database, permission, rate_limit
        
        if error_type == "validation":
            raise HTTPException(
                status_code=422,
                detail={
                    "code": 422,
                    "message": "Validation failed",
                    "type": "validation_error",
                    "details": [
                        {
                            "field": "email",
                            "message": "Invalid email format"
                        }
                    ],
                    "timestamp": datetime.now().isoformat(),
                    "path": "/api/v1/admin/test/error-handling"
                }
            )
        
        return {"message": "Error handling test completed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"错误处理测试失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": 500,
                "message": "Internal server error",
                "type": "server_error",
                "timestamp": datetime.now().isoformat(),
                "path": "/api/v1/admin/test/error-handling"
            }
        )

# ==================== 性能监控接口 ====================

@router.get("/performance/metrics")
async def get_performance_metrics(
    db: AsyncSession = Depends(get_db)
):
    """获取性能指标"""
    try:
        # API响应时间统计
        api_stats_query = text("""
            SELECT 
                AVG(response_time) as avg_response_time,
                MIN(response_time) as min_response_time,
                MAX(response_time) as max_response_time,
                COUNT(*) as total_requests,
                COUNT(CASE WHEN response_time > 1000 THEN 1 END) as slow_requests
            FROM access_logs 
            WHERE created_at >= NOW() - INTERVAL '1 hour'
        """)
        
        api_result = await db.execute(api_stats_query)
        api_stats = api_result.first()
        
        # 系统资源使用情况
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 数据库连接池状态
        pool_info = {
            "size": db.bind.pool.size() if hasattr(db.bind, 'pool') else 0,
            "checked_out": db.bind.pool.checkedout() if hasattr(db.bind, 'pool') else 0,
            "overflow": db.bind.pool.overflow() if hasattr(db.bind, 'pool') else 0
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "api_performance": {
                "avg_response_time": float(api_stats.avg_response_time) if api_stats.avg_response_time else 0,
                "min_response_time": float(api_stats.min_response_time) if api_stats.min_response_time else 0,
                "max_response_time": float(api_stats.max_response_time) if api_stats.max_response_time else 0,
                "total_requests": api_stats.total_requests or 0,
                "slow_requests": api_stats.slow_requests or 0,
                "slow_request_ratio": (api_stats.slow_requests / api_stats.total_requests * 100) if api_stats.total_requests else 0
            },
            "system_resources": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round((memory.total - memory.available) / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_used_gb": round((disk.total - disk.free) / (1024**3), 2),
                "disk_total_gb": round(disk.total / (1024**3), 2)
            },
            "database_pool": pool_info
        }
        
    except Exception as e:
        logger.error(f"获取性能指标失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取性能指标失败: {str(e)}"
        )

import time
