#!/usr/bin/env python3
"""
简单的登录测试
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.core.security import verify_password

async def test_simple_login():
    """测试简单登录逻辑"""
    print("🔐 测试简单登录逻辑...")
    
    username = "lawyer1"
    password = "123456"
    
    try:
        async with AsyncSessionLocal() as session:
            # 1. 查询用户
            print(f"1. 查询用户: {username}")
            result = await session.execute(
                text("SELECT id, email, username, status, password_hash FROM users WHERE username = :username"),
                {"username": username}
            )
            user_row = result.fetchone()
            
            if not user_row:
                print("❌ 用户不存在")
                return
            
            print(f"✅ 找到用户: {user_row.username} ({user_row.email})")
            print(f"   状态: {user_row.status}")
            print(f"   密码哈希: {user_row.password_hash[:20]}...")
            
            # 2. 验证密码
            print(f"2. 验证密码: {password}")
            is_valid = verify_password(password, user_row.password_hash)
            print(f"   密码验证结果: {'✅ 正确' if is_valid else '❌ 错误'}")
            
            if not is_valid:
                print("❌ 密码验证失败")
                return
            
            # 3. 检查状态
            print(f"3. 检查用户状态")
            if user_row.status != "ACTIVE":
                print(f"❌ 用户状态不是ACTIVE: {user_row.status}")
                return
            
            print("✅ 用户状态正常")
            
            # 4. 获取角色
            print("4. 获取用户角色")
            role_result = await session.execute(
                text("""
                    SELECT r.name as role_name
                    FROM user_roles ur
                    JOIN roles r ON ur.role_id = r.id
                    WHERE ur.user_id = :user_id
                """),
                {"user_id": user_row.id}
            )
            role_row = role_result.fetchone()
            
            user_role = role_row.role_name if role_row else "user"
            print(f"✅ 用户角色: {user_role}")
            
            # 5. 模拟成功登录
            print("5. 模拟成功登录")
            print(f"✅ 登录成功!")
            print(f"   用户ID: {user_row.id}")
            print(f"   用户名: {user_row.username}")
            print(f"   邮箱: {user_row.email}")
            print(f"   角色: {user_role}")
            print(f"   状态: {user_row.status}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_login()) 