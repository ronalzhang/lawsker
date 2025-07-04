"""
统一配置管理服务
负责系统级配置的安全管理，包括API keys、业务参数等
"""

import asyncio
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func, text
from sqlalchemy.orm import selectinload
from cryptography.fernet import Fernet
import base64
import os
import logging

from app.models.tenant import SystemConfig, Tenant
from app.core.config import settings

logger = logging.getLogger(__name__)


class ConfigEncryption:
    """配置加密管理类"""
    
    def __init__(self):
        # 从环境变量获取加密密钥，如果没有则生成一个
        encryption_key = os.getenv("CONFIG_ENCRYPTION_KEY")
        if not encryption_key:
            # 生成新的加密密钥
            key = Fernet.generate_key()
            encryption_key = base64.urlsafe_b64encode(key).decode()
            logger.warning(f"生成新的配置加密密钥，请将其保存到环境变量 CONFIG_ENCRYPTION_KEY 中: {encryption_key[:10]}...")
        
        self.encryption_key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
        self.fernet = Fernet(base64.urlsafe_b64decode(self.encryption_key))
    
    def encrypt_value(self, value: str) -> str:
        """加密敏感配置值"""
        try:
            if not value:
                return value
            return self.fernet.encrypt(value.encode()).decode()
        except Exception as e:
            logger.error(f"配置值加密失败: {str(e)}")
            raise
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """解密敏感配置值"""
        try:
            if not encrypted_value:
                return encrypted_value
            return self.fernet.decrypt(encrypted_value.encode()).decode()
        except Exception as e:
            logger.error(f"配置值解密失败: {str(e)}")
            raise


class SystemConfigService:
    """系统配置管理服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.encryption = ConfigEncryption()
        
        # 敏感配置类型定义
        self.sensitive_categories = {
            "ai_api_keys",
            "payment_keys", 
            "third_party_apis",
            "security_keys",
            "database_credentials"
        }
    
    async def get_config(
        self, 
        category: str, 
        key: str, 
        tenant_id: Optional[UUID] = None,
        decrypt_sensitive: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        获取配置项
        
        Args:
            category: 配置类别
            key: 配置键名
            tenant_id: 租户ID（None表示全局配置）
            decrypt_sensitive: 是否解密敏感配置
            
        Returns:
            配置值字典或None
        """
        try:
            query = select(SystemConfig).where(
                and_(
                    SystemConfig.category == category,
                    SystemConfig.key == key,
                    SystemConfig.tenant_id == tenant_id,
                    SystemConfig.is_active == True
                )
            )
            
            result = await self.db.execute(query)
            config = result.scalar_one_or_none()
            
            if not config:
                return None
            
            # 正确处理JSONB字段的值
            value: Dict[str, Any] = config.value if isinstance(config.value, dict) else {}
            
            # 如果是敏感配置且需要解密
            if (decrypt_sensitive and 
                category in self.sensitive_categories and 
                isinstance(value, dict) and 
                value.get("encrypted")):
                
                decrypted_data = {}
                for k, v in value.items():
                    if k != "encrypted" and isinstance(v, str):
                        try:
                            decrypted_data[k] = self.encryption.decrypt_value(v)
                        except:
                            decrypted_data[k] = v  # 如果解密失败，返回原值
                    else:
                        decrypted_data[k] = v
                
                return decrypted_data
            
            return value
            
        except Exception as e:
            logger.error(f"获取配置失败 - category: {category}, key: {key}, error: {str(e)}")
            return None
    
    async def set_config(
        self,
        category: str,
        key: str,
        value: Dict[str, Any],
        description: str = "",
        tenant_id: Optional[UUID] = None,
        is_editable: bool = True,
        encrypt_sensitive: bool = True
    ) -> SystemConfig:
        """
        设置配置项
        
        Args:
            category: 配置类别
            key: 配置键名
            value: 配置值
            description: 配置描述
            tenant_id: 租户ID（None表示全局配置）
            is_editable: 是否可编辑
            encrypt_sensitive: 是否加密敏感配置
            
        Returns:
            配置对象
        """
        try:
            # 如果是敏感配置且需要加密
            final_value = value
            if encrypt_sensitive and category in self.sensitive_categories:
                encrypted_value: Dict[str, Any] = {"encrypted": True}
                for k, v in value.items():
                    if isinstance(v, str) and v:  # 只加密非空字符串
                        encrypted_value[k] = self.encryption.encrypt_value(v)
                    else:
                        encrypted_value[k] = v
                final_value = encrypted_value
            
            # 查找是否已存在配置
            query = select(SystemConfig).where(
                and_(
                    SystemConfig.category == category,
                    SystemConfig.key == key,
                    SystemConfig.tenant_id == tenant_id
                )
            )
            
            result = await self.db.execute(query)
            config = result.scalar_one_or_none()
            
            if config:
                # 更新现有配置
                await self.db.execute(
                    update(SystemConfig)
                    .where(SystemConfig.id == config.id)
                    .values(
                        value=final_value,
                        description=description,
                        is_editable=is_editable,
                        updated_at=datetime.utcnow()
                    )
                )
            else:
                # 创建新配置
                config = SystemConfig(
                    tenant_id=tenant_id,
                    category=category,
                    key=key,
                    value=final_value,
                    description=description,
                    is_editable=is_editable
                )
                self.db.add(config)
            
            await self.db.commit()
            
            # 重新获取配置对象
            result = await self.db.execute(query)
            config = result.scalar_one_or_none()
            
            logger.info(f"配置设置成功 - category: {category}, key: {key}, tenant_id: {str(tenant_id) if tenant_id else 'global'}")
            
            return config
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"设置配置失败 - category: {category}, key: {key}, error: {str(e)}")
            raise
    
    async def get_category_configs(
        self,
        category: str,
        tenant_id: Optional[UUID] = None,
        decrypt_sensitive: bool = True
    ) -> List[Dict[str, Any]]:
        """获取指定类别的所有配置"""
        try:
            query = select(SystemConfig).where(
                and_(
                    SystemConfig.category == category,
                    SystemConfig.tenant_id == tenant_id,
                    SystemConfig.is_active == True
                )
            ).order_by(SystemConfig.key)
            
            result = await self.db.execute(query)
            configs = result.scalars().all()
            
            config_list = []
            for config in configs:
                config_data = {
                    "id": str(config.id),
                    "key": config.key,
                    "value": config.value,
                    "description": config.description,
                    "is_editable": config.is_editable,
                    "created_at": config.created_at.isoformat(),
                    "updated_at": config.updated_at.isoformat()
                }
                
                # 处理敏感配置解密
                if (decrypt_sensitive and 
                    category in self.sensitive_categories and 
                    isinstance(config.value, dict) and 
                    config.value.get("encrypted")):
                    
                    decrypted_value = {}
                    for k, v in config.value.items():
                        if k != "encrypted" and isinstance(v, str):
                            try:
                                decrypted_value[k] = self.encryption.decrypt_value(v)
                            except:
                                decrypted_value[k] = "****"  # 解密失败时隐藏
                        else:
                            decrypted_value[k] = v
                    
                    config_data["value"] = decrypted_value
                
                config_list.append(config_data)
            
            return config_list
            
        except Exception as e:
            logger.error(f"获取类别配置失败 - category: {category}, error: {str(e)}")
            return []
    
    async def initialize_default_configs(self, tenant_id: Optional[UUID] = None):
        """初始化默认系统配置"""
        try:
            # AI API配置
            await self._init_ai_configs(tenant_id)
            
            # 业务配置
            await self._init_business_configs(tenant_id)
            
            # 支付配置
            await self._init_payment_configs(tenant_id)
            
            # 通知配置
            await self._init_notification_configs(tenant_id)
            
            logger.info(f"默认配置初始化完成 - tenant_id: {str(tenant_id) if tenant_id else 'global'}")
            
        except Exception as e:
            logger.error(f"默认配置初始化失败: {str(e)}")
            raise
    
    async def _init_ai_configs(self, tenant_id: Optional[UUID] = None):
        """初始化AI相关配置"""
        ai_configs = [
            {
                "key": "openai",
                "value": {
                    "api_key": "YOUR_OPENAI_API_KEY",
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-4",
                    "timeout": 60,
                    "max_retries": 3
                },
                "description": "OpenAI API配置，用于AI文书生成"
            },
            {
                "key": "deepseek",
                "value": {
                    "api_key": "",  # 待配置
                    "base_url": "https://api.deepseek.com/v1",
                    "model": "deepseek-chat",
                    "timeout": 60,
                    "max_retries": 3
                },
                "description": "Deepseek API配置，用于内容优化润色"
            }
        ]
        
        for config in ai_configs:
            await self.set_config(
                category="ai_api_keys",
                key=config["key"],
                value=config["value"],
                description=config["description"],
                tenant_id=tenant_id
            )
    
    async def _init_business_configs(self, tenant_id: Optional[UUID] = None):
        """初始化业务配置"""
        business_configs = [
            {
                "key": "commission_rates",
                "value": {
                    "platform": 0.50,
                    "lawyer": 0.30,
                    "sales": 0.20,
                    "safety_margin": 0.15
                },
                "description": "平台分成比例配置"
            },
            {
                "key": "risk_thresholds",
                "value": {
                    "insurance_threshold": 100000.0,
                    "high_risk_threshold": 500000.0,
                    "auto_approve_threshold": 10000.0
                },
                "description": "风险控制阈值配置"
            },
            {
                "key": "business_rules",
                "value": {
                    "max_cases_per_lawyer": 50,
                    "case_timeout_days": 90,
                    "auto_assignment_enabled": True,
                    "review_required_threshold": 50000.0
                },
                "description": "业务规则配置"
            }
        ]
        
        for config in business_configs:
            await self.set_config(
                category="business",
                key=config["key"],
                value=config["value"],
                description=config["description"],
                tenant_id=tenant_id,
                encrypt_sensitive=False
            )
    
    async def _init_payment_configs(self, tenant_id: Optional[UUID] = None):
        """初始化支付配置"""
        payment_configs = [
            {
                "key": "wechat_pay",
                "value": {
                    "app_id": "",
                    "app_secret": "",
                    "mch_id": "",
                    "api_key": "",
                    "enabled": False
                },
                "description": "微信支付配置"
            },
            {
                "key": "alipay",
                "value": {
                    "app_id": "",
                    "private_key": "",
                    "public_key": "",
                    "enabled": False
                },
                "description": "支付宝配置"
            }
        ]
        
        for config in payment_configs:
            await self.set_config(
                category="payment_keys",
                key=config["key"],
                value=config["value"],
                description=config["description"],
                tenant_id=tenant_id
            )
    
    async def _init_notification_configs(self, tenant_id: Optional[UUID] = None):
        """初始化通知配置"""
        notification_configs = [
            {
                "key": "email_smtp",
                "value": {
                    "host": "",
                    "port": 587,
                    "username": "",
                    "password": "",
                    "use_tls": True,
                    "enabled": False
                },
                "description": "邮件SMTP配置"
            },
            {
                "key": "sms_provider",
                "value": {
                    "provider": "aliyun",
                    "access_key": "",
                    "secret_key": "",
                    "sign_name": "",
                    "enabled": False
                },
                "description": "短信服务配置"
            }
        ]
        
        for config in notification_configs:
            await self.set_config(
                category="third_party_apis",
                key=config["key"],
                value=config["value"],
                description=config["description"],
                tenant_id=tenant_id
            )
    
    async def update_ai_config(
        self,
        provider: str,
        api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        tenant_id: Optional[UUID] = None
    ) -> SystemConfig:
        """更新AI服务配置"""
        try:
            current_config = await self.get_config("ai_api_keys", provider, tenant_id)
            
            if not current_config:
                current_config = {
                    "api_key": "",
                    "base_url": "https://api.openai.com/v1" if provider == "openai" else "https://api.deepseek.com/v1",
                    "model": "gpt-4" if provider == "openai" else "deepseek-chat",
                    "timeout": 60,
                    "max_retries": 3
                }
            
            # 更新配置
            current_config["api_key"] = api_key
            if base_url:
                current_config["base_url"] = base_url
            if model:
                current_config["model"] = model
            
            return await self.set_config(
                category="ai_api_keys",
                key=provider,
                value=current_config,
                description=f"{provider.upper()} API配置",
                tenant_id=tenant_id
            )
            
        except Exception as e:
            logger.error(f"更新AI配置失败 - provider: {provider}, error: {str(e)}")
            raise
    
    async def get_all_categories(self, tenant_id: Optional[UUID] = None) -> List[str]:
        """获取所有配置类别"""
        try:
            query = select(SystemConfig.category).distinct().where(
                SystemConfig.tenant_id == tenant_id
            )
            
            result = await self.db.execute(query)
            categories = [row[0] for row in result.fetchall()]
            
            return categories
            
        except Exception as e:
            logger.error(f"获取配置类别失败: {str(e)}")
            return []
    
    async def delete_config(
        self,
        category: str,
        key: str,
        tenant_id: Optional[UUID] = None
    ) -> bool:
        """删除配置项"""
        try:
            query = select(SystemConfig).where(
                and_(
                    SystemConfig.category == category,
                    SystemConfig.key == key,
                    SystemConfig.tenant_id == tenant_id
                )
            )
            
            result = await self.db.execute(query)
            config = result.scalar_one_or_none()
            
            if config:
                await self.db.delete(config)
                await self.db.commit()
                logger.info(f"配置删除成功 - category: {category}, key: {key}")
                return True
            
            return False
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"删除配置失败 - category: {category}, key: {key}, error: {str(e)}")
            return False 