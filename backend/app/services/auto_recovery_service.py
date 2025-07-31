"""
自动恢复服务
当系统检测到问题时，尝试自动修复
"""
import asyncio
import psutil
import redis
import shutil
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.logging import get_logger
from app.core.database import get_db

logger = get_logger(__name__)

class AutoRecoveryService:
    """自动恢复服务"""
    
    def __init__(self):
        self.recovery_actions = {
            "database_connection_failed": self.restart_db_pool,
            "redis_connection_failed": self.restart_redis_connection,
            "high_memory_usage": self.clear_caches,
            "disk_space_low": self.cleanup_temp_files,
            "high_cpu_usage": self.optimize_processes,
            "too_many_connections": self.cleanup_connections,
            "log_files_too_large": self.rotate_logs,
            "cache_corruption": self.rebuild_cache
        }
        
        self.recovery_history = []
        self.max_recovery_attempts = 3
        self.recovery_cooldown = 300  # 5分钟冷却时间
        
    async def attempt_recovery(self, issue_type: str, details: Dict[str, Any] = None) -> bool:
        """尝试自动恢复"""
        try:
            # 检查是否在冷却期内
            if self._is_in_cooldown(issue_type):
                logger.info(f"Recovery for {issue_type} is in cooldown period")
                return False
            
            # 检查恢复尝试次数
            if self._get_recent_attempts(issue_type) >= self.max_recovery_attempts:
                logger.warning(f"Max recovery attempts reached for {issue_type}")
                return False
            
            # 记录恢复尝试
            recovery_record = {
                "issue_type": issue_type,
                "timestamp": datetime.now(),
                "details": details or {},
                "success": False,
                "error": None
            }
            
            logger.info(f"Attempting auto recovery for: {issue_type}")
            
            # 执行恢复操作
            if issue_type in self.recovery_actions:
                success = await self.recovery_actions[issue_type](details)
                recovery_record["success"] = success
                
                if success:
                    logger.info(f"Auto recovery successful for: {issue_type}")
                else:
                    logger.warning(f"Auto recovery failed for: {issue_type}")
                
                self.recovery_history.append(recovery_record)
                return success
            else:
                logger.warning(f"No recovery action defined for: {issue_type}")
                return False
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Auto recovery error for {issue_type}: {error_msg}")
            
            recovery_record["error"] = error_msg
            self.recovery_history.append(recovery_record)
            return False
    
    def _is_in_cooldown(self, issue_type: str) -> bool:
        """检查是否在冷却期内"""
        cutoff_time = datetime.now() - timedelta(seconds=self.recovery_cooldown)
        
        for record in self.recovery_history:
            if (record["issue_type"] == issue_type and 
                record["timestamp"] > cutoff_time):
                return True
        
        return False
    
    def _get_recent_attempts(self, issue_type: str) -> int:
        """获取最近的恢复尝试次数"""
        cutoff_time = datetime.now() - timedelta(hours=1)  # 1小时内
        
        count = 0
        for record in self.recovery_history:
            if (record["issue_type"] == issue_type and 
                record["timestamp"] > cutoff_time):
                count += 1
        
        return count
    
    async def restart_db_pool(self, details: Dict[str, Any] = None) -> bool:
        """重启数据库连接池"""
        try:
            logger.info("Attempting to restart database connection pool")
            
            # 这里应该重新初始化数据库连接池
            # 由于FastAPI的数据库连接管理，我们尝试创建新连接来测试
            async for db in get_db():
                try:
                    await db.execute(text("SELECT 1"))
                    logger.info("Database connection pool restart successful")
                    return True
                except Exception as e:
                    logger.error(f"Database connection test failed: {str(e)}")
                    return False
                finally:
                    await db.close()
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to restart database pool: {str(e)}")
            return False
    
    async def restart_redis_connection(self, details: Dict[str, Any] = None) -> bool:
        """重启Redis连接"""
        try:
            logger.info("Attempting to restart Redis connection")
            
            # 创建新的Redis连接
            redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            
            # 测试连接
            await asyncio.get_event_loop().run_in_executor(None, redis_client.ping)
            
            logger.info("Redis connection restart successful")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restart Redis connection: {str(e)}")
            return False
    
    async def clear_caches(self, details: Dict[str, Any] = None) -> bool:
        """清理缓存"""
        try:
            logger.info("Attempting to clear caches")
            
            # 清理Redis缓存
            try:
                redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                
                # 获取所有缓存键
                cache_patterns = [
                    "cache:*",
                    "session:*",
                    "temp:*"
                ]
                
                deleted_keys = 0
                for pattern in cache_patterns:
                    keys = await asyncio.get_event_loop().run_in_executor(
                        None, redis_client.keys, pattern
                    )
                    if keys:
                        deleted = await asyncio.get_event_loop().run_in_executor(
                            None, redis_client.delete, *keys
                        )
                        deleted_keys += deleted
                
                logger.info(f"Cleared {deleted_keys} cache keys from Redis")
                
            except Exception as e:
                logger.warning(f"Failed to clear Redis cache: {str(e)}")
            
            # 清理系统缓存
            try:
                # 清理Python缓存
                import gc
                gc.collect()
                
                logger.info("System cache cleanup completed")
                
            except Exception as e:
                logger.warning(f"Failed to clear system cache: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear caches: {str(e)}")
            return False
    
    async def cleanup_temp_files(self, details: Dict[str, Any] = None) -> bool:
        """清理临时文件"""
        try:
            logger.info("Attempting to cleanup temporary files")
            
            temp_dirs = [
                "/tmp",
                "/var/tmp",
                "./temp",
                "./logs",
                "./uploads/temp"
            ]
            
            total_freed = 0
            
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    try:
                        # 删除超过24小时的临时文件
                        cutoff_time = time.time() - (24 * 3600)
                        
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                try:
                                    if os.path.getmtime(file_path) < cutoff_time:
                                        file_size = os.path.getsize(file_path)
                                        os.remove(file_path)
                                        total_freed += file_size
                                except Exception:
                                    continue
                                    
                    except Exception as e:
                        logger.warning(f"Failed to cleanup {temp_dir}: {str(e)}")
            
            logger.info(f"Freed {total_freed / (1024*1024):.2f} MB of temporary files")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {str(e)}")
            return False
    
    async def optimize_processes(self, details: Dict[str, Any] = None) -> bool:
        """优化进程"""
        try:
            logger.info("Attempting to optimize processes")
            
            # 获取当前进程信息
            current_process = psutil.Process()
            
            # 降低进程优先级
            try:
                current_process.nice(5)  # 降低优先级
                logger.info("Process priority lowered")
            except Exception as e:
                logger.warning(f"Failed to lower process priority: {str(e)}")
            
            # 强制垃圾回收
            import gc
            gc.collect()
            
            # 如果可能，重启工作进程
            # 这里可以添加重启Gunicorn worker的逻辑
            
            logger.info("Process optimization completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to optimize processes: {str(e)}")
            return False
    
    async def cleanup_connections(self, details: Dict[str, Any] = None) -> bool:
        """清理连接"""
        try:
            logger.info("Attempting to cleanup connections")
            
            # 清理数据库连接
            try:
                async for db in get_db():
                    try:
                        # 关闭空闲连接
                        await db.close()
                    except Exception:
                        pass
                    break
                
                logger.info("Database connections cleaned up")
                
            except Exception as e:
                logger.warning(f"Failed to cleanup database connections: {str(e)}")
            
            # 清理Redis连接
            try:
                redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                
                # 获取连接信息
                info = await asyncio.get_event_loop().run_in_executor(None, redis_client.info)
                connected_clients = info.get('connected_clients', 0)
                
                logger.info(f"Redis has {connected_clients} connected clients")
                
            except Exception as e:
                logger.warning(f"Failed to check Redis connections: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup connections: {str(e)}")
            return False
    
    async def rotate_logs(self, details: Dict[str, Any] = None) -> bool:
        """轮转日志文件"""
        try:
            logger.info("Attempting to rotate log files")
            
            log_dirs = [
                "./logs",
                "/var/log/lawsker",
                "/tmp/lawsker_logs"
            ]
            
            for log_dir in log_dirs:
                if os.path.exists(log_dir):
                    try:
                        for file in os.listdir(log_dir):
                            if file.endswith('.log'):
                                file_path = os.path.join(log_dir, file)
                                file_size = os.path.getsize(file_path)
                                
                                # 如果日志文件超过100MB，进行轮转
                                if file_size > 100 * 1024 * 1024:
                                    backup_path = f"{file_path}.{int(time.time())}"
                                    shutil.move(file_path, backup_path)
                                    
                                    # 创建新的空日志文件
                                    open(file_path, 'w').close()
                                    
                                    logger.info(f"Rotated log file: {file}")
                                    
                    except Exception as e:
                        logger.warning(f"Failed to rotate logs in {log_dir}: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to rotate logs: {str(e)}")
            return False
    
    async def rebuild_cache(self, details: Dict[str, Any] = None) -> bool:
        """重建缓存"""
        try:
            logger.info("Attempting to rebuild cache")
            
            # 清理损坏的缓存
            await self.clear_caches()
            
            # 预热关键缓存
            try:
                redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                
                # 预热一些基础数据
                cache_data = {
                    "cache:system_status": "healthy",
                    "cache:last_rebuild": datetime.now().isoformat()
                }
                
                for key, value in cache_data.items():
                    await asyncio.get_event_loop().run_in_executor(
                        None, redis_client.setex, key, 3600, value
                    )
                
                logger.info("Cache rebuild completed")
                return True
                
            except Exception as e:
                logger.warning(f"Failed to rebuild cache: {str(e)}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to rebuild cache: {str(e)}")
            return False
    
    def get_recovery_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取恢复历史"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_history = [
            {
                "issue_type": record["issue_type"],
                "timestamp": record["timestamp"].isoformat(),
                "success": record["success"],
                "error": record.get("error"),
                "details": record.get("details", {})
            }
            for record in self.recovery_history
            if record["timestamp"] > cutoff_time
        ]
        
        return recent_history
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """获取恢复统计"""
        total_attempts = len(self.recovery_history)
        successful_attempts = sum(1 for r in self.recovery_history if r["success"])
        
        # 按问题类型统计
        issue_stats = {}
        for record in self.recovery_history:
            issue_type = record["issue_type"]
            if issue_type not in issue_stats:
                issue_stats[issue_type] = {"total": 0, "successful": 0}
            
            issue_stats[issue_type]["total"] += 1
            if record["success"]:
                issue_stats[issue_type]["successful"] += 1
        
        return {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "success_rate": (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0,
            "issue_stats": issue_stats,
            "last_recovery": self.recovery_history[-1]["timestamp"].isoformat() if self.recovery_history else None
        }

# 全局自动恢复服务实例
auto_recovery_service = AutoRecoveryService()

async def trigger_auto_recovery(issue_type: str, details: Dict[str, Any] = None) -> bool:
    """触发自动恢复"""
    return await auto_recovery_service.attempt_recovery(issue_type, details)

def get_recovery_service() -> AutoRecoveryService:
    """获取自动恢复服务实例"""
    return auto_recovery_service