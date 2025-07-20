#!/usr/bin/env python3
"""
测试创建案件脚本
"""

import asyncio
import sys
import os
import random
import json
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def test_create_cases():
    """测试创建案件"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🚀 开始测试创建案件...")
            
            # 获取租户ID
            tenant_query = text("SELECT id FROM tenants LIMIT 1")
            tenant_result = await session.execute(tenant_query)
            tenant_id = tenant_result.scalar()
            
            if not tenant_id:
                print("❌ 没有找到租户")
                return
            
            print(f"✅ 找到租户: {tenant_id}")
            
            # 获取或创建一个客户
            clients_query = text("SELECT id FROM clients LIMIT 1")
            clients_result = await session.execute(clients_query)
            client_id = clients_result.scalar()
            
            if not client_id:
                # 创建一个客户
                client_id = str(uuid4())
                
                # 获取销售用户
                sales_query = text("SELECT id FROM users WHERE username LIKE 'sales%' LIMIT 1")
                sales_result = await session.execute(sales_query)
                sales_user_id = sales_result.scalar()
                
                if not sales_user_id:
                    print("❌ 没有找到销售用户")
                    return
                
                create_client_sql = text("""
                    INSERT INTO clients (id, tenant_id, name, contact_person, contact_phone, contact_email, address, sales_owner_id, created_at, updated_at)
                    VALUES (:id, :tenant_id, :name, :contact, :phone, :email, :address, :sales_owner, :created_at, :updated_at)
                """)
                
                await session.execute(create_client_sql, {
                    'id': client_id,
                    'tenant_id': tenant_id,
                    'name': "测试客户公司",
                    'contact': "测试联系人",
                    'phone': "13800138000",
                    'email': "test@test.com",
                    'address': "测试地址123号",
                    'sales_owner': sales_user_id,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                })
                print(f"✅ 创建客户: {client_id}")
            
            print(f"✅ 使用客户: {client_id}")
            
            # 创建一个测试案件
            case_id = str(uuid4())
            case_number = f"TEST-{datetime.now().strftime('%Y%m%d')}-001"
            
            debtor_info = {
                "name": "张三",
                "phone": "13900139001",
                "id_card": "110101199001011234",
                "address": "北京市朝阳区测试路123号"
            }
            
            case_sql = text("""
                INSERT INTO cases (
                    id, tenant_id, client_id, case_number, debtor_info, case_amount, status,
                    assigned_to_user_id, sales_user_id, description, notes, tags,
                    debt_creation_date, legal_status, limitation_expires_at,
                    ai_risk_score, data_quality_score, data_freshness_score,
                    created_at, updated_at
                ) VALUES (
                    :id, :tenant_id, :client_id, :case_number, :debtor_info, :amount, :status,
                    :assigned_lawyer, :sales_user, :description, :notes, :tags,
                    :debt_date, :legal_status, :limitation_date,
                    :risk_score, :quality_score, :freshness_score,
                    :created_at, :updated_at
                )
            """)
            
            # 获取销售用户
            sales_query = text("SELECT id FROM users WHERE username LIKE 'sales%' LIMIT 1")
            sales_result = await session.execute(sales_query)
            sales_user_id = sales_result.scalar()
            
            await session.execute(case_sql, {
                'id': case_id,
                'tenant_id': tenant_id,
                'client_id': client_id,
                'case_number': case_number,
                'debtor_info': json.dumps(debtor_info, ensure_ascii=False),
                'amount': Decimal('50000.00'),
                'status': 'PENDING',
                'assigned_lawyer': None,
                'sales_user': sales_user_id,
                'description': '测试案件描述：这是一个用于测试的债务催收案件',
                'notes': '测试案件备注',
                'tags': json.dumps(['测试案件', '债务催收'], ensure_ascii=False),
                'debt_date': datetime.now() - timedelta(days=30),
                'legal_status': 'VALID',
                'limitation_date': datetime.now() + timedelta(days=365),
                'risk_score': 80,
                'quality_score': 90,
                'freshness_score': 85,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
            
            print(f"✅ 创建案件: {case_number}")
            
            # 提交事务
            await session.commit()
            print("✅ 事务已提交")
            
            # 验证创建结果
            verify_query = text("SELECT COUNT(*) FROM cases WHERE case_number = :case_number")
            verify_result = await session.execute(verify_query, {'case_number': case_number})
            count = verify_result.scalar()
            
            print(f"✅ 验证结果: 找到 {count} 个案件")
            
        except Exception as e:
            print(f"❌ 创建失败: {e}")
            await session.rollback()
            raise

async def main():
    """主函数"""
    try:
        await test_create_cases()
        print("✅ 测试完成")
    except Exception as e:
        print(f"💥 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())