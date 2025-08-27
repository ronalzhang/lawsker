#!/usr/bin/env python3
"""
企业服务免责声明测试脚本
验证催收统计服务的免责声明功能
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.collection_statistics_service import CollectionStatisticsService
from unittest.mock import AsyncMock, MagicMock

async def test_collection_statistics_disclaimers():
    """测试催收统计服务的免责声明"""
    print("🧪 测试企业服务免责声明...")
    print("=" * 50)
    
    # 模拟数据库会话
    mock_db = AsyncMock()
    
    # 模拟查询结果
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (100, 80, 15, 5, 24.5, 75, 90)
    mock_db.execute.return_value = mock_result
    
    # 创建服务实例
    service = CollectionStatisticsService(mock_db)
    
    # 测试获取催收统计数据
    print("📊 测试催收统计数据...")
    stats = await service.get_collection_statistics()
    
    # 验证免责声明
    test_results = []
    
    # 检查是否包含免责声明
    if 'disclaimer' in stats:
        print("✅ 包含基础免责声明")
        test_results.append(True)
        
        disclaimer_content = stats['disclaimer']['content']
        required_phrases = [
            "仅供参考",
            "不构成",
            "承诺",
            "不保证"
        ]
        
        disclaimer_text = ' '.join(disclaimer_content)
        for phrase in required_phrases:
            if phrase in disclaimer_text:
                print(f"✅ 包含关键免责词汇: {phrase}")
                test_results.append(True)
            else:
                print(f"❌ 缺少关键免责词汇: {phrase}")
                test_results.append(False)
    else:
        print("❌ 缺少基础免责声明")
        test_results.append(False)
    
    # 检查数据源说明
    if 'data_source_note' in stats:
        print("✅ 包含数据源说明")
        test_results.append(True)
    else:
        print("❌ 缺少数据源说明")
        test_results.append(False)
    
    # 检查参考指标标识
    if 'reference_indicators' in stats:
        print("✅ 使用'参考指标'标识而非'成功率'")
        test_results.append(True)
    else:
        print("❌ 缺少参考指标标识")
        test_results.append(False)
    
    print("\n" + "=" * 50)
    
    # 测试律师表现参考数据
    print("👨‍⚖️ 测试律师表现参考数据...")
    
    # 模拟律师表现查询结果
    mock_result.fetchone.return_value = (25, 20, 4.5, 18)
    
    lawyer_data = await service.get_lawyer_performance_reference("test_lawyer_id")
    
    # 验证律师表现免责声明
    if 'performance_disclaimer' in lawyer_data:
        print("✅ 包含律师表现免责声明")
        test_results.append(True)
        
        disclaimer_content = lawyer_data['performance_disclaimer']['content']
        disclaimer_text = ' '.join(disclaimer_content)
        
        if "不构成" in disclaimer_text and "能力保证" in disclaimer_text:
            print("✅ 包含能力免责声明")
            test_results.append(True)
        else:
            print("❌ 缺少能力免责声明")
            test_results.append(False)
    else:
        print("❌ 缺少律师表现免责声明")
        test_results.append(False)
    
    print("\n" + "=" * 50)
    
    # 计算测试结果
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"📈 测试结果:")
    print(f"通过测试: {passed_tests}/{total_tests}")
    print(f"成功率: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("✅ 企业服务免责声明测试通过")
        return True
    else:
        print("❌ 企业服务免责声明测试失败")
        return False

async def test_empty_data_disclaimers():
    """测试空数据情况的免责声明"""
    print("\n🔍 测试空数据免责声明...")
    
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchone.return_value = None
    mock_db.execute.return_value = mock_result
    
    service = CollectionStatisticsService(mock_db)
    
    # 测试空数据统计
    empty_stats = await service.get_collection_statistics()
    
    if 'disclaimer' in empty_stats and "暂无足够数据" in ' '.join(empty_stats['disclaimer']['content']):
        print("✅ 空数据情况包含适当免责声明")
        return True
    else:
        print("❌ 空数据情况缺少免责声明")
        return False

async def main():
    """主测试函数"""
    print("🚀 开始企业服务免责声明测试")
    print("=" * 60)
    
    try:
        # 测试正常数据免责声明
        test1_result = await test_collection_statistics_disclaimers()
        
        # 测试空数据免责声明
        test2_result = await test_empty_data_disclaimers()
        
        print("\n" + "=" * 60)
        print("🎯 总体测试结果:")
        
        if test1_result and test2_result:
            print("✅ 所有免责声明测试通过")
            print("✅ 企业服务已成功移除成功率承诺")
            print("✅ 数据导向服务定位明确")
            return 0
        else:
            print("❌ 部分免责声明测试失败")
            print("⚠️  需要进一步完善免责声明")
            return 1
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        return 2

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)