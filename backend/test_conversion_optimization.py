#!/usr/bin/env python3
"""
转化率优化系统测试脚本
Test script for conversion optimization system

Tests the implementation of user registration conversion rate optimization
to achieve the 40% improvement target.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.conversion_optimization_service import ConversionOptimizationService, get_conversion_optimization_config
from sqlalchemy.orm import Session


class ConversionOptimizationTester:
    """转化率优化测试器"""
    
    def __init__(self):
        self.db = None
        self.service = None
        self.test_results = []
    
    async def setup(self):
        """设置测试环境"""
        # For testing, we'll create a mock service without database dependency
        self.service = ConversionOptimizationService(None)
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始转化率优化系统测试...")
        print("=" * 60)
        
        # Setup test environment
        await self.setup()
        
        # Test 1: Configuration
        await self.test_optimization_config()
        
        # Test 2: Event Tracking
        await self.test_event_tracking()
        
        # Test 3: Metrics Calculation
        await self.test_metrics_calculation()
        
        # Test 4: Recommendations
        await self.test_recommendations()
        
        # Test 5: Funnel Analysis
        await self.test_funnel_analysis()
        
        # Test 6: Conversion Report
        await self.test_conversion_report()
        
        # Test 7: A/B Testing
        await self.test_ab_testing()
        
        # Test 8: Simulation
        await self.test_conversion_simulation()
        
        # Summary
        self.print_test_summary()
    
    async def test_optimization_config(self):
        """测试优化配置"""
        print("\n📋 测试 1: 优化配置")
        
        try:
            config = get_conversion_optimization_config()
            
            # Verify required config keys
            required_keys = [
                'target_improvement',
                'baseline_conversion_rate',
                'target_conversion_rate',
                'demo_conversion_target',
                'ab_test_variants',
                'tracking_events'
            ]
            
            for key in required_keys:
                assert key in config, f"Missing config key: {key}"
            
            # Verify target improvement is 40%
            assert config['target_improvement'] == 40.0, "Target improvement should be 40%"
            
            # Verify target conversion rate calculation
            baseline = config['baseline_conversion_rate']
            target = config['target_conversion_rate']
            expected_target = baseline * 1.4  # 40% improvement
            assert abs(target - expected_target) < 0.1, f"Target rate calculation incorrect: {target} vs {expected_target}"
            
            print("✅ 优化配置测试通过")
            print(f"   - 目标改进: {config['target_improvement']}%")
            print(f"   - 基线转化率: {config['baseline_conversion_rate']}%")
            print(f"   - 目标转化率: {config['target_conversion_rate']}%")
            print(f"   - A/B测试变体: {len(config['ab_test_variants'])}个")
            print(f"   - 跟踪事件: {len(config['tracking_events'])}个")
            
            self.test_results.append(("优化配置", True, "配置正确"))
            
        except Exception as e:
            print(f"❌ 优化配置测试失败: {str(e)}")
            self.test_results.append(("优化配置", False, str(e)))
    
    async def test_event_tracking(self):
        """测试事件跟踪"""
        print("\n📊 测试 2: 事件跟踪")
        
        try:
            # Test tracking different events
            events_to_test = [
                ('page_load', None, 'test_session_1', {'source': 'direct'}),
                ('demo_start', None, 'test_session_1', {'demo_type': 'user'}),
                ('registration_attempt', 'test_user_1', 'test_session_1', {'identity_type': 'user'}),
                ('registration_success', 'test_user_1', 'test_session_1', {'identity_type': 'user'})
            ]
            
            for event_type, user_id, session_id, metadata in events_to_test:
                result = await self.service.track_conversion_event(
                    event_type=event_type,
                    user_id=user_id,
                    session_id=session_id,
                    metadata=metadata
                )
                
                assert result['event_type'] == event_type, f"Event type mismatch: {result['event_type']}"
                assert result['user_id'] == user_id, f"User ID mismatch: {result['user_id']}"
                assert result['session_id'] == session_id, f"Session ID mismatch: {result['session_id']}"
                assert result['metadata'] == metadata, f"Metadata mismatch: {result['metadata']}"
            
            print("✅ 事件跟踪测试通过")
            print(f"   - 成功跟踪 {len(events_to_test)} 个事件")
            print("   - 事件类型: page_load, demo_start, registration_attempt, registration_success")
            
            self.test_results.append(("事件跟踪", True, f"跟踪了{len(events_to_test)}个事件"))
            
        except Exception as e:
            print(f"❌ 事件跟踪测试失败: {str(e)}")
            self.test_results.append(("事件跟踪", False, str(e)))
    
    async def test_metrics_calculation(self):
        """测试指标计算"""
        print("\n📈 测试 3: 指标计算")
        
        try:
            # Get metrics for the last 30 days
            metrics = await self.service.get_conversion_metrics()
            
            # Verify metrics structure
            required_keys = ['period', 'metrics', 'targets']
            for key in required_keys:
                assert key in metrics, f"Missing metrics key: {key}"
            
            # Verify metrics data
            metrics_data = metrics['metrics']
            required_metrics = [
                'total_visitors',
                'total_registrations',
                'demo_users',
                'demo_conversions',
                'registration_conversion_rate',
                'demo_conversion_rate'
            ]
            
            for metric in required_metrics:
                assert metric in metrics_data, f"Missing metric: {metric}"
                assert isinstance(metrics_data[metric], (int, float)), f"Invalid metric type: {metric}"
            
            # Verify targets
            targets = metrics['targets']
            assert 'registration_rate_target' in targets, "Missing registration rate target"
            assert 'demo_conversion_target' in targets, "Missing demo conversion target"
            
            print("✅ 指标计算测试通过")
            print(f"   - 总访问者: {metrics_data['total_visitors']}")
            print(f"   - 总注册数: {metrics_data['total_registrations']}")
            print(f"   - 当前转化率: {metrics_data['registration_conversion_rate']}%")
            print(f"   - 目标转化率: {targets['registration_rate_target']}%")
            print(f"   - 演示转化率: {metrics_data['demo_conversion_rate']}%")
            
            self.test_results.append(("指标计算", True, f"转化率: {metrics_data['registration_conversion_rate']}%"))
            
        except Exception as e:
            print(f"❌ 指标计算测试失败: {str(e)}")
            self.test_results.append(("指标计算", False, str(e)))
    
    async def test_recommendations(self):
        """测试优化建议"""
        print("\n💡 测试 4: 优化建议")
        
        try:
            recommendations = await self.service.get_optimization_recommendations()
            
            assert isinstance(recommendations, list), "Recommendations should be a list"
            
            for rec in recommendations:
                required_keys = ['type', 'priority', 'title', 'description', 'actions']
                for key in required_keys:
                    assert key in rec, f"Missing recommendation key: {key}"
                
                assert rec['priority'] in ['high', 'medium', 'low'], f"Invalid priority: {rec['priority']}"
                assert isinstance(rec['actions'], list), "Actions should be a list"
                assert len(rec['actions']) > 0, "Actions list should not be empty"
            
            print("✅ 优化建议测试通过")
            print(f"   - 生成了 {len(recommendations)} 条建议")
            
            for i, rec in enumerate(recommendations[:3], 1):  # Show first 3
                print(f"   {i}. [{rec['priority'].upper()}] {rec['title']}")
                print(f"      {rec['description']}")
            
            self.test_results.append(("优化建议", True, f"生成了{len(recommendations)}条建议"))
            
        except Exception as e:
            print(f"❌ 优化建议测试失败: {str(e)}")
            self.test_results.append(("优化建议", False, str(e)))
    
    async def test_funnel_analysis(self):
        """测试漏斗分析"""
        print("\n🔍 测试 5: 漏斗分析")
        
        try:
            analysis = await self.service.get_registration_funnel_analysis()
            
            # Verify analysis structure
            required_keys = ['funnel_data', 'conversion_rates', 'overall_conversion_rate', 'bottlenecks']
            for key in required_keys:
                assert key in analysis, f"Missing analysis key: {key}"
            
            # Verify funnel data
            funnel_data = analysis['funnel_data']
            assert isinstance(funnel_data, dict), "Funnel data should be a dict"
            assert len(funnel_data) > 0, "Funnel data should not be empty"
            
            # Verify conversion rates
            conversion_rates = analysis['conversion_rates']
            assert isinstance(conversion_rates, dict), "Conversion rates should be a dict"
            
            # Verify overall rate
            overall_rate = analysis['overall_conversion_rate']
            assert isinstance(overall_rate, (int, float)), "Overall rate should be numeric"
            assert 0 <= overall_rate <= 100, "Overall rate should be between 0 and 100"
            
            # Verify bottlenecks
            bottlenecks = analysis['bottlenecks']
            assert isinstance(bottlenecks, list), "Bottlenecks should be a list"
            
            print("✅ 漏斗分析测试通过")
            print(f"   - 整体转化率: {overall_rate}%")
            print(f"   - 漏斗步骤: {len(funnel_data)}个")
            print(f"   - 识别瓶颈: {len(bottlenecks)}个")
            
            # Show funnel steps
            for step, value in list(funnel_data.items())[:3]:
                print(f"   - {step.replace('_', ' ').title()}: {value}")
            
            self.test_results.append(("漏斗分析", True, f"整体转化率: {overall_rate}%"))
            
        except Exception as e:
            print(f"❌ 漏斗分析测试失败: {str(e)}")
            self.test_results.append(("漏斗分析", False, str(e)))
    
    async def test_conversion_report(self):
        """测试转化率报告"""
        print("\n📋 测试 6: 转化率报告")
        
        try:
            report = await self.service.generate_conversion_report()
            
            # Verify report structure
            required_keys = [
                'report_date',
                'current_month',
                'last_month',
                'improvement',
                'recommendations',
                'next_actions'
            ]
            
            for key in required_keys:
                assert key in report, f"Missing report key: {key}"
            
            # Verify improvement data
            improvement = report['improvement']
            required_improvement_keys = ['percentage', 'target_achieved', 'target_progress']
            for key in required_improvement_keys:
                assert key in improvement, f"Missing improvement key: {key}"
            
            # Verify recommendations
            recommendations = report['recommendations']
            assert isinstance(recommendations, list), "Recommendations should be a list"
            
            # Verify next actions
            next_actions = report['next_actions']
            assert isinstance(next_actions, list), "Next actions should be a list"
            assert len(next_actions) > 0, "Next actions should not be empty"
            
            print("✅ 转化率报告测试通过")
            print(f"   - 报告日期: {report['report_date'][:10]}")
            print(f"   - 改进百分比: {improvement['percentage']}%")
            print(f"   - 目标达成: {'是' if improvement['target_achieved'] else '否'}")
            print(f"   - 目标进度: {improvement['target_progress']:.1f}%")
            print(f"   - 建议数量: {len(recommendations)}")
            print(f"   - 下一步行动: {len(next_actions)}项")
            
            self.test_results.append(("转化率报告", True, f"改进: {improvement['percentage']}%"))
            
        except Exception as e:
            print(f"❌ 转化率报告测试失败: {str(e)}")
            self.test_results.append(("转化率报告", False, str(e)))
    
    async def test_ab_testing(self):
        """测试A/B测试"""
        print("\n🧪 测试 7: A/B测试")
        
        try:
            # Test A/B test result tracking
            test_cases = [
                ('registration_flow_test', 'original', 'user_1', False, {'time_spent': 120}),
                ('registration_flow_test', 'streamlined_2_step', 'user_2', True, {'time_spent': 80}),
                ('demo_prominence_test', 'demo_prominent', 'user_3', True, {'demo_used': True}),
                ('trust_indicators_test', 'trust_indicators', 'user_4', True, {'trust_score': 8})
            ]
            
            for test_name, variant, user_id, converted, metadata in test_cases:
                result = await self.service.track_ab_test_result(
                    test_name=test_name,
                    variant=variant,
                    user_id=user_id,
                    converted=converted,
                    metadata=metadata
                )
                
                assert result['test_name'] == test_name, f"Test name mismatch: {result['test_name']}"
                assert result['variant'] == variant, f"Variant mismatch: {result['variant']}"
                assert result['user_id'] == user_id, f"User ID mismatch: {result['user_id']}"
                assert result['converted'] == converted, f"Converted mismatch: {result['converted']}"
            
            print("✅ A/B测试跟踪通过")
            print(f"   - 测试了 {len(test_cases)} 个A/B测试结果")
            print("   - 测试类型: registration_flow, demo_prominence, trust_indicators")
            
            # Calculate conversion rates by variant
            variants_tested = {}
            for test_name, variant, user_id, converted, metadata in test_cases:
                if variant not in variants_tested:
                    variants_tested[variant] = {'total': 0, 'converted': 0}
                variants_tested[variant]['total'] += 1
                if converted:
                    variants_tested[variant]['converted'] += 1
            
            print("   - 变体转化率:")
            for variant, data in variants_tested.items():
                rate = (data['converted'] / data['total']) * 100 if data['total'] > 0 else 0
                print(f"     {variant}: {rate:.1f}% ({data['converted']}/{data['total']})")
            
            self.test_results.append(("A/B测试", True, f"测试了{len(test_cases)}个结果"))
            
        except Exception as e:
            print(f"❌ A/B测试失败: {str(e)}")
            self.test_results.append(("A/B测试", False, str(e)))
    
    async def test_conversion_simulation(self):
        """测试转化率模拟"""
        print("\n🎯 测试 8: 转化率模拟")
        
        try:
            # Simulate conversion improvement calculation
            from app.services.conversion_optimization_service import calculate_conversion_improvement
            
            # Test cases
            test_cases = [
                (10.0, 14.0, 40.0),  # 40% improvement
                (8.5, 12.75, 50.0),  # 50% improvement
                (12.0, 15.6, 30.0),  # 30% improvement
            ]
            
            for baseline, current, expected_improvement in test_cases:
                actual_improvement = calculate_conversion_improvement(baseline, current)
                assert abs(actual_improvement - expected_improvement) < 0.1, \
                    f"Improvement calculation error: {actual_improvement} vs {expected_improvement}"
            
            print("✅ 转化率模拟测试通过")
            print("   - 改进计算公式正确")
            print("   - 测试用例:")
            for baseline, current, expected in test_cases:
                actual = calculate_conversion_improvement(baseline, current)
                print(f"     {baseline}% → {current}% = {actual:.1f}% 改进")
            
            # Test target achievement
            config = get_conversion_optimization_config()
            baseline = config['baseline_conversion_rate']
            target = config['target_conversion_rate']
            target_improvement = calculate_conversion_improvement(baseline, target)
            
            print(f"   - 目标改进: {baseline}% → {target}% = {target_improvement:.1f}%")
            
            self.test_results.append(("转化率模拟", True, f"目标改进: {target_improvement:.1f}%"))
            
        except Exception as e:
            print(f"❌ 转化率模拟测试失败: {str(e)}")
            self.test_results.append(("转化率模拟", False, str(e)))
    
    def print_test_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("📊 转化率优化系统测试总结")
        print("=" * 60)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        print(f"总测试数: {total}")
        print(f"通过测试: {passed}")
        print(f"失败测试: {total - passed}")
        print(f"成功率: {(passed/total)*100:.1f}%")
        
        print("\n详细结果:")
        for test_name, success, details in self.test_results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"  {status} {test_name}: {details}")
        
        if passed == total:
            print(f"\n🎉 所有测试通过！转化率优化系统实施成功！")
            print("\n📈 系统功能:")
            print("  ✅ 事件跟踪和分析")
            print("  ✅ 转化率指标计算")
            print("  ✅ 优化建议生成")
            print("  ✅ 注册漏斗分析")
            print("  ✅ A/B测试支持")
            print("  ✅ 转化率报告")
            print("  ✅ 改进模拟计算")
            
            print("\n🎯 优化目标:")
            config = get_conversion_optimization_config()
            print(f"  - 基线转化率: {config['baseline_conversion_rate']}%")
            print(f"  - 目标转化率: {config['target_conversion_rate']}%")
            print(f"  - 目标改进: {config['target_improvement']}%")
            
            print("\n🚀 下一步行动:")
            print("  1. 部署优化版注册页面 (unified-auth-optimized.html)")
            print("  2. 启用转化率监控仪表盘")
            print("  3. 开始A/B测试不同的注册流程")
            print("  4. 监控转化率改进进度")
            print("  5. 根据数据调整优化策略")
        else:
            print(f"\n⚠️  有 {total - passed} 个测试失败，请检查实施状态")


async def main():
    """主函数"""
    tester = ConversionOptimizationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())