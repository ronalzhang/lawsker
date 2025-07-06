#!/usr/bin/env python3
"""
测试数据初始化脚本
为系统添加测试数据以验证功能
"""

import asyncio
import sys
import os
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4
import random

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, engine
from app.models.user import User, Role, UserRole, Profile, UserStatus
from app.models.tenant import Tenant, SystemConfig
from app.models.case import Case, Client, CaseStatus, LegalStatus
from app.models.finance import Transaction, CommissionSplit, Wallet
from app.models.lawyer_review import DocumentReviewTask, ReviewStatus
from app.models.statistics import SystemStatistics, UserActivityLog, DataUploadRecord, TaskPublishRecord


async def create_test_data():
    """创建测试数据"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🚀 开始创建测试数据...")
            
            # 1. 创建租户
            print("📊 创建租户数据...")
            tenant = Tenant(
                id=uuid4(),
                name="律客科技有限公司",
                tenant_code="lawsker",
                domain="lawsker.com",
                system_config={
                    "theme": "default",
                    "language": "zh-CN",
                    "timezone": "Asia/Shanghai"
                }
            )
            session.add(tenant)
            await session.flush()
            
            # 2. 创建角色
            print("👥 创建角色数据...")
            roles = []
            role_names = ["admin", "lawyer", "sales", "institution"]
            for role_name in role_names:
                role = Role(
                    id=uuid4(),
                    name=role_name,
                    description=f"{role_name.title()}角色",
                    permissions={"read": True, "write": True, "delete": False}
                )
                roles.append(role)
                session.add(role)
            await session.flush()
            
            # 3. 创建用户
            print("👤 创建用户数据...")
            users = []
            
            # 管理员用户
            admin_user = User(
                id=uuid4(),
                tenant_id=tenant.id,
                username="admin",
                email="admin@lawsker.com",
                password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # admin123
                phone_number="13800000001",
                status=UserStatus.ACTIVE
            )
            users.append(admin_user)
            session.add(admin_user)
            
            # 律师用户
            for i in range(5):
                lawyer = User(
                    id=uuid4(),
                    tenant_id=tenant.id,
                    username=f"lawyer{i+1}",
                    email=f"lawyer{i+1}@lawsker.com",
                    password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # demo123
                    phone_number=f"1380000{i+1:04d}",
                    status=UserStatus.ACTIVE
                )
                users.append(lawyer)
                session.add(lawyer)
            
            # 销售用户
            for i in range(8):
                sales = User(
                    id=uuid4(),
                    tenant_id=tenant.id,
                    username=f"sales{i+1}",
                    email=f"sales{i+1}@lawsker.com",
                    password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # demo123
                    phone_number=f"1381000{i+1:04d}",
                    status=UserStatus.ACTIVE
                )
                users.append(sales)
                session.add(sales)
            
            # 机构用户
            for i in range(3):
                institution = User(
                    id=uuid4(),
                    tenant_id=tenant.id,
                    username=f"institution{i+1}",
                    email=f"institution{i+1}@lawsker.com",
                    password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # demo123
                    phone_number=f"1382000{i+1:04d}",
                    status=UserStatus.ACTIVE
                )
                users.append(institution)
                session.add(institution)
            
            await session.flush()
            
            # 4. 为用户分配角色
            print("👥 分配用户角色...")
            # 为简化测试，我们先给用户添加一个临时的role属性
            admin_user.role = "admin"
            for i, lawyer in enumerate(users[1:6]):  # 前5个是律师
                lawyer.role = "lawyer"
            for i, sales in enumerate(users[6:14]):  # 接下来8个是销售
                sales.role = "sales"
            for i, institution in enumerate(users[14:17]):  # 最后3个是机构
                institution.role = "institution"
            
            # 5. 创建客户
            print("🏢 创建客户数据...")
            clients = []
            sales_users = [u for u in users if hasattr(u, 'role') and u.role == "sales"]
            
            for i in range(10):
                client = Client(
                    id=uuid4(),
                    tenant_id=tenant.id,
                    name=f"客户公司{i+1}",
                    client_type="银行" if i % 3 == 0 else "消费金融" if i % 3 == 1 else "小贷公司",
                    business_license=f"9144{random.randint(1000000000000000, 9999999999999999)}",
                    contact_person=f"联系人{i+1}",
                    contact_phone=f"1390000{i+1:04d}",
                    contact_email=f"client{i+1}@example.com",
                    address=f"测试地址{i+1}号",
                    sales_owner_id=random.choice(sales_users).id,
                    cooperation_level="VIP" if i < 3 else "普通",
                    credit_rating="AA" if i < 2 else "A" if i < 5 else "B",
                    total_cases=random.randint(10, 100),
                    total_amount=Decimal(random.randint(100000, 5000000)),
                    success_rate=Decimal(random.randint(70, 95)) / 100
                )
                clients.append(client)
                session.add(client)
            
            await session.flush()
            
            # 6. 创建案件
            print("📋 创建案件数据...")
            cases = []
            lawyer_users = [u for u in users if hasattr(u, 'role') and u.role == "lawyer"]
            
            for i in range(50):
                case = Case(
                    id=uuid4(),
                    tenant_id=tenant.id,
                    client_id=random.choice(clients).id,
                    case_number=f"LAW-2024-{i+1:04d}",
                    debtor_info={
                        "name": f"债务人{i+1}",
                        "id_card": f"44010119{random.randint(800101, 991231)}{random.randint(1000, 9999)}",
                        "phone": f"1390000{i+1:04d}",
                        "address": f"债务人地址{i+1}号"
                    },
                    case_amount=Decimal(random.randint(5000, 500000)),
                    status=random.choice([CaseStatus.PENDING, CaseStatus.ASSIGNED, CaseStatus.IN_PROGRESS, CaseStatus.COMPLETED]),
                    assigned_to_user_id=random.choice(lawyer_users).id if random.random() > 0.3 else None,
                    sales_user_id=random.choice(sales_users).id,
                    ai_risk_score=random.randint(60, 95),
                    data_quality_score=random.randint(70, 100),
                    data_freshness_score=random.randint(65, 95),
                    debt_creation_date=date.today() - timedelta(days=random.randint(30, 365)),
                    last_follow_up_date=date.today() - timedelta(days=random.randint(1, 30)) if random.random() > 0.3 else None,
                    legal_status=random.choice([LegalStatus.VALID, LegalStatus.EXPIRING_SOON]),
                    limitation_expires_at=date.today() + timedelta(days=random.randint(30, 730)),
                    description=f"案件{i+1}的详细描述",
                    notes=f"案件{i+1}的备注信息",
                    tags=["紧急"] if i < 5 else ["普通"] if i < 30 else ["低优先级"],
                    created_at=datetime.now() - timedelta(days=random.randint(1, 90)),
                    completed_at=datetime.now() - timedelta(days=random.randint(1, 30)) if random.random() > 0.7 else None
                )
                cases.append(case)
                session.add(case)
            
            await session.flush()
            
            # 7. 创建交易记录
            print("💰 创建交易数据...")
            completed_cases = [c for c in cases if c.status == CaseStatus.COMPLETED]
            
            for case in completed_cases[:20]:  # 为已完成案件创建交易
                transaction = Transaction(
                    id=uuid4(),
                    case_id=case.id,
                    amount=Decimal(random.randint(int(case.case_amount * 0.3), int(case.case_amount * 0.8))),
                    transaction_type="collection",
                    status="completed",
                    payment_method="bank_transfer",
                    description=f"案件{case.case_number}催收回款",
                    created_at=datetime.now() - timedelta(days=random.randint(1, 30))
                )
                session.add(transaction)
                
                # 创建分成记录
                commission_splits = [
                    CommissionSplit(
                        id=uuid4(),
                        transaction_id=transaction.id,
                        user_id=case.assigned_to_user_id,
                        split_type="lawyer",
                        percentage=Decimal("0.30"),
                        amount=transaction.amount * Decimal("0.30"),
                        status="paid",
                        paid_at=datetime.now() - timedelta(days=random.randint(1, 30))
                    ),
                    CommissionSplit(
                        id=uuid4(),
                        transaction_id=transaction.id,
                        user_id=case.sales_user_id,
                        split_type="sales",
                        percentage=Decimal("0.20"),
                        amount=transaction.amount * Decimal("0.20"),
                        status="paid",
                        paid_at=datetime.now() - timedelta(days=random.randint(1, 30))
                    )
                ]
                
                for split in commission_splits:
                    session.add(split)
            
            # 8. 创建数据上传记录
            print("📤 创建数据上传记录...")
            for i in range(15):
                upload_record = DataUploadRecord(
                    id=uuid4(),
                    user_id=random.choice(sales_users).id,
                    file_name=f"客户数据_{date.today().strftime('%Y%m%d')}_{i+1}.xlsx",
                    file_size=random.randint(50000, 5000000),
                    file_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    file_path=f"/uploads/data/{uuid4()}.xlsx",
                    data_type=random.choice(["debt_collection", "client_data", "contact_info"]),
                    total_records=random.randint(100, 1000),
                    processed_records=random.randint(80, 950),
                    failed_records=random.randint(0, 50),
                    status=random.choice(["completed", "processing", "failed"]),
                    processing_notes=f"数据处理完成，成功率{random.randint(85, 98)}%",
                    created_at=datetime.now() - timedelta(days=random.randint(1, 30))
                )
                session.add(upload_record)
            
            # 9. 创建任务发布记录
            print("📝 创建任务发布记录...")
            for i in range(25):
                task_record = TaskPublishRecord(
                    id=uuid4(),
                    user_id=random.choice(sales_users).id,
                    task_type=random.choice(["lawyer_letter", "debt_collection", "contract_review"]),
                    title=f"任务{i+1} - {random.choice(['律师函发送', '债务催收', '合同审查'])}",
                    description=f"任务{i+1}的详细描述和要求",
                    target_info={
                        "target_name": f"目标对象{i+1}",
                        "contact_info": f"1390000{i+1:04d}",
                        "address": f"目标地址{i+1}号"
                    },
                    amount=Decimal(random.randint(1000, 50000)),
                    urgency=random.choice(["normal", "urgent", "low"]),
                    status=random.choice(["pending", "assigned", "completed"]),
                    assigned_to=random.choice(lawyer_users).id if random.random() > 0.4 else None,
                    completion_notes=f"任务{i+1}已完成" if random.random() > 0.6 else None,
                    created_at=datetime.now() - timedelta(days=random.randint(1, 60)),
                    completed_at=datetime.now() - timedelta(days=random.randint(1, 30)) if random.random() > 0.6 else None
                )
                session.add(task_record)
            
            # 10. 创建用户活动日志
            print("📊 创建活动日志...")
            for i in range(100):
                activity = UserActivityLog(
                    id=uuid4(),
                    user_id=random.choice(users).id,
                    action=random.choice([
                        "登录系统", "案件分配", "提现申请", "数据上传", "任务发布",
                        "案件更新", "文档审核", "收益查看", "系统配置"
                    ]),
                    resource_type=random.choice(["case", "task", "upload", "withdrawal", "system"]),
                    resource_id=uuid4(),
                    details={
                        "description": f"活动{i+1}的详细信息",
                        "result": "成功" if random.random() > 0.1 else "失败"
                    },
                    ip_address=f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    session_id=str(uuid4()),
                    created_at=datetime.now() - timedelta(hours=random.randint(1, 720))
                )
                session.add(activity)
            
            # 11. 创建系统统计
            print("📈 创建系统统计...")
            for i in range(30):  # 创建30天的统计数据
                stat_date = date.today() - timedelta(days=i)
                stats = SystemStatistics(
                    id=uuid4(),
                    stat_date=stat_date,
                    total_cases=random.randint(800, 1200),
                    active_cases=random.randint(50, 150),
                    completed_cases=random.randint(700, 1100),
                    total_users=random.randint(100, 200),
                    active_lawyers=random.randint(15, 30),
                    active_sales=random.randint(30, 60),
                    total_transactions=random.randint(500, 800),
                    total_amount=Decimal(random.randint(5000000, 20000000)),
                    total_commissions=Decimal(random.randint(500000, 2000000))
                )
                session.add(stats)
            
            # 12. 创建系统配置
            print("⚙️ 创建系统配置...")
            configs = [
                SystemConfig(
                    id=uuid4(),
                    tenant_id=tenant.id,
                    category="commission",
                    key="lawyer_letter_price",
                    value={"amount": 30, "currency": "CNY"},
                    description="律师函服务价格"
                ),
                SystemConfig(
                    id=uuid4(),
                    tenant_id=tenant.id,
                    category="commission",
                    key="commission_rates",
                    value={
                        "platform": 0.50,
                        "lawyer": 0.30,
                        "sales": 0.20
                    },
                    description="分成比例配置"
                ),
                SystemConfig(
                    id=uuid4(),
                    tenant_id=tenant.id,
                    category="system",
                    key="withdrawal_limits",
                    value={
                        "small_amount": 50000,
                        "large_amount": 500000,
                        "small_processing_time": "秒到账",
                        "large_processing_time": "1-2个工作日"
                    },
                    description="提现限额和处理时间"
                )
            ]
            
            for config in configs:
                session.add(config)
            
            # 提交所有数据
            await session.commit()
            print("✅ 测试数据创建完成！")
            
            # 打印统计信息
            print("\n📊 数据统计:")
            print(f"  • 租户: 1个")
            print(f"  • 角色: {len(roles)}个")
            print(f"  • 用户: {len(users)}个")
            print(f"  • 客户: {len(clients)}个")
            print(f"  • 案件: {len(cases)}个")
            print(f"  • 交易: {len(completed_cases[:20])}个")
            print(f"  • 数据上传记录: 15个")
            print(f"  • 任务发布记录: 25个")
            print(f"  • 活动日志: 100个")
            print(f"  • 系统统计: 30天")
            print(f"  • 系统配置: {len(configs)}个")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ 创建测试数据失败: {e}")
            raise
        finally:
            await session.close()


async def main():
    """主函数"""
    try:
        await create_test_data()
        print("\n🎉 测试数据初始化完成！")
    except Exception as e:
        print(f"\n💥 初始化失败: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main()) 