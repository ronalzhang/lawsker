#!/usr/bin/env python3
"""
初始化角色脚本
"""

import asyncio
import sys
import os
sys.path.append('/root/lawsker/backend')

from app.core.database import get_db
from app.services.user_service import UserService

async def init_roles():
    """初始化角色"""
    print("开始初始化角色...")
    
    async for db in get_db():
        try:
            user_service = UserService(db)
            
            # 创建律师角色
            lawyer_role = await user_service.create_role(
                name='lawyer',
                description='律师角色',
                permissions=['case:read', 'case:write', 'case:delete', 'user:read'],
                tenant_id='ba5a72ab-0ba5-4de6-b6a3-989a4225e258'
            )
            print(f'✅ 律师角色创建成功')
            
            # 创建用户角色
            user_role = await user_service.create_role(
                name='user',
                description='普通用户角色',
                permissions=['case:read', 'case:write'],
                tenant_id='ba5a72ab-0ba5-4de6-b6a3-989a4225e258'
            )
            print(f'✅ 用户角色创建成功')
            
            # 创建管理员角色
            admin_role = await user_service.create_role(
                name='admin',
                description='管理员角色',
                permissions=['*'],
                tenant_id='ba5a72ab-0ba5-4de6-b6a3-989a4225e258'
            )
            print(f'✅ 管理员角色创建成功')
            
            break
        except Exception as e:
            print(f'❌ 初始化角色失败: {e}')
            break

if __name__ == '__main__':
    asyncio.run(init_roles()) 