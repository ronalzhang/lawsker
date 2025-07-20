#!/usr/bin/env python3
"""
创建50-100个真实案件任务数据
包含详细的案件信息、债务人信息等
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

# 真实案件类型和描述模板
CASE_TEMPLATES = [
    {
        "type": "debt_collection",
        "title_template": "{company}欠款催收案",
        "description_template": "{debtor_name}于{loan_date}通过{platform}申请借款{amount}元，约定还款期限{deadline}，现已逾期{overdue_days}天未还。债务人{debtor_name}，身份证号{id_card}，联系电话{phone}，现住址{address}。经多次催收无果，特委托律师函催收。",
        "case_type": "债务催收"
    },
    {
        "type": "contract_dispute", 
        "title_template": "{company}合同违约纠纷案",
        "description_template": "{debtor_name}与{company}签订{contract_type}，合同金额{amount}元，约定履行期限{deadline}。现{debtor_name}违约，拒不履行合同义务，已造成经济损失。需要律师发函要求其履行合同或承担违约责任。",
        "case_type": "合同纠纷"
    },
    {
        "type": "credit_card",
        "title_template": "{bank}信用卡逾期催收案", 
        "description_template": "持卡人{debtor_name}，身份证号{id_card}，信用卡账户透支{amount}元，已逾期{overdue_days}天。持卡人联系电话{phone}，账单地址{address}。银行已通过电话、短信等方式催收，但持卡人仍未还款，现委托律师函催收。",
        "case_type": "信用卡逾期"
    },
    {
        "type": "loan_overdue",
        "title_template": "{company}个人贷款逾期案",
        "description_template": "借款人{debtor_name}于{loan_date}向{company}申请个人消费贷款{amount}元，月利率{rate}%，期限{term}个月。现已逾期{overdue_days}天，欠本金{principal}元，利息{interest}元，违约金{penalty}元，合计{total}元。",
        "case_type": "个人贷款"
    },
    {
        "type": "rent_dispute",
        "title_template": "{landlord}房租纠纷案",
        "description_template": "承租人{debtor_name}承租{landlord}位于{address}的房屋，月租金{rent}元。现承租人拖欠租金{amount}元（共{months}个月），经催告仍不支付。房东要求解除租赁合同并追收欠款。",
        "case_type": "房租纠纷"
    }
]

# 公司名称
COMPANIES = [
    "北京京东金融科技有限公司", "上海蚂蚁金服信息技术有限公司", "深圳腾讯金融科技有限公司",
    "杭州阿里小贷有限公司", "广州平安普惠企业管理有限公司", "成都宜信普惠信息咨询有限公司",
    "南京苏宁金融服务有限公司", "武汉360金融信息服务有限公司", "重庆小米金融科技有限公司",
    "西安招商银行消费金融有限公司", "郑州中原银行股份有限公司", "青岛海尔消费金融有限公司",
    "大连恒信普惠信息咨询有限公司", "沈阳盛京银行股份有限公司", "长春吉林银行股份有限公司",
    "哈尔滨北方金融控股有限公司", "石家庄河北银行股份有限公司", "太原晋商银行股份有限公司",
    "呼和浩特内蒙古银行股份有限公司", "兰州甘肃银行股份有限公司", "银川宁夏银行股份有限公司",
    "乌鲁木齐新疆汇和银行有限公司", "拉萨西藏银行股份有限公司", "昆明富滇银行股份有限公司",
    "贵阳贵州银行股份有限公司", "南宁广西北部湾银行股份有限公司", "海口海南银行股份有限公司"
]

# 银行名称
BANKS = [
    "中国工商银行", "中国建设银行", "中国农业银行", "中国银行", "交通银行",
    "招商银行", "浦发银行", "中信银行", "光大银行", "华夏银行",
    "民生银行", "广发银行", "兴业银行", "平安银行", "上海银行"
]

# 平台名称
PLATFORMS = [
    "京东金融", "支付宝借呗", "微信微粒贷", "360借条", "小米贷款",
    "苏宁任性付", "唯品花", "美团借钱", "滴滴金融", "拍拍贷",
    "宜人贷", "人人贷", "有利网", "陆金所", "爱钱进"
]

# 姓名库
NAMES = [
    "王伟", "李娜", "张强", "刘敏", "陈静", "杨军", "赵丽", "黄勇", "周芳", "吴涛",
    "朱霞", "郭斌", "马晨", "孙宇", "李明", "王芳", "张杰", "刘强", "陈薇", "杨帆",
    "赵磊", "黄婷", "周鑫", "吴雪", "朱彬", "郭颖", "马超", "孙燕", "李峰", "王静",
    "张敏", "刘涛", "陈刚", "杨雷", "赵星", "黄丽", "周浩", "吴洁", "朱晶", "郭健",
    "马璐", "孙伟", "李慧", "王飞", "张艳", "刘娟", "陈斌", "杨梅", "赵林", "黄阳"
]

# 地址前缀
ADDRESS_PREFIXES = [
    "北京市朝阳区", "上海市浦东新区", "广州市天河区", "深圳市南山区", "杭州市西湖区",
    "南京市秦淮区", "成都市锦江区", "武汉市武昌区", "重庆市渝中区", "西安市雁塔区",
    "郑州市金水区", "青岛市市南区", "大连市沙河口区", "沈阳市和平区", "长春市朝阳区",
    "哈尔滨市南岗区", "石家庄市长安区", "太原市小店区", "呼和浩特市新城区", "兰州市城关区"
]

# 合同类型
CONTRACT_TYPES = [
    "服务合同", "采购合同", "租赁合同", "装修合同", "技术合同",
    "销售合同", "代理合同", "咨询合同", "运输合同", "保险合同"
]

def generate_phone():
    """生成随机手机号"""
    prefixes = ['130', '131', '132', '133', '134', '135', '136', '137', '138', '139',
                '150', '151', '152', '153', '155', '156', '157', '158', '159',
                '170', '171', '172', '173', '175', '176', '177', '178',
                '180', '181', '182', '183', '184', '185', '186', '187', '188', '189']
    return random.choice(prefixes) + ''.join([str(random.randint(0, 9)) for _ in range(8)])

def generate_id_card():
    """生成随机身份证号"""
    area_codes = ['110101', '310101', '440101', '440301', '330101', 
                  '320101', '510101', '420101', '500101', '610101']
    area = random.choice(area_codes)
    birth_year = random.randint(1970, 2000)
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    sequence = random.randint(100, 999)
    return f"{area}{birth_year}{birth_month:02d}{birth_day:02d}{sequence}X"

def generate_address():
    """生成随机地址"""
    prefix = random.choice(ADDRESS_PREFIXES)
    street = f"{random.choice(['中山', '人民', '解放', '建设', '和平', '友谊', '光明', '胜利'])}路"
    number = random.randint(1, 999)
    unit = random.randint(1, 50)
    room = random.randint(101, 2999)
    return f"{prefix}{street}{number}号{unit}单元{room}室"

async def create_realistic_tasks():
    """创建真实的案件任务数据"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("🚀 开始创建真实案件任务数据...")
            
            # 获取租户ID
            tenant_query = text("SELECT id FROM tenants LIMIT 1")
            tenant_result = await session.execute(tenant_query)
            tenant_id = tenant_result.scalar()
            
            # 获取律师和销售用户
            lawyers_query = text("SELECT id FROM users WHERE username LIKE 'lawyer%'")
            lawyers_result = await session.execute(lawyers_query)
            lawyers = [row[0] for row in lawyers_result.fetchall()]
            
            sales_query = text("SELECT id FROM users WHERE username LIKE 'sales%'")
            sales_result = await session.execute(sales_query)
            sales_users = [row[0] for row in sales_result.fetchall()]
            
            print(f"✅ 找到 {len(lawyers)} 个律师, {len(sales_users)} 个销售")
            
            # 创建一些客户数据（如果不存在的话）
            client_names = [
                "北京科技有限公司", "上海贸易集团", "广州制造企业", "深圳创新公司", "杭州电商平台",
                "南京软件开发", "成都金融服务", "武汉物流公司", "重庆建筑集团", "西安能源企业",
                "郑州农业合作社", "青岛海洋科技", "大连港务集团", "沈阳重工业", "长春汽车制造",
                "哈尔滨食品加工", "石家庄钢铁公司", "太原煤炭集团", "呼和浩特牧业", "兰州化工企业"
            ]
            
            clients = []
            for name in client_names:
                # 检查客户是否已存在
                check_client = await session.execute(text("SELECT id FROM clients WHERE name = :name"), {'name': name})
                existing_client = check_client.fetchone()
                
                if not existing_client:
                    # 创建新客户
                    client_id = str(uuid4())
                    create_client_sql = text("""
                        INSERT INTO clients (id, tenant_id, name, contact_person, contact_phone, contact_email, address, sales_owner_id, created_at, updated_at)
                        VALUES (:id, :tenant_id, :name, :contact, :phone, :email, :address, :sales_owner, :created_at, :updated_at)
                    """)
                    
                    await session.execute(create_client_sql, {
                        'id': client_id,
                        'tenant_id': tenant_id,
                        'name': name,
                        'contact': f"{name}联系人",
                        'phone': f"400{random.randint(1000000, 9999999)}",
                        'email': f"contact@{name.replace('有限公司', '').replace('集团', '').replace('企业', '')}.com",
                        'address': f"{random.choice(['北京', '上海', '广州', '深圳', '杭州'])}市{random.choice(['朝阳区', '浦东新区', '天河区', '南山区', '西湖区'])}{random.choice(['建国路', '中山路', '解放路', '人民路'])}123号",
                        'sales_owner': random.choice(sales_users) if sales_users else None,
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    })
                    clients.append((client_id, name))
                else:
                    clients.append((existing_client[0], name))
            
            # 创建100个案件
            cases_created = 0
            for i in range(100):
                try:
                    # 随机选择案件模板
                    template = random.choice(CASE_TEMPLATES)
                    
                    # 生成债务人信息
                    debtor_name = random.choice(NAMES)
                    debtor_phone = generate_phone()
                    debtor_id_card = generate_id_card()
                    debtor_address = generate_address()
                    
                    # 生成案件金额和时间
                    amount = random.randint(5000, 500000)
                    overdue_days = random.randint(30, 365)
                    loan_date = (datetime.now() - timedelta(days=overdue_days + random.randint(30, 180))).strftime('%Y年%m月%d日')
                    deadline = (datetime.now() - timedelta(days=overdue_days)).strftime('%Y年%m月%d日')
                    
                    # 根据模板生成具体信息
                    case_data = {}
                    
                    if template["type"] == "debt_collection":
                        company = random.choice(COMPANIES)
                        platform = random.choice(PLATFORMS)
                        case_data = {
                            "company": company,
                            "platform": platform,
                            "debtor_name": debtor_name,
                            "loan_date": loan_date,
                            "amount": amount,
                            "deadline": deadline,
                            "overdue_days": overdue_days,
                            "id_card": debtor_id_card,
                            "phone": debtor_phone,
                            "address": debtor_address
                        }
                        
                    elif template["type"] == "contract_dispute":
                        company = random.choice(COMPANIES)
                        contract_type = random.choice(CONTRACT_TYPES)
                        case_data = {
                            "company": company,
                            "contract_type": contract_type,
                            "debtor_name": debtor_name,
                            "amount": amount,
                            "deadline": deadline
                        }
                        
                    elif template["type"] == "credit_card":
                        bank = random.choice(BANKS)
                        case_data = {
                            "bank": bank,
                            "debtor_name": debtor_name,
                            "id_card": debtor_id_card,
                            "amount": amount,
                            "overdue_days": overdue_days,
                            "phone": debtor_phone,
                            "address": debtor_address
                        }
                        
                    elif template["type"] == "loan_overdue":
                        company = random.choice(COMPANIES)
                        rate = round(random.uniform(0.5, 2.0), 2)
                        term = random.randint(6, 36)
                        principal = int(amount * 0.8)
                        interest = int(amount * 0.15)
                        penalty = int(amount * 0.05)
                        total = principal + interest + penalty
                        
                        case_data = {
                            "company": company,
                            "debtor_name": debtor_name,
                            "loan_date": loan_date,
                            "amount": amount,
                            "rate": rate,
                            "term": term,
                            "overdue_days": overdue_days,
                            "principal": principal,
                            "interest": interest,
                            "penalty": penalty,
                            "total": total
                        }
                        
                    elif template["type"] == "rent_dispute":
                        landlord = random.choice(NAMES) + "先生"
                        rent = random.randint(2000, 8000)
                        months = random.randint(2, 6)
                        amount = rent * months
                        
                        case_data = {
                            "landlord": landlord,
                            "debtor_name": debtor_name,
                            "address": debtor_address,
                            "rent": rent,
                            "amount": amount,
                            "months": months
                        }
                    
                    # 生成标题和描述
                    title = template["title_template"].format(**case_data)
                    description = template["description_template"].format(**case_data)
                    
                    # 债务人信息JSON
                    debtor_info = {
                        "name": debtor_name,
                        "phone": debtor_phone,
                        "id_card": debtor_id_card,
                        "address": debtor_address
                    }
                    
                    # 随机分配状态
                    statuses = ['PENDING', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED']
                    weights = [0.4, 0.3, 0.2, 0.1]  # 大部分是待处理和已分配
                    status = random.choices(statuses, weights=weights)[0]
                    
                    # 分配律师（30%概率）
                    assigned_lawyer = random.choice(lawyers) if random.random() < 0.3 and lawyers else None
                    
                    # 随机选择一个客户
                    selected_client = random.choice(clients) if clients else None
                    
                    # 插入案件数据
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
                    
                    case_id = str(uuid4())
                    case_number = f"LAW-2024-{i+1:05d}"
                    
                    # 标签
                    tags = [template["case_type"]]
                    if amount > 100000:
                        tags.append("大额案件")
                    if overdue_days > 180:
                        tags.append("长期逾期")
                    
                    await session.execute(case_sql, {
                        'id': case_id,
                        'tenant_id': tenant_id,
                        'client_id': selected_client[0] if selected_client else None,
                        'case_number': case_number,
                        'debtor_info': json.dumps(debtor_info, ensure_ascii=False),
                        'amount': Decimal(str(amount)),
                        'status': status,
                        'assigned_lawyer': assigned_lawyer,
                        'sales_user': random.choice(sales_users) if sales_users else None,
                        'description': description,
                        'notes': f"案件备注：{title}",
                        'tags': json.dumps(tags, ensure_ascii=False),
                        'debt_date': datetime.now() - timedelta(days=overdue_days + random.randint(30, 180)),
                        'legal_status': 'VALID',
                        'limitation_date': datetime.now() + timedelta(days=random.randint(365, 1095)),
                        'risk_score': random.randint(60, 95),
                        'quality_score': random.randint(70, 100),
                        'freshness_score': random.randint(65, 95),
                        'created_at': datetime.now() - timedelta(days=random.randint(1, 90)),
                        'updated_at': datetime.now()
                    })
                    
                    cases_created += 1
                    
                    if cases_created % 10 == 0:
                        print(f"✅ 已创建 {cases_created} 个案件")
                    
                except Exception as e:
                    print(f"创建案件 {i+1} 失败: {e}")
                    continue
            
            await session.commit()
            print(f"\n🎉 成功创建了 {cases_created} 个真实案件任务！")
            
        except Exception as e:
            print(f"❌ 创建失败: {e}")
            await session.rollback()
            raise

async def main():
    """主函数"""
    try:
        await create_realistic_tasks()
        print("✅ 真实案件任务数据创建完成")
    except Exception as e:
        print(f"💥 创建失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())