#!/usr/bin/env python3
"""
更新测试用户密码脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash

async def update_user_passwords():
    """更新测试用户密码"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🔧 开始更新测试用户密码...")
            
            # demo123的密码哈希
            new_password_hash = "$2b$12$Uh/67FlK.0pstsOQGuEO4u72n664o.dz5IIv2Qvssri5UZcos360a"
            
            # 要更新的用户名列表
            test_usernames = [
                "admin", "lawyer1", "lawyer2", "lawyer3", "lawyer4", "lawyer5",
                "sales1", "sales2", "sales3", "sales4", "sales5", "sales6", "sales7", "sales8",
                "institution1", "institution2", "institution3"
            ]
            
            updated_count = 0
            
            from sqlalchemy import select, update
            
            for username in test_usernames:
                # 先查找用户是否存在
                result = await session.execute(
                    select(User).where(User.username == username)
                )
                user = result.scalar_one_or_none()
                
                if user:
                    # 更新密码
                    user.password_hash = new_password_hash
                    print(f"✅ 更新用户 {username} 密码成功")
                    updated_count += 1
                else:
                    print(f"❌ 用户 {username} 不存在")
            
            await session.commit()
            print(f"\n🎉 总共更新了 {updated_count} 个用户的密码")
            print("密码已设置为: demo123")
            
        except Exception as e:
            print(f"❌ 更新密码失败: {e}")
            await session.rollback()
            raise

async def main():
    """主函数"""
    try:
        await update_user_passwords()
        print("✅ 密码更新完成")
    except Exception as e:
        print(f"💥 更新失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 