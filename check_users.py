#!/usr/bin/env python3
"""
检查数据库中的用户数据
"""

import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select

async def check_users():
    """检查用户数据"""
    async with AsyncSessionLocal() as session:
        try:
            # 查询所有用户
            result = await session.execute(select(User))
            users = result.scalars().all()
            
            print(f"Total users: {len(users)}")
            
            if users:
                print("\nFirst 5 users:")
                for i, user in enumerate(users[:5]):
                    print(f"{i+1}. Email: {user.email}, Status: {user.status}, Username: {user.username}")
            else:
                print("No users found in database")
                
        except Exception as e:
            print(f"Error checking users: {e}")

if __name__ == "__main__":
    asyncio.run(check_users()) 