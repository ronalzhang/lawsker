"""
数据加密保护系统测试
测试AES-256加密、密钥管理和数据脱敏功能
"""
import os
import pytest
import asyncio
from datetime import datetime

# 设置测试环境变量
os.environ["ENCRYPTION_MASTER_KEY"] = "test_master_key_for_encryption_testing_12345"

from app.core.encryption import (
    EncryptionManager, 
    DataMasking, 
    KeyManager,
    encrypt_sensitive_data,
    decrypt_sensitive_data,
    mask_sensitive_data
)
from app.services.key_rotation_service import KeyRotationService, DataMigrationService

class TestEncryptionManager:
    """测试加密管理器"""
    
    def setup_method(self):
        """测试前设置"""
        self.encryption_manager = EncryptionManager()
    
    def test_field_encryption_decryption(self):
        """测试字段加密解密"""
        test_data = "张三"
        field_name = "full_name"
        
        # 加密
        encrypted_data = self.encryption_manager.encrypt_field(test_data, field_name)
        assert encrypted_data != test_data
        assert len(encrypted_data) > 0
        
        # 解密
        decrypted_data = self.encryption_manager.decrypt_field(encrypted_data, field_name)
        assert decrypted_data == test_data
    
    def test_json_encryption_decryption(self):
        """测试JSON加密解密"""
        test_data = {
            "name": "张三",
            "id_card": "110101199001011234",
            "phone": "13800138000"
        }
        
        # 加密
        encrypted_data = self.encryption_manager.encrypt_json(test_data)
        assert encrypted_data != str(test_data)
        
        # 解密
        decrypted_data = self.encryption_manager.decrypt_json(encrypted_data)
        assert decrypted_data == test_data
    
    def test_field_key_rotation(self):
        """测试字段密钥轮换"""
        field_name = "test_field"
        
        # 获取原始密钥
        original_key = self.encryption_manager._get_field_key(field_name)
        
        # 轮换密钥
        success = self.encryption_manager.rotate_field_key(field_name)
        assert success
        
        # 获取新密钥
        new_key = self.encryption_manager._get_field_key(field_name)
        
        # 验证密钥已更改
        assert original_key != new_key
    
    def test_empty_data_handling(self):
        """测试空数据处理"""
        # 测试空字符串
        encrypted_empty = self.encryption_manager.encrypt_field("", "test_field")
        assert encrypted_empty == ""
        
        # 测试None
        encrypted_none = self.encryption_manager.encrypt_field(None, "test_field")
        assert encrypted_none is None


class TestDataMasking:
    """测试数据脱敏"""
    
    def test_phone_masking(self):
        """测试手机号脱敏"""
        phone = "13800138000"
        masked = DataMasking.mask_phone(phone)
        assert masked == "138****8000"
        
        # 测试短号码
        short_phone = "123456"
        masked_short = DataMasking.mask_phone(short_phone)
        assert masked_short == "123456"  # 太短不脱敏
    
    def test_email_masking(self):
        """测试邮箱脱敏"""
        email = "zhangsan@example.com"
        masked = DataMasking.mask_email(email)
        assert masked == "z******n@example.com"
        
        # 测试短邮箱
        short_email = "ab@test.com"
        masked_short = DataMasking.mask_email(short_email)
        assert masked_short == "ab@test.com"  # 太短不脱敏
    
    def test_id_card_masking(self):
        """测试身份证号脱敏"""
        id_card = "110101199001011234"
        masked = DataMasking.mask_id_card(id_card)
        assert masked == "1101**********1234"
    
    def test_name_masking(self):
        """测试姓名脱敏"""
        # 测试三字姓名
        name = "张三丰"
        masked = DataMasking.mask_name(name)
        assert masked == "张*丰"
        
        # 测试两字姓名
        name2 = "李四"
        masked2 = DataMasking.mask_name(name2)
        assert masked2 == "李*"
    
    def test_custom_masking(self):
        """测试自定义脱敏"""
        data = "1234567890"
        masked = DataMasking.mask_custom(data, start=2, end=2, mask_char='*')
        assert masked == "12******90"


class TestKeyManager:
    """测试密钥管理器"""
    
    def setup_method(self):
        """测试前设置"""
        self.key_manager = KeyManager()
    
    def test_rsa_keypair_generation(self):
        """测试RSA密钥对生成"""
        keypair = self.key_manager.generate_rsa_keypair()
        
        assert "private_key" in keypair
        assert "public_key" in keypair
        assert keypair["private_key"].startswith("-----BEGIN PRIVATE KEY-----")
        assert keypair["public_key"].startswith("-----BEGIN PUBLIC KEY-----")
    
    def test_key_storage_retrieval(self):
        """测试密钥存储和检索"""
        key_id = "test_key_123"
        key_data = "test_key_data_12345"
        
        # 存储密钥
        success = self.key_manager.store_key(key_id, key_data, ttl=3600)
        assert success
        
        # 检索密钥
        retrieved_key = self.key_manager.retrieve_key(key_id)
        assert retrieved_key == key_data
        
        # 删除密钥
        deleted = self.key_manager.delete_key(key_id)
        assert deleted
        
        # 验证密钥已删除
        retrieved_after_delete = self.key_manager.retrieve_key(key_id)
        assert retrieved_after_delete is None


class TestConvenienceFunctions:
    """测试便捷函数"""
    
    def test_encrypt_decrypt_sensitive_data(self):
        """测试敏感数据加密解密便捷函数"""
        test_data = "敏感信息123"
        field_name = "sensitive_field"
        
        # 加密
        encrypted = encrypt_sensitive_data(test_data, field_name)
        assert encrypted != test_data
        
        # 解密
        decrypted = decrypt_sensitive_data(encrypted, field_name)
        assert decrypted == test_data
    
    def test_mask_sensitive_data_function(self):
        """测试敏感数据脱敏便捷函数"""
        # 测试手机号脱敏
        phone = "13800138000"
        masked_phone = mask_sensitive_data(phone, "phone")
        assert masked_phone == "138****8000"
        
        # 测试邮箱脱敏
        email = "test@example.com"
        masked_email = mask_sensitive_data(email, "email")
        assert masked_email == "t**t@example.com"
        
        # 测试未知类型
        unknown_data = "unknown_data"
        masked_unknown = mask_sensitive_data(unknown_data, "unknown_type")
        assert masked_unknown == unknown_data  # 未知类型不脱敏


@pytest.mark.asyncio
class TestKeyRotationService:
    """测试密钥轮换服务"""
    
    def setup_method(self):
        """测试前设置"""
        self.key_rotation_service = KeyRotationService()
    
    async def test_emergency_key_rotation(self):
        """测试紧急密钥轮换"""
        field_names = ["test_field_1", "test_field_2"]
        
        # 执行紧急密钥轮换
        await self.key_rotation_service.emergency_key_rotation(field_names)
        
        # 验证轮换成功（这里只是确保没有异常）
        assert True
    
    async def test_get_key_status(self):
        """测试获取密钥状态"""
        status = await self.key_rotation_service.get_key_status()
        
        assert "rotation_enabled" in status
        assert "field_keys" in status
        assert "system_keys" in status
        assert isinstance(status["field_keys"], dict)


class TestDataMigrationService:
    """测试数据迁移服务"""
    
    def setup_method(self):
        """测试前设置"""
        self.migration_service = DataMigrationService()
    
    def test_decrypt_encrypt_with_key(self):
        """测试使用指定密钥加密解密"""
        test_data = "test_data_123"
        test_key = "test_key_456"
        
        # 加密
        encrypted = self.migration_service._encrypt_with_key(test_data, test_key)
        assert encrypted is not None
        
        # 解密
        decrypted = self.migration_service._decrypt_with_key(encrypted, test_key)
        assert decrypted is not None


def test_integration_scenario():
    """集成测试场景"""
    # 模拟完整的加密流程
    encryption_manager = EncryptionManager()
    
    # 1. 加密用户敏感信息
    user_data = {
        "full_name": "张三",
        "id_card_number": "110101199001011234",
        "phone_number": "13800138000",
        "email": "zhangsan@example.com"
    }
    
    encrypted_data = {}
    for field, value in user_data.items():
        encrypted_data[field] = encryption_manager.encrypt_field(value, field)
    
    # 2. 验证加密成功
    for field, encrypted_value in encrypted_data.items():
        assert encrypted_value != user_data[field]
    
    # 3. 解密验证
    decrypted_data = {}
    for field, encrypted_value in encrypted_data.items():
        decrypted_data[field] = encryption_manager.decrypt_field(encrypted_value, field)
    
    # 4. 验证解密正确
    assert decrypted_data == user_data
    
    # 5. 测试数据脱敏
    masked_data = {}
    for field, value in user_data.items():
        if field == "phone_number":
            masked_data[field] = mask_sensitive_data(value, "phone")
        elif field == "email":
            masked_data[field] = mask_sensitive_data(value, "email")
        elif field == "id_card_number":
            masked_data[field] = mask_sensitive_data(value, "id_card")
        elif field == "full_name":
            masked_data[field] = mask_sensitive_data(value, "name")
        else:
            masked_data[field] = value
    
    # 6. 验证脱敏效果
    assert masked_data["phone_number"] == "138****8000"
    assert masked_data["email"] == "z******n@example.com"
    assert masked_data["id_card_number"] == "1101**********1234"
    assert masked_data["full_name"] == "张*"


if __name__ == "__main__":
    # 运行测试
    print("开始测试数据加密保护系统...")
    
    # 运行同步测试
    test_integration_scenario()
    print("✅ 集成测试通过")
    
    # 运行加密管理器测试
    test_encryption = TestEncryptionManager()
    test_encryption.setup_method()
    test_encryption.test_field_encryption_decryption()
    test_encryption.test_json_encryption_decryption()
    test_encryption.test_field_key_rotation()
    test_encryption.test_empty_data_handling()
    print("✅ 加密管理器测试通过")
    
    # 运行数据脱敏测试
    test_masking = TestDataMasking()
    test_masking.test_phone_masking()
    test_masking.test_email_masking()
    test_masking.test_id_card_masking()
    test_masking.test_name_masking()
    test_masking.test_custom_masking()
    print("✅ 数据脱敏测试通过")
    
    # 运行密钥管理器测试
    test_key_manager = TestKeyManager()
    test_key_manager.setup_method()
    test_key_manager.test_rsa_keypair_generation()
    test_key_manager.test_key_storage_retrieval()
    print("✅ 密钥管理器测试通过")
    
    # 运行便捷函数测试
    test_functions = TestConvenienceFunctions()
    test_functions.test_encrypt_decrypt_sensitive_data()
    test_functions.test_mask_sensitive_data_function()
    print("✅ 便捷函数测试通过")
    
    print("🎉 所有测试通过！数据加密保护系统功能正常")