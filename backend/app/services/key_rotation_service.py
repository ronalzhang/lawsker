"""
密钥轮换服务
实现自动密钥轮换和密钥生命周期管理
"""
import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.encryption import key_manager
from app.core.logging import get_logger
from app.models.user import Profile, LawyerQualification

logger = get_logger(__name__)

class KeyRotationService:
    """密钥轮换服务"""
    
    def __init__(self):
        self.rotation_interval_hours = 24 * 7  # 7天轮换一次
        self.backup_retention_days = 30  # 备份保留30天
        self.is_running = False
        
    async def start_rotation_scheduler(self):
        """启动密钥轮换调度器"""
        if self.is_running:
            logger.warning("Key rotation scheduler is already running")
            return
        
        self.is_running = True
        logger.info("Starting key rotation scheduler")
        
        # 设置定时任务
        schedule.every(self.rotation_interval_hours).hours.do(self._rotate_all_keys)
        schedule.every().day.at("02:00").do(self._cleanup_old_keys)
        
        # 运行调度器
        while self.is_running:
            schedule.run_pending()
            await asyncio.sleep(60)  # 每分钟检查一次
    
    def stop_rotation_scheduler(self):
        """停止密钥轮换调度器"""
        self.is_running = False
        schedule.clear()
        logger.info("Key rotation scheduler stopped")
    
    async def _rotate_all_keys(self):
        """轮换所有密钥"""
        try:
            logger.info("Starting key rotation process")
            
            # 轮换字段密钥
            field_keys = ["full_name", "id_card_number", "lawyer_name"]
            for field_name in field_keys:
                await self._rotate_field_key(field_name)
            
            # 轮换系统密钥
            await self._rotate_system_keys()
            
            logger.info("Key rotation process completed successfully")
            
        except Exception as e:
            logger.error(f"Key rotation failed: {str(e)}")
    
    async def _rotate_field_key(self, field_name: str):
        """轮换字段密钥"""
        try:
            logger.info(f"Rotating key for field: {field_name}")
            
            # 备份当前密钥
            await self._backup_field_key(field_name)
            
            # 轮换密钥
            from app.core.encryption import encryption_manager
        success = encryption_manager.rotate_field_key(field_name)
            
            if success:
                logger.info(f"Successfully rotated key for field: {field_name}")
            else:
                logger.error(f"Failed to rotate key for field: {field_name}")
                
        except Exception as e:
            logger.error(f"Field key rotation failed for {field_name}: {str(e)}")
    
    async def _backup_field_key(self, field_name: str):
        """备份字段密钥"""
        try:
            backup_key_id = f"backup_{field_name}_{int(datetime.now().timestamp())}"
            
            # 获取当前密钥
            from app.core.encryption import encryption_manager
        current_key = encryption_manager._get_field_key(field_name)
            
            # 存储备份密钥
            key_manager.store_key(
                backup_key_id,
                current_key.decode('utf-8'),
                ttl=self.backup_retention_days * 24 * 3600
            )
            
            logger.info(f"Backed up key for field: {field_name}")
            
        except Exception as e:
            logger.error(f"Key backup failed for {field_name}: {str(e)}")
    
    async def _rotate_system_keys(self):
        """轮换系统密钥"""
        try:
            logger.info("Rotating system keys")
            
            # 生成新的RSA密钥对
            keypair = key_manager.generate_rsa_keypair()
            
            # 存储新密钥
            timestamp = int(datetime.now().timestamp())
            key_manager.store_key(f"rsa_private_{timestamp}", keypair['private_key'])
            key_manager.store_key(f"rsa_public_{timestamp}", keypair['public_key'])
            
            logger.info("System keys rotated successfully")
            
        except Exception as e:
            logger.error(f"System key rotation failed: {str(e)}")
    
    async def _cleanup_old_keys(self):
        """清理过期密钥"""
        try:
            logger.info("Starting key cleanup process")
            
            # 清理过期的备份密钥
            cutoff_time = datetime.now() - timedelta(days=self.backup_retention_days)
            cutoff_timestamp = int(cutoff_time.timestamp())
            
            # 这里应该实现具体的清理逻辑
            # 由于Redis键的TTL机制，过期键会自动清理
            
            logger.info("Key cleanup process completed")
            
        except Exception as e:
            logger.error(f"Key cleanup failed: {str(e)}")
    
    async def emergency_key_rotation(self, field_names: Optional[List[str]] = None):
        """紧急密钥轮换"""
        try:
            logger.warning("Starting emergency key rotation")
            
            if field_names is None:
                field_names = ["full_name", "id_card_number", "lawyer_name"]
            
            for field_name in field_names:
                await self._rotate_field_key(field_name)
            
            # 轮换系统密钥
            await self._rotate_system_keys()
            
            logger.warning("Emergency key rotation completed")
            
        except Exception as e:
            logger.error(f"Emergency key rotation failed: {str(e)}")
    
    async def get_key_status(self) -> Dict[str, Any]:
        """获取密钥状态"""
        try:
            status = {
                "rotation_enabled": self.is_running,
                "last_rotation": None,
                "next_rotation": None,
                "field_keys": {},
                "system_keys": {}
            }
            
            # 检查字段密钥状态
            field_keys = ["full_name", "id_card_number", "lawyer_name"]
            for field_name in field_keys:
                try:
                    from app.core.encryption import encryption_manager
        key = encryption_manager._get_field_key(field_name)
                    status["field_keys"][field_name] = {
                        "exists": True,
                        "length": len(key)
                    }
                except Exception:
                    status["field_keys"][field_name] = {
                        "exists": False,
                        "length": 0
                    }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get key status: {str(e)}")
            return {"error": str(e)}


class DataMigrationService:
    """数据迁移服务 - 用于密钥轮换后的数据重新加密"""
    
    def __init__(self):
        self.batch_size = 100
    
    async def migrate_encrypted_data(self, field_name: str, old_key: str, new_key: str):
        """迁移加密数据"""
        try:
            logger.info(f"Starting data migration for field: {field_name}")
            
            db = next(get_db())
            
            if field_name in ["full_name", "id_card_number"]:
                await self._migrate_profile_data(db, field_name, old_key, new_key)
            elif field_name in ["lawyer_name"]:
                await self._migrate_lawyer_data(db, field_name, old_key, new_key)
            
            logger.info(f"Data migration completed for field: {field_name}")
            
        except Exception as e:
            logger.error(f"Data migration failed for {field_name}: {str(e)}")
    
    async def _migrate_profile_data(self, db: Session, field_name: str, old_key: str, new_key: str):
        """迁移用户资料数据"""
        try:
            # 分批处理数据
            offset = 0
            while True:
                profiles = db.query(Profile).offset(offset).limit(self.batch_size).all()
                
                if not profiles:
                    break
                
                for profile in profiles:
                    # 使用旧密钥解密数据
                    if field_name == "full_name" and profile._encrypted_full_name:
                        decrypted_data = self._decrypt_with_key(
                            profile._encrypted_full_name, old_key
                        )
                        # 使用新密钥重新加密
                        profile._encrypted_full_name = self._encrypt_with_key(
                            decrypted_data, new_key
                        )
                    
                    elif field_name == "id_card_number" and profile._encrypted_id_card_number:
                        decrypted_data = self._decrypt_with_key(
                            profile._encrypted_id_card_number, old_key
                        )
                        profile._encrypted_id_card_number = self._encrypt_with_key(
                            decrypted_data, new_key
                        )
                
                db.commit()
                offset += self.batch_size
                
                # 避免长时间占用数据库连接
                await asyncio.sleep(0.1)
                
        except Exception as e:
            db.rollback()
            raise e
    
    async def _migrate_lawyer_data(self, db: Session, field_name: str, old_key: str, new_key: str):
        """迁移律师资质数据"""
        try:
            offset = 0
            while True:
                qualifications = db.query(LawyerQualification).offset(offset).limit(self.batch_size).all()
                
                if not qualifications:
                    break
                
                for qualification in qualifications:
                    if field_name == "lawyer_name" and qualification._encrypted_lawyer_name:
                        decrypted_data = self._decrypt_with_key(
                            qualification._encrypted_lawyer_name, old_key
                        )
                        qualification._encrypted_lawyer_name = self._encrypt_with_key(
                            decrypted_data, new_key
                        )
                    
                    elif field_name == "id_card_number" and qualification._encrypted_id_card_number:
                        decrypted_data = self._decrypt_with_key(
                            qualification._encrypted_id_card_number, old_key
                        )
                        qualification._encrypted_id_card_number = self._encrypt_with_key(
                            decrypted_data, new_key
                        )
                
                db.commit()
                offset += self.batch_size
                await asyncio.sleep(0.1)
                
        except Exception as e:
            db.rollback()
            raise e
    
    def _decrypt_with_key(self, encrypted_data: str, key: str) -> str:
        """使用指定密钥解密数据"""
        # 这里应该实现具体的解密逻辑
        # 暂时返回原数据，实际实现需要根据加密算法调整
        return encrypted_data
    
    def _encrypt_with_key(self, data: str, key: str) -> str:
        """使用指定密钥加密数据"""
        # 这里应该实现具体的加密逻辑
        # 暂时返回原数据，实际实现需要根据加密算法调整
        return data


# 全局服务实例
key_rotation_service = KeyRotationService()
data_migration_service = DataMigrationService()

# 启动密钥轮换服务的函数
async def start_key_rotation():
    """启动密钥轮换服务"""
    await key_rotation_service.start_rotation_scheduler()

def stop_key_rotation():
    """停止密钥轮换服务"""
    key_rotation_service.stop_rotation_scheduler()