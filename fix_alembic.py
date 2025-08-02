#!/usr/bin/env python3
"""
修复alembic版本问题
"""

import asyncio
import sys
import os
from sqlalchemy import text

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app.core.database import engine

async def fix_alembic():
    """修复alembic版本"""
    try:
        async with engine.begin() as conn:
            # 删除所有版本记录
            await conn.execute(text("DELETE FROM alembic_version"))
            print("删除所有版本记录")
            
            # 插入正确的版本记录
            await conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('008_enhance_lawyer_qualification')"))
            print("插入正确的版本记录")
            
            # 验证修复结果
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.fetchone()
            print(f"当前alembic版本: {version[0] if version else 'None'}")
                
    except Exception as e:
        print(f"修复alembic版本失败: {e}")

if __name__ == "__main__":
    asyncio.run(fix_alembic()) 