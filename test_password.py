#!/usr/bin/env python3
"""
测试密码验证
"""

import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app.core.security import verify_password

def test_password():
    """测试密码验证"""
    password_hash = "$2b$12$/CMKAwLJ.JFMQNko15.izeZGUGNalEkWlKCu1IUMj5seabkkvR0x2"
    
    # 测试不同的密码
    test_passwords = ["demo123", "password", "123456", "lawyer1"]
    
    for password in test_passwords:
        is_valid = verify_password(password, password_hash)
        print(f"Password '{password}': {is_valid}")

if __name__ == "__main__":
    test_password() 