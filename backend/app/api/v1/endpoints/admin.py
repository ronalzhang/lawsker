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
            description=config_item.description,
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