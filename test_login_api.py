#!/usr/bin/env python3
"""
测试登录API功能
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.core.security import verify_password

async def test_login_query():
    """测试登录查询逻辑"""
    print("🔍 测试登录查询逻辑...")
    
    test_cases = [
        {"username": "lawyer1", "expected": "lawyer1@test.com"},
        {"username": "lawyer2", "expected": "lawyer2@test.com"},
        {"username": "user1", "expected": "user1@test.com"},
        {"username": "user2", "expected": "user2@test.com"},
        {"username": "lawyer1@test.com", "expected": "lawyer1@test.com"},
        {"username": "nonexistent", "expected": None}
    ]
    
    async with AsyncSessionLocal() as session:
        for test_case in test_cases:
            username = test_case["username"]
            expected = test_case["expected"]
            
            print(f"\n📝 测试用户名: {username}")
            
            try:
                # 执行登录查询
                result = await session.execute(
                    text("""
                        SELECT u.id, u.email, u.username, u.status, u.password_hash, r.name as role_name
                        FROM users u
                        LEFT JOIN user_roles ur ON u.id = ur.user_id
                        LEFT JOIN roles r ON ur.role_id = r.id
                        WHERE u.email = :login_id OR u.username = :login_id
                    """),
                    {"login_id": username}
                )
                user_row = result.fetchone()
                
                if user_row:
                    print(f"  ✅ 找到用户:")
                    print(f"    - ID: {user_row.id}")
                    print(f"    - Email: {user_row.email}")
                    print(f"    - Username: {user_row.username}")
                    print(f"    - Status: {user_row.status}")
                    print(f"    - Role: {user_row.role_name}")
                    print(f"    - Password Hash: {user_row.password_hash[:20]}...")
                    
                    # 测试密码验证
                    password = "123456"
                    is_valid = verify_password(password, user_row.password_hash)
                    print(f"    - 密码验证: {'✅ 正确' if is_valid else '❌ 错误'}")
                    
                    if expected and user_row.email != expected:
                        print(f"    ⚠️  期望邮箱: {expected}, 实际: {user_row.email}")
                else:
                    print(f"  ❌ 未找到用户")
                    if expected:
                        print(f"    ⚠️  期望找到: {expected}")
                        
            except Exception as e:
                print(f"  ❌ 查询错误: {e}")

async def test_direct_login():
    """测试直接登录逻辑"""
    print("\n🔐 测试直接登录逻辑...")
    
    test_users = ["lawyer1", "user1"]
    
    for username in test_users:
        print(f"\n📝 测试用户: {username}")
        
        try:
            async with AsyncSessionLocal() as session:
                # 执行登录查询
                result = await session.execute(
                    text("""
                        SELECT u.id, u.email, u.username, u.status, u.password_hash, r.name as role_name
                        FROM users u
                        LEFT JOIN user_roles ur ON u.id = ur.user_id
                        LEFT JOIN roles r ON ur.role_id = r.id
                        WHERE u.email = :login_id OR u.username = :login_id
                    """),
                    {"login_id": username}
                )
                user_row = result.fetchone()
                
                if not user_row:
                    print(f"  ❌ 用户不存在")
                    continue
                
                # 验证密码
                password = "123456"
                if not verify_password(password, user_row.password_hash):
                    print(f"  ❌ 密码验证失败")
                    continue
                
                # 检查用户状态
                if user_row.status != "ACTIVE":
                    print(f"  ❌ 用户状态不是ACTIVE: {user_row.status}")
                    continue
                
                # 获取用户角色
                user_role = user_row.role_name if user_row.role_name else "user"
                
                print(f"  ✅ 登录成功!")
                print(f"    - 用户ID: {user_row.id}")
                print(f"    - 用户名: {user_row.username}")
                print(f"    - 邮箱: {user_row.email}")
                print(f"    - 角色: {user_role}")
                print(f"    - 状态: {user_row.status}")
                
        except Exception as e:
            print(f"  ❌ 登录测试错误: {e}")

async def main():
    """主函数"""
    await test_login_query()
    await test_direct_login()

if __name__ == "__main__":
    asyncio.run(main()) 