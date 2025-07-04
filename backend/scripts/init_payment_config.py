#!/usr/bin/env python3
"""
微信支付配置初始化脚本
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import AsyncSessionLocal
from app.services.config_service import SystemConfigService


async def init_payment_config():
    """初始化微信支付配置"""
    
    try:
        # 创建数据库会话
        async with AsyncSessionLocal() as db:
            config_service = SystemConfigService(db)
            
            print("🔧 开始初始化微信支付配置...")
            
            # 微信支付配置（示例配置，实际使用时需要真实的微信支付参数）
            wechat_config = {
                "app_id": "wx1234567890abcdef",           # 微信公众号/小程序AppID
                "app_secret": "your_app_secret_here",      # 微信应用密钥
                "mch_id": "1234567890",                    # 微信商户号
                "api_key": "your_wechat_api_key_here",     # 微信支付API密钥
                "cert_path": "/path/to/apiclient_cert.pem", # 微信支付证书路径
                "key_path": "/path/to/apiclient_key.pem",   # 微信支付私钥路径
                "enabled": False,                           # 默认禁用，需要配置后手动启用
                "notify_url": "https://api.lawsker.com/api/v1/finance/payment/callback",
                "sandbox": True                             # 是否使用沙箱环境
            }
            
            # 支付宝配置（预留）
            alipay_config = {
                "app_id": "your_alipay_app_id",
                "private_key": "your_alipay_private_key",
                "public_key": "alipay_public_key",
                "enabled": False,
                "sandbox": True
            }
            
            # 银联配置（预留）
            unionpay_config = {
                "merchant_id": "your_unionpay_merchant_id",
                "access_key": "your_unionpay_access_key",
                "secret_key": "your_unionpay_secret_key",
                "enabled": False,
                "sandbox": True
            }
            
            # 设置微信支付配置
            await config_service.set_config(
                category="payment_keys",
                key="wechat_pay",
                value=wechat_config,
                description="微信支付配置",
                encrypt_sensitive=True
            )
            print("✅ 微信支付配置初始化完成")
            
            # 设置支付宝配置
            await config_service.set_config(
                category="payment_keys",
                key="alipay",
                value=alipay_config,
                description="支付宝配置",
                encrypt_sensitive=True
            )
            print("✅ 支付宝配置初始化完成")
            
            # 设置银联配置
            await config_service.set_config(
                category="payment_keys",
                key="unionpay",
                value=unionpay_config,
                description="银联支付配置",
                encrypt_sensitive=True
            )
            print("✅ 银联支付配置初始化完成")
            
            # 设置分账规则配置
            commission_rules = {
                "default_rule": {
                    "platform": 0.50,      # 平台分成50%
                    "lawyer": 0.30,        # 律师分成30%
                    "sales": 0.20,         # 销售分成20%
                    "safety_margin": 0.15  # 安全边际15%
                },
                "high_amount_rule": {
                    "amount_threshold": 100000.0,  # 10万以上案件
                    "platform": 0.45,              # 平台分成降至45%
                    "lawyer": 0.35,                # 律师分成增至35%
                    "sales": 0.20,                 # 销售分成保持20%
                    "safety_margin": 0.10          # 安全边际降至10%
                },
                "instant_split_enabled": True,     # 启用即时分账
                "split_delay_seconds": 30,         # 分账延迟30秒
                "min_split_amount": 1.0,           # 最小分账金额1元
                "max_daily_withdrawal": 50000.0    # 单日最大提现金额5万元
            }
            
            await config_service.set_config(
                category="business",
                key="payment_rules",
                value=commission_rules,
                description="支付和分账规则配置",
                encrypt_sensitive=False
            )
            print("✅ 分账规则配置初始化完成")
            
            # 设置风险控制配置
            risk_config = {
                "max_daily_amount": 1000000.0,     # 单日最大交易金额100万
                "max_single_amount": 500000.0,     # 单笔最大交易金额50万
                "suspicious_amount": 100000.0,     # 可疑交易金额阈值10万
                "require_insurance_amount": 100000.0,  # 强制投保金额阈值10万
                "auto_freeze_suspicious": True,     # 自动冻结可疑交易
                "manual_review_threshold": 50000.0, # 人工审核阈值5万
                "blacklist_check_enabled": True,    # 启用黑名单检查
                "velocity_check_enabled": True,     # 启用交易频率检查
                "max_failed_attempts": 3,           # 最大失败尝试次数
                "lockout_duration_minutes": 30     # 锁定时长30分钟
            }
            
            await config_service.set_config(
                category="business",
                key="risk_control",
                value=risk_config,
                description="风险控制配置",
                encrypt_sensitive=False
            )
            print("✅ 风险控制配置初始化完成")
            
            # 设置通知配置
            notification_config = {
                "payment_success": {
                    "enabled": True,
                    "channels": ["email", "sms", "wechat"],
                    "template": "payment_success_template"
                },
                "commission_received": {
                    "enabled": True,
                    "channels": ["email", "wechat"],
                    "template": "commission_received_template"
                },
                "withdrawal_processed": {
                    "enabled": True,
                    "channels": ["email", "sms"],
                    "template": "withdrawal_processed_template"
                },
                "risk_alert": {
                    "enabled": True,
                    "channels": ["email", "admin_wechat"],
                    "template": "risk_alert_template"
                }
            }
            
            await config_service.set_config(
                category="notification",
                key="payment_notifications",
                value=notification_config,
                description="支付相关通知配置",
                encrypt_sensitive=False
            )
            print("✅ 通知配置初始化完成")
            
            print("\n🎉 微信支付系统配置初始化完成！")
            print("\n📋 后续配置步骤：")
            print("1. 获取真实的微信支付商户号和API密钥")
            print("2. 上传微信支付证书文件")
            print("3. 配置支付回调域名白名单")
            print("4. 在管理后台启用支付功能")
            print("5. 进行支付功能测试")
            
            return True
            
    except Exception as e:
        print(f"❌ 微信支付配置初始化失败: {str(e)}")
        return False


async def verify_payment_config():
    """验证支付配置"""
    
    try:
        async with AsyncSessionLocal() as db:
            config_service = SystemConfigService(db)
            
            print("\n🔍 验证支付配置...")
            
            # 验证微信支付配置
            wechat_config = await config_service.get_config("payment_keys", "wechat_pay")
            if wechat_config:
                print("✅ 微信支付配置存在")
                print(f"   - 应用ID: {wechat_config.get('app_id', 'N/A')}")
                print(f"   - 商户号: {wechat_config.get('mch_id', 'N/A')}")
                print(f"   - 启用状态: {wechat_config.get('enabled', False)}")
                print(f"   - 沙箱模式: {wechat_config.get('sandbox', True)}")
            else:
                print("❌ 微信支付配置不存在")
            
            # 验证分账规则配置
            rules_config = await config_service.get_config("business", "payment_rules")
            if rules_config:
                print("✅ 分账规则配置存在")
                default_rule = rules_config.get('default_rule', {})
                print(f"   - 平台分成: {default_rule.get('platform', 0)*100}%")
                print(f"   - 律师分成: {default_rule.get('lawyer', 0)*100}%")
                print(f"   - 销售分成: {default_rule.get('sales', 0)*100}%")
                print(f"   - 即时分账: {rules_config.get('instant_split_enabled', False)}")
            else:
                print("❌ 分账规则配置不存在")
            
            # 验证风险控制配置
            risk_config = await config_service.get_config("business", "risk_control")
            if risk_config:
                print("✅ 风险控制配置存在")
                print(f"   - 单日最大金额: ¥{risk_config.get('max_daily_amount', 0):,.2f}")
                print(f"   - 单笔最大金额: ¥{risk_config.get('max_single_amount', 0):,.2f}")
                print(f"   - 强制投保阈值: ¥{risk_config.get('require_insurance_amount', 0):,.2f}")
            else:
                print("❌ 风险控制配置不存在")
            
            return True
            
    except Exception as e:
        print(f"❌ 验证支付配置失败: {str(e)}")
        return False


async def main():
    """主函数"""
    print("🚀 Lawsker 微信支付系统配置初始化工具")
    print("=" * 50)
    
    # 初始化配置
    init_success = await init_payment_config()
    
    if init_success:
        # 验证配置
        await verify_payment_config()
        
        print("\n✨ 微信支付系统配置初始化成功！")
        print("\n🔑 重要提醒：")
        print("- 配置中的敏感信息已加密存储")
        print("- 请妥善保管加密密钥")
        print("- 生产环境请使用真实的支付参数")
        print("- 定期检查和更新支付配置")
        
    else:
        print("\n💥 微信支付系统配置初始化失败！")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 