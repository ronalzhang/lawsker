"""
WebSocket API端点
提供实时数据推送功能
"""

import asyncio
import json
import logging
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer
from jose import jwt, JWTError

from app.core.config import settings
from app.services.websocket_manager import websocket_manager
from app.services.auth_service import AuthService
from app.core.deps import get_auth_service

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


async def get_user_from_token(token: str) -> Dict[str, Any]:
    """从JWT token获取用户信息"""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的token"
            )
        
        # 这里简化处理，实际项目中应该从数据库获取完整用户信息
        return {
            "id": user_id,
            "username": payload.get("username", ""),
            "role": payload.get("role", "user"),
            "status": "active"
        }
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的token"
        )


@router.websocket("/admin/realtime")
async def admin_realtime_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT认证token")
):
    """管理员实时数据WebSocket连接"""
    connection_id = None
    
    try:
        # 验证token
        user = await get_user_from_token(token)
        
        # 检查权限（只允许管理员连接）
        if user["role"] not in ["admin", "super_admin"]:
            await websocket.close(code=4003, reason="权限不足")
            return
        
        # 建立连接
        connection_id = await websocket_manager.connect(
            websocket=websocket,
            user_id=user["id"],
            user_role=user["role"]
        )
        
        logger.info(f"管理员WebSocket连接建立: {user['username']} ({connection_id})")
        
        # 保持连接并处理消息
        while True:
            try:
                # 接收客户端消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 处理客户端消息
                await handle_client_message(connection_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"管理员WebSocket连接断开: {user['username']}")
                break
            except json.JSONDecodeError:
                # 发送错误消息
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "无效的JSON格式",
                    "timestamp": "2024-01-01T00:00:00Z"
                }))
            except Exception as e:
                logger.error(f"处理WebSocket消息失败: {str(e)}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "处理消息失败",
                    "timestamp": "2024-01-01T00:00:00Z"
                }))
                
    except HTTPException as e:
        # 认证失败
        await websocket.close(code=4001, reason=e.detail)
        return
    except Exception as e:
        logger.error(f"WebSocket连接异常: {str(e)}")
        await websocket.close(code=4000, reason="服务器内部错误")
    finally:
        # 清理连接
        if connection_id:
            await websocket_manager.disconnect(connection_id)


async def handle_client_message(connection_id: str, message: dict):
    """处理客户端消息"""
    try:
        message_type = message.get("type")
        
        if message_type == "ping":
            # 心跳响应
            await websocket_manager._send_to_connection(connection_id, {
                "type": "pong",
                "timestamp": message.get("timestamp")
            })
            
        elif message_type == "subscribe":
            # 订阅特定数据类型
            data_types = message.get("data_types", [])
            await handle_subscription(connection_id, data_types)
            
        elif message_type == "unsubscribe":
            # 取消订阅
            data_types = message.get("data_types", [])
            await handle_unsubscription(connection_id, data_types)
            
        elif message_type == "request_data":
            # 请求特定数据
            data_type = message.get("data_type")
            await handle_data_request(connection_id, data_type)
            
        else:
            # 未知消息类型
            await websocket_manager._send_to_connection(connection_id, {
                "type": "error",
                "message": f"未知的消息类型: {message_type}",
                "timestamp": "2024-01-01T00:00:00Z"
            })
            
    except Exception as e:
        logger.error(f"处理客户端消息失败: {str(e)}")


async def handle_subscription(connection_id: str, data_types: list):
    """处理订阅请求"""
    # 这里可以实现更细粒度的订阅控制
    # 目前简化处理，发送确认消息
    await websocket_manager._send_to_connection(connection_id, {
        "type": "subscription_confirmed",
        "data_types": data_types,
        "timestamp": "2024-01-01T00:00:00Z"
    })


async def handle_unsubscription(connection_id: str, data_types: list):
    """处理取消订阅请求"""
    await websocket_manager._send_to_connection(connection_id, {
        "type": "unsubscription_confirmed",
        "data_types": data_types,
        "timestamp": "2024-01-01T00:00:00Z"
    })


async def handle_data_request(connection_id: str, data_type: str):
    """处理数据请求"""
    try:
        if data_type == "connection_stats":
            # 返回连接统计
            stats = websocket_manager.get_connection_stats()
            await websocket_manager._send_to_connection(connection_id, {
                "type": "data_response",
                "data_type": "connection_stats",
                "data": stats,
                "timestamp": "2024-01-01T00:00:00Z"
            })
            
        elif data_type == "system_status":
            # 返回系统状态
            await websocket_manager._send_to_connection(connection_id, {
                "type": "data_response",
                "data_type": "system_status",
                "data": {
                    "status": "running",
                    "uptime": "unknown",
                    "version": "1.0.0"
                },
                "timestamp": "2024-01-01T00:00:00Z"
            })
            
        else:
            await websocket_manager._send_to_connection(connection_id, {
                "type": "error",
                "message": f"不支持的数据类型: {data_type}",
                "timestamp": "2024-01-01T00:00:00Z"
            })
            
    except Exception as e:
        logger.error(f"处理数据请求失败: {str(e)}")


@router.get("/admin/websocket/stats")
async def get_websocket_stats():
    """获取WebSocket连接统计"""
    try:
        stats = websocket_manager.get_connection_stats()
        return {
            "code": 200,
            "message": "获取WebSocket统计成功",
            "data": stats
        }
    except Exception as e:
        logger.error(f"获取WebSocket统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取WebSocket统计失败"
        )


@router.post("/admin/websocket/broadcast")
async def broadcast_message(
    message_data: dict
):
    """广播消息到所有管理员连接"""
    try:
        message_type = message_data.get("type", "notification")
        
        if message_type == "stats_update":
            from app.services.websocket_manager import broadcast_stats_update
            await broadcast_stats_update(message_data.get("data", {}))
            
        elif message_type == "alert":
            from app.services.websocket_manager import broadcast_system_alert
            await broadcast_system_alert(message_data.get("data", {}))
            
        elif message_type == "notification":
            from app.services.websocket_manager import send_admin_notification
            await send_admin_notification(message_data.get("data", {}))
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的消息类型: {message_type}"
            )
        
        return {
            "code": 200,
            "message": "消息广播成功",
            "data": {"message_type": message_type}
        }
        
    except Exception as e:
        logger.error(f"广播消息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="广播消息失败"
        )