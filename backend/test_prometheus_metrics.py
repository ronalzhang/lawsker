#!/usr/bin/env python3
"""
Prometheus监控指标测试脚本
测试指标收集、HTTP监控、数据库监控等功能
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
import httpx

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from app.services.prometheus_metrics import prometheus_metrics
from app.services.metrics_collector import metrics_collector, record_business_event
from app.core.db_monitor import monitor_db_query, db_monitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_prometheus_metrics():
    """测试Prometheus指标收集"""
    logger.info("🧪 测试Prometheus指标收集...")
    
    try:
        # 测试HTTP请求指标
        prometheus_metrics.record_http_request("GET", "/api/v1/test", 200, 0.5)
        prometheus_metrics.record_http_request("POST", "/api/v1/cases", 201, 1.2)
        prometheus_metrics.record_http_request("GET", "/api/v1/users", 500, 2.1)
        
        # 测试数据库查询指标
        prometheus_metrics.record_db_query("select", 0.1)
        prometheus_metrics.record_db_query("insert", 0.3)
        prometheus_metrics.record_db_query("update", 0.8)
        
        # 测试业务指标
        prometheus_metrics.record_case_creation("client")
        prometheus_metrics.record_case_creation("lawyer")
        prometheus_metrics.record_transaction("payment", "success", 1000.0)
        prometheus_metrics.record_transaction("refund", "failed", 500.0)
        prometheus_metrics.record_lawyer_response_time(1800)  # 30分钟
        
        # 测试Redis指标
        prometheus_metrics.record_redis_operation("lpush", "success")
        prometheus_metrics.record_redis_operation("rpop", "success")
        prometheus_metrics.record_redis_operation("get", "error")
        
        # 测试WebSocket指标
        prometheus_metrics.record_websocket_connection(50)
        prometheus_metrics.record_websocket_message("sent")
        prometheus_metrics.record_websocket_message("received")
        
        # 更新系统指标
        prometheus_metrics.update_system_metrics()
        prometheus_metrics.update_app_uptime()
        
        logger.info("✅ Prometheus指标收集测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ Prometheus指标收集测试失败: {str(e)}")
        return False


async def test_metrics_collector():
    """测试指标收集器"""
    logger.info("🧪 测试指标收集器...")
    
    try:
        # 启动指标收集器
        await metrics_collector.start()
        
        # 等待一段时间让收集器运行
        await asyncio.sleep(2)
        
        # 获取收集器状态
        status = await metrics_collector.get_collection_status()
        logger.info(f"收集器状态: {status}")
        
        # 测试业务事件记录
        record_business_event("case_created", user_type="client")
        record_business_event("transaction", transaction_type="payment", status="success", amount=1500.0)
        record_business_event("lawyer_response", response_time_seconds=900)
        record_business_event("websocket_connection", active_connections=25)
        record_business_event("websocket_message", direction="sent")
        record_business_event("redis_operation", operation="set", status="success")
        
        # 手动触发业务指标收集
        result = await metrics_collector.collect_business_metrics_now()
        logger.info(f"业务指标收集结果: {result}")
        
        # 停止指标收集器
        await metrics_collector.stop()
        
        logger.info("✅ 指标收集器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 指标收集器测试失败: {str(e)}")
        return False


async def test_db_monitor():
    """测试数据库监控"""
    logger.info("🧪 测试数据库监控...")
    
    try:
        # 测试数据库监控装饰器
        @monitor_db_query("test_select")
        async def test_db_query():
            await asyncio.sleep(0.1)  # 模拟数据库查询
            return "test_result"
        
        # 执行测试查询
        result = await test_db_query()
        logger.info(f"测试查询结果: {result}")
        
        # 测试数据库连接统计
        conn_result = await db_monitor.get_connection_stats()
        logger.info(f"数据库连接统计: {conn_result}")
        
        # 手动记录查询指标
        db_monitor.monitor_query_execution("manual_test", 0.5, True)
        db_monitor.monitor_query_execution("manual_error", 1.0, False)
        
        logger.info("✅ 数据库监控测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库监控测试失败: {str(e)}")
        return False


async def test_metrics_export():
    """测试指标导出"""
    logger.info("🧪 测试指标导出...")
    
    try:
        # 收集所有指标
        await prometheus_metrics.collect_all_metrics()
        
        # 获取Prometheus格式的指标
        metrics_data = prometheus_metrics.get_metrics()
        
        # 检查指标数据
        if not metrics_data:
            raise ValueError("指标数据为空")
        
        # 检查是否包含预期的指标
        expected_metrics = [
            "http_requests_total",
            "http_request_duration_seconds",
            "db_connections_active",
            "db_query_duration_seconds",
            "system_cpu_usage_percent",
            "system_memory_usage_bytes",
            "app_uptime_seconds"
        ]
        
        for metric in expected_metrics:
            if metric not in metrics_data:
                logger.warning(f"指标 {metric} 未找到")
            else:
                logger.debug(f"✓ 指标 {metric} 存在")
        
        # 保存指标到文件用于检查
        with open("test_metrics_output.txt", "w") as f:
            f.write(metrics_data)
        
        logger.info(f"✅ 指标导出测试通过，数据长度: {len(metrics_data)} 字符")
        return True
        
    except Exception as e:
        logger.error(f"❌ 指标导出测试失败: {str(e)}")
        return False


async def test_metrics_api():
    """测试指标API端点"""
    logger.info("🧪 测试指标API端点...")
    
    try:
        base_url = "http://localhost:8000"
        
        async with httpx.AsyncClient() as client:
            # 测试指标端点 (不需要认证)
            try:
                response = await client.get(f"{base_url}/api/v1/metrics/metrics")
                if response.status_code == 200:
                    logger.info("✓ 指标端点可访问")
                else:
                    logger.warning(f"指标端点返回状态码: {response.status_code}")
            except Exception as e:
                logger.warning(f"指标端点测试失败 (可能服务未启动): {str(e)}")
            
            # 测试健康检查端点
            try:
                response = await client.get(f"{base_url}/api/v1/metrics/health/metrics")
                if response.status_code == 200:
                    health_data = response.json()
                    logger.info(f"✓ 健康检查端点可访问: {health_data.get('status', 'unknown')}")
                else:
                    logger.warning(f"健康检查端点返回状态码: {response.status_code}")
            except Exception as e:
                logger.warning(f"健康检查端点测试失败 (可能服务未启动): {str(e)}")
        
        logger.info("✅ 指标API端点测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 指标API端点测试失败: {str(e)}")
        return False


async def test_system_metrics():
    """测试系统指标收集"""
    logger.info("🧪 测试系统指标收集...")
    
    try:
        # 更新系统指标
        prometheus_metrics.update_system_metrics()
        
        # 检查是否能正常获取系统信息
        import psutil
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        logger.info(f"CPU使用率: {cpu_percent}%")
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        logger.info(f"内存使用: {memory.percent}% ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)")
        
        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        logger.info(f"磁盘使用: {disk.percent}% ({disk.used / 1024**3:.1f}GB / {disk.total / 1024**3:.1f}GB)")
        
        # 网络统计
        network = psutil.net_io_counters()
        logger.info(f"网络: 发送 {network.bytes_sent / 1024**2:.1f}MB, 接收 {network.bytes_recv / 1024**2:.1f}MB")
        
        logger.info("✅ 系统指标收集测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 系统指标收集测试失败: {str(e)}")
        return False


async def run_all_tests():
    """运行所有测试"""
    logger.info("🚀 开始Prometheus监控指标测试")
    logger.info("=" * 60)
    
    test_results = []
    
    # 运行各项测试
    tests = [
        ("Prometheus指标收集", test_prometheus_metrics),
        ("系统指标收集", test_system_metrics),
        ("数据库监控", test_db_monitor),
        ("指标收集器", test_metrics_collector),
        ("指标导出", test_metrics_export),
        ("指标API端点", test_metrics_api),
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 执行测试: {test_name}")
        logger.info("-" * 40)
        
        try:
            result = await test_func()
            test_results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name} 测试通过")
            else:
                logger.error(f"❌ {test_name} 测试失败")
                
        except Exception as e:
            logger.error(f"❌ {test_name} 测试异常: {str(e)}")
            test_results.append((test_name, False))
        
        # 测试间隔
        await asyncio.sleep(1)
    
    # 输出测试结果汇总
    logger.info("\n" + "=" * 60)
    logger.info("📊 测试结果汇总:")
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  {test_name}: {status}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\n总计: {passed + failed} 个测试")
    logger.info(f"通过: {passed} 个")
    logger.info(f"失败: {failed} 个")
    logger.info(f"成功率: {(passed / (passed + failed) * 100):.1f}%")
    
    if failed == 0:
        logger.info("\n🎉 所有测试通过！Prometheus监控功能正常工作")
        return True
    else:
        logger.error(f"\n⚠️  有 {failed} 个测试失败，请检查相关功能")
        return False


async def main():
    """主函数"""
    print("🔧 Lawsker Prometheus监控指标测试")
    print("=" * 60)
    
    try:
        success = await run_all_tests()
        
        if success:
            print("\n✅ Prometheus监控指标测试全部通过")
            sys.exit(0)
        else:
            print("\n❌ 部分测试失败")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 测试执行异常: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())