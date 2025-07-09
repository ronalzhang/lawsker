#!/usr/bin/env python3
"""
为用户分配正确的角色
"""

import asyncio
import sys
import os
from uuid import uuid4

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, select
from app.core.database import AsyncSessionLocal

async def assign_user_roles():
    """为所有用户分配正确的角色"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🔧 开始为用户分配角色...")
            
            # 获取所有角色
            roles_result = await session.execute(text("SELECT id, name FROM roles"))
            roles = {name: role_id for role_id, name in roles_result.fetchall()}
            print(f"✅ 找到 {len(roles)} 个角色: {list(roles.keys())}")
            
            # 获取所有用户
            users_result = await session.execute(text("SELECT id, username FROM users"))
            users = users_result.fetchall()
            print(f"✅ 找到 {len(users)} 个用户")
            
            # 用户角色映射规则
            role_assignments = []
            
            for user_id, username in users:
                if username == 'admin':
                    role_name = 'admin'
                elif username.startswith('lawyer'):
                    role_name = 'lawyer' 
                elif username.startswith('sales'):
                    role_name = 'sales'
                elif username.startswith('institution'):
                    role_name = 'institution'
                else:
                    role_name = 'sales'  # 默认为销售角色
                
                role_assignments.append((user_id, roles[role_name], username, role_name))
            
            # 清空现有user_roles数据
            await session.execute(text("DELETE FROM user_roles"))
            print("✅ 清空现有角色分配")
            
            # 批量插入新的角色分配
            for user_id, role_id, username, role_name in role_assignments:
                await session.execute(text("""
                    INSERT INTO user_roles (user_id, role_id, assigned_at)
                    VALUES (:user_id, :role_id, NOW())
                """), {
                    "user_id": user_id,
                    "role_id": role_id
                })
                print(f"✅ 分配用户 {username} -> {role_name}")
            
            await session.commit()
            print(f"✅ 成功为 {len(role_assignments)} 个用户分配角色")
            
            # 验证结果
            verify_result = await session.execute(text("""
                SELECT u.username, r.name as role_name
                FROM users u
                JOIN user_roles ur ON u.id = ur.user_id
                JOIN roles r ON ur.role_id = r.id
                ORDER BY u.username
            """))
            
            print("\n📋 最终角色分配结果:")
            for username, role_name in verify_result.fetchall():
                print(f"  {username} -> {role_name}")
                
        except Exception as e:
            await session.rollback()
            print(f"❌ 角色分配失败: {e}")

if __name__ == "__main__":
    asyncio.run(assign_user_roles()) 