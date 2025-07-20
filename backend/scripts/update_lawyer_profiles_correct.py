#!/usr/bin/env python3
"""
正确更新律师资料到profiles表
"""

import asyncio
import sys
import os
import random
import uuid
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import AsyncSessionLocal
from app.models.user import User


# 律师事务所
LAW_FIRMS = [
    "北京金杜律师事务所", "北京君合律师事务所", "北京大成律师事务所", 
    "上海锦天城律师事务所", "广东信达律师事务所", "北京环球律师事务所",
    "上海海华永泰律师事务所", "深圳市律师协会", "广州广和律师事务所",
    "北京市中伦律师事务所", "上海市方达律师事务所", "深圳国浩律师事务所"
]

# 律师姓名和性别
LAWYER_NAMES = [
    {"name": "张志强", "gender": "male"},
    {"name": "李美华", "gender": "female"}, 
    {"name": "王建国", "gender": "male"},
    {"name": "陈雪梅", "gender": "female"},
    {"name": "刘德华", "gender": "male"},
    {"name": "林小芳", "gender": "female"},
    {"name": "赵文博", "gender": "male"},
    {"name": "孙丽娜", "gender": "female"},
    {"name": "周建明", "gender": "male"},
    {"name": "吴雅琴", "gender": "female"}
]

# 专业领域
SPECIALTIES = [
    "民商事诉讼", "刑事辩护", "公司法务", "知识产权", "劳动争议",
    "房地产法", "金融法", "税务法", "国际贸易", "婚姻家庭"
]

# 教育背景
EDUCATION_BACKGROUNDS = [
    "北京大学法学院", "清华大学法学院", "中国人民大学法学院",
    "中国政法大学", "华东政法大学", "西南政法大学",
    "中南财经政法大学", "上海交通大学法学院", "复旦大学法学院"
]


async def update_lawyer_profiles_correct():
    """正确更新律师资料到profiles表"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🚀 开始更新律师资料到profiles表...")
            
            # 获取所有律师账户
            lawyers_query = select(User).where(User.username.like('lawyer%'))
            lawyers_result = await session.execute(lawyers_query)
            lawyers = lawyers_result.scalars().all()
            
            print(f"📋 找到 {len(lawyers)} 个律师账户")
            
            for i, lawyer in enumerate(lawyers):
                print(f"\n👨‍💼 处理律师: {lawyer.username}")
                
                # 选择律师信息
                lawyer_info = LAWYER_NAMES[i % len(LAWYER_NAMES)]
                law_firm = LAW_FIRMS[i % len(LAW_FIRMS)]
                specialty = random.choice(SPECIALTIES)
                education = random.choice(EDUCATION_BACKGROUNDS)
                
                # 生成其他信息
                years_experience = random.randint(3, 20)
                license_number = f"A{random.randint(100000, 999999)}{random.randint(2015, 2022)}"
                
                # 生成身份证号（模拟）
                birth_year = random.randint(1975, 1995)
                birth_month = random.randint(1, 12)
                birth_day = random.randint(1, 28)
                id_card = f"110101{birth_year}{birth_month:02d}{birth_day:02d}{random.randint(1000, 9999)}"
                
                # 检查是否已有profile记录
                check_profile_sql = text("SELECT user_id FROM profiles WHERE user_id = :user_id")
                profile_result = await session.execute(check_profile_sql, {'user_id': lawyer.id})
                existing_profile = profile_result.fetchone()
                
                # 准备资格信息JSON
                qualification_details = {
                    "law_firm": law_firm,
                    "license_number": license_number,
                    "specialties": specialty,
                    "years_experience": years_experience,
                    "education": education,
                    "certificate_number": license_number
                }
                
                bio = f"专业从事{specialty}法律事务{years_experience}年，具有丰富的实务经验。毕业于{education}，在{law_firm}执业。擅长处理各类{specialty}案件，为客户提供专业、高效的法律服务。"
                
                if existing_profile:
                    # 更新现有资料
                    update_profile_sql = text("""
                        UPDATE profiles SET
                            full_name = :full_name,
                            did = :id_card,
                            bio = :bio,
                            qualification_details = :qualification_details,
                            verification_status = 'VERIFIED',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = :user_id
                    """)
                    
                    await session.execute(update_profile_sql, {
                        'user_id': lawyer.id,
                        'full_name': lawyer_info['name'],
                        'id_card': id_card,
                        'bio': bio,
                        'qualification_details': json.dumps(qualification_details)
                    })
                    
                    print(f"✅ 更新现有资料: {lawyer_info['name']} - {law_firm}")
                else:
                    # 创建新的profile记录
                    insert_profile_sql = text("""
                        INSERT INTO profiles (
                            user_id, full_name, did, bio, qualification_details,
                            verification_status, created_at, updated_at
                        ) VALUES (
                            :user_id, :full_name, :id_card, :bio, :qualification_details,
                            'VERIFIED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                    """)
                    
                    await session.execute(insert_profile_sql, {
                        'user_id': lawyer.id,
                        'full_name': lawyer_info['name'],
                        'id_card': id_card,
                        'bio': bio,
                        'qualification_details': json.dumps(qualification_details)
                    })
                    
                    print(f"✅ 创建新资料: {lawyer_info['name']} - {law_firm}")
            
            await session.commit()
            print(f"\n🎉 成功更新了 {len(lawyers)} 个律师的profiles资料！")
            
        except Exception as e:
            print(f"❌ 更新失败: {e}")
            await session.rollback()
            raise


async def main():
    """主函数"""
    try:
        await update_lawyer_profiles_correct()
        print("✅ 律师资料更新完成")
    except Exception as e:
        print(f"💥 更新失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())