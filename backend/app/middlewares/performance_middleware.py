"""
性能监控中间件
监控所有HTTP请求的性能指标，确保满足性能要求
"""

import time
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from prometheus_client import Counter, Histogram
import asyncio

from app.core.performance_monitor import (
    REQUEST_COUNT, 
    REQUEST_DURATION, 
    CONCURRENT_USERS,
    performance_optimizer
)

logger = logging.getLogger(__name__)

class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    def __init__(self, app, performance_thresholds: dict = None):
        super().__init__(app)
        self.performance_thresholds = performance_thresholds or {
            '/api/v1/auth/': 1.0,  # 认证接口1秒
            '/api/v1/points/': 0.5,  # 积分接口500ms
            '/api/v1/credits/': 2.0,  # Credits接口2秒
            'default': 3.0  # 默认3秒
        }
        self.concurrent_requests = 0
        self.request_lock = asyncio.Lock()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并监控性能"""
        start_time = time.time()
        
        # 增加并发请求计数
        async with self.request_lock:
            self.concurrent_requests += 1
            CONCURRENT_USERS.set(self.concurrent_requests)
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算响应时间
            duration = time.time() - start_time
            
            # 记录指标
            method = request.method
            path = request.url.path
            status_code = response.status_code
            
            REQUEST_COUNT.labels(method=method, endpoint=path, status=status_code).inc()
            REQUEST_DURATION.observe(duration)
            
            # 检查性能阈值
            await self._check_performance_threshold(path, duration)
            
            # 添加性能头信息
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            response.headers["X-Concurrent-Requests"] = str(self.concurrent_requests)
            
            # 记录慢请求
            if duration > 2.0:  # 超过2秒的请求
                logger.warning(f"Slow request: {method} {path} took {duration:.3f}s")
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Request error: {request.method} {request.url.path} - {e}, duration: {duration:.3f}s")
            
            # 记录错误指标
            REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=500).inc()
            REQUEST_DURATION.observe(duration)
            
            raise
        
        finally:
            # 减少并发请求计数
            async with self.request_lock:
                self.concurrent_requests = max(0, self.concurrent_requests - 1)
                CONCURRENT_USERS.set(self.concurrent_requests)
    
    async def _check_performance_threshold(self, path: str, duration: float):
        """检查性能阈值"""
        threshold = self._get_threshold_for_path(path)
        
        if duration > threshold:
            await self._send_performance_alert(path, duration, threshold)
    
    def _get_threshold_for_path(self, path: str) -> float:
        """获取路径对应的性能阈值"""
        for pattern, threshold in self.performance_thresholds.items():
            if pattern in path:
                return threshold
        return self.performance_thresholds['default']
    
    async def _send_performance_alert(self, path: str, duration: float, threshold: float):
        """发送性能告警"""
        alert_data = {
            'type': 'api_performance_alert',
            'path': path,
            'duration': duration,
            'threshold': threshold,
            'severity': 'warning' if duration < threshold * 1.5 else 'critical'
        }
        
        try:
            # 通过性能优化器发送告警
            if hasattr(performance_optimizer, 'monitor') and performance_optimizer.monitor.redis_client:
                await performance_optimizer.monitor.redis_client.publish(
                    'api_performance_alerts', 
                    str(alert_data)
                )
        except Exception as e:
            logger.error(f"Failed to send API performance alert: {e}")

class ConcurrencyLimitMiddleware(BaseHTTPMiddleware):
    """并发限制中间件"""
    
    def __init__(self, app, max_concurrent_requests: int = 1000):
        super().__init__(app)
        self.max_concurrent_requests = max_concurrent_requests
        self.current_requests = 0
        self.request_semaphore = asyncio.Semaphore(max_concurrent_requests)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理并发限制"""
        # 检查是否超过并发限制
        if self.current_requests >= self.max_concurrent_requests:
            logger.warning(f"Concurrent request limit exceeded: {self.current_requests}")
            return Response(
                content="Server is busy, please try again later",
                status_code=503,
                headers={"Retry-After": "5"}
            )
        
        async with self.request_semaphore:
            self.current_requests += 1
            try:
                response = await call_next(request)
                return response
            finally:
                self.current_requests -= 1

class ResponseCompressionMiddleware(BaseHTTPMiddleware):
    """响应压缩中间件"""
    
    def __init__(self, app, min_size: int = 1024):
        super().__init__(app)
        self.min_size = min_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理响应压缩"""
        response = await call_next(request)
        
        # 检查是否支持压缩
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding.lower():
            return response
        
        # 检查响应大小
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) < self.min_size:
            return response
        
        # 这里可以添加gzip压缩逻辑
        # 为了简化，暂时只添加压缩标识
        response.headers["X-Compression-Available"] = "gzip"
        
        return response

class CacheControlMiddleware(BaseHTTPMiddleware):
    """缓存控制中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        self.cache_rules = {
            '/static/': 'public, max-age=86400',  # 静态资源缓存1天
            '/api/v1/config/': 'public, max-age=300',  # 配置接口缓存5分钟
            '/api/v1/levels/': 'public, max-age=600',  # 等级信息缓存10分钟
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理缓存控制"""
        response = await call_next(request)
        
        # 设置缓存头
        path = request.url.path
        for pattern, cache_control in self.cache_rules.items():
            if path.startswith(pattern):
                response.headers["Cache-Control"] = cache_control
                break
        else:
            # 默认不缓存API响应
            if path.startswith('/api/'):
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        
        return response