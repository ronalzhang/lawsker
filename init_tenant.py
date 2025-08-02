#!/usr/bin/env python3
"""
初始化租户脚本
"""

import asyncio
import sys
import os
sys.path.append('/root/lawsker/backend')

from app.core.database import get_db
from app.models.tenant import Tenant, TenantStatus, TenantMode

async def init_tenant():
    """初始化租户"""
    print("开始初始化租户...")
    
    async for db in get_db():
        try:
            # 检查租户是否已存在
            from sqlalchemy import text
            stmt = text("SELECT id FROM tenants WHERE id = 'ba5a72ab-0ba5-4de6-b6a3-989a4225e258'")
            result = await db.execute(stmt)
            existing_tenant = result.fetchone()
            
            if existing_tenant:
                print("✅ 租户已存在")
                return
            
            # 创建租户
            tenant = Tenant(
                id='ba5a72ab-0ba5-4de6-b6a3-989a4225e258',
                name='Lawsker主租户',
                tenant_code='lawsker_main',
                status=TenantStatus.ACTIVE
            )
            
            db.add(tenant)
            await db.commit()
            
            print("✅ 租户创建成功")
            break
        except Exception as e:
            print(f'❌ 初始化租户失败: {e}')
            break

if __name__ == '__main__':
    asyncio.run(init_tenant()) 