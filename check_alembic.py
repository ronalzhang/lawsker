#!/usr/bin/env python3
"""
检查alembic版本
"""

import asyncio
import sys
import os
from sqlalchemy import text

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app.core.database import engine

async def check_alembic():
    """检查alembic版本"""
    try:
        async with engine.begin() as conn:
            # 检查alembic_version表是否存在（SQLite语法）
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'"))
            if result.fetchone():
                result = await conn.execute(text("SELECT version_num FROM alembic_version"))
                version = result.fetchone()
                print(f"当前alembic版本: {version[0] if version else 'None'}")
            else:
                print("alembic_version表不存在")
                
    except Exception as e:
        print(f"检查alembic版本失败: {e}")

if __name__ == "__main__":
    asyncio.run(check_alembic()) 