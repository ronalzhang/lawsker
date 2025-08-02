#!/usr/bin/env python3
"""
检查数据库表
"""

import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app.core.database import engine

async def check_tables():
    """检查数据库表"""
    try:
        async with engine.begin() as conn:
            result = await conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = [row[0] for row in result.fetchall()]
            print("数据库中的表:")
            for table in sorted(tables):
                print(f"  - {table}")
            
            # 检查用户表
            if 'users' in tables:
                result = await conn.execute("SELECT COUNT(*) FROM users")
                count = result.fetchone()[0]
                print(f"\n用户表中有 {count} 个用户")
                
                if count > 0:
                    result = await conn.execute("SELECT username, email, role FROM users LIMIT 5")
                    users = result.fetchall()
                    print("前5个用户:")
                    for user in users:
                        print(f"  - {user[0]} ({user[1]}) - {user[2]}")
            else:
                print("\n用户表不存在")
                
    except Exception as e:
        print(f"检查数据库失败: {e}")

if __name__ == "__main__":
    asyncio.run(check_tables()) 