"""
高级缓存系统
实现多层缓存、缓存预热、智能失效等功能
"""

import json
import time
import logging
import asyncio
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import pickle
import aioredis
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class CacheLevel:
    """缓存级别枚举"""
    MEMORY = "memory"
    REDIS = "redis"
    DATABASE = "database"

class CacheStrategy:
    """缓存策略"""
    LRU = "lru"  # 最近最少使用
    LFU = "lfu"  # 最少使用频率
    TTL = "ttl"  # 基于时间
    WRITE_THROUGH = "write_through"  # 写穿透
    WRITE_BACK = "write_back"  # 写回

class MemoryCache:
    """内存缓存"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = {}
        self.access_times = {}
        self.access_counts = {}
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        if key not in self.cache:
            return None
        
        # 检查TTL
        if time.time() - self.cache[key]['timestamp'] > self.ttl:
            self._remove(key)
            return None
        
        # 更新访问统计
        self.access_times[key] = time.time()
        self.access_counts[key] = self.access_counts.get(key, 0) + 1
        
        return self.cache[key]['data']
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存数据"""
        # 检查容量限制
        if len(self.cache) >= self.max_size and key not in self.cache:
            self._evict_one()
        
        self.cache[key] = {
            'data': value,
            'timestamp': time.time()
        }
        self.access_times[key] = time.time()
        self.access_counts[key] = self.access_counts.get(key, 0) + 1
    
    def delete(self, key: str) -> bool:
        """删除缓存数据"""
        return self._remove(key)
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.access_times.clear()
        self.access_counts.clear()
    
    def _remove(self, key: str) -> bool:
        """移除缓存项"""
        if key in self.cache:
            del self.cache[key]
            self.access_times.pop(key, None)
            self.access_counts.pop(key, None)
            return True
        return False
    
    def _evict_one(self) -> None:
        """驱逐一个缓存项（LRU策略）"""
        if not self.cache:
            return
        
        # 找到最久未访问的项
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        self._remove(oldest_key)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_rate': self._calculate_hit_rate(),
            'memory_usage': self._estimate_memory_usage()
        }
    
    def _calculate_hit_rate(self) -> float:
        """计算命中率"""
        total_accesses = sum(self.access_counts.values())
        if total_accesses == 0:
            return 0.0
        return len(self.cache) / total_accesses
    
    def _estimate_memory_usage(self) -> int:
        """估算内存使用量"""
        try:
            return sum(len(pickle.dumps(item['data'])) for item in self.cache.values())
        except:
            return 0

class RedisCache:
    """Redis缓存"""
    
    def __init__(self, redis_client: aioredis.Redis, prefix: str = "lawsker:"):
        self.redis = redis_client
        self.prefix = prefix
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
    
    def _make_key(self, key: str) -> str:
        """生成Redis键"""
        return f"{self.prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        try:
            redis_key = self._make_key(key)
            data = await self.redis.get(redis_key)
            
            if data is None:
                self.stats['misses'] += 1
                return None
            
            self.stats['hits'] += 1
            return json.loads(data)
            
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self.stats['misses'] += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """设置缓存数据"""
        try:
            redis_key = self._make_key(key)
            data = json.dumps(value, default=str)
            
            await self.redis.setex(redis_key, ttl, data)
            self.stats['sets'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存数据"""
        try:
            redis_key = self._make_key(key)
            result = await self.redis.delete(redis_key)
            self.stats['deletes'] += 1
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            redis_key = self._make_key(key)
            return await self.redis.exists(redis_key) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """设置过期时间"""
        try:
            redis_key = self._make_key(key)
            return await self.redis.expire(redis_key, ttl)
        except Exception as e:
            logger.error(f"Redis expire error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的键"""
        try:
            redis_pattern = self._make_key(pattern)
            keys = await self.redis.keys(redis_pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis clear pattern error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'sets': self.stats['sets'],
            'deletes': self.stats['deletes'],
            'hit_rate': hit_rate
        }

class MultiLevelCache:
    """多级缓存"""
    
    def __init__(self, memory_cache: MemoryCache, redis_cache: RedisCache):
        self.memory_cache = memory_cache
        self.redis_cache = redis_cache
        self.stats = {
            'l1_hits': 0,  # 内存缓存命中
            'l2_hits': 0,  # Redis缓存命中
            'misses': 0,   # 完全未命中
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """多级获取缓存数据"""
        # L1: 内存缓存
        data = self.memory_cache.get(key)
        if data is not None:
            self.stats['l1_hits'] += 1
            return data
        
        # L2: Redis缓存
        data = await self.redis_cache.get(key)
        if data is not None:
            self.stats['l2_hits'] += 1
            # 回填到内存缓存
            self.memory_cache.set(key, data)
            return data
        
        self.stats['misses'] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """多级设置缓存数据"""
        # 同时设置两级缓存
        self.memory_cache.set(key, value)
        await self.redis_cache.set(key, value, ttl)
    
    async def delete(self, key: str) -> None:
        """多级删除缓存数据"""
        self.memory_cache.delete(key)
        await self.redis_cache.delete(key)
    
    async def clear_pattern(self, pattern: str) -> None:
        """清除匹配模式的缓存"""
        # 清除内存缓存中匹配的键
        keys_to_remove = [k for k in self.memory_cache.cache.keys() if pattern in k]
        for key in keys_to_remove:
            self.memory_cache.delete(key)
        
        # 清除Redis缓存
        await self.redis_cache.clear_pattern(pattern)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取多级缓存统计"""
        total_requests = self.stats['l1_hits'] + self.stats['l2_hits'] + self.stats['misses']
        
        return {
            'l1_hits': self.stats['l1_hits'],
            'l2_hits': self.stats['l2_hits'],
            'misses': self.stats['misses'],
            'total_requests': total_requests,
            'l1_hit_rate': (self.stats['l1_hits'] / total_requests * 100) if total_requests > 0 else 0,
            'l2_hit_rate': (self.stats['l2_hits'] / total_requests * 100) if total_requests > 0 else 0,
            'overall_hit_rate': ((self.stats['l1_hits'] + self.stats['l2_hits']) / total_requests * 100) if total_requests > 0 else 0,
            'memory_stats': self.memory_cache.get_stats(),
            'redis_stats': self.redis_cache.get_stats()
        }

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.memory_cache = MemoryCache(max_size=1000, ttl=300)
        self.redis_cache = RedisCache(redis_client)
        self.multi_cache = MultiLevelCache(self.memory_cache, self.redis_cache)
        self.cache_warming_tasks = {}
        self.cache_patterns = {
            'user': 'user:{}',
            'lawyer_level': 'lawyer_level:{}',
            'membership': 'membership:{}',
            'credits': 'credits:{}',
            'points': 'points:{}',
            'config': 'config:{}',
        }
    
    def cache_key(self, pattern: str, *args) -> str:
        """生成缓存键"""
        if pattern in self.cache_patterns:
            return self.cache_patterns[pattern].format(*args)
        return f"{pattern}:{':'.join(map(str, args))}"
    
    async def get_or_set(self, key: str, fetch_func: Callable, ttl: int = 300) -> Any:
        """获取或设置缓存"""
        # 尝试从缓存获取
        data = await self.multi_cache.get(key)
        if data is not None:
            return data
        
        # 缓存未命中，从数据源获取
        try:
            data = await fetch_func()
            if data is not None:
                await self.multi_cache.set(key, data, ttl)
            return data
        except Exception as e:
            logger.error(f"Cache fetch function error: {e}")
            return None
    
    async def invalidate_pattern(self, pattern: str) -> None:
        """失效匹配模式的缓存"""
        await self.multi_cache.clear_pattern(pattern)
        logger.info(f"Invalidated cache pattern: {pattern}")
    
    async def warm_up_cache(self, warm_up_functions: Dict[str, Callable]) -> None:
        """缓存预热"""
        logger.info("Starting cache warm-up...")
        
        for cache_key, fetch_func in warm_up_functions.items():
            try:
                data = await fetch_func()
                await self.multi_cache.set(cache_key, data, ttl=600)  # 预热数据缓存10分钟
                logger.info(f"Warmed up cache: {cache_key}")
            except Exception as e:
                logger.error(f"Cache warm-up error for {cache_key}: {e}")
        
        logger.info("Cache warm-up completed")
    
    async def start_cache_maintenance(self) -> None:
        """启动缓存维护任务"""
        asyncio.create_task(self._cache_maintenance_loop())
    
    async def _cache_maintenance_loop(self) -> None:
        """缓存维护循环"""
        while True:
            try:
                # 清理过期的内存缓存
                await self._cleanup_expired_memory_cache()
                
                # 统计缓存使用情况
                stats = self.multi_cache.get_stats()
                logger.info(f"Cache stats: {stats}")
                
                # 每5分钟执行一次维护
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Cache maintenance error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_expired_memory_cache(self) -> None:
        """清理过期的内存缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, item in self.memory_cache.cache.items():
            if current_time - item['timestamp'] > self.memory_cache.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            self.memory_cache.delete(key)
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

def cached(ttl: int = 300, key_pattern: str = None):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_pattern:
                cache_key = key_pattern.format(*args, **kwargs)
            else:
                # 基于函数名和参数生成键
                func_name = func.__name__
                args_str = ':'.join(map(str, args))
                kwargs_str = ':'.join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{func_name}:{args_str}:{kwargs_str}"
            
            # 尝试从缓存获取
            if hasattr(wrapper, '_cache_manager'):
                data = await wrapper._cache_manager.multi_cache.get(cache_key)
                if data is not None:
                    return data
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            if hasattr(wrapper, '_cache_manager') and result is not None:
                await wrapper._cache_manager.multi_cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

# 全局缓存管理器实例
cache_manager: Optional[CacheManager] = None

async def initialize_cache_system(redis_client: aioredis.Redis) -> CacheManager:
    """初始化缓存系统"""
    global cache_manager
    
    cache_manager = CacheManager(redis_client)
    await cache_manager.start_cache_maintenance()
    
    # 设置装饰器的缓存管理器
    for func in [cached]:
        if hasattr(func, '_cache_manager'):
            func._cache_manager = cache_manager
    
    logger.info("Cache system initialized successfully")
    return cache_manager

async def get_cache_manager() -> CacheManager:
    """获取缓存管理器"""
    if cache_manager is None:
        raise RuntimeError("Cache system not initialized")
    return cache_manager