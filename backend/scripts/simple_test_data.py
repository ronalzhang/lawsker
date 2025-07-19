#!/usr/bin/env python3
"""
创建简单的测试数据
"""

import asyncio
import sys
import os
from datetime import datetime
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def create_simple_test_data():
    """创建简单的测试数据"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🚀 开始创建简单测试数据...")
            
            # 1. 创建10个测试案件
            print("📋 创建案件数据...")
            for i in range(10):
                case_sql = """
                    INSERT INTO cases (id, tenant_id, case_number, debtor_info, case_amount, status, created_at)
                    VALUES (gen_random_uuid(), (SELECT id FROM tenants LIMIT 1), :case_number, :debtor_info, :amount, :status, :created_at)
                """
                
                debtor_info = {
                    "name": f"债务人{i+1}",
                    "phone": f"1390000{i+1:04d}",
                    "address": f"测试地址{i+1}号"
                }
                
                params = {
                    'case_number': f'CASE-2024-{i+1:04d}',
                    'debtor_info': json.dumps(debtor_info, ensure_ascii=False),
                    'amount': 50000 + i * 10000,
                    'status': 'PENDING',
                    'created_at': datetime.now()
                }
                
                await session.execute(text(case_sql), params)
            
            await session.commit()
            print("✅ 创建了10个测试案件")
            
            # 2. 为用户创建钱包数据
            print("💰 创建钱包数据...")
            users_result = await session.execute(text("SELECT id FROM users"))
            users = users_result.fetchall()
            
            for user in users:
                wallet_sql = """
                    INSERT INTO wallets (user_id, available_balance, frozen_balance, total_earnings, total_withdrawals, pending_amount, created_at)
                    VALUES (:user_id, :available, :frozen, :earnings, :withdrawals, :pending, :created_at)
                    ON CONFLICT (user_id) DO UPDATE SET
                        available_balance = EXCLUDED.available_balance,
                        total_earnings = EXCLUDED.total_earnings
                """
                
                params = {
                    'user_id': user[0],
                    'available': 10000.00,
                    'frozen': 500.00,
                    'earnings': 50000.00,
                    'withdrawals': 20000.00,
                    'pending': 1000.00,
                    'created_at': datetime.now()
                }
                
                await session.execute(text(wallet_sql), params)
            
            await session.commit()
            print(f"✅ 创建了{len(users)}个用户钱包")
            
            print("\n🎉 简单测试数据创建完成！")
            print("包含:")
            print("- 10个测试案件")
            print(f"- {len(users)}个用户钱包")
            
        except Exception as e:
            print(f"❌ 创建失败: {e}")
            await session.rollback()
            raise

async def main():
    """主函数"""
    try:
        await create_simple_test_data()
        print("✅ 简单测试数据创建完成")
    except Exception as e:
        print(f"💥 创建失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())