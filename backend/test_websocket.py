#!/usr/bin/env python3
"""
WebSocket实时推送系统测试脚本
"""

import asyncio
import json
import websockets
from datetime import datetime

async def test_websocket_connection():
    """测试WebSocket连接"""
    # 这里需要一个有效的JWT token
    # 在实际测试中，你需要先登录获取token
    test_token = "your-jwt-token-here"
    
    uri = f"ws://localhost:8000/api/v1/websocket/admin/realtime?token={test_token}"
    
    print("🧪 开始测试WebSocket连接...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接建立成功")
            
            # 发送心跳消息
            ping_message = {
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(ping_message))
            print("📡 发送心跳消息")
            
            # 订阅数据类型
            subscribe_message = {
                "type": "subscribe",
                "data_types": ["stats_update", "system_alert", "user_activity"]
            }
            await websocket.send(json.dumps(subscribe_message))
            print("📡 发送订阅消息")
            
            # 请求连接统计
            request_message = {
                "type": "request_data",
                "data_type": "connection_stats"
            }
            await websocket.send(json.dumps(request_message))
            print("📡 请求连接统计数据")
            
            # 监听消息
            print("👂 开始监听WebSocket消息...")
            timeout_count = 0
            max_timeout = 10  # 最多等待10次超时
            
            while timeout_count < max_timeout:
                try:
                    # 等待消息，设置超时
                    message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    data = json.loads(message)
                    
                    print(f"📨 收到消息: {data.get('type')} - {data.get('timestamp', 'N/A')}")
                    
                    if data.get('type') == 'pong':
                        print("   💓 心跳响应")
                    elif data.get('type') == 'stats_update':
                        print(f"   📊 统计更新: {json.dumps(data.get('data', {}), indent=2)}")
                    elif data.get('type') == 'system_alert':
                        print(f"   🚨 系统告警: {data.get('data', {}).get('message', 'N/A')}")
                    elif data.get('type') == 'connection_established':
                        print(f"   🔗 连接建立: {data.get('connection_id', 'N/A')}")
                    elif data.get('type') == 'data_response':
                        print(f"   📋 数据响应: {data.get('data_type')} - {json.dumps(data.get('data', {}), indent=2)}")
                    
                    timeout_count = 0  # 重置超时计数
                    
                except asyncio.TimeoutError:
                    timeout_count += 1
                    print(f"⏰ 等待消息超时 ({timeout_count}/{max_timeout})")
                    
                    # 发送心跳保持连接
                    if timeout_count % 3 == 0:
                        ping_message = {
                            "type": "ping",
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(ping_message))
                        print("💓 发送心跳保持连接")
            
            print("✅ WebSocket测试完成")
            
    except websockets.exceptions.InvalidStatusCode as e:
        if e.status_code == 4001:
            print("❌ 认证失败: 无效的token")
        elif e.status_code == 4003:
            print("❌ 权限不足: 需要管理员权限")
        else:
            print(f"❌ WebSocket连接失败: 状态码 {e.status_code}")
    except Exception as e:
        print(f"❌ WebSocket测试失败: {str(e)}")

async def test_broadcast_api():
    """测试广播API"""
    import aiohttp
    
    print("\n🧪 测试广播API...")
    
    # 测试数据
    test_messages = [
        {
            "type": "stats_update",
            "data": {
                "total_visits": 1234,
                "active_users": 56,
                "timestamp": datetime.now().isoformat()
            }
        },
        {
            "type": "alert",
            "data": {
                "level": "warning",
                "message": "测试告警消息",
                "details": {"test": True}
            }
        },
        {
            "type": "notification",
            "data": {
                "title": "测试通知",
                "message": "这是一个测试通知消息",
                "priority": "normal"
            }
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for message in test_messages:
            try:
                url = "http://localhost:8000/api/v1/websocket/admin/websocket/broadcast"
                
                async with session.post(url, json=message) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ 广播消息成功: {message['type']}")
                    else:
                        print(f"❌ 广播消息失败: {message['type']} - 状态码 {response.status}")
                        
                # 等待一下再发送下一条
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ 广播API测试失败: {str(e)}")

async def test_websocket_stats_api():
    """测试WebSocket统计API"""
    import aiohttp
    
    print("\n🧪 测试WebSocket统计API...")
    
    try:
        async with aiohttp.ClientSession() as session:
            url = "http://localhost:8000/api/v1/websocket/admin/websocket/stats"
            
            async with session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ 获取WebSocket统计成功:")
                    print(f"   {json.dumps(result.get('data', {}), indent=2)}")
                else:
                    print(f"❌ 获取WebSocket统计失败: 状态码 {response.status}")
                    
    except Exception as e:
        print(f"❌ WebSocket统计API测试失败: {str(e)}")

def print_websocket_test_info():
    """打印WebSocket测试信息"""
    print("🚀 Lawsker WebSocket实时推送系统测试")
    print("=" * 50)
    print("📋 测试内容:")
    print("  1. WebSocket连接建立")
    print("  2. 心跳机制测试")
    print("  3. 消息订阅测试")
    print("  4. 数据请求测试")
    print("  5. 广播API测试")
    print("  6. 统计API测试")
    print()
    print("⚠️  注意事项:")
    print("  - 需要先启动Lawsker后端服务")
    print("  - 需要有效的JWT token进行认证")
    print("  - 需要管理员权限才能连接WebSocket")
    print("=" * 50)

if __name__ == "__main__":
    print_websocket_test_info()
    
    # 运行测试
    print("\n🔧 开始WebSocket功能测试...")
    
    # 注意: 在实际测试中，你需要先获取有效的JWT token
    print("⚠️  请先获取有效的JWT token并更新test_token变量")
    print("   可以通过登录API获取: POST /api/v1/auth/login")
    
    # 测试统计API（不需要认证）
    asyncio.run(test_websocket_stats_api())
    
    # 测试广播API（不需要认证）
    asyncio.run(test_broadcast_api())
    
    # WebSocket连接测试需要有效token
    print("\n💡 要测试WebSocket连接，请:")
    print("   1. 获取有效的JWT token")
    print("   2. 更新脚本中的test_token变量")
    print("   3. 重新运行测试")
    
    # 如果有有效token，可以取消注释下面这行
    # asyncio.run(test_websocket_connection())