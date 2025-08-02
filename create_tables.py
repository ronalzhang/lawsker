#!/usr/bin/env python3
"""
手动创建数据库表
"""

import asyncio
import sys
import os
from sqlalchemy import text

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app.core.database import engine
from app.models.user import User
from app.models.tenant import Tenant
from app.models.case import Case
from app.core.database import Base

async def create_tables():
    """创建数据库表"""
    try:
        async with engine.begin() as conn:
            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
            print("✅ 数据库表创建完成")
                
    except Exception as e:
        print(f"❌ 创建数据库表失败: {e}")

if __name__ == "__main__":
    asyncio.run(create_tables()) 