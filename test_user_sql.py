#!/usr/bin/env python3
"""
使用SQL直接查询用户
"""

import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app.core.database import AsyncSessionLocal
from app.core.security import verify_password
from sqlalchemy import text

async def test_user_sql():
    """使用SQL查询用户"""
    async with AsyncSessionLocal() as session:
        try:
            # 查询所有用户
            result = await session.execute(text("SELECT id, email, username, role, status, password_hash FROM users"))
            users = result.fetchall()
            
            print(f"Total users: {len(users)}")
            
            for user in users:
                print(f"User: {user.email}, Username: {user.username}, Role: {user.role}, Status: {user.status}")
                print(f"Password hash: {user.password_hash[:20]}...")
                
                # 测试密码验证
                is_valid = verify_password("demo123", user.password_hash)
                print(f"Password verification: {is_valid}")
                print("---")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_user_sql()) 