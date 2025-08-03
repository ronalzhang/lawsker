"""
访问日志处理服务
定时处理Redis队列中的访问日志数据
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)


class AccessLogProcessor:
    """访问日志处理器"""
    
    def __init__(self):
        self.redis_client = None
        self.batch_size = 100
        self.process_interval = 30  # 30秒处理一次
        self.running = False
        
    async def _get_redis_client(self):
        """获取Redis客户端"""
        if self.redis_client is None:
            try:
                self.redis_client = redis.from_url(settings.REDIS_URL)
                await self.redis_client.ping()
            except Exception as e:
                logger.error(f"Redis连接失败: {str(e)}")
                self.redis_client = None
        return self.redis_client
    
    async def start_processing(self):
        """启动日志处理循环"""
        self.running = True
        logger.info("访问日志处理器启动")
        
        while self.running:
            try:
                await self._process_pending_logs()
                await asyncio.sleep(self.process_interval)
            except Exception as e:
                logger.error(f"处理访问日志时发生错误: {str(e)}")
                await asyncio.sleep(5)  # 错误时短暂等待
    
    async def stop_processing(self):
        """停止日志处理"""
        self.running = False
        logger.info("访问日志处理器停止")
    
    async def _process_pending_logs(self):
        """处理待处理的日志"""
        redis_client = await self._get_redis_client()
        if not redis_client:
            return
            
        try:
            # 检查队列长度
            queue_length = await redis_client.llen("access_logs_queue")
            if queue_length == 0:
                return
                
            logger.info(f"处理待处理访问日志: {queue_length}条")
            
            # 分批处理
            processed_count = 0
            while True:
                logs = await self._fetch_batch_from_queue(redis_client)
                if not logs:
                    break
                    
                await self._batch_insert_to_database(logs)
                processed_count += len(logs)
                
                # 避免长时间占用
                if processed_count >= 1000:
                    break
                    
            if processed_count > 0:
                logger.info(f"成功处理访问日志: {processed_count}条")
                
        except Exception as e:
            logger.error(f"处理待处理日志失败: {str(e)}")
    
    async def _fetch_batch_from_queue(self, redis_client) -> List[Dict[str, Any]]:
        """从队列中获取一批日志数据"""
        logs = []
        try:
            for _ in range(self.batch_size):
                log_data = await redis_client.rpop("access_logs_queue")
                if log_data:
                    try:
                        parsed_log = json.loads(log_data)
                        logs.append(parsed_log)
                    except json.JSONDecodeError as e:
                        logger.error(f"解析日志数据失败: {str(e)}")
                else:
                    break
        except Exception as e:
            logger.error(f"从Redis队列获取数据失败: {str(e)}")
            
        return logs
    
    async def _batch_insert_to_database(self, logs: List[Dict[str, Any]]):
        """批量插入日志到数据库"""
        if not logs:
            return
            
        try:
            async with AsyncSessionLocal() as db:
                insert_query = text("""
                    INSERT INTO access_logs (
                        user_id, session_id, ip_address, user_agent, referer,
                        request_path, request_method, status_code, response_time,
                        device_type, browser, os, country, region, city, created_at
                    ) VALUES (
                        :user_id, :session_id, :ip_address, :user_agent, :referer,
                        :request_path, :request_method, :status_code, :response_time,
                        :device_type, :browser, :os, :country, :region, :city, 
                        COALESCE(:created_at, NOW())
                    )
                """)
                
                # 批量执行插入
                await db.execute(insert_query, logs)
                await db.commit()
                
        except Exception as e:
            logger.error(f"批量插入访问日志到数据库失败: {str(e)}")
            await db.rollback()
            raise
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        redis_client = await self._get_redis_client()
        if not redis_client:
            return {"status": "redis_unavailable"}
            
        try:
            queue_length = await redis_client.llen("access_logs_queue")
            return {
                "status": "running" if self.running else "stopped",
                "queue_length": queue_length,
                "batch_size": self.batch_size,
                "process_interval": self.process_interval
            }
        except Exception as e:
            logger.error(f"获取队列状态失败: {str(e)}")
            return {"status": "error", "error": str(e)}


# 全局处理器实例
access_log_processor = AccessLogProcessor()


async def start_access_log_processor():
    """启动访问日志处理器"""
    asyncio.create_task(access_log_processor.start_processing())


async def stop_access_log_processor():
    """停止访问日志处理器"""
    await access_log_processor.stop_processing()


async def get_access_log_queue_status():
    """获取访问日志队列状态"""
    return await access_log_processor.get_queue_status()