#!/usr/bin/env python3
"""
创建任务测试数据脚本
专门为任务发布-抢单功能创建测试数据
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
import random

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User, Role, UserRole
from app.models.statistics import TaskPublishRecord


async def create_task_test_data():
    """创建任务测试数据"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🚀 开始创建任务测试数据...")
            
            # 1. 查找现有用户
            print("👥 查找现有用户...")
            # 查找所有用户
            users_query = select(User).limit(20)
            users_result = await session.execute(users_query)
            all_users = users_result.scalars().all()
            
            if not all_users:
                print("❌ 没有找到用户，请先运行用户创建脚本")
                return
            
            # 简单地将用户分为普通用户和律师（基于用户名）
            users = [u for u in all_users if not u.username.startswith('lawyer')]
            lawyers = [u for u in all_users if u.username.startswith('lawyer')]
            
            # 如果没有明确区分，就随机分配
            if not lawyers:
                lawyers = all_users[:len(all_users)//3]  # 1/3作为律师
                users = all_users[len(all_users)//3:]    # 2/3作为用户
            
            if not users:
                print("❌ 没有找到用户，请先运行用户创建脚本")
                return
            
            print(f"✅ 找到 {len(users)} 个用户, {len(lawyers)} 个律师")
            
            # 2. 创建可抢单的任务（状态为published）
            print("📝 创建可抢单任务...")
            available_tasks = []
            
            task_templates = [
                {
                    "type": "lawyer_letter",
                    "title": "债权催收律师函",
                    "description": "需要向欠款人发送正式的债权催收律师函，督促其履行还款义务。",
                    "amount_range": (300, 800)
                },
                {
                    "type": "debt_collection", 
                    "title": "企业欠款催收",
                    "description": "企业间的货款纠纷，需要专业律师进行催收处理。",
                    "amount_range": (2000, 8000)
                },
                {
                    "type": "contract_review",
                    "title": "商务合同审查",
                    "description": "需要律师审查商务合作合同的条款和风险点。",
                    "amount_range": (500, 2000)
                },
                {
                    "type": "legal_consultation",
                    "title": "法律咨询服务",
                    "description": "关于公司经营中的法律问题咨询和建议。",
                    "amount_range": (200, 1000)
                },
                {
                    "type": "lawyer_letter",
                    "title": "违约责任追究函",
                    "description": "合同违约后需要发送法律函件追究违约责任。",
                    "amount_range": (400, 1200)
                },
                {
                    "type": "debt_collection",
                    "title": "个人借贷纠纷处理", 
                    "description": "个人间的借贷纠纷，需要通过法律途径解决。",
                    "amount_range": (1000, 5000)
                }
            ]
            
            # 创建15个可抢单任务
            for i in range(15):
                template = random.choice(task_templates)
                user = random.choice(users)
                
                task = TaskPublishRecord(
                    id=uuid4(),
                    user_id=user.id,
                    task_type=template["type"],
                    title=f"{template['title']} #{i+1:03d}",
                    description=f"{template['description']} 案件编号: CASE-2024-{i+1:04d}",
                    target_info={
                        "target_name": f"目标对象{i+1}",
                        "contact_phone": f"1{random.randint(300000000, 999999999)}",
                        "contact_address": f"上海市浦东新区{random.choice(['张江', '陆家嘴', '世纪大道'])}{random.randint(100, 999)}号",
                        "case_details": f"案件{i+1}的具体情况和要求"
                    },
                    amount=Decimal(random.randint(*template["amount_range"])),
                    urgency=random.choice(["normal", "normal", "urgent", "low"]),  # 大多数是正常优先级
                    status="published",  # 重要：设置为可抢单状态
                    assigned_to=None,  # 未分配律师
                    created_at=datetime.now() - timedelta(
                        hours=random.randint(1, 72),  # 1-72小时前发布
                        minutes=random.randint(0, 59)
                    )
                )
                session.add(task)
                available_tasks.append(task)
            
            # 3. 创建已被抢单的任务（各种状态）
            print("🎯 创建已抢单任务...")
            grabbed_tasks = []
            
            status_distribution = [
                ("grabbed", 5),      # 刚抢到，还未开始
                ("in_progress", 8),  # 进行中
                ("completed", 6),    # 已完成
                ("confirmed", 4)     # 客户已确认
            ]
            
            for status, count in status_distribution:
                for i in range(count):
                    template = random.choice(task_templates)
                    user = random.choice(users)
                    lawyer = random.choice(lawyers) if lawyers else None
                    
                    # 计算时间
                    created_time = datetime.now() - timedelta(
                        days=random.randint(1, 30),
                        hours=random.randint(0, 23)
                    )
                    
                    updated_time = created_time + timedelta(hours=random.randint(1, 48))
                    completed_time = None
                    
                    if status in ["completed", "confirmed"]:
                        completed_time = updated_time + timedelta(
                            days=random.randint(1, 10),
                            hours=random.randint(0, 23)
                        )
                    
                    task = TaskPublishRecord(
                        id=uuid4(),
                        user_id=user.id,
                        task_type=template["type"],
                        title=f"{template['title']} #{len(available_tasks)+i+1:03d}",
                        description=f"{template['description']} 案件编号: CASE-2024-{len(available_tasks)+i+1:04d}",
                        target_info={
                            "target_name": f"目标对象{len(available_tasks)+i+1}",
                            "contact_phone": f"1{random.randint(300000000, 999999999)}",
                            "contact_address": f"北京市朝阳区{random.choice(['CBD', '三里屯', '望京'])}{random.randint(100, 999)}号",
                            "case_details": f"案件{len(available_tasks)+i+1}的具体情况和要求"
                        },
                        amount=Decimal(random.randint(*template["amount_range"])),
                        urgency=random.choice(["normal", "urgent", "low"]),
                        status=status,
                        assigned_to=lawyer.id if lawyer else None,
                        completion_notes=f"任务已{status}" if status in ["completed", "confirmed"] else None,
                        created_at=created_time,
                        updated_at=updated_time,
                        completed_at=completed_time
                    )
                    session.add(task)
                    grabbed_tasks.append(task)
            
            # 4. 创建用户自己发布的历史任务
            print("📋 创建用户历史任务...")
            if users:
                # 为前几个用户创建历史任务
                for user in users[:3]:
                    for i in range(random.randint(2, 5)):
                        template = random.choice(task_templates)
                        
                        historical_status = random.choice([
                            "published", "grabbed", "in_progress", "completed", "confirmed"
                        ])
                        
                        lawyer = random.choice(lawyers) if lawyers and historical_status != "published" else None
                        
                        task = TaskPublishRecord(
                            id=uuid4(),
                            user_id=user.id,
                            task_type=template["type"],
                            title=f"{template['title']} (历史任务)",
                            description=f"{template['description']} 用户{user.username}的历史任务。",
                            target_info={
                                "target_name": f"历史目标{i+1}",
                                "contact_phone": f"1{random.randint(300000000, 999999999)}",
                                "contact_address": f"广州市天河区{random.choice(['珠江新城', '体育中心', '天河城'])}{random.randint(100, 999)}号"
                            },
                            amount=Decimal(random.randint(*template["amount_range"])),
                            urgency=random.choice(["normal", "urgent", "low"]),
                            status=historical_status,
                            assigned_to=lawyer.id if lawyer else None,
                            created_at=datetime.now() - timedelta(
                                days=random.randint(7, 60),
                                hours=random.randint(0, 23)
                            )
                        )
                        session.add(task)
            
            # 提交所有数据
            await session.commit()
            
            print(f"\n✅ 测试数据创建完成!")
            print(f"📊 可抢单任务: {len(available_tasks)} 个")
            print(f"🎯 已抢单任务: {len(grabbed_tasks)} 个")
            print(f"📝 用户历史任务: 若干个")
            print(f"\n🔍 任务状态分布:")
            print(f"   📌 published (可抢单): {len(available_tasks)} 个")
            print(f"   🎯 grabbed (刚抢到): 5 个") 
            print(f"   ⚙️  in_progress (进行中): 8 个")
            print(f"   ✅ completed (已完成): 6 个")
            print(f"   🎉 confirmed (已确认): 4 个")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ 创建测试数据失败: {str(e)}")
            raise


async def main():
    """主函数"""
    await create_task_test_data()


if __name__ == "__main__":
    asyncio.run(main())