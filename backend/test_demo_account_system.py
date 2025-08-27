#!/usr/bin/env python3
"""
演示账户系统测试脚本
验证演示数据隔离和安全性
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.demo_account_service import DemoAccountService
from app.services.demo_data_isolation_service import DemoDataIsolationService
from app.models.unified_auth import DemoAccount


class DemoAccountSystemTester:
    """演示账户系统测试器"""
    
    def __init__(self):
        # 数据库连接配置
        self.database_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/lawsker"
        self.engine = None
        self.session_factory = None
    
    async def setup(self):
        """设置测试环境"""
        try:
            self.engine = create_async_engine(
                self.database_url,
                echo=False,
                future=True
            )
            
            self.session_factory = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            print("✅ 数据库连接设置成功")
            return True
            
        except Exception as e:
            print(f"❌ 数据库连接设置失败: {e}")
            return False
    
    async def cleanup(self):
        """清理测试环境"""
        if self.engine:
            await self.engine.dispose()
            print("✅ 数据库连接已关闭")
    
    async def test_demo_account_creation(self):
        """测试演示账户创建"""
        print("\n🧪 测试演示账户创建...")
        
        try:
            async with self.session_factory() as db:
                demo_service = DemoAccountService(db)
                
                # 测试律师演示账户
                lawyer_demo = await demo_service.get_demo_account_data('lawyer')
                
                assert lawyer_demo['is_demo'] == True
                assert lawyer_demo['demo_type'] == 'lawyer'
                assert 'workspace_id' in lawyer_demo
                assert 'demo_data' in lawyer_demo
                assert 'session_id' in lawyer_demo
                
                print(f"  ✅ 律师演示账户创建成功: {lawyer_demo['workspace_id']}")
                
                # 测试用户演示账户
                user_demo = await demo_service.get_demo_account_data('user')
                
                assert user_demo['is_demo'] == True
                assert user_demo['demo_type'] == 'user'
                assert 'workspace_id' in user_demo
                assert 'demo_data' in user_demo
                
                print(f"  ✅ 用户演示账户创建成功: {user_demo['workspace_id']}")
                
                return True
                
        except Exception as e:
            print(f"  ❌ 演示账户创建测试失败: {e}")
            return False
    
    async def test_demo_data_isolation(self):
        """测试演示数据隔离"""
        print("\n🧪 测试演示数据隔离...")
        
        try:
            async with self.session_factory() as db:
                isolation_service = DemoDataIsolationService(db)
                
                # 测试演示案件数据
                demo_workspace_id = "demo-lawyer-test"
                cases_data = await isolation_service.get_isolated_demo_data(
                    demo_workspace_id, 'cases'
                )
                
                assert cases_data['is_demo'] == True
                assert 'data' in cases_data
                assert len(cases_data['data']) > 0
                
                # 验证案件数据包含演示标识
                for case in cases_data['data']:
                    assert case['id'].startswith('demo-case-')
                
                print(f"  ✅ 演示案件数据隔离正常，共 {len(cases_data['data'])} 条记录")
                
                # 测试演示用户数据
                users_data = await isolation_service.get_isolated_demo_data(
                    demo_workspace_id, 'users'
                )
                
                assert users_data['is_demo'] == True
                assert 'data' in users_data
                
                print(f"  ✅ 演示用户数据隔离正常，共 {len(users_data['data'])} 条记录")
                
                # 测试非演示工作台访问限制
                real_workspace_id = "ws-real-workspace"
                real_data = await isolation_service.get_isolated_demo_data(
                    real_workspace_id, 'cases'
                )
                
                # 应该返回错误信息而不是抛出异常
                if 'error' in real_data and '非演示工作台不能访问演示数据' in real_data['error']:
                    print("  ✅ 非演示工作台访问限制正常")
                else:
                    print("  ❌ 非演示工作台访问限制失败")
                    return False
                
                return True
                
        except Exception as e:
            print(f"  ❌ 演示数据隔离测试失败: {e}")
            return False
    
    async def test_demo_restrictions(self):
        """测试演示账户功能限制"""
        print("\n🧪 测试演示账户功能限制...")
        
        try:
            async with self.session_factory() as db:
                demo_service = DemoAccountService(db)
                
                # 测试律师演示账户限制
                lawyer_restrictions = await demo_service.get_demo_restrictions('lawyer')
                
                assert lawyer_restrictions['can_create_real_cases'] == False
                assert lawyer_restrictions['can_make_payments'] == False
                assert lawyer_restrictions['can_upload_files'] == False
                assert lawyer_restrictions['can_accept_cases'] == False
                
                print("  ✅ 律师演示账户功能限制正常")
                
                # 测试用户演示账户限制
                user_restrictions = await demo_service.get_demo_restrictions('user')
                
                assert user_restrictions['can_create_real_cases'] == False
                assert user_restrictions['can_make_payments'] == False
                assert user_restrictions['can_publish_cases'] == False
                
                print("  ✅ 用户演示账户功能限制正常")
                
                # 测试操作验证
                demo_workspace_id = "demo-lawyer-test"
                
                # 测试被禁止的操作
                forbidden_result = await demo_service.validate_demo_action(
                    demo_workspace_id, 'create_case'
                )
                
                assert forbidden_result['allowed'] == False
                assert 'reason' in forbidden_result
                
                print("  ✅ 危险操作拦截正常")
                
                return True
                
        except Exception as e:
            print(f"  ❌ 演示账户功能限制测试失败: {e}")
            return False
    
    async def test_demo_workspace_detection(self):
        """测试演示工作台检测"""
        print("\n🧪 测试演示工作台检测...")
        
        try:
            async with self.session_factory() as db:
                demo_service = DemoAccountService(db)
                
                # 测试演示工作台ID检测
                demo_workspace_ids = [
                    "demo-lawyer-001",
                    "demo-user-001",
                    "demo-test-123"
                ]
                
                for workspace_id in demo_workspace_ids:
                    is_demo = await demo_service.is_demo_workspace(workspace_id)
                    if workspace_id.startswith('demo-'):
                        assert is_demo == True
                        print(f"  ✅ 演示工作台检测正常: {workspace_id}")
                
                # 测试真实工作台ID检测
                real_workspace_ids = [
                    "ws-real-123",
                    "user-workspace-456",
                    "lawyer-workspace-789"
                ]
                
                for workspace_id in real_workspace_ids:
                    is_demo = await demo_service.is_demo_workspace(workspace_id)
                    assert is_demo == False
                    print(f"  ✅ 真实工作台检测正常: {workspace_id}")
                
                return True
                
        except Exception as e:
            print(f"  ❌ 演示工作台检测测试失败: {e}")
            return False
    
    async def test_demo_data_refresh(self):
        """测试演示数据刷新"""
        print("\n🧪 测试演示数据刷新...")
        
        try:
            async with self.session_factory() as db:
                demo_service = DemoAccountService(db)
                
                # 获取演示账户
                demo_data = await demo_service.get_demo_account_data('lawyer')
                
                # 检查数据是否包含时间相关信息
                demo_content = demo_data['demo_data']
                
                if 'recent_activities' in demo_content:
                    activities = demo_content['recent_activities']
                    assert len(activities) > 0
                    
                    # 检查活动时间是否为相对时间
                    for activity in activities:
                        assert 'time' in activity
                        assert any(keyword in activity['time'] for keyword in ['小时前', '天前'])
                    
                    print("  ✅ 演示数据时间刷新正常")
                
                if 'demo_cases' in demo_content:
                    cases = demo_content['demo_cases']
                    assert len(cases) > 0
                    
                    # 检查案件时间是否合理
                    for case in cases:
                        assert 'created_at' in case
                        created_at = datetime.fromisoformat(case['created_at'].replace('Z', '+00:00'))
                        now = datetime.now()
                        
                        # 创建时间应该在合理范围内
                        time_diff = now - created_at.replace(tzinfo=None)
                        assert time_diff.days <= 30  # 不超过30天
                    
                    print("  ✅ 演示案件时间刷新正常")
                
                return True
                
        except Exception as e:
            print(f"  ❌ 演示数据刷新测试失败: {e}")
            return False
    
    async def test_demo_session_management(self):
        """测试演示会话管理"""
        print("\n🧪 测试演示会话管理...")
        
        try:
            async with self.session_factory() as db:
                demo_service = DemoAccountService(db)
                
                # 生成演示会话ID
                session_id1 = demo_service.generate_demo_session_id()
                session_id2 = demo_service.generate_demo_session_id()
                
                assert session_id1 != session_id2
                assert session_id1.startswith('demo-session-')
                assert session_id2.startswith('demo-session-')
                
                print(f"  ✅ 演示会话ID生成正常: {session_id1}")
                
                # 测试演示活动记录
                await demo_service.log_demo_activity(
                    "demo-test-workspace",
                    "test_action",
                    {"test": "data"}
                )
                
                print("  ✅ 演示活动记录正常")
                
                return True
                
        except Exception as e:
            print(f"  ❌ 演示会话管理测试失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始演示账户系统测试")
        print("=" * 50)
        
        if not await self.setup():
            return False
        
        tests = [
            self.test_demo_account_creation,
            self.test_demo_data_isolation,
            self.test_demo_restrictions,
            self.test_demo_workspace_detection,
            self.test_demo_data_refresh,
            self.test_demo_session_management
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if await test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ 测试执行异常: {e}")
                failed += 1
        
        await self.cleanup()
        
        print("\n" + "=" * 50)
        print(f"📊 测试结果: 通过 {passed} 个，失败 {failed} 个")
        
        if failed == 0:
            print("🎉 所有测试通过！演示账户系统运行正常")
            return True
        else:
            print("⚠️  部分测试失败，请检查系统配置")
            return False


async def main():
    """主函数"""
    tester = DemoAccountSystemTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✅ 演示账户系统验证完成，系统正常运行")
        sys.exit(0)
    else:
        print("\n❌ 演示账户系统验证失败，请检查配置")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())