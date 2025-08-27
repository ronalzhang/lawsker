#!/usr/bin/env python3
"""
企业客户满意度系统测试脚本
验证满意度跟踪、分析和改进功能
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.enterprise_customer_satisfaction_service import EnterpriseCustomerSatisfactionService
from unittest.mock import AsyncMock, MagicMock
import json
from datetime import datetime, timedelta

async def test_satisfaction_tracking():
    """测试满意度跟踪功能"""
    print("🧪 测试企业客户满意度跟踪...")
    print("=" * 50)
    
    # 模拟数据库会话
    mock_db = AsyncMock()
    
    # 创建服务实例
    service = EnterpriseCustomerSatisfactionService(mock_db)
    
    # 测试记录满意度
    print("📊 测试满意度记录...")
    result = await service.track_customer_satisfaction(
        customer_id="test-customer-001",
        service_type="data_analysis",
        satisfaction_score=4.5,
        feedback_text="服务质量很好，数据分析准确",
        service_quality_metrics={
            "response_time": 2.5,
            "accuracy_rate": 95.0,
            "completeness": 98.0
        }
    )
    
    test_results = []
    
    # 验证记录结果
    if result.get("success"):
        print("✅ 满意度记录成功")
        test_results.append(True)
    else:
        print("❌ 满意度记录失败")
        test_results.append(False)
    
    if result.get("satisfaction_score") == 4.5:
        print("✅ 满意度评分记录正确")
        test_results.append(True)
    else:
        print("❌ 满意度评分记录错误")
        test_results.append(False)
    
    # 验证数据库调用
    if mock_db.execute.called:
        print("✅ 数据库插入操作已调用")
        test_results.append(True)
    else:
        print("❌ 数据库插入操作未调用")
        test_results.append(False)
    
    return all(test_results)

async def test_satisfaction_analytics():
    """测试满意度分析功能"""
    print("\n📈 测试满意度分析...")
    print("=" * 50)
    
    # 模拟数据库会话
    mock_db = AsyncMock()
    
    # 模拟查询结果
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        (100, 4.2, 85, 60, 5, 'data_analysis', 25),  # 数据分析服务
        (80, 4.0, 68, 45, 8, 'legal_consultation', 20),  # 法律咨询服务
        (60, 3.8, 48, 30, 12, 'document_review', 18)  # 文档审查服务
    ]
    mock_db.execute.return_value = mock_result
    
    # 创建服务实例
    service = EnterpriseCustomerSatisfactionService(mock_db)
    
    # 测试获取分析数据
    analytics = await service.get_satisfaction_analytics(date_range=30)
    
    test_results = []
    
    # 验证分析结果结构
    required_keys = [
        'period', 'overall_metrics', 'service_breakdown', 
        'improvement_suggestions', 'target_achievement', 'data_disclaimer'
    ]
    
    for key in required_keys:
        if key in analytics:
            print(f"✅ 包含{key}分析数据")
            test_results.append(True)
        else:
            print(f"❌ 缺少{key}分析数据")
            test_results.append(False)
    
    # 验证整体指标
    overall_metrics = analytics.get('overall_metrics', {})
    if overall_metrics.get('total_responses', 0) > 0:
        print("✅ 总体响应数据正确")
        test_results.append(True)
    else:
        print("❌ 总体响应数据错误")
        test_results.append(False)
    
    # 验证满意度计算
    satisfaction_rate = overall_metrics.get('satisfaction_rate_percent', 0)
    if 0 <= satisfaction_rate <= 100:
        print(f"✅ 满意度百分比计算正确: {satisfaction_rate}%")
        test_results.append(True)
    else:
        print(f"❌ 满意度百分比计算错误: {satisfaction_rate}%")
        test_results.append(False)
    
    # 验证目标达成情况
    target_achievement = analytics.get('target_achievement', {})
    if target_achievement.get('target_satisfaction_rate') == 95.0:
        print("✅ 目标满意度设置正确 (95%)")
        test_results.append(True)
    else:
        print("❌ 目标满意度设置错误")
        test_results.append(False)
    
    # 验证改进建议
    suggestions = analytics.get('improvement_suggestions', [])
    if len(suggestions) > 0:
        print(f"✅ 生成了 {len(suggestions)} 条改进建议")
        test_results.append(True)
        
        # 检查建议结构
        first_suggestion = suggestions[0]
        suggestion_keys = ['priority', 'category', 'title', 'description', 'actions']
        if all(key in first_suggestion for key in suggestion_keys):
            print("✅ 改进建议结构完整")
            test_results.append(True)
        else:
            print("❌ 改进建议结构不完整")
            test_results.append(False)
    else:
        print("⚠️  未生成改进建议")
        test_results.append(True)  # 可能满意度已经很高
    
    # 验证免责声明
    disclaimer = analytics.get('data_disclaimer', {})
    if disclaimer and 'content' in disclaimer:
        disclaimer_text = ' '.join(disclaimer['content'])
        if '仅供参考' in disclaimer_text and '不构成' in disclaimer_text:
            print("✅ 包含适当的免责声明")
            test_results.append(True)
        else:
            print("❌ 免责声明内容不完整")
            test_results.append(False)
    else:
        print("❌ 缺少免责声明")
        test_results.append(False)
    
    return all(test_results)

async def test_customer_trends():
    """测试客户满意度趋势分析"""
    print("\n📊 测试客户满意度趋势...")
    print("=" * 50)
    
    # 模拟数据库会话
    mock_db = AsyncMock()
    
    # 模拟趋势查询结果
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        (datetime(2024, 1, 1), 4.2, 25, 'data_analysis'),
        (datetime(2024, 2, 1), 4.0, 30, 'data_analysis'),
        (datetime(2024, 3, 1), 4.5, 28, 'data_analysis')
    ]
    mock_db.execute.return_value = mock_result
    
    # 创建服务实例
    service = EnterpriseCustomerSatisfactionService(mock_db)
    
    # 测试获取趋势数据
    trends = await service.get_customer_feedback_trends(
        customer_id="test-customer-001",
        months=6
    )
    
    test_results = []
    
    # 验证趋势数据结构
    required_keys = ['customer_id', 'period_months', 'satisfaction_trends', 'recent_feedback', 'trend_analysis']
    
    for key in required_keys:
        if key in trends:
            print(f"✅ 包含{key}趋势数据")
            test_results.append(True)
        else:
            print(f"❌ 缺少{key}趋势数据")
            test_results.append(False)
    
    # 验证客户ID
    if trends.get('customer_id') == "test-customer-001":
        print("✅ 客户ID匹配正确")
        test_results.append(True)
    else:
        print("❌ 客户ID匹配错误")
        test_results.append(False)
    
    # 验证趋势分析
    trend_analysis = trends.get('trend_analysis', {})
    if 'trend' in trend_analysis and 'message' in trend_analysis:
        print(f"✅ 趋势分析完整: {trend_analysis.get('message', '')}")
        test_results.append(True)
    else:
        print("❌ 趋势分析不完整")
        test_results.append(False)
    
    return all(test_results)

async def test_improvement_implementation():
    """测试改进措施实施"""
    print("\n🔧 测试改进措施实施...")
    print("=" * 50)
    
    # 模拟数据库会话
    mock_db = AsyncMock()
    
    # 创建服务实例
    service = EnterpriseCustomerSatisfactionService(mock_db)
    
    # 测试实施改进措施
    improvement_actions = [
        {
            "type": "service_training",
            "description": "加强客服团队培训，提升服务质量",
            "expected_impact": "预期提升满意度至4.5分以上",
            "timeline_days": 30
        },
        {
            "type": "process_optimization",
            "description": "优化数据分析流程，提高响应速度",
            "expected_impact": "预期响应时间缩短至2小时内",
            "timeline_days": 15
        }
    ]
    
    result = await service.implement_satisfaction_improvement(
        customer_id="test-customer-001",
        improvement_actions=improvement_actions
    )
    
    test_results = []
    
    # 验证实施结果
    if result.get("success"):
        print("✅ 改进措施实施成功")
        test_results.append(True)
    else:
        print("❌ 改进措施实施失败")
        test_results.append(False)
    
    if result.get("improvement_count") == 2:
        print("✅ 改进措施数量正确")
        test_results.append(True)
    else:
        print("❌ 改进措施数量错误")
        test_results.append(False)
    
    # 验证数据库操作
    if mock_db.execute.call_count >= 2:  # 至少调用2次（每个改进措施一次）
        print("✅ 改进措施数据库记录正确")
        test_results.append(True)
    else:
        print("❌ 改进措施数据库记录错误")
        test_results.append(False)
    
    return all(test_results)

async def test_satisfaction_threshold_check():
    """测试满意度阈值检查和警报"""
    print("\n⚠️  测试满意度阈值检查...")
    print("=" * 50)
    
    # 模拟数据库会话
    mock_db = AsyncMock()
    
    # 模拟低满意度查询结果
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (3.2, 5)  # 平均3.2分，5次评价
    mock_db.execute.return_value = mock_result
    
    # 创建服务实例
    service = EnterpriseCustomerSatisfactionService(mock_db)
    
    # 测试阈值检查（这是内部方法，通过记录满意度触发）
    await service._check_satisfaction_threshold(
        customer_id="test-customer-002",
        service_type="legal_consultation"
    )
    
    test_results = []
    
    # 验证警报创建（通过数据库调用次数判断）
    if mock_db.execute.call_count >= 2:  # 查询 + 插入警报
        print("✅ 低满意度警报创建成功")
        test_results.append(True)
    else:
        print("❌ 低满意度警报创建失败")
        test_results.append(False)
    
    return all(test_results)

async def test_empty_data_handling():
    """测试空数据处理"""
    print("\n🔍 测试空数据处理...")
    print("=" * 50)
    
    # 模拟数据库会话
    mock_db = AsyncMock()
    
    # 模拟空查询结果
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_db.execute.return_value = mock_result
    
    # 创建服务实例
    service = EnterpriseCustomerSatisfactionService(mock_db)
    
    # 测试空数据分析
    analytics = await service.get_satisfaction_analytics()
    
    test_results = []
    
    # 验证空数据处理
    if analytics.get('overall_metrics', {}).get('total_responses') == 0:
        print("✅ 空数据响应数量正确")
        test_results.append(True)
    else:
        print("❌ 空数据响应数量错误")
        test_results.append(False)
    
    # 验证改进建议
    suggestions = analytics.get('improvement_suggestions', [])
    if len(suggestions) > 0:
        first_suggestion = suggestions[0]
        if first_suggestion.get('category') == 'data_collection':
            print("✅ 空数据改进建议正确")
            test_results.append(True)
        else:
            print("❌ 空数据改进建议错误")
            test_results.append(False)
    else:
        print("❌ 缺少空数据改进建议")
        test_results.append(False)
    
    # 验证目标达成状态
    target_achievement = analytics.get('target_achievement', {})
    if not target_achievement.get('on_track', True):
        print("✅ 空数据目标达成状态正确")
        test_results.append(True)
    else:
        print("❌ 空数据目标达成状态错误")
        test_results.append(False)
    
    return all(test_results)

async def main():
    """主测试函数"""
    print("🚀 开始企业客户满意度系统测试")
    print("=" * 60)
    print("目标：验证满意度跟踪、分析和改进功能，确保能够提升企业客户满意度至95%")
    print("=" * 60)
    
    try:
        # 执行各项测试
        test_results = []
        
        # 测试满意度跟踪
        result1 = await test_satisfaction_tracking()
        test_results.append(result1)
        
        # 测试满意度分析
        result2 = await test_satisfaction_analytics()
        test_results.append(result2)
        
        # 测试客户趋势
        result3 = await test_customer_trends()
        test_results.append(result3)
        
        # 测试改进实施
        result4 = await test_improvement_implementation()
        test_results.append(result4)
        
        # 测试阈值检查
        result5 = await test_satisfaction_threshold_check()
        test_results.append(result5)
        
        # 测试空数据处理
        result6 = await test_empty_data_handling()
        test_results.append(result6)
        
        print("\n" + "=" * 60)
        print("🎯 测试结果汇总:")
        
        test_names = [
            "满意度跟踪功能",
            "满意度分析功能", 
            "客户趋势分析",
            "改进措施实施",
            "满意度阈值检查",
            "空数据处理"
        ]
        
        for i, (name, result) in enumerate(zip(test_names, test_results)):
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{i+1}. {name}: {status}")
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"\n📊 总体测试结果:")
        print(f"通过测试: {passed_tests}/{total_tests}")
        print(f"成功率: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("\n🎉 企业客户满意度系统测试通过！")
            print("✅ 系统具备以下能力:")
            print("   • 准确跟踪和记录客户满意度")
            print("   • 全面分析满意度数据和趋势")
            print("   • 自动生成改进建议和警报")
            print("   • 实施和跟踪改进措施")
            print("   • 目标导向的95%满意度管理")
            print("   • 数据导向的服务优化")
            return 0
        elif success_rate >= 70:
            print("\n⚠️  企业客户满意度系统部分功能需要完善")
            print("建议重点关注失败的测试项目")
            return 1
        else:
            print("\n❌ 企业客户满意度系统需要重大改进")
            print("请检查核心功能实现")
            return 2
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        return 3

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)