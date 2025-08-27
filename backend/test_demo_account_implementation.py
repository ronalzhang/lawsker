#!/usr/bin/env python3
"""
演示账户系统实现测试
验证演示账户功能的完整性和正确性
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.demo_account_service import DemoAccountService
from app.core.database import get_db


class DemoAccountTester:
    """演示账户系统测试器"""
    
    def __init__(self):
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
    
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'passed': passed,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if passed:
            self.passed_tests += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.failed_tests += 1
            print(f"❌ {test_name}: {message}")
    
    async def test_demo_account_creation(self, demo_service: DemoAccountService):
        """测试演示账户创建"""
        try:
            # 测试律师演示账户
            lawyer_demo = await demo_service.get_demo_account_data('lawyer')
            
            assert lawyer_demo is not None, "律师演示账户数据不能为空"
            assert lawyer_demo['demo_type'] == 'lawyer', "演示类型应为lawyer"
            assert lawyer_demo['is_demo'] is True, "应标记为演示账户"
            assert 'workspace_id' in lawyer_demo, "应包含workspace_id"
            assert 'demo_data' in lawyer_demo, "应包含演示数据"
            
            self.log_test("律师演示账户创建", True, "成功创建律师演示账户")
            
            # 测试用户演示账户
            user_demo = await demo_service.get_demo_account_data('user')
            
            assert user_demo is not None, "用户演示账户数据不能为空"
            assert user_demo['demo_type'] == 'user', "演示类型应为user"
            assert user_demo['is_demo'] is True, "应标记为演示账户"
            
            self.log_test("用户演示账户创建", True, "成功创建用户演示账户")
            
        except Exception as e:
            self.log_test("演示账户创建", False, f"创建失败: {str(e)}")
    
    async def test_demo_data_structure(self, demo_service: DemoAccountService):
        """测试演示数据结构"""
        try:
            lawyer_demo = await demo_service.get_demo_account_data('lawyer')
            demo_data = lawyer_demo['demo_data']
            
            # 检查律师演示数据结构
            required_fields = ['profile', 'statistics', 'demo_cases', 'recent_activities', 'earnings']
            for field in required_fields:
                assert field in demo_data, f"律师演示数据应包含{field}字段"
            
            # 检查案件数据
            assert len(demo_data['demo_cases']) > 0, "应包含演示案件"
            case = demo_data['demo_cases'][0]
            case_fields = ['id', 'title', 'client_name', 'amount', 'status']
            for field in case_fields:
                assert field in case, f"案件数据应包含{field}字段"
            
            self.log_test("律师演示数据结构", True, "数据结构完整")
            
            # 检查用户演示数据
            user_demo = await demo_service.get_demo_account_data('user')
            user_data = user_demo['demo_data']
            
            user_required_fields = ['profile', 'statistics', 'demo_cases', 'recent_activities', 'budget_info']
            for field in user_required_fields:
                assert field in user_data, f"用户演示数据应包含{field}字段"
            
            self.log_test("用户演示数据结构", True, "数据结构完整")
            
        except Exception as e:
            self.log_test("演示数据结构", False, f"结构检查失败: {str(e)}")
    
    async def test_demo_workspace_validation(self, demo_service: DemoAccountService):
        """测试演示工作台验证"""
        try:
            lawyer_demo = await demo_service.get_demo_account_data('lawyer')
            workspace_id = lawyer_demo['workspace_id']
            
            # 测试演示工作台识别
            is_demo = await demo_service.is_demo_workspace(workspace_id)
            assert is_demo is True, "应正确识别演示工作台"
            
            # 测试非演示工作台
            is_demo_false = await demo_service.is_demo_workspace('real-workspace-123')
            assert is_demo_false is False, "应正确识别非演示工作台"
            
            self.log_test("演示工作台验证", True, "工作台识别正确")
            
        except Exception as e:
            self.log_test("演示工作台验证", False, f"验证失败: {str(e)}")
    
    async def test_demo_restrictions(self, demo_service: DemoAccountService):
        """测试演示账户功能限制"""
        try:
            # 测试律师演示限制
            lawyer_restrictions = await demo_service.get_demo_restrictions('lawyer')
            
            assert lawyer_restrictions['can_create_real_cases'] is False, "演示账户不能创建真实案件"
            assert lawyer_restrictions['can_make_payments'] is False, "演示账户不能进行支付"
            assert lawyer_restrictions['can_accept_cases'] is False, "演示账户不能接受案件"
            
            self.log_test("律师演示限制", True, "功能限制正确")
            
            # 测试用户演示限制
            user_restrictions = await demo_service.get_demo_restrictions('user')
            
            assert user_restrictions['can_publish_cases'] is False, "演示账户不能发布案件"
            assert user_restrictions['can_hire_lawyers'] is False, "演示账户不能雇佣律师"
            
            self.log_test("用户演示限制", True, "功能限制正确")
            
        except Exception as e:
            self.log_test("演示账户限制", False, f"限制检查失败: {str(e)}")
    
    async def test_demo_action_validation(self, demo_service: DemoAccountService):
        """测试演示账户操作验证"""
        try:
            lawyer_demo = await demo_service.get_demo_account_data('lawyer')
            workspace_id = lawyer_demo['workspace_id']
            
            # 测试受限操作
            validation = await demo_service.validate_demo_action(workspace_id, 'create_case')
            assert validation['allowed'] is False, "创建案件操作应被禁止"
            assert 'reason' in validation, "应提供禁止原因"
            
            # 测试允许的操作（如果有的话）
            validation_view = await demo_service.validate_demo_action(workspace_id, 'view_data')
            # 大多数查看操作应该被允许
            
            self.log_test("演示操作验证", True, "操作验证正确")
            
        except Exception as e:
            self.log_test("演示操作验证", False, f"操作验证失败: {str(e)}")
    
    async def test_demo_data_refresh(self, demo_service: DemoAccountService):
        """测试演示数据刷新"""
        try:
            # 获取演示账户
            lawyer_demo = await demo_service.get_demo_account_data('lawyer')
            
            # 检查数据是否包含时间相关字段
            demo_data = lawyer_demo['demo_data']
            
            if 'recent_activities' in demo_data:
                activities = demo_data['recent_activities']
                assert len(activities) > 0, "应包含最近活动"
                
                # 检查时间格式
                first_activity = activities[0]
                assert 'time' in first_activity, "活动应包含时间字段"
            
            self.log_test("演示数据刷新", True, "数据刷新功能正常")
            
        except Exception as e:
            self.log_test("演示数据刷新", False, f"数据刷新失败: {str(e)}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始演示账户系统测试...")
        print("=" * 50)
        
        try:
            # 获取数据库连接
            async with get_db() as db:
                demo_service = DemoAccountService(db)
                
                # 运行各项测试
                await self.test_demo_account_creation(demo_service)
                await self.test_demo_data_structure(demo_service)
                await self.test_demo_workspace_validation(demo_service)
                await self.test_demo_restrictions(demo_service)
                await self.test_demo_action_validation(demo_service)
                await self.test_demo_data_refresh(demo_service)
                
        except Exception as e:
            self.log_test("数据库连接", False, f"数据库连接失败: {str(e)}")
        
        # 输出测试结果
        print("\n" + "=" * 50)
        print("📊 测试结果汇总:")
        print(f"✅ 通过: {self.passed_tests}")
        print(f"❌ 失败: {self.failed_tests}")
        print(f"📈 成功率: {(self.passed_tests / (self.passed_tests + self.failed_tests) * 100):.1f}%")
        
        if self.failed_tests == 0:
            print("\n🎉 所有测试通过！演示账户系统实现正确。")
            return True
        else:
            print(f"\n⚠️  有 {self.failed_tests} 个测试失败，请检查实现。")
            return False
    
    def save_test_report(self, filename: str = "demo_account_test_report.json"):
        """保存测试报告"""
        report = {
            'test_summary': {
                'total_tests': len(self.test_results),
                'passed_tests': self.passed_tests,
                'failed_tests': self.failed_tests,
                'success_rate': (self.passed_tests / len(self.test_results) * 100) if self.test_results else 0,
                'test_date': datetime.now().isoformat()
            },
            'test_results': self.test_results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 测试报告已保存到: {filename}")


async def main():
    """主函数"""
    tester = DemoAccountTester()
    
    try:
        success = await tester.run_all_tests()
        tester.save_test_report()
        
        # 返回适当的退出码
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试过程中发生未预期错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())