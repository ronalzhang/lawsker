"""
数据加密保护系统
提供AES-256加密、密钥管理和数据脱敏功能
"""
import os
import base64
import hashlib
import secrets
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import redis
from app.core.logging import get_logger

logger = get_logger(__name__)

class EncryptionManager:
    """加密管理器"""
    
    def __init__(self, master_key: Optional[str] = None, redis_url: str = "redis://localhost:6379/3"):
        self.master_key = master_key or os.environ.get("ENCRYPTION_MASTER_KEY")
        if not self.master_key:
            raise ValueError("Master key is required for encryption")
        
        # Redis连接用于密钥存储
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)}")
            self.redis_client = None
        
        # 内存密钥缓存
        self._key_cache = {}
        self._cache_ttl = 3600  # 1小时
        
        # 初始化主密钥
        self._init_master_key()
    
    def _init_master_key(self):
        """初始化主密钥"""
        # 从主密钥派生加密密钥
        salt = b'lawsker_encryption_salt'  # 在生产环境中应该使用随机盐
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        self.fernet = Fernet(key)
    
    def encrypt_field(self, data: str, field_name: str = "default") -> str:
        """加密字段数据"""
        try:
            if not data:
                return data
            
            # 获取字段专用密钥
            field_key = self._get_field_key(field_name)
            fernet = Fernet(field_key)
            
            # 加密数据
            encrypted_data = fernet.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Field encryption failed: {str(e)}")
            raise
    
    def decrypt_field(self, encrypted_data: str, field_name: str = "default") -> str:
        """解密字段数据"""
        try:
            if not encrypted_data:
                return encrypted_data
            
            # 获取字段专用密钥
            field_key = self._get_field_key(field_name)
            fernet = Fernet(field_key)
            
            # 解密数据
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Field decryption failed: {str(e)}")
            raise
    
    def _get_field_key(self, field_name: str) -> bytes:
        """获取字段专用密钥"""
        cache_key = f"field_key_{field_name}"
        
        # 检查内存缓存
        if cache_key in self._key_cache:
            cached_data = self._key_cache[cache_key]
            if datetime.now() < cached_data['expires']:
                return cached_data['key']
        
        # 检查Redis缓存
        if self.redis_client:
            try:
                cached_key = self.redis_client.get(cache_key)
                if cached_key:
                    key_bytes = base64.urlsafe_b64decode(cached_key)
                    self._cache_key(cache_key, key_bytes)
                    return key_bytes
            except Exception as e:
                logger.warning(f"Redis key retrieval failed: {str(e)}")
        
        # 生成新的字段密钥
        field_key = self._generate_field_key(field_name)
        self._cache_key(cache_key, field_key)
        
        # 存储到Redis
        if self.redis_client:
            try:
                encoded_key = base64.urlsafe_b64encode(field_key).decode('utf-8')
                self.redis_client.setex(cache_key, self._cache_ttl, encoded_key)
            except Exception as e:
                logger.warning(f"Redis key storage failed: {str(e)}")
        
        return field_key
    
    def _generate_field_key(self, field_name: str) -> bytes:
        """生成字段专用密钥"""
        # 使用主密钥和字段名生成专用密钥
        field_salt = hashlib.sha256(f"field_{field_name}".encode()).digest()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=field_salt,
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
    
    def _cache_key(self, cache_key: str, key_bytes: bytes):
        """缓存密钥到内存"""
        self._key_cache[cache_key] = {
            'key': key_bytes,
            'expires': datetime.now() + timedelta(seconds=self._cache_ttl)
        }
    
    def encrypt_json(self, data: Dict[str, Any]) -> str:
        """加密JSON数据"""
        try:
            import json
            json_str = json.dumps(data, ensure_ascii=False)
            return self.fernet.encrypt(json_str.encode('utf-8')).decode('utf-8')
        except Exception as e:
            logger.error(f"JSON encryption failed: {str(e)}")
            raise
    
    def decrypt_json(self, encrypted_data: str) -> Dict[str, Any]:
        """解密JSON数据"""
        try:
            import json
            decrypted_bytes = self.fernet.decrypt(encrypted_data.encode('utf-8'))
            return json.loads(decrypted_bytes.decode('utf-8'))
        except Exception as e:
            logger.error(f"JSON decryption failed: {str(e)}")
            raise
    
    def rotate_field_key(self, field_name: str) -> bool:
        """轮换字段密钥"""
        try:
            cache_key = f"field_key_{field_name}"
            
            # 清除缓存
            if cache_key in self._key_cache:
                del self._key_cache[cache_key]
            
            if self.redis_client:
                self.redis_client.delete(cache_key)
            
            logger.info(f"Field key rotated for: {field_name}")
            return True
            
        except Exception as e:
            logger.error(f"Key rotation failed: {str(e)}")
            return False

class DataMasking:
    """数据脱敏工具"""
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """手机号脱敏"""
        if not phone or len(phone) < 7:
            return phone
        return phone[:3] + "****" + phone[-4:]
    
    @staticmethod
    def mask_email(email: str) -> str:
        """邮箱脱敏"""
        if not email or '@' not in email:
            return email
        
        local, domain = email.split('@', 1)
        if len(local) <= 2:
            masked_local = local
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def mask_id_card(id_card: str) -> str:
        """身份证号脱敏"""
        if not id_card or len(id_card) < 8:
            return id_card
        return id_card[:4] + "**********" + id_card[-4:]
    
    @staticmethod
    def mask_bank_card(bank_card: str) -> str:
        """银行卡号脱敏"""
        if not bank_card or len(bank_card) < 8:
            return bank_card
        return bank_card[:4] + "****" + bank_card[-4:]
    
    @staticmethod
    def mask_name(name: str) -> str:
        """姓名脱敏"""
        if not name:
            return name
        if len(name) <= 2:
            return name[0] + '*'
        return name[0] + '*' * (len(name) - 2) + name[-1]
    
    @staticmethod
    def mask_address(address: str) -> str:
        """地址脱敏"""
        if not address or len(address) < 6:
            return address
        return address[:6] + "****"
    
    @staticmethod
    def mask_custom(data: str, start: int = 0, end: int = 0, mask_char: str = '*') -> str:
        """自定义脱敏"""
        if not data:
            return data
        
        length = len(data)
        if start + end >= length:
            return mask_char * length
        
        return data[:start] + mask_char * (length - start - end) + data[length - end:] if end > 0 else data[:start] + mask_char * (length - start)

class EncryptedField:
    """加密字段描述符"""
    
    def __init__(self, field_name: str, encryption_manager: EncryptionManager):
        self.field_name = field_name
        self.encryption_manager = encryption_manager
        self.private_name = f'_encrypted_{field_name}'
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        
        encrypted_value = getattr(obj, self.private_name, None)
        if encrypted_value is None:
            return None
        
        try:
            return self.encryption_manager.decrypt_field(encrypted_value, self.field_name)
        except Exception as e:
            logger.error(f"Failed to decrypt field {self.field_name}: {str(e)}")
            return None
    
    def __set__(self, obj, value):
        if value is None:
            setattr(obj, self.private_name, None)
            return
        
        try:
            encrypted_value = self.encryption_manager.encrypt_field(str(value), self.field_name)
            setattr(obj, self.private_name, encrypted_value)
        except Exception as e:
            logger.error(f"Failed to encrypt field {self.field_name}: {str(e)}")
            setattr(obj, self.private_name, None)

class KeyManager:
    """密钥管理器"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/3"):
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)}")
            self.redis_client = None
        
        self.memory_keys = {}
    
    def generate_rsa_keypair(self, key_size: int = 2048) -> Dict[str, str]:
        """生成RSA密钥对"""
        try:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
                backend=default_backend()
            )
            
            public_key = private_key.public_key()
            
            # 序列化私钥
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # 序列化公钥
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            return {
                'private_key': private_pem.decode('utf-8'),
                'public_key': public_pem.decode('utf-8')
            }
            
        except Exception as e:
            logger.error(f"RSA keypair generation failed: {str(e)}")
            raise
    
    def store_key(self, key_id: str, key_data: str, ttl: int = 86400) -> bool:
        """存储密钥"""
        try:
            if self.redis_client:
                self.redis_client.setex(f"key:{key_id}", ttl, key_data)
            else:
                self.memory_keys[key_id] = {
                    'data': key_data,
                    'expires': datetime.now() + timedelta(seconds=ttl)
                }
            
            logger.info(f"Key stored: {key_id}")
            return True
            
        except Exception as e:
            logger.error(f"Key storage failed: {str(e)}")
            return False
    
    def retrieve_key(self, key_id: str) -> Optional[str]:
        """检索密钥"""
        try:
            if self.redis_client:
                return self.redis_client.get(f"key:{key_id}")
            else:
                key_info = self.memory_keys.get(key_id)
                if key_info and datetime.now() < key_info['expires']:
                    return key_info['data']
                elif key_info:
                    del self.memory_keys[key_id]
            
            return None
            
        except Exception as e:
            logger.error(f"Key retrieval failed: {str(e)}")
            return None
    
    def delete_key(self, key_id: str) -> bool:
        """删除密钥"""
        try:
            if self.redis_client:
                result = self.redis_client.delete(f"key:{key_id}")
                return result > 0
            else:
                if key_id in self.memory_keys:
                    del self.memory_keys[key_id]
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Key deletion failed: {str(e)}")
            return False
    
    def rotate_keys(self, key_pattern: str = "*") -> int:
        """批量轮换密钥"""
        try:
            rotated_count = 0
            
            if self.redis_client:
                keys = self.redis_client.keys(f"key:{key_pattern}")
                for key in keys:
                    # 生成新密钥
                    new_key = secrets.token_urlsafe(32)
                    self.redis_client.set(key, new_key)
                    rotated_count += 1
            else:
                # 内存密钥轮换
                for key_id in list(self.memory_keys.keys()):
                    new_key = secrets.token_urlsafe(32)
                    self.memory_keys[key_id]['data'] = new_key
                    rotated_count += 1
            
            logger.info(f"Rotated {rotated_count} keys")
            return rotated_count
            
        except Exception as e:
            logger.error(f"Key rotation failed: {str(e)}")
            return 0

# 全局实例
encryption_manager = EncryptionManager()
key_manager = KeyManager()
data_masking = DataMasking()

# 便捷函数
def encrypt_sensitive_data(data: str, field_name: str = "default") -> str:
    """加密敏感数据"""
    return encryption_manager.encrypt_field(data, field_name)

def decrypt_sensitive_data(encrypted_data: str, field_name: str = "default") -> str:
    """解密敏感数据"""
    return encryption_manager.decrypt_field(encrypted_data, field_name)

def mask_sensitive_data(data: str, data_type: str) -> str:
    """脱敏敏感数据"""
    masking_functions = {
        'phone': data_masking.mask_phone,
        'email': data_masking.mask_email,
        'id_card': data_masking.mask_id_card,
        'bank_card': data_masking.mask_bank_card,
        'name': data_masking.mask_name,
        'address': data_masking.mask_address
    }
    
    mask_func = masking_functions.get(data_type)
    if mask_func:
        return mask_func(data)
    
    return data

def create_encrypted_field(field_name: str) -> EncryptedField:
    """创建加密字段"""
    return EncryptedField(field_name, encryption_manager)