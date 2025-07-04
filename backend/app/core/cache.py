"""
缓存模块
用于存储临时数据，如验证码
"""

from typing import Dict, Any, Optional
from datetime import datetime

# 内存缓存字典，用于开发环境或Redis不可用时
memory_cache: Dict[str, Any] = {}


def clear_expired_cache():
    """清理过期的缓存数据"""
    current_time = datetime.now()
    expired_keys = [
        key for key, value in memory_cache.items()
        if isinstance(value, dict) and 'expires' in value and value['expires'] < current_time
    ]
    
    for key in expired_keys:
        memory_cache.pop(key, None)


def get_cache(key: str) -> Any:
    """获取缓存数据"""
    # 清理过期数据
    clear_expired_cache()
    return memory_cache.get(key)


def set_cache(key: str, value: Any, expires: Optional[datetime] = None) -> None:
    """设置缓存数据"""
    if expires:
        memory_cache[key] = {
            'data': value,
            'expires': expires
        }
    else:
        memory_cache[key] = value


def delete_cache(key: str) -> None:
    """删除缓存数据"""
    memory_cache.pop(key, None) 