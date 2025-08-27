#!/usr/bin/env python3
"""
Lawsker数据库设置验证脚本
验证所有表、索引、视图是否正确创建
"""

import asyncio
import asyncpg
import os
from datetime import datetime

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'lawsker_prod',
    'user': 'lawsker_user',
    'password': 'lawsker_2025_prod'
}

# 预期的表列表
EXPECTED_TABLES = [
    'users',
    'workspace_mappings',
    'lawyer_certification_requests',
    'demo_accounts',
    'demo_data_isolation',
    'lawyer_levels',
    'lawyer_level_details',
    'lawyer_point_transactions',
    'lawyer_case_declines',
    'lawyer_suspension_records',
    'lawyer_memberships',
    'lawyer_membership_history',
    'user_credits',
    'credit_purchase_records',
    'credit_usage_records',
    'batch_upload_tasks',
    'enterprise_customer_satisfaction',
    'customer_satisfaction_alerts',
    'customer_satisfaction_improvements',
    'customer_improvement_tasks',
    'lawyer_referral_programs',
    'lawyer_promotion_tracking',
    'lawyer_promotion_campaigns',
    'lawyer_registration_funnel',
    'lawyer_promotion_stats'
]

# 预期的视图列表
EXPECTED_VIEWS = [
    'customer_satisfaction_summary',
    'lawyer_promotion_overview',
    'lawyer_registration_growth'
]

# 预期的索引列表
EXPECTED_INDEXES = [
    'idx_users_workspace_id',
    'idx_users_account_type',
    'idx_users_email_verified',
    'idx_lawyer_cert_user_id',
    'idx_lawyer_cert_status',
    'idx_lawyer_level_details_lawyer_id',
    'idx_lawyer_point_trans_lawyer_id',
    'idx_user_credits_user_id',
    'idx_satisfaction_customer_id',
    'idx_promotion_tracking_created'
]

async def verify_database_setup():
    """验证数据库设置"""
    print("🔍 开始验证Lawsker数据库设置...")
    print(f"⏰ 验证时间: {datetime.now()}")
    print("=" * 60)
    
    try:
        # 连接数据库
        conn = await asyncpg.connect(**DB_CONFIG)
        print("✅ 数据库连接成功")
        
        # 验证表
        await verify_tables(conn)
        
        # 验证视图
        await verify_views(conn)
        
        # 验证索引
        await verify_indexes(conn)
        
        # 验证数据
        await verify_initial_data(conn)
        
        # 验证权限
        await verify_permissions(conn)
        
        await conn.close()
        
        print("=" * 60)
        print("🎉 数据库验证完成！所有检查都通过了。")
        print("🚀 系统已就绪，可以启动应用服务。")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库验证失败: {e}")
        return False

async def verify_tables(conn):
    """验证表是否存在"""
    print("\n📋 验证数据表...")
    
    # 获取所有表
    tables = await conn.fetch("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    """)
    
    existing_tables = [row['table_name'] for row in tables]
    
    missing_tables = []
    for table in EXPECTED_TABLES:
        if table in existing_tables:
            print(f"  ✅ {table}")
        else:
            print(f"  ❌ {table} (缺失)")
            missing_tables.append(table)
    
    if missing_tables:
        raise Exception(f"缺失表: {', '.join(missing_tables)}")
    
    print(f"✅ 所有 {len(EXPECTED_TABLES)} 张表都存在")

async def verify_views(conn):
    """验证视图是否存在"""
    print("\n👁️ 验证数据视图...")
    
    # 获取所有视图
    views = await conn.fetch("""
        SELECT table_name 
        FROM information_schema.views 
        WHERE table_schema = 'public'
    """)
    
    existing_views = [row['table_name'] for row in views]
    
    missing_views = []
    for view in EXPECTED_VIEWS:
        if view in existing_views:
            print(f"  ✅ {view}")
        else:
            print(f"  ❌ {view} (缺失)")
            missing_views.append(view)
    
    if missing_views:
        raise Exception(f"缺失视图: {', '.join(missing_views)}")
    
    print(f"✅ 所有 {len(EXPECTED_VIEWS)} 个视图都存在")

async def verify_indexes(conn):
    """验证索引是否存在"""
    print("\n🔍 验证数据库索引...")
    
    # 获取所有索引
    indexes = await conn.fetch("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE schemaname = 'public'
    """)
    
    existing_indexes = [row['indexname'] for row in indexes]
    
    missing_indexes = []
    for index in EXPECTED_INDEXES:
        if index in existing_indexes:
            print(f"  ✅ {index}")
        else:
            print(f"  ⚠️ {index} (可选)")
    
    print(f"✅ 索引验证完成")

async def verify_initial_data(conn):
    """验证初始数据"""
    print("\n📊 验证初始数据...")
    
    # 检查律师等级数据
    level_count = await conn.fetchval("SELECT COUNT(*) FROM lawyer_levels")
    if level_count >= 10:
        print(f"  ✅ 律师等级数据: {level_count} 条")
    else:
        print(f"  ❌ 律师等级数据不足: {level_count} 条")
        raise Exception("律师等级数据不完整")
    
    print("✅ 初始数据验证通过")

async def verify_permissions(conn):
    """验证用户权限"""
    print("\n🔐 验证用户权限...")
    
    try:
        # 测试基本查询权限
        await conn.fetchval("SELECT COUNT(*) FROM users")
        print("  ✅ 查询权限")
        
        # 测试插入权限（回滚）
        async with conn.transaction():
            await conn.execute("""
                INSERT INTO users (id, email, full_name) 
                VALUES (uuid_generate_v4(), 'test@test.com', 'Test User')
            """)
            print("  ✅ 插入权限")
            raise Exception("回滚测试")  # 故意回滚
            
    except Exception as e:
        if "回滚测试" in str(e):
            print("  ✅ 事务回滚正常")
        else:
            print(f"  ❌ 权限测试失败: {e}")
            raise
    
    print("✅ 用户权限验证通过")

if __name__ == "__main__":
    success = asyncio.run(verify_database_setup())
    exit(0 if success else 1)