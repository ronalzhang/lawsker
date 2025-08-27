"""
Lawsker系统性能监控和优化模块
实现系统性能指标监控、缓存优化、数据库优化等功能
"""

import time
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from functools import wraps
import redis
import psutil
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import aioredis
from contextlib import asynccontextmanager

# from app.core.database import get_db
# from app.core.cache import get_redis_client

logger = logging.getLogger(__name__)

# Prometheus指标定义
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_USERS = Gauge('active_users_total', 'Number of active users')
DATABASE_CONNECTIONS = Gauge('database_connections_active', 'Active database connections')
CACHE_HIT_RATE = Gauge('cache_hit_rate', 'Cache hit rate percentage')
SYSTEM_CPU_USAGE = Gauge('system_cpu_usage_percent', 'System CPU usage percentage')
SYSTEM_MEMORY_USAGE = Gauge('system_memory_usage_percent', 'System memory usage percentage')

# 业务指标
AUTH_RESPONSE_TIME = Histogram('auth_response_time_seconds', 'Authentication response time')
POINTS_CALCULATION_TIME = Histogram('points_calculation_time_seconds', 'Points calculation time')
CREDITS_PAYMENT_TIME = Histogram('credits_payment_time_seconds', 'Credits payment processing time')
CONCURRENT_USERS = Gauge('concurrent_users_count', 'Current concurrent users')

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.redis_client = None
        self.performance_data = {}
        self.alert_thresholds = {
            'auth_response_time': 1.0,  # 1秒
            'points_calculation_time': 0.5,  # 500ms
            'credits_payment_time': 2.0,  # 2秒
            'cpu_usage': 80.0,  # 80%
            'memory_usage': 85.0,  # 85%
            'database_connections': 80,  # 80个连接
        }
    
    async def initialize(self):
        """初始化监控器"""
        try:
            # self.redis_client = await get_redis_client()
            # 启动Prometheus指标服务器
            start_http_server(8001)
            logger.info("Performance monitor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize performance monitor: {e}")
    
    def performance_timer(self, metric_name: str):
        """性能计时装饰器"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # 记录指标
                    if metric_name == 'auth':
                        AUTH_RESPONSE_TIME.observe(duration)
                    elif metric_name == 'points':
                        POINTS_CALCULATION_TIME.observe(duration)
                    elif metric_name == 'credits':
                        CREDITS_PAYMENT_TIME.observe(duration)
                    
                    REQUEST_DURATION.observe(duration)
                    
                    # 检查性能阈值
                    await self._check_performance_threshold(metric_name, duration)
                    
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(f"Performance error in {metric_name}: {e}, duration: {duration}s")
                    raise
            return wrapper
        return decorator
    
    async def _check_performance_threshold(self, metric_name: str, duration: float):
        """检查性能阈值"""
        threshold_key = f"{metric_name}_response_time"
        if threshold_key in self.alert_thresholds:
            threshold = self.alert_thresholds[threshold_key]
            if duration > threshold:
                await self._send_performance_alert(metric_name, duration, threshold)
    
    async def _send_performance_alert(self, metric_name: str, actual: float, threshold: float):
        """发送性能告警"""
        alert_data = {
            'type': 'performance_alert',
            'metric': metric_name,
            'actual_value': actual,
            'threshold': threshold,
            'timestamp': datetime.now().isoformat(),
            'severity': 'warning' if actual < threshold * 1.5 else 'critical'
        }
        
        try:
            if self.redis_client:
                await self.redis_client.publish('performance_alerts', str(alert_data))
            logger.warning(f"Performance alert: {metric_name} took {actual:.3f}s (threshold: {threshold}s)")
        except Exception as e:
            logger.error(f"Failed to send performance alert: {e}")
    
    async def collect_system_metrics(self):
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            SYSTEM_CPU_USAGE.set(cpu_percent)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            SYSTEM_MEMORY_USAGE.set(memory.percent)
            
            # 检查系统资源阈值
            if cpu_percent > self.alert_thresholds['cpu_usage']:
                await self._send_system_alert('cpu_usage', cpu_percent)
            
            if memory.percent > self.alert_thresholds['memory_usage']:
                await self._send_system_alert('memory_usage', memory.percent)
                
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    async def _send_system_alert(self, metric_type: str, value: float):
        """发送系统告警"""
        alert_data = {
            'type': 'system_alert',
            'metric': metric_type,
            'value': value,
            'threshold': self.alert_thresholds[metric_type],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if self.redis_client:
                await self.redis_client.publish('system_alerts', str(alert_data))
            logger.warning(f"System alert: {metric_type} at {value}% (threshold: {self.alert_thresholds[metric_type]}%)")
        except Exception as e:
            logger.error(f"Failed to send system alert: {e}")
    
    async def update_concurrent_users(self, count: int):
        """更新并发用户数"""
        CONCURRENT_USERS.set(count)
        ACTIVE_USERS.set(count)
        
        # 检查并发用户数是否超过1000
        if count > 1000:
            logger.info(f"High concurrent users: {count}")

class DatabaseOptimizer:
    """数据库性能优化器"""
    
    def __init__(self):
        self.connection_pool_size = 20
        self.max_overflow = 30
        self.pool_timeout = 30
        self.pool_recycle = 3600
    
    async def optimize_query_performance(self, db: AsyncSession):
        """优化查询性能"""
        try:
            # 检查慢查询
            slow_queries = await self._get_slow_queries(db)
            if slow_queries:
                logger.warning(f"Found {len(slow_queries)} slow queries")
                await self._analyze_slow_queries(slow_queries)
            
            # 检查数据库连接数
            connection_count = await self._get_connection_count(db)
            DATABASE_CONNECTIONS.set(connection_count)
            
            if connection_count > self.alert_thresholds.get('database_connections', 80):
                logger.warning(f"High database connections: {connection_count}")
                
        except Exception as e:
            logger.error(f"Database optimization error: {e}")
    
    async def _get_slow_queries(self, db: AsyncSession) -> List[Dict]:
        """获取慢查询"""
        try:
            query = text("""
                SELECT query, mean_time, calls, total_time
                FROM pg_stat_statements 
                WHERE mean_time > 1000 
                ORDER BY mean_time DESC 
                LIMIT 10
            """)
            result = await db.execute(query)
            return [dict(row) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get slow queries: {e}")
            return []
    
    async def _analyze_slow_queries(self, slow_queries: List[Dict]):
        """分析慢查询"""
        for query in slow_queries:
            logger.warning(f"Slow query detected: {query['query'][:100]}... "
                         f"Mean time: {query['mean_time']:.2f}ms, "
                         f"Calls: {query['calls']}")
    
    async def _get_connection_count(self, db: AsyncSession) -> int:
        """获取数据库连接数"""
        try:
            query = text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
            result = await db.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Failed to get connection count: {e}")
            return 0

class CacheOptimizer:
    """缓存优化器"""
    
    def __init__(self):
        self.redis_client = None
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0
        }
    
    async def initialize(self):
        """初始化缓存优化器"""
        try:
            self.redis_client = await get_redis_client()
            logger.info("Cache optimizer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize cache optimizer: {e}")
    
    async def get_with_cache(self, key: str, fetch_func, expire: int = 300):
        """带缓存的数据获取"""
        try:
            # 尝试从缓存获取
            cached_data = await self.redis_client.get(key)
            if cached_data:
                self.cache_stats['hits'] += 1
                self._update_cache_hit_rate()
                return eval(cached_data)  # 注意：生产环境应使用json.loads
            
            # 缓存未命中，从数据源获取
            self.cache_stats['misses'] += 1
            data = await fetch_func()
            
            # 存入缓存
            await self.redis_client.setex(key, expire, str(data))
            self._update_cache_hit_rate()
            
            return data
            
        except Exception as e:
            logger.error(f"Cache operation error: {e}")
            # 缓存失败时直接从数据源获取
            return await fetch_func()
    
    def _update_cache_hit_rate(self):
        """更新缓存命中率"""
        self.cache_stats['total_requests'] = self.cache_stats['hits'] + self.cache_stats['misses']
        if self.cache_stats['total_requests'] > 0:
            hit_rate = (self.cache_stats['hits'] / self.cache_stats['total_requests']) * 100
            CACHE_HIT_RATE.set(hit_rate)
    
    async def warm_up_cache(self):
        """缓存预热"""
        try:
            # 预热常用数据
            warm_up_keys = [
                'lawyer_levels',
                'membership_tiers',
                'system_config',
                'active_promotions'
            ]
            
            for key in warm_up_keys:
                # 这里应该调用相应的数据获取函数
                logger.info(f"Warming up cache for key: {key}")
                
        except Exception as e:
            logger.error(f"Cache warm-up error: {e}")

class PerformanceOptimizer:
    """性能优化器主类"""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.db_optimizer = DatabaseOptimizer()
        self.cache_optimizer = CacheOptimizer()
        self.optimization_tasks = []
    
    async def initialize(self):
        """初始化性能优化器"""
        await self.monitor.initialize()
        await self.cache_optimizer.initialize()
        
        # 启动后台优化任务
        self.optimization_tasks = [
            asyncio.create_task(self._system_metrics_collector()),
            asyncio.create_task(self._performance_analyzer()),
            asyncio.create_task(self._cache_maintenance())
        ]
        
        logger.info("Performance optimizer initialized")
    
    async def _system_metrics_collector(self):
        """系统指标收集器"""
        while True:
            try:
                await self.monitor.collect_system_metrics()
                await asyncio.sleep(30)  # 每30秒收集一次
            except Exception as e:
                logger.error(f"System metrics collection error: {e}")
                await asyncio.sleep(60)
    
    async def _performance_analyzer(self):
        """性能分析器"""
        while True:
            try:
                # 分析性能数据
                await self._analyze_performance_trends()
                await asyncio.sleep(300)  # 每5分钟分析一次
            except Exception as e:
                logger.error(f"Performance analysis error: {e}")
                await asyncio.sleep(600)
    
    async def _cache_maintenance(self):
        """缓存维护"""
        while True:
            try:
                # 缓存预热和清理
                await self.cache_optimizer.warm_up_cache()
                await asyncio.sleep(3600)  # 每小时执行一次
            except Exception as e:
                logger.error(f"Cache maintenance error: {e}")
                await asyncio.sleep(1800)
    
    async def _analyze_performance_trends(self):
        """分析性能趋势"""
        try:
            # 这里可以添加性能趋势分析逻辑
            # 比如检测性能下降、预测资源需求等
            logger.info("Performance trend analysis completed")
        except Exception as e:
            logger.error(f"Performance trend analysis error: {e}")
    
    async def shutdown(self):
        """关闭优化器"""
        for task in self.optimization_tasks:
            task.cancel()
        
        try:
            await asyncio.gather(*self.optimization_tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        logger.info("Performance optimizer shutdown completed")

# 全局性能优化器实例
performance_optimizer = PerformanceOptimizer()

# 装饰器函数
def monitor_auth_performance(func):
    """监控认证性能"""
    return performance_optimizer.monitor.performance_timer('auth')(func)

def monitor_points_performance(func):
    """监控积分计算性能"""
    return performance_optimizer.monitor.performance_timer('points')(func)

def monitor_credits_performance(func):
    """监控Credits支付性能"""
    return performance_optimizer.monitor.performance_timer('credits')(func)

@asynccontextmanager
async def performance_context():
    """性能监控上下文管理器"""
    await performance_optimizer.initialize()
    try:
        yield performance_optimizer
    finally:
        await performance_optimizer.shutdown()