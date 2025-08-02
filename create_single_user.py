#!/usr/bin/env python3
"""
创建单个测试用户
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

async def create_single_user():
    """创建单个测试用户"""
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
            
            # 创建单个测试用户
            user_id = str(uuid.uuid4())
            password_hash = get_password_hash("demo123")
            
            await session.execute(text(f"""
                INSERT INTO users (id, tenant_id, username, email, password_hash, phone_number, 
                                 status, role, is_verified, is_premium, login_count, created_at, updated_at)
                VALUES ('{user_id}', '{tenant_id}', 'admin', 'admin@lawsker.com', 
                        '{password_hash}', '13800000001', 
                        'active', 'admin', 1, 0, 0, '{current_time}', '{current_time}')
            """))
            
            await session.commit()
            print("Test user created successfully!")
            print("Username: admin")
            print("Email: admin@lawsker.com")
            print("Password: demo123")
            
        except Exception as e:
            await session.rollback()
            print(f"Error creating user: {e}")

if __name__ == "__main__":
    asyncio.run(create_single_user()) 