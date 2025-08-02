#!/usr/bin/env python3
"""
测试登录页面功能
"""

import requests
import json

def test_login():
    """测试登录功能"""
    url = "https://lawsker.com/api/v1/auth/login"
    
    # 测试用户数据
    test_users = [
        {
            "username": "lawyer1@test.com",
            "password": "123456",
            "description": "律师账号"
        },
        {
            "username": "user1@test.com", 
            "password": "123456",
            "description": "用户账号"
        }
    ]
    
    for user in test_users:
        print(f"\n测试 {user['description']}:")
        print(f"用户名: {user['username']}")
        print(f"密码: {user['password']}")
        
        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "username": user["username"],
                    "password": user["password"]
                },
                timeout=10
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ 登录成功!")
                print(f"用户ID: {data['user']['id']}")
                print(f"用户角色: {data['user']['role']}")
                print(f"用户状态: {data['user']['status']}")
                print(f"访问令牌: {data['access_token'][:50]}...")
            else:
                print(f"❌ 登录失败: {response.text}")
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    test_login() 