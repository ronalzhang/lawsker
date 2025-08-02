#!/usr/bin/env python3
"""
使用SQL直接创建测试用户
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from sqlalchemy import text

async def create_users_with_sql():
    """使用SQL直接创建用户"""
    async with AsyncSessionLocal() as session:
        try:
            # 创建租户
            tenant_id = str(uuid.uuid4())
            current_time = datetime.now().isoformat()
            await session.execute(text(f"""
                INSERT INTO tenants (id, name, tenant_code, mode, status, domain, system_config, created_at, updated_at)
                VALUES ('{tenant_id}', '律客科技有限公司', 'lawsker', 'production', 'active', 'lawsker.com', 
                        '{{"theme": "default", "language": "zh-CN", "timezone": "Asia/Shanghai"}}',
                        '{current_time}', '{current_time}')
            """))
            
            # 创建测试用户
            test_users = [
                {
                    "username": "admin",
                    "email": "admin@lawsker.com",
                    "password": "demo123",
                    "role": "admin"
                },
                {
                    "username": "lawyer1",
                    "email": "lawyer1@lawsker.com",
                    "password": "demo123",
                    "role": "lawyer"
                },
                {
                    "username": "sales1",
                    "email": "sales1@lawsker.com",
                    "password": "demo123",
                    "role": "sales"
                }
            ]
            
            for user_data in test_users:
                user_id = str(uuid.uuid4())
                password_hash = get_password_hash(user_data["password"])
                
                # 检查用户是否已存在
                result = await session.execute(text(f"SELECT id FROM users WHERE email = '{user_data['email']}'"))
                if result.fetchone():
                    print(f"User {user_data['email']} already exists")
                    continue
                
                # 创建用户
                await session.execute(text(f"""
                    INSERT INTO users (id, tenant_id, username, email, password_hash, phone_number, 
                                     status, role, is_verified, is_premium, login_count, created_at, updated_at)
                    VALUES ('{user_id}', '{tenant_id}', '{user_data['username']}', '{user_data['email']}', 
                            '{password_hash}', '1380000{user_data['username'][-1]}{user_data['username'][-1]}000', 
                            'active', '{user_data['role']}', 1, 0, 0, '{current_time}', '{current_time}')
                """))
                print(f"Created user: {user_data['email']}")
            
            await session.commit()
            print("Test users created successfully!")
            
        except Exception as e:
            await session.rollback()
            print(f"Error creating users: {e}")

if __name__ == "__main__":
    asyncio.run(create_users_with_sql()) 