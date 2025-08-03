"""
用户行为追踪服务
记录用户的关键操作行为，用于用户行为分析
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)


class ActivityType(str, Enum):
    """用户活动类型枚举"""
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    
    # 案件相关
    CASE_CREATE = "case_create"
    CASE_VIEW = "case_view"
    CASE_UPDATE = "case_update"
    CASE_DELETE = "case_delete"
    CASE_ASSIGN = "case_assign"
    CASE_GRAB = "case_grab"
    CASE_COMPLETE = "case_complete"
    
    # 支付相关
    PAYMENT_CREATE = "payment_create"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    
    # 文档相关
    DOCUMENT_GENERATE = "document_generate"
    DOCUMENT_REVIEW = "document_review"
    DOCUMENT_APPROVE = "document_approve"
    DOCUMENT_REJECT = "document_reject"
    DOCUMENT_SEND = "document_send"
    
    # 提现相关
    WITHDRAWAL_REQUEST = "withdrawal_request"
    WITHDRAWAL_APPROVE = "withdrawal_approve"
    WITHDRAWAL_REJECT = "withdrawal_reject"
    
    # 配置相关
    CONFIG_UPDATE = "config_update"
    
    # 其他
    PROFILE_UPDATE = "profile_update"
    PASSWORD_CHANGE = "password_change"


class UserActivityTracker:
    """用户行为追踪器"""
    
    def __init__(self):
        self.redis_client = None
        self.batch_size = 30
        self.queue_name = "user_activities_queue"
        
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
    
    async def track_activity(
        self,
        user_id: str,
        activity_type: ActivityType,
        target_id: Optional[str] = None,
        target_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """记录用户活动"""
        try:
            activity_data = {
                "user_id": user_id,
                "action": activity_type.value,
                "resource_type": target_type,
                "resource_id": target_id,
                "details": details or {},
                "ip_address": ip_address,
                "user_agent": user_agent,
                "created_at": datetime.now().isoformat()
            }
            
            # 尝试使用Redis队列
            redis_client = await self._get_redis_client()
            if redis_client:
                await self._queue_activity_to_redis(redis_client, activity_data)
            else:
                # Redis不可用，直接写数据库
                await self._insert_activity_to_db(activity_data)
                
        except Exception as e:
            logger.error(f"记录用户活动失败: {str(e)}")
    
    async def _queue_activity_to_redis(self, redis_client, activity_data: dict):
        """将活动数据加入Redis队列"""
        try:
            await redis_client.lpush(self.queue_name, json.dumps(activity_data, ensure_ascii=False))
            
            # 检查队列长度，触发批量处理
            queue_length = await redis_client.llen(self.queue_name)
            if queue_length >= self.batch_size:
                asyncio.create_task(self._process_activity_batch())
                
        except Exception as e:
            logger.error(f"Redis队列操作失败: {str(e)}")
            # 降级到直接数据库写入
            await self._insert_activity_to_db(activity_data)
    
    async def _process_activity_batch(self):
        """批量处理用户活动数据"""
        try:
            redis_client = await self._get_redis_client()
            if not redis_client:
                return
                
            activities = []
            for _ in range(self.batch_size):
                activity_data = await redis_client.rpop(self.queue_name)
                if activity_data:
                    try:
                        activities.append(json.loads(activity_data))
                    except json.JSONDecodeError as e:
                        logger.error(f"解析活动数据失败: {str(e)}")
                else:
                    break
            
            if activities:
                await self._batch_insert_activities(activities)
                logger.info(f"批量处理用户活动: {len(activities)}条")
                
        except Exception as e:
            logger.error(f"批量处理用户活动失败: {str(e)}")
    
    async def _insert_activity_to_db(self, activity_data: dict):
        """单条插入活动数据到数据库"""
        try:
            async with AsyncSessionLocal() as db:
                await self._execute_insert(db, [activity_data])
        except Exception as e:
            logger.error(f"插入用户活动到数据库失败: {str(e)}")
    
    async def _batch_insert_activities(self, activities: list):
        """批量插入活动数据到数据库"""
        try:
            async with AsyncSessionLocal() as db:
                await self._execute_insert(db, activities)
        except Exception as e:
            logger.error(f"批量插入用户活动失败: {str(e)}")
    
    async def _execute_insert(self, db: AsyncSession, activities: list):
        """执行数据库插入操作"""
        try:
            insert_query = text("""
                INSERT INTO user_activity_logs (
                    user_id, action, resource_type, resource_id,
                    details, ip_address, user_agent, created_at
                ) VALUES (
                    :user_id, :action, :resource_type, :resource_id,
                    :details, :ip_address, :user_agent,
                    COALESCE(:created_at, NOW())
                )
            """)
            
            # 处理details字段的JSON序列化
            for activity in activities:
                if activity.get('details'):
                    activity['details'] = json.dumps(activity['details'], ensure_ascii=False)
            
            await db.execute(insert_query, activities)
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            raise e


# 全局追踪器实例
user_activity_tracker = UserActivityTracker()


# 便捷方法
async def track_login(user_id: str, ip_address: str = None, user_agent: str = None):
    """记录用户登录"""
    await user_activity_tracker.track_activity(
        user_id=user_id,
        activity_type=ActivityType.LOGIN,
        ip_address=ip_address,
        user_agent=user_agent
    )


async def track_logout(user_id: str, ip_address: str = None):
    """记录用户登出"""
    await user_activity_tracker.track_activity(
        user_id=user_id,
        activity_type=ActivityType.LOGOUT,
        ip_address=ip_address
    )


async def track_case_action(
    user_id: str,
    action: str,
    case_id: str,
    details: Dict[str, Any] = None,
    ip_address: str = None
):
    """记录案件相关操作"""
    activity_type_map = {
        "create": ActivityType.CASE_CREATE,
        "view": ActivityType.CASE_VIEW,
        "update": ActivityType.CASE_UPDATE,
        "delete": ActivityType.CASE_DELETE,
        "assign": ActivityType.CASE_ASSIGN,
        "grab": ActivityType.CASE_GRAB,
        "complete": ActivityType.CASE_COMPLETE
    }
    
    activity_type = activity_type_map.get(action, ActivityType.CASE_VIEW)
    
    await user_activity_tracker.track_activity(
        user_id=user_id,
        activity_type=activity_type,
        target_id=case_id,
        target_type="case",
        details=details,
        ip_address=ip_address
    )


async def track_payment_action(
    user_id: str,
    action: str,
    payment_id: str,
    amount: float = None,
    details: Dict[str, Any] = None,
    ip_address: str = None
):
    """记录支付相关操作"""
    activity_type_map = {
        "create": ActivityType.PAYMENT_CREATE,
        "success": ActivityType.PAYMENT_SUCCESS,
        "failed": ActivityType.PAYMENT_FAILED
    }
    
    activity_type = activity_type_map.get(action, ActivityType.PAYMENT_CREATE)
    
    payment_details = details or {}
    if amount:
        payment_details["amount"] = amount
    
    await user_activity_tracker.track_activity(
        user_id=user_id,
        activity_type=activity_type,
        target_id=payment_id,
        target_type="payment",
        details=payment_details,
        ip_address=ip_address
    )


async def track_document_action(
    user_id: str,
    action: str,
    document_id: str,
    document_type: str = None,
    details: Dict[str, Any] = None,
    ip_address: str = None
):
    """记录文档相关操作"""
    activity_type_map = {
        "generate": ActivityType.DOCUMENT_GENERATE,
        "review": ActivityType.DOCUMENT_REVIEW,
        "approve": ActivityType.DOCUMENT_APPROVE,
        "reject": ActivityType.DOCUMENT_REJECT,
        "send": ActivityType.DOCUMENT_SEND
    }
    
    activity_type = activity_type_map.get(action, ActivityType.DOCUMENT_GENERATE)
    
    doc_details = details or {}
    if document_type:
        doc_details["document_type"] = document_type
    
    await user_activity_tracker.track_activity(
        user_id=user_id,
        activity_type=activity_type,
        target_id=document_id,
        target_type="document",
        details=doc_details,
        ip_address=ip_address
    )


async def track_withdrawal_action(
    user_id: str,
    action: str,
    withdrawal_id: str,
    amount: float = None,
    details: Dict[str, Any] = None,
    ip_address: str = None
):
    """记录提现相关操作"""
    activity_type_map = {
        "request": ActivityType.WITHDRAWAL_REQUEST,
        "approve": ActivityType.WITHDRAWAL_APPROVE,
        "reject": ActivityType.WITHDRAWAL_REJECT
    }
    
    activity_type = activity_type_map.get(action, ActivityType.WITHDRAWAL_REQUEST)
    
    withdrawal_details = details or {}
    if amount:
        withdrawal_details["amount"] = amount
    
    await user_activity_tracker.track_activity(
        user_id=user_id,
        activity_type=activity_type,
        target_id=withdrawal_id,
        target_type="withdrawal",
        details=withdrawal_details,
        ip_address=ip_address
    )


async def track_config_update(
    user_id: str,
    config_key: str,
    old_value: Any = None,
    new_value: Any = None,
    ip_address: str = None
):
    """记录配置更新操作"""
    details = {
        "config_key": config_key
    }
    
    if old_value is not None:
        details["old_value"] = str(old_value)
    if new_value is not None:
        details["new_value"] = str(new_value)
    
    await user_activity_tracker.track_activity(
        user_id=user_id,
        activity_type=ActivityType.CONFIG_UPDATE,
        target_id=config_key,
        target_type="config",
        details=details,
        ip_address=ip_address
    )


async def get_user_activity_stats(user_id: str, days: int = 30) -> Dict[str, Any]:
    """获取用户活动统计"""
    try:
        async with AsyncSessionLocal() as db:
            stats_query = text("""
                SELECT 
                    action,
                    COUNT(*) as count,
                    MAX(created_at) as last_activity
                FROM user_activity_logs 
                WHERE user_id = :user_id 
                AND created_at >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY action
                ORDER BY count DESC
            """ % days)
            
            result = await db.execute(stats_query, {"user_id": user_id})
            
            stats = {}
            total_activities = 0
            
            for row in result.fetchall():
                stats[row.action] = {
                    "count": row.count,
                    "last_activity": row.last_activity.isoformat() if row.last_activity else None
                }
                total_activities += row.count
            
            return {
                "user_id": user_id,
                "period_days": days,
                "total_activities": total_activities,
                "activity_breakdown": stats
            }
            
    except Exception as e:
        logger.error(f"获取用户活动统计失败: {str(e)}")
        return {"error": str(e)}