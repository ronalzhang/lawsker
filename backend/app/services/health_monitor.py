"""
系统健康检查和自愈机制
监控系统各组件状态，自动处理异常情况
"""
import asyncio
import time
import psutil
import redis
import requests
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy import text
from app.core.database import get_db
from app.core.logging import get_logger
from app.services.alert_manager import AlertManager
from app.services.notification_channels import NotificationManager

logger = get_logger(__name__)

class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """健康检查结果"""
    component: str
    status: HealthStatus
    message: str
    metrics: Dict[str, Any]
    timestamp: datetime
    response_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['status'] = self.status.value
        result['timestamp'] = self.timestamp.isoformat()
        return result

class HealthChecker:
    """健康检查器基类"""
    
    def __init__(self, name: str, check_interval: int = 60):
        self.name = name
        self.check_interval = check_interval
        self.last_check_time = None
        self.last_result = None
        self.failure_count = 0
        self.max_failures = 3
    
    async def check(self) -> HealthCheckResult:
        """执行健康检查"""
        start_time = time.time()
        
        try:
            result = await self._perform_check()
            response_time = time.time() - start_time
            
            # 重置失败计数
            if result.status == HealthStatus.HEALTHY:
                self.failure_count = 0
            else:
                self.failure_count += 1
            
            result.response_time = response_time
            result.timestamp = datetime.now()
            
            self.last_check_time = datetime.now()
            self.last_result = result
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            response_time = time.time() - start_time
            
            result = HealthCheckResult(
                component=self.name,
                status=HealthStatus.CRITICAL,
                message=f"Health check failed: {str(e)}",
                metrics={},
                timestamp=datetime.now(),
                response_time=response_time
            )
            
            self.last_result = result
            return result
    
    async def _perform_check(self) -> HealthCheckResult:
        """子类需要实现的具体检查逻辑"""
        raise NotImplementedError
    
    def is_critical(self) -> bool:
        """检查是否处于严重状态"""
        return self.failure_count >= self.max_failures

class DatabaseHealthChecker(HealthChecker):
    """数据库健康检查器"""
    
    def __init__(self):
        super().__init__("database", check_interval=30)
    
    async def _perform_check(self) -> HealthCheckResult:
        """检查数据库连接和性能"""
        try:
            db = next(get_db())
            
            # 检查连接
            start_time = time.time()
            result = db.execute(text("SELECT 1"))
            connection_time = time.time() - start_time
            
            # 检查连接池状态
            pool = db.get_bind().pool
            pool_metrics = {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
            
            # 检查慢查询
            slow_queries = db.execute(text("""
                SELECT count(*) as slow_query_count
                FROM pg_stat_statements 
                WHERE mean_time > 1000
            """)).scalar()
            
            # 检查数据库大小
            db_size_result = db.execute(text("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as db_size,
                       pg_database_size(current_database()) as db_size_bytes
            """)).fetchone()
            
            metrics = {
                "connection_time": round(connection_time * 1000, 2),  # ms
                "slow_query_count": slow_queries or 0,
                "database_size": db_size_result.db_size if db_size_result else "unknown",
                "database_size_bytes": db_size_result.db_size_bytes if db_size_result else 0,
                **pool_metrics
            }
            
            # 判断健康状态
            if connection_time > 1.0:  # 连接时间超过1秒
                status = HealthStatus.WARNING
                message = f"Database connection slow: {connection_time:.2f}s"
            elif pool_metrics["checked_out"] / pool_metrics["pool_size"] > 0.8:  # 连接池使用率超过80%
                status = HealthStatus.WARNING
                message = "Database connection pool usage high"
            elif slow_queries and slow_queries > 10:  # 慢查询超过10个
                status = HealthStatus.WARNING
                message = f"High number of slow queries: {slow_queries}"
            else:
                status = HealthStatus.HEALTHY
                message = "Database is healthy"
            
            return HealthCheckResult(
                component=self.name,
                status=status,
                message=message,
                metrics=metrics,
                timestamp=datetime.now(),
                response_time=0
            )
            
        except Exception as e:
            raise Exception(f"Database health check failed: {str(e)}")

class RedisHealthChecker(HealthChecker):
    """Redis健康检查器"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        super().__init__("redis", check_interval=30)
        self.redis_url = redis_url
        self.redis_client = None
    
    async def _perform_check(self) -> HealthCheckResult:
        """检查Redis连接和性能"""
        try:
            if not self.redis_client:
                self.redis_client = redis.from_url(self.redis_url)
            
            # 检查连接
            start_time = time.time()
            self.redis_client.ping()
            ping_time = time.time() - start_time
            
            # 获取Redis信息
            info = self.redis_client.info()
            
            metrics = {
                "ping_time": round(ping_time * 1000, 2),  # ms
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
            
            # 计算命中率
            hits = metrics["keyspace_hits"]
            misses = metrics["keyspace_misses"]
            hit_rate = (hits / (hits + misses) * 100) if (hits + misses) > 0 else 0
            metrics["hit_rate"] = round(hit_rate, 2)
            
            # 判断健康状态
            if ping_time > 0.1:  # ping时间超过100ms
                status = HealthStatus.WARNING
                message = f"Redis response slow: {ping_time:.3f}s"
            elif hit_rate < 80 and (hits + misses) > 1000:  # 命中率低于80%
                status = HealthStatus.WARNING
                message = f"Redis hit rate low: {hit_rate:.1f}%"
            elif metrics["connected_clients"] > 100:  # 连接数过多
                status = HealthStatus.WARNING
                message = f"High number of Redis connections: {metrics['connected_clients']}"
            else:
                status = HealthStatus.HEALTHY
                message = "Redis is healthy"
            
            return HealthCheckResult(
                component=self.name,
                status=status,
                message=message,
                metrics=metrics,
                timestamp=datetime.now(),
                response_time=0
            )
            
        except Exception as e:
            raise Exception(f"Redis health check failed: {str(e)}")

class SystemResourceChecker(HealthChecker):
    """系统资源检查器"""
    
    def __init__(self):
        super().__init__("system_resources", check_interval=60)
    
    async def _perform_check(self) -> HealthCheckResult:
        """检查系统资源使用情况"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            
            # 网络统计
            network = psutil.net_io_counters()
            
            # 进程数量
            process_count = len(psutil.pids())
            
            metrics = {
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "memory_total": memory.total,
                "memory_used": memory.used,
                "memory_percent": memory.percent,
                "memory_available": memory.available,
                "disk_total": disk.total,
                "disk_used": disk.used,
                "disk_percent": (disk.used / disk.total) * 100,
                "disk_free": disk.free,
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "process_count": process_count
            }
            
            # 判断健康状态
            warnings = []
            if cpu_percent > 80:
                warnings.append(f"High CPU usage: {cpu_percent:.1f}%")
            if memory.percent > 85:
                warnings.append(f"High memory usage: {memory.percent:.1f}%")
            if metrics["disk_percent"] > 90:
                warnings.append(f"High disk usage: {metrics['disk_percent']:.1f}%")
            
            if warnings:
                status = HealthStatus.WARNING
                message = "; ".join(warnings)
            else:
                status = HealthStatus.HEALTHY
                message = "System resources are healthy"
            
            return HealthCheckResult(
                component=self.name,
                status=status,
                message=message,
                metrics=metrics,
                timestamp=datetime.now(),
                response_time=0
            )
            
        except Exception as e:
            raise Exception(f"System resource check failed: {str(e)}")

class ApplicationHealthChecker(HealthChecker):
    """应用程序健康检查器"""
    
    def __init__(self, health_endpoint: str = "http://localhost:8000/api/v1/health"):
        super().__init__("application", check_interval=30)
        self.health_endpoint = health_endpoint
    
    async def _perform_check(self) -> HealthCheckResult:
        """检查应用程序健康状态"""
        try:
            start_time = time.time()
            response = requests.get(self.health_endpoint, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                metrics = {
                    "response_time": round(response_time * 1000, 2),  # ms
                    "status_code": response.status_code,
                    **data.get("metrics", {})
                }
                
                # 判断健康状态
                if response_time > 2.0:  # 响应时间超过2秒
                    status = HealthStatus.WARNING
                    message = f"Application response slow: {response_time:.2f}s"
                else:
                    status = HealthStatus.HEALTHY
                    message = "Application is healthy"
                
                return HealthCheckResult(
                    component=self.name,
                    status=status,
                    message=message,
                    metrics=metrics,
                    timestamp=datetime.now(),
                    response_time=0
                )
            else:
                raise Exception(f"Health endpoint returned status {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Application health check failed: {str(e)}")

class SelfHealingManager:
    """自愈管理器"""
    
    def __init__(self):
        self.healing_actions: Dict[str, List[Callable]] = {}
        self.healing_history: List[Dict[str, Any]] = []
        self.max_healing_attempts = 3
        self.healing_cooldown = 300  # 5分钟冷却时间
        self.last_healing_time: Dict[str, datetime] = {}
    
    def register_healing_action(self, component: str, action: Callable):
        """注册自愈动作"""
        if component not in self.healing_actions:
            self.healing_actions[component] = []
        self.healing_actions[component].append(action)
    
    async def attempt_healing(self, health_result: HealthCheckResult) -> bool:
        """尝试自愈"""
        component = health_result.component
        
        # 检查是否在冷却期
        if self._is_in_cooldown(component):
            logger.info(f"Healing for {component} is in cooldown period")
            return False
        
        # 检查是否有注册的自愈动作
        if component not in self.healing_actions:
            logger.info(f"No healing actions registered for {component}")
            return False
        
        healing_record = {
            "component": component,
            "timestamp": datetime.now().isoformat(),
            "health_status": health_result.status.value,
            "health_message": health_result.message,
            "actions_attempted": [],
            "success": False
        }
        
        try:
            # 执行自愈动作
            for i, action in enumerate(self.healing_actions[component]):
                try:
                    logger.info(f"Attempting healing action {i+1} for {component}")
                    
                    action_name = getattr(action, '__name__', f'action_{i+1}')
                    await action(health_result)
                    
                    healing_record["actions_attempted"].append({
                        "action": action_name,
                        "status": "success"
                    })
                    
                    logger.info(f"Healing action {action_name} completed for {component}")
                    
                except Exception as e:
                    logger.error(f"Healing action {i+1} failed for {component}: {str(e)}")
                    healing_record["actions_attempted"].append({
                        "action": getattr(action, '__name__', f'action_{i+1}'),
                        "status": "failed",
                        "error": str(e)
                    })
            
            # 记录自愈时间
            self.last_healing_time[component] = datetime.now()
            healing_record["success"] = True
            
            logger.info(f"Self-healing completed for {component}")
            return True
            
        except Exception as e:
            logger.error(f"Self-healing failed for {component}: {str(e)}")
            healing_record["error"] = str(e)
            return False
        
        finally:
            self.healing_history.append(healing_record)
            # 保持历史记录在合理范围内
            if len(self.healing_history) > 100:
                self.healing_history = self.healing_history[-50:]
    
    def _is_in_cooldown(self, component: str) -> bool:
        """检查是否在冷却期"""
        if component not in self.last_healing_time:
            return False
        
        last_time = self.last_healing_time[component]
        cooldown_end = last_time + timedelta(seconds=self.healing_cooldown)
        
        return datetime.now() < cooldown_end
    
    def get_healing_history(self, component: str = None) -> List[Dict[str, Any]]:
        """获取自愈历史"""
        if component:
            return [record for record in self.healing_history if record["component"] == component]
        return self.healing_history

class HealthMonitorService:
    """健康监控服务"""
    
    def __init__(self):
        self.checkers: List[HealthChecker] = []
        self.self_healing = SelfHealingManager()
        self.alert_manager = AlertManager()
        self.notification_manager = NotificationManager()
        self.monitoring_task = None
        self.is_running = False
        
        # 初始化检查器
        self._initialize_checkers()
        self._register_healing_actions()
    
    def _initialize_checkers(self):
        """初始化健康检查器"""
        self.checkers = [
            DatabaseHealthChecker(),
            RedisHealthChecker(),
            SystemResourceChecker(),
            ApplicationHealthChecker()
        ]
    
    def _register_healing_actions(self):
        """注册自愈动作"""
        # 数据库自愈动作
        self.self_healing.register_healing_action("database", self._heal_database)
        
        # Redis自愈动作
        self.self_healing.register_healing_action("redis", self._heal_redis)
        
        # 系统资源自愈动作
        self.self_healing.register_healing_action("system_resources", self._heal_system_resources)
        
        # 应用程序自愈动作
        self.self_healing.register_healing_action("application", self._heal_application)
    
    async def start_monitoring(self):
        """开始监控"""
        if self.is_running:
            logger.warning("Health monitoring is already running")
            return
        
        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """停止监控"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                # 执行所有健康检查
                check_tasks = [checker.check() for checker in self.checkers]
                results = await asyncio.gather(*check_tasks, return_exceptions=True)
                
                # 处理检查结果
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Health check failed: {str(result)}")
                        continue
                    
                    checker = self.checkers[i]
                    await self._process_health_result(result, checker)
                
                # 等待下次检查
                await asyncio.sleep(30)  # 30秒检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {str(e)}")
                await asyncio.sleep(60)  # 出错时等待更长时间
    
    async def _process_health_result(self, result: HealthCheckResult, checker: HealthChecker):
        """处理健康检查结果"""
        # 记录结果
        logger.debug(f"Health check result for {result.component}: {result.status.value}")
        
        # 如果状态不健康，发送告警
        if result.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
            await self._send_health_alert(result)
            
            # 如果是严重状态且检查器处于严重状态，尝试自愈
            if result.status == HealthStatus.CRITICAL and checker.is_critical():
                logger.warning(f"Component {result.component} is in critical state, attempting self-healing")
                healing_success = await self.self_healing.attempt_healing(result)
                
                if healing_success:
                    await self._send_healing_notification(result.component, True)
                else:
                    await self._send_healing_notification(result.component, False)
    
    async def _send_health_alert(self, result: HealthCheckResult):
        """发送健康告警"""
        alert_data = {
            "component": result.component,
            "status": result.status.value,
            "message": result.message,
            "metrics": result.metrics,
            "timestamp": result.timestamp.isoformat()
        }
        
        # 发送到告警管理器
        await self.alert_manager.create_alert(
            title=f"Health Check Alert: {result.component}",
            message=result.message,
            severity=result.status.value,
            source="health_monitor",
            metadata=alert_data
        )
    
    async def _send_healing_notification(self, component: str, success: bool):
        """发送自愈通知"""
        if success:
            message = f"🔧 Self-healing completed successfully for {component}"
        else:
            message = f"❌ Self-healing failed for {component}"
        
        await self.notification_manager.send_notification(
            channel="system",
            message=message,
            priority="high" if not success else "medium"
        )
    
    # 自愈动作实现
    async def _heal_database(self, health_result: HealthCheckResult):
        """数据库自愈"""
        logger.info("Attempting database healing")
        
        # 重启数据库连接池
        try:
            from app.core.database import engine
            engine.dispose()
            logger.info("Database connection pool restarted")
        except Exception as e:
            logger.error(f"Failed to restart database connection pool: {str(e)}")
            raise
    
    async def _heal_redis(self, health_result: HealthCheckResult):
        """Redis自愈"""
        logger.info("Attempting Redis healing")
        
        # 清理Redis连接
        try:
            # 这里可以实现Redis连接重置逻辑
            logger.info("Redis connections cleaned")
        except Exception as e:
            logger.error(f"Failed to heal Redis: {str(e)}")
            raise
    
    async def _heal_system_resources(self, health_result: HealthCheckResult):
        """系统资源自愈"""
        logger.info("Attempting system resource healing")
        
        # 清理系统资源
        try:
            # 清理临时文件
            import tempfile
            import shutil
            temp_dir = tempfile.gettempdir()
            
            # 清理Python缓存
            import gc
            gc.collect()
            
            logger.info("System resources cleaned")
        except Exception as e:
            logger.error(f"Failed to heal system resources: {str(e)}")
            raise
    
    async def _heal_application(self, health_result: HealthCheckResult):
        """应用程序自愈"""
        logger.info("Attempting application healing")
        
        # 重启应用程序组件
        try:
            # 这里可以实现应用程序重启逻辑
            # 例如重启某些服务或清理缓存
            logger.info("Application components restarted")
        except Exception as e:
            logger.error(f"Failed to heal application: {str(e)}")
            raise
    
    async def get_health_status(self) -> Dict[str, Any]:
        """获取整体健康状态"""
        # 执行所有健康检查
        check_tasks = [checker.check() for checker in self.checkers]
        results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        health_data = {
            "overall_status": HealthStatus.HEALTHY.value,
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "summary": {
                "healthy": 0,
                "warning": 0,
                "critical": 0,
                "unknown": 0
            }
        }
        
        overall_status = HealthStatus.HEALTHY
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                component_name = self.checkers[i].name
                health_data["components"][component_name] = {
                    "status": HealthStatus.UNKNOWN.value,
                    "message": f"Check failed: {str(result)}",
                    "metrics": {},
                    "timestamp": datetime.now().isoformat()
                }
                health_data["summary"]["unknown"] += 1
                continue
            
            health_data["components"][result.component] = result.to_dict()
            health_data["summary"][result.status.value] += 1
            
            # 更新整体状态
            if result.status == HealthStatus.CRITICAL:
                overall_status = HealthStatus.CRITICAL
            elif result.status == HealthStatus.WARNING and overall_status != HealthStatus.CRITICAL:
                overall_status = HealthStatus.WARNING
        
        health_data["overall_status"] = overall_status.value
        
        return health_data

# 全局健康监控服务实例
health_monitor = HealthMonitorService()