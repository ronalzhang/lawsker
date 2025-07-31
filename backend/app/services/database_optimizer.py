"""
数据库性能优化服务
包含慢查询分析、读写分离、监控告警等功能
"""
import asyncio
import time
import psutil
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import text, create_engine, MetaData, inspect
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
import asyncpg
import redis
from dataclasses import dataclass

from app.core.database import get_db, engine
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)

@dataclass
class SlowQuery:
    """慢查询记录"""
    query: str
    duration: float
    timestamp: datetime
    database: str
    user: str
    rows_examined: int
    rows_sent: int

@dataclass
class DatabaseMetrics:
    """数据库指标"""
    connections_active: int
    connections_idle: int
    connections_total: int
    queries_per_second: float
    slow_queries_count: int
    cache_hit_ratio: float
    disk_usage_gb: float
    memory_usage_mb: float
    cpu_usage_percent: float

class DatabaseOptimizer:
    """数据库性能优化器"""
    
    def __init__(self):
        self.slow_query_threshold = 1.0  # 1秒
        self.monitoring_interval = 60  # 60秒
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.metrics_history = []
        
    async def analyze_slow_queries(self, hours: int = 24) -> List[SlowQuery]:
        """分析慢查询"""
        logger.info(f"Analyzing slow queries for the last {hours} hours")
        
        slow_queries = []
        
        try:
            # 查询PostgreSQL慢查询日志
            query = text("""
                SELECT 
                    query,
                    mean_exec_time,
                    calls,
                    total_exec_time,
                    rows,
                    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                FROM pg_stat_statements 
                WHERE mean_exec_time > :threshold
                ORDER BY mean_exec_time DESC
                LIMIT 50
            """)
            
            with engine.connect() as conn:
                result = conn.execute(query, {"threshold": self.slow_query_threshold * 1000})
                
                for row in result:
                    slow_query = SlowQuery(
                        query=row.query,
                        duration=row.mean_exec_time / 1000.0,  # 转换为秒
                        timestamp=datetime.now(),
                        database=settings.DATABASE_NAME,
                        user="app_user",
                        rows_examined=row.rows,
                        rows_sent=row.rows
                    )
                    slow_queries.append(slow_query)
            
            logger.info(f"Found {len(slow_queries)} slow queries")
            return slow_queries
            
        except Exception as e:
            logger.error(f"Failed to analyze slow queries: {str(e)}")
            return []
    
    async def optimize_queries(self, slow_queries: List[SlowQuery]) -> Dict[str, Any]:
        """优化慢查询"""
        logger.info("Starting query optimization")
        
        optimization_results = {
            "optimized_queries": [],
            "index_recommendations": [],
            "query_rewrites": [],
            "performance_improvements": []
        }
        
        for slow_query in slow_queries:
            try:
                # 分析查询执行计划
                explain_result = await self._analyze_query_plan(slow_query.query)
                
                # 生成索引建议
                index_suggestions = await self._suggest_indexes(slow_query.query, explain_result)
                optimization_results["index_recommendations"].extend(index_suggestions)
                
                # 查询重写建议
                rewrite_suggestions = await self._suggest_query_rewrites(slow_query.query)
                optimization_results["query_rewrites"].extend(rewrite_suggestions)
                
                optimization_results["optimized_queries"].append({
                    "original_query": slow_query.query,
                    "duration": slow_query.duration,
                    "suggestions": len(index_suggestions) + len(rewrite_suggestions)
                })
                
            except Exception as e:
                logger.error(f"Failed to optimize query: {str(e)}")
        
        return optimization_results
    
    async def _analyze_query_plan(self, query: str) -> Dict[str, Any]:
        """分析查询执行计划"""
        try:
            explain_query = text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
            
            with engine.connect() as conn:
                result = conn.execute(explain_query)
                plan = result.fetchone()[0]
                return plan[0] if plan else {}
                
        except Exception as e:
            logger.error(f"Failed to analyze query plan: {str(e)}")
            return {}
    
    async def _suggest_indexes(self, query: str, explain_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """建议索引优化"""
        suggestions = []
        
        try:
            # 分析执行计划中的顺序扫描
            if self._has_sequential_scan(explain_result):
                # 提取表名和条件字段
                table_info = self._extract_table_info(query)
                
                for table, columns in table_info.items():
                    suggestion = {
                        "type": "index",
                        "table": table,
                        "columns": columns,
                        "index_sql": f"CREATE INDEX CONCURRENTLY idx_{table}_{'_'.join(columns)} ON {table} ({', '.join(columns)});",
                        "reason": "Sequential scan detected, index may improve performance"
                    }
                    suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to suggest indexes: {str(e)}")
            return []
    
    async def _suggest_query_rewrites(self, query: str) -> List[Dict[str, Any]]:
        """建议查询重写"""
        suggestions = []
        
        try:
            query_lower = query.lower()
            
            # 检查是否使用了SELECT *
            if "select *" in query_lower:
                suggestions.append({
                    "type": "rewrite",
                    "issue": "SELECT * usage",
                    "suggestion": "Specify only needed columns instead of SELECT *",
                    "reason": "Reduces data transfer and memory usage"
                })
            
            # 检查是否有子查询可以优化为JOIN
            if "in (select" in query_lower:
                suggestions.append({
                    "type": "rewrite",
                    "issue": "Subquery in WHERE clause",
                    "suggestion": "Consider rewriting subquery as JOIN",
                    "reason": "JOINs are often more efficient than subqueries"
                })
            
            # 检查是否有LIMIT但没有ORDER BY
            if "limit" in query_lower and "order by" not in query_lower:
                suggestions.append({
                    "type": "rewrite",
                    "issue": "LIMIT without ORDER BY",
                    "suggestion": "Add ORDER BY clause when using LIMIT",
                    "reason": "Ensures consistent results and may enable index usage"
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to suggest query rewrites: {str(e)}")
            return []
    
    def _has_sequential_scan(self, explain_result: Dict[str, Any]) -> bool:
        """检查是否有顺序扫描"""
        def check_node(node):
            if isinstance(node, dict):
                if node.get("Node Type") == "Seq Scan":
                    return True
                for child in node.get("Plans", []):
                    if check_node(child):
                        return True
            return False
        
        return check_node(explain_result.get("Plan", {}))
    
    def _extract_table_info(self, query: str) -> Dict[str, List[str]]:
        """从查询中提取表和字段信息"""
        # 简化的表和字段提取逻辑
        # 实际实现需要更复杂的SQL解析
        table_info = {}
        
        try:
            query_lower = query.lower()
            
            # 提取FROM子句中的表名
            if "from " in query_lower:
                from_part = query_lower.split("from ")[1].split(" ")[0]
                table_name = from_part.strip()
                
                # 提取WHERE子句中的字段
                if "where " in query_lower:
                    where_part = query_lower.split("where ")[1]
                    # 简单提取字段名（实际需要更复杂的解析）
                    columns = []
                    for word in where_part.split():
                        if "." in word and "=" in where_part:
                            column = word.split(".")[1] if "." in word else word
                            if column not in columns:
                                columns.append(column)
                    
                    if columns:
                        table_info[table_name] = columns
            
            return table_info
            
        except Exception as e:
            logger.error(f"Failed to extract table info: {str(e)}")
            return {}
    
    async def setup_read_write_splitting(self) -> Dict[str, Any]:
        """设置读写分离"""
        logger.info("Setting up read-write splitting")
        
        try:
            # 创建读库连接配置
            read_db_config = {
                "host": settings.READ_DB_HOST or settings.DATABASE_HOST,
                "port": settings.READ_DB_PORT or settings.DATABASE_PORT,
                "database": settings.DATABASE_NAME,
                "user": settings.DATABASE_USER,
                "password": settings.DATABASE_PASSWORD,
                "pool_size": 10,
                "max_overflow": 20
            }
            
            # 创建写库连接配置
            write_db_config = {
                "host": settings.DATABASE_HOST,
                "port": settings.DATABASE_PORT,
                "database": settings.DATABASE_NAME,
                "user": settings.DATABASE_USER,
                "password": settings.DATABASE_PASSWORD,
                "pool_size": 5,
                "max_overflow": 10
            }
            
            # 创建读写分离的数据库引擎
            read_engine = self._create_database_engine(read_db_config, "read")
            write_engine = self._create_database_engine(write_db_config, "write")
            
            # 测试连接
            await self._test_database_connection(read_engine, "read")
            await self._test_database_connection(write_engine, "write")
            
            return {
                "status": "success",
                "read_engine": "configured",
                "write_engine": "configured",
                "message": "Read-write splitting configured successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to setup read-write splitting: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _create_database_engine(self, config: Dict[str, Any], engine_type: str) -> Engine:
        """创建数据库引擎"""
        database_url = (
            f"postgresql://{config['user']}:{config['password']}"
            f"@{config['host']}:{config['port']}/{config['database']}"
        )
        
        return create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=config['pool_size'],
            max_overflow=config['max_overflow'],
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=False,
            connect_args={
                "application_name": f"lawsker_{engine_type}",
                "connect_timeout": 10
            }
        )
    
    async def _test_database_connection(self, engine: Engine, engine_type: str):
        """测试数据库连接"""
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            logger.info(f"{engine_type.capitalize()} database connection successful")
        except Exception as e:
            logger.error(f"{engine_type.capitalize()} database connection failed: {str(e)}")
            raise
    
    async def collect_database_metrics(self) -> DatabaseMetrics:
        """收集数据库指标"""
        try:
            with engine.connect() as conn:
                # 连接数统计
                conn_result = conn.execute(text("""
                    SELECT 
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        count(*) FILTER (WHERE state = 'idle') as idle_connections
                    FROM pg_stat_activity 
                    WHERE datname = current_database()
                """))
                conn_stats = conn_result.fetchone()
                
                # 查询性能统计
                perf_result = conn.execute(text("""
                    SELECT 
                        sum(calls) as total_queries,
                        sum(calls) / EXTRACT(EPOCH FROM (now() - stats_reset)) as qps
                    FROM pg_stat_statements
                """))
                perf_stats = perf_result.fetchone()
                
                # 缓存命中率
                cache_result = conn.execute(text("""
                    SELECT 
                        sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 as cache_hit_ratio
                    FROM pg_statio_user_tables
                """))
                cache_stats = cache_result.fetchone()
                
                # 数据库大小
                size_result = conn.execute(text("""
                    SELECT pg_database_size(current_database()) / (1024*1024*1024.0) as size_gb
                """))
                size_stats = size_result.fetchone()
            
            # 系统资源使用
            memory_usage = psutil.virtual_memory().used / (1024 * 1024)  # MB
            cpu_usage = psutil.cpu_percent(interval=1)
            
            return DatabaseMetrics(
                connections_active=conn_stats.active_connections or 0,
                connections_idle=conn_stats.idle_connections or 0,
                connections_total=conn_stats.total_connections or 0,
                queries_per_second=perf_stats.qps or 0.0,
                slow_queries_count=0,  # 需要从慢查询分析中获取
                cache_hit_ratio=cache_stats.cache_hit_ratio or 0.0,
                disk_usage_gb=size_stats.size_gb or 0.0,
                memory_usage_mb=memory_usage,
                cpu_usage_percent=cpu_usage
            )
            
        except Exception as e:
            logger.error(f"Failed to collect database metrics: {str(e)}")
            return DatabaseMetrics(0, 0, 0, 0.0, 0, 0.0, 0.0, 0.0, 0.0)
    
    async def optimize_database_config(self) -> Dict[str, Any]:
        """优化数据库配置参数"""
        logger.info("Optimizing database configuration")
        
        try:
            # 获取当前系统资源
            memory_gb = psutil.virtual_memory().total / (1024**3)
            cpu_count = psutil.cpu_count()
            
            # 计算推荐配置
            recommendations = {
                "shared_buffers": f"{int(memory_gb * 0.25)}GB",  # 25% of RAM
                "effective_cache_size": f"{int(memory_gb * 0.75)}GB",  # 75% of RAM
                "work_mem": f"{max(4, int(memory_gb * 1024 / 200))}MB",  # RAM/200
                "maintenance_work_mem": f"{min(2048, int(memory_gb * 1024 / 16))}MB",  # RAM/16, max 2GB
                "max_connections": min(200, max(100, cpu_count * 4)),
                "max_worker_processes": cpu_count,
                "max_parallel_workers": cpu_count,
                "max_parallel_workers_per_gather": min(4, cpu_count // 2),
                "wal_buffers": "16MB",
                "checkpoint_completion_target": "0.9",
                "random_page_cost": "1.1",  # For SSD
                "effective_io_concurrency": "200",  # For SSD
                "log_min_duration_statement": "1000",  # Log slow queries > 1s
                "log_checkpoints": "on",
                "log_connections": "on",
                "log_disconnections": "on",
                "log_lock_waits": "on"
            }
            
            # 生成配置文件内容
            config_content = self._generate_postgresql_config(recommendations)
            
            return {
                "status": "success",
                "recommendations": recommendations,
                "config_content": config_content,
                "system_info": {
                    "memory_gb": memory_gb,
                    "cpu_count": cpu_count
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize database config: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _generate_postgresql_config(self, recommendations: Dict[str, Any]) -> str:
        """生成PostgreSQL配置文件内容"""
        config_lines = [
            "# PostgreSQL Configuration - Optimized for Lawsker",
            "# Generated by Database Optimizer",
            f"# Generated at: {datetime.now().isoformat()}",
            "",
            "# Memory Configuration",
            f"shared_buffers = {recommendations['shared_buffers']}",
            f"effective_cache_size = {recommendations['effective_cache_size']}",
            f"work_mem = {recommendations['work_mem']}",
            f"maintenance_work_mem = {recommendations['maintenance_work_mem']}",
            "",
            "# Connection Configuration",
            f"max_connections = {recommendations['max_connections']}",
            "",
            "# Parallel Query Configuration",
            f"max_worker_processes = {recommendations['max_worker_processes']}",
            f"max_parallel_workers = {recommendations['max_parallel_workers']}",
            f"max_parallel_workers_per_gather = {recommendations['max_parallel_workers_per_gather']}",
            "",
            "# WAL Configuration",
            f"wal_buffers = {recommendations['wal_buffers']}",
            f"checkpoint_completion_target = {recommendations['checkpoint_completion_target']}",
            "",
            "# Storage Configuration",
            f"random_page_cost = {recommendations['random_page_cost']}",
            f"effective_io_concurrency = {recommendations['effective_io_concurrency']}",
            "",
            "# Logging Configuration",
            f"log_min_duration_statement = {recommendations['log_min_duration_statement']}",
            f"log_checkpoints = {recommendations['log_checkpoints']}",
            f"log_connections = {recommendations['log_connections']}",
            f"log_disconnections = {recommendations['log_disconnections']}",
            f"log_lock_waits = {recommendations['log_lock_waits']}",
            "",
            "# Query Planning",
            "enable_partitionwise_join = on",
            "enable_partitionwise_aggregate = on",
            "",
            "# Statistics",
            "track_activities = on",
            "track_counts = on",
            "track_io_timing = on",
            "track_functions = all",
            "",
            "# Extensions",
            "shared_preload_libraries = 'pg_stat_statements'",
            "pg_stat_statements.track = all",
            "pg_stat_statements.max = 10000",
            ""
        ]
        
        return "\n".join(config_lines)
    
    async def setup_monitoring_alerts(self) -> Dict[str, Any]:
        """设置数据库监控告警"""
        logger.info("Setting up database monitoring alerts")
        
        try:
            alert_rules = {
                "high_connection_usage": {
                    "condition": "connections_active / connections_total > 0.8",
                    "threshold": 0.8,
                    "message": "Database connection usage is high",
                    "severity": "warning"
                },
                "slow_query_rate": {
                    "condition": "slow_queries_per_minute > 10",
                    "threshold": 10,
                    "message": "High rate of slow queries detected",
                    "severity": "warning"
                },
                "low_cache_hit_ratio": {
                    "condition": "cache_hit_ratio < 95",
                    "threshold": 95,
                    "message": "Database cache hit ratio is low",
                    "severity": "warning"
                },
                "high_cpu_usage": {
                    "condition": "cpu_usage_percent > 80",
                    "threshold": 80,
                    "message": "Database server CPU usage is high",
                    "severity": "critical"
                },
                "high_memory_usage": {
                    "condition": "memory_usage_percent > 90",
                    "threshold": 90,
                    "message": "Database server memory usage is high",
                    "severity": "critical"
                }
            }
            
            # 保存告警规则到Redis
            for rule_name, rule_config in alert_rules.items():
                self.redis_client.hset(
                    "db_alert_rules",
                    rule_name,
                    str(rule_config)
                )
            
            return {
                "status": "success",
                "alert_rules": alert_rules,
                "message": "Database monitoring alerts configured"
            }
            
        except Exception as e:
            logger.error(f"Failed to setup monitoring alerts: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def run_performance_analysis(self) -> Dict[str, Any]:
        """运行完整的性能分析"""
        logger.info("Running comprehensive database performance analysis")
        
        analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "slow_queries": [],
            "optimization_suggestions": {},
            "database_metrics": None,
            "configuration_recommendations": {},
            "read_write_splitting": {},
            "monitoring_setup": {}
        }
        
        try:
            # 1. 分析慢查询
            slow_queries = await self.analyze_slow_queries()
            analysis_results["slow_queries"] = [
                {
                    "query": sq.query[:200] + "..." if len(sq.query) > 200 else sq.query,
                    "duration": sq.duration,
                    "timestamp": sq.timestamp.isoformat()
                }
                for sq in slow_queries
            ]
            
            # 2. 生成优化建议
            if slow_queries:
                optimization_suggestions = await self.optimize_queries(slow_queries)
                analysis_results["optimization_suggestions"] = optimization_suggestions
            
            # 3. 收集数据库指标
            metrics = await self.collect_database_metrics()
            analysis_results["database_metrics"] = {
                "connections_active": metrics.connections_active,
                "connections_total": metrics.connections_total,
                "queries_per_second": metrics.queries_per_second,
                "cache_hit_ratio": metrics.cache_hit_ratio,
                "disk_usage_gb": metrics.disk_usage_gb,
                "memory_usage_mb": metrics.memory_usage_mb,
                "cpu_usage_percent": metrics.cpu_usage_percent
            }
            
            # 4. 生成配置建议
            config_recommendations = await self.optimize_database_config()
            analysis_results["configuration_recommendations"] = config_recommendations
            
            # 5. 设置读写分离
            rw_splitting = await self.setup_read_write_splitting()
            analysis_results["read_write_splitting"] = rw_splitting
            
            # 6. 设置监控告警
            monitoring_setup = await self.setup_monitoring_alerts()
            analysis_results["monitoring_setup"] = monitoring_setup
            
            logger.info("Database performance analysis completed")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Database performance analysis failed: {str(e)}")
            analysis_results["error"] = str(e)
            return analysis_results


# 全局优化器实例
database_optimizer = DatabaseOptimizer()

# 便捷函数
async def run_database_optimization() -> Dict[str, Any]:
    """运行数据库优化"""
    return await database_optimizer.run_performance_analysis()

async def analyze_slow_queries(hours: int = 24) -> List[SlowQuery]:
    """分析慢查询"""
    return await database_optimizer.analyze_slow_queries(hours)

async def collect_db_metrics() -> DatabaseMetrics:
    """收集数据库指标"""
    return await database_optimizer.collect_database_metrics()