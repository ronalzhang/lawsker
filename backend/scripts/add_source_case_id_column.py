#!/usr/bin/env python3
"""
添加source_case_id字段到task_publish_records表
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def add_source_case_id_column():
    """添加source_case_id字段"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🚀 开始添加source_case_id字段...")
            
            # 检查字段是否已存在
            check_column_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'task_publish_records' 
            AND column_name = 'source_case_id';
            """
            
            result = await session.execute(text(check_column_sql))
            exists = result.fetchone()
            
            if exists:
                print("✅ source_case_id字段已存在，无需添加")
                return
            
            # 添加字段
            add_column_sql = """
            ALTER TABLE task_publish_records 
            ADD COLUMN source_case_id UUID REFERENCES cases(id);
            """
            
            await session.execute(text(add_column_sql))
            await session.commit()
            
            print("✅ 成功添加source_case_id字段")
            
            # 同时修改user_id字段允许为空
            alter_user_id_sql = """
            ALTER TABLE task_publish_records 
            ALTER COLUMN user_id DROP NOT NULL;
            """
            
            await session.execute(text(alter_user_id_sql))
            await session.commit()
            
            print("✅ 修改user_id字段允许为空")
            
        except Exception as e:
            print(f"❌ 添加字段失败: {e}")
            await session.rollback()
            raise


async def main():
    """主函数"""
    try:
        await add_source_case_id_column()
        print("✅ 数据库迁移完成")
    except Exception as e:
        print(f"💥 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())