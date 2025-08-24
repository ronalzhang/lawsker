#!/usr/bin/env python3
"""
配置管理系统演示脚本
展示配置管理系统的主要功能
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from configuration_manager import ConfigurationManager
from secure_config_manager import SecureConfigManager
from config_templates import ConfigTemplates
from config_validator import ConfigValidator


def main():
    """主演示函数"""
    print("🚀 配置管理系统演示")
    print("=" * 50)
    
    # 创建临时目录
    temp_dir = Path(tempfile.mkdtemp(prefix="config_demo_"))
    print(f"📁 演示目录: {temp_dir}")
    
    try:
        # 1. 初始化组件
        print("\n1️⃣ 初始化配置管理组件...")
        
        config_manager = ConfigurationManager(
            config_dir=str(temp_dir / "config"),
            templates_dir=str(temp_dir / "templates"),
            backup_dir=str(temp_dir / "backups")
        )
        
        secure_manager = SecureConfigManager(
            vault_path=str(temp_dir / "vault"),
            audit_log_path=str(temp_dir / "audit.log")
        )
        
        templates = ConfigTemplates(config_manager)
        validator = ConfigValidator()
        
        print("✅ 组件初始化完成")
        
        # 2. 创建配置模板
        print("\n2️⃣ 创建配置模板...")
        
        if templates.create_all_templates():
            template_count = len(list(config_manager.templates_dir.glob("*.j2")))
            print(f"✅ 成功创建 {template_count} 个配置模板")
        else:
            print("❌ 模板创建失败")
            return
        
        # 3. 密钥管理演示
        print("\n3️⃣ 密钥管理演示...")
        
        # 存储密钥
        secrets = [
            ("database_password", "SecureDBPassword123!", "password"),
            ("api_key", "sk-1234567890abcdef", "api_key"),
            ("jwt_secret", "super-secret-jwt-key", "password")
        ]
        
        for name, value, secret_type in secrets:
            if secure_manager.store_secret(name, value, secret_type):
                print(f"✅ 存储密钥: {name}")
            else:
                print(f"❌ 存储密钥失败: {name}")
        
        # 检索密钥
        print("\n🔍 检索密钥:")
        for name, _, _ in secrets:
            retrieved = secure_manager.retrieve_secret(name)
            if retrieved:
                print(f"✅ {name}: {retrieved[:10]}...")
            else:
                print(f"❌ 检索失败: {name}")
        
        # 4. 配置文件生成演示
        print("\n4️⃣ 配置文件生成演示...")
        
        # 生成Nginx配置
        nginx_vars = {
            "app_name": "lawsker-demo",
            "domain": "demo.lawsker.com",
            "ssl_enabled": True,
            "ssl_cert_path": "/etc/ssl/certs/demo.crt",
            "ssl_key_path": "/etc/ssl/private/demo.key",
            "backend_url": "http://127.0.0.1:8000",
            "static_path": "/opt/lawsker/static",
            "frontend_path": "/opt/lawsker/frontend",
            "log_path": "/var/log/nginx"
        }
        
        nginx_output = temp_dir / "nginx_demo.conf"
        if config_manager.generate_config_file("nginx_site", str(nginx_output), nginx_vars):
            print(f"✅ 生成Nginx配置: {nginx_output.name}")
            
            # 显示配置文件片段
            with open(nginx_output, 'r') as f:
                lines = f.readlines()[:10]
                print("📄 配置文件预览:")
                for line in lines:
                    print(f"   {line.rstrip()}")
                print("   ...")
        else:
            print("❌ Nginx配置生成失败")
        
        # 5. 配置验证演示
        print("\n5️⃣ 配置验证演示...")
        
        # 验证环境变量
        env_vars = {
            "SECRET_KEY": "this-is-a-very-long-secret-key-for-demo",
            "DATABASE_URL": "postgresql://user:pass@localhost/demo_db",
            "REDIS_URL": "redis://localhost:6379/0"
        }
        
        env_result = validator.validate_environment_variables(env_vars)
        if env_result.is_valid:
            print("✅ 环境变量验证通过")
        else:
            print(f"❌ 环境变量验证失败: {env_result.errors}")
        
        if env_result.warnings:
            print("⚠️  警告:")
            for warning in env_result.warnings:
                print(f"   - {warning}")
        
        # 6. 安全合规检查演示
        print("\n6️⃣ 安全合规检查演示...")
        
        compliance_report = secure_manager.run_security_compliance_check()
        print(f"🛡️  合规状态: {compliance_report['overall_status']}")
        
        for check in compliance_report['checks']:
            status_icon = "✅" if check['status'] == "PASS" else "⚠️" if check['status'] == "WARN" else "❌"
            print(f"   {status_icon} {check['name']}: {check['status']}")
        
        # 7. 配置变更检测演示
        print("\n7️⃣ 配置变更检测演示...")
        
        config_files = [str(nginx_output)]
        changes = config_manager.detect_config_changes(config_files)
        
        print("📊 配置变更状态:")
        for path, change_info in changes.items():
            status_icon = "✅" if change_info['status'] == "unchanged" else "🔄" if change_info['status'] == "modified" else "🆕"
            print(f"   {status_icon} {Path(path).name}: {change_info['status']}")
        
        print("\n🎉 演示完成！配置管理系统运行正常。")
        
        # 显示统计信息
        print("\n📊 统计信息:")
        print(f"   - 配置模板: {len(list(config_manager.templates_dir.glob('*.j2')))} 个")
        print(f"   - 存储密钥: {len(secure_manager.secrets_metadata)} 个")
        print(f"   - 生成配置: 1 个")
        print(f"   - 审计记录: {len(secure_manager.access_records)} 条")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理临时目录
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"\n🧹 清理演示目录: {temp_dir}")


if __name__ == "__main__":
    main()