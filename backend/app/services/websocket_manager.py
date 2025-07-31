"""
WebSocket连接管理器
管理管理员的WebSocket连接，实现实时数据推送
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class ConnectionInfo:
    """连接信息"""
    def __init__(self, websocket: WebSocket, user_id: str, user_role: str):
        self.id = str(uuid4())
        self.websocket = websocket
        self.user_id = user_id
        self.user_role = user_role
        self.connected_at = datetime.now()
        self.last_ping = datetime.now()
        self.is_active = True


class WebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 存储活跃连接 {connection_id: ConnectionInfo}
        self.active_connections: Dict[str, ConnectionInfo] = {}
        # 按用户ID索引连接 {user_id: [connection_ids]}
        self.user_connections: Dict[str, List[str]] = {}
        # 按角色索引连接 {role: [connection_ids]}
        self.role_connections: Dict[str, List[str]] = {}
        
        self.redis_client = None
        self.pubsub = None
        self.listening_task = None
        
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
    
    async def start_redis_listener(self):
        """启动Redis发布订阅监听"""
        try:
            redis_client = await self._get_redis_client()
            if not redis_client:
                logger.warning("Redis不可用，无法启动实时推送")
                return
                
            self.pubsub = redis_client.pubsub()
            await self.pubsub.subscribe(
                "realtime_stats",      # 实时统计数据
                "system_alerts",       # 系统告警
                "user_activities",     # 用户活动通知
                "admin_notifications"  # 管理员通知
            )
            
            # 启动监听任务
            self.listening_task = asyncio.create_task(self._listen_redis_messages())
            logger.info("WebSocket Redis监听器启动成功")
            
        except Exception as e:
            logger.error(f"启动Redis监听器失败: {str(e)}")
    
    async def stop_redis_listener(self):
        """停止Redis监听器"""
        try:
            if self.listening_task:
                self.listening_task.cancel()
                
            if self.pubsub:
                await self.pubsub.unsubscribe()
                await self.pubsub.close()
                
            if self.redis_client:
                await self.redis_client.close()
                
            logger.info("WebSocket Redis监听器已停止")
            
        except Exception as e:
            logger.error(f"停止Redis监听器失败: {str(e)}")
    
    async def _listen_redis_messages(self):
        """监听Redis消息"""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    await self._handle_redis_message(message)
        except asyncio.CancelledError:
            logger.info("Redis消息监听任务被取消")
        except Exception as e:
            logger.error(f"Redis消息监听失败: {str(e)}")
    
    async def _handle_redis_message(self, message):
        """处理Redis消息"""
        try:
            channel = message["channel"].decode()
            data = json.loads(message["data"])
            
            # 根据频道类型处理消息
            if channel == "realtime_stats":
                await self._broadcast_stats_update(data)
            elif channel == "system_alerts":
                await self._broadcast_alert(data)
            elif channel == "user_activities":
                await self._broadcast_user_activity(data)
            elif channel == "admin_notifications":
                await self._broadcast_admin_notification(data)
                
        except Exception as e:
            logger.error(f"处理Redis消息失败: {str(e)}")
    
    async def connect(self, websocket: WebSocket, user_id: str, user_role: str) -> str:
        """建立WebSocket连接"""
        try:
            await websocket.accept()
            
            # 创建连接信息
            connection = ConnectionInfo(websocket, user_id, user_role)
            connection_id = connection.id
            
            # 存储连接
            self.active_connections[connection_id] = connection
            
            # 按用户ID索引
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(connection_id)
            
            # 按角色索引
            if user_role not in self.role_connections:
                self.role_connections[user_role] = []
            self.role_connections[user_role].append(connection_id)
            
            logger.info(f"WebSocket连接建立: {connection_id} (用户: {user_id}, 角色: {user_role})")
            
            # 发送连接成功消息
            await self._send_to_connection(connection_id, {
                "type": "connection_established",
                "connection_id": connection_id,
                "timestamp": datetime.now().isoformat(),
                "message": "WebSocket连接建立成功"
            })
            
            # 发送初始数据
            await self._send_initial_data(connection_id)
            
            return connection_id
            
        except Exception as e:
            logger.error(f"建立WebSocket连接失败: {str(e)}")
            raise
    
    async def disconnect(self, connection_id: str):
        """断开WebSocket连接"""
        try:
            if connection_id not in self.active_connections:
                return
                
            connection = self.active_connections[connection_id]
            user_id = connection.user_id
            user_role = connection.user_role
            
            # 从索引中移除
            if user_id in self.user_connections:
                self.user_connections[user_id].remove(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            if user_role in self.role_connections:
                self.role_connections[user_role].remove(connection_id)
                if not self.role_connections[user_role]:
                    del self.role_connections[user_role]
            
            # 移除连接
            del self.active_connections[connection_id]
            
            logger.info(f"WebSocket连接断开: {connection_id} (用户: {user_id})")
            
        except Exception as e:
            logger.error(f"断开WebSocket连接失败: {str(e)}")
    
    async def _send_initial_data(self, connection_id: str):
        """发送初始数据"""
        try:
            # 发送当前连接统计
            stats = {
                "total_connections": len(self.active_connections),
                "admin_connections": len(self.role_connections.get("admin", [])),
                "online_users": len(self.user_connections)
            }
            
            await self._send_to_connection(connection_id, {
                "type": "initial_stats",
                "data": stats,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"发送初始数据失败: {str(e)}")
    
    async def _send_to_connection(self, connection_id: str, message: dict):
        """向特定连接发送消息"""
        try:
            if connection_id not in self.active_connections:
                return False
                
            connection = self.active_connections[connection_id]
            if not connection.is_active:
                return False
                
            await connection.websocket.send_text(json.dumps(message, ensure_ascii=False))
            return True
            
        except WebSocketDisconnect:
            await self.disconnect(connection_id)
            return False
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {str(e)}")
            # 标记连接为非活跃
            if connection_id in self.active_connections:
                self.active_connections[connection_id].is_active = False
            return False
    
    async def broadcast_to_all(self, message: dict):
        """向所有连接广播消息"""
        if not self.active_connections:
            return
            
        # 并发发送消息
        tasks = []
        for connection_id in list(self.active_connections.keys()):
            task = asyncio.create_task(self._send_to_connection(connection_id, message))
            tasks.append(task)
        
        # 等待所有发送完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 统计发送结果
        success_count = sum(1 for result in results if result is True)
        logger.info(f"广播消息完成: 成功 {success_count}/{len(tasks)}")
    
    async def broadcast_to_role(self, role: str, message: dict):
        """向特定角色广播消息"""
        if role not in self.role_connections:
            return
            
        connection_ids = self.role_connections[role].copy()
        tasks = []
        
        for connection_id in connection_ids:
            task = asyncio.create_task(self._send_to_connection(connection_id, message))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        success_count = sum(1 for result in results if result is True)
        logger.info(f"向角色 {role} 广播消息: 成功 {success_count}/{len(tasks)}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """向特定用户发送消息"""
        if user_id not in self.user_connections:
            return False
            
        connection_ids = self.user_connections[user_id].copy()
        tasks = []
        
        for connection_id in connection_ids:
            task = asyncio.create_task(self._send_to_connection(connection_id, message))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        success_count = sum(1 for result in results if result is True)
        
        return success_count > 0
    
    async def _broadcast_stats_update(self, data: dict):
        """广播统计数据更新"""
        message = {
            "type": "stats_update",
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_role("admin", message)
    
    async def _broadcast_alert(self, data: dict):
        """广播系统告警"""
        message = {
            "type": "system_alert",
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "priority": data.get("priority", "normal")
        }
        await self.broadcast_to_role("admin", message)
    
    async def _broadcast_user_activity(self, data: dict):
        """广播用户活动通知"""
        message = {
            "type": "user_activity",
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_role("admin", message)
    
    async def _broadcast_admin_notification(self, data: dict):
        """广播管理员通知"""
        message = {
            "type": "admin_notification",
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_role("admin", message)
    
    async def ping_all_connections(self):
        """向所有连接发送心跳"""
        ping_message = {
            "type": "ping",
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_all(ping_message)
    
    def get_connection_stats(self) -> dict:
        """获取连接统计信息"""
        return {
            "total_connections": len(self.active_connections),
            "connections_by_role": {
                role: len(connections) 
                for role, connections in self.role_connections.items()
            },
            "unique_users": len(self.user_connections),
            "active_connections": sum(
                1 for conn in self.active_connections.values() 
                if conn.is_active
            )
        }
    
    async def cleanup_inactive_connections(self):
        """清理非活跃连接"""
        inactive_connections = [
            conn_id for conn_id, conn in self.active_connections.items()
            if not conn.is_active
        ]
        
        for conn_id in inactive_connections:
            await self.disconnect(conn_id)
        
        if inactive_connections:
            logger.info(f"清理非活跃连接: {len(inactive_connections)}个")


# 全局WebSocket管理器实例
websocket_manager = WebSocketManager()


async def start_websocket_manager():
    """启动WebSocket管理器"""
    await websocket_manager.start_redis_listener()


async def stop_websocket_manager():
    """停止WebSocket管理器"""
    await websocket_manager.stop_redis_listener()


# 便捷方法
async def broadcast_stats_update(data: dict):
    """广播统计数据更新"""
    redis_client = await websocket_manager._get_redis_client()
    if redis_client:
        await redis_client.publish("realtime_stats", json.dumps(data, ensure_ascii=False))


async def broadcast_system_alert(alert_data: dict):
    """广播系统告警"""
    redis_client = await websocket_manager._get_redis_client()
    if redis_client:
        await redis_client.publish("system_alerts", json.dumps(alert_data, ensure_ascii=False))


async def broadcast_user_activity(activity_data: dict):
    """广播用户活动通知"""
    redis_client = await websocket_manager._get_redis_client()
    if redis_client:
        await redis_client.publish("user_activities", json.dumps(activity_data, ensure_ascii=False))


async def send_admin_notification(notification_data: dict):
    """发送管理员通知"""
    redis_client = await websocket_manager._get_redis_client()
    if redis_client:
        await redis_client.publish("admin_notifications", json.dumps(notification_data, ensure_ascii=False))