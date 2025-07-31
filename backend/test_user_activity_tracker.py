#!/usr/bin/env python3
"""
用户行为追踪系统测试脚本
"""

import asyncio
import json
from datetime import datetime

async def test_user_activity_tracker():
    """测试用户行为追踪功能"""
    print("🧪 开始测试用户行为追踪系统...")
    
    try:
        from app.services.user_activity_tracker import (
            track_login, track_case_action, track_payment_action,
            track_document_action, get_user_activity_stats
        )
        
        # 测试用户ID
        test_user_id = "test-user-123"
        test_ip = "192.168.1.100"
        
        print("📝 测试登录行为追踪...")
        await track_login(
            user_id=test_user_id,
            ip_address=test_ip,
            user_agent="Mozilla/5.0 (Test Browser)"
        )
        
        print("📝 测试案件操作追踪...")
        await track_case_action(
            user_id=test_user_id,
            action="create",
            case_id="case-456",
            details={"case_amount": 50000.0, "debtor_name": "测试债务人"},
            ip_address=test_ip
        )
        
        print("📝 测试支付操作追踪...")
        await track_payment_action(
            user_id=test_user_id,
            action="success",
            payment_id="payment-789",
            amount=30.0,
            details={"payment_method": "wechat"},
            ip_address=test_ip
        )
        
        print("📝 测试文档操作追踪...")
        await track_document_action(
            user_id=test_user_id,
            action="generate",
            document_id="doc-101",
            document_type="lawyer_letter",
            details={"template": "debt_collection"},
            ip_address=test_ip
        )
        
        # 等待一下让数据处理
        await asyncio.sleep(2)
        
        print("📊 获取用户活动统计...")
        stats = await get_user_activity_stats(test_user_id, days=1)
        print(f"   用户活动统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        
        print("✅ 用户行为追踪测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

async def check_activity_queue_status():
    """检查用户活动队列状态"""
    try:
        import redis.asyncio as redis
        from app.core.config import settings
        
        redis_client = redis.from_url(settings.REDIS_URL)
        queue_length = await redis_client.llen("user_activities_queue")
        
        print(f"📊 用户活动队列状态:")
        print(f"   队列长度: {queue_length}")
        
        if queue_length > 0:
            # 查看队列中的一条数据（不移除）
            sample_data = await redis_client.lindex("user_activities_queue", 0)
            if sample_data:
                sample_activity = json.loads(sample_data)
                print(f"   样本数据: {sample_activity.get('action')} - {sample_activity.get('user_id')}")
        
        await redis_client.close()
        
    except Exception as e:
        print(f"❌ 检查用户活动队列失败: {str(e)}")

async def test_database_query():
    """测试数据库查询"""
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as db:
            # 查询最近的用户活动
            query = text("""
                SELECT action, resource_type, resource_id, created_at
                FROM user_activity_logs 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            result = await db.execute(query)
            activities = result.fetchall()
            
            print("📊 最近的用户活动:")
            for activity in activities:
                print(f"   {activity.action} - {activity.resource_type} - {activity.created_at}")
                
    except Exception as e:
        print(f"❌ 数据库查询失败: {str(e)}")

if __name__ == "__main__":
    print("🚀 Lawsker用户行为追踪系统测试")
    print("=" * 50)
    
    # 运行测试
    asyncio.run(test_user_activity_tracker())
    
    print("\n" + "=" * 50)
    asyncio.run(check_activity_queue_status())
    
    print("\n" + "=" * 50)
    asyncio.run(test_database_query())