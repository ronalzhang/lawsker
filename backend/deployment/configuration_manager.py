#!/usr/bin/env python3
"""
配置管理系统 - ConfigurationManager类实现
支持环境配置模板管理、环境变量管理、配置文件生成和部署、配置更改检测和同步
"""

import os
import json
import yaml
import hashlib
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from jinja2 import Environment, FileSystemLoader, Template
from cryptography.fernet import Fernet
import subprocess
import re


@dataclass
class ConfigTemplate:
    """配置模板数据类"""
    name: str
    path: str
    template_content: str
    variables: Dict[str, Any]
    target_path: str
    permissions: str = "644"
    owner: Optional[str] = None
    group: Optional[str] = None


@dataclass
class EnvironmentConfig:
    """环境配置数据类"""
    name: str
    variables: Dict[str, str]
    encrypted_variables: Dict[str, str]
    config_files: List[str]
    validation_rules: Dict[str, Any]


@dataclass
class ConfigChange:
    """配置变更记录"""
    timestamp: datetime
    config_name: str
    change_type: str  # create, update, delete
    old_hash: Optional[str]
    new_hash: Optional[str]
    user: str
    description: str


class ConfigurationManager:
    """配置管理器类"""
    
    def __init__(self, config_dir: str = "/opt/lawsker/config", 
                 templates_dir: str = "/opt/lawsker/templates",
                 backup_dir: str = "/opt/lawsker/backups/config"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
            templates_dir: 模板文件目录
            backup_dir: 备份目录
        """
        self.config_dir = Path(config_dir)
        self.templates_dir = Path(templates_dir)
        self.backup_dir = Path(backup_dir)
        self.logger = logging.getLogger(__name__)
        
        # 创建必要目录
        for directory in [self.config_dir, self.templates_dir, self.backup_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # 初始化Jinja2模板环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 配置变更历史
        self.change_history: List[ConfigChange] = []
        self.change_history_file = self.config_dir / "change_history.json"
        
        # 加载变更历史
        self._load_change_history()
        
        # 初始化加密密钥
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        self.logger.info(f"ConfigurationManager initialized with config_dir: {config_dir}")
    
    def _get_or_create_encryption_key(self) -> bytes:
        """获取或创建加密密钥"""
        key_file = self.config_dir / ".encryption_key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # 只有所有者可读写
            return key
    
    def create_template(self, name: str, template_content: str, 
                       variables: Dict[str, Any], target_path: str,
                       permissions: str = "644", owner: Optional[str] = None,
                       group: Optional[str] = None) -> bool:
        """
        创建配置模板
        
        Args:
            name: 模板名称
            template_content: 模板内容
            variables: 模板变量
            target_path: 目标路径
            permissions: 文件权限
            owner: 文件所有者
            group: 文件组
            
        Returns:
            bool: 创建是否成功
        """
        try:
            template_file = self.templates_dir / f"{name}.j2"
            
            # 保存模板文件
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            # 保存模板元数据
            metadata = {
                'name': name,
                'template_file': str(template_file),
                'variables': variables,
                'target_path': target_path,
                'permissions': permissions,
                'owner': owner,
                'group': group,
                'created_at': datetime.now().isoformat()
            }
            
            metadata_file = self.templates_dir / f"{name}.meta.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Template '{name}' created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create template '{name}': {e}")
            return False
    
    def load_template(self, name: str) -> Optional[ConfigTemplate]:
        """
        加载配置模板
        
        Args:
            name: 模板名称
            
        Returns:
            ConfigTemplate: 模板对象，如果不存在返回None
        """
        try:
            metadata_file = self.templates_dir / f"{name}.meta.json"
            template_file = self.templates_dir / f"{name}.j2"
            
            if not metadata_file.exists() or not template_file.exists():
                self.logger.warning(f"Template '{name}' not found")
                return None
            
            # 加载元数据
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # 加载模板内容
            with open(template_file, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            return ConfigTemplate(
                name=metadata['name'],
                path=str(template_file),
                template_content=template_content,
                variables=metadata['variables'],
                target_path=metadata['target_path'],
                permissions=metadata.get('permissions', '644'),
                owner=metadata.get('owner'),
                group=metadata.get('group')
            )
            
        except Exception as e:
            self.logger.error(f"Failed to load template '{name}': {e}")
            return None
    
    def render_template(self, template_name: str, variables: Dict[str, Any]) -> Optional[str]:
        """
        渲染配置模板
        
        Args:
            template_name: 模板名称
            variables: 模板变量
            
        Returns:
            str: 渲染后的内容，失败返回None
        """
        try:
            template = self.jinja_env.get_template(f"{template_name}.j2")
            rendered_content = template.render(**variables)
            
            self.logger.info(f"Template '{template_name}' rendered successfully")
            return rendered_content
            
        except Exception as e:
            self.logger.error(f"Failed to render template '{template_name}': {e}")
            return None
    
    def validate_environment_variables(self, env_config: EnvironmentConfig) -> Tuple[bool, List[str]]:
        """
        验证环境变量
        
        Args:
            env_config: 环境配置
            
        Returns:
            Tuple[bool, List[str]]: (验证是否通过, 错误信息列表)
        """
        errors = []
        
        try:
            for var_name, rules in env_config.validation_rules.items():
                if var_name not in env_config.variables and var_name not in env_config.encrypted_variables:
                    if rules.get('required', False):
                        errors.append(f"Required variable '{var_name}' is missing")
                    continue
                
                # 获取变量值
                value = env_config.variables.get(var_name)
                if value is None and var_name in env_config.encrypted_variables:
                    # 解密变量值进行验证
                    encrypted_value = env_config.encrypted_variables[var_name]
                    value = self.cipher.decrypt(encrypted_value.encode()).decode()
                
                if value is None:
                    continue
                
                # 验证规则
                if 'type' in rules:
                    expected_type = rules['type']
                    if expected_type == 'int':
                        try:
                            int(value)
                        except ValueError:
                            errors.append(f"Variable '{var_name}' must be an integer")
                    elif expected_type == 'float':
                        try:
                            float(value)
                        except ValueError:
                            errors.append(f"Variable '{var_name}' must be a float")
                    elif expected_type == 'bool':
                        if value.lower() not in ['true', 'false', '1', '0', 'yes', 'no']:
                            errors.append(f"Variable '{var_name}' must be a boolean")
                
                if 'pattern' in rules:
                    pattern = rules['pattern']
                    if not re.match(pattern, value):
                        errors.append(f"Variable '{var_name}' does not match pattern: {pattern}")
                
                if 'min_length' in rules:
                    if len(value) < rules['min_length']:
                        errors.append(f"Variable '{var_name}' is too short (min: {rules['min_length']})")
                
                if 'max_length' in rules:
                    if len(value) > rules['max_length']:
                        errors.append(f"Variable '{var_name}' is too long (max: {rules['max_length']})")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            self.logger.error(f"Error validating environment variables: {e}")
            return False, [f"Validation error: {e}"]
    
    def encrypt_sensitive_variable(self, value: str) -> str:
        """
        加密敏感变量
        
        Args:
            value: 要加密的值
            
        Returns:
            str: 加密后的值
        """
        try:
            encrypted_value = self.cipher.encrypt(value.encode())
            return encrypted_value.decode()
        except Exception as e:
            self.logger.error(f"Failed to encrypt variable: {e}")
            raise
    
    def decrypt_sensitive_variable(self, encrypted_value: str) -> str:
        """
        解密敏感变量
        
        Args:
            encrypted_value: 加密的值
            
        Returns:
            str: 解密后的值
        """
        try:
            decrypted_value = self.cipher.decrypt(encrypted_value.encode())
            return decrypted_value.decode()
        except Exception as e:
            self.logger.error(f"Failed to decrypt variable: {e}")
            raise
    
    def generate_config_file(self, template_name: str, output_path: str, 
                           variables: Dict[str, Any], 
                           encrypted_variables: Optional[Dict[str, str]] = None) -> bool:
        """
        生成配置文件
        
        Args:
            template_name: 模板名称
            output_path: 输出路径
            variables: 模板变量
            encrypted_variables: 加密变量
            
        Returns:
            bool: 生成是否成功
        """
        try:
            # 合并变量
            all_variables = variables.copy()
            
            # 解密敏感变量
            if encrypted_variables:
                for key, encrypted_value in encrypted_variables.items():
                    try:
                        decrypted_value = self.decrypt_sensitive_variable(encrypted_value)
                        all_variables[key] = decrypted_value
                    except Exception as e:
                        self.logger.error(f"Failed to decrypt variable '{key}': {e}")
                        return False
            
            # 渲染模板
            rendered_content = self.render_template(template_name, all_variables)
            if rendered_content is None:
                return False
            
            # 备份现有文件
            output_file = Path(output_path)
            if output_file.exists():
                self._backup_config_file(output_path)
            
            # 创建目录
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(rendered_content)
            
            # 设置权限
            template = self.load_template(template_name)
            if template:
                os.chmod(output_file, int(template.permissions, 8))
                
                # 设置所有者和组
                if template.owner or template.group:
                    self._set_file_ownership(output_path, template.owner, template.group)
            
            # 记录变更
            self._record_config_change(
                config_name=template_name,
                change_type="update",
                new_hash=self._calculate_file_hash(output_path),
                description=f"Generated config file: {output_path}"
            )
            
            self.logger.info(f"Config file generated: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate config file '{output_path}': {e}")
            return False
    
    def deploy_config_files(self, env_config: EnvironmentConfig) -> bool:
        """
        部署配置文件
        
        Args:
            env_config: 环境配置
            
        Returns:
            bool: 部署是否成功
        """
        try:
            # 验证环境变量
            is_valid, errors = self.validate_environment_variables(env_config)
            if not is_valid:
                self.logger.error(f"Environment validation failed: {errors}")
                return False
            
            success_count = 0
            total_count = len(env_config.config_files)
            
            for config_file in env_config.config_files:
                template_name = Path(config_file).stem
                
                if self.generate_config_file(
                    template_name=template_name,
                    output_path=config_file,
                    variables=env_config.variables,
                    encrypted_variables=env_config.encrypted_variables
                ):
                    success_count += 1
                else:
                    self.logger.error(f"Failed to deploy config file: {config_file}")
            
            success = success_count == total_count
            self.logger.info(f"Config deployment: {success_count}/{total_count} files deployed successfully")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to deploy config files: {e}")
            return False
    
    def detect_config_changes(self, config_paths: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        检测配置文件变更
        
        Args:
            config_paths: 配置文件路径列表
            
        Returns:
            Dict: 变更信息
        """
        changes = {}
        
        try:
            for config_path in config_paths:
                config_file = Path(config_path)
                if not config_file.exists():
                    changes[config_path] = {
                        'status': 'missing',
                        'message': 'Config file does not exist'
                    }
                    continue
                
                current_hash = self._calculate_file_hash(config_path)
                
                # 查找最近的变更记录
                last_change = None
                for change in reversed(self.change_history):
                    if config_path in change.description:
                        last_change = change
                        break
                
                if last_change is None:
                    changes[config_path] = {
                        'status': 'new',
                        'current_hash': current_hash,
                        'message': 'No previous change record found'
                    }
                elif last_change.new_hash != current_hash:
                    changes[config_path] = {
                        'status': 'modified',
                        'current_hash': current_hash,
                        'last_hash': last_change.new_hash,
                        'last_change': last_change.timestamp.isoformat(),
                        'message': 'File has been modified since last deployment'
                    }
                else:
                    changes[config_path] = {
                        'status': 'unchanged',
                        'current_hash': current_hash,
                        'message': 'File unchanged since last deployment'
                    }
            
            return changes
            
        except Exception as e:
            self.logger.error(f"Failed to detect config changes: {e}")
            return {}
    
    def sync_config_changes(self, source_env: str, target_env: str, 
                          config_names: List[str]) -> bool:
        """
        同步配置变更
        
        Args:
            source_env: 源环境
            target_env: 目标环境
            config_names: 要同步的配置名称列表
            
        Returns:
            bool: 同步是否成功
        """
        try:
            source_config = self._load_environment_config(source_env)
            target_config = self._load_environment_config(target_env)
            
            if not source_config or not target_config:
                self.logger.error("Failed to load source or target environment config")
                return False
            
            sync_success = True
            
            for config_name in config_names:
                try:
                    # 从源环境获取配置
                    if config_name not in source_config.config_files:
                        self.logger.warning(f"Config '{config_name}' not found in source environment")
                        continue
                    
                    # 生成目标环境的配置文件
                    template_name = Path(config_name).stem
                    target_path = config_name.replace(source_env, target_env)
                    
                    if not self.generate_config_file(
                        template_name=template_name,
                        output_path=target_path,
                        variables=target_config.variables,
                        encrypted_variables=target_config.encrypted_variables
                    ):
                        sync_success = False
                        self.logger.error(f"Failed to sync config '{config_name}'")
                    else:
                        self.logger.info(f"Successfully synced config '{config_name}' to {target_env}")
                
                except Exception as e:
                    self.logger.error(f"Error syncing config '{config_name}': {e}")
                    sync_success = False
            
            return sync_success
            
        except Exception as e:
            self.logger.error(f"Failed to sync config changes: {e}")
            return False
    
    def _backup_config_file(self, config_path: str) -> bool:
        """备份配置文件"""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                return True
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{config_file.name}.{timestamp}.backup"
            backup_path = self.backup_dir / backup_name
            
            shutil.copy2(config_file, backup_path)
            self.logger.info(f"Config file backed up: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to backup config file '{config_path}': {e}")
            return False
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to calculate hash for '{file_path}': {e}")
            return ""
    
    def _set_file_ownership(self, file_path: str, owner: Optional[str], group: Optional[str]):
        """设置文件所有者和组"""
        try:
            if owner or group:
                cmd = ["chown"]
                if owner and group:
                    cmd.append(f"{owner}:{group}")
                elif owner:
                    cmd.append(owner)
                elif group:
                    cmd.append(f":{group}")
                cmd.append(file_path)
                
                subprocess.run(cmd, check=True, capture_output=True)
                self.logger.info(f"Set ownership for '{file_path}': {owner}:{group}")
        except Exception as e:
            self.logger.error(f"Failed to set ownership for '{file_path}': {e}")
    
    def _record_config_change(self, config_name: str, change_type: str,
                            old_hash: Optional[str] = None, new_hash: Optional[str] = None,
                            description: str = ""):
        """记录配置变更"""
        try:
            change = ConfigChange(
                timestamp=datetime.now(),
                config_name=config_name,
                change_type=change_type,
                old_hash=old_hash,
                new_hash=new_hash,
                user=os.getenv('USER', 'system'),
                description=description
            )
            
            self.change_history.append(change)
            self._save_change_history()
            
        except Exception as e:
            self.logger.error(f"Failed to record config change: {e}")
    
    def _load_change_history(self):
        """加载变更历史"""
        try:
            if self.change_history_file.exists():
                with open(self.change_history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    
                for item in history_data:
                    change = ConfigChange(
                        timestamp=datetime.fromisoformat(item['timestamp']),
                        config_name=item['config_name'],
                        change_type=item['change_type'],
                        old_hash=item.get('old_hash'),
                        new_hash=item.get('new_hash'),
                        user=item['user'],
                        description=item['description']
                    )
                    self.change_history.append(change)
                    
        except Exception as e:
            self.logger.error(f"Failed to load change history: {e}")
            self.change_history = []
    
    def _save_change_history(self):
        """保存变更历史"""
        try:
            history_data = []
            for change in self.change_history:
                history_data.append({
                    'timestamp': change.timestamp.isoformat(),
                    'config_name': change.config_name,
                    'change_type': change.change_type,
                    'old_hash': change.old_hash,
                    'new_hash': change.new_hash,
                    'user': change.user,
                    'description': change.description
                })
            
            with open(self.change_history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to save change history: {e}")
    
    def _load_environment_config(self, env_name: str) -> Optional[EnvironmentConfig]:
        """加载环境配置"""
        try:
            config_file = self.config_dir / f"{env_name}.env.json"
            if not config_file.exists():
                return None
            
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return EnvironmentConfig(
                name=data['name'],
                variables=data['variables'],
                encrypted_variables=data.get('encrypted_variables', {}),
                config_files=data['config_files'],
                validation_rules=data.get('validation_rules', {})
            )
            
        except Exception as e:
            self.logger.error(f"Failed to load environment config '{env_name}': {e}")
            return None


def main():
    """主函数 - 用于测试"""
    logging.basicConfig(level=logging.INFO)
    
    # 创建配置管理器
    config_manager = ConfigurationManager()
    
    # 示例：创建Nginx配置模板
    nginx_template = """
server {
    listen 80;
    server_name {{ domain }};
    
    {% if ssl_enabled %}
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name {{ domain }};
    
    ssl_certificate {{ ssl_cert_path }};
    ssl_certificate_key {{ ssl_key_path }};
    {% endif %}
    
    location / {
        proxy_pass {{ backend_url }};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias {{ static_path }}/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
"""
    
    # 创建模板
    config_manager.create_template(
        name="nginx_site",
        template_content=nginx_template,
        variables={
            "domain": "example.com",
            "ssl_enabled": True,
            "ssl_cert_path": "/etc/ssl/certs/example.com.crt",
            "ssl_key_path": "/etc/ssl/private/example.com.key",
            "backend_url": "http://127.0.0.1:8000",
            "static_path": "/var/www/static"
        },
        target_path="/etc/nginx/sites-available/example.com"
    )
    
    print("ConfigurationManager test completed successfully!")


if __name__ == "__main__":
    main()