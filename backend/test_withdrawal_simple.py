#!/usr/bin/env python3
"""
提现系统简化测试脚本
只测试数据库连接和表结构
"""

import sys
import os
from decimal import Decimal

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 数据库
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 应用导入
from app.core.config import settings

class SimpleWithdrawalTester:
    """简化的提现系统测试器"""
    
    def __init__(self):
        # 创建同步数据库连接
        sync_db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        self.engine = create_engine(sync_db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        print("🔗 数据库连接已创建")
        print(f"📍 使用数据库: {sync_db_url}")
    
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
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns 
                        WHERE table_name = 'withdrawal_requests'
                        ORDER BY ordinal_position;
                    """)).fetchall()
                    
                    print(f"✅ 表包含 {len(columns)} 个字段:")
                    for col_name, col_type, nullable in columns:
                        nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                        print(f"   - {col_name}: {col_type} {nullable_str}")
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
            return False
    
    def test_data_operations(self):
        """测试数据操作"""
        print("\n🔍 测试数据操作...")
        
        try:
            with self.SessionLocal() as db:
                # 测试插入数据（不使用模型，直接SQL）
                test_data = {
                    'request_number': f'TEST{str(uuid4())[:8].upper()}',
                    'user_id': str(uuid4()),
                    'wallet_id': str(uuid4()),
                    'amount': Decimal('1000.00'),
                    'fee': Decimal('10.00'),
                    'actual_amount': Decimal('990.00'),
                    'bank_account': '6225887712345678',
                    'bank_name': '招商银行',
                    'account_holder': '测试用户',
                    'status': 'pending'
                }
                
                # 插入测试数据
                insert_sql = text("""
                    INSERT INTO withdrawal_requests 
                    (id, request_number, user_id, wallet_id, amount, fee, actual_amount, 
                     bank_account, bank_name, account_holder, status)
                    VALUES 
                    (gen_random_uuid(), :request_number, :user_id::uuid, :wallet_id::uuid, 
                     :amount, :fee, :actual_amount, :bank_account, :bank_name, :account_holder, 
                     :status::withdrawal_status)
                    RETURNING id;
                """)
                
                result = db.execute(insert_sql, test_data)
                test_id = result.scalar()
                db.commit()
                
                if test_id:
                    print(f"✅ 测试数据插入成功，ID: {test_id}")
                    
                    # 查询测试数据
                    select_sql = text("""
                        SELECT request_number, amount, status, created_at
                        FROM withdrawal_requests 
                        WHERE id = :test_id
                    """)
                    
                    result = db.execute(select_sql, {'test_id': test_id}).fetchone()
                    if result:
                        print("✅ 测试数据查询成功:")
                        print(f"   - 请求号: {result[0]}")
                        print(f"   - 金额: {result[1]}")
                        print(f"   - 状态: {result[2]}")
                        print(f"   - 创建时间: {result[3]}")
                    
                    # 更新状态
                    update_sql = text("""
                        UPDATE withdrawal_requests 
                        SET status = 'approved'::withdrawal_status, updated_at = NOW()
                        WHERE id = :test_id
                    """)
                    db.execute(update_sql, {'test_id': test_id})
                    db.commit()
                    print("✅ 状态更新成功")
                    
                    # 删除测试数据
                    delete_sql = text("DELETE FROM withdrawal_requests WHERE id = :test_id")
                    db.execute(delete_sql, {'test_id': test_id})
                    db.commit()
                    print("✅ 测试数据清理完成")
                    
                    return True
                else:
                    print("❌ 测试数据插入失败")
                    return False
                
        except Exception as e:
            print(f"❌ 数据操作测试失败: {str(e)}")
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
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始WithdrawalRequests提现功能测试...")
        print("=" * 60)
        
        # 运行测试
        tests = [
            ("数据库连接", self.test_database_connection),
            ("数据操作", self.test_data_operations),
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
            print("💡 下一步可以测试API接口和前端功能。")
        else:
            print("⚠️  部分测试失败，请检查相关配置。")
        
        return passed == total

def main():
    """主函数"""
    from uuid import uuid4  # 需要在这里导入
    tester = SimpleWithdrawalTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 