#!/usr/bin/env python3
"""
更新律师账户详细信息
添加真实的律所、姓名、性别等信息
"""

import asyncio
import sys
import os
import random
from datetime import datetime, date
from uuid import UUID

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

# 真实的律师事务所名单
LAW_FIRMS = [
    "北京金杜律师事务所",
    "北京君合律师事务所", 
    "北京大成律师事务所",
    "上海锦天城律师事务所",
    "广东信达律师事务所",
    "浙江天册律师事务所",
    "江苏世纪同仁律师事务所",
    "山东德衡律师事务所",
    "河南豫龙律师事务所",
    "湖北山河律师事务所",
    "四川明炬律师事务所",
    "陕西恒达律师事务所",
    "福建闽君律师事务所",
    "安徽徽商律师事务所",
    "江西求正律师事务所"
]

# 律师姓名（常见姓氏+名字）
LAWYER_NAMES = [
    {"name": "张志强", "gender": "male"},
    {"name": "李美华", "gender": "female"},
    {"name": "王建国", "gender": "male"},
    {"name": "陈雪梅", "gender": "female"},
    {"name": "刘德华", "gender": "male"},
    {"name": "赵丽君", "gender": "female"},
    {"name": "孙明亮", "gender": "male"},
    {"name": "周婷婷", "gender": "female"},
    {"name": "吴海峰", "gender": "male"},
    {"name": "郑小芳", "gender": "female"},
    {"name": "马俊杰", "gender": "male"},
    {"name": "林静怡", "gender": "female"},
    {"name": "黄文博", "gender": "male"},
    {"name": "朱晓红", "gender": "female"},
    {"name": "胡正义", "gender": "male"},
    {"name": "许娟娟", "gender": "female"},
    {"name": "何志华", "gender": "male"},
    {"name": "邓小慧", "gender": "female"},
    {"name": "罗家伟", "gender": "male"},
    {"name": "高雅琴", "gender": "female"}
]

# 专业领域
SPECIALTIES = [
    "债务催收", "合同纠纷", "公司法务", "劳动争议", "知识产权",
    "房地产纠纷", "刑事辩护", "婚姻家庭", "交通事故", "医疗纠纷",
    "建筑工程", "金融法律", "税务筹划", "行政诉讼", "仲裁调解"
]

# 学历背景
EDUCATION_BACKGROUNDS = [
    "中国政法大学法学学士",
    "北京大学法学硕士",
    "清华大学法学博士",
    "复旦大学法学学士",
    "上海交通大学法学硕士",
    "浙江大学法学学士",
    "南京大学法学硕士",
    "华中科技大学法学学士",
    "西南政法大学法学硕士",
    "华东政法大学法学博士"
]

async def update_lawyer_profiles():
    """更新律师账户详细信息"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🚀 开始更新律师账户信息...")
            
            # 获取所有律师用户（根据用户名识别）
            lawyers_query = text("SELECT id, username FROM users WHERE username LIKE 'lawyer%'")
            result = await session.execute(lawyers_query)
            lawyers = result.fetchall()
            
            print(f"✅ 找到 {len(lawyers)} 个律师账户")
            
            for i, (lawyer_id, username) in enumerate(lawyers):
                # 选择律师信息
                lawyer_info = LAWYER_NAMES[i % len(LAWYER_NAMES)]
                law_firm = LAW_FIRMS[i % len(LAW_FIRMS)]
                specialty = random.choice(SPECIALTIES)
                education = random.choice(EDUCATION_BACKGROUNDS)
                
                # 生成其他信息
                years_experience = random.randint(3, 20)
                license_number = f"A{random.randint(100000, 999999)}{random.randint(2015, 2022)}"
                phone = f"1{random.choice([3,5,7,8,9])}{random.randint(10000000, 99999999)}"
                
                # 生成身份证号（模拟）
                birth_year = random.randint(1975, 1995)
                birth_month = random.randint(1, 12)
                birth_day = random.randint(1, 28)
                id_card = f"110101{birth_year}{birth_month:02d}{birth_day:02d}{random.randint(1000, 9999)}"
                
                # 先检查并添加缺少的字段
                try:
                    add_column_sql = text("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(100)")
                    await session.execute(add_column_sql)
                except:
                    pass
                
                # 更新用户基本信息
                update_user_sql = text("""
                    UPDATE users SET 
                        phone_number = :phone,
                        email = :email,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :user_id
                """)
                
                await session.execute(update_user_sql, {
                    'user_id': lawyer_id,
                    'phone': phone,
                    'email': f"{username}@lawfirm.com"
                })
                
                # 检查是否已有律师资料
                check_profile_sql = text("SELECT id FROM lawyer_profiles WHERE user_id = :user_id")
                profile_result = await session.execute(check_profile_sql, {'user_id': lawyer_id})
                existing_profile = profile_result.fetchone()
                
                if existing_profile:
                    # 更新现有资料
                    update_profile_sql = text("""
                        UPDATE lawyer_profiles SET
                            law_firm = :law_firm,
                            license_number = :license_number,
                            specialty = :specialty,
                            years_experience = :years_experience,
                            education_background = :education,
                            gender = :gender,
                            id_card_number = :id_card,
                            bio = :bio,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = :user_id
                    """)
                else:
                    # 创建新的律师资料
                    update_profile_sql = text("""
                        INSERT INTO lawyer_profiles (
                            user_id, law_firm, license_number, specialty, years_experience,
                            education_background, gender, id_card_number, bio, 
                            verification_status, created_at, updated_at
                        ) VALUES (
                            :user_id, :law_firm, :license_number, :specialty, :years_experience,
                            :education, :gender, :id_card, :bio,
                            'verified', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                    """)
                
                bio = f"专业从事{specialty}法律事务{years_experience}年，具有丰富的实务经验。毕业于{education}，在{law_firm}执业。擅长处理各类{specialty}案件，为客户提供专业、高效的法律服务。"
                
                await session.execute(update_profile_sql, {
                    'user_id': lawyer_id,
                    'law_firm': law_firm,
                    'license_number': license_number,
                    'specialty': specialty,
                    'years_experience': years_experience,
                    'education': education,
                    'gender': lawyer_info['gender'],
                    'id_card': id_card,
                    'bio': bio
                })
                
                print(f"✅ 更新律师: {lawyer_info['name']} - {law_firm}")
            
            await session.commit()
            print(f"\n🎉 成功更新了 {len(lawyers)} 个律师账户的详细信息！")
            
        except Exception as e:
            print(f"❌ 更新失败: {e}")
            await session.rollback()
            raise

async def create_lawyer_profiles_table():
    """创建律师资料表（如果不存在）"""
    async with AsyncSessionLocal() as session:
        try:
            create_table_sql = text("""
                CREATE TABLE IF NOT EXISTS lawyer_profiles (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) UNIQUE,
                    law_firm VARCHAR(200),
                    license_number VARCHAR(50),
                    specialty VARCHAR(100),
                    years_experience INTEGER,
                    education_background TEXT,
                    gender VARCHAR(10),
                    id_card_number VARCHAR(18),
                    bio TEXT,
                    verification_status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute(create_table_sql)
            await session.commit()
            print("✅ 律师资料表已创建")
            
        except Exception as e:
            print(f"创建表失败: {e}")
            await session.rollback()

async def main():
    """主函数"""
    try:
        await create_lawyer_profiles_table()
        await update_lawyer_profiles()
        print("✅ 律师账户信息更新完成")
    except Exception as e:
        print(f"💥 更新失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())