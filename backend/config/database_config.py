"""
数据库配置管理
包含读写分离、连接池、性能参数等配置
"""
import os
from typing import Dict, Any, Optional
from pydantic import BaseSettings, validator
from sqlalchemy import create_engine, Engine
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.engine.events import event

class DatabaseSettings(BaseSettings):
    """数据库设置"""
    
    # 主数据库配置
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "lawsker"
    DATABASE_USER: str = "lawsker_user"
    DATABASE_PASSWORD: str
    
    # 读库配置（可选）
    READ_DB_HOST: Optional[str] = None
    READ_DB_PORT: Optional[int] = None
    READ_DB_USER: Optional[str] = None
    READ_DB_PASSWORD: Optional[str] = None
    
    # 连接池配置
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_PRE_PING: bool = True
    
    # 性能配置
    DB_ECHO: bool = False
    DB_ECHO_POOL: bool = False
    DB_CONNECT_TIMEOUT: int = 10
    DB_COMMAND_TIMEOUT: int = 30
    
    # SSL配置
    DB_SSL_MODE: str = "prefer"  # disable, allow, prefer, require, verify-ca, verify-full
    DB_SSL_CERT: Optional[str] = None
    DB_SSL_KEY: Optional[str] = None
    DB_SSL_ROOT_CERT: Optional[str] = None
    
    # 监控配置
    DB_ENABLE_MONITORING: bool = True
    DB_SLOW_QUERY_THRESHOLD: float = 1.0  # 秒
    DB_LOG_STATEMENTS: bool = False
    
    # 读写分离配置
    ENABLE_READ_WRITE_SPLITTING: bool = False
    READ_WRITE_RATIO: float = 0.7  # 读请求比例
    
    @validator('DATABASE_PASSWORD')
    def validate_password(cls, v):
        if not v:
            raise ValueError('Database password is required')
        return v
    
    @validator('DB_POOL_SIZE')
    def validate_pool_size(cls, v):
        if v < 1:
            raise ValueError('Pool size must be at least 1')
        return v
    
    @validator('DB_MAX_OVERFLOW')
    def validate_max_overflow(cls, v):
        if v < 0:
            raise ValueError('Max overflow must be non-negative')
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 数据库设置实例
db_settings = DatabaseSettings()

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.write_engine: Optional[Engine] = None
        self.read_engine: Optional[Engine] = None
        self._engines_initialized = False
    
    def initialize_engines(self):
        """初始化数据库引擎"""
        if self._engines_initialized:
            return
        
        # 创建写库引擎
        self.write_engine = self._create_engine(
            host=db_settings.DATABASE_HOST,
            port=db_settings.DATABASE_PORT,
            user=db_settings.DATABASE_USER,
            password=db_settings.DATABASE_PASSWORD,
            database=db_settings.DATABASE_NAME,
            engine_type="write"
        )
        
        # 创建读库引擎（如果配置了读写分离）
        if db_settings.ENABLE_READ_WRITE_SPLITTING and db_settings.READ_DB_HOST:
            self.read_engine = self._create_engine(
                host=db_settings.READ_DB_HOST,
                port=db_settings.READ_DB_PORT or db_settings.DATABASE_PORT,
                user=db_settings.READ_DB_USER or db_settings.DATABASE_USER,
                password=db_settings.READ_DB_PASSWORD or db_settings.DATABASE_PASSWORD,
                database=db_settings.DATABASE_NAME,
                engine_type="read"
            )
        else:
            # 如果没有配置读库，读写都使用同一个引擎
            self.read_engine = self.write_engine
        
        # 设置引擎事件监听
        self._setup_engine_events()
        
        self._engines_initialized = True
    
    def _create_engine(
        self, host: str, port: int, user: str, password: str, 
        database: str, engine_type: str
    ) -> Engine:
        """创建数据库引擎"""
        
        # 构建连接URL
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        # SSL参数
        connect_args = {
            "application_name": f"lawsker_{engine_type}",
            "connect_timeout": db_settings.DB_CONNECT_TIMEOUT,
            "command_timeout": db_settings.DB_COMMAND_TIMEOUT,
        }
        
        if db_settings.DB_SSL_MODE != "disable":
            connect_args["sslmode"] = db_settings.DB_SSL_MODE
            
            if db_settings.DB_SSL_CERT:
                connect_args["sslcert"] = db_settings.DB_SSL_CERT
            if db_settings.DB_SSL_KEY:
                connect_args["sslkey"] = db_settings.DB_SSL_KEY
            if db_settings.DB_SSL_ROOT_CERT:
                connect_args["sslrootcert"] = db_settings.DB_SSL_ROOT_CERT
        
        # 连接池配置
        pool_config = {
            "poolclass": QueuePool,
            "pool_size": db_settings.DB_POOL_SIZE,
            "max_overflow": db_settings.DB_MAX_OVERFLOW,
            "pool_timeout": db_settings.DB_POOL_TIMEOUT,
            "pool_recycle": db_settings.DB_POOL_RECYCLE,
            "pool_pre_ping": db_settings.DB_POOL_PRE_PING,
        }
        
        # 读库使用较小的连接池
        if engine_type == "read":
            pool_config["pool_size"] = max(5, db_settings.DB_POOL_SIZE // 2)
            pool_config["max_overflow"] = max(10, db_settings.DB_MAX_OVERFLOW // 2)
        
        return create_engine(
            database_url,
            echo=db_settings.DB_ECHO,
            echo_pool=db_settings.DB_ECHO_POOL,
            connect_args=connect_args,
            **pool_config
        )
    
    def _setup_engine_events(self):
        """设置引擎事件监听"""
        if db_settings.DB_ENABLE_MONITORING:
            # 监听连接事件
            @event.listens_for(self.write_engine, "connect")
            def receive_connect(dbapi_connection, connection_record):
                """连接建立事件"""
                connection_record.info['connect_time'] = time.time()
            
            @event.listens_for(self.write_engine, "checkout")
            def receive_checkout(dbapi_connection, connection_record, connection_proxy):
                """连接检出事件"""
                connection_record.info['checkout_time'] = time.time()
            
            @event.listens_for(self.write_engine, "checkin")
            def receive_checkin(dbapi_connection, connection_record):
                """连接检入事件"""
                checkout_time = connection_record.info.get('checkout_time')
                if checkout_time:
                    usage_time = time.time() - checkout_time
                    # 记录连接使用时间（可以发送到监控系统）
                    pass
            
            # 如果有读库，也设置相同的监听
            if self.read_engine != self.write_engine:
                @event.listens_for(self.read_engine, "connect")
                def receive_read_connect(dbapi_connection, connection_record):
                    connection_record.info['connect_time'] = time.time()
                
                @event.listens_for(self.read_engine, "checkout")
                def receive_read_checkout(dbapi_connection, connection_record, connection_proxy):
                    connection_record.info['checkout_time'] = time.time()
                
                @event.listens_for(self.read_engine, "checkin")
                def receive_read_checkin(dbapi_connection, connection_record):
                    checkout_time = connection_record.info.get('checkout_time')
                    if checkout_time:
                        usage_time = time.time() - checkout_time
                        # 记录读库连接使用时间
                        pass
    
    def get_write_engine(self) -> Engine:
        """获取写库引擎"""
        if not self._engines_initialized:
            self.initialize_engines()
        return self.write_engine
    
    def get_read_engine(self) -> Engine:
        """获取读库引擎"""
        if not self._engines_initialized:
            self.initialize_engines()
        return self.read_engine
    
    def get_engine_for_operation(self, operation_type: str = "read") -> Engine:
        """根据操作类型获取引擎"""
        if operation_type.lower() in ["select", "read", "query"]:
            return self.get_read_engine()
        else:
            return self.get_write_engine()
    
    def close_engines(self):
        """关闭所有引擎"""
        if self.write_engine:
            self.write_engine.dispose()
        
        if self.read_engine and self.read_engine != self.write_engine:
            self.read_engine.dispose()
        
        self._engines_initialized = False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        info = {
            "write_engine": {
                "url": str(self.write_engine.url).replace(f":{db_settings.DATABASE_PASSWORD}@", ":***@"),
                "pool_size": self.write_engine.pool.size(),
                "checked_in": self.write_engine.pool.checkedin(),
                "checked_out": self.write_engine.pool.checkedout(),
                "overflow": self.write_engine.pool.overflow(),
                "invalid": self.write_engine.pool.invalid()
            }
        }
        
        if self.read_engine != self.write_engine:
            info["read_engine"] = {
                "url": str(self.read_engine.url).replace(f":{db_settings.DATABASE_PASSWORD}@", ":***@"),
                "pool_size": self.read_engine.pool.size(),
                "checked_in": self.read_engine.pool.checkedin(),
                "checked_out": self.read_engine.pool.checkedout(),
                "overflow": self.read_engine.pool.overflow(),
                "invalid": self.read_engine.pool.invalid()
            }
        
        return info

# 全局数据库管理器实例
db_manager = DatabaseManager()

# PostgreSQL优化配置模板
POSTGRESQL_OPTIMIZATION_CONFIG = {
    # 内存配置
    "memory": {
        "shared_buffers": "256MB",  # 根据系统内存调整
        "effective_cache_size": "1GB",  # 根据系统内存调整
        "work_mem": "4MB",
        "maintenance_work_mem": "64MB",
        "temp_buffers": "8MB",
    },
    
    # 连接配置
    "connections": {
        "max_connections": "100",
        "superuser_reserved_connections": "3",
    },
    
    # 检查点配置
    "checkpoint": {
        "checkpoint_completion_target": "0.9",
        "checkpoint_timeout": "5min",
        "max_wal_size": "1GB",
        "min_wal_size": "80MB",
    },
    
    # 查询规划器配置
    "planner": {
        "random_page_cost": "1.1",  # SSD优化
        "effective_io_concurrency": "200",  # SSD优化
        "seq_page_cost": "1.0",
        "cpu_tuple_cost": "0.01",
        "cpu_index_tuple_cost": "0.005",
        "cpu_operator_cost": "0.0025",
    },
    
    # 并行查询配置
    "parallel": {
        "max_worker_processes": "8",
        "max_parallel_workers": "8",
        "max_parallel_workers_per_gather": "2",
        "max_parallel_maintenance_workers": "2",
        "parallel_tuple_cost": "0.1",
        "parallel_setup_cost": "1000.0",
    },
    
    # 日志配置
    "logging": {
        "log_destination": "stderr",
        "logging_collector": "on",
        "log_directory": "log",
        "log_filename": "postgresql-%Y-%m-%d_%H%M%S.log",
        "log_rotation_age": "1d",
        "log_rotation_size": "10MB",
        "log_min_duration_statement": "1000",  # 记录慢查询
        "log_checkpoints": "on",
        "log_connections": "on",
        "log_disconnections": "on",
        "log_lock_waits": "on",
        "log_temp_files": "0",
        "log_autovacuum_min_duration": "0",
    },
    
    # 统计配置
    "statistics": {
        "track_activities": "on",
        "track_counts": "on",
        "track_io_timing": "on",
        "track_functions": "all",
        "track_activity_query_size": "1024",
        "update_process_title": "on",
    },
    
    # 自动清理配置
    "autovacuum": {
        "autovacuum": "on",
        "autovacuum_max_workers": "3",
        "autovacuum_naptime": "1min",
        "autovacuum_vacuum_threshold": "50",
        "autovacuum_analyze_threshold": "50",
        "autovacuum_vacuum_scale_factor": "0.2",
        "autovacuum_analyze_scale_factor": "0.1",
        "autovacuum_freeze_max_age": "200000000",
        "autovacuum_multixact_freeze_max_age": "400000000",
        "autovacuum_vacuum_cost_delay": "20ms",
        "autovacuum_vacuum_cost_limit": "200",
    },
    
    # 扩展配置
    "extensions": {
        "shared_preload_libraries": "pg_stat_statements",
        "pg_stat_statements.max": "10000",
        "pg_stat_statements.track": "all",
        "pg_stat_statements.track_utility": "off",
        "pg_stat_statements.save": "on",
    }
}

def generate_postgresql_config(system_memory_gb: float, cpu_cores: int) -> str:
    """根据系统资源生成PostgreSQL配置"""
    
    # 根据系统资源调整配置
    config = POSTGRESQL_OPTIMIZATION_CONFIG.copy()
    
    # 内存配置调整
    shared_buffers_mb = int(system_memory_gb * 1024 * 0.25)  # 25% of RAM
    effective_cache_size_mb = int(system_memory_gb * 1024 * 0.75)  # 75% of RAM
    work_mem_mb = max(4, int(system_memory_gb * 1024 / 200))  # RAM/200
    maintenance_work_mem_mb = min(2048, int(system_memory_gb * 1024 / 16))  # RAM/16, max 2GB
    
    config["memory"]["shared_buffers"] = f"{shared_buffers_mb}MB"
    config["memory"]["effective_cache_size"] = f"{effective_cache_size_mb}MB"
    config["memory"]["work_mem"] = f"{work_mem_mb}MB"
    config["memory"]["maintenance_work_mem"] = f"{maintenance_work_mem_mb}MB"
    
    # 连接数调整
    max_connections = min(200, max(100, cpu_cores * 4))
    config["connections"]["max_connections"] = str(max_connections)
    
    # 并行配置调整
    config["parallel"]["max_worker_processes"] = str(cpu_cores)
    config["parallel"]["max_parallel_workers"] = str(cpu_cores)
    config["parallel"]["max_parallel_workers_per_gather"] = str(min(4, cpu_cores // 2))
    
    # 自动清理配置调整
    autovacuum_workers = min(3, max(1, cpu_cores // 4))
    config["autovacuum"]["autovacuum_max_workers"] = str(autovacuum_workers)
    
    # 生成配置文件内容
    config_lines = [
        "# PostgreSQL Configuration - Optimized for Lawsker",
        f"# Generated for system with {system_memory_gb:.1f}GB RAM and {cpu_cores} CPU cores",
        f"# Generated at: {datetime.now().isoformat()}",
        ""
    ]
    
    for section_name, section_config in config.items():
        config_lines.append(f"# {section_name.title()} Configuration")
        for param, value in section_config.items():
            config_lines.append(f"{param} = {value}")
        config_lines.append("")
    
    return "\n".join(config_lines)

def get_database_config() -> Dict[str, Any]:
    """获取数据库配置"""
    return {
        "settings": db_settings.dict(),
        "optimization_config": POSTGRESQL_OPTIMIZATION_CONFIG,
        "connection_info": db_manager.get_connection_info() if db_manager._engines_initialized else None
    }

# 导入时间模块
import time
from datetime import datetime