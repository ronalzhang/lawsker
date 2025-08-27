"""
性能配置文件
定义系统性能相关的配置参数
"""

from typing import Dict, Any
import os

class PerformanceConfig:
    """性能配置类"""
    
    # 响应时间要求（秒）
    RESPONSE_TIME_REQUIREMENTS = {
        'auth_system': 1.0,  # 统一认证系统响应时间 < 1秒
        'points_calculation': 0.5,  # 律师积分计算和更新延迟 < 500ms
        'credits_payment': 2.0,  # 用户Credits支付处理时间 < 2秒
        'page_load': 2.0,  # 前端页面加载时间 < 2秒
        'api_default': 3.0,  # 默认API响应时间 < 3秒
    }
    
    # 并发能力要求
    CONCURRENCY_REQUIREMENTS = {
        'max_concurrent_users': 1000,  # 支持1000+并发用户访问
        'credits_processing_rate': 10000,  # Credits支付系统处理能力 > 10000次/小时
        'database_connections': 100,  # 最大数据库连接数
        'redis_connections': 50,  # 最大Redis连接数
    }
    
    # 系统可用性要求
    AVAILABILITY_REQUIREMENTS = {
        'system_availability': 99.9,  # 系统可用性 > 99.9%
        'max_downtime_minutes': 43.2,  # 每月最大停机时间（分钟）
        'error_rate_threshold': 1.0,  # 错误率阈值 < 1%
    }
    
    # 缓存配置
    CACHE_CONFIG = {
        'memory_cache_size': 1000,  # 内存缓存大小
        'memory_cache_ttl': 300,  # 内存缓存TTL（秒）
        'redis_cache_ttl': 600,  # Redis缓存TTL（秒）
        'cache_warm_up_interval': 3600,  # 缓存预热间隔（秒）
        'cache_patterns': {
            'user_data': 'user:{}',
            'lawyer_levels': 'lawyer_level:{}',
            'membership_tiers': 'membership:{}',
            'credits_balance': 'credits:{}',
            'points_records': 'points:{}',
            'system_config': 'config:{}',
        }
    }
    
    # 数据库性能配置
    DATABASE_CONFIG = {
        'connection_pool_size': 20,  # 连接池大小
        'max_overflow': 30,  # 最大溢出连接数
        'pool_timeout': 30,  # 连接超时时间（秒）
        'pool_recycle': 3600,  # 连接回收时间（秒）
        'slow_query_threshold': 1.0,  # 慢查询阈值（秒）
        'query_cache_size': 500,  # 查询缓存大小
        'query_cache_ttl': 300,  # 查询缓存TTL（秒）
    }
    
    # 监控配置
    MONITORING_CONFIG = {
        'metrics_collection_interval': 30,  # 指标收集间隔（秒）
        'performance_analysis_interval': 300,  # 性能分析间隔（秒）
        'alert_thresholds': {
            'cpu_usage': 80.0,  # CPU使用率告警阈值（%）
            'memory_usage': 85.0,  # 内存使用率告警阈值（%）
            'disk_usage': 90.0,  # 磁盘使用率告警阈值（%）
            'response_time_multiplier': 1.5,  # 响应时间告警倍数
            'error_rate': 5.0,  # 错误率告警阈值（%）
        },
        'prometheus_port': 8001,  # Prometheus指标端口
    }
    
    # 优化策略配置
    OPTIMIZATION_CONFIG = {
        'batch_processing_size': 100,  # 批处理大小
        'batch_processing_delay': 0.01,  # 批处理间延迟（秒）
        'connection_pool_optimization': True,  # 启用连接池优化
        'query_optimization': True,  # 启用查询优化
        'cache_optimization': True,  # 启用缓存优化
        'compression_enabled': True,  # 启用响应压缩
        'compression_min_size': 1024,  # 压缩最小大小（字节）
    }
    
    # 负载测试配置
    LOAD_TEST_CONFIG = {
        'test_duration': 300,  # 测试持续时间（秒）
        'ramp_up_time': 60,  # 负载递增时间（秒）
        'concurrent_users_levels': [100, 500, 1000, 1500],  # 并发用户测试级别
        'test_endpoints': [
            '/api/v1/auth/login',
            '/api/v1/points/calculate',
            '/api/v1/credits/purchase',
            '/api/v1/health',
            '/api/v1/config/system',
        ],
        'success_rate_threshold': 95.0,  # 成功率阈值（%）
    }
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """获取完整配置"""
        return {
            'response_time_requirements': cls.RESPONSE_TIME_REQUIREMENTS,
            'concurrency_requirements': cls.CONCURRENCY_REQUIREMENTS,
            'availability_requirements': cls.AVAILABILITY_REQUIREMENTS,
            'cache_config': cls.CACHE_CONFIG,
            'database_config': cls.DATABASE_CONFIG,
            'monitoring_config': cls.MONITORING_CONFIG,
            'optimization_config': cls.OPTIMIZATION_CONFIG,
            'load_test_config': cls.LOAD_TEST_CONFIG,
        }
    
    @classmethod
    def get_response_time_threshold(cls, endpoint_type: str) -> float:
        """获取响应时间阈值"""
        return cls.RESPONSE_TIME_REQUIREMENTS.get(endpoint_type, cls.RESPONSE_TIME_REQUIREMENTS['api_default'])
    
    @classmethod
    def get_cache_ttl(cls, cache_type: str) -> int:
        """获取缓存TTL"""
        if cache_type == 'memory':
            return cls.CACHE_CONFIG['memory_cache_ttl']
        elif cache_type == 'redis':
            return cls.CACHE_CONFIG['redis_cache_ttl']
        else:
            return cls.CACHE_CONFIG['redis_cache_ttl']
    
    @classmethod
    def get_alert_threshold(cls, metric_name: str) -> float:
        """获取告警阈值"""
        return cls.MONITORING_CONFIG['alert_thresholds'].get(metric_name, 0.0)
    
    @classmethod
    def is_optimization_enabled(cls, optimization_type: str) -> bool:
        """检查优化是否启用"""
        return cls.OPTIMIZATION_CONFIG.get(optimization_type, False)

# 环境变量覆盖配置
def load_performance_config_from_env():
    """从环境变量加载性能配置"""
    config_overrides = {}
    
    # 响应时间配置
    if os.getenv('AUTH_RESPONSE_TIME_LIMIT'):
        config_overrides['auth_response_time'] = float(os.getenv('AUTH_RESPONSE_TIME_LIMIT'))
    
    if os.getenv('POINTS_CALCULATION_TIME_LIMIT'):
        config_overrides['points_calculation_time'] = float(os.getenv('POINTS_CALCULATION_TIME_LIMIT'))
    
    if os.getenv('CREDITS_PAYMENT_TIME_LIMIT'):
        config_overrides['credits_payment_time'] = float(os.getenv('CREDITS_PAYMENT_TIME_LIMIT'))
    
    # 并发配置
    if os.getenv('MAX_CONCURRENT_USERS'):
        config_overrides['max_concurrent_users'] = int(os.getenv('MAX_CONCURRENT_USERS'))
    
    if os.getenv('DATABASE_POOL_SIZE'):
        config_overrides['database_pool_size'] = int(os.getenv('DATABASE_POOL_SIZE'))
    
    # 缓存配置
    if os.getenv('CACHE_TTL'):
        config_overrides['cache_ttl'] = int(os.getenv('CACHE_TTL'))
    
    if os.getenv('MEMORY_CACHE_SIZE'):
        config_overrides['memory_cache_size'] = int(os.getenv('MEMORY_CACHE_SIZE'))
    
    # 监控配置
    if os.getenv('PROMETHEUS_PORT'):
        config_overrides['prometheus_port'] = int(os.getenv('PROMETHEUS_PORT'))
    
    if os.getenv('CPU_ALERT_THRESHOLD'):
        config_overrides['cpu_alert_threshold'] = float(os.getenv('CPU_ALERT_THRESHOLD'))
    
    if os.getenv('MEMORY_ALERT_THRESHOLD'):
        config_overrides['memory_alert_threshold'] = float(os.getenv('MEMORY_ALERT_THRESHOLD'))
    
    return config_overrides

# 性能配置实例
performance_config = PerformanceConfig()

# 加载环境变量覆盖
env_overrides = load_performance_config_from_env()

# 应用环境变量覆盖
if env_overrides:
    for key, value in env_overrides.items():
        if hasattr(performance_config, key.upper()):
            setattr(performance_config, key.upper(), value)