#!/usr/bin/env python3
"""
批量数据处理功能测试脚本
测试访问日志批量插入、数据清理、分页查询和导出功能
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import uuid

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from app.services.batch_data_processor import batch_data_processor
from app.services.pagination_service import pagination_service
from app.services.data_export_service import data_export_service
from app.services.scheduled_tasks import run_manual_cleanup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_test_access_logs(count: int = 100) -> List[Dict[str, Any]]:
    """生成测试访问日志数据"""
    logs = []
    base_time = datetime.now() - timedelta(days=30)
    
    for i in range(count):
        log = {
            "user_id": str(uuid.uuid4()) if i % 3 == 0 else None,  # 1/3的请求有用户ID
            "session_id": str(uuid.uuid4()),
            "ip_address": f"192.168.1.{(i % 254) + 1}",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "referer": "https://lawsker.com" if i % 2 == 0 else None,
            "request_path": f"/api/v1/test/{i % 10}",
            "request_method": "GET" if i % 3 == 0 else "POST",
            "status_code": 200 if i % 10 != 9 else 404,  # 10%的请求返回404
            "response_time": 50 + (i % 200),  # 50-250ms响应时间
            "device_type": "desktop" if i % 2 == 0 else "mobile",
            "browser": "Chrome" if i % 3 == 0 else "Firefox",
            "os": "Windows" if i % 2 == 0 else "macOS",
            "country": "中国",
            "region": "北京市" if i % 2 == 0 else "上海市",
            "city": "北京" if i % 2 == 0 else "上海",
            "created_at": base_time + timedelta(minutes=i * 5)
        }
        logs.append(log)
    
    return logs


def generate_test_user_activities(count: int = 50) -> List[Dict[str, Any]]:
    """生成测试用户活动数据"""
    activities = []
    base_time = datetime.now() - timedelta(days=15)
    actions = ["login", "logout", "create_case", "update_case", "payment", "view_document"]
    
    for i in range(count):
        activity = {
            "user_id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "action": actions[i % len(actions)],
            "resource_type": "case" if i % 3 == 0 else "document",
            "resource_id": str(uuid.uuid4()),
            "details": json.dumps({"test": True, "index": i}),
            "ip_address": f"10.0.0.{(i % 254) + 1}",
            "user_agent": "Mozilla/5.0 Test Agent",
            "created_at": base_time + timedelta(hours=i * 2)
        }
        activities.append(activity)
    
    return activities


async def test_batch_insert():
    """测试批量插入功能"""
    logger.info("🧪 测试批量插入功能...")
    
    try:
        # 测试访问日志批量插入
        access_logs = generate_test_access_logs(200)
        inserted_count = await batch_data_processor.batch_insert_access_logs(access_logs)
        logger.info(f"✅ 访问日志批量插入成功: {inserted_count}/{len(access_logs)} 条")
        
        # 测试用户活动批量插入
        user_activities = generate_test_user_activities(100)
        inserted_count = await batch_data_processor.batch_insert_user_activities(user_activities)
        logger.info(f"✅ 用户活动批量插入成功: {inserted_count}/{len(user_activities)} 条")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 批量插入测试失败: {str(e)}")
        return False


async def test_pagination():
    """测试分页查询功能"""
    logger.info("🧪 测试分页查询功能...")
    
    try:
        # 测试访问日志分页
        result = await pagination_service.paginate_access_logs(
            page=1,
            page_size=10,
            status_code=200
        )
        logger.info(f"✅ 访问日志分页查询成功: 总数={result.total}, 当前页={result.page}, 数据条数={len(result.items)}")
        
        # 测试用户活动分页
        result = await pagination_service.paginate_user_activities(
            page=1,
            page_size=5,
            action="login"
        )
        logger.info(f"✅ 用户活动分页查询成功: 总数={result.total}, 当前页={result.page}, 数据条数={len(result.items)}")
        
        # 测试游标分页
        cursor_result = await pagination_service.cursor_paginate_query(
            query="SELECT id, created_at, request_path FROM access_logs",
            cursor_field="created_at",
            page_size=5,
            order="desc"
        )
        logger.info(f"✅ 游标分页查询成功: 数据条数={len(cursor_result.items)}, 有下一页={cursor_result.has_next}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 分页查询测试失败: {str(e)}")
        return False


async def test_data_export():
    """测试数据导出功能"""
    logger.info("🧪 测试数据导出功能...")
    
    try:
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        # 测试CSV导出
        csv_file = await data_export_service.export_access_logs(
            start_date=start_date,
            end_date=end_date,
            format="csv"
        )
        logger.info(f"✅ CSV导出成功: {csv_file}")
        
        # 测试Excel导出
        excel_file = await data_export_service.export_user_activities(
            start_date=start_date,
            end_date=end_date,
            format="excel"
        )
        logger.info(f"✅ Excel导出成功: {excel_file}")
        
        # 测试统计报表导出
        stats_file = await data_export_service.export_statistics_report(
            start_date=start_date,
            end_date=end_date,
            format="excel"
        )
        logger.info(f"✅ 统计报表导出成功: {stats_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据导出测试失败: {str(e)}")
        return False


async def test_data_cleanup():
    """测试数据清理功能"""
    logger.info("🧪 测试数据清理功能...")
    
    try:
        # 测试访问日志清理（保留1天，用于测试）
        deleted_count = await batch_data_processor.cleanup_old_access_logs(1)
        logger.info(f"✅ 访问日志清理成功: 删除 {deleted_count} 条记录")
        
        # 测试用户活动清理（保留1天，用于测试）
        deleted_count = await batch_data_processor.cleanup_old_user_activities(1)
        logger.info(f"✅ 用户活动清理成功: 删除 {deleted_count} 条记录")
        
        # 测试导出文件清理
        await data_export_service.cleanup_old_exports(0)  # 清理所有导出文件
        logger.info("✅ 导出文件清理成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据清理测试失败: {str(e)}")
        return False


async def test_manual_cleanup():
    """测试手动清理任务"""
    logger.info("🧪 测试手动清理任务...")
    
    try:
        # 测试手动清理访问日志
        result = await run_manual_cleanup("access_logs", days_to_keep=30)
        logger.info(f"✅ 手动清理访问日志: {result}")
        
        # 测试手动清理用户活动
        result = await run_manual_cleanup("user_activities", days_to_keep=60)
        logger.info(f"✅ 手动清理用户活动: {result}")
        
        # 测试手动清理导出文件
        result = await run_manual_cleanup("exports", days_to_keep=3)
        logger.info(f"✅ 手动清理导出文件: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 手动清理任务测试失败: {str(e)}")
        return False


async def test_table_stats():
    """测试表统计信息"""
    logger.info("🧪 测试表统计信息...")
    
    try:
        # 测试访问日志表统计
        stats = await pagination_service.get_table_stats("access_logs")
        logger.info(f"✅ 访问日志表统计: {stats}")
        
        # 测试用户活动表统计
        stats = await pagination_service.get_table_stats("user_activity_logs")
        logger.info(f"✅ 用户活动表统计: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 表统计信息测试失败: {str(e)}")
        return False


async def run_all_tests():
    """运行所有测试"""
    logger.info("🚀 开始批量数据处理功能测试")
    logger.info("=" * 60)
    
    test_results = []
    
    # 运行各项测试
    tests = [
        ("批量插入", test_batch_insert),
        ("分页查询", test_pagination),
        ("数据导出", test_data_export),
        ("表统计信息", test_table_stats),
        ("手动清理任务", test_manual_cleanup),
        ("数据清理", test_data_cleanup),  # 放在最后，因为会删除测试数据
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
        logger.info("\n🎉 所有测试通过！批量数据处理功能正常工作")
        return True
    else:
        logger.error(f"\n⚠️  有 {failed} 个测试失败，请检查相关功能")
        return False


async def main():
    """主函数"""
    print("🔧 Lawsker批量数据处理功能测试")
    print("=" * 60)
    
    try:
        success = await run_all_tests()
        
        if success:
            print("\n✅ 批量数据处理功能测试全部通过")
            sys.exit(0)
        else:
            print("\n❌ 部分测试失败")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 测试执行异常: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())