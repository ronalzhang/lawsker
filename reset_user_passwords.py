#!/usr/bin/env python3
import sys
import os
import bcrypt
import asyncio

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def reset_user_passwords():
    """重置用户密码为123456"""
    async with AsyncSessionLocal() as session:
        # 生成新密码哈希
        new_password = "123456"
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        # 更新所有用户的密码
        result = await session.execute(text("""
            UPDATE users 
            SET password_hash = :password_hash 
            WHERE username IN ('lawyer1', 'lawyer2', 'user1', 'user2')
        """), {"password_hash": password_hash.decode('utf-8')})
        
        await session.commit()
        
        print(f"✅ 已重置所有用户密码为: {new_password}")
        
        # 验证更新
        result = await session.execute(text("""
            SELECT username, email, password_hash 
            FROM users 
            WHERE username IN ('lawyer1', 'lawyer2', 'user1', 'user2')
        """))
        
        users = result.fetchall()
        print("\n📊 用户密码已更新:")
        for user in users:
            print(f"  {user.username}: {user.email}")

if __name__ == "__main__":
    asyncio.run(reset_user_passwords()) 