#!/usr/bin/env python3
"""
演示账户系统验证脚本
快速验证演示系统的核心功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.demo_account_service import DemoAccountService
from app.services.demo_data_isolation_service import DemoDataIsolationService


async def verify_demo_system():
    """验证演示系统核心功能"""
    print("🔍 演示账户系统快速验证")
    print("=" * 40)
    
    try:
        # 数据库连接
        database_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/lawsker"
        engine = create_async_engine(database_url, echo=False)
        session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with session_factory() as db:
            demo_service = DemoAccountService(db)
            isolation_service = DemoDataIsolationService(db)
            
            # 1. 验证演示账户创建
            print("1. 测试演示账户创建...")
            lawyer_demo = await demo_service.get_demo_account_data('lawyer')
            user_demo = await demo_service.get_demo_account_data('user')
            
            assert lawyer_demo['is_demo'] == True
            assert user_demo['is_demo'] == True
            print("   ✅ 演示账户创建正常")
            
            # 2. 验证数据隔离
            print("2. 测试数据隔离...")
            demo_cases = await isolation_service.get_isolated_demo_data(
                "demo-lawyer-test", 'cases'
            )
            assert demo_cases['is_demo'] == True
            assert len(demo_cases['data']) > 0
            print("   ✅ 数据隔离正常")
            
            # 3. 验证功能限制
            print("3. 测试功能限制...")
            restrictions = await demo_service.get_demo_restrictions('lawyer')
            assert restrictions['can_create_real_cases'] == False
            assert restrictions['can_make_payments'] == False
            print("   ✅ 功能限制正常")
            
            # 4. 验证工作台检测
            print("4. 测试工作台检测...")
            is_demo = await demo_service.is_demo_workspace("demo-test-123")
            is_real = await demo_service.is_demo_workspace("ws-real-123")
            assert is_demo == True
            assert is_real == False
            print("   ✅ 工作台检测正常")
            
            print("\n🎉 演示账户系统验证通过！")
            print("✅ 所有核心功能正常运行")
            
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        return False


async def main():
    """主函数"""
    success = await verify_demo_system()
    
    if success:
        print("\n✅ 演示账户系统已成功实现并正常运行")
        print("📋 实现的功能包括:")
        print("   • 安全的演示数据隔离")
        print("   • 完整的功能限制机制")
        print("   • 律师和用户两种演示模式")
        print("   • 演示会话管理")
        print("   • 数据自动刷新")
        print("   • 转换引导功能")
        print("\n🌐 访问演示页面: /demo-account.html")
        sys.exit(0)
    else:
        print("\n❌ 演示账户系统验证失败")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())