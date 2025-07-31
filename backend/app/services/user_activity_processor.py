"""
用户活动处理器
定时处理Redis队列中的用户活动数据
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


class UserActivityProcessor:
    """用户活动处理器"""
    
    def __init__(self):
        self.redis_client = None
        self.batch_size = 50
        self.process_interval = 20  # 20秒处理一次
        self.queue_name = "user_activities_queue"
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
        """启动用户活动处理循环"""
        self.running = True
        logger.info("用户活动处理器启动")
        
        while self.running:
            try:
                await self._process_pending_activities()
                await asyncio.sleep(self.process_interval)
            except Exception as e:
                logger.error(f"处理用户活动时发生错误: {str(e)}")
                await asyncio.sleep(5)  # 错误时短暂等待
    
    async def stop_processing(self):
        """停止活动处理"""
        self.running = False
        logger.info("用户活动处理器停止")
    
    async def _process_pending_activities(self):
        """处理待处理的用户活动"""
        redis_client = await self._get_redis_client()
        if not redis_client:
            return
            
        try:
            # 检查队列长度
            queue_length = await redis_client.llen(self.queue_name)
            if queue_length == 0:
                return
                
            logger.info(f"处理待处理用户活动: {queue_length}条")
            
            # 分批处理
            processed_count = 0
            while True:
                activities = await self._fetch_batch_from_queue(redis_client)
                if not activities:
                    break
                    
                await self._batch_insert_to_database(activities)
                processed_count += len(activities)
                
                # 避免长时间占用
                if processed_count >= 500:
                    break
                    
            if processed_count > 0:
                logger.info(f"成功处理用户活动: {processed_count}条")
                
        except Exception as e:
            logger.error(f"处理待处理用户活动失败: {str(e)}")
    
    async def _fetch_batch_from_queue(self, redis_client) -> List[Dict[str, Any]]:
        """从队列中获取一批活动数据"""
        activities = []
        try:
            for _ in range(self.batch_size):
                activity_data = await redis_client.rpop(self.queue_name)
                if activity_data:
                    try:
                        parsed_activity = json.loads(activity_data)
                        activities.append(parsed_activity)
                    except json.JSONDecodeError as e:
                        logger.error(f"解析用户活动数据失败: {str(e)}")
                else:
                    break
        except Exception as e:
            logger.error(f"从Redis队列获取用户活动数据失败: {str(e)}")
            
        return activities
    
    async def _batch_insert_to_database(self, activities: List[Dict[str, Any]]):
        """批量插入用户活动到数据库"""
        if not activities:
            return
            
        try:
            async with AsyncSessionLocal() as db:
                insert_query = text("""
                    INSERT INTO user_activity_logs (
                        user_id, action, resource_type, resource_id,
                        details, ip_address, user_agent, created_at
                    ) VALUES (
                        :user_id, :action, :resource_type, :resource_id,
                        :details, :ip_address, :user_agent,
                        COALESCE(:created_at::timestamp, NOW())
                    )
                """)
                
                # 处理details字段的JSON序列化
                for activity in activities:
                    if activity.get('details'):
                        activity['details'] = json.dumps(activity['details'], ensure_ascii=False)
                
                # 批量执行插入
                await db.execute(insert_query, activities)
                await db.commit()
                
        except Exception as e:
            logger.error(f"批量插入用户活动到数据库失败: {str(e)}")
            await db.rollback()
            raise
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        redis_client = await self._get_redis_client()
        if not redis_client:
            return {"status": "redis_unavailable"}
            
        try:
            queue_length = await redis_client.llen(self.queue_name)
            return {
                "status": "running" if self.running else "stopped",
                "queue_length": queue_length,
                "batch_size": self.batch_size,
                "process_interval": self.process_interval
            }
        except Exception as e:
            logger.error(f"获取用户活动队列状态失败: {str(e)}")
            return {"status": "error", "error": str(e)}


# 全局处理器实例
user_activity_processor = UserActivityProcessor()


async def start_user_activity_processor():
    """启动用户活动处理器"""
    asyncio.create_task(user_activity_processor.start_processing())


async def stop_user_activity_processor():
    """停止用户活动处理器"""
    await user_activity_processor.stop_processing()


async def get_user_activity_queue_status():
    """获取用户活动队列状态"""
    return await user_activity_processor.get_queue_status()