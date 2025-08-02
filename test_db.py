#!/usr/bin/env python3
"""
测试数据库连接
"""

import asyncio
import sys
import os
sys.path.append('/root/lawsker/backend')

from app.core.database import get_db
from app.core.config import settings

async def test_db():
    print(f"数据库URL: {settings.DATABASE_URL}")
    try:
        async for db in get_db():
            print("✅ 数据库连接正常")
            break
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")

if __name__ == '__main__':
    asyncio.run(test_db()) 