#!/usr/bin/env python3
"""
初始化演示数据脚本
将前端演示数据写入数据库确保功能完整性
"""

import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.lawyer_review import DocumentReviewTask, ReviewStatus
from sqlalchemy import text


async def init_demo_users(db: AsyncSession):
    """初始化演示用户数据"""
    # 生成固定的UUID，便于前端引用
    user_001_id = "1b364915-89df-48d8-9c70-e1e16a6d9446"
    lawyer_001_id = "2c475026-9aef-59e9-ad81-f2f27b7daf57"
    lawyer_002_id = "3d586137-abf0-6afa-be92-g3g38c8ebg68"
    
    demo_users = [
        {
            "id": user_001_id,
            "username": "demo_user_001", 
            "email": "user001@lawsker.com",
            "phone_number": "13812345678",
            "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewJMpEPoZaIlM9KG",  # password: demo123
            "status": "active",
            "created_at": datetime.now() - timedelta(days=30)
        },
        {
            "id": lawyer_001_id,
            "username": "lawyer_zhang",
            "email": "zhang.jianguo@lawsker.com", 
            "phone_number": "13800000001",
            "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewJMpEPoZaIlM9KG",  # password: demo123
            "status": "active",
            "created_at": datetime.now() - timedelta(days=60)
        },
        {
            "id": lawyer_002_id, 
            "username": "lawyer_li",
            "email": "li.minghua@lawsker.com",
            "phone_number": "13800000002",
            "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewJMpEPoZaIlM9KG",  # password: demo123
            "status": "active",
            "created_at": datetime.now() - timedelta(days=50)
        }
    ]
    
    for user_data in demo_users:
        # 检查用户是否已存在
        existing_user = await db.execute(
            select(User).where(User.id == user_data["id"])
        )
        if existing_user.scalar_one_or_none():
            print(f"用户 {user_data['full_name']} 已存在，跳过创建")
            continue
            
        user = User(**user_data)
        db.add(user)
        print(f"创建用户: {user_data['full_name']}")
    
    await db.commit()
    print("✅ 演示用户数据初始化完成")


async def init_demo_tasks(db: AsyncSession):
    """初始化演示任务数据"""
    # 使用前面定义的UUID
    user_001_id = "1b364915-89df-48d8-9c70-e1e16a6d9446"
    lawyer_001_id = "2c475026-9aef-59e9-ad81-f2f27b7daf57"
    lawyer_002_id = "3d586137-abf0-6afa-be92-g3g38c8ebg68"
    
    demo_tasks = [
        {
            "task_id": "user-task-001",
            "case_title": "债权催收律师函",
            "case_description": "需要向欠款方发送律师函，催收货款15万元",
            "service_type": "collection_letter",
            "urgency": "普通",
            "expected_amount": 150000,
            "overdue_days": 90,
            "user_id": user_001_id,
            "lawyer_id": lawyer_001_id,
            "status": ReviewStatus.GRABBED,
            "created_at": datetime.now() - timedelta(days=2),
            "target_info": {
                "target_name": "王某某",
                "contact_phone": "138****5678", 
                "contact_address": "上海市浦东新区张江路123号",
                "case_details": "拖欠货款15万元，已逾期3个月未付"
            },
            "lawyer_fee": 650
        },
        {
            "task_id": "user-task-002",
            "case_title": "商务合作合同审查", 
            "case_description": "重要合作协议需要法律专业审查，合同金额500万",
            "service_type": "contract_review",
            "urgency": "紧急",
            "expected_amount": 5000000,
            "user_id": user_001_id,
            "lawyer_id": lawyer_002_id, 
            "status": ReviewStatus.COMPLETED,
            "created_at": datetime.now() - timedelta(days=5),
            "completed_at": datetime.now() - timedelta(days=1),
            "target_info": {
                "target_name": "ABC科技有限公司",
                "contact_phone": "021-12345678",
                "contact_address": "上海市黄浦区南京路100号", 
                "case_details": "战略合作协议，涉及知识产权和技术转让"
            },
            "lawyer_fee": 1200
        },
        {
            "task_id": "user-task-003",
            "case_title": "劳动纠纷法律咨询",
            "case_description": "公司员工劳动合同纠纷，需要专业法律建议",
            "service_type": "legal_consultation", 
            "urgency": "普通",
            "expected_amount": 0,
            "user_id": user_001_id,
            "status": ReviewStatus.PUBLISHED,
            "created_at": datetime.now() - timedelta(hours=3),
            "target_info": {
                "target_name": "员工小李",
                "contact_phone": "150****9876",
                "contact_address": "北京市朝阳区建国路88号",
                "case_details": "劳动合同到期争议，涉及补偿金计算"
            },
            "lawyer_fee": 400
        }
    ]
    
    for task_data in demo_tasks:
        # 检查任务是否已存在
        existing_task = await db.execute(
            select(DocumentReviewTask).where(DocumentReviewTask.task_id == task_data["task_id"])
        )
        if existing_task.scalar_one_or_none():
            print(f"任务 {task_data['case_title']} 已存在，跳过创建")
            continue
            
        task = DocumentReviewTask(**task_data)
        db.add(task)
        print(f"创建任务: {task_data['case_title']}")
    
    await db.commit()
    print("✅ 演示任务数据初始化完成")


async def main():
    """主函数"""
    print("🚀 开始初始化演示数据...")
    
    try:
        async with AsyncSessionLocal() as db:
            # 初始化用户数据
            await init_demo_users(db)
            
            # 初始化任务数据  
            await init_demo_tasks(db)
            
        print("🎉 演示数据初始化完成！")
        print("📝 已创建：")
        print("   - 3个演示用户（1个普通用户，2个律师）")
        print("   - 3个演示任务（不同状态）")
        print("   - 包含完整的用户信息、律师资质、任务详情等")
        
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())