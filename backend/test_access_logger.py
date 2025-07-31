#!/usr/bin/env python3
"""
访问日志中间件测试脚本
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_access_logger():
    """测试访问日志记录功能"""
    base_url = "http://localhost:8000"
    
    # 测试不同的端点
    test_endpoints = [
        "/health",
        "/api/v1/auth/login",
        "/",
        "/api/v1/admin/access-logs/queue-status"
    ]
    
    print("🧪 开始测试访问日志中间件...")
    
    async with aiohttp.ClientSession() as session:
        for endpoint in test_endpoints:
            try:
                url = f"{base_url}{endpoint}"
                print(f"📡 测试端点: {url}")
                
                # 发送GET请求
                async with session.get(url) as response:
                    print(f"   状态码: {response.status}")
                    print(f"   响应时间: {response.headers.get('X-Response-Time', 'N/A')}")
                
                # 短暂等待
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ 请求失败: {str(e)}")
    
    print("\n✅ 访问日志测试完成")
    print("💡 请检查数据库access_logs表和Redis队列中的数据")

async def check_queue_status():
    """检查Redis队列状态"""
    try:
        import redis.asyncio as redis
        from app.core.config import settings
        
        redis_client = redis.from_url(settings.REDIS_URL)
        queue_length = await redis_client.llen("access_logs_queue")
        
        print(f"📊 Redis队列状态:")
        print(f"   队列长度: {queue_length}")
        
        if queue_length > 0:
            # 查看队列中的一条数据（不移除）
            sample_data = await redis_client.lindex("access_logs_queue", 0)
            if sample_data:
                sample_log = json.loads(sample_data)
                print(f"   样本数据: {sample_log.get('request_path')} - {sample_log.get('ip_address')}")
        
        await redis_client.close()
        
    except Exception as e:
        print(f"❌ 检查Redis队列失败: {str(e)}")

if __name__ == "__main__":
    print("🚀 Lawsker访问日志中间件测试")
    print("=" * 50)
    
    # 运行测试
    asyncio.run(test_access_logger())
    
    print("\n" + "=" * 50)
    asyncio.run(check_queue_status())