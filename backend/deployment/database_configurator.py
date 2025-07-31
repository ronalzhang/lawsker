"""
数据库配置系统
提供PostgreSQL自动配置、用户管理、权限配置和连接池优化功能
"""

import os
import sys
import subprocess
import logging
import time
import psutil
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import tempfile
import shutil
from datetime import datetime

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import structlog

logger = structlog.get_logger()

@dataclass
class DatabaseConfig:
    """数据库配置数据类"""
    host: str = "localhost"
    port: int = 5432
    name: str = "lawsker_prod"
    user: str = "lawsker_user"
    password: str = ""
    admin_user: str = "postgres"
    admin_password: str = ""
    ssl_mode: str = "prefer"
    
    # 连接池配置
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    # 性能配置
    shared_buffers_mb: int = 256
    effective_cache_size_mb: int = 1024
    work_mem_mb: int = 4
    maintenance_work_mem_mb: int = 64
    max_connections: int = 100
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

@dataclass
class DatabaseStatus:
    """数据库状态数据类"""
    service_running: bool = False
    database_exists: bool = False
    user_exists: bool = False
    connection_successful: bool = False
    migrations_applied: bool = False
    performance_optimized: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

class DatabaseConfigurator:
    """数据库配置器"""
    
    def __init__(self, config: DatabaseConfig, project_root: str = "."):
        self.config = config
        self.project_root = Path(project_root).resolve()
        self.logger = structlog.get_logger(__name__)
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 状态跟踪
        self.status = DatabaseStatus()
        
        # 备份目录
        self.backup_dir = self.project_root / "backend" / "deployment" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置文件路径
        self.postgresql_conf_path = None
        self.pg_hba_conf_path = None
        
    def check_postgresql_service(self) -> bool:
        """检查PostgreSQL服务状态"""
        try:
            self.logger.info("检查PostgreSQL服务状态...")
            
            # 方法1: 尝试连接到默认数据库
            try:
                conn = psycopg2.connect(
                    host=self.config.host,
                    port=self.config.port,
                    user=self.config.admin_user,
                    password=self.config.admin_password,
                    database="postgres",
                    connect_timeout=5
                )
                conn.close()
                self.status.service_running = True
                self.logger.info("✅ PostgreSQL服务正在运行")
                return True
                
            except psycopg2.OperationalError as e:
                self.logger.warning(f"无法连接到PostgreSQL: {e}")
                
            # 方法2: 检查进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'postgres' in proc.info['name'].lower():
                        self.status.service_running = True
                        self.logger.info("✅ 发现PostgreSQL进程")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            # 方法3: 检查端口
            connections = psutil.net_connections()
            for conn in connections:
                if conn.laddr.port == self.config.port and conn.status == 'LISTEN':
                    self.status.service_running = True
                    self.logger.info(f"✅ 端口 {self.config.port} 正在监听")
                    return True
                    
            self.logger.error("❌ PostgreSQL服务未运行")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 检查PostgreSQL服务时出错: {e}")
            return False
    
    def create_database_and_user(self) -> bool:
        """创建数据库和用户"""
        try:
            self.logger.info("创建数据库和用户...")
            
            # 连接到PostgreSQL管理数据库
            admin_conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.admin_user,
                password=self.config.admin_password,
                database="postgres"
            )
            admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            admin_cursor = admin_conn.cursor()
            
            try:
                # 检查用户是否存在
                admin_cursor.execute(
                    "SELECT 1 FROM pg_roles WHERE rolname = %s",
                    (self.config.user,)
                )
                user_exists = admin_cursor.fetchone() is not None
                
                if not user_exists:
                    # 创建用户
                    self.logger.info(f"创建用户: {self.config.user}")
                    admin_cursor.execute(
                        f"CREATE ROLE {self.config.user} WITH LOGIN PASSWORD %s",
                        (self.config.password,)
                    )
                    self.logger.info("✅ 用户创建成功")
                else:
                    self.logger.info(f"用户 {self.config.user} 已存在")
                    # 更新密码
                    admin_cursor.execute(
                        f"ALTER ROLE {self.config.user} WITH PASSWORD %s",
                        (self.config.password,)
                    )
                
                self.status.user_exists = True
                
                # 检查数据库是否存在
                admin_cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (self.config.name,)
                )
                db_exists = admin_cursor.fetchone() is not None
                
                if not db_exists:
                    # 创建数据库
                    self.logger.info(f"创建数据库: {self.config.name}")
                    admin_cursor.execute(
                        f"CREATE DATABASE {self.config.name} OWNER {self.config.user}"
                    )
                    self.logger.info("✅ 数据库创建成功")
                else:
                    self.logger.info(f"数据库 {self.config.name} 已存在")
                
                self.status.database_exists = True
                
                # 授予权限
                self._grant_database_permissions(admin_cursor)
                
                return True
                
            finally:
                admin_cursor.close()
                admin_conn.close()
                
        except Exception as e:
            self.logger.error(f"❌ 创建数据库和用户失败: {e}")
            return False
    
    def _grant_database_permissions(self, cursor):
        """授予数据库权限"""
        try:
            self.logger.info("配置数据库权限...")
            
            # 基本权限
            permissions = [
                f"GRANT ALL PRIVILEGES ON DATABASE {self.config.name} TO {self.config.user}",
                f"GRANT ALL ON SCHEMA public TO {self.config.user}",
                f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {self.config.user}",
                f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {self.config.user}",
                f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO {self.config.user}",
            ]
            
            for permission in permissions:
                try:
                    cursor.execute(permission)
                    self.logger.debug(f"执行权限: {permission}")
                except Exception as e:
                    self.logger.warning(f"权限设置警告: {permission} - {e}")
            
            self.logger.info("✅ 数据库权限配置完成")
            
        except Exception as e:
            self.logger.error(f"❌ 配置数据库权限失败: {e}")
            raise
    
    def verify_connection(self) -> bool:
        """验证数据库连接"""
        try:
            self.logger.info("验证数据库连接...")
            
            # 构建连接URL
            database_url = (
                f"postgresql://{self.config.user}:{self.config.password}@"
                f"{self.config.host}:{self.config.port}/{self.config.name}"
            )
            
            # 创建SQLAlchemy引擎进行测试
            engine = create_engine(
                database_url,
                pool_pre_ping=True,
                connect_args={
                    "connect_timeout": 10,
                    "sslmode": self.config.ssl_mode
                }
            )
            
            # 测试连接
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                self.logger.info(f"✅ 数据库连接成功: {version}")
                
                # 测试基本操作
                conn.execute(text("SELECT NOW()"))
                self.logger.info("✅ 基本查询测试通过")
                
            engine.dispose()
            self.status.connection_successful = True
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 数据库连接验证失败: {e}")
            return False
    
    def optimize_connection_pool(self) -> Dict[str, Any]:
        """优化连接池配置"""
        try:
            self.logger.info("优化连接池配置...")
            
            # 获取系统资源信息
            memory_gb = psutil.virtual_memory().total / (1024**3)
            cpu_cores = psutil.cpu_count()
            
            # 根据系统资源调整连接池参数
            if memory_gb >= 8:
                self.config.pool_size = min(30, max(20, int(cpu_cores * 2)))
                self.config.max_overflow = min(50, self.config.pool_size * 2)
            elif memory_gb >= 4:
                self.config.pool_size = min(20, max(15, int(cpu_cores * 1.5)))
                self.config.max_overflow = min(30, self.config.pool_size * 2)
            else:
                self.config.pool_size = min(15, max(10, cpu_cores))
                self.config.max_overflow = min(20, self.config.pool_size * 2)
            
            # 调整超时参数
            self.config.pool_timeout = 30
            self.config.pool_recycle = 3600  # 1小时
            
            pool_config = {
                "pool_size": self.config.pool_size,
                "max_overflow": self.config.max_overflow,
                "pool_timeout": self.config.pool_timeout,
                "pool_recycle": self.config.pool_recycle,
                "system_memory_gb": memory_gb,
                "cpu_cores": cpu_cores
            }
            
            self.logger.info(f"✅ 连接池配置优化完成: {pool_config}")
            return pool_config
            
        except Exception as e:
            self.logger.error(f"❌ 连接池配置优化失败: {e}")
            return {}
    
    def generate_postgresql_config(self) -> str:
        """生成PostgreSQL配置文件"""
        try:
            self.logger.info("生成PostgreSQL配置...")
            
            # 获取系统资源
            memory_gb = psutil.virtual_memory().total / (1024**3)
            cpu_cores = psutil.cpu_count()
            
            # 计算配置参数
            shared_buffers_mb = int(memory_gb * 1024 * 0.25)  # 25% of RAM
            effective_cache_size_mb = int(memory_gb * 1024 * 0.75)  # 75% of RAM
            work_mem_mb = max(4, int(memory_gb * 1024 / 200))  # RAM/200
            maintenance_work_mem_mb = min(2048, int(memory_gb * 1024 / 16))  # RAM/16, max 2GB
            max_connections = min(200, max(100, cpu_cores * 4))
            
            # 更新配置对象
            self.config.shared_buffers_mb = shared_buffers_mb
            self.config.effective_cache_size_mb = effective_cache_size_mb
            self.config.work_mem_mb = work_mem_mb
            self.config.maintenance_work_mem_mb = maintenance_work_mem_mb
            self.config.max_connections = max_connections
            
            # 生成配置内容
            config_content = f"""# PostgreSQL Configuration - Optimized for Lawsker
# Generated for system with {memory_gb:.1f}GB RAM and {cpu_cores} CPU cores
# Generated at: {datetime.now().isoformat()}

# Memory Configuration
shared_buffers = {shared_buffers_mb}MB
effective_cache_size = {effective_cache_size_mb}MB
work_mem = {work_mem_mb}MB
maintenance_work_mem = {maintenance_work_mem_mb}MB
temp_buffers = 8MB

# Connection Configuration
max_connections = {max_connections}
superuser_reserved_connections = 3

# Checkpoint Configuration
checkpoint_completion_target = 0.9
checkpoint_timeout = 5min
max_wal_size = 1GB
min_wal_size = 80MB

# Query Planner Configuration
random_page_cost = 1.1
effective_io_concurrency = 200
seq_page_cost = 1.0
cpu_tuple_cost = 0.01
cpu_index_tuple_cost = 0.005
cpu_operator_cost = 0.0025

# Parallel Query Configuration
max_worker_processes = {cpu_cores}
max_parallel_workers = {cpu_cores}
max_parallel_workers_per_gather = {min(4, cpu_cores // 2)}
max_parallel_maintenance_workers = {min(3, cpu_cores // 4)}
parallel_tuple_cost = 0.1
parallel_setup_cost = 1000.0

# Logging Configuration
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 10MB
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
log_temp_files = 0
log_autovacuum_min_duration = 0

# Statistics Configuration
track_activities = on
track_counts = on
track_io_timing = on
track_functions = all
track_activity_query_size = 1024
update_process_title = on

# Autovacuum Configuration
autovacuum = on
autovacuum_max_workers = {min(3, max(1, cpu_cores // 4))}
autovacuum_naptime = 1min
autovacuum_vacuum_threshold = 50
autovacuum_analyze_threshold = 50
autovacuum_vacuum_scale_factor = 0.2
autovacuum_analyze_scale_factor = 0.1
autovacuum_freeze_max_age = 200000000
autovacuum_multixact_freeze_max_age = 400000000
autovacuum_vacuum_cost_delay = 20ms
autovacuum_vacuum_cost_limit = 200

# Extensions Configuration
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.max = 10000
pg_stat_statements.track = all
pg_stat_statements.track_utility = off
pg_stat_statements.save = on

# SSL Configuration
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'
ssl_ca_file = ''
ssl_crl_file = ''
ssl_prefer_server_ciphers = on
ssl_ciphers = 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384'
ssl_ecdh_curve = 'prime256v1'
"""
            
            self.logger.info("✅ PostgreSQL配置生成完成")
            return config_content
            
        except Exception as e:
            self.logger.error(f"❌ 生成PostgreSQL配置失败: {e}")
            return ""
    
    def apply_postgresql_config(self, config_content: str) -> bool:
        """应用PostgreSQL配置"""
        try:
            self.logger.info("应用PostgreSQL配置...")
            
            # 查找PostgreSQL配置文件
            possible_paths = [
                "/etc/postgresql/*/main/postgresql.conf",
                "/var/lib/postgresql/data/postgresql.conf",
                "/usr/local/var/postgres/postgresql.conf",
                "/opt/homebrew/var/postgres/postgresql.conf"
            ]
            
            config_file = None
            for path_pattern in possible_paths:
                import glob
                matches = glob.glob(path_pattern)
                if matches:
                    config_file = matches[0]
                    break
            
            if not config_file:
                self.logger.warning("未找到PostgreSQL配置文件，保存到临时文件")
                config_file = self.backup_dir / "postgresql_optimized.conf"
                
            # 备份原配置文件
            if Path(config_file).exists():
                backup_file = self.backup_dir / f"postgresql.conf.backup.{int(time.time())}"
                shutil.copy2(config_file, backup_file)
                self.logger.info(f"原配置文件已备份到: {backup_file}")
            
            # 写入新配置
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            self.logger.info(f"✅ PostgreSQL配置已保存到: {config_file}")
            self.postgresql_conf_path = config_file
            
            # 提示重启服务
            self.logger.info("⚠️  请重启PostgreSQL服务以应用新配置")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 应用PostgreSQL配置失败: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息"""
        try:
            info = {
                "config": self.config.to_dict(),
                "status": self.status.to_dict(),
                "system_info": {
                    "memory_gb": psutil.virtual_memory().total / (1024**3),
                    "cpu_cores": psutil.cpu_count(),
                    "disk_usage": {}
                },
                "connection_info": {},
                "performance_metrics": {}
            }
            
            # 获取磁盘使用情况
            try:
                disk_usage = psutil.disk_usage('/')
                info["system_info"]["disk_usage"] = {
                    "total_gb": disk_usage.total / (1024**3),
                    "used_gb": disk_usage.used / (1024**3),
                    "free_gb": disk_usage.free / (1024**3),
                    "percent": (disk_usage.used / disk_usage.total) * 100
                }
            except:
                pass
            
            # 如果连接成功，获取数据库统计信息
            if self.status.connection_successful:
                try:
                    database_url = (
                        f"postgresql://{self.config.user}:{self.config.password}@"
                        f"{self.config.host}:{self.config.port}/{self.config.name}"
                    )
                    
                    engine = create_engine(database_url, pool_pre_ping=True)
                    with engine.connect() as conn:
                        # 获取数据库版本
                        result = conn.execute(text("SELECT version()"))
                        info["connection_info"]["version"] = result.fetchone()[0]
                        
                        # 获取连接数
                        result = conn.execute(text(
                            "SELECT count(*) FROM pg_stat_activity WHERE datname = %s"
                        ), (self.config.name,))
                        info["connection_info"]["active_connections"] = result.fetchone()[0]
                        
                        # 获取数据库大小
                        result = conn.execute(text(
                            "SELECT pg_size_pretty(pg_database_size(%s))"
                        ), (self.config.name,))
                        info["connection_info"]["database_size"] = result.fetchone()[0]
                        
                    engine.dispose()
                    
                except Exception as e:
                    self.logger.warning(f"获取数据库统计信息失败: {e}")
            
            return info
            
        except Exception as e:
            self.logger.error(f"获取数据库信息失败: {e}")
            return {"error": str(e)}
    
    def save_configuration_report(self, filename: str = None) -> str:
        """保存配置报告"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"database_config_report_{timestamp}.json"
            
            report_path = self.backup_dir / filename
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "database_info": self.get_database_info(),
                "postgresql_config_path": str(self.postgresql_conf_path) if self.postgresql_conf_path else None,
                "backup_directory": str(self.backup_dir)
            }
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✅ 配置报告已保存到: {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.logger.error(f"❌ 保存配置报告失败: {e}")
            return ""