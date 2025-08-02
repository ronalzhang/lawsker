#!/usr/bin/env python3
import sys
import os
import bcrypt

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import AsyncSessionLocal
from sqlalchemy import text
import asyncio

async def test_password_verification():
    async with AsyncSessionLocal() as session:
        # 获取用户信息
        result = await session.execute(text("""
            SELECT username, email, password_hash 
            FROM users 
            WHERE username = 'lawyer1'
        """))
        user = result.fetchone()
        
        if user:
            print(f"用户: {user.username}")
            print(f"邮箱: {user.email}")
            print(f"密码哈希: {user.password_hash}")
            
            # 测试不同密码
            test_passwords = [
                "password123",
                "123456",
                "lawyer1",
                "test",
                "admin"
            ]
            
            for password in test_passwords:
                # 验证密码
                is_valid = bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))
                print(f"密码 '{password}': {'正确' if is_valid else '错误'}")
        else:
            print("未找到用户")

if __name__ == "__main__":
    asyncio.run(test_password_verification()) 