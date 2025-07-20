#!/usr/bin/env python3
"""
更新所有用户账户的详细信息
添加联系方式、电话等信息
"""

import asyncio
import sys
import os
import random
from datetime import datetime, date

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

# 销售人员信息
SALES_NAMES = [
    {"name": "王销售", "gender": "male", "dept": "华北区销售部"},
    {"name": "李销售", "gender": "female", "dept": "华东区销售部"},
    {"name": "张经理", "gender": "male", "dept": "华南区销售部"},
    {"name": "刘主任", "gender": "female", "dept": "西南区销售部"},
    {"name": "陈总监", "gender": "male", "dept": "华中区销售部"},
    {"name": "周销售", "gender": "female", "dept": "东北区销售部"},
    {"name": "吴经理", "gender": "male", "dept": "西北区销售部"},
    {"name": "赵销售", "gender": "female", "dept": "客户开发部"}
]

# 机构信息
INSTITUTION_INFO = [
    {"name": "北京银行", "type": "银行", "contact": "客户经理张先生"},
    {"name": "招商银行", "type": "银行", "contact": "业务部李女士"},
    {"name": "平安普惠", "type": "金融公司", "contact": "风控部王经理"},
    {"name": "宜信普惠", "type": "小贷公司", "contact": "法务部刘主任"},
    {"name": "捷信消费金融", "type": "消费金融", "contact": "催收部陈经理"},
    {"name": "中银消费金融", "type": "消费金融", "contact": "合规部周女士"},
    {"name": "马上消费金融", "type": "消费金融", "contact": "业务部吴先生"}
]

# 城市列表
CITIES = [
    "北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "武汉",
    "西安", "重庆", "天津", "苏州", "郑州", "长沙", "沈阳", "青岛"
]

async def update_all_users_info():
    """更新所有用户的详细信息"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🚀 开始更新所有用户账户信息...")
            
            # 获取所有用户
            users_query = text("SELECT id, username FROM users ORDER BY username")
            result = await session.execute(users_query)
            users = result.fetchall()
            
            print(f"✅ 找到 {len(users)} 个用户账户")
            
            for i, (user_id, username) in enumerate(users):
                print(f"处理用户: {username}")
                
                # 根据用户名类型确定信息
                if username.startswith('lawyer'):
                    # 律师用户 - 获取律师资料中的姓名
                    lawyer_query = text("SELECT law_firm FROM lawyer_profiles WHERE user_id = :user_id")
                    lawyer_result = await session.execute(lawyer_query, {'user_id': user_id})
                    lawyer_info = lawyer_result.fetchone()
                    continue  # 律师信息已在前面更新
                    
                elif username.startswith('sales'):
                    # 销售用户
                    sales_idx = (i - 6) % len(SALES_NAMES)  # 排除律师用户
                    sales_info = SALES_NAMES[sales_idx]
                    
                    full_name = sales_info['name']
                    phone = f"1{random.choice([3,5,7,8,9])}{random.randint(10000000, 99999999)}"
                    email = f"{username}@lawsker.com"
                    
                    # 创建销售人员资料
                    try:
                        create_sales_profile_sql = text("""
                            INSERT INTO sales_profiles (
                                user_id, full_name, department, phone, email, city, gender, created_at
                            ) VALUES (
                                :user_id, :full_name, :dept, :phone, :email, :city, :gender, CURRENT_TIMESTAMP
                            ) ON CONFLICT (user_id) DO UPDATE SET
                                full_name = EXCLUDED.full_name,
                                department = EXCLUDED.department,
                                phone = EXCLUDED.phone,
                                email = EXCLUDED.email,
                                updated_at = CURRENT_TIMESTAMP
                        """)
                        
                        await session.execute(create_sales_profile_sql, {
                            'user_id': user_id,
                            'full_name': full_name,
                            'dept': sales_info['dept'],
                            'phone': phone,
                            'email': email,
                            'city': random.choice(CITIES),
                            'gender': sales_info['gender']
                        })
                    except Exception as e:
                        print(f"创建销售资料时出错（可能表不存在）: {e}")
                    
                elif username.startswith('institution'):
                    # 机构用户
                    inst_idx = (i - 14) % len(INSTITUTION_INFO)  # 排除前面的用户
                    inst_info = INSTITUTION_INFO[inst_idx]
                    
                    phone = f"400{random.randint(1000000, 9999999)}"
                    email = f"{username}@{inst_info['name'].replace('银行', 'bank').replace('金融', 'finance')}.com"
                    
                    # 创建机构资料
                    try:
                        create_inst_profile_sql = text("""
                            INSERT INTO institution_profiles (
                                user_id, institution_name, institution_type, contact_person, 
                                phone, email, city, business_license, created_at
                            ) VALUES (
                                :user_id, :inst_name, :inst_type, :contact, :phone, :email, 
                                :city, :license, CURRENT_TIMESTAMP
                            ) ON CONFLICT (user_id) DO UPDATE SET
                                institution_name = EXCLUDED.institution_name,
                                contact_person = EXCLUDED.contact_person,
                                phone = EXCLUDED.phone,
                                email = EXCLUDED.email,
                                updated_at = CURRENT_TIMESTAMP
                        """)
                        
                        license_num = f"9144{random.randint(1000000000000000, 9999999999999999)}"
                        
                        await session.execute(create_inst_profile_sql, {
                            'user_id': user_id,
                            'inst_name': inst_info['name'],
                            'inst_type': inst_info['type'],
                            'contact': inst_info['contact'],
                            'phone': phone,
                            'email': email,
                            'city': random.choice(CITIES),
                            'license': license_num
                        })
                    except Exception as e:
                        print(f"创建机构资料时出错（可能表不存在）: {e}")
                    
                elif username == 'admin':
                    # 管理员用户
                    phone = "13800138000"
                    email = "admin@lawsker.com"
                    
                elif username == 'test':
                    # 测试用户
                    phone = f"1{random.choice([3,5,7,8,9])}{random.randint(10000000, 99999999)}"
                    email = f"{username}@test.com"
                
                else:
                    # 其他用户
                    phone = f"1{random.choice([3,5,7,8,9])}{random.randint(10000000, 99999999)}"
                    email = f"{username}@example.com"
                
                # 更新用户基本信息
                update_user_sql = text("""
                    UPDATE users SET 
                        phone_number = :phone,
                        email = :email,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :user_id
                """)
                
                await session.execute(update_user_sql, {
                    'user_id': user_id,
                    'phone': phone,
                    'email': email
                })
                
                print(f"✅ 更新用户: {username}")
            
            await session.commit()
            print(f"\n🎉 成功更新了 {len(users)} 个用户账户的联系信息！")
            
        except Exception as e:
            print(f"❌ 更新失败: {e}")
            await session.rollback()
            raise

async def create_profile_tables():
    """创建用户资料表（如果不存在）"""
    async with AsyncSessionLocal() as session:
        try:
            # 创建销售人员资料表
            create_sales_table_sql = text("""
                CREATE TABLE IF NOT EXISTS sales_profiles (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) UNIQUE,
                    full_name VARCHAR(100),
                    department VARCHAR(100),
                    phone VARCHAR(20),
                    email VARCHAR(100),
                    city VARCHAR(50),
                    gender VARCHAR(10),
                    employee_id VARCHAR(50),
                    hire_date DATE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建机构资料表
            create_inst_table_sql = text("""
                CREATE TABLE IF NOT EXISTS institution_profiles (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) UNIQUE,
                    institution_name VARCHAR(200),
                    institution_type VARCHAR(50),
                    contact_person VARCHAR(100),
                    phone VARCHAR(20),
                    email VARCHAR(100),
                    address TEXT,
                    city VARCHAR(50),
                    business_license VARCHAR(50),
                    cooperation_level VARCHAR(20) DEFAULT 'standard',
                    credit_rating VARCHAR(10),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute(create_sales_table_sql)
            await session.execute(create_inst_table_sql)
            await session.commit()
            print("✅ 用户资料表已创建")
            
        except Exception as e:
            print(f"创建表失败: {e}")
            await session.rollback()

async def main():
    """主函数"""
    try:
        await create_profile_tables()
        await update_all_users_info()
        print("✅ 所有用户账户信息更新完成")
    except Exception as e:
        print(f"💥 更新失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())