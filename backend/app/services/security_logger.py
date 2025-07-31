"""
安全日志记录服务
记录和分析安全相关事件
"""
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
from fastapi import Request
import redis
from app.core.logging import get_logger
from app.core.database import get_db

logger = get_logger(__name__)

class SecurityEventType(str, Enum):
    """安全事件类型"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGED = "password_changed"
    PERMISSION_DENIED = "permission_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    CSRF_ATTACK = "csrf_attack"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_EXPORT = "data_export"
    ADMIN_ACTION = "admin_action"
    SYSTEM_ERROR = "system_error"

class SecurityEventLevel(str, Enum):
    """安全事件级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityEvent:
    """安全事件数据类"""
    event_type: SecurityEventType
    level: SecurityEventLevel
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.details is None:
            self.details = {}

class SecurityLogger:
    """安全日志记录器"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/2"):
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
        except Exception as e:
            logger.error(f"Redis connection failed: {str(e)}")
            self.redis_client = None
        
        # 内存存储（Redis不可用时的备选方案）
        self.memory_store = []
        self.max_memory_events = 10000
        
        # 事件级别配置
        self.level_config = {
            SecurityEventLevel.LOW: {"retention_days": 7, "alert": False},
            SecurityEventLevel.MEDIUM: {"retention_days": 30, "alert": False},
            SecurityEventLevel.HIGH: {"retention_days": 90, "alert": True},
            SecurityEventLevel.CRITICAL: {"retention_days": 365, "alert": True}
        }
    
    async def log_event(self, event: SecurityEvent):
        """记录安全事件"""
        try:
            # 序列化事件数据
            event_data = self._serialize_event(event)
            
            # 存储到Redis或内存
            await self._store_event(event_data)
            
            # 检查是否需要告警
            if self.level_config[event.level]["alert"]:
                await self._trigger_alert(event)
            
            # 记录到应用日志
            self._log_to_application(event)
            
        except Exception as e:
            logger.error(f"Failed to log security event: {str(e)}")
    
    def _serialize_event(self, event: SecurityEvent) -> Dict[str, Any]:
        """序列化事件数据"""
        event_dict = asdict(event)
        event_dict["timestamp"] = event.timestamp.isoformat()
        return event_dict
    
    async def _store_event(self, event_data: Dict[str, Any]):
        """存储事件数据"""
        event_key = f"security_event:{event_data['timestamp']}:{event_data.get('user_id', 'anonymous')}"
        
        if self.redis_client:
            try:
                # 存储到Redis
                self.redis_client.setex(
                    event_key,
                    self._get_retention_seconds(event_data["level"]),
                    json.dumps(event_data)
                )
                
                # 添加到事件类型索引
                type_key = f"events_by_type:{event_data['event_type']}"
                self.redis_client.zadd(type_key, {event_key: time.time()})
                self.redis_client.expire(type_key, self._get_retention_seconds(event_data["level"]))
                
                # 添加到用户索引
                if event_data.get("user_id"):
                    user_key = f"events_by_user:{event_data['user_id']}"
                    self.redis_client.zadd(user_key, {event_key: time.time()})
                    self.redis_client.expire(user_key, self._get_retention_seconds(event_data["level"]))
                
                # 添加到IP索引
                if event_data.get("ip_address"):
                    ip_key = f"events_by_ip:{event_data['ip_address']}"
                    self.redis_client.zadd(ip_key, {event_key: time.time()})
                    self.redis_client.expire(ip_key, self._get_retention_seconds(event_data["level"]))
                
            except Exception as e:
                logger.error(f"Redis storage failed: {str(e)}")
                self._store_in_memory(event_data)
        else:
            self._store_in_memory(event_data)
    
    def _store_in_memory(self, event_data: Dict[str, Any]):
        """存储到内存"""
        self.memory_store.append(event_data)
        
        # 限制内存使用
        if len(self.memory_store) > self.max_memory_events:
            self.memory_store = self.memory_store[-self.max_memory_events:]
    
    def _get_retention_seconds(self, level: str) -> int:
        """获取保留时间（秒）"""
        days = self.level_config.get(level, {}).get("retention_days", 7)
        return days * 24 * 60 * 60
    
    async def _trigger_alert(self, event: SecurityEvent):
        """触发告警"""
        try:
            # 这里可以集成告警系统
            alert_data = {
                "event_type": event.event_type,
                "level": event.level,
                "user_id": event.user_id,
                "ip_address": event.ip_address,
                "timestamp": event.timestamp.isoformat(),
                "details": event.details
            }
            
            # 发送到告警队列
            if self.redis_client:
                self.redis_client.lpush("security_alerts", json.dumps(alert_data))
            
            logger.warning(f"Security alert triggered: {event.event_type} - {event.level}")
            
        except Exception as e:
            logger.error(f"Failed to trigger alert: {str(e)}")
    
    def _log_to_application(self, event: SecurityEvent):
        """记录到应用日志"""
        log_message = (
            f"Security Event: {event.event_type} - "
            f"Level: {event.level} - "
            f"User: {event.user_id or 'anonymous'} - "
            f"IP: {event.ip_address or 'unknown'}"
        )
        
        if event.level in [SecurityEventLevel.HIGH, SecurityEventLevel.CRITICAL]:
            logger.error(log_message, extra={"security_event": asdict(event)})
        elif event.level == SecurityEventLevel.MEDIUM:
            logger.warning(log_message, extra={"security_event": asdict(event)})
        else:
            logger.info(log_message, extra={"security_event": asdict(event)})
    
    async def get_events(
        self,
        event_type: Optional[SecurityEventType] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        level: Optional[SecurityEventLevel] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查询安全事件"""
        try:
            events = []
            
            if self.redis_client:
                events = await self._query_redis_events(
                    event_type, user_id, ip_address, level, start_time, end_time, limit
                )
            else:
                events = self._query_memory_events(
                    event_type, user_id, ip_address, level, start_time, end_time, limit
                )
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to query events: {str(e)}")
            return []
    
    async def _query_redis_events(
        self,
        event_type: Optional[SecurityEventType],
        user_id: Optional[str],
        ip_address: Optional[str],
        level: Optional[SecurityEventLevel],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        limit: int
    ) -> List[Dict[str, Any]]:
        """从Redis查询事件"""
        events = []
        
        # 构建查询键
        if event_type:
            query_key = f"events_by_type:{event_type}"
        elif user_id:
            query_key = f"events_by_user:{user_id}"
        elif ip_address:
            query_key = f"events_by_ip:{ip_address}"
        else:
            # 查询所有事件（性能较差，仅用于小规模数据）
            query_key = "security_event:*"
        
        try:
            if query_key.endswith("*"):
                # 扫描所有键
                keys = self.redis_client.keys(query_key)
            else:
                # 从有序集合获取键
                start_score = start_time.timestamp() if start_time else 0
                end_score = end_time.timestamp() if end_time else time.time()
                keys = self.redis_client.zrangebyscore(query_key, start_score, end_score)
            
            # 获取事件数据
            for key in keys[:limit]:
                event_data = self.redis_client.get(key)
                if event_data:
                    event = json.loads(event_data)
                    
                    # 应用过滤条件
                    if self._matches_filters(event, level, start_time, end_time):
                        events.append(event)
            
        except Exception as e:
            logger.error(f"Redis query failed: {str(e)}")
        
        return sorted(events, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    def _query_memory_events(
        self,
        event_type: Optional[SecurityEventType],
        user_id: Optional[str],
        ip_address: Optional[str],
        level: Optional[SecurityEventLevel],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        limit: int
    ) -> List[Dict[str, Any]]:
        """从内存查询事件"""
        filtered_events = []
        
        for event in self.memory_store:
            if self._matches_filters(event, level, start_time, end_time, event_type, user_id, ip_address):
                filtered_events.append(event)
        
        return sorted(filtered_events, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    def _matches_filters(
        self,
        event: Dict[str, Any],
        level: Optional[SecurityEventLevel] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[SecurityEventType] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """检查事件是否匹配过滤条件"""
        if level and event.get("level") != level:
            return False
        
        if event_type and event.get("event_type") != event_type:
            return False
        
        if user_id and event.get("user_id") != user_id:
            return False
        
        if ip_address and event.get("ip_address") != ip_address:
            return False
        
        event_time = datetime.fromisoformat(event["timestamp"])
        
        if start_time and event_time < start_time:
            return False
        
        if end_time and event_time > end_time:
            return False
        
        return True
    
    async def get_event_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取事件统计信息"""
        try:
            if not start_time:
                start_time = datetime.utcnow() - timedelta(days=7)
            if not end_time:
                end_time = datetime.utcnow()
            
            events = await self.get_events(start_time=start_time, end_time=end_time, limit=10000)
            
            # 统计分析
            stats = {
                "total_events": len(events),
                "events_by_type": {},
                "events_by_level": {},
                "events_by_hour": {},
                "top_ips": {},
                "top_users": {}
            }
            
            for event in events:
                # 按类型统计
                event_type = event.get("event_type", "unknown")
                stats["events_by_type"][event_type] = stats["events_by_type"].get(event_type, 0) + 1
                
                # 按级别统计
                level = event.get("level", "unknown")
                stats["events_by_level"][level] = stats["events_by_level"].get(level, 0) + 1
                
                # 按小时统计
                event_time = datetime.fromisoformat(event["timestamp"])
                hour_key = event_time.strftime("%Y-%m-%d %H:00")
                stats["events_by_hour"][hour_key] = stats["events_by_hour"].get(hour_key, 0) + 1
                
                # IP统计
                ip = event.get("ip_address")
                if ip:
                    stats["top_ips"][ip] = stats["top_ips"].get(ip, 0) + 1
                
                # 用户统计
                user_id = event.get("user_id")
                if user_id:
                    stats["top_users"][user_id] = stats["top_users"].get(user_id, 0) + 1
            
            # 排序Top统计
            stats["top_ips"] = dict(sorted(stats["top_ips"].items(), key=lambda x: x[1], reverse=True)[:10])
            stats["top_users"] = dict(sorted(stats["top_users"].items(), key=lambda x: x[1], reverse=True)[:10])
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get event statistics: {str(e)}")
            return {}

# 全局安全日志记录器
security_logger = SecurityLogger()

# 便捷函数
async def log_login_success(user_id: str, request: Request):
    """记录登录成功"""
    event = SecurityEvent(
        event_type=SecurityEventType.LOGIN_SUCCESS,
        level=SecurityEventLevel.LOW,
        user_id=user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        endpoint=str(request.url.path),
        method=request.method
    )
    await security_logger.log_event(event)

async def log_login_failed(username: str, request: Request, reason: str = ""):
    """记录登录失败"""
    event = SecurityEvent(
        event_type=SecurityEventType.LOGIN_FAILED,
        level=SecurityEventLevel.MEDIUM,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        endpoint=str(request.url.path),
        method=request.method,
        details={"username": username, "reason": reason}
    )
    await security_logger.log_event(event)

async def log_permission_denied(user_id: str, resource: str, action: str, request: Request):
    """记录权限拒绝"""
    event = SecurityEvent(
        event_type=SecurityEventType.PERMISSION_DENIED,
        level=SecurityEventLevel.MEDIUM,
        user_id=user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        endpoint=str(request.url.path),
        method=request.method,
        details={"resource": resource, "action": action}
    )
    await security_logger.log_event(event)

async def log_suspicious_activity(user_id: Optional[str], activity_type: str, request: Request, details: Dict[str, Any] = None):
    """记录可疑活动"""
    event = SecurityEvent(
        event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
        level=SecurityEventLevel.HIGH,
        user_id=user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        endpoint=str(request.url.path),
        method=request.method,
        details={"activity_type": activity_type, **(details or {})}
    )
    await security_logger.log_event(event)