#!/usr/bin/env python3
"""
通过API创建任务测试数据
"""

import requests
import json
import random
import time

# 服务器配置
BASE_URL = "https://lawsker.com/api/v1"

# 测试用户凭据（根据实际情况调整）
TEST_USERS = [
    {"username": "user1", "password": "demo123"},
    {"username": "user2", "password": "demo123"},
    {"username": "user3", "password": "demo123"},
    {"username": "sales1", "password": "demo123"},
    {"username": "sales2", "password": "demo123"}
]

TEST_LAWYERS = [
    {"username": "lawyer1", "password": "demo123"},
    {"username": "lawyer2", "password": "demo123"},
    {"username": "lawyer3", "password": "demo123"},
    {"username": "lawyer4", "password": "demo123"},
    {"username": "lawyer5", "password": "demo123"}
]

# 任务模板
TASK_TEMPLATES = [
    {
        "task_type": "lawyer_letter",
        "title": "债权催收律师函",
        "description": "需要向欠款人发送正式的债权催收律师函，督促其履行还款义务。涉及金额较大，请务必严格按照法律程序处理。",
        "budget_range": (300, 800),
        "urgency": "normal"
    },
    {
        "task_type": "debt_collection", 
        "title": "企业欠款催收",
        "description": "企业间的货款纠纷，需要专业律师进行催收处理。对方公司已逾期3个月未付款，需要采取法律措施。",
        "budget_range": (2000, 8000),
        "urgency": "urgent"
    },
    {
        "task_type": "contract_review",
        "title": "商务合同审查",
        "description": "需要律师审查商务合作合同的条款和风险点。合同金额较大，条款复杂，需要专业法律意见。",
        "budget_range": (500, 2000),
        "urgency": "normal"
    },
    {
        "task_type": "legal_consultation",
        "title": "法律咨询服务",
        "description": "关于公司经营中的法律问题咨询和建议。涉及劳动法、合同法等多个法律领域。",
        "budget_range": (200, 1000),
        "urgency": "low"
    },
    {
        "task_type": "lawyer_letter",
        "title": "违约责任追究函",
        "description": "合同违约后需要发送法律函件追究违约责任。对方严重违约，造成经济损失，需要法律救济。",
        "budget_range": (400, 1200),
        "urgency": "urgent"
    },
    {
        "task_type": "debt_collection",
        "title": "个人借贷纠纷处理", 
        "description": "个人间的借贷纠纷，需要通过法律途径解决。借款人拒不还款，需要采取强制措施。",
        "budget_range": (1000, 5000),
        "urgency": "normal"
    }
]

def login_user(username, password):
    """用户登录获取token"""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", 
                               json={"username": username, "password": password},
                               timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("access_token"):
                return data["access_token"]
        print(f"❌ 用户 {username} 登录失败: {response.status_code}")
        return None
    except Exception as e:
        print(f"❌ 用户 {username} 登录异常: {str(e)}")
        return None

def publish_task(token, task_data):
    """发布任务"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/tasks/user/publish", 
                               json=task_data, 
                               headers=headers,
                               timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ 发布任务失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 发布任务异常: {str(e)}")
        return None

def grab_task(token, task_id):
    """律师抢单"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/tasks/grab/{task_id}", 
                               headers=headers,
                               timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ 抢单失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 抢单异常: {str(e)}")
        return None

def get_available_tasks(token):
    """获取可抢单任务"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/tasks/available", 
                              headers=headers,
                              timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ 获取可抢单任务失败: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ 获取可抢单任务异常: {str(e)}")
        return []

def create_test_data():
    """创建测试数据"""
    print("🚀 开始通过API创建任务测试数据...")
    
    # 1. 用户登录并发布任务
    print("\n📝 第一步：用户发布任务...")
    user_tokens = []
    for user in TEST_USERS:
        token = login_user(user["username"], user["password"])
        if token:
            user_tokens.append((user["username"], token))
            print(f"✅ 用户 {user['username']} 登录成功")
        else:
            print(f"❌ 用户 {user['username']} 登录失败")
    
    if not user_tokens:
        print("❌ 没有用户成功登录，无法继续")
        return
    
    # 发布任务
    published_tasks = []
    for i in range(15):  # 发布15个任务
        user_name, token = random.choice(user_tokens)
        template = random.choice(TASK_TEMPLATES)
        
        task_data = {
            "task_type": template["task_type"],
            "title": f"{template['title']} #{i+1:03d}",
            "description": f"{template['description']} 案件编号: CASE-2024-{i+1:04d}",
            "budget": random.randint(*template["budget_range"]),
            "urgency": template["urgency"],
            "target_info": {
                "target_name": f"目标对象{i+1}",
                "contact_phone": f"1{random.randint(300000000, 999999999)}",
                "contact_address": f"上海市浦东新区张江路{random.randint(100, 999)}号",
                "case_details": f"案件{i+1}的具体情况和要求"
            }
        }
        
        result = publish_task(token, task_data)
        if result and result.get("success"):
            published_tasks.append(result)
            print(f"✅ {user_name} 发布任务: {task_data['title']}")
            time.sleep(0.5)  # 避免请求过于频繁
        else:
            print(f"❌ {user_name} 发布任务失败")
    
    print(f"\n📊 共发布了 {len(published_tasks)} 个任务")
    
    # 2. 律师登录并抢单
    print("\n🎯 第二步：律师抢单...")
    lawyer_tokens = []
    for lawyer in TEST_LAWYERS:
        token = login_user(lawyer["username"], lawyer["password"])
        if token:
            lawyer_tokens.append((lawyer["username"], token))
            print(f"✅ 律师 {lawyer['username']} 登录成功")
        else:
            print(f"❌ 律师 {lawyer['username']} 登录失败")
    
    if not lawyer_tokens:
        print("❌ 没有律师成功登录，跳过抢单步骤")
        return
    
    # 获取可抢单任务并进行抢单
    grabbed_count = 0
    for lawyer_name, token in lawyer_tokens:
        available_tasks = get_available_tasks(token)
        if available_tasks:
            print(f"📋 律师 {lawyer_name} 看到 {len(available_tasks)} 个可抢单任务")
            
            # 随机抢取1-3个任务
            grab_count = random.randint(1, min(3, len(available_tasks)))
            tasks_to_grab = random.sample(available_tasks, grab_count)
            
            for task in tasks_to_grab:
                task_id = task.get("task_id")
                if task_id:
                    result = grab_task(token, task_id)
                    if result and result.get("success"):
                        grabbed_count += 1
                        print(f"✅ 律师 {lawyer_name} 抢单成功: {task.get('title', 'Unknown')}")
                        time.sleep(0.5)
                    else:
                        print(f"❌ 律师 {lawyer_name} 抢单失败: {task.get('title', 'Unknown')}")
        else:
            print(f"📋 律师 {lawyer_name} 没有看到可抢单任务")
    
    print(f"\n🎉 测试数据创建完成!")
    print(f"📊 发布任务: {len(published_tasks)} 个")
    print(f"🎯 抢单成功: {grabbed_count} 个")
    print(f"📋 剩余可抢单: {len(published_tasks) - grabbed_count} 个")
    
    # 3. 验证结果
    print("\n🔍 验证结果...")
    if lawyer_tokens:
        lawyer_name, token = lawyer_tokens[0]
        available_tasks = get_available_tasks(token)
        print(f"✅ 当前可抢单任务数量: {len(available_tasks)}")
        
        # 显示一些任务示例
        for i, task in enumerate(available_tasks[:3]):
            print(f"   {i+1}. {task.get('title', 'Unknown')} - ¥{task.get('budget', 0)}")

if __name__ == "__main__":
    create_test_data()