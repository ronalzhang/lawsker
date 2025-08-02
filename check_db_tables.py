#!/usr/bin/env python3
import asyncio
import sys
import os
from sqlalchemy import text

# 添加backend目录到Python路径
sys.path.append('/root/lawsker/backend')

async def check_tables():
    try:
        from app.core.database import engine
        
        # 检查access_logs表是否存在
        async with engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='access_logs'")
            )
            access_logs_exists = result.fetchone() is not None
            print(f"access_logs table exists: {access_logs_exists}")
            
            # 检查其他重要表
            tables_to_check = ['users', 'cases', 'tasks', 'alerts']
            for table in tables_to_check:
                result = await conn.execute(
                    text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                )
                exists = result.fetchone() is not None
                print(f"{table} table exists: {exists}")
            
    except Exception as e:
        print(f"Error checking tables: {e}")

if __name__ == "__main__":
    asyncio.run(check_tables()) 