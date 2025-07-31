"""
后端API性能优化工具
包含缓存、压缩、连接池等优化功能
"""
import time
import gzip
import json
import asyncio
from typing import Dict, Any, Optional, Callable, Union
from functools import wraps
from contextlib import asynccontextmanager
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis
import aioredis
from sqlalchemy.pool import QueuePool
from app.core.logging import get_logger

logger = get_logger(__name__)

class ResponseCompressionMiddleware(BaseHTTPMiddleware):
    """响应压缩中间件"""
    
    def __init__(
        self,
        app,
        minimum_size: int = 1024,
        compression_level: int = 6,
        exclude_paths: list = None
    ):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compression_level = compression_level
        self.exclude_paths = exclude_paths or []
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查是否需要压缩
        if not self._should_compress(request):
            return await call_next(request)
        
        response = await call_next(request)
        
        # 检查响应是否适合压缩
        if not self._can_compress_response(response):
            return response
        
        # 获取响应内容
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        
        # 检查内容大小
        if len(response_body) < self.minimum_size:
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        
        # 压缩内容
        compressed_body = gzip.compress(response_body, compresslevel=self.compression_level)
        
        # 创建压缩响应
        headers = dict(response.headers)
        headers["content-encoding"] = "gzip"
        headers["content-length"] = str(len(compressed_body))
        
        return Response(
            content=compressed_body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type
        )
    
    def _should_compress(self, request: Request) -> bool:
        """检查是否应该压缩"""
        # 检查Accept-Encoding头
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding:
            return False
        
        # 检查排除路径
        path = request.url.path
        if any(path.startswith(exclude_path) for exclude_path in self.exclude_paths):
            return False
        
        return True
    
    def _can_compress_response(self, response: Response) -> bool:
        """检查响应是否可以压缩"""
        # 检查状态码
        if response.status_code < 200 or response.status_code >= 300:
            return False
        
        # 检查Content-Type
        content_type = response.headers.get("content-type", "")
        compressible_types = [
            "application/json",
            "application/javascript",
            "text/html",
            "text/css",
            "text/plain",
            "text/xml"
        ]
        
        if not any(ct in content_type for ct in compressible_types):
            return False
        
        # 检查是否已经压缩
        if response.headers.get("content-encoding"):
            return False
        
        return True

class APICache:
    """API缓存管理器"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/4"):
        self.redis_client = None
        self.memory_cache = {}
        self.cache_stats = {"hits": 0, "misses": 0}
        
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis connection failed, using memory cache: {str(e)}")
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            if self.redis_client:
                cached_data = self.redis_client.get(key)
                if cached_data:
                    self.cache_stats["hits"] += 1
                    return json.loads(cached_data)
            else:
                cached_item = self.memory_cache.get(key)
                if cached_item and cached_item["expires"] > time.time():
                    self.cache_stats["hits"] += 1
                    return cached_item["data"]
                elif cached_item:
                    del self.memory_cache[key]
            
            self.cache_stats["misses"] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            self.cache_stats["misses"] += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """设置缓存"""
        try:
            if self.redis_client:
                serialized_value = json.dumps(value, default=str)
                return self.redis_client.setex(key, ttl, serialized_value)
            else:
                self.memory_cache[key] = {
                    "data": value,
                    "expires": time.time() + ttl
                }
                
                # 限制内存缓存大小
                if len(self.memory_cache) > 1000:
                    # 删除最旧的条目
                    oldest_key = min(self.memory_cache.keys(), 
                                   key=lambda k: self.memory_cache[k]["expires"])
                    del self.memory_cache[oldest_key]
                
                return True
                
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            if self.redis_client:
                return self.redis_client.delete(key) > 0
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False
    
    async def clear(self, pattern: str = "*") -> int:
        """清理缓存"""
        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
            else:
                cleared_count = 0
                keys_to_delete = []
                
                for key in self.memory_cache.keys():
                    if pattern == "*" or pattern in key:
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del self.memory_cache[key]
                    cleared_count += 1
                
                return cleared_count
                
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests,
            "cache_type": "redis" if self.redis_client else "memory",
            "memory_cache_size": len(self.memory_cache) if not self.redis_client else None
        }

# 全局缓存实例
api_cache = APICache()

def cache_response(ttl: int = 300, key_prefix: str = "api"):
    """API响应缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 构建缓存键
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # 没有request对象，直接执行函数
                return await func(*args, **kwargs)
            
            # 构建缓存键
            cache_key = f"{key_prefix}:{request.method}:{request.url.path}"
            if request.url.query:
                cache_key += f":{request.url.query}"
            
            # 尝试从缓存获取
            cached_result = await api_cache.get(cache_key)
            if cached_result is not None:
                return JSONResponse(content=cached_result)
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            if isinstance(result, JSONResponse):
                await api_cache.set(cache_key, result.body.decode(), ttl)
            elif isinstance(result, dict):
                await api_cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

class DatabaseConnectionPool:
    """数据库连接池管理器"""
    
    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 30,
        pool_timeout: int = 30,
        pool_recycle: int = 3600
    ):
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.pool = None
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "pool_hits": 0,
            "pool_misses": 0
        }
    
    def create_pool(self):
        """创建连接池"""
        from sqlalchemy import create_engine
        
        engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=True,  # 连接前检查
            echo=False
        )
        
        self.pool = engine.pool
        return engine
    
    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接"""
        connection = None
        try:
            connection = self.pool.connect()
            self.stats["active_connections"] += 1
            self.stats["pool_hits"] += 1
            yield connection
        except Exception as e:
            self.stats["pool_misses"] += 1
            logger.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if connection:
                connection.close()
                self.stats["active_connections"] -= 1
    
    def get_pool_status(self) -> Dict[str, Any]:
        """获取连接池状态"""
        if not self.pool:
            return {"status": "not_initialized"}
        
        return {
            "pool_size": self.pool.size(),
            "checked_in": self.pool.checkedin(),
            "checked_out": self.pool.checkedout(),
            "overflow": self.pool.overflow(),
            "invalid": self.pool.invalid(),
            "stats": self.stats
        }

class AsyncTaskMonitor:
    """异步任务监控器"""
    
    def __init__(self):
        self.tasks = {}
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "active_tasks": 0
        }
    
    def create_task(self, coro, name: str = None) -> asyncio.Task:
        """创建并监控异步任务"""
        task = asyncio.create_task(coro)
        task_id = id(task)
        
        self.tasks[task_id] = {
            "task": task,
            "name": name or f"task_{task_id}",
            "created_at": time.time(),
            "status": "running"
        }
        
        self.stats["total_tasks"] += 1
        self.stats["active_tasks"] += 1
        
        # 添加完成回调
        task.add_done_callback(lambda t: self._task_done_callback(task_id, t))
        
        return task
    
    def _task_done_callback(self, task_id: int, task: asyncio.Task):
        """任务完成回调"""
        if task_id in self.tasks:
            task_info = self.tasks[task_id]
            
            if task.exception():
                task_info["status"] = "failed"
                task_info["error"] = str(task.exception())
                self.stats["failed_tasks"] += 1
                logger.error(f"Task {task_info['name']} failed: {task.exception()}")
            else:
                task_info["status"] = "completed"
                self.stats["completed_tasks"] += 1
            
            task_info["completed_at"] = time.time()
            task_info["duration"] = task_info["completed_at"] - task_info["created_at"]
            
            self.stats["active_tasks"] -= 1
            
            # 清理完成的任务（保留最近100个）
            if len(self.tasks) > 100:
                completed_tasks = [
                    (tid, info) for tid, info in self.tasks.items()
                    if info["status"] in ["completed", "failed"]
                ]
                
                if len(completed_tasks) > 50:
                    # 删除最旧的任务
                    completed_tasks.sort(key=lambda x: x[1]["completed_at"])
                    for tid, _ in completed_tasks[:25]:
                        del self.tasks[tid]
    
    def get_task_stats(self) -> Dict[str, Any]:
        """获取任务统计"""
        active_tasks = [
            {"id": tid, "name": info["name"], "duration": time.time() - info["created_at"]}
            for tid, info in self.tasks.items()
            if info["status"] == "running"
        ]
        
        return {
            "stats": self.stats.copy(),
            "active_tasks": active_tasks,
            "total_tracked_tasks": len(self.tasks)
        }
    
    def cancel_all_tasks(self):
        """取消所有活跃任务"""
        cancelled_count = 0
        for task_info in self.tasks.values():
            if task_info["status"] == "running":
                task_info["task"].cancel()
                cancelled_count += 1
        
        return cancelled_count

# 全局实例
db_pool = DatabaseConnectionPool("postgresql://user:pass@localhost/db")
task_monitor = AsyncTaskMonitor()

class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        self.request_stats = {
            "total_requests": 0,
            "total_response_time": 0,
            "slow_requests": 0,
            "error_requests": 0
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 增加请求计数
        self.request_stats["total_requests"] += 1
        
        try:
            response = await call_next(request)
            
            # 计算响应时间
            response_time = time.time() - start_time
            self.request_stats["total_response_time"] += response_time
            
            # 检查慢请求
            if response_time > 2.0:  # 2秒以上为慢请求
                self.request_stats["slow_requests"] += 1
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path} - "
                    f"{response_time:.3f}s"
                )
            
            # 检查错误响应
            if response.status_code >= 400:
                self.request_stats["error_requests"] += 1
            
            # 添加性能头
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            
            return response
            
        except Exception as e:
            self.request_stats["error_requests"] += 1
            logger.error(f"Request processing error: {str(e)}")
            raise
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        total_requests = self.request_stats["total_requests"]
        if total_requests == 0:
            return self.request_stats
        
        avg_response_time = self.request_stats["total_response_time"] / total_requests
        slow_request_rate = (self.request_stats["slow_requests"] / total_requests) * 100
        error_rate = (self.request_stats["error_requests"] / total_requests) * 100
        
        return {
            **self.request_stats,
            "avg_response_time": round(avg_response_time, 3),
            "slow_request_rate": round(slow_request_rate, 2),
            "error_rate": round(error_rate, 2)
        }

# 全局性能中间件实例
performance_middleware = PerformanceMiddleware