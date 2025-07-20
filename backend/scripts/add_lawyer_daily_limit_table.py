#!/usr/bin/env python3
"""
添加律师每日接单限制表
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def add_lawyer_daily_limit_table():
    """添加律师每日接单限制表"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🚀 开始创建lawyer_daily_limits表...")
            
            # 检查表是否已存在
            check_table_sql = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'lawyer_daily_limits'
            );
            """
            
            result = await session.execute(text(check_table_sql))
            exists = result.scalar()
            
            if exists:
                print("✅ lawyer_daily_limits表已存在，无需创建")
                return
            
            # 创建表
            create_table_sql = """
            CREATE TABLE lawyer_daily_limits (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                lawyer_id UUID NOT NULL REFERENCES users(id),
                date DATE NOT NULL,
                grabbed_count INTEGER DEFAULT 0 NOT NULL,
                max_daily_limit INTEGER DEFAULT 3 NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
            """
            
            await session.execute(text(create_table_sql))
            
            # 创建索引
            create_index_sql = """
            CREATE UNIQUE INDEX idx_lawyer_daily_limits_lawyer_date 
            ON lawyer_daily_limits(lawyer_id, date);
            """
            
            await session.execute(text(create_index_sql))
            
            # 创建更新时间触发器函数
            create_function_sql = """
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
            """
            
            await session.execute(text(create_function_sql))
            
            # 创建触发器
            create_trigger_sql = """
            CREATE TRIGGER update_lawyer_daily_limits_updated_at 
                BEFORE UPDATE ON lawyer_daily_limits 
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """
            
            await session.execute(text(create_trigger_sql))
            
            await session.commit()
            
            print("✅ 成功创建lawyer_daily_limits表及相关索引和触发器")
            
        except Exception as e:
            print(f"❌ 创建表失败: {e}")
            await session.rollback()
            raise


async def main():
    """主函数"""
    try:
        await add_lawyer_daily_limit_table()
        print("✅ 数据库迁移完成")
    except Exception as e:
        print(f"💥 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())