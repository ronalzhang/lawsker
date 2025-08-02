#!/usr/bin/env python3
"""
创建测试账号脚本
"""

import asyncio
import sys
import os
sys.path.append('/root/lawsker/backend')

from app.core.database import get_db
from app.services.user_service import UserService

async def create_test_users():
    """创建测试账号"""
    print("开始创建测试账号...")
    
    async for db in get_db():
        try:
            user_service = UserService(db)
            
            # 创建律师账号
            lawyer1 = await user_service.create_user(
                email='lawyer1@test.com',
                password='123456',
                role_name='lawyer',
                tenant_id='ba5a72ab-0ba5-4de6-b6a3-989a4225e258',
                full_name='张律师',
                phone_number='13800138001'
            )
            print(f'✅ 律师账号1创建成功: lawyer1@test.com / 123456')
            
            lawyer2 = await user_service.create_user(
                email='lawyer2@test.com',
                password='123456',
                role_name='lawyer',
                tenant_id='ba5a72ab-0ba5-4de6-b6a3-989a4225e258',
                full_name='李律师',
                phone_number='13800138002'
            )
            print(f'✅ 律师账号2创建成功: lawyer2@test.com / 123456')
            
            # 创建用户账号
            user1 = await user_service.create_user(
                email='user1@test.com',
                password='123456',
                role_name='user',
                tenant_id='ba5a72ab-0ba5-4de6-b6a3-989a4225e258',
                full_name='王用户',
                phone_number='13800138003'
            )
            print(f'✅ 用户账号1创建成功: user1@test.com / 123456')
            
            user2 = await user_service.create_user(
                email='user2@test.com',
                password='123456',
                role_name='user',
                tenant_id='ba5a72ab-0ba5-4de6-b6a3-989a4225e258',
                full_name='赵用户',
                phone_number='13800138004'
            )
            print(f'✅ 用户账号2创建成功: user2@test.com / 123456')
            
            print("\n🎉 所有测试账号创建完成！")
            print("\n📋 测试账号列表：")
            print("律师账号：")
            print("  - lawyer1@test.com / 123456")
            print("  - lawyer2@test.com / 123456")
            print("用户账号：")
            print("  - user1@test.com / 123456")
            print("  - user2@test.com / 123456")
            print("管理员账号：")
            print("  - 密码: 123abc74531")
            
        except Exception as e:
            print(f"❌ 创建测试账号失败: {e}")
        finally:
            break

if __name__ == '__main__':
    asyncio.run(create_test_users()) 