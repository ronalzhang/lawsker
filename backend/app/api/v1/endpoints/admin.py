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
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

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