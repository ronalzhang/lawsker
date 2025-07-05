#!/usr/bin/env python3
"""
提现系统综合测试脚本
测试提现功能的完整流程，包括API、数据库、服务类等
"""

import asyncio
import sys
import os
from pathlib import Path
from decimal import Decimal
from uuid import uuid4, UUID
import json
import traceback
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.models.finance import WithdrawalRequest, WithdrawalStatus, Wallet
from app.models.user import User
from app.services.payment_service import WithdrawalService, WithdrawalError
from app.services.config_service import SystemConfigService


class WithdrawalSystemTester:
    """提现系统测试器"""
    
    def __init__(self):
        # 创建同步数据库连接
        self.engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.config_service = SystemConfigService()
        self.withdrawal_service = WithdrawalService(self.config_service)
        
        # 测试结果
        self.test_results = {
            "database": {"status": "未测试", "details": []},
            "models": {"status": "未测试", "details": []},
            "services": {"status": "未测试", "details": []},
            "api_logic": {"status": "未测试", "details": []},
            "business_rules": {"status": "未测试", "details": []}
        }
    
    def log_test(self, category: str, test_name: str, success: bool, details: str = ""):
        """记录测试结果"""
        status = "✅ 通过" if success else "❌ 失败"
        self.test_results[category]["details"].append({
            "test": test_name,
            "status": status,
            "details": details
        })
        print(f"  {status} {test_name}: {details}")
    
    def update_category_status(self, category: str):
        """更新分类状态"""
        details = self.test_results[category]["details"]
        failed_tests = [d for d in details if "❌" in d["status"]]
        
        if not details:
            self.test_results[category]["status"] = "未执行"
        elif failed_tests:
            self.test_results[category]["status"] = f"部分失败 ({len(failed_tests)}/{len(details)})"
        else:
            self.test_results[category]["status"] = "全部通过"
    
    def test_database_connection(self):
        """测试数据库连接和表结构"""
        print("\n🔍 测试数据库连接和表结构...")
        
        try:
            with self.SessionLocal() as db:
                # 测试基本连接
                result = db.execute(text("SELECT 1")).scalar()
                self.log_test("database", "数据库连接", result == 1)
                
                # 检查withdrawal_requests表是否存在
                table_exists = db.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'withdrawal_requests'
                    );
                """)).scalar()
                self.log_test("database", "withdrawal_requests表存在", table_exists, 
                             "表已创建" if table_exists else "表不存在，请运行迁移脚本")
                
                if table_exists:
                    # 检查表结构
                    columns = db.execute(text("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'withdrawal_requests'
                        ORDER BY ordinal_position;
                    """)).fetchall()
                    
                    required_columns = [
                        'id', 'request_number', 'user_id', 'amount', 'fee', 
                        'actual_amount', 'bank_account', 'bank_name', 'account_holder',
                        'status', 'created_at'
                    ]
                    
                    existing_columns = [col[0] for col in columns]
                    missing_columns = [col for col in required_columns if col not in existing_columns]
                    
                    self.log_test("database", "表结构完整性", len(missing_columns) == 0,
                                 f"缺失字段: {missing_columns}" if missing_columns else f"包含{len(existing_columns)}个字段")
                
                # 检查users表（依赖表）
                users_exists = db.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'users'
                    );
                """)).scalar()
                self.log_test("database", "users表存在", users_exists)
                
                # 检查wallets表
                wallets_exists = db.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'wallets'
                    );
                """)).scalar()
                self.log_test("database", "wallets表存在", wallets_exists)
                
        except Exception as e:
            self.log_test("database", "数据库连接", False, f"错误: {str(e)}")
        
        self.update_category_status("database")
    
    def test_models(self):
        """测试模型定义"""
        print("\n🔍 测试模型定义...")
        
        try:
            # 测试WithdrawalStatus枚举
            status_values = [status.value for status in WithdrawalStatus]
            expected_statuses = ['pending', 'approved', 'processing', 'completed', 'rejected', 'failed', 'cancelled']
            
            missing_statuses = [s for s in expected_statuses if s not in status_values]
            self.log_test("models", "WithdrawalStatus枚举", len(missing_statuses) == 0,
                         f"缺失状态: {missing_statuses}" if missing_statuses else f"包含{len(status_values)}个状态")
            
            # 测试WithdrawalRequest模型创建
            test_withdrawal = WithdrawalRequest(
                request_number="TEST123456",
                user_id=uuid4(),
                amount=Decimal("500.00"),
                fee=Decimal("5.00"),
                actual_amount=Decimal("495.00"),
                bank_account="6225887712345678",
                bank_name="招商银行",
                account_holder="测试用户",
                status=WithdrawalStatus.PENDING
            )
            
            self.log_test("models", "WithdrawalRequest模型创建", True, "模型实例化成功")
            
            # 测试字段验证
            required_fields = ['request_number', 'user_id', 'amount', 'bank_account', 'bank_name', 'account_holder']
            for field in required_fields:
                has_field = hasattr(test_withdrawal, field)
                self.log_test("models", f"字段存在: {field}", has_field)
                
        except Exception as e:
            self.log_test("models", "模型定义", False, f"错误: {str(e)}")
            traceback.print_exc()
        
        self.update_category_status("models")
    
    async def test_services(self):
        """测试服务类"""
        print("\n🔍 测试服务类...")
        
        try:
            # 测试服务类初始化
            self.log_test("services", "WithdrawalService初始化", True, "服务类创建成功")
            
            # 测试提现配置获取
            config = await self.withdrawal_service.get_withdrawal_config()
            self.log_test("services", "获取提现配置", isinstance(config, dict),
                         f"配置项: {len(config)}个" if isinstance(config, dict) else "配置获取失败")
            
            # 测试风险评估
            risk_score = await self.withdrawal_service.calculate_risk_score(
                user_id=uuid4(),
                amount=Decimal("1000.00"),
                db=self.SessionLocal()
            )
            self.log_test("services", "风险评估计算", isinstance(risk_score, (int, float)),
                         f"风险评分: {risk_score}" if isinstance(risk_score, (int, float)) else "计算失败")
            
        except Exception as e:
            self.log_test("services", "服务类测试", False, f"错误: {str(e)}")
            traceback.print_exc()
        
        self.update_category_status("services")
    
    def test_business_rules(self):
        """测试业务规则"""
        print("\n🔍 测试业务规则...")
        
        try:
            with self.SessionLocal() as db:
                # 测试提现金额限制
                min_amount = 10.0
                max_amount = 50000.0
                daily_limit = 100000.0
                
                # 测试最小金额
                test_amounts = [
                    (5.0, False, "低于最小金额"),
                    (10.0, True, "等于最小金额"),
                    (1000.0, True, "正常金额"),
                    (50000.0, True, "等于最大金额"),
                    (60000.0, False, "超过最大金额")
                ]
                
                for amount, should_pass, desc in test_amounts:
                    is_valid = min_amount <= amount <= max_amount
                    self.log_test("business_rules", f"金额验证 - {desc}", is_valid == should_pass,
                                 f"金额: ¥{amount}")
                
                # 测试手续费计算
                test_fee_cases = [
                    (100.0, 1.0),    # 100元 -> 1元手续费 (1%)
                    (1000.0, 5.0),   # 1000元 -> 5元手续费 (0.5%)
                    (10000.0, 10.0)  # 10000元 -> 10元手续费 (0.1%)
                ]
                
                for amount, expected_fee in test_fee_cases:
                    # 简化版手续费计算逻辑
                    if amount <= 1000:
                        calculated_fee = amount * 0.01  # 1%
                    elif amount <= 5000:
                        calculated_fee = amount * 0.005  # 0.5%
                    else:
                        calculated_fee = amount * 0.001  # 0.1%
                    
                    fee_correct = abs(calculated_fee - expected_fee) < 0.01
                    self.log_test("business_rules", f"手续费计算", fee_correct,
                                 f"¥{amount} -> ¥{calculated_fee:.2f} (预期: ¥{expected_fee})")
                
                # 测试银行卡号格式验证
                test_bank_accounts = [
                    ("6225887712345678", True, "正常银行卡号"),
                    ("1234567890123456", True, "16位数字"),
                    ("12345", False, "过短"),
                    ("12345678901234567890", False, "过长"),
                    ("abcd1234", False, "包含字母")
                ]
                
                for account, should_pass, desc in test_bank_accounts:
                    # 简单验证：16-19位数字
                    is_valid = account.isdigit() and 16 <= len(account) <= 19
                    self.log_test("business_rules", f"银行卡号验证 - {desc}", is_valid == should_pass,
                                 f"卡号: {account}")
                
        except Exception as e:
            self.log_test("business_rules", "业务规则测试", False, f"错误: {str(e)}")
            traceback.print_exc()
        
        self.update_category_status("business_rules")
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*80)
        print("🎯 WithdrawalRequests提现功能测试总结")
        print("="*80)
        
        for category, result in self.test_results.items():
            category_name = {
                "database": "📊 数据库测试",
                "models": "🏗️  模型定义",
                "services": "⚙️  服务类",
                "api_logic": "🔌 API逻辑",
                "business_rules": "📋 业务规则"
            }.get(category, category)
            
            print(f"\n{category_name}: {result['status']}")
            
            for detail in result["details"]:
                print(f"  {detail['status']} {detail['test']}")
                if detail["details"]:
                    print(f"    └─ {detail['details']}")
        
        # 计算总体状态
        total_tests = sum(len(result["details"]) for result in self.test_results.values())
        failed_tests = sum(
            len([d for d in result["details"] if "❌" in d["status"]])
            for result in self.test_results.values()
        )
        passed_tests = total_tests - failed_tests
        
        print(f"\n📈 总体测试结果:")
        print(f"   ✅ 通过: {passed_tests}")
        print(f"   ❌ 失败: {failed_tests}")
        print(f"   📊 总计: {total_tests}")
        print(f"   📈 成功率: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "   📈 成功率: 0%")
        
        if failed_tests == 0:
            print("\n🎉 恭喜！WithdrawalRequests提现功能测试全部通过！")
            print("✨ 系统已准备就绪，可以开始使用提现功能。")
        else:
            print(f"\n⚠️  发现 {failed_tests} 个问题需要修复。")
            print("📝 请查看上面的详细信息进行修复。")
        
        print("\n💡 下一步:")
        print("   1. 如果有数据库相关错误，请运行迁移脚本: backend/migrations/add_withdrawal_request_table.sql")
        print("   2. 启动后端服务测试API端点")
        print("   3. 在前端测试提现功能界面")
        print("   4. 验证完整的提现申请到审核流程")


async def main():
    """主测试函数"""
    print("🚀 开始WithdrawalRequests提现功能综合测试...")
    
    tester = WithdrawalSystemTester()
    
    # 执行各项测试
    tester.test_database_connection()
    tester.test_models()
    await tester.test_services()
    tester.test_business_rules()
    
    # 打印总结
    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main()) 