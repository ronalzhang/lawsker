#!/usr/bin/env python3
"""
测试数据库连接
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def test_db_connection():
    """测试数据库连接"""
    print("🔍 测试数据库连接...")
    
    try:
        async with AsyncSessionLocal() as session:
            # 测试基本连接
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✅ 数据库连接成功: {row.test}")
            
            # 测试用户查询
            result = await session.execute(text("SELECT COUNT(*) as count FROM users"))
            row = result.fetchone()
            print(f"✅ 用户表查询成功: {row.count} 个用户")
            
            # 测试特定用户查询
            result = await session.execute(
                text("SELECT username, email FROM users WHERE username = :username"),
                {"username": "lawyer1"}
            )
            row = result.fetchone()
            if row:
                print(f"✅ 找到用户: {row.username} ({row.email})")
            else:
                print("❌ 未找到用户 lawyer1")
                
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db_connection()) 