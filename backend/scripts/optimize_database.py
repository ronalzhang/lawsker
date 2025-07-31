#!/usr/bin/env python3
"""
数据库优化脚本
执行索引优化、统计信息更新等数据库优化操作
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def execute_sql_file(db: AsyncSession, file_path: str):
    """执行SQL文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句（简单处理，按分号分割）
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            if statement and not statement.startswith('--'):
                try:
                    logger.info(f"执行SQL语句 {i+1}/{len(statements)}")
                    await db.execute(text(statement))
                    await db.commit()
                except Exception as e:
                    logger.warning(f"SQL语句执行失败 (可能已存在): {str(e)}")
                    await db.rollback()
        
        logger.info(f"SQL文件执行完成: {file_path}")
        
    except Exception as e:
        logger.error(f"执行SQL文件失败: {str(e)}")
        raise


async def analyze_database_performance():
    """分析数据库性能"""
    try:
        async with AsyncSessionLocal() as db:
            logger.info("🔍 分析数据库性能...")
            
            # 检查表大小
            table_sizes_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10;
            """)
            
            result = await db.execute(table_sizes_query)
            tables = result.fetchall()
            
            logger.info("📊 数据库表大小统计:")
            for table in tables:
                logger.info(f"   {table.tablename}: {table.size}")
            
            # 检查索引使用情况
            index_usage_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    CASE 
                        WHEN idx_scan = 0 THEN 'UNUSED'
                        WHEN idx_scan < 100 THEN 'LOW_USAGE'
                        WHEN idx_scan < 1000 THEN 'MEDIUM_USAGE'
                        ELSE 'HIGH_USAGE'
                    END as usage_level
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                ORDER BY idx_scan DESC
                LIMIT 20;
            """)
            
            result = await db.execute(index_usage_query)
            indexes = result.fetchall()
            
            logger.info("📈 索引使用情况统计:")
            for index in indexes:
                logger.info(f"   {index.indexname} ({index.tablename}): {index.idx_scan} scans - {index.usage_level}")
            
            # 检查未使用的索引
            unused_indexes_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public' AND idx_scan = 0
                ORDER BY tablename, indexname;
            """)
            
            result = await db.execute(unused_indexes_query)
            unused_indexes = result.fetchall()
            
            if unused_indexes:
                logger.warning("⚠️  发现未使用的索引:")
                for index in unused_indexes:
                    logger.warning(f"   {index.indexname} on {index.tablename}")
            else:
                logger.info("✅ 所有索引都有被使用")
            
    except Exception as e:
        logger.error(f"分析数据库性能失败: {str(e)}")


async def update_table_statistics():
    """更新表统计信息"""
    try:
        async with AsyncSessionLocal() as db:
            logger.info("📊 更新表统计信息...")
            
            # 获取所有用户表
            tables_query = text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename;
            """)
            
            result = await db.execute(tables_query)
            tables = result.fetchall()
            
            # 更新每个表的统计信息
            for table in tables:
                table_name = table.tablename
                logger.info(f"   更新表统计信息: {table_name}")
                
                analyze_query = text(f"ANALYZE {table_name};")
                await db.execute(analyze_query)
                await db.commit()
            
            logger.info("✅ 表统计信息更新完成")
            
    except Exception as e:
        logger.error(f"更新表统计信息失败: {str(e)}")


async def check_database_health():
    """检查数据库健康状况"""
    try:
        async with AsyncSessionLocal() as db:
            logger.info("🏥 检查数据库健康状况...")
            
            # 检查连接数
            connections_query = text("""
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity;
            """)
            
            result = await db.execute(connections_query)
            conn_stats = result.fetchone()
            
            logger.info(f"🔗 数据库连接统计:")
            logger.info(f"   总连接数: {conn_stats.total_connections}")
            logger.info(f"   活跃连接: {conn_stats.active_connections}")
            logger.info(f"   空闲连接: {conn_stats.idle_connections}")
            
            # 检查锁等待
            locks_query = text("""
                SELECT 
                    count(*) as waiting_locks
                FROM pg_stat_activity 
                WHERE wait_event_type = 'Lock';
            """)
            
            result = await db.execute(locks_query)
            lock_stats = result.fetchone()
            
            if lock_stats.waiting_locks > 0:
                logger.warning(f"⚠️  发现 {lock_stats.waiting_locks} 个等待锁的查询")
            else:
                logger.info("✅ 没有锁等待问题")
            
            # 检查数据库大小
            db_size_query = text("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as db_size;
            """)
            
            result = await db.execute(db_size_query)
            db_size = result.fetchone()
            
            logger.info(f"💾 数据库大小: {db_size.db_size}")
            
    except Exception as e:
        logger.error(f"检查数据库健康状况失败: {str(e)}")


async def optimize_database():
    """执行数据库优化"""
    logger.info("🚀 开始数据库优化...")
    
    try:
        # 1. 执行索引优化脚本
        migrations_dir = Path(__file__).parent.parent / "migrations"
        index_optimization_file = migrations_dir / "010_optimize_database_indexes.sql"
        
        if index_optimization_file.exists():
            logger.info("📈 执行索引优化...")
            async with AsyncSessionLocal() as db:
                await execute_sql_file(db, str(index_optimization_file))
        else:
            logger.warning("⚠️  索引优化文件不存在")
        
        # 2. 更新表统计信息
        await update_table_statistics()
        
        # 3. 分析数据库性能
        await analyze_database_performance()
        
        # 4. 检查数据库健康状况
        await check_database_health()
        
        logger.info("✅ 数据库优化完成")
        
    except Exception as e:
        logger.error(f"数据库优化失败: {str(e)}")
        raise


async def main():
    """主函数"""
    print("🔧 Lawsker数据库优化工具")
    print("=" * 50)
    
    try:
        await optimize_database()
        print("\n✅ 数据库优化成功完成")
        
    except Exception as e:
        print(f"\n❌ 数据库优化失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())