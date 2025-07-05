"""
缓存服务
支持Redis和内存缓存
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
import threading

logger = logging.getLogger(__name__)

# Redis client (可选)
redis_client: Optional[Any] = None

try:
    import redis
    # TODO: 从配置中读取Redis连接信息
    # redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
except ImportError:
    logger.info("Redis not available, using memory cache")


class MemoryCache:
    """内存缓存类"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """设置缓存"""
        try:
            with self._lock:
                expires_at = None
                if expire_seconds:
                    expires_at = datetime.now() + timedelta(seconds=expire_seconds)
                
                self._cache[key] = {
                    "value": value,
                    "expires_at": expires_at,
                    "created_at": datetime.now()
                }
                return True
        except Exception as e:
            logger.error(f"Memory cache set error: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            with self._lock:
                if key not in self._cache:
                    return None
                
                cache_item = self._cache[key]
                
                # 检查是否过期
                if cache_item["expires_at"] and cache_item["expires_at"] < datetime.now():
                    del self._cache[key]
                    return None
                
                return cache_item["value"]
        except Exception as e:
            logger.error(f"Memory cache get error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            with self._lock:
                if key in self._cache:
                    del self._cache[key]
                    return True
                return False
        except Exception as e:
            logger.error(f"Memory cache delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            with self._lock:
                if key not in self._cache:
                    return False
                
                cache_item = self._cache[key]
                
                # 检查是否过期
                if cache_item["expires_at"] and cache_item["expires_at"] < datetime.now():
                    del self._cache[key]
                    return False
                
                return True
        except Exception as e:
            logger.error(f"Memory cache exists error: {e}")
            return False
    
    def clear(self) -> bool:
        """清空缓存"""
        try:
            with self._lock:
                self._cache.clear()
                return True
        except Exception as e:
            logger.error(f"Memory cache clear error: {e}")
            return False
    
    def size(self) -> int:
        """获取缓存大小"""
        try:
            with self._lock:
                # 清理过期项
                current_time = datetime.now()
                expired_keys = []
                
                for key, cache_item in self._cache.items():
                    if cache_item["expires_at"] and cache_item["expires_at"] < current_time:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self._cache[key]
                
                return len(self._cache)
        except Exception as e:
            logger.error(f"Memory cache size error: {e}")
            return 0


# 全局内存缓存实例
memory_cache = MemoryCache()


class CacheService:
    """统一缓存服务"""
    
    def __init__(self, use_redis: bool = True):
        self.use_redis = use_redis and redis_client is not None
        self.memory_cache = memory_cache
    
    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            if self.use_redis and redis_client is not None:
                # 使用Redis
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value, ensure_ascii=False)
                else:
                    value_str = str(value)
                
                if expire_seconds:
                    result = redis_client.setex(key, expire_seconds, value_str)
                    return bool(result)
                else:
                    result = redis_client.set(key, value_str)
                    return bool(result)
            else:
                # 使用内存缓存
                return self.memory_cache.set(key, value, expire_seconds)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            # 回退到内存缓存
            return self.memory_cache.set(key, value, expire_seconds)
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            if self.use_redis and redis_client is not None:
                # 使用Redis
                value = redis_client.get(key)
                if value is None:
                    return None
                
                # 尝试解析JSON
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            else:
                # 使用内存缓存
                return self.memory_cache.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            # 回退到内存缓存
            return self.memory_cache.get(key)
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            if self.use_redis and redis_client is not None:
                result = redis_client.delete(key)
                return bool(result)
            else:
                return self.memory_cache.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            # 回退到内存缓存
            return self.memory_cache.delete(key)
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            if self.use_redis and redis_client is not None:
                result = redis_client.exists(key)
                return bool(result)
            else:
                return self.memory_cache.exists(key)
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            # 回退到内存缓存
            return self.memory_cache.exists(key)
    
    async def setex(self, key: str, expire_seconds: int, value: Any) -> bool:
        """设置带过期时间的缓存值"""
        return await self.set(key, value, expire_seconds)
    
    async def ttl(self, key: str) -> int:
        """获取键的剩余生存时间"""
        try:
            if self.use_redis and redis_client is not None:
                result = redis_client.ttl(key)
                return int(result)
            else:
                # 内存缓存不支持TTL查询，返回-1表示不支持
                return -1
        except Exception as e:
            logger.error(f"Cache ttl error: {e}")
            return -1


# 全局缓存服务实例
cache_service = CacheService()


def get_cache_service() -> CacheService:
    """获取缓存服务实例"""
    return cache_service 