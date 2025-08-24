#!/usr/bin/env python3
"""
配置管理CLI工具
提供命令行接口来管理配置模板、环境变量、密钥存储等功能
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from configuration_manager import ConfigurationManager, EnvironmentConfig
from secure_config_manager import SecureConfigManager
from config_templates import ConfigTemplates


class ConfigManagementCLI:
    """配置管理CLI类"""
    
    def __init__(self):
        self.config_manager = ConfigurationManager()
        self.secure_manager = SecureConfigManager()
        self.templates = ConfigTemplates(self.config_manager)
        self.logger = logging.getLogger(__name__)
    
    def setup_templates(self) -> bool:
        """设置配置模板"""
        print("Setting up configuration templates...")
        
        if self.templates.create_all_templates():
            print("✓ All configuration templates created successfully")
            return True
        else:
            print("✗ Some templates failed to create")
            return False
    
    def create_environment(self, env_name: str, config_file: str) -> bool:
        """创建环境配置"""
        try:
            print(f"Creating environment configuration: {env_name}")
            
            # 读取配置文件
            with open(config_file, 'r') as f:
                if config_file.endswith('.json'):
                    config_data = json.load(f)
                elif config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    import yaml
                    config_data = yaml.safe_load(f)
                else:
                    print("Unsupported config file format. Use JSON or YAML.")
                    return False
            
            # 创建环境配置对象
            env_config = EnvironmentConfig(
                name=env_name,
                variables=config_data.get('variables', {}),
                encrypted_variables=config_data.get('encrypted_variables', {}),
                config_files=config_data.get('config_files', []),
                validation_rules=config_data.get('validation_rules', {})
            )
            
            # 保存环境配置
            config_file_path = self.config_manager.config_dir / f"{env_name}.env.json"
            with open(config_file_path, 'w') as f:
                json.dump({
                    'name': env_config.name,
                    'variables': env_config.variables,
                    'encrypted_variables': env_config.encrypted_variables,
                    'config_files': env_config.config_files,
                    'validation_rules': env_config.validation_rules
                }, f, indent=2)
            
            print(f"✓ Environment '{env_name}' created successfully")
            return True
            
        except Exception as e:
            print(f"✗ Failed to create environment '{env_name}': {e}")
            return False
    
    def deploy_environment(self, env_name: str) -> bool:
        """部署环境配置"""
        try:
            print(f"Deploying environment: {env_name}")
            
            # 加载环境配置
            env_config = self.config_manager._load_environment_config(env_name)
            if not env_config:
                print(f"✗ Environment '{env_name}' not found")
                return False
            
            # 部署配置文件
            if self.config_manager.deploy_config_files(env_config):
                print(f"✓ Environment '{env_name}' deployed successfully")
                return True
            else:
                print(f"✗ Failed to deploy environment '{env_name}'")
                return False
                
        except Exception as e:
            print(f"✗ Failed to deploy environment '{env_name}': {e}")
            return False
    
    def store_secret(self, name: str, value: str, secret_type: str = "password",
                    access_level: str = "internal", expires_days: Optional[int] = None) -> bool:
        """存储密钥"""
        try:
            print(f"Storing secret: {name}")
            
            if self.secure_manager.store_secret(
                name=name,
                value=value,
                secret_type=secret_type,
                access_level=access_level,
                expires_days=expires_days
            ):
                print(f"✓ Secret '{name}' stored successfully")
                return True
            else:
                print(f"✗ Failed to store secret '{name}'")
                return False
                
        except Exception as e:
            print(f"✗ Failed to store secret '{name}': {e}")
            return False
    
    def retrieve_secret(self, name: str) -> Optional[str]:
        """检索密钥"""
        try:
            value = self.secure_manager.retrieve_secret(name)
            if value:
                print(f"✓ Secret '{name}' retrieved successfully")
                return value
            else:
                print(f"✗ Failed to retrieve secret '{name}'")
                return None
                
        except Exception as e:
            print(f"✗ Failed to retrieve secret '{name}': {e}")
            return None
    
    def rotate_secret(self, name: str, new_value: Optional[str] = None) -> bool:
        """轮换密钥"""
        try:
            print(f"Rotating secret: {name}")
            
            if self.secure_manager.rotate_secret(name, new_value):
                print(f"✓ Secret '{name}' rotated successfully")
                return True
            else:
                print(f"✗ Failed to rotate secret '{name}'")
                return False
                
        except Exception as e:
            print(f"✗ Failed to rotate secret '{name}': {e}")
            return False
    
    def check_security_compliance(self) -> bool:
        """检查安全合规性"""
        try:
            print("Running security compliance check...")
            
            report = self.secure_manager.run_security_compliance_check()
            
            print(f"\nCompliance Status: {report['overall_status']}")
            print(f"Timestamp: {report['timestamp']}")
            
            print("\nCheck Results:")
            for check in report['checks']:
                status_symbol = "✓" if check['status'] == "PASS" else "⚠" if check['status'] == "WARN" else "✗"
                print(f"  {status_symbol} {check['name']}: {check['status']}")
                for detail in check.get('details', []):
                    print(f"    - {detail}")
            
            if report['issues']:
                print("\nIssues Found:")
                for issue in report['issues']:
                    print(f"  ✗ {issue}")
            
            if report['recommendations']:
                print("\nRecommendations:")
                for rec in report['recommendations']:
                    print(f"  → {rec}")
            
            return report['overall_status'] in ['PASS', 'WARN']
            
        except Exception as e:
            print(f"✗ Security compliance check failed: {e}")
            return False
    
    def check_expiring_secrets(self, days_ahead: int = 30):
        """检查即将过期的密钥"""
        try:
            print(f"Checking for secrets expiring in the next {days_ahead} days...")
            
            expiring = self.secure_manager.check_expiring_secrets(days_ahead)
            
            if expiring:
                print(f"\nFound {len(expiring)} expiring secrets:")
                for secret in expiring:
                    print(f"  ⚠ {secret['name']} ({secret['type']}) - expires in {secret['days_left']} days")
            else:
                print("✓ No secrets expiring soon")
                
        except Exception as e:
            print(f"✗ Failed to check expiring secrets: {e}")
    
    def check_rotation_needed(self):
        """检查需要轮换的密钥"""
        try:
            print("Checking for secrets that need rotation...")
            
            rotation_needed = self.secure_manager.check_rotation_needed()
            
            if rotation_needed:
                print(f"\nFound {len(rotation_needed)} secrets needing rotation:")
                for secret in rotation_needed:
                    print(f"  ⚠ {secret['name']} ({secret['type']}) - {secret['days_overdue']} days overdue")
            else:
                print("✓ All secrets are up to date")
                
        except Exception as e:
            print(f"✗ Failed to check rotation status: {e}")
    
    def detect_config_changes(self, config_paths: List[str]):
        """检测配置文件变更"""
        try:
            print("Detecting configuration changes...")
            
            changes = self.config_manager.detect_config_changes(config_paths)
            
            if changes:
                print(f"\nConfiguration change summary:")
                for path, change_info in changes.items():
                    status = change_info['status']
                    symbol = "✓" if status == "unchanged" else "⚠" if status == "modified" else "?" if status == "new" else "✗"
                    print(f"  {symbol} {path}: {status}")
                    if change_info.get('message'):
                        print(f"    {change_info['message']}")
            else:
                print("✓ No configuration files to check")
                
        except Exception as e:
            print(f"✗ Failed to detect config changes: {e}")
    
    def generate_config_file(self, template_name: str, output_path: str, variables_file: str) -> bool:
        """生成配置文件"""
        try:
            print(f"Generating config file from template '{template_name}'...")
            
            # 读取变量文件
            with open(variables_file, 'r') as f:
                if variables_file.endswith('.json'):
                    variables = json.load(f)
                elif variables_file.endswith('.yaml') or variables_file.endswith('.yml'):
                    import yaml
                    variables = yaml.safe_load(f)
                else:
                    print("Unsupported variables file format. Use JSON or YAML.")
                    return False
            
            # 生成配置文件
            if self.config_manager.generate_config_file(
                template_name=template_name,
                output_path=output_path,
                variables=variables.get('variables', {}),
                encrypted_variables=variables.get('encrypted_variables', {})
            ):
                print(f"✓ Config file generated: {output_path}")
                return True
            else:
                print(f"✗ Failed to generate config file")
                return False
                
        except Exception as e:
            print(f"✗ Failed to generate config file: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Configuration Management CLI")
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # 设置模板命令
    setup_parser = subparsers.add_parser('setup-templates', help='Setup configuration templates')
    
    # 创建环境命令
    create_env_parser = subparsers.add_parser('create-env', help='Create environment configuration')
    create_env_parser.add_argument('name', help='Environment name')
    create_env_parser.add_argument('config', help='Configuration file path')
    
    # 部署环境命令
    deploy_parser = subparsers.add_parser('deploy', help='Deploy environment configuration')
    deploy_parser.add_argument('name', help='Environment name')
    
    # 存储密钥命令
    store_secret_parser = subparsers.add_parser('store-secret', help='Store a secret')
    store_secret_parser.add_argument('name', help='Secret name')
    store_secret_parser.add_argument('value', help='Secret value')
    store_secret_parser.add_argument('--type', default='password', help='Secret type')
    store_secret_parser.add_argument('--access-level', default='internal', help='Access level')
    store_secret_parser.add_argument('--expires-days', type=int, help='Expiration days')
    
    # 检索密钥命令
    get_secret_parser = subparsers.add_parser('get-secret', help='Retrieve a secret')
    get_secret_parser.add_argument('name', help='Secret name')
    
    # 轮换密钥命令
    rotate_parser = subparsers.add_parser('rotate-secret', help='Rotate a secret')
    rotate_parser.add_argument('name', help='Secret name')
    rotate_parser.add_argument('--new-value', help='New secret value (auto-generated if not provided)')
    
    # 安全合规检查命令
    compliance_parser = subparsers.add_parser('check-compliance', help='Run security compliance check')
    
    # 检查过期密钥命令
    expiring_parser = subparsers.add_parser('check-expiring', help='Check expiring secrets')
    expiring_parser.add_argument('--days', type=int, default=30, help='Days ahead to check')
    
    # 检查轮换需求命令
    rotation_parser = subparsers.add_parser('check-rotation', help='Check secrets needing rotation')
    
    # 检测配置变更命令
    changes_parser = subparsers.add_parser('detect-changes', help='Detect configuration changes')
    changes_parser.add_argument('paths', nargs='+', help='Configuration file paths')
    
    # 生成配置文件命令
    generate_parser = subparsers.add_parser('generate-config', help='Generate configuration file')
    generate_parser.add_argument('template', help='Template name')
    generate_parser.add_argument('output', help='Output file path')
    generate_parser.add_argument('variables', help='Variables file path')
    
    args = parser.parse_args()
    
    # 设置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建CLI实例
    cli = ConfigManagementCLI()
    
    # 执行命令
    try:
        if args.command == 'setup-templates':
            success = cli.setup_templates()
            sys.exit(0 if success else 1)
            
        elif args.command == 'create-env':
            success = cli.create_environment(args.name, args.config)
            sys.exit(0 if success else 1)
            
        elif args.command == 'deploy':
            success = cli.deploy_environment(args.name)
            sys.exit(0 if success else 1)
            
        elif args.command == 'store-secret':
            success = cli.store_secret(
                args.name, args.value, args.type, 
                args.access_level, args.expires_days
            )
            sys.exit(0 if success else 1)
            
        elif args.command == 'get-secret':
            value = cli.retrieve_secret(args.name)
            if value:
                print(value)
                sys.exit(0)
            else:
                sys.exit(1)
                
        elif args.command == 'rotate-secret':
            success = cli.rotate_secret(args.name, args.new_value)
            sys.exit(0 if success else 1)
            
        elif args.command == 'check-compliance':
            success = cli.check_security_compliance()
            sys.exit(0 if success else 1)
            
        elif args.command == 'check-expiring':
            cli.check_expiring_secrets(args.days)
            sys.exit(0)
            
        elif args.command == 'check-rotation':
            cli.check_rotation_needed()
            sys.exit(0)
            
        elif args.command == 'detect-changes':
            cli.detect_config_changes(args.paths)
            sys.exit(0)
            
        elif args.command == 'generate-config':
            success = cli.generate_config_file(args.template, args.output, args.variables)
            sys.exit(0 if success else 1)
            
        else:
            parser.print_help()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()