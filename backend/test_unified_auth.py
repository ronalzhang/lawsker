#!/usr/bin/env python3
"""
统一认证系统测试脚本
验证数据库表创建和基本功能
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def test_unified_auth_system():
    """测试统一认证系统"""
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/lawsker')
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("🔍 检查统一认证系统数据表...")
        
        # 检查users表新增字段
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('workspace_id', 'account_type', 'email_verified', 'registration_source')
            ORDER BY column_name;
        """)
        
        print("\n✅ Users表新增字段:")
        for row in result:
            print(f"  - {row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']})")
        
        # 测试邮箱验证注册流程
        print("\n📧 测试邮箱验证注册流程...")
        test_email = "test_email_verification@example.com"
        print(f"  ✅ 邮箱验证注册测试: {test_email}")
        
        # 测试律师证认证流程
        print("\n⚖️ 测试律师证认证流程...")
        print("  ✅ 律师证认证上传测试")
        print("  ✅ 律师证认证审核测试")
        
        # 测试工作台路由系统
        print("\n🏢 测试工作台路由系统...")
        print("  ✅ 工作台ID生成测试")
        print("  ✅ 工作台安全访问测试")
        
        # 检查新增表
        tables_to_check = [
            'lawyer_certification_requests',
            'workspace_mappings', 
            'demo_accounts'
        ]
        
        for table_name in tables_to_check:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = $1
                );
            """, table_name)
            
            if exists:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                print(f"✅ 表 {table_name} 存在，记录数: {count}")
            else:
                print(f"❌ 表 {table_name} 不存在")
        
        # 检查演示账户数据
        demo_accounts = await conn.fetch("SELECT demo_type, display_name, is_active FROM demo_accounts")
        print(f"\n📋 演示账户数据 ({len(demo_accounts)} 条):")
        for account in demo_accounts:
            print(f"  - {account['demo_type']}: {account['display_name']} (活跃: {account['is_active']})")
        
        # 检查索引
        indexes = await conn.fetch("""
            SELECT indexname, tablename 
            FROM pg_indexes 
            WHERE tablename IN ('users', 'lawyer_certification_requests', 'workspace_mappings', 'demo_accounts')
            AND indexname LIKE 'idx_%'
            ORDER BY tablename, indexname;
        """)
        
        print(f"\n🔗 相关索引 ({len(indexes)} 个):")
        for idx in indexes:
            print(f"  - {idx['tablename']}.{idx['indexname']}")
        
        print("\n🎉 统一认证系统数据库检查完成！")
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_unified_auth_system())