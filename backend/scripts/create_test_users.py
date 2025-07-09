#!/usr/bin/env python3
"""
创建测试用户脚本
"""

import asyncio
import sys
import os
from uuid import uuid4

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.user import User, UserStatus

async def create_test_users():
    """创建测试用户"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("👤 开始创建测试用户...")
            
            # demo123的密码哈希
            password_hash = "$2b$12$Uh/67FlK.0pstsOQGuEO4u72n664o.dz5IIv2Qvssri5UZcos360a"
            
            # 获取默认租户ID (先查找或创建)
            from sqlalchemy import text
            result = await session.execute(text("SELECT id FROM tenants LIMIT 1"))
            tenant_row = result.fetchone()
            
            if not tenant_row:
                # 创建默认租户
                from app.models.tenant import Tenant
                tenant = Tenant(
                    id=uuid4(),
                    name="律客科技有限公司",
                    tenant_code="lawsker",
                    domain="lawsker.com"
                )
                session.add(tenant)
                await session.flush()
                tenant_id = tenant.id
                print("✅ 创建默认租户")
            else:
                tenant_id = tenant_row[0]
                print("✅ 使用现有租户")
            
            # 创建测试用户
            test_users = [
                {"username": "admin", "email": "admin@lawsker.com", "role": "admin", "phone": "13800000001"},
                {"username": "lawyer1", "email": "lawyer1@lawsker.com", "role": "lawyer", "phone": "13800000002"},
                {"username": "lawyer2", "email": "lawyer2@lawsker.com", "role": "lawyer", "phone": "13800000003"},
                {"username": "lawyer3", "email": "lawyer3@lawsker.com", "role": "lawyer", "phone": "13800000004"},
                {"username": "lawyer4", "email": "lawyer4@lawsker.com", "role": "lawyer", "phone": "13800000005"},
                {"username": "lawyer5", "email": "lawyer5@lawsker.com", "role": "lawyer", "phone": "13800000006"},
                {"username": "sales1", "email": "sales1@lawsker.com", "role": "sales", "phone": "13810000001"},
                {"username": "sales2", "email": "sales2@lawsker.com", "role": "sales", "phone": "13810000002"},
                {"username": "sales3", "email": "sales3@lawsker.com", "role": "sales", "phone": "13810000003"},
                {"username": "sales4", "email": "sales4@lawsker.com", "role": "sales", "phone": "13810000004"},
                {"username": "sales5", "email": "sales5@lawsker.com", "role": "sales", "phone": "13810000005"},
                {"username": "sales6", "email": "sales6@lawsker.com", "role": "sales", "phone": "13810000006"},
                {"username": "sales7", "email": "sales7@lawsker.com", "role": "sales", "phone": "13810000007"},
                {"username": "sales8", "email": "sales8@lawsker.com", "role": "sales", "phone": "13810000008"},
                {"username": "institution1", "email": "institution1@lawsker.com", "role": "institution", "phone": "13820000001"},
                {"username": "institution2", "email": "institution2@lawsker.com", "role": "institution", "phone": "13820000002"},
                {"username": "institution3", "email": "institution3@lawsker.com", "role": "institution", "phone": "13820000003"},
            ]
            
            created_count = 0
            
            for user_data in test_users:
                # 检查用户是否已存在
                check_result = await session.execute(
                    text("SELECT id FROM users WHERE username = :username"),
                    {"username": user_data["username"]}
                )
                if check_result.fetchone():
                    print(f"⚠️  用户 {user_data['username']} 已存在，跳过")
                    continue
                
                # 创建新用户
                user = User(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=password_hash,
                    phone_number=user_data["phone"],
                    status=UserStatus.ACTIVE
                )
                session.add(user)
                print(f"✅ 创建用户 {user_data['username']} ({user_data['role']})")
                created_count += 1
            
            await session.commit()
            print(f"\n🎉 总共创建了 {created_count} 个新用户")
            print("所有用户密码: demo123")
            
        except Exception as e:
            print(f"❌ 创建用户失败: {e}")
            await session.rollback()
            raise

async def main():
    """主函数"""
    try:
        await create_test_users()
        print("✅ 测试用户创建完成")
    except Exception as e:
        print(f"💥 创建失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 