#!/usr/bin/env python3
"""
配置管理系统集成测试
测试ConfigurationManager、SecureConfigManager、ConfigTemplates和ConfigValidator的集成功能
"""

import os
import sys
import json
import tempfile
import shutil
import logging
from pathlib import Path
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from configuration_manager import ConfigurationManager, EnvironmentConfig
    from secure_config_manager import SecureConfigManager
    from config_validator import ConfigValidator
    
    # 直接导入ConfigTemplates类而不是模块
    from config_templates import ConfigTemplates
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required dependencies are installed:")
    print("pip install cryptography jinja2 pyyaml python-dateutil")
    sys.exit(1)


class ConfigManagementIntegrationTest:
    """配置管理系统集成测试类"""
    
    def __init__(self):
        self.test_dir = None
        self.config_manager = None
        self.secure_manager = None
        self.templates = None
        self.validator = None
        self.logger = logging.getLogger(__name__)
    
    def setup_test_environment(self):
        """设置测试环境"""
        print("Setting up test environment...")
        
        # 创建临时测试目录
        self.test_dir = Path(tempfile.mkdtemp(prefix="config_test_"))
        print(f"Test directory: {self.test_dir}")
        
        # 初始化组件
        config_dir = self.test_dir / "config"
        templates_dir = self.test_dir / "templates"
        vault_dir = self.test_dir / "vault"
        backup_dir = self.test_dir / "backups"
        audit_log = self.test_dir / "audit.log"
        
        self.config_manager = ConfigurationManager(
            config_dir=str(config_dir),
            templates_dir=str(templates_dir),
            backup_dir=str(backup_dir)
        )
        
        self.secure_manager = SecureConfigManager(
            vault_path=str(vault_dir),
            audit_log_path=str(audit_log)
        )
        
        self.templates = ConfigTemplates(self.config_manager)
        self.validator = ConfigValidator()
        
        print("✓ Test environment setup completed")
    
    def cleanup_test_environment(self):
        """清理测试环境"""
        if self.test_dir and self.test_dir.exists():
            shutil.rmtree(self.test_dir)
            print("✓ Test environment cleaned up")
    
    def test_template_creation(self) -> bool:
        """测试模板创建"""
        print("\n--- Testing Template Creation ---")
        
        try:
            # 创建所有预定义模板
            success = self.templates.create_all_templates()
            
            if success:
                print("✓ All templates created successfully")
                
                # 验证模板文件存在
                template_files = list(self.config_manager.templates_dir.glob("*.j2"))
                metadata_files = list(self.config_manager.templates_dir.glob("*.meta.json"))
                
                print(f"✓ Created {len(template_files)} template files")
                print(f"✓ Created {len(metadata_files)} metadata files")
                
                return True
            else:
                print("✗ Failed to create templates")
                return False
                
        except Exception as e:
            print(f"✗ Template creation test failed: {e}")
            return False
    
    def test_secret_management(self) -> bool:
        """测试密钥管理"""
        print("\n--- Testing Secret Management ---")
        
        try:
            # 存储测试密钥
            secrets_to_test = [
                ("database_password", "MySecurePassword123!", "password", "confidential"),
                ("api_key", "sk-1234567890abcdef", "api_key", "internal"),
                ("jwt_secret", "super-secret-jwt-key-for-testing", "password", "internal")
            ]
            
            for name, value, secret_type, access_level in secrets_to_test:
                success = self.secure_manager.store_secret(
                    name=name,
                    value=value,
                    secret_type=secret_type,
                    access_level=access_level,
                    expires_days=90,
                    rotation_interval_days=30
                )
                
                if success:
                    print(f"✓ Stored secret: {name}")
                else:
                    print(f"✗ Failed to store secret: {name}")
                    return False
            
            # 测试密钥检索
            for name, expected_value, _, _ in secrets_to_test:
                retrieved_value = self.secure_manager.retrieve_secret(name)
                if retrieved_value == expected_value:
                    print(f"✓ Retrieved secret: {name}")
                else:
                    print(f"✗ Failed to retrieve secret: {name}")
                    return False
            
            # 测试密钥轮换
            if self.secure_manager.rotate_secret("api_key"):
                print("✓ Secret rotation successful")
                
                # 验证轮换后的值不同
                new_value = self.secure_manager.retrieve_secret("api_key")
                if new_value != "sk-1234567890abcdef":
                    print("✓ Secret value changed after rotation")
                else:
                    print("✗ Secret value unchanged after rotation")
                    return False
            else:
                print("✗ Secret rotation failed")
                return False
            
            return True
            
        except Exception as e:
            print(f"✗ Secret management test failed: {e}")
            return False
    
    def test_config_generation(self) -> bool:
        """测试配置文件生成"""
        print("\n--- Testing Configuration Generation ---")
        
        try:
            # 创建测试变量
            variables = {
                "app_name": "lawsker-test",
                "domain": "test.lawsker.com",
                "ssl_enabled": True,
                "ssl_cert_path": "/etc/ssl/certs/test.crt",
                "ssl_key_path": "/etc/ssl/private/test.key",
                "backend_url": "http://127.0.0.1:8000",
                "static_path": "/opt/lawsker/static",
                "frontend_path": "/opt/lawsker/frontend",
                "log_path": "/var/log/nginx"
            }
            
            # 生成Nginx配置
            output_path = self.test_dir / "nginx_test.conf"
            success = self.config_manager.generate_config_file(
                template_name="nginx_site",
                output_path=str(output_path),
                variables=variables
            )
            
            if success and output_path.exists():
                print("✓ Nginx configuration generated successfully")
                
                # 验证生成的配置内容
                with open(output_path, 'r') as f:
                    content = f.read()
                
                if "test.lawsker.com" in content and "ssl_certificate" in content:
                    print("✓ Generated configuration contains expected content")
                else:
                    print("✗ Generated configuration missing expected content")
                    return False
            else:
                print("✗ Failed to generate Nginx configuration")
                return False
            
            # 生成应用配置
            app_variables = {
                "app_name": "lawsker-test",
                "environment": "test",
                "secret_key": "${SECRET_KEY}",
                "database_url": "${DATABASE_URL}",
                "redis_url": "${REDIS_URL}"
            }
            
            app_output_path = self.test_dir / "app_test.conf"
            success = self.config_manager.generate_config_file(
                template_name="app_config",
                output_path=str(app_output_path),
                variables=app_variables
            )
            
            if success and app_output_path.exists():
                print("✓ Application configuration generated successfully")
            else:
                print("✗ Failed to generate application configuration")
                return False
            
            return True
            
        except Exception as e:
            print(f"✗ Configuration generation test failed: {e}")
            return False
    
    def test_config_validation(self) -> bool:
        """测试配置验证"""
        print("\n--- Testing Configuration Validation ---")
        
        try:
            # 创建测试JSON配置
            test_config = {
                "app_name": "lawsker-test",
                "secret_key": "this-is-a-very-long-secret-key-for-testing-purposes",
                "log_level": "INFO",
                "cors_origins": ["https://test.lawsker.com", "https://admin.test.lawsker.com"]
            }
            
            json_file = self.test_dir / "test_config.json"
            with open(json_file, 'w') as f:
                json.dump(test_config, f, indent=2)
            
            # 验证JSON语法
            json_result = self.validator.validate_json_syntax(str(json_file))
            if json_result.is_valid:
                print("✓ JSON syntax validation passed")
            else:
                print(f"✗ JSON syntax validation failed: {json_result.errors}")
                return False
            
            # 验证环境变量
            env_vars = {
                "SECRET_KEY": "this-is-a-very-long-secret-key-for-testing",
                "DATABASE_URL": "postgresql://user:pass@localhost/testdb",
                "REDIS_URL": "redis://localhost:6379/0",
                "LOG_LEVEL": "INFO"
            }
            
            env_result = self.validator.validate_environment_variables(env_vars)
            if env_result.is_valid:
                print("✓ Environment variables validation passed")
                if env_result.warnings:
                    for warning in env_result.warnings:
                        print(f"  Warning: {warning}")
            else:
                print(f"✗ Environment variables validation failed: {env_result.errors}")
                return False
            
            return True
            
        except Exception as e:
            print(f"✗ Configuration validation test failed: {e}")
            return False
    
    def test_security_compliance(self) -> bool:
        """测试安全合规检查"""
        print("\n--- Testing Security Compliance ---")
        
        try:
            # 运行安全合规检查
            compliance_report = self.secure_manager.run_security_compliance_check()
            
            print(f"Compliance Status: {compliance_report['overall_status']}")
            
            # 显示检查结果
            for check in compliance_report['checks']:
                status_symbol = "✓" if check['status'] == "PASS" else "⚠" if check['status'] == "WARN" else "✗"
                print(f"  {status_symbol} {check['name']}: {check['status']}")
            
            # 检查过期密钥
            expiring_secrets = self.secure_manager.check_expiring_secrets(30)
            print(f"✓ Found {len(expiring_secrets)} secrets expiring in 30 days")
            
            # 检查需要轮换的密钥
            rotation_needed = self.secure_manager.check_rotation_needed()
            print(f"✓ Found {len(rotation_needed)} secrets needing rotation")
            
            return compliance_report['overall_status'] in ['PASS', 'WARN']
            
        except Exception as e:
            print(f"✗ Security compliance test failed: {e}")
            return False
    
    def test_environment_deployment(self) -> bool:
        """测试环境部署"""
        print("\n--- Testing Environment Deployment ---")
        
        try:
            # 创建测试环境配置
            env_config = EnvironmentConfig(
                name="test",
                variables={
                    "app_name": "lawsker-test",
                    "domain": "test.lawsker.com",
                    "backend_url": "http://127.0.0.1:8000",
                    "log_level": "INFO"
                },
                encrypted_variables={},
                config_files=[
                    str(self.test_dir / "nginx_test.conf"),
                    str(self.test_dir / "app_test.conf")
                ],
                validation_rules={
                    "app_name": {"required": True, "type": "str"},
                    "domain": {"required": True, "pattern": r"^[a-zA-Z0-9.-]+$"},
                    "log_level": {"required": True, "type": "str"}
                }
            )
            
            # 验证环境变量
            is_valid, errors = self.config_manager.validate_environment_variables(env_config)
            if is_valid:
                print("✓ Environment variables validation passed")
            else:
                print(f"✗ Environment variables validation failed: {errors}")
                return False
            
            # 部署配置文件
            success = self.config_manager.deploy_config_files(env_config)
            if success:
                print("✓ Environment deployment successful")
            else:
                print("✗ Environment deployment failed")
                return False
            
            return True
            
        except Exception as e:
            print(f"✗ Environment deployment test failed: {e}")
            return False
    
    def test_change_detection(self) -> bool:
        """测试变更检测"""
        print("\n--- Testing Change Detection ---")
        
        try:
            # 创建测试配置文件
            test_files = [
                self.test_dir / "nginx_test.conf",
                self.test_dir / "app_test.conf"
            ]
            
            # 检测变更
            changes = self.config_manager.detect_config_changes([str(f) for f in test_files])
            
            print(f"✓ Detected changes for {len(changes)} files")
            for path, change_info in changes.items():
                print(f"  {Path(path).name}: {change_info['status']}")
            
            return True
            
        except Exception as e:
            print(f"✗ Change detection test failed: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("=" * 60)
        print("Configuration Management System Integration Test")
        print("=" * 60)
        
        try:
            self.setup_test_environment()
            
            tests = [
                ("Template Creation", self.test_template_creation),
                ("Secret Management", self.test_secret_management),
                ("Configuration Generation", self.test_config_generation),
                ("Configuration Validation", self.test_config_validation),
                ("Security Compliance", self.test_security_compliance),
                ("Environment Deployment", self.test_environment_deployment),
                ("Change Detection", self.test_change_detection)
            ]
            
            passed_tests = 0
            total_tests = len(tests)
            
            for test_name, test_func in tests:
                try:
                    if test_func():
                        passed_tests += 1
                        print(f"✓ {test_name} - PASSED")
                    else:
                        print(f"✗ {test_name} - FAILED")
                except Exception as e:
                    print(f"✗ {test_name} - ERROR: {e}")
            
            print("\n" + "=" * 60)
            print(f"Test Results: {passed_tests}/{total_tests} tests passed")
            print("=" * 60)
            
            success = passed_tests == total_tests
            if success:
                print("🎉 All tests passed! Configuration management system is working correctly.")
            else:
                print("❌ Some tests failed. Please check the implementation.")
            
            return success
            
        except Exception as e:
            print(f"Test execution failed: {e}")
            return False
        finally:
            self.cleanup_test_environment()


def main():
    """主函数"""
    # 设置日志
    logging.basicConfig(
        level=logging.WARNING,  # 减少日志输出以保持测试输出清晰
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行集成测试
    test_runner = ConfigManagementIntegrationTest()
    success = test_runner.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()