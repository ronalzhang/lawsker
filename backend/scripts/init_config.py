#!/usr/bin/env python3
"""
配置初始化脚本
"""

import os
import sys
import re
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.models.tenant import SystemConfig
from cryptography.fernet import Fernet
import base64
import json


class SyncConfigService:
    """同步配置管理服务（用于初始化脚本）"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # 初始化加密
        encryption_key = os.getenv("CONFIG_ENCRYPTION_KEY")
        if not encryption_key:
            key = Fernet.generate_key()
            encryption_key = base64.urlsafe_b64encode(key).decode()
            print(f"生成新的配置加密密钥: {encryption_key[:10]}...")
        
        self.encryption_key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
        self.fernet = Fernet(base64.urlsafe_b64decode(self.encryption_key))
        
        # 敏感配置类型
        self.sensitive_categories = {
            "ai_api_keys", "payment_keys", "third_party_apis", 
            "security_keys", "database_credentials"
        }
    
    def encrypt_value(self, value: str) -> str:
        """加密配置值"""
        if not value:
            return value
        return self.fernet.encrypt(value.encode()).decode()
    
    def update_config(self, category: str, config_data: dict, description: str = ""):
        """更新配置"""
        try:
            # 检查是否是敏感配置需要加密
            final_value = config_data
            if category in self.sensitive_categories:
                encrypted_value: Dict[str, Any] = {"encrypted": True}
                for k, v in config_data.items():
                    if isinstance(v, str) and v:
                        encrypted_value[k] = self.encrypt_value(v)
                    else:
                        encrypted_value[k] = v
                final_value = encrypted_value
            
            # 查找是否已存在
            existing = self.db.query(SystemConfig).filter(
                SystemConfig.category == category,
                SystemConfig.key == "default",
                SystemConfig.tenant_id.is_(None)
            ).first()
            
            if existing:
                existing.value = final_value  # type: ignore
                existing.description = description  # type: ignore
            else:
                config = SystemConfig(
                    tenant_id=None,
                    category=category,
                    key="default",
                    value=final_value,
                    description=description,
                    is_editable=True
                )
                self.db.add(config)
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            print(f"❌ 更新配置失败 - {category}: {e}")
            raise


def read_api_keys_from_file():
    """从API-KEY文件读取API密钥"""
    api_key_file = project_root.parent / "API-KEY"
    api_keys = {}
    
    if api_key_file.exists():
        try:
            content = api_key_file.read_text(encoding='utf-8')
            print(f"✅ 成功读取API-KEY文件")
            
            # 解析OpenAI API Key
            openai_match = re.search(r'OPENAI API-KEY:\s*(sk-[a-zA-Z0-9\-_]+)', content, re.MULTILINE)
            if openai_match:
                api_keys['openai'] = openai_match.group(1)
                print(f"✅ OpenAI API Key已获取: {api_keys['openai'][:20]}...")
            
            # 解析Deepseek API Key  
            deepseek_match = re.search(r'Deepseek API-KEY:\s*(sk-[a-zA-Z0-9\-_]+)', content, re.MULTILINE)
            if deepseek_match:
                api_keys['deepseek'] = deepseek_match.group(1)
                print(f"✅ Deepseek API Key已获取: {api_keys['deepseek'][:20]}...")
                
        except Exception as e:
            print(f"❌ 读取API-KEY文件时出错: {e}")
            
    else:
        print(f"⚠️  API-KEY文件不存在: {api_key_file}")
    
    return api_keys


def init_ai_config(config_service: SyncConfigService, api_keys: dict):
    """初始化AI服务配置"""
    print("\n🤖 初始化AI服务配置...")
    
    ai_config = {
        "openai": {
            "api_key": api_keys.get('openai', ''),
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4",
            "max_tokens": 4000,
            "temperature": 0.7,
            "timeout": 60,
            "enabled": bool(api_keys.get('openai'))
        },
        "deepseek": {
            "api_key": api_keys.get('deepseek', ''),
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
            "max_tokens": 4000,
            "temperature": 0.7,
            "timeout": 60,
            "enabled": bool(api_keys.get('deepseek'))
        },
        "default_provider": "openai" if api_keys.get('openai') else "deepseek",
        "fallback_enabled": True,
        "retry_attempts": 3
    }
    
    config_service.update_config("ai_api_keys", ai_config, "AI服务API密钥配置")
    print("✅ AI服务配置已完成")


def init_business_config(config_service: SyncConfigService):
    """初始化业务配置"""
    print("\n💼 初始化业务配置...")
    
    # 分成比例配置
    commission_config = {
        "platform": 0.50,
        "lawyer": 0.30,
        "sales": 0.20,
        "safety_margin": 0.15
    }
    
    # 风险控制阈值
    risk_config = {
        "insurance_threshold": 100000.0,
        "high_risk_threshold": 500000.0,
        "auto_approve_threshold": 10000.0,
        "review_required_threshold": 50000.0
    }
    
    # 业务规则配置
    business_rules = {
        "max_cases_per_lawyer": 50,
        "case_timeout_days": 90,
        "auto_assignment_enabled": True,
        "independent_letter_price": 30.0,
        "urgent_processing_fee": 10.0,
        "lawyer_letter_base_price": 30.0,
        "ai_document_generation_fee": 10.0,
        "platform_service_fee_rate": 0.05
    }
    
    business_config = {
        "commission": commission_config,
        "risk_control": risk_config,
        "rules": business_rules
    }
    
    config_service.update_config("business", business_config, "业务规则和分成配置")
    print("✅ 业务配置已完成")


def init_third_party_config(config_service: SyncConfigService):
    """初始化第三方服务配置（占位符）"""
    print("\n🔌 初始化第三方服务配置...")
    
    third_party_config = {
        "email": {
            "smtp_server": "",
            "smtp_port": 587,
            "username": "",
            "password": "",
            "enabled": False
        },
        "sms": {
            "provider": "aliyun",
            "access_key": "",
            "secret_key": "",
            "enabled": False
        },
        "express": {
            "provider": "sf",
            "api_key": "",
            "secret_key": "",
            "enabled": False
        },
        "storage": {
            "provider": "minio",
            "endpoint": "",
            "access_key": "",
            "secret_key": "",
            "bucket": "lawsker-documents",
            "enabled": False
        }
    }
    
    config_service.update_config("third_party_apis", third_party_config, "第三方服务API配置")
    print("✅ 第三方服务配置已完成")


def init_payment_config(config_service: SyncConfigService):
    """初始化支付配置（占位符）"""
    print("\n💳 初始化支付配置...")
    
    payment_config = {
        "wechat": {
            "app_id": "",
            "mch_id": "",
            "api_key": "",
            "api_secret": "",
            "cert_path": "",
            "enabled": False
        },
        "alipay": {
            "app_id": "",
            "private_key": "",
            "public_key": "",
            "enabled": False
        },
        "bank": {
            "bank_code": "",
            "merchant_id": "",
            "api_key": "",
            "enabled": False
        }
    }
    
    config_service.update_config("payment_keys", payment_config, "支付服务密钥配置")
    print("✅ 支付配置已完成")


def verify_config(config_service: SyncConfigService):
    """验证配置完整性"""
    print("\n🔍 验证配置完整性...")
    
    categories = ["ai_api_keys", "business", "third_party_apis", "payment_keys"]
    
    for category in categories:
        try:
            config = config_service.db.query(SystemConfig).filter(
                SystemConfig.category == category,
                SystemConfig.key == "default",
                SystemConfig.tenant_id.is_(None)
            ).first()
            
            if config and config.value:  # type: ignore
                print(f"✅ {category} 配置验证通过")
            else:
                print(f"❌ {category} 配置为空")
        except Exception as e:
            print(f"❌ {category} 配置验证失败: {e}")


def main():
    """主函数"""
    print("🚀 开始初始化Lawsker配置系统...")
    
    # 读取API密钥
    api_keys = read_api_keys_from_file()
    
    if not api_keys:
        print("⚠️  未找到任何API密钥，将使用空配置")
    
    # 创建同步数据库连接
    sync_database_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    config_service = SyncConfigService(db)
    
    try:
        # 初始化各类配置
        init_ai_config(config_service, api_keys)
        init_business_config(config_service)
        init_third_party_config(config_service)
        init_payment_config(config_service)
        
        # 验证配置
        verify_config(config_service)
        
        print("\n🎉 配置初始化完成！")
        print("\n📝 配置摘要:")
        print(f"   - OpenAI API: {'✅ 已配置' if api_keys.get('openai') else '❌ 未配置'}")
        print(f"   - Deepseek API: {'✅ 已配置' if api_keys.get('deepseek') else '❌ 未配置'}")
        print(f"   - 业务配置: ✅ 已完成")
        print(f"   - 第三方服务: ⏳ 待配置")
        print(f"   - 支付服务: ⏳ 待配置")
        
    except Exception as e:
        print(f"❌ 配置初始化失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main() 