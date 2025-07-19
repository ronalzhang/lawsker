#!/usr/bin/env python3
"""
测试任务发布和获取流程
"""

import requests
import json

BASE_URL = "https://lawsker.com/api/v1"

def test_user_registration_and_task_publish():
    """测试用户注册和任务发布"""
    
    # 1. 测试用户注册
    print("🔐 测试用户注册...")
    register_data = {
        "phone": "13800138001",
        "password": "test123456",
        "role": "user",
        "sms_code": "123456",  # 使用测试验证码
        "email": "testuser@example.com",
        "full_name": "测试用户"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        print(f"注册响应状态: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"注册结果: {result}")
        else:
            print(f"注册失败: {response.text}")
            # 可能用户已存在，继续登录测试
    except Exception as e:
        print(f"注册请求异常: {e}")
    
    # 2. 测试用户登录
    print("\n🔑 测试用户登录...")
    login_data = {
        "username": "13800138001",  # 使用手机号登录
        "password": "test123456"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"登录响应状态: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"登录成功: {result}")
            token = result.get("access_token")
            if not token:
                print("❌ 未获取到访问令牌")
                return
        else:
            print(f"登录失败: {response.text}")
            return
    except Exception as e:
        print(f"登录请求异常: {e}")
        return
    
    # 3. 测试任务发布
    print("\n📝 测试任务发布...")
    headers = {"Authorization": f"Bearer {token}"}
    task_data = {
        "task_type": "lawyer_letter",
        "title": "测试债权催收律师函",
        "description": "这是一个测试任务，用于验证任务发布和获取流程",
        "budget": 500,
        "urgency": "normal",
        "target_info": {
            "target_name": "测试目标",
            "contact_phone": "13800138000",
            "contact_address": "测试地址",
            "case_details": "测试案件详情"
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/tasks/user/publish", 
                               json=task_data, headers=headers)
        print(f"任务发布响应状态: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"任务发布成功: {result}")
            task_id = result.get("task_id")
        else:
            print(f"任务发布失败: {response.text}")
            return
    except Exception as e:
        print(f"任务发布请求异常: {e}")
        return
    
    # 4. 测试获取可抢单任务（无认证）
    print("\n📋 测试获取可抢单任务（无认证）...")
    try:
        response = requests.get(f"{BASE_URL}/tasks/available")
        print(f"获取任务响应状态: {response.status_code}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"获取任务请求异常: {e}")
    
    # 5. 测试律师注册和登录
    print("\n👨‍⚖️ 测试律师注册...")
    lawyer_register_data = {
        "phone": "13800138002",
        "password": "test123456",
        "role": "lawyer",
        "sms_code": "123456",  # 使用测试验证码
        "email": "testlawyer@example.com",
        "full_name": "测试律师"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=lawyer_register_data)
        print(f"律师注册响应状态: {response.status_code}")
        if response.status_code != 200:
            print(f"律师注册失败: {response.text}")
    except Exception as e:
        print(f"律师注册请求异常: {e}")
    
    # 6. 律师登录
    print("\n🔑 测试律师登录...")
    lawyer_login_data = {
        "username": "13800138002",  # 使用手机号登录
        "password": "test123456"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=lawyer_login_data)
        print(f"律师登录响应状态: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"律师登录成功: {result}")
            lawyer_token = result.get("access_token")
        else:
            print(f"律师登录失败: {response.text}")
            return
    except Exception as e:
        print(f"律师登录请求异常: {e}")
        return
    
    # 7. 测试律师获取可抢单任务
    print("\n📋 测试律师获取可抢单任务...")
    lawyer_headers = {"Authorization": f"Bearer {lawyer_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/tasks/available", headers=lawyer_headers)
        print(f"律师获取任务响应状态: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"律师获取到的任务: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"律师获取任务失败: {response.text}")
    except Exception as e:
        print(f"律师获取任务请求异常: {e}")

if __name__ == "__main__":
    test_user_registration_and_task_publish()