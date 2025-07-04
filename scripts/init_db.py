#!/usr/bin/env python3
"""
Lawsker数据库初始化脚本
创建数据库表和初始数据
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import create_tables, AsyncSessionLocal, engine
from app.core.config import settings
from app.models.tenant import Tenant, TenantMode, TenantStatus, SystemConfig
from app.models.user import User, Role, UserRole, Profile, UserStatus
from sqlalchemy import text
import structlog

logger = structlog.get_logger()


async def create_default_tenant():
    """创建默认租户"""
    async with AsyncSessionLocal() as session:
        try:
            # 检查是否已存在默认租户
            result = await session.execute(
                text("SELECT id FROM tenants WHERE tenant_code = 'default'")
            )
            if result.first():
                logger.info("默认租户已存在，跳过创建")
                return

            # 创建默认租户
            default_tenant = Tenant(
                name="Lawsker默认租户",
                tenant_code="default",
                mode=TenantMode.SAAS,
                status=TenantStatus.ACTIVE,
                feature_flags={
                    "ai_enabled": True,
                    "web3_enabled": False,
                    "multi_language": False
                },
                system_config={
                    "commission_rates": {
                        "platform": 0.50,
                        "lawyer": 0.30,
                        "sales": 0.20,
                        "safety_margin": 0.15
                    }
                }
            )
            
            session.add(default_tenant)
            await session.commit()
            await session.refresh(default_tenant)
            
            logger.info("✅ 默认租户创建成功", tenant_id=str(default_tenant.id))
            return default_tenant.id
            
        except Exception as e:
            await session.rollback()
            logger.error("❌ 创建默认租户失败", error=str(e))
            raise


async def create_default_roles(tenant_id):
    """创建默认角色"""
    async with AsyncSessionLocal() as session:
        try:
            roles_data = [
                {
                    "name": "admin",
                    "description": "系统管理员",
                    "permissions": {
                        "can_manage_users": True,
                        "can_manage_system": True,
                        "can_view_all_data": True,
                        "can_modify_config": True
                    }
                },
                {
                    "name": "lawyer",
                    "description": "执业律师",
                    "permissions": {
                        "can_view_cases": True,
                        "can_handle_cases": True,
                        "can_generate_documents": True,
                        "can_view_commission": True
                    }
                },
                {
                    "name": "sales",
                    "description": "业务销售",
                    "permissions": {
                        "can_upload_cases": True,
                        "can_manage_clients": True,
                        "can_view_commission": True,
                        "can_view_statistics": True
                    }
                },
                {
                    "name": "institution",
                    "description": "机构管理员",
                    "permissions": {
                        "can_view_dashboard": True,
                        "can_manage_insurance": True,
                        "can_view_settlements": True,
                        "can_export_reports": True
                    }
                }
            ]
            
            created_roles = []
            for role_data in roles_data:
                # 检查角色是否已存在
                result = await session.execute(
                    text("SELECT id FROM roles WHERE tenant_id = :tenant_id AND name = :name"),
                    {"tenant_id": tenant_id, "name": role_data["name"]}
                )
                if result.first():
                    logger.info(f"角色 {role_data['name']} 已存在，跳过创建")
                    continue
                
                role = Role(
                    tenant_id=tenant_id,
                    name=role_data["name"],
                    description=role_data["description"],
                    permissions=role_data["permissions"]
                )
                session.add(role)
                created_roles.append(role)
            
            if created_roles:
                await session.commit()
                for role in created_roles:
                    await session.refresh(role)
                logger.info(f"✅ 成功创建 {len(created_roles)} 个角色")
            
        except Exception as e:
            await session.rollback()
            logger.error("❌ 创建默认角色失败", error=str(e))
            raise


async def create_default_configs(tenant_id):
    """创建默认系统配置"""
    async with AsyncSessionLocal() as session:
        try:
            configs_data = [
                {
                    "category": "commission",
                    "key": "platform_rate",
                    "value": {"rate": 0.50},
                    "description": "平台分成比例"
                },
                {
                    "category": "commission", 
                    "key": "lawyer_rate",
                    "value": {"rate": 0.30},
                    "description": "律师分成比例"
                },
                {
                    "category": "commission",
                    "key": "sales_rate", 
                    "value": {"rate": 0.20},
                    "description": "销售分成比例"
                },
                {
                    "category": "risk",
                    "key": "insurance_threshold",
                    "value": {"amount": 100000.0},
                    "description": "强制投保金额阈值"
                },
                {
                    "category": "risk",
                    "key": "high_risk_threshold",
                    "value": {"amount": 500000.0},
                    "description": "高风险案件金额阈值"
                }
            ]
            
            created_configs = []
            for config_data in configs_data:
                # 检查配置是否已存在
                result = await session.execute(
                    text("SELECT id FROM system_configs WHERE tenant_id = :tenant_id AND category = :category AND key = :key"),
                    {"tenant_id": tenant_id, "category": config_data["category"], "key": config_data["key"]}
                )
                if result.first():
                    continue
                
                config = SystemConfig(
                    tenant_id=tenant_id,
                    category=config_data["category"],
                    key=config_data["key"],
                    value=config_data["value"],
                    description=config_data["description"]
                )
                session.add(config)
                created_configs.append(config)
            
            if created_configs:
                await session.commit()
                logger.info(f"✅ 成功创建 {len(created_configs)} 个系统配置")
            
        except Exception as e:
            await session.rollback()
            logger.error("❌ 创建默认配置失败", error=str(e))
            raise


async def check_database_connection():
    """检查数据库连接"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ 数据库连接成功")
        return True
    except Exception as e:
        logger.error("❌ 数据库连接失败", error=str(e))
        return False


async def init_database():
    """初始化数据库"""
    logger.info("🚀 开始初始化Lawsker数据库...")
    
    # 检查数据库连接
    if not await check_database_connection():
        logger.error("数据库连接失败，请检查配置")
        return False
    
    try:
        # 创建数据库表
        logger.info("📋 创建数据库表...")
        await create_tables()
        
        # 创建默认租户
        logger.info("🏢 创建默认租户...")
        tenant_id = await create_default_tenant()
        
        # 创建默认角色
        logger.info("👥 创建默认角色...")
        await create_default_roles(tenant_id)
        
        # 创建默认配置
        logger.info("⚙️ 创建默认配置...")
        await create_default_configs(tenant_id)
        
        logger.info("🎉 数据库初始化完成！")
        return True
        
    except Exception as e:
        logger.error("❌ 数据库初始化失败", error=str(e))
        return False


if __name__ == "__main__":
    asyncio.run(init_database()) 