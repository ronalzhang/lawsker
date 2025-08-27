"""
数据库性能优化模块
优化数据库连接池、查询性能、索引等
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker
import time

from app.core.config import settings

logger = logging.getLogger(__name__)

class DatabasePerformanceOptimizer:
    """数据库性能优化器"""
    
    def __init__(self):
        self.connection_pool_config = {
            'pool_size': 20,  # 连接池大小
            'max_overflow': 30,  # 最大溢出连接数
            'pool_timeout': 30,  # 连接超时时间
            'pool_recycle': 3600,  # 连接回收时间（1小时）
            'pool_pre_ping': True,  # 连接前ping检查
        }
        self.query_cache = {}
        self.slow_query_threshold = 1.0  # 1秒
    
    def create_optimized_engine(self, database_url: str):
        """创建优化的数据库引擎"""
        return create_async_engine(
            database_url,
            poolclass=QueuePool,
            **self.connection_pool_config,
            echo=False,  # 生产环境关闭SQL日志
            future=True
        )
    
    async def optimize_database_settings(self, db: AsyncSession):
        """优化数据库设置"""
        try:
            # 设置数据库参数优化
            optimization_queries = [
                # 增加共享缓冲区
                "ALTER SYSTEM SET shared_buffers = '256MB'",
                # 优化工作内存
                "ALTER SYSTEM SET work_mem = '4MB'",
                # 优化维护工作内存
                "ALTER SYSTEM SET maintenance_work_mem = '64MB'",
                # 优化检查点设置
                "ALTER SYSTEM SET checkpoint_completion_target = 0.9",
                # 优化WAL缓冲区
                "ALTER SYSTEM SET wal_buffers = '16MB'",
                # 优化随机页面成本
                "ALTER SYSTEM SET random_page_cost = 1.1",
                # 启用并行查询
                "ALTER SYSTEM SET max_parallel_workers_per_gather = 2",
            ]
            
            for query in optimization_queries:
                try:
                    await db.execute(text(query))
                    logger.info(f"Applied database optimization: {query}")
                except Exception as e:
                    logger.warning(f"Failed to apply optimization {query}: {e}")
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"Database optimization error: {e}")
            await db.rollback()
    
    async def create_performance_indexes(self, db: AsyncSession):
        """创建性能优化索引"""
        try:
            # 性能优化索引
            indexes = [
                # 用户表索引
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_active ON users(email) WHERE status = 'active'",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_workspace_id ON users(workspace_id)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_account_type ON users(account_type)",
                
                # 律师等级表索引
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lawyer_levels_points ON lawyer_level_details(level_points DESC)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lawyer_levels_user ON lawyer_level_details(user_id)",
                
                # 积分记录表索引
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_points_records_user_time ON lawyer_point_records(user_id, created_at DESC)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_points_records_action ON lawyer_point_records(action_type)",
                
                # Credits表索引
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_credits_user ON user_credits(user_id)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_credits_purchase_user_time ON credit_purchase_records(user_id, created_at DESC)",
                
                # 会员表索引
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lawyer_membership_user ON lawyer_memberships(user_id)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lawyer_membership_type ON lawyer_memberships(membership_type)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lawyer_membership_active ON lawyer_memberships(user_id) WHERE status = 'active'",
                
                # 案件表索引
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cases_status_created ON cases(status, created_at DESC)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cases_lawyer_status ON cases(assigned_lawyer_id, status)",
                
                # 访问日志表索引（如果存在）
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_access_logs_user_time ON access_logs(user_id, created_at DESC)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_access_logs_ip_time ON access_logs(ip_address, created_at DESC)",
            ]
            
            for index_query in indexes:
                try:
                    await db.execute(text(index_query))
                    logger.info(f"Created index: {index_query.split('idx_')[1].split(' ')[0]}")
                except Exception as e:
                    logger.warning(f"Failed to create index: {e}")
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"Index creation error: {e}")
            await db.rollback()
    
    async def analyze_query_performance(self, db: AsyncSession):
        """分析查询性能"""
        try:
            # 获取慢查询统计
            slow_queries_query = text("""
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows,
                    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                FROM pg_stat_statements 
                WHERE mean_time > :threshold
                ORDER BY mean_time DESC 
                LIMIT 20
            """)
            
            result = await db.execute(slow_queries_query, {"threshold": self.slow_query_threshold * 1000})
            slow_queries = result.fetchall()
            
            if slow_queries:
                logger.warning(f"Found {len(slow_queries)} slow queries")
                for query in slow_queries:
                    logger.warning(f"Slow query: {query.query[:100]}... "
                                 f"Mean time: {query.mean_time:.2f}ms, "
                                 f"Calls: {query.calls}, "
                                 f"Hit rate: {query.hit_percent:.1f}%")
            
            # 获取表统计信息
            table_stats_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins,
                    n_tup_upd,
                    n_tup_del,
                    n_live_tup,
                    n_dead_tup,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables 
                ORDER BY n_live_tup DESC
            """)
            
            result = await db.execute(table_stats_query)
            table_stats = result.fetchall()
            
            # 检查需要维护的表
            for table in table_stats:
                dead_ratio = table.n_dead_tup / max(table.n_live_tup, 1)
                if dead_ratio > 0.1:  # 死元组比例超过10%
                    logger.warning(f"Table {table.tablename} needs maintenance: "
                                 f"dead ratio {dead_ratio:.2f}")
            
        except Exception as e:
            logger.error(f"Query performance analysis error: {e}")
    
    async def optimize_table_maintenance(self, db: AsyncSession):
        """优化表维护"""
        try:
            # 获取需要维护的表
            maintenance_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    n_dead_tup,
                    n_live_tup,
                    last_vacuum,
                    last_analyze
                FROM pg_stat_user_tables 
                WHERE n_dead_tup > 1000 
                   OR last_vacuum < NOW() - INTERVAL '1 day'
                   OR last_analyze < NOW() - INTERVAL '1 day'
            """)
            
            result = await db.execute(maintenance_query)
            tables_to_maintain = result.fetchall()
            
            for table in tables_to_maintain:
                table_name = f"{table.schemaname}.{table.tablename}"
                
                # 执行VACUUM ANALYZE
                try:
                    await db.execute(text(f"VACUUM ANALYZE {table_name}"))
                    logger.info(f"Maintained table: {table_name}")
                except Exception as e:
                    logger.warning(f"Failed to maintain table {table_name}: {e}")
            
        except Exception as e:
            logger.error(f"Table maintenance error: {e}")

class QueryOptimizer:
    """查询优化器"""
    
    def __init__(self):
        self.query_cache = {}
        self.cache_ttl = 300  # 5分钟缓存
    
    async def execute_optimized_query(self, db: AsyncSession, query: str, params: dict = None):
        """执行优化的查询"""
        start_time = time.time()
        
        try:
            # 检查查询缓存
            cache_key = f"{query}:{str(params)}"
            if cache_key in self.query_cache:
                cache_data = self.query_cache[cache_key]
                if time.time() - cache_data['timestamp'] < self.cache_ttl:
                    return cache_data['result']
            
            # 执行查询
            result = await db.execute(text(query), params or {})
            data = result.fetchall()
            
            # 缓存结果
            self.query_cache[cache_key] = {
                'result': data,
                'timestamp': time.time()
            }
            
            # 记录查询时间
            duration = time.time() - start_time
            if duration > 1.0:  # 超过1秒的查询
                logger.warning(f"Slow query executed: {query[:100]}... took {duration:.3f}s")
            
            return data
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Query execution error: {e}, duration: {duration:.3f}s")
            raise
    
    def clear_cache(self):
        """清理查询缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, data in self.query_cache.items()
            if current_time - data['timestamp'] > self.cache_ttl
        ]
        
        for key in expired_keys:
            del self.query_cache[key]
        
        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired query cache entries")

class ConnectionPoolMonitor:
    """连接池监控器"""
    
    def __init__(self, engine):
        self.engine = engine
        self.pool_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'idle_connections': 0,
            'overflow_connections': 0
        }
    
    async def collect_pool_stats(self):
        """收集连接池统计信息"""
        try:
            pool = self.engine.pool
            
            self.pool_stats.update({
                'total_connections': pool.size(),
                'active_connections': pool.checkedout(),
                'idle_connections': pool.checkedin(),
                'overflow_connections': pool.overflow(),
            })
            
            # 检查连接池健康状态
            if self.pool_stats['active_connections'] > pool.size() * 0.8:
                logger.warning(f"High connection pool usage: "
                             f"{self.pool_stats['active_connections']}/{pool.size()}")
            
            return self.pool_stats
            
        except Exception as e:
            logger.error(f"Failed to collect pool stats: {e}")
            return self.pool_stats
    
    async def optimize_pool_settings(self):
        """优化连接池设置"""
        try:
            stats = await self.collect_pool_stats()
            
            # 根据使用情况调整连接池
            if stats['active_connections'] > stats['total_connections'] * 0.9:
                logger.info("Consider increasing connection pool size")
            elif stats['active_connections'] < stats['total_connections'] * 0.3:
                logger.info("Consider decreasing connection pool size")
                
        except Exception as e:
            logger.error(f"Pool optimization error: {e}")

# 全局实例
db_optimizer = DatabasePerformanceOptimizer()
query_optimizer = QueryOptimizer()

async def initialize_database_performance():
    """初始化数据库性能优化"""
    try:
        logger.info("Initializing database performance optimization...")
        # 这里可以添加初始化逻辑
        logger.info("Database performance optimization initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database performance: {e}")

async def cleanup_database_performance():
    """清理数据库性能优化"""
    try:
        query_optimizer.clear_cache()
        logger.info("Database performance cleanup completed")
    except Exception as e:
        logger.error(f"Database performance cleanup error: {e}")