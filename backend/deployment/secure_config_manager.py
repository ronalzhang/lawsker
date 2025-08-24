#!/usr/bin/env python3
"""
安全配置管理器 - SecureConfigManager类实现
实现密钥和证书安全存储、访问权限控制和审计、密钥轮换和更新机制、安全配置合规检查
"""

import os
import json
import yaml
import hashlib
import logging
import secrets
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.x509 import load_pem_x509_certificate
import base64
import stat
import pwd
import grp


@dataclass
class SecretMetadata:
    """密钥元数据"""
    name: str
    type: str  # password, api_key, certificate, private_key, etc.
    created_at: datetime
    expires_at: Optional[datetime]
    last_rotated: Optional[datetime]
    rotation_interval: Optional[int]  # days
    access_level: str  # public, internal, restricted, confidential
    owner: str
    tags: List[str]


@dataclass
class AccessRecord:
    """访问记录"""
    timestamp: datetime
    user: str
    action: str  # read, write, delete, rotate
    secret_name: str
    ip_address: Optional[str]
    success: bool
    details: Optional[str]


@dataclass
class SecurityPolicy:
    """安全策略"""
    min_password_length: int = 12
    require_special_chars: bool = True
    require_numbers: bool = True
    require_uppercase: bool = True
    require_lowercase: bool = True
    max_password_age_days: int = 90
    password_history_count: int = 5
    failed_attempts_threshold: int = 5
    lockout_duration_minutes: int = 30
    encryption_algorithm: str = "AES-256-GCM"
    key_rotation_interval_days: int = 30
    certificate_renewal_days: int = 30
    audit_retention_days: int = 365


class SecureConfigManager:
    """安全配置管理器"""
    
    def __init__(self, vault_path: str = "/opt/lawsker/vault",
                 audit_log_path: str = "/var/log/lawsker/security_audit.log"):
        """
        初始化安全配置管理器
        
        Args:
            vault_path: 密钥库路径
            audit_log_path: 审计日志路径
        """
        self.vault_path = Path(vault_path)
        self.audit_log_path = Path(audit_log_path)
        self.logger = logging.getLogger(__name__)
        
        # 创建必要目录
        self.vault_path.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 设置目录权限
        os.chmod(self.vault_path, 0o700)
        
        # 密钥存储路径
        self.secrets_path = self.vault_path / "secrets"
        self.keys_path = self.vault_path / "keys"
        self.certs_path = self.vault_path / "certificates"
        self.metadata_path = self.vault_path / "metadata"
        
        for path in [self.secrets_path, self.keys_path, self.certs_path, self.metadata_path]:
            path.mkdir(exist_ok=True, mode=0o700)
        
        # 初始化主密钥
        self.master_key = self._get_or_create_master_key()
        self.cipher = Fernet(self.master_key)
        
        # 安全策略
        self.security_policy = SecurityPolicy()
        
        # 访问记录
        self.access_records: List[AccessRecord] = []
        
        # 密钥元数据缓存
        self.secrets_metadata: Dict[str, SecretMetadata] = {}
        self._load_secrets_metadata()
        
        # 失败尝试跟踪
        self.failed_attempts: Dict[str, List[datetime]] = {}
        
        self.logger.info(f"SecureConfigManager initialized with vault: {vault_path}")
    
    def _get_or_create_master_key(self) -> bytes:
        """获取或创建主密钥"""
        master_key_file = self.vault_path / ".master_key"
        
        if master_key_file.exists():
            # 验证文件权限
            file_stat = master_key_file.stat()
            if file_stat.st_mode & 0o077:
                raise PermissionError("Master key file has insecure permissions")
            
            with open(master_key_file, 'rb') as f:
                return f.read()
        else:
            # 生成新的主密钥
            key = Fernet.generate_key()
            with open(master_key_file, 'wb') as f:
                f.write(key)
            os.chmod(master_key_file, 0o600)
            
            self.logger.info("New master key generated")
            return key
    
    def store_secret(self, name: str, value: str, secret_type: str = "password",
                    access_level: str = "internal", expires_days: Optional[int] = None,
                    rotation_interval_days: Optional[int] = None,
                    tags: Optional[List[str]] = None) -> bool:
        """
        存储密钥
        
        Args:
            name: 密钥名称
            value: 密钥值
            secret_type: 密钥类型
            access_level: 访问级别
            expires_days: 过期天数
            rotation_interval_days: 轮换间隔天数
            tags: 标签
            
        Returns:
            bool: 存储是否成功
        """
        try:
            # 验证访问权限
            if not self._check_access_permission("write", name):
                self._log_access("write", name, False, "Access denied")
                return False
            
            # 验证密钥强度
            if secret_type == "password" and not self._validate_password_strength(value):
                self._log_access("write", name, False, "Password does not meet security requirements")
                return False
            
            # 加密密钥值
            encrypted_value = self.cipher.encrypt(value.encode())
            
            # 创建密钥文件
            secret_file = self.secrets_path / f"{name}.enc"
            with open(secret_file, 'wb') as f:
                f.write(encrypted_value)
            os.chmod(secret_file, 0o600)
            
            # 创建元数据
            expires_at = None
            if expires_days:
                expires_at = datetime.now() + timedelta(days=expires_days)
            
            metadata = SecretMetadata(
                name=name,
                type=secret_type,
                created_at=datetime.now(),
                expires_at=expires_at,
                last_rotated=None,
                rotation_interval=rotation_interval_days,
                access_level=access_level,
                owner=os.getenv('USER', 'system'),
                tags=tags or []
            )
            
            self.secrets_metadata[name] = metadata
            self._save_secret_metadata(name, metadata)
            
            self._log_access("write", name, True, f"Secret stored with type: {secret_type}")
            self.logger.info(f"Secret '{name}' stored successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store secret '{name}': {e}")
            self._log_access("write", name, False, f"Error: {e}")
            return False
    
    def retrieve_secret(self, name: str) -> Optional[str]:
        """
        检索密钥
        
        Args:
            name: 密钥名称
            
        Returns:
            str: 密钥值，失败返回None
        """
        try:
            # 验证访问权限
            if not self._check_access_permission("read", name):
                self._log_access("read", name, False, "Access denied")
                return None
            
            # 检查密钥是否存在
            secret_file = self.secrets_path / f"{name}.enc"
            if not secret_file.exists():
                self._log_access("read", name, False, "Secret not found")
                return None
            
            # 检查密钥是否过期
            metadata = self.secrets_metadata.get(name)
            if metadata and metadata.expires_at and datetime.now() > metadata.expires_at:
                self._log_access("read", name, False, "Secret expired")
                return None
            
            # 读取并解密密钥
            with open(secret_file, 'rb') as f:
                encrypted_value = f.read()
            
            decrypted_value = self.cipher.decrypt(encrypted_value).decode()
            
            self._log_access("read", name, True, "Secret retrieved")
            return decrypted_value
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve secret '{name}': {e}")
            self._log_access("read", name, False, f"Error: {e}")
            return None
    
    def delete_secret(self, name: str) -> bool:
        """
        删除密钥
        
        Args:
            name: 密钥名称
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 验证访问权限
            if not self._check_access_permission("delete", name):
                self._log_access("delete", name, False, "Access denied")
                return False
            
            # 删除密钥文件
            secret_file = self.secrets_path / f"{name}.enc"
            if secret_file.exists():
                secret_file.unlink()
            
            # 删除元数据
            metadata_file = self.metadata_path / f"{name}.json"
            if metadata_file.exists():
                metadata_file.unlink()
            
            # 从缓存中移除
            if name in self.secrets_metadata:
                del self.secrets_metadata[name]
            
            self._log_access("delete", name, True, "Secret deleted")
            self.logger.info(f"Secret '{name}' deleted successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete secret '{name}': {e}")
            self._log_access("delete", name, False, f"Error: {e}")
            return False
    
    def rotate_secret(self, name: str, new_value: Optional[str] = None) -> bool:
        """
        轮换密钥
        
        Args:
            name: 密钥名称
            new_value: 新密钥值，如果为None则自动生成
            
        Returns:
            bool: 轮换是否成功
        """
        try:
            # 验证访问权限
            if not self._check_access_permission("rotate", name):
                self._log_access("rotate", name, False, "Access denied")
                return False
            
            # 获取现有元数据
            metadata = self.secrets_metadata.get(name)
            if not metadata:
                self._log_access("rotate", name, False, "Secret not found")
                return False
            
            # 生成新密钥值
            if new_value is None:
                if metadata.type == "password":
                    new_value = self._generate_secure_password()
                elif metadata.type == "api_key":
                    new_value = self._generate_api_key()
                else:
                    self._log_access("rotate", name, False, "Cannot auto-generate value for this secret type")
                    return False
            
            # 备份旧密钥
            old_value = self.retrieve_secret(name)
            if old_value:
                self._backup_secret(name, old_value)
            
            # 存储新密钥
            if self.store_secret(
                name=name,
                value=new_value,
                secret_type=metadata.type,
                access_level=metadata.access_level,
                rotation_interval_days=metadata.rotation_interval,
                tags=metadata.tags
            ):
                # 更新轮换时间
                metadata.last_rotated = datetime.now()
                self.secrets_metadata[name] = metadata
                self._save_secret_metadata(name, metadata)
                
                self._log_access("rotate", name, True, "Secret rotated")
                self.logger.info(f"Secret '{name}' rotated successfully")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to rotate secret '{name}': {e}")
            self._log_access("rotate", name, False, f"Error: {e}")
            return False
    
    def store_certificate(self, name: str, cert_content: str, private_key: Optional[str] = None,
                         cert_chain: Optional[str] = None) -> bool:
        """
        存储SSL证书
        
        Args:
            name: 证书名称
            cert_content: 证书内容
            private_key: 私钥内容
            cert_chain: 证书链内容
            
        Returns:
            bool: 存储是否成功
        """
        try:
            # 验证证书格式
            try:
                cert = load_pem_x509_certificate(cert_content.encode())
                expires_at = cert.not_valid_after
            except Exception as e:
                self.logger.error(f"Invalid certificate format: {e}")
                return False
            
            # 存储证书
            cert_file = self.certs_path / f"{name}.crt"
            with open(cert_file, 'w') as f:
                f.write(cert_content)
            os.chmod(cert_file, 0o644)
            
            # 存储私钥
            if private_key:
                key_file = self.keys_path / f"{name}.key"
                encrypted_key = self.cipher.encrypt(private_key.encode())
                with open(key_file, 'wb') as f:
                    f.write(encrypted_key)
                os.chmod(key_file, 0o600)
            
            # 存储证书链
            if cert_chain:
                chain_file = self.certs_path / f"{name}-chain.crt"
                with open(chain_file, 'w') as f:
                    f.write(cert_chain)
                os.chmod(chain_file, 0o644)
            
            # 创建元数据
            metadata = SecretMetadata(
                name=name,
                type="certificate",
                created_at=datetime.now(),
                expires_at=expires_at,
                last_rotated=None,
                rotation_interval=None,
                access_level="internal",
                owner=os.getenv('USER', 'system'),
                tags=["ssl", "certificate"]
            )
            
            self.secrets_metadata[name] = metadata
            self._save_secret_metadata(name, metadata)
            
            self._log_access("write", name, True, "Certificate stored")
            self.logger.info(f"Certificate '{name}' stored successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store certificate '{name}': {e}")
            self._log_access("write", name, False, f"Error: {e}")
            return False
    
    def get_certificate_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取证书信息
        
        Args:
            name: 证书名称
            
        Returns:
            Dict: 证书信息
        """
        try:
            cert_file = self.certs_path / f"{name}.crt"
            if not cert_file.exists():
                return None
            
            with open(cert_file, 'r') as f:
                cert_content = f.read()
            
            cert = load_pem_x509_certificate(cert_content.encode())
            
            return {
                "subject": cert.subject.rfc4514_string(),
                "issuer": cert.issuer.rfc4514_string(),
                "serial_number": str(cert.serial_number),
                "not_valid_before": cert.not_valid_before.isoformat(),
                "not_valid_after": cert.not_valid_after.isoformat(),
                "days_until_expiry": (cert.not_valid_after - datetime.now()).days,
                "signature_algorithm": cert.signature_algorithm_oid._name
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get certificate info for '{name}': {e}")
            return None
    
    def check_expiring_secrets(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """
        检查即将过期的密钥
        
        Args:
            days_ahead: 提前检查天数
            
        Returns:
            List: 即将过期的密钥列表
        """
        expiring_secrets = []
        cutoff_date = datetime.now() + timedelta(days=days_ahead)
        
        for name, metadata in self.secrets_metadata.items():
            if metadata.expires_at and metadata.expires_at <= cutoff_date:
                days_left = (metadata.expires_at - datetime.now()).days
                expiring_secrets.append({
                    "name": name,
                    "type": metadata.type,
                    "expires_at": metadata.expires_at.isoformat(),
                    "days_left": days_left,
                    "access_level": metadata.access_level
                })
        
        return expiring_secrets
    
    def check_rotation_needed(self) -> List[Dict[str, Any]]:
        """
        检查需要轮换的密钥
        
        Returns:
            List: 需要轮换的密钥列表
        """
        rotation_needed = []
        
        for name, metadata in self.secrets_metadata.items():
            if metadata.rotation_interval:
                if metadata.last_rotated:
                    next_rotation = metadata.last_rotated + timedelta(days=metadata.rotation_interval)
                else:
                    next_rotation = metadata.created_at + timedelta(days=metadata.rotation_interval)
                
                if datetime.now() >= next_rotation:
                    days_overdue = (datetime.now() - next_rotation).days
                    rotation_needed.append({
                        "name": name,
                        "type": metadata.type,
                        "last_rotated": metadata.last_rotated.isoformat() if metadata.last_rotated else None,
                        "rotation_interval": metadata.rotation_interval,
                        "days_overdue": days_overdue,
                        "access_level": metadata.access_level
                    })
        
        return rotation_needed
    
    def run_security_compliance_check(self) -> Dict[str, Any]:
        """
        运行安全合规检查
        
        Returns:
            Dict: 合规检查结果
        """
        compliance_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "PASS",
            "checks": [],
            "issues": [],
            "recommendations": []
        }
        
        try:
            # 检查文件权限
            self._check_file_permissions(compliance_report)
            
            # 检查密钥强度
            self._check_secret_strength(compliance_report)
            
            # 检查过期密钥
            self._check_expired_secrets(compliance_report)
            
            # 检查轮换策略
            self._check_rotation_policy(compliance_report)
            
            # 检查访问控制
            self._check_access_controls(compliance_report)
            
            # 检查审计日志
            self._check_audit_logs(compliance_report)
            
            # 确定总体状态
            if any(check["status"] == "FAIL" for check in compliance_report["checks"]):
                compliance_report["overall_status"] = "FAIL"
            elif any(check["status"] == "WARN" for check in compliance_report["checks"]):
                compliance_report["overall_status"] = "WARN"
            
            return compliance_report
            
        except Exception as e:
            self.logger.error(f"Security compliance check failed: {e}")
            compliance_report["overall_status"] = "ERROR"
            compliance_report["issues"].append(f"Compliance check error: {e}")
            return compliance_report
    
    def _check_access_permission(self, action: str, secret_name: str) -> bool:
        """检查访问权限"""
        # 简化的权限检查 - 在实际环境中应该更复杂
        user = os.getenv('USER', 'unknown')
        
        # 检查失败尝试
        if user in self.failed_attempts:
            recent_failures = [
                attempt for attempt in self.failed_attempts[user]
                if datetime.now() - attempt < timedelta(minutes=self.security_policy.lockout_duration_minutes)
            ]
            if len(recent_failures) >= self.security_policy.failed_attempts_threshold:
                return False
        
        # 检查密钥访问级别
        metadata = self.secrets_metadata.get(secret_name)
        if metadata:
            if metadata.access_level == "confidential" and user != metadata.owner:
                return False
        
        return True
    
    def _validate_password_strength(self, password: str) -> bool:
        """验证密码强度"""
        policy = self.security_policy
        
        if len(password) < policy.min_password_length:
            return False
        
        if policy.require_uppercase and not any(c.isupper() for c in password):
            return False
        
        if policy.require_lowercase and not any(c.islower() for c in password):
            return False
        
        if policy.require_numbers and not any(c.isdigit() for c in password):
            return False
        
        if policy.require_special_chars and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False
        
        return True
    
    def _generate_secure_password(self, length: int = 16) -> str:
        """生成安全密码"""
        import string
        
        # 确保包含所有必需字符类型
        chars = ""
        password = ""
        
        if self.security_policy.require_uppercase:
            chars += string.ascii_uppercase
            password += secrets.choice(string.ascii_uppercase)
        
        if self.security_policy.require_lowercase:
            chars += string.ascii_lowercase
            password += secrets.choice(string.ascii_lowercase)
        
        if self.security_policy.require_numbers:
            chars += string.digits
            password += secrets.choice(string.digits)
        
        if self.security_policy.require_special_chars:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            chars += special_chars
            password += secrets.choice(special_chars)
        
        # 填充剩余长度
        for _ in range(length - len(password)):
            password += secrets.choice(chars)
        
        # 打乱密码字符顺序
        password_list = list(password)
        secrets.SystemRandom().shuffle(password_list)
        
        return ''.join(password_list)
    
    def _generate_api_key(self, length: int = 32) -> str:
        """生成API密钥"""
        return secrets.token_urlsafe(length)
    
    def _backup_secret(self, name: str, value: str):
        """备份密钥"""
        try:
            backup_dir = self.vault_path / "backups"
            backup_dir.mkdir(exist_ok=True, mode=0o700)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"{name}_{timestamp}.backup"
            
            encrypted_backup = self.cipher.encrypt(value.encode())
            with open(backup_file, 'wb') as f:
                f.write(encrypted_backup)
            os.chmod(backup_file, 0o600)
            
        except Exception as e:
            self.logger.error(f"Failed to backup secret '{name}': {e}")
    
    def _log_access(self, action: str, secret_name: str, success: bool, details: str = ""):
        """记录访问日志"""
        try:
            record = AccessRecord(
                timestamp=datetime.now(),
                user=os.getenv('USER', 'unknown'),
                action=action,
                secret_name=secret_name,
                ip_address=os.getenv('SSH_CLIENT', '').split()[0] if os.getenv('SSH_CLIENT') else None,
                success=success,
                details=details
            )
            
            self.access_records.append(record)
            
            # 写入审计日志
            log_entry = {
                "timestamp": record.timestamp.isoformat(),
                "user": record.user,
                "action": record.action,
                "secret_name": record.secret_name,
                "ip_address": record.ip_address,
                "success": record.success,
                "details": record.details
            }
            
            with open(self.audit_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            # 记录失败尝试
            if not success:
                user = record.user
                if user not in self.failed_attempts:
                    self.failed_attempts[user] = []
                self.failed_attempts[user].append(record.timestamp)
            
        except Exception as e:
            self.logger.error(f"Failed to log access: {e}")
    
    def _save_secret_metadata(self, name: str, metadata: SecretMetadata):
        """保存密钥元数据"""
        try:
            metadata_file = self.metadata_path / f"{name}.json"
            metadata_dict = asdict(metadata)
            
            # 转换datetime对象为字符串
            for key, value in metadata_dict.items():
                if isinstance(value, datetime):
                    metadata_dict[key] = value.isoformat()
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata_dict, f, indent=2)
            os.chmod(metadata_file, 0o600)
            
        except Exception as e:
            self.logger.error(f"Failed to save metadata for '{name}': {e}")
    
    def _load_secrets_metadata(self):
        """加载密钥元数据"""
        try:
            for metadata_file in self.metadata_path.glob("*.json"):
                with open(metadata_file, 'r') as f:
                    metadata_dict = json.load(f)
                
                # 转换字符串为datetime对象
                for key in ['created_at', 'expires_at', 'last_rotated']:
                    if metadata_dict.get(key):
                        metadata_dict[key] = datetime.fromisoformat(metadata_dict[key])
                
                metadata = SecretMetadata(**metadata_dict)
                self.secrets_metadata[metadata.name] = metadata
                
        except Exception as e:
            self.logger.error(f"Failed to load secrets metadata: {e}")
    
    def _check_file_permissions(self, report: Dict[str, Any]):
        """检查文件权限"""
        check_result = {
            "name": "File Permissions",
            "status": "PASS",
            "details": []
        }
        
        # 检查关键目录权限
        critical_paths = [
            self.vault_path,
            self.secrets_path,
            self.keys_path,
            self.metadata_path
        ]
        
        for path in critical_paths:
            if path.exists():
                stat_info = path.stat()
                mode = stat_info.st_mode & 0o777
                if mode != 0o700:
                    check_result["status"] = "FAIL"
                    check_result["details"].append(f"Insecure permissions on {path}: {oct(mode)}")
                    report["issues"].append(f"Directory {path} has insecure permissions")
        
        report["checks"].append(check_result)
    
    def _check_secret_strength(self, report: Dict[str, Any]):
        """检查密钥强度"""
        check_result = {
            "name": "Secret Strength",
            "status": "PASS",
            "details": []
        }
        
        weak_secrets = []
        for name, metadata in self.secrets_metadata.items():
            if metadata.type == "password":
                secret_value = self.retrieve_secret(name)
                if secret_value and not self._validate_password_strength(secret_value):
                    weak_secrets.append(name)
        
        if weak_secrets:
            check_result["status"] = "WARN"
            check_result["details"] = [f"Weak passwords found: {', '.join(weak_secrets)}"]
            report["recommendations"].append("Consider strengthening weak passwords")
        
        report["checks"].append(check_result)
    
    def _check_expired_secrets(self, report: Dict[str, Any]):
        """检查过期密钥"""
        check_result = {
            "name": "Expired Secrets",
            "status": "PASS",
            "details": []
        }
        
        expired_secrets = []
        for name, metadata in self.secrets_metadata.items():
            if metadata.expires_at and datetime.now() > metadata.expires_at:
                expired_secrets.append(name)
        
        if expired_secrets:
            check_result["status"] = "FAIL"
            check_result["details"] = [f"Expired secrets found: {', '.join(expired_secrets)}"]
            report["issues"].append("Expired secrets must be renewed or removed")
        
        report["checks"].append(check_result)
    
    def _check_rotation_policy(self, report: Dict[str, Any]):
        """检查轮换策略"""
        check_result = {
            "name": "Rotation Policy",
            "status": "PASS",
            "details": []
        }
        
        overdue_rotations = self.check_rotation_needed()
        if overdue_rotations:
            check_result["status"] = "WARN"
            overdue_names = [item["name"] for item in overdue_rotations]
            check_result["details"] = [f"Overdue rotations: {', '.join(overdue_names)}"]
            report["recommendations"].append("Rotate overdue secrets")
        
        report["checks"].append(check_result)
    
    def _check_access_controls(self, report: Dict[str, Any]):
        """检查访问控制"""
        check_result = {
            "name": "Access Controls",
            "status": "PASS",
            "details": []
        }
        
        # 检查是否有过多的高权限密钥
        confidential_count = sum(1 for metadata in self.secrets_metadata.values() 
                               if metadata.access_level == "confidential")
        
        if confidential_count > len(self.secrets_metadata) * 0.5:
            check_result["status"] = "WARN"
            check_result["details"].append("High percentage of confidential secrets")
            report["recommendations"].append("Review access levels for secrets")
        
        report["checks"].append(check_result)
    
    def _check_audit_logs(self, report: Dict[str, Any]):
        """检查审计日志"""
        check_result = {
            "name": "Audit Logs",
            "status": "PASS",
            "details": []
        }
        
        if not self.audit_log_path.exists():
            check_result["status"] = "WARN"
            check_result["details"].append("Audit log file not found")
            report["recommendations"].append("Ensure audit logging is properly configured")
        else:
            # 检查日志文件权限
            stat_info = self.audit_log_path.stat()
            mode = stat_info.st_mode & 0o777
            if mode & 0o022:  # 检查是否其他用户可写
                check_result["status"] = "FAIL"
                check_result["details"].append("Audit log has insecure permissions")
                report["issues"].append("Audit log file permissions are too permissive")
        
        report["checks"].append(check_result)


def main():
    """主函数 - 用于测试"""
    logging.basicConfig(level=logging.INFO)
    
    # 创建安全配置管理器
    secure_manager = SecureConfigManager()
    
    # 测试存储密钥
    secure_manager.store_secret(
        name="database_password",
        value="MySecurePassword123!",
        secret_type="password",
        access_level="confidential",
        expires_days=90,
        rotation_interval_days=30,
        tags=["database", "production"]
    )
    
    # 测试检索密钥
    password = secure_manager.retrieve_secret("database_password")
    print(f"Retrieved password: {password}")
    
    # 运行合规检查
    compliance_report = secure_manager.run_security_compliance_check()
    print(f"Compliance status: {compliance_report['overall_status']}")
    
    print("SecureConfigManager test completed successfully!")


if __name__ == "__main__":
    main()