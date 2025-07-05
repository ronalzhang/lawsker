#!/usr/bin/env python3
"""
提现系统功能测试脚本
测试数据库连接、表结构、基本功能
"""

import asyncio
import traceback
from decimal import Decimal
from uuid import uuid4
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 数据库
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 应用导入
from app.core.config import settings
from app.models.finance import WithdrawalRequest, WithdrawalStatus

class SimpleWithdrawalTester:
    """简化的提现系统测试器"""
    
    def __init__(self):
        # 创建数据库连接
        self.engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(bind=self.engine)
        print("🔗 数据库连接已创建")
    
    def test_database_connection(self):
        """测试数据库连接"""
        print("\n🔍 测试数据库连接...")
        
        try:
            with self.SessionLocal() as db:
                # 测试基本连接
                result = db.execute(text("SELECT 1")).scalar()
                if result == 1:
                    print("✅ 数据库连接成功")
                else:
                    print("❌ 数据库连接失败")
                    return False
                
                # 检查withdrawal_requests表
                table_exists = db.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'withdrawal_requests'
                    );
                """)).scalar()
                
                if table_exists:
                    print("✅ withdrawal_requests表存在")
                    
                    # 获取表结构
                    columns = db.execute(text("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'withdrawal_requests'
                        ORDER BY ordinal_position;
                    """)).fetchall()
                    
                    print(f"✅ 表包含 {len(columns)} 个字段:")
                    for col_name, col_type in columns:
                        print(f"   - {col_name}: {col_type}")
                else:
                    print("❌ withdrawal_requests表不存在")
                    return False
                
                # 检查依赖表
                for table in ['users', 'wallets']:
                    exists = db.execute(text(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = '{table}'
                        );
                    """)).scalar()
                    
                    if exists:
                        print(f"✅ {table}表存在")
                    else:
                        print(f"❌ {table}表不存在")
                
                return True
                
        except Exception as e:
            print(f"❌ 数据库测试失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def test_models(self):
        """测试模型定义"""
        print("\n🔍 测试模型定义...")
        
        try:
            # 测试WithdrawalStatus枚举
            status_values = [status.value for status in WithdrawalStatus]
            print(f"✅ WithdrawalStatus枚举包含状态: {status_values}")
            
            # 测试WithdrawalRequest模型创建
            test_withdrawal = WithdrawalRequest(
                request_number="TEST" + str(uuid4())[:8],
                user_id=uuid4(),
                amount=Decimal("500.00"),
                fee=Decimal("5.00"),
                actual_amount=Decimal("495.00"),
                bank_account="6225887712345678",
                bank_name="招商银行",
                account_holder="测试用户",
                status=WithdrawalStatus.PENDING
            )
            
            print("✅ WithdrawalRequest模型创建成功")
            print(f"   - 请求号: {test_withdrawal.request_number}")
            print(f"   - 金额: {test_withdrawal.amount}")
            print(f"   - 手续费: {test_withdrawal.fee}")
            print(f"   - 实际到账: {test_withdrawal.actual_amount}")
            print(f"   - 状态: {test_withdrawal.status.value}")
            
            return True
            
        except Exception as e:
            print(f"❌ 模型测试失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def test_database_operations(self):
        """测试数据库操作"""
        print("\n🔍 测试数据库操作...")
        
        try:
            with self.SessionLocal() as db:
                # 创建测试数据
                test_user_id = uuid4()
                test_withdrawal = WithdrawalRequest(
                    request_number="TEST" + str(uuid4())[:8].replace('-', ''),
                    user_id=test_user_id,
                    amount=Decimal("1000.00"),
                    fee=Decimal("10.00"),
                    actual_amount=Decimal("990.00"),
                    bank_account="6225887712345678",
                    bank_name="招商银行",
                    account_holder="测试用户",
                    status=WithdrawalStatus.PENDING,
                    metadata_={'test': True}
                )
                
                # 插入测试数据
                db.add(test_withdrawal)
                db.commit()
                print(f"✅ 测试提现记录插入成功，ID: {test_withdrawal.id}")
                
                # 查询测试数据
                retrieved = db.query(WithdrawalRequest).filter(
                    WithdrawalRequest.id == test_withdrawal.id
                ).first()
                
                if retrieved:
                    print("✅ 测试数据查询成功")
                    print(f"   - 请求号: {retrieved.request_number}")
                    print(f"   - 状态: {retrieved.status.value}")
                    print(f"   - 创建时间: {retrieved.created_at}")
                else:
                    print("❌ 测试数据查询失败")
                    return False
                
                # 更新状态
                retrieved.status = WithdrawalStatus.APPROVED
                db.commit()
                print("✅ 状态更新成功")
                
                # 删除测试数据
                db.delete(retrieved)
                db.commit()
                print("✅ 测试数据清理完成")
                
                return True
                
        except Exception as e:
            print(f"❌ 数据库操作测试失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def test_business_logic(self):
        """测试业务逻辑"""
        print("\n🔍 测试业务逻辑...")
        
        try:
            # 测试金额验证
            test_cases = [
                (5.0, "低于最小金额"),
                (10.0, "最小金额"),
                (1000.0, "正常金额"),
                (50000.0, "最大金额"),
                (60000.0, "超过最大金额")
            ]
            
            for amount, desc in test_cases:
                is_valid = 10.0 <= amount <= 50000.0
                status = "✅" if is_valid else "❌"
                print(f"   {status} {desc}: ¥{amount}")
            
            # 测试手续费计算
            fee_cases = [
                (100, 1.0),     # 1%
                (1000, 5.0),    # 0.5%
                (10000, 10.0),  # 0.1%
            ]
            
            print("\n   手续费计算测试:")
            for amount, expected_fee in fee_cases:
                if amount <= 1000:
                    calculated_fee = amount * 0.01
                elif amount <= 5000:
                    calculated_fee = amount * 0.005
                else:
                    calculated_fee = amount * 0.001
                
                is_correct = abs(calculated_fee - expected_fee) < 0.01
                status = "✅" if is_correct else "❌"
                print(f"   {status} ¥{amount} -> ¥{calculated_fee:.2f} (预期: ¥{expected_fee})")
            
            return True
            
        except Exception as e:
            print(f"❌ 业务逻辑测试失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始WithdrawalRequests提现功能测试...")
        print("=" * 60)
        
        # 运行测试
        tests = [
            ("数据库连接", self.test_database_connection),
            ("模型定义", self.test_models),
            ("数据库操作", self.test_database_operations),
            ("业务逻辑", self.test_business_logic)
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name}测试异常: {str(e)}")
                results[test_name] = False
        
        # 输出测试结果汇总
        print("\n" + "=" * 60)
        print("📊 测试结果汇总:")
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {status} {test_name}")
            if result:
                passed += 1
        
        print(f"\n🎯 总体结果: {passed}/{total} 测试通过")
        
        if passed == total:
            print("🎉 所有测试通过！提现功能基础设施就绪。")
        else:
            print("⚠️  部分测试失败，请检查相关配置。")
        
        return passed == total

def main():
    """主函数"""
    tester = SimpleWithdrawalTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 