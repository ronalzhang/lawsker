"""
数据库监控服务
实时监控数据库性能指标并发送告警
"""
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import psutil
from sqlalchemy import text
import redis

from app.core.database import engine
from app.core.logging import get_logger
from app.services.alert_manager import alert_manager
from app.services.database_optimizer import DatabaseMetrics, database_optimizer

logger = get_logger(__name__)

@dataclass
class DatabaseAlert:
    """数据库告警"""
    alert_id: str
    alert_type: str
    severity: str
    message: str
    metric_name: str
    current_value: float
    threshold_value: float
    timestamp: datetime
    resolved: bool = False

class DatabaseMonitor:
    """数据库监控器"""
    
    def __init__(self):
        self.redis_client = redis.from_url("redis://localhost:6379/4")
        self.monitoring_interval = 60  # 60秒
        self.is_monitoring = False
        self.alert_cooldown = 300  # 5分钟告警冷却期
        
        # 告警阈值配置
        self.alert_thresholds = {
            "connections_usage_percent": {"warning": 70, "critical": 85},
            "cpu_usage_percent": {"warning": 70, "critical": 85},
            "memory_usage_percent": {"warning": 80, "critical": 90},
            "cache_hit_ratio": {"warning": 90, "critical": 85},  # 低于阈值告警
            "queries_per_second": {"warning": 1000, "critical": 2000},
            "slow_queries_per_minute": {"warning": 5, "critical": 10},
            "disk_usage_percent": {"warning": 80, "critical": 90},
            "connection_wait_time": {"warning": 5, "critical": 10},  # 秒
            "deadlock_count": {"warning": 1, "critical": 5},
            "replication_lag": {"warning": 60, "critical": 300}  # 秒
        }
        
        # 历史数据保留时间
        self.metrics_retention_hours = 24 * 7  # 7天
    
    async def start_monitoring(self):
        """启动监控"""
        if self.is_monitoring:
            logger.warning("Database monitoring is already running")
            return
        
        self.is_monitoring = True
        logger.info("Starting database monitoring")
        
        try:
            while self.is_monitoring:
                await self._collect_and_check_metrics()
                await asyncio.sleep(self.monitoring_interval)
        except Exception as e:
            logger.error(f"Database monitoring error: {str(e)}")
        finally:
            self.is_monitoring = False
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        logger.info("Database monitoring stopped")
    
    async def _collect_and_check_metrics(self):
        """收集指标并检查告警"""
        try:
            # 收集基础指标
            metrics = await database_optimizer.collect_database_metrics()
            
            # 收集扩展指标
            extended_metrics = await self._collect_extended_metrics()
            
            # 合并指标
            all_metrics = {
                **asdict(metrics),
                **extended_metrics
            }
            
            # 存储指标历史
            await self._store_metrics_history(all_metrics)
            
            # 检查告警条件
            await self._check_alert_conditions(all_metrics)
            
            # 清理过期数据
            await self._cleanup_old_metrics()
            
        except Exception as e:
            logger.error(f"Failed to collect and check metrics: {str(e)}")
    
    async def _collect_extended_metrics(self) -> Dict[str, Any]:
        """收集扩展指标"""
        extended_metrics = {}
        
        try:
            with engine.connect() as conn:
                # 连接等待时间
                wait_result = conn.execute(text("""
                    SELECT COALESCE(AVG(EXTRACT(EPOCH FROM (now() - query_start))), 0) as avg_wait_time
                    FROM pg_stat_activity 
                    WHERE state = 'active' AND wait_event_type IS NOT NULL
                """))
                wait_stats = wait_result.fetchone()
                extended_metrics["connection_wait_time"] = wait_stats.avg_wait_time or 0
                
                # 死锁统计
                deadlock_result = conn.execute(text("""
                    SELECT deadlocks FROM pg_stat_database WHERE datname = current_database()
                """))
                deadlock_stats = deadlock_result.fetchone()
                extended_metrics["deadlock_count"] = deadlock_stats.deadlocks or 0
                
                # 复制延迟（如果有从库）
                try:
                    replication_result = conn.execute(text("""
                        SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) as replication_lag
                    """))
                    replication_stats = replication_result.fetchone()
                    extended_metrics["replication_lag"] = replication_stats.replication_lag or 0
                except:
                    extended_metrics["replication_lag"] = 0
                
                # 磁盘使用率
                disk_result = conn.execute(text("""
                    SELECT 
                        pg_database_size(current_database()) as db_size,
                        pg_tablespace_size('pg_default') as tablespace_size
                """))
                disk_stats = disk_result.fetchone()
                
                # 计算磁盘使用百分比（简化计算）
                disk_usage = psutil.disk_usage('/')
                extended_metrics["disk_usage_percent"] = (disk_usage.used / disk_usage.total) * 100
                
                # 慢查询统计
                slow_query_result = conn.execute(text("""
                    SELECT COUNT(*) as slow_query_count
                    FROM pg_stat_statements 
                    WHERE mean_exec_time > 1000  -- 大于1秒的查询
                """))
                slow_query_stats = slow_query_result.fetchone()
                extended_metrics["slow_queries_per_minute"] = slow_query_stats.slow_query_count or 0
                
                # 连接使用率
                if metrics.connections_total > 0:
                    extended_metrics["connections_usage_percent"] = (
                        metrics.connections_active / metrics.connections_total
                    ) * 100
                else:
                    extended_metrics["connections_usage_percent"] = 0
                
                # 内存使用率
                memory = psutil.virtual_memory()
                extended_metrics["memory_usage_percent"] = memory.percent
            
            return extended_metrics
            
        except Exception as e:
            logger.error(f"Failed to collect extended metrics: {str(e)}")
            return {}
    
    async def _store_metrics_history(self, metrics: Dict[str, Any]):
        """存储指标历史"""
        try:
            timestamp = datetime.now()
            
            # 存储到Redis时序数据
            metrics_data = {
                "timestamp": timestamp.isoformat(),
                "metrics": metrics
            }
            
            # 使用时间戳作为键
            key = f"db_metrics:{timestamp.strftime('%Y%m%d_%H%M%S')}"
            self.redis_client.setex(
                key,
                self.metrics_retention_hours * 3600,  # TTL
                json.dumps(metrics_data)
            )
            
            # 更新最新指标
            self.redis_client.setex(
                "db_metrics:latest",
                300,  # 5分钟TTL
                json.dumps(metrics_data)
            )
            
        except Exception as e:
            logger.error(f"Failed to store metrics history: {str(e)}")
    
    async def _check_alert_conditions(self, metrics: Dict[str, Any]):
        """检查告警条件"""
        current_time = datetime.now()
        
        for metric_name, thresholds in self.alert_thresholds.items():
            if metric_name not in metrics:
                continue
            
            current_value = metrics[metric_name]
            
            # 检查关键告警
            if "critical" in thresholds:
                await self._check_threshold_alert(
                    metric_name, current_value, thresholds["critical"],
                    "critical", current_time
                )
            
            # 检查警告告警
            if "warning" in thresholds:
                await self._check_threshold_alert(
                    metric_name, current_value, thresholds["warning"],
                    "warning", current_time
                )
    
    async def _check_threshold_alert(
        self, metric_name: str, current_value: float, 
        threshold: float, severity: str, timestamp: datetime
    ):
        """检查阈值告警"""
        try:
            # 确定告警条件
            is_alert_condition = False
            
            if metric_name == "cache_hit_ratio":
                # 缓存命中率低于阈值时告警
                is_alert_condition = current_value < threshold
            else:
                # 其他指标高于阈值时告警
                is_alert_condition = current_value > threshold
            
            alert_id = f"{metric_name}_{severity}"
            
            if is_alert_condition:
                # 检查告警冷却期
                if await self._is_in_cooldown(alert_id):
                    return
                
                # 创建告警
                alert = DatabaseAlert(
                    alert_id=alert_id,
                    alert_type="database_metric",
                    severity=severity,
                    message=self._generate_alert_message(metric_name, current_value, threshold, severity),
                    metric_name=metric_name,
                    current_value=current_value,
                    threshold_value=threshold,
                    timestamp=timestamp
                )
                
                await self._send_alert(alert)
                await self._set_alert_cooldown(alert_id)
                
            else:
                # 检查是否需要解除告警
                await self._resolve_alert(alert_id)
                
        except Exception as e:
            logger.error(f"Failed to check threshold alert: {str(e)}")
    
    def _generate_alert_message(
        self, metric_name: str, current_value: float, 
        threshold: float, severity: str
    ) -> str:
        """生成告警消息"""
        metric_descriptions = {
            "connections_usage_percent": "数据库连接使用率",
            "cpu_usage_percent": "CPU使用率",
            "memory_usage_percent": "内存使用率",
            "cache_hit_ratio": "缓存命中率",
            "queries_per_second": "每秒查询数",
            "slow_queries_per_minute": "每分钟慢查询数",
            "disk_usage_percent": "磁盘使用率",
            "connection_wait_time": "连接等待时间",
            "deadlock_count": "死锁数量",
            "replication_lag": "复制延迟"
        }
        
        metric_desc = metric_descriptions.get(metric_name, metric_name)
        
        if metric_name == "cache_hit_ratio":
            return f"【{severity.upper()}】{metric_desc}过低: {current_value:.2f}% < {threshold}%"
        else:
            return f"【{severity.upper()}】{metric_desc}过高: {current_value:.2f} > {threshold}"
    
    async def _is_in_cooldown(self, alert_id: str) -> bool:
        """检查是否在告警冷却期"""
        try:
            cooldown_key = f"alert_cooldown:{alert_id}"
            return self.redis_client.exists(cooldown_key)
        except Exception as e:
            logger.error(f"Failed to check alert cooldown: {str(e)}")
            return False
    
    async def _set_alert_cooldown(self, alert_id: str):
        """设置告警冷却期"""
        try:
            cooldown_key = f"alert_cooldown:{alert_id}"
            self.redis_client.setex(cooldown_key, self.alert_cooldown, "1")
        except Exception as e:
            logger.error(f"Failed to set alert cooldown: {str(e)}")
    
    async def _send_alert(self, alert: DatabaseAlert):
        """发送告警"""
        try:
            # 存储告警记录
            alert_key = f"db_alert:{alert.alert_id}:{alert.timestamp.strftime('%Y%m%d_%H%M%S')}"
            self.redis_client.setex(
                alert_key,
                86400 * 7,  # 7天TTL
                json.dumps(asdict(alert), default=str)
            )
            
            # 发送告警通知
            await alert_manager.send_alert(
                alert_type="database",
                severity=alert.severity,
                title=f"数据库告警: {alert.metric_name}",
                message=alert.message,
                details={
                    "metric_name": alert.metric_name,
                    "current_value": alert.current_value,
                    "threshold_value": alert.threshold_value,
                    "timestamp": alert.timestamp.isoformat()
                }
            )
            
            logger.warning(f"Database alert sent: {alert.message}")
            
        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")
    
    async def _resolve_alert(self, alert_id: str):
        """解除告警"""
        try:
            # 检查是否有活跃的告警
            pattern = f"db_alert:{alert_id}:*"
            keys = self.redis_client.keys(pattern)
            
            for key in keys:
                alert_data = self.redis_client.get(key)
                if alert_data:
                    alert_dict = json.loads(alert_data)
                    if not alert_dict.get("resolved", False):
                        # 标记为已解决
                        alert_dict["resolved"] = True
                        alert_dict["resolved_at"] = datetime.now().isoformat()
                        
                        self.redis_client.setex(
                            key,
                            86400 * 7,  # 7天TTL
                            json.dumps(alert_dict)
                        )
                        
                        logger.info(f"Database alert resolved: {alert_id}")
                        break
                        
        except Exception as e:
            logger.error(f"Failed to resolve alert: {str(e)}")
    
    async def _cleanup_old_metrics(self):
        """清理过期指标数据"""
        try:
            # Redis的TTL会自动清理过期数据
            # 这里可以添加额外的清理逻辑
            pass
        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {str(e)}")
    
    async def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取指标历史"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # 获取时间范围内的所有指标
            pattern = "db_metrics:*"
            keys = self.redis_client.keys(pattern)
            
            metrics_history = []
            for key in keys:
                if key == "db_metrics:latest":
                    continue
                
                data = self.redis_client.get(key)
                if data:
                    metrics_data = json.loads(data)
                    timestamp = datetime.fromisoformat(metrics_data["timestamp"])
                    
                    if start_time <= timestamp <= end_time:
                        metrics_history.append(metrics_data)
            
            # 按时间排序
            metrics_history.sort(key=lambda x: x["timestamp"])
            return metrics_history
            
        except Exception as e:
            logger.error(f"Failed to get metrics history: {str(e)}")
            return []
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃告警"""
        try:
            pattern = "db_alert:*"
            keys = self.redis_client.keys(pattern)
            
            active_alerts = []
            for key in keys:
                data = self.redis_client.get(key)
                if data:
                    alert_dict = json.loads(data)
                    if not alert_dict.get("resolved", False):
                        active_alerts.append(alert_dict)
            
            # 按时间排序
            active_alerts.sort(key=lambda x: x["timestamp"], reverse=True)
            return active_alerts
            
        except Exception as e:
            logger.error(f"Failed to get active alerts: {str(e)}")
            return []
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        try:
            # 获取最新指标
            latest_data = self.redis_client.get("db_metrics:latest")
            latest_metrics = json.loads(latest_data) if latest_data else None
            
            # 获取活跃告警数量
            active_alerts = await self.get_active_alerts()
            
            return {
                "is_monitoring": self.is_monitoring,
                "monitoring_interval": self.monitoring_interval,
                "latest_metrics": latest_metrics,
                "active_alerts_count": len(active_alerts),
                "alert_thresholds": self.alert_thresholds,
                "metrics_retention_hours": self.metrics_retention_hours
            }
            
        except Exception as e:
            logger.error(f"Failed to get monitoring status: {str(e)}")
            return {
                "is_monitoring": self.is_monitoring,
                "error": str(e)
            }


# 全局监控器实例
database_monitor = DatabaseMonitor()

# 便捷函数
async def start_database_monitoring():
    """启动数据库监控"""
    await database_monitor.start_monitoring()

def stop_database_monitoring():
    """停止数据库监控"""
    database_monitor.stop_monitoring()

async def get_database_metrics_history(hours: int = 24) -> List[Dict[str, Any]]:
    """获取数据库指标历史"""
    return await database_monitor.get_metrics_history(hours)

async def get_database_alerts() -> List[Dict[str, Any]]:
    """获取数据库告警"""
    return await database_monitor.get_active_alerts()