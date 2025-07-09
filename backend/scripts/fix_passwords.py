#!/usr/bin/env python3
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash

async def fix_all_passwords():
    """修复所有用户的密码哈希"""
    
    # 生成正确的demo123密码哈希
    correct_hash = get_password_hash('demo123')
    print(f"正确的密码哈希: {correct_hash[:50]}...")
    
    async with AsyncSessionLocal() as session:
        try:
            # 更新所有用户的密码哈希
            result = await session.execute(
                text("UPDATE users SET password_hash = :hash"), 
                {"hash": correct_hash}
            )
            await session.commit()
            print(f"✅ 成功更新了 {result.rowcount} 个用户的密码")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ 更新失败: {e}")

if __name__ == "__main__":
    print("🔧 开始修复用户密码...")
    asyncio.run(fix_all_passwords())
    print("✅ 密码修复完成！") 