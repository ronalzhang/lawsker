#!/usr/bin/env python3
"""
创建简化的测试数据脚本
用于前端API测试
"""

import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
import random

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def create_simple_test_data():
    """创建简化的测试数据"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🚀 开始创建简化测试数据...")
            
            # 获取现有用户
            users_result = await session.execute(text("SELECT id, username FROM users ORDER BY username"))
            users = users_result.fetchall()
            print(f"✅ 找到 {len(users)} 个用户")
            
            # 1. 创建钱包数据
            print("💰 创建钱包数据...")
            for user in users:
                user_id = str(user[0])
                username = user[1]
                
                # 根据用户类型生成不同的余额
                if username.startswith('lawyer'):
                    available = random.randint(5000, 50000)
                    total_earnings = random.randint(20000, 200000)
                elif username.startswith('sales'):
                    available = random.randint(3000, 30000)
                    total_earnings = random.randint(15000, 150000)
                else:
                    available = random.randint(1000, 10000)
                    total_earnings = random.randint(5000, 50000)
                
                wallet_sql = f"""
                    INSERT INTO wallets (user_id, withdrawable_balance, frozen_balance, total_earned,
                                       total_withdrawn, balance, commission_count, created_at)
                    VALUES ('{user_id}', {available}, {random.randint(0, 5000)}, {total_earnings},
                           {random.randint(0, int(total_earnings * 0.8))}, {available + random.randint(0, 5000)}, 
                           {random.randint(1, 50)}, '{datetime.now().isoformat()}')
                    ON CONFLICT (user_id) DO UPDATE SET
                        withdrawable_balance = EXCLUDED.withdrawable_balance,
                        total_earned = EXCLUDED.total_earned
                """
                
                await session.execute(text(wallet_sql))
            
            await session.commit()
            print(f"✅ 创建了 {len(users)} 个钱包")
            
            # 2. 创建提现申请表（如果不存在）
            print("🏦 创建提现申请表...")
            create_withdrawal_table_sql = """
                CREATE TABLE IF NOT EXISTS withdrawal_requests (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id),
                    amount DECIMAL(15,2) NOT NULL,
                    withdrawal_method VARCHAR(50) NOT NULL,
                    account_info JSONB NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    admin_notes TEXT,
                    processed_by UUID REFERENCES users(id),
                    processed_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """
            await session.execute(text(create_withdrawal_table_sql))
            
            # 创建提现记录
            for i, user in enumerate(users[:20]):  # 只为前20个用户创建提现记录
                user_id = str(user[0])
                methods = ["alipay", "wechat", "bank_transfer"]
                statuses = ["completed", "pending", "rejected"]
                
                method = random.choice(methods)
                status = random.choice(statuses)
                amount = random.randint(500, 20000)
                
                # 简化account_info JSON
                if method == "alipay":
                    account_info = f'{{"account": "alipay{i+1}@example.com", "name": "用户{i+1}"}}'
                elif method == "wechat":
                    account_info = f'{{"account": "wx{i+1:08d}", "name": "用户{i+1}"}}'
                else:
                    account_info = f'{{"bank": "工商银行", "account": "621226{i+1:010d}", "name": "用户{i+1}"}}'
                
                processed_at = "NULL"
                if status != "pending":
                    processed_at = f"'{(datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()}'"
                
                withdrawal_sql = f"""
                    INSERT INTO withdrawal_requests (user_id, amount, withdrawal_method, account_info,
                                                   status, admin_notes, processed_at, created_at)
                    VALUES ('{user_id}', {amount}, '{method}', '{account_info}',
                           '{status}', 
                           {'NULL' if status == 'pending' else f"'提现处理备注{i+1}'"}, 
                           {processed_at}, 
                           '{(datetime.now() - timedelta(days=random.randint(1, 60))).isoformat()}')
                """
                
                await session.execute(text(withdrawal_sql))
            
            await session.commit()
            print("✅ 创建了 20 条提现记录")
            
            # 3. 创建系统统计数据
            print("📊 创建系统统计数据...")
            for i in range(30):  # 最近30天的统计
                stat_date = (date.today() - timedelta(days=i)).isoformat()
                stats_sql = f"""
                    INSERT INTO system_statistics (stat_date, daily_new_users, daily_active_users,
                                                  daily_cases, daily_revenue, total_users,
                                                  total_cases, total_revenue, created_at)
                    VALUES ('{stat_date}', {random.randint(5, 50)}, {random.randint(100, 500)},
                           {random.randint(20, 100)}, {random.randint(50000, 500000)},
                           {len(users) + random.randint(0, 100)}, {100 + random.randint(0, 1000)},
                           {random.randint(1000000, 10000000)}, '{datetime.now().isoformat()}')
                    ON CONFLICT (stat_date) DO UPDATE SET
                        daily_new_users = EXCLUDED.daily_new_users,
                        daily_active_users = EXCLUDED.daily_active_users
                """
                await session.execute(text(stats_sql))
            
            await session.commit()
            print("✅ 创建了 30 天的系统统计数据")
            
            # 4. 创建一些案例数据（简化版）
            print("📋 创建案例数据...")
            tenant_result = await session.execute(text("SELECT id FROM tenants LIMIT 1"))
            tenant_row = tenant_result.fetchone()
            if not tenant_row:
                print("⚠️  没有找到租户，跳过案例创建")
                return
            tenant_id = tenant_row[0]
            
            lawyers = [u for u in users if u[1].startswith('lawyer')]
            sales_users = [u for u in users if u[1].startswith('sales')]
            
            if lawyers and sales_users:
                for i in range(20):  # 创建20个案例
                    case_id = str(uuid4())
                    assigned_lawyer = random.choice(lawyers)[0] if random.random() > 0.3 else None
                    sales_user = random.choice(sales_users)[0]
                    
                    case_sql = f"""
                        INSERT INTO cases (id, tenant_id, case_number, case_amount, status,
                                         assigned_to_user_id, sales_user_id, ai_risk_score,
                                         created_at, description)
                        VALUES ('{case_id}', '{tenant_id}', 'LAW-2024-{i+1:04d}', 
                               {random.randint(5000, 500000)}, 'pending',
                               {'NULL' if assigned_lawyer is None else f"'{assigned_lawyer}'"}, 
                               '{sales_user}', {random.randint(60, 95)},
                               '{(datetime.now() - timedelta(days=random.randint(1, 90))).isoformat()}',
                               '案例{i+1}的描述')
                    """
                    await session.execute(text(case_sql))
                
                await session.commit()
                print("✅ 创建了 20 个案例")
            
            print("\n🎉 简化测试数据创建完成！")
            print("包含:")
            print("- 所有用户的钱包数据")
            print("- 20条提现记录")
            print("- 30天统计数据")
            print("- 20个案例数据")
            
        except Exception as e:
            print(f"❌ 创建数据失败: {e}")
            await session.rollback()
            raise

async def main():
    """主函数"""
    try:
        await create_simple_test_data()
        print("✅ 简化测试数据创建完成")
    except Exception as e:
        print(f"💥 创建失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 