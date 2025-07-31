"""
实时数据聚合服务
定期聚合系统数据并推送到WebSocket客户端
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.services.websocket_manager import broadcast_stats_update, broadcast_system_alert

logger = logging.getLogger(__name__)


class RealtimeDataAggregator:
    """实时数据聚合器"""
    
    def __init__(self):
        self.running = False
        self.update_interval = 30  # 30秒更新一次
        self.alert_thresholds = {
            "high_error_rate": 0.05,  # 5%错误率
            "low_response_time": 5000,  # 5秒响应时间
            "high_queue_length": 1000,  # 队列长度超过1000
            "low_disk_space": 0.1  # 磁盘空间低于10%
        }
        
    async def start_aggregation(self):
        """启动数据聚合循环"""
        self.running = True
        logger.info("实时数据聚合器启动")
        
        while self.running:
            try:
                # 聚合并推送数据
                await self._aggregate_and_push_data()
                
                # 检查告警条件
                await self._check_alerts()
                
                # 等待下次更新
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"数据聚合过程中发生错误: {str(e)}")
                await asyncio.sleep(5)  # 错误时短暂等待
    
    async def stop_aggregation(self):
        """停止数据聚合"""
        self.running = False
        logger.info("实时数据聚合器停止")
    
    async def _aggregate_and_push_data(self):
        """聚合数据并推送"""
        try:
            # 聚合各种统计数据
            stats_data = await self._collect_system_stats()
            
            # 推送到WebSocket客户端
            await broadcast_stats_update(stats_data)
            
            logger.debug("实时数据推送完成")
            
        except Exception as e:
            logger.error(f"聚合和推送数据失败: {str(e)}")
    
    async def _collect_system_stats(self) -> Dict[str, Any]:
        """收集系统统计数据"""
        try:
            async with AsyncSessionLocal() as db:
                # 今日访问统计
                today_stats = await self._get_today_access_stats(db)
                
                # 用户活动统计
                activity_stats = await self._get_user_activity_stats(db)
                
                # 案件统计
                case_stats = await self._get_case_stats(db)
                
                # 系统性能指标
                performance_stats = await self._get_performance_stats(db)
                
                return {
                    "timestamp": datetime.now().isoformat(),
                    "access": today_stats,
                    "activities": activity_stats,
                    "cases": case_stats,
                    "performance": performance_stats
                }
                
        except Exception as e:
            logger.error(f"收集系统统计数据失败: {str(e)}")
            return {"timestamp": datetime.now().isoformat(), "error": str(e)}
    
    async def _get_today_access_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """获取今日访问统计"""
        try:
            query = text("""
                SELECT 
                    COUNT(*) as total_visits,
                    COUNT(DISTINCT ip_address) as unique_visitors,
                    COUNT(DISTINCT user_id) as logged_users,
                    AVG(response_time) as avg_response_time,
                    COUNT(CASE WHEN device_type = 'mobile' THEN 1 END) as mobile_visits,
                    COUNT(CASE WHEN device_type = 'desktop' THEN 1 END) as desktop_visits,
                    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count
                FROM access_logs 
                WHERE DATE(created_at) = CURRENT_DATE
            """)
            
            result = await db.execute(query)
            row = result.fetchone()
            
            if row:
                return {
                    "total_visits": row.total_visits or 0,
                    "unique_visitors": row.unique_visitors or 0,
                    "logged_users": row.logged_users or 0,
                    "avg_response_time": float(row.avg_response_time) if row.avg_response_time else 0,
                    "mobile_visits": row.mobile_visits or 0,
                    "desktop_visits": row.desktop_visits or 0,
                    "error_count": row.error_count or 0,
                    "error_rate": (row.error_count or 0) / max(row.total_visits or 1, 1)
                }
            else:
                return {"total_visits": 0, "unique_visitors": 0, "error_rate": 0}
                
        except Exception as e:
            logger.error(f"获取今日访问统计失败: {str(e)}")
            return {"error": str(e)}
    
    async def _get_user_activity_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """获取用户活动统计"""
        try:
            query = text("""
                SELECT 
                    COUNT(*) as total_activities,
                    COUNT(DISTINCT user_id) as active_users,
                    COUNT(CASE WHEN action = 'login' THEN 1 END) as login_count,
                    COUNT(CASE WHEN action LIKE 'case_%' THEN 1 END) as case_activities,
                    COUNT(CASE WHEN action LIKE 'payment_%' THEN 1 END) as payment_activities
                FROM user_activity_logs 
                WHERE DATE(created_at) = CURRENT_DATE
            """)
            
            result = await db.execute(query)
            row = result.fetchone()
            
            if row:
                return {
                    "total_activities": row.total_activities or 0,
                    "active_users": row.active_users or 0,
                    "login_count": row.login_count or 0,
                    "case_activities": row.case_activities or 0,
                    "payment_activities": row.payment_activities or 0
                }
            else:
                return {"total_activities": 0, "active_users": 0}
                
        except Exception as e:
            logger.error(f"获取用户活动统计失败: {str(e)}")
            return {"error": str(e)}
    
    async def _get_case_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """获取案件统计"""
        try:
            query = text("""
                SELECT 
                    COUNT(*) as total_cases,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_cases,
                    COUNT(CASE WHEN status = 'assigned' THEN 1 END) as assigned_cases,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_cases,
                    COUNT(CASE WHEN DATE(created_at) = CURRENT_DATE THEN 1 END) as today_new_cases
                FROM cases
            """)
            
            result = await db.execute(query)
            row = result.fetchone()
            
            if row:
                return {
                    "total_cases": row.total_cases or 0,
                    "pending_cases": row.pending_cases or 0,
                    "assigned_cases": row.assigned_cases or 0,
                    "completed_cases": row.completed_cases or 0,
                    "today_new_cases": row.today_new_cases or 0
                }
            else:
                return {"total_cases": 0, "pending_cases": 0}
                
        except Exception as e:
            logger.error(f"获取案件统计失败: {str(e)}")
            return {"error": str(e)}
    
    async def _get_performance_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """获取性能统计"""
        try:
            # 获取最近1小时的性能数据
            query = text("""
                SELECT 
                    AVG(response_time) as avg_response_time,
                    MAX(response_time) as max_response_time,
                    COUNT(CASE WHEN response_time > 3000 THEN 1 END) as slow_requests
                FROM access_logs 
                WHERE created_at >= NOW() - INTERVAL '1 hour'
            """)
            
            result = await db.execute(query)
            row = result.fetchone()
            
            if row:
                return {
                    "avg_response_time": float(row.avg_response_time) if row.avg_response_time else 0,
                    "max_response_time": row.max_response_time or 0,
                    "slow_requests": row.slow_requests or 0
                }
            else:
                return {"avg_response_time": 0, "max_response_time": 0, "slow_requests": 0}
                
        except Exception as e:
            logger.error(f"获取性能统计失败: {str(e)}")
            return {"error": str(e)}
    
    async def _check_alerts(self):
        """检查告警条件"""
        try:
            async with AsyncSessionLocal() as db:
                # 检查错误率
                await self._check_error_rate_alert(db)
                
                # 检查响应时间
                await self._check_response_time_alert(db)
                
                # 检查队列长度
                await self._check_queue_length_alert()
                
        except Exception as e:
            logger.error(f"检查告警条件失败: {str(e)}")
    
    async def _check_error_rate_alert(self, db: AsyncSession):
        """检查错误率告警"""
        try:
            query = text("""
                SELECT 
                    COUNT(*) as total_requests,
                    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_requests
                FROM access_logs 
                WHERE created_at >= NOW() - INTERVAL '10 minutes'
            """)
            
            result = await db.execute(query)
            row = result.fetchone()
            
            if row and row.total_requests > 10:  # 至少有10个请求才检查
                error_rate = row.error_requests / row.total_requests
                
                if error_rate > self.alert_thresholds["high_error_rate"]:
                    await broadcast_system_alert({
                        "type": "high_error_rate",
                        "level": "warning",
                        "message": f"错误率过高: {error_rate:.2%}",
                        "details": {
                            "error_rate": error_rate,
                            "total_requests": row.total_requests,
                            "error_requests": row.error_requests,
                            "time_window": "10分钟"
                        }
                    })
                    
        except Exception as e:
            logger.error(f"检查错误率告警失败: {str(e)}")
    
    async def _check_response_time_alert(self, db: AsyncSession):
        """检查响应时间告警"""
        try:
            query = text("""
                SELECT AVG(response_time) as avg_response_time
                FROM access_logs 
                WHERE created_at >= NOW() - INTERVAL '5 minutes'
                AND response_time IS NOT NULL
            """)
            
            result = await db.execute(query)
            row = result.fetchone()
            
            if row and row.avg_response_time:
                avg_response_time = float(row.avg_response_time)
                
                if avg_response_time > self.alert_thresholds["low_response_time"]:
                    await broadcast_system_alert({
                        "type": "slow_response_time",
                        "level": "warning",
                        "message": f"平均响应时间过慢: {avg_response_time:.0f}ms",
                        "details": {
                            "avg_response_time": avg_response_time,
                            "threshold": self.alert_thresholds["low_response_time"],
                            "time_window": "5分钟"
                        }
                    })
                    
        except Exception as e:
            logger.error(f"检查响应时间告警失败: {str(e)}")
    
    async def _check_queue_length_alert(self):
        """检查队列长度告警"""
        try:
            import redis.asyncio as redis
            from app.core.config import settings
            
            redis_client = redis.from_url(settings.REDIS_URL)
            
            # 检查访问日志队列
            access_queue_length = await redis_client.llen("access_logs_queue")
            activity_queue_length = await redis_client.llen("user_activities_queue")
            
            await redis_client.close()
            
            if access_queue_length > self.alert_thresholds["high_queue_length"]:
                await broadcast_system_alert({
                    "type": "high_queue_length",
                    "level": "warning",
                    "message": f"访问日志队列积压: {access_queue_length}条",
                    "details": {
                        "queue_name": "access_logs_queue",
                        "queue_length": access_queue_length,
                        "threshold": self.alert_thresholds["high_queue_length"]
                    }
                })
            
            if activity_queue_length > self.alert_thresholds["high_queue_length"]:
                await broadcast_system_alert({
                    "type": "high_queue_length",
                    "level": "warning",
                    "message": f"用户活动队列积压: {activity_queue_length}条",
                    "details": {
                        "queue_name": "user_activities_queue",
                        "queue_length": activity_queue_length,
                        "threshold": self.alert_thresholds["high_queue_length"]
                    }
                })
                
        except Exception as e:
            logger.error(f"检查队列长度告警失败: {str(e)}")


# 全局聚合器实例
realtime_data_aggregator = RealtimeDataAggregator()


async def start_realtime_data_aggregator():
    """启动实时数据聚合器"""
    asyncio.create_task(realtime_data_aggregator.start_aggregation())


async def stop_realtime_data_aggregator():
    """停止实时数据聚合器"""
    await realtime_data_aggregator.stop_aggregation()