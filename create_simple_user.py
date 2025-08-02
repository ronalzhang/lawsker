#!/usr/bin/env python3
"""
创建简单的测试用户
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app.core.database import AsyncSessionLocal
from app.models.user import User, UserStatus, UserRole
from app.models.tenant import Tenant
from app.core.security import get_password_hash

async def create_simple_user():
    """创建简单的测试用户"""
    async with AsyncSessionLocal() as session:
        try:
            # 首先创建租户
            tenant = Tenant(
                id=uuid.uuid4(),
                name="律客科技有限公司",
                tenant_code="lawsker",
                domain="lawsker.com",
                system_config={
                    "theme": "default",
                    "language": "zh-CN",
                    "timezone": "Asia/Shanghai"
                }
            )
            session.add(tenant)
            await session.flush()
            
            # 创建测试用户
            test_users = [
                {
                    "username": "admin",
                    "email": "admin@lawsker.com",
                    "password": "demo123",
                    "role": UserRole.ADMIN
                },
                {
                    "username": "lawyer1",
                    "email": "lawyer1@lawsker.com",
                    "password": "demo123",
                    "role": UserRole.LAWYER
                },
                {
                    "username": "sales1",
                    "email": "sales1@lawsker.com",
                    "password": "demo123",
                    "role": UserRole.SALES
                }
            ]
            
            for user_data in test_users:
                # 检查用户是否已存在
                existing_user = await session.execute(
                    f"SELECT id FROM users WHERE email = '{user_data['email']}'"
                )
                if existing_user.fetchone():
                    print(f"User {user_data['email']} already exists")
                    continue
                
                # 创建用户
                user = User(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=get_password_hash(user_data["password"]),
                    phone_number=f"1380000{user_data['username'][-1]}000",
                    status=UserStatus.ACTIVE,
                    role=user_data["role"],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(user)
                print(f"Created user: {user_data['email']}")
            
            await session.commit()
            print("Test users created successfully!")
            
        except Exception as e:
            await session.rollback()
            print(f"Error creating users: {e}")

if __name__ == "__main__":
    asyncio.run(create_simple_user()) 