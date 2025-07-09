#!/usr/bin/env python3
"""
创建丰富的测试数据脚本 
包含完整业务数据用于前端API测试
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
from app.models.user import User, UserStatus
from app.models.case import Case, Client, CaseStatus, LegalStatus
from app.models.finance import Transaction, CommissionSplit, Wallet
from app.models.lawyer_review import DocumentReviewTask, ReviewStatus
from app.models.statistics import SystemStatistics, UserActivityLog
from sqlalchemy import text

async def create_rich_test_data():
    """创建丰富的测试数据"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🚀 开始创建丰富的测试数据...")
            
            # 获取现有用户
            users_result = await session.execute(text("SELECT id, username FROM users ORDER BY username"))
            users = users_result.fetchall()
            print(f"✅ 找到 {len(users)} 个用户")
            
            if len(users) < 5:
                print("❌ 用户数量不足，请先运行 create_test_users.py")
                return
            
            # 按角色分类用户
            lawyers = [u for u in users if u[1].startswith('lawyer')]
            sales_users = [u for u in users if u[1].startswith('sales')]
            institutions = [u for u in users if u[1].startswith('institution')]
            admin_users = [u for u in users if u[1] == 'admin']
            
            print(f"律师: {len(lawyers)}, 销售: {len(sales_users)}, 机构: {len(institutions)}, 管理员: {len(admin_users)}")
            
            # 1. 创建客户数据
            print("🏢 创建客户数据...")
            client_data = []
            for i in range(15):
                client_id = str(uuid4())
                client_sql = """
                    INSERT INTO clients (id, tenant_id, name, client_type, business_license, 
                                       contact_person, contact_phone, contact_email, address,
                                       sales_owner_id, cooperation_level, credit_rating,
                                       total_cases, total_amount, success_rate, created_at)
                    VALUES ($1, (SELECT id FROM tenants LIMIT 1), $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                """
                
                client_types = ["银行", "消费金融", "小贷公司", "担保公司", "资产管理公司"]
                cooperation_levels = ["VIP", "金牌", "银牌", "普通"]
                credit_ratings = ["AAA", "AA", "A", "BBB", "BB"]
                
                params = [
                    client_id,
                    f"客户公司{i+1}",
                    random.choice(client_types),
                    f"9144{random.randint(1000000000000000, 9999999999999999)}",
                    f"联系人{i+1}",
                    f"1390000{i+1:04d}",
                    f"client{i+1}@example.com",
                    f"测试地址{i+1}号",
                    random.choice(sales_users)[0] if sales_users else admin_users[0][0],
                    random.choice(cooperation_levels),
                    random.choice(credit_ratings),
                    random.randint(50, 500),
                    Decimal(random.randint(1000000, 10000000)),
                    Decimal(random.randint(75, 98)) / 100,
                    datetime.now() - timedelta(days=random.randint(30, 365))
                ]
                
                await session.execute(text(client_sql), params)
                client_data.append(client_id)
            
            await session.commit()
            print(f"✅ 创建了 {len(client_data)} 个客户")
            
            # 2. 创建案件数据
            print("📋 创建案件数据...")
            case_data = []
            for i in range(100):
                case_id = str(uuid4())
                case_sql = """
                    INSERT INTO cases (id, tenant_id, client_id, case_number, debtor_info,
                                     case_amount, status, assigned_to_user_id, sales_user_id,
                                     ai_risk_score, data_quality_score, data_freshness_score,
                                     debt_creation_date, last_follow_up_date, legal_status,
                                     limitation_expires_at, description, notes, tags,
                                     created_at, completed_at)
                    VALUES ($1, (SELECT id FROM tenants LIMIT 1), $2, $3, $4, $5, $6, $7, $8, 
                           $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
                """
                
                statuses = ["pending", "assigned", "in_progress", "completed", "cancelled"]
                legal_statuses = ["valid", "expiring_soon", "expired"]
                
                debtor_info = {
                    "name": f"债务人{i+1}",
                    "id_card": f"44010119{random.randint(800101, 991231)}{random.randint(1000, 9999)}",
                    "phone": f"1390000{i+1:04d}",
                    "address": f"债务人地址{i+1}号"
                }
                
                case_status = random.choice(statuses)
                assigned_lawyer = random.choice(lawyers)[0] if random.random() > 0.3 and lawyers else None
                
                params = [
                    case_id,
                    random.choice(client_data),
                    f"LAW-2024-{i+1:04d}",
                    str(debtor_info).replace("'", '"'),  # 简化JSON存储
                    Decimal(random.randint(5000, 500000)),
                    case_status,
                    assigned_lawyer,
                    random.choice(sales_users)[0] if sales_users else admin_users[0][0],
                    random.randint(60, 95),
                    random.randint(70, 100),
                    random.randint(65, 95),
                    date.today() - timedelta(days=random.randint(30, 365)),
                    date.today() - timedelta(days=random.randint(1, 30)) if random.random() > 0.3 else None,
                    random.choice(legal_statuses),
                    date.today() + timedelta(days=random.randint(30, 730)),
                    f"案件{i+1}的详细描述",
                    f"案件{i+1}的备注信息",
                    '["紧急"]' if i < 10 else '["普通"]',
                    datetime.now() - timedelta(days=random.randint(1, 90)),
                    datetime.now() - timedelta(days=random.randint(1, 30)) if case_status == "completed" else None
                ]
                
                await session.execute(text(case_sql), params)
                case_data.append((case_id, case_status, assigned_lawyer))
            
            await session.commit()
            print(f"✅ 创建了 {len(case_data)} 个案件")
            
            # 3. 创建钱包数据
            print("💰 创建钱包数据...")
            for user in users:
                wallet_sql = """
                    INSERT INTO wallets (user_id, available_balance, frozen_balance, total_earnings,
                                       total_withdrawals, pending_amount, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (user_id) DO UPDATE SET
                        available_balance = EXCLUDED.available_balance,
                        total_earnings = EXCLUDED.total_earnings
                """
                
                # 根据用户类型生成不同的余额
                if user[1].startswith('lawyer'):
                    available = Decimal(random.randint(5000, 50000))
                    total_earnings = Decimal(random.randint(20000, 200000))
                elif user[1].startswith('sales'):
                    available = Decimal(random.randint(3000, 30000))
                    total_earnings = Decimal(random.randint(15000, 150000))
                else:
                    available = Decimal(random.randint(1000, 10000))
                    total_earnings = Decimal(random.randint(5000, 50000))
                
                params = [
                    user[0],
                    available,
                    Decimal(random.randint(0, 5000)),
                    total_earnings,
                    Decimal(random.randint(0, int(float(total_earnings) * 0.8))),
                    Decimal(random.randint(0, 2000)),
                    datetime.now()
                ]
                
                await session.execute(text(wallet_sql), params)
            
            await session.commit()
            print(f"✅ 创建了 {len(users)} 个钱包")
            
            # 4. 创建交易记录
            print("💳 创建交易记录...")
            for i in range(200):
                transaction_sql = """
                    INSERT INTO transactions (id, tenant_id, from_user_id, to_user_id, amount,
                                            transaction_type, status, case_id, order_id,
                                            payment_method, description, metadata, created_at)
                    VALUES ($1, (SELECT id FROM tenants LIMIT 1), $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """
                
                transaction_types = ["payment", "withdrawal", "commission", "refund"]
                statuses = ["completed", "pending", "failed"]
                payment_methods = ["alipay", "wechat", "bank_transfer"]
                
                # 选择相关案件和用户
                case_info = random.choice(case_data)
                from_user = random.choice(users)[0]
                to_user = random.choice(users)[0]
                
                params = [
                    str(uuid4()),
                    from_user,
                    to_user,
                    Decimal(random.randint(100, 10000)),
                    random.choice(transaction_types),
                    random.choice(statuses),
                    case_info[0],
                    f"ORDER-{i+1:06d}",
                    random.choice(payment_methods),
                    f"交易描述{i+1}",
                    '{"source": "test_data"}',
                    datetime.now() - timedelta(days=random.randint(1, 180))
                ]
                
                await session.execute(text(transaction_sql), params)
            
            await session.commit()
            print("✅ 创建了 200 条交易记录")
            
            # 5. 创建提现申请表（如果不存在）
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
            for i in range(50):
                withdrawal_sql = """
                    INSERT INTO withdrawal_requests (user_id, amount, withdrawal_method, account_info,
                                                   status, admin_notes, processed_at, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """
                
                methods = ["alipay", "wechat", "bank_transfer"]
                statuses = ["completed", "pending", "rejected"]
                
                method = random.choice(methods)
                if method == "alipay":
                    account_info = {"account": f"alipay{i+1}@example.com", "name": f"用户{i+1}"}
                elif method == "wechat":
                    account_info = {"account": f"wx{i+1:08d}", "name": f"用户{i+1}"}
                else:
                    account_info = {"bank": "工商银行", "account": f"621226{i+1:010d}", "name": f"用户{i+1}"}
                
                status = random.choice(statuses)
                processed_at = datetime.now() - timedelta(days=random.randint(1, 30)) if status != "pending" else None
                
                params = [
                    random.choice(users)[0],
                    Decimal(random.randint(500, 20000)),
                    method,
                    str(account_info).replace("'", '"'),
                    status,
                    f"提现处理备注{i+1}" if status != "pending" else None,
                    processed_at,
                    datetime.now() - timedelta(days=random.randint(1, 60))
                ]
                
                await session.execute(text(withdrawal_sql), params)
            
            await session.commit()
            print("✅ 创建了 50 条提现记录")
            
            # 6. 创建系统统计数据
            print("📊 创建系统统计数据...")
            stats_sql = """
                INSERT INTO system_statistics (stat_date, daily_new_users, daily_active_users,
                                              daily_cases, daily_revenue, total_users,
                                              total_cases, total_revenue, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (stat_date) DO UPDATE SET
                    daily_new_users = EXCLUDED.daily_new_users,
                    daily_active_users = EXCLUDED.daily_active_users
            """
            
            for i in range(30):  # 最近30天的统计
                stat_date = date.today() - timedelta(days=i)
                params = [
                    stat_date,
                    random.randint(5, 50),
                    random.randint(100, 500),
                    random.randint(20, 100),
                    Decimal(random.randint(50000, 500000)),
                    len(users) + random.randint(0, 100),
                    100 + random.randint(0, 1000),
                    Decimal(random.randint(1000000, 10000000)),
                    datetime.now()
                ]
                await session.execute(text(stats_sql), params)
            
            await session.commit()
            print("✅ 创建了 30 天的系统统计数据")
            
            print("\n🎉 丰富测试数据创建完成！")
            print("包含:")
            print("- 15个客户")
            print("- 100个案件")  
            print("- 所有用户的钱包数据")
            print("- 200条交易记录")
            print("- 50条提现记录")
            print("- 30天统计数据")
            
        except Exception as e:
            print(f"❌ 创建丰富数据失败: {e}")
            await session.rollback()
            raise

async def main():
    """主函数"""
    try:
        await create_rich_test_data()
        print("✅ 丰富测试数据创建完成")
    except Exception as e:
        print(f"💥 创建失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 