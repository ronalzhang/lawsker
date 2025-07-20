#!/usr/bin/env python3
"""
更新律师资料显示脚本
确保律师资料在前端正确显示
"""

import asyncio
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import AsyncSessionLocal
from app.models.user import User


async def update_lawyer_profiles_display():
    """更新律师资料显示"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🚀 开始更新律师资料显示...")
            
            # 查询所有律师用户
            lawyers_query = select(User).where(User.username.like('lawyer%'))
            lawyers_result = await session.execute(lawyers_query)
            lawyers = lawyers_result.scalars().all()
            
            print(f"📋 找到 {len(lawyers)} 个律师账户")
            
            for lawyer in lawyers:
                print(f"\n👨‍💼 律师: {lawyer.username}")
                print(f"   - 用户名: {lawyer.username}")
                print(f"   - 邮箱: {lawyer.email or '未设置'}")
                print(f"   - 电话: {lawyer.phone_number or '未设置'}")
                print(f"   - 状态: {lawyer.status or '未设置'}")
                print(f"   - 上次登录: {lawyer.last_login or '从未登录'}")
                
                # 检查律师资料表(profiles表)
                check_profile_sql = """
                SELECT did, full_name, bio, qualification_details, verification_status
                FROM profiles 
                WHERE user_id = :user_id
                """
                
                profile_result = await session.execute(
                    text(check_profile_sql), 
                    {"user_id": lawyer.id}
                )
                profile = profile_result.fetchone()
                
                if profile:
                    print(f"   - 真实姓名: {profile.full_name or '未设置'}")
                    print(f"   - 个人简介: {profile.bio or '未设置'}")
                    print(f"   - 身份证号: {profile.did or '未设置'}")
                    print(f"   - 认证状态: {profile.verification_status or '未认证'}")
                    
                    if profile.qualification_details:
                        qual_data = profile.qualification_details
                        print(f"   - 律所: {qual_data.get('law_firm', '未设置')}")
                        print(f"   - 专业领域: {qual_data.get('specialties', '未设置')}")
                        print(f"   - 教育背景: {qual_data.get('education', '未设置')}")
                        print(f"   - 执业年限: {qual_data.get('experience_years', '未设置')}年")
                        print(f"   - 执业证号: {qual_data.get('certificate_number', '未设置')}")
                    else:
                        print("   - ⚠️  执业资格信息未完善")
                else:
                    print("   - ⚠️  缺少律师资料表记录")
            
            # 统计信息
            print(f"\n📊 统计信息:")
            
            # 律师总数
            total_lawyers = len(lawyers)
            print(f"   - 律师总数: {total_lawyers}")
            
            # 有完整资料的律师数
            complete_profiles = await session.execute(text("""
                SELECT COUNT(*) FROM profiles p
                JOIN users u ON p.user_id = u.id
                WHERE u.username LIKE 'lawyer%'
                AND p.qualification_details IS NOT NULL
                AND p.qualification_details->>'law_firm' IS NOT NULL
                AND p.qualification_details->>'specialties' IS NOT NULL
            """))
            complete_count = complete_profiles.scalar()
            print(f"   - 完整资料: {complete_count}")
            
            # 活跃律师数
            active_lawyers = sum(1 for l in lawyers if l.status == 'active')
            print(f"   - 活跃律师: {active_lawyers}")
            
            # 检查案件分配情况
            assigned_cases = await session.execute(text("""
                SELECT COUNT(*) FROM cases c
                JOIN users u ON c.assigned_to_user_id = u.id
                WHERE u.username LIKE 'lawyer%'
            """))
            assigned_count = assigned_cases.scalar()
            print(f"   - 已分配案件: {assigned_count}")
            
        except Exception as e:
            print(f"❌ 更新失败: {e}")
            raise


async def main():
    """主函数"""
    try:
        await update_lawyer_profiles_display()
        print("\n✅ 律师资料检查完成")
    except Exception as e:
        print(f"💥 检查失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())