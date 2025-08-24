#!/usr/bin/env python3
"""
配置验证器 - ConfigValidator类实现
实现配置验证和语法检查功能
"""

import os
import json
import yaml
import re
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
import ipaddress
import urllib.parse


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


@dataclass
class ValidationRule:
    """验证规则"""
    name: str
    rule_type: str  # required, format, range, custom
    parameters: Dict[str, Any]
    error_message: str
    warning_message: Optional[str] = None


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_rules = self._load_default_rules()
    
    def _load_default_rules(self) -> Dict[str, List[ValidationRule]]:
        """加载默认验证规则"""
        return {
            "nginx": [
                ValidationRule(
                    name="server_name_format",
                    rule_type="format",
                    parameters={"pattern": r"^[a-zA-Z0-9.-]+$"},
                    error_message="Invalid server name format"
                ),
                ValidationRule(
                    name="listen_port",
                    rule_type="range",
                    parameters={"min": 1, "max": 65535},
                    error_message="Port must be between 1 and 65535"
                ),
                ValidationRule(
                    name="ssl_certificate_exists",
                    rule_type="custom",
                    parameters={"function": "check_file_exists"},
                    error_message="SSL certificate file not found"
                )
            ],
            "database": [
                ValidationRule(
                    name="connection_string_format",
                    rule_type="format",
                    parameters={"pattern": r"^postgresql://.*"},
                    error_message="Invalid PostgreSQL connection string format"
                ),
                ValidationRule(
                    name="pool_size",
                    rule_type="range",
                    parameters={"min": 1, "max": 100},
                    error_message="Pool size must be between 1 and 100"
                ),
                ValidationRule(
                    name="timeout_value",
                    rule_type="range",
                    parameters={"min": 1, "max": 300},
                    error_message="Timeout must be between 1 and 300 seconds"
                )
            ],
            "redis": [
                ValidationRule(
                    name="bind_address",
                    rule_type="custom",
                    parameters={"function": "validate_ip_address"},
                    error_message="Invalid IP address format"
                ),
                ValidationRule(
                    name="port_number",
                    rule_type="range",
                    parameters={"min": 1024, "max": 65535},
                    error_message="Port should be between 1024 and 65535"
                ),
                ValidationRule(
                    name="memory_limit",
                    rule_type="format",
                    parameters={"pattern": r"^\d+[kmg]?b?$"},
                    error_message="Invalid memory limit format (e.g., 256mb, 1gb)"
                )
            ],
            "application": [
                ValidationRule(
                    name="secret_key_length",
                    rule_type="custom",
                    parameters={"function": "validate_secret_key"},
                    error_message="Secret key must be at least 32 characters long"
                ),
                ValidationRule(
                    name="log_level",
                    rule_type="custom",
                    parameters={"function": "validate_log_level"},
                    error_message="Invalid log level"
                ),
                ValidationRule(
                    name="cors_origins",
                    rule_type="custom",
                    parameters={"function": "validate_cors_origins"},
                    error_message="Invalid CORS origins format"
                )
            ]
        }
    
    def validate_config_file(self, file_path: str, config_type: str) -> ValidationResult:
        """
        验证配置文件
        
        Args:
            file_path: 配置文件路径
            config_type: 配置类型 (nginx, database, redis, application)
            
        Returns:
            ValidationResult: 验证结果
        """
        try:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Configuration file not found: {file_path}"],
                    warnings=[],
                    suggestions=[]
                )
            
            # 根据文件类型解析配置
            config_data = self._parse_config_file(file_path)
            if config_data is None:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Failed to parse configuration file: {file_path}"],
                    warnings=[],
                    suggestions=[]
                )
            
            # 执行验证
            return self._validate_config_data(config_data, config_type)
            
        except Exception as e:
            self.logger.error(f"Error validating config file '{file_path}': {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {e}"],
                warnings=[],
                suggestions=[]
            )
    
    def validate_nginx_config(self, config_path: str) -> ValidationResult:
        """验证Nginx配置"""
        try:
            # 使用nginx -t命令验证语法
            result = subprocess.run(
                ['nginx', '-t', '-c', config_path],
                capture_output=True,
                text=True
            )
            
            errors = []
            warnings = []
            suggestions = []
            
            if result.returncode != 0:
                # 解析nginx错误输出
                error_lines = result.stderr.split('\n')
                for line in error_lines:
                    if 'error' in line.lower():
                        errors.append(line.strip())
                    elif 'warn' in line.lower():
                        warnings.append(line.strip())
            
            # 执行自定义验证
            custom_result = self._validate_nginx_custom(config_path)
            errors.extend(custom_result.errors)
            warnings.extend(custom_result.warnings)
            suggestions.extend(custom_result.suggestions)
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions
            )
            
        except FileNotFoundError:
            return ValidationResult(
                is_valid=False,
                errors=["nginx command not found. Please install nginx."],
                warnings=[],
                suggestions=["Install nginx to enable syntax validation"]
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Nginx validation error: {e}"],
                warnings=[],
                suggestions=[]
            )
    
    def validate_json_syntax(self, file_path: str) -> ValidationResult:
        """验证JSON语法"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            
            return ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[],
                suggestions=[]
            )
            
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"JSON syntax error at line {e.lineno}, column {e.colno}: {e.msg}"],
                warnings=[],
                suggestions=["Check for missing commas, quotes, or brackets"]
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Error reading JSON file: {e}"],
                warnings=[],
                suggestions=[]
            )
    
    def validate_yaml_syntax(self, file_path: str) -> ValidationResult:
        """验证YAML语法"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            
            return ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[],
                suggestions=[]
            )
            
        except yaml.YAMLError as e:
            error_msg = str(e)
            if hasattr(e, 'problem_mark'):
                mark = e.problem_mark
                error_msg = f"YAML syntax error at line {mark.line + 1}, column {mark.column + 1}: {e.problem}"
            
            return ValidationResult(
                is_valid=False,
                errors=[error_msg],
                warnings=[],
                suggestions=["Check indentation and YAML syntax"]
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Error reading YAML file: {e}"],
                warnings=[],
                suggestions=[]
            )
    
    def validate_environment_variables(self, env_vars: Dict[str, str]) -> ValidationResult:
        """验证环境变量"""
        errors = []
        warnings = []
        suggestions = []
        
        # 检查必需的环境变量
        required_vars = [
            'SECRET_KEY', 'DATABASE_URL', 'REDIS_URL'
        ]
        
        for var in required_vars:
            if var not in env_vars or not env_vars[var]:
                errors.append(f"Required environment variable '{var}' is missing or empty")
        
        # 验证特定变量格式
        if 'DATABASE_URL' in env_vars:
            if not self._validate_database_url(env_vars['DATABASE_URL']):
                errors.append("Invalid DATABASE_URL format")
        
        if 'REDIS_URL' in env_vars:
            if not self._validate_redis_url(env_vars['REDIS_URL']):
                errors.append("Invalid REDIS_URL format")
        
        if 'SECRET_KEY' in env_vars:
            if len(env_vars['SECRET_KEY']) < 32:
                warnings.append("SECRET_KEY should be at least 32 characters long")
        
        # 检查敏感信息泄露
        for key, value in env_vars.items():
            if self._contains_sensitive_info(key, value):
                warnings.append(f"Variable '{key}' may contain sensitive information")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def validate_ssl_certificate(self, cert_path: str, key_path: Optional[str] = None) -> ValidationResult:
        """验证SSL证书"""
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # 检查证书文件是否存在
            cert_file = Path(cert_path)
            if not cert_file.exists():
                errors.append(f"Certificate file not found: {cert_path}")
                return ValidationResult(False, errors, warnings, suggestions)
            
            # 使用openssl验证证书
            result = subprocess.run(
                ['openssl', 'x509', '-in', cert_path, '-text', '-noout'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                errors.append(f"Invalid certificate format: {result.stderr}")
                return ValidationResult(False, errors, warnings, suggestions)
            
            # 检查证书过期时间
            result = subprocess.run(
                ['openssl', 'x509', '-in', cert_path, '-enddate', '-noout'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                end_date_line = result.stdout.strip()
                if 'notAfter=' in end_date_line:
                    # 解析过期时间并检查
                    from datetime import datetime
                    import dateutil.parser
                    
                    date_str = end_date_line.split('notAfter=')[1]
                    try:
                        expire_date = dateutil.parser.parse(date_str)
                        days_left = (expire_date - datetime.now()).days
                        
                        if days_left < 0:
                            errors.append("Certificate has expired")
                        elif days_left < 30:
                            warnings.append(f"Certificate expires in {days_left} days")
                        elif days_left < 90:
                            suggestions.append(f"Certificate expires in {days_left} days - consider renewal")
                    except Exception:
                        warnings.append("Could not parse certificate expiration date")
            
            # 如果提供了私钥，验证匹配性
            if key_path:
                key_file = Path(key_path)
                if not key_file.exists():
                    errors.append(f"Private key file not found: {key_path}")
                else:
                    if not self._verify_cert_key_match(cert_path, key_path):
                        errors.append("Certificate and private key do not match")
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions
            )
            
        except FileNotFoundError:
            return ValidationResult(
                is_valid=False,
                errors=["openssl command not found. Please install OpenSSL."],
                warnings=[],
                suggestions=["Install OpenSSL to enable certificate validation"]
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Certificate validation error: {e}"],
                warnings=[],
                suggestions=[]
            )
    
    def _parse_config_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """解析配置文件"""
        try:
            file_path_obj = Path(file_path)
            suffix = file_path_obj.suffix.lower()
            
            with open(file_path, 'r', encoding='utf-8') as f:
                if suffix == '.json':
                    return json.load(f)
                elif suffix in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                elif suffix == '.conf' or suffix == '.ini':
                    # 简单的配置文件解析
                    config = {}
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                config[key.strip()] = value.strip()
                    return config
                else:
                    # 尝试作为JSON解析
                    f.seek(0)
                    return json.load(f)
                    
        except Exception as e:
            self.logger.error(f"Failed to parse config file '{file_path}': {e}")
            return None
    
    def _validate_config_data(self, config_data: Dict[str, Any], config_type: str) -> ValidationResult:
        """验证配置数据"""
        errors = []
        warnings = []
        suggestions = []
        
        rules = self.validation_rules.get(config_type, [])
        
        for rule in rules:
            try:
                if rule.rule_type == "required":
                    field = rule.parameters.get("field")
                    if field not in config_data or not config_data[field]:
                        errors.append(rule.error_message)
                
                elif rule.rule_type == "format":
                    field = rule.parameters.get("field")
                    pattern = rule.parameters.get("pattern")
                    if field in config_data:
                        value = str(config_data[field])
                        if not re.match(pattern, value):
                            errors.append(rule.error_message)
                
                elif rule.rule_type == "range":
                    field = rule.parameters.get("field")
                    min_val = rule.parameters.get("min")
                    max_val = rule.parameters.get("max")
                    if field in config_data:
                        try:
                            value = float(config_data[field])
                            if min_val is not None and value < min_val:
                                errors.append(rule.error_message)
                            elif max_val is not None and value > max_val:
                                errors.append(rule.error_message)
                        except (ValueError, TypeError):
                            errors.append(f"Invalid numeric value for {field}")
                
                elif rule.rule_type == "custom":
                    function_name = rule.parameters.get("function")
                    if hasattr(self, f"_{function_name}"):
                        validation_func = getattr(self, f"_{function_name}")
                        if not validation_func(config_data, rule.parameters):
                            errors.append(rule.error_message)
                            if rule.warning_message:
                                warnings.append(rule.warning_message)
                                
            except Exception as e:
                self.logger.error(f"Error applying validation rule '{rule.name}': {e}")
                warnings.append(f"Could not apply validation rule: {rule.name}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_nginx_custom(self, config_path: str) -> ValidationResult:
        """自定义Nginx配置验证"""
        errors = []
        warnings = []
        suggestions = []
        
        try:
            with open(config_path, 'r') as f:
                content = f.read()
            
            # 检查常见问题
            if 'ssl_certificate' in content and 'ssl_certificate_key' not in content:
                errors.append("SSL certificate specified but no private key found")
            
            if 'proxy_pass' in content and 'proxy_set_header Host' not in content:
                warnings.append("Consider adding 'proxy_set_header Host $host' for proper proxying")
            
            if 'gzip on' not in content:
                suggestions.append("Consider enabling gzip compression for better performance")
            
            # 检查安全头
            security_headers = [
                'add_header Strict-Transport-Security',
                'add_header X-Frame-Options',
                'add_header X-Content-Type-Options'
            ]
            
            missing_headers = []
            for header in security_headers:
                if header not in content:
                    missing_headers.append(header.split()[-1])
            
            if missing_headers:
                suggestions.append(f"Consider adding security headers: {', '.join(missing_headers)}")
            
        except Exception as e:
            errors.append(f"Error reading nginx config: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_database_url(self, url: str) -> bool:
        """验证数据库URL格式"""
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.scheme in ['postgresql', 'postgres'] and parsed.hostname
        except Exception:
            return False
    
    def _validate_redis_url(self, url: str) -> bool:
        """验证Redis URL格式"""
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.scheme == 'redis' and parsed.hostname
        except Exception:
            return False
    
    def _contains_sensitive_info(self, key: str, value: str) -> bool:
        """检查是否包含敏感信息"""
        sensitive_patterns = [
            r'password', r'secret', r'key', r'token', r'credential'
        ]
        
        key_lower = key.lower()
        for pattern in sensitive_patterns:
            if re.search(pattern, key_lower):
                return True
        
        return False
    
    def _verify_cert_key_match(self, cert_path: str, key_path: str) -> bool:
        """验证证书和私钥是否匹配"""
        try:
            # 获取证书的公钥哈希
            cert_result = subprocess.run(
                ['openssl', 'x509', '-in', cert_path, '-pubkey', '-noout'],
                capture_output=True,
                text=True
            )
            
            if cert_result.returncode != 0:
                return False
            
            cert_pubkey_result = subprocess.run(
                ['openssl', 'pkey', '-pubin', '-pubout'],
                input=cert_result.stdout,
                capture_output=True,
                text=True
            )
            
            # 获取私钥的公钥哈希
            key_result = subprocess.run(
                ['openssl', 'pkey', '-in', key_path, '-pubout'],
                capture_output=True,
                text=True
            )
            
            if key_result.returncode != 0:
                return False
            
            return cert_pubkey_result.stdout == key_result.stdout
            
        except Exception:
            return False
    
    def _validate_ip_address(self, config_data: Dict[str, Any], params: Dict[str, Any]) -> bool:
        """验证IP地址格式"""
        field = params.get("field", "bind_address")
        if field not in config_data:
            return True  # 字段不存在时跳过验证
        
        try:
            ipaddress.ip_address(config_data[field])
            return True
        except ValueError:
            return False
    
    def _validate_secret_key(self, config_data: Dict[str, Any], params: Dict[str, Any]) -> bool:
        """验证密钥长度"""
        field = params.get("field", "secret_key")
        min_length = params.get("min_length", 32)
        
        if field not in config_data:
            return False
        
        return len(str(config_data[field])) >= min_length
    
    def _validate_log_level(self, config_data: Dict[str, Any], params: Dict[str, Any]) -> bool:
        """验证日志级别"""
        field = params.get("field", "log_level")
        valid_levels = params.get("valid_levels", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        
        if field not in config_data:
            return True
        
        return str(config_data[field]).upper() in valid_levels
    
    def _validate_cors_origins(self, config_data: Dict[str, Any], params: Dict[str, Any]) -> bool:
        """验证CORS源"""
        field = params.get("field", "cors_origins")
        
        if field not in config_data:
            return True
        
        origins = config_data[field]
        if isinstance(origins, str):
            try:
                origins = json.loads(origins)
            except json.JSONDecodeError:
                return False
        
        if not isinstance(origins, list):
            return False
        
        for origin in origins:
            if origin != "*":
                try:
                    parsed = urllib.parse.urlparse(origin)
                    if not parsed.scheme or not parsed.netloc:
                        return False
                except Exception:
                    return False
        
        return True


def main():
    """主函数 - 用于测试"""
    logging.basicConfig(level=logging.INFO)
    
    validator = ConfigValidator()
    
    # 测试JSON语法验证
    print("Testing JSON validation...")
    json_result = validator.validate_json_syntax("test_config.json")
    print(f"JSON validation result: {json_result.is_valid}")
    
    # 测试环境变量验证
    print("\nTesting environment variables validation...")
    env_vars = {
        "SECRET_KEY": "short_key",
        "DATABASE_URL": "postgresql://user:pass@localhost/db",
        "REDIS_URL": "redis://localhost:6379/0"
    }
    env_result = validator.validate_environment_variables(env_vars)
    print(f"Environment validation result: {env_result.is_valid}")
    for warning in env_result.warnings:
        print(f"Warning: {warning}")
    
    print("ConfigValidator test completed!")


if __name__ == "__main__":
    main()