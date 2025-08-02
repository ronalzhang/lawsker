#!/usr/bin/env python3
"""
重置alembic状态
"""

import asyncio
import sys
import os
from sqlalchemy import text

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app.core.database import engine

async def reset_alembic():
    """重置alembic状态"""
    try:
        async with engine.begin() as conn:
            # 删除alembic_version表（如果存在）
            await conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
            print("删除alembic_version表")
            
            # 重新创建alembic_version表
            await conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL, PRIMARY KEY (version_num))"))
            print("重新创建alembic_version表")
            
            # 插入基础版本
            await conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('940b959512f7')"))
            print("插入基础版本")
                
    except Exception as e:
        print(f"重置alembic状态失败: {e}")

if __name__ == "__main__":
    asyncio.run(reset_alembic()) 