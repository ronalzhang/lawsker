#!/usr/bin/env python3
"""
创建测试任务数据 - 直接数据库操作
绕过API认证，直接向数据库插入测试数据
"""

import os
import sys
from datetime import datetime, timedelta
import uuid
import json

def create_test_data():
    """创建测试用户和任务数据"""
    
    # 生成测试任务数据的SQL
    sql_commands = []
    
    # 1. 创建测试用户（绕过验证码）
    test_users = [
        {
            'id': str(uuid.uuid4()),
            'phone': '13800138001',
            'email': 'testuser1@example.com',
            'password_hash': '$2b$12$rQV7kST7LXZ5nU9wX8YQK.8P5xVXJ7F0.QwE5A9dDsJ7qW2xF5G9e',  # test123456
            'role': 'user',
            'full_name': '张三',
            'status': 'active',
            'created_at': datetime.now() - timedelta(days=5)
        },
        {
            'id': str(uuid.uuid4()),
            'phone': '13800138002', 
            'email': 'testuser2@example.com',
            'password_hash': '$2b$12$rQV7kST7LXZ5nU9wX8YQK.8P5xVXJ7F0.QwE5A9dDsJ7qW2xF5G9e',  # test123456
            'role': 'user',
            'full_name': '李四',
            'status': 'active',
            'created_at': datetime.now() - timedelta(days=3)
        },
        {
            'id': str(uuid.uuid4()),
            'phone': '13800138003',
            'email': 'testlawyer1@example.com', 
            'password_hash': '$2b$12$rQV7kST7LXZ5nU9wX8YQK.8P5xVXJ7F0.QwE5A9dDsJ7qW2xF5G9e',  # test123456
            'role': 'lawyer',
            'full_name': '王律师',
            'status': 'active',
            'created_at': datetime.now() - timedelta(days=7)
        },
        {
            'id': str(uuid.uuid4()),
            'phone': '13800138004',
            'email': 'testlawyer2@example.com',
            'password_hash': '$2b$12$rQV7kST7LXZ5nU9wX8YQK.8P5xVXJ7F0.QwE5A9dDsJ7qW2xF5G9e',  # test123456
            'role': 'lawyer', 
            'full_name': '赵律师',
            'status': 'active',
            'created_at': datetime.now() - timedelta(days=4)
        }
    ]
    
    # 生成用户插入SQL
    for user in test_users:
        sql_commands.append(f"""
INSERT INTO users (id, phone, email, password_hash, role, full_name, status, created_at, updated_at)
VALUES ('{user['id']}', '{user['phone']}', '{user['email']}', '{user['password_hash']}', 
        '{user['role']}', '{user['full_name']}', '{user['status']}', 
        '{user['created_at']}', '{user['created_at']}')
ON CONFLICT (phone) DO NOTHING;
""")
    
    # 2. 创建测试任务发布记录
    user_publishers = [u for u in test_users if u['role'] == 'user']
    
    test_tasks = [
        {
            'id': str(uuid.uuid4()),
            'publisher_id': user_publishers[0]['id'],
            'task_type': 'lawyer_letter',
            'title': '债权催收律师函 #001',
            'description': '需要向欠款人发送正式的债权催收律师函，督促其履行还款义务。债务金额约5万元，欠款时间已超过6个月。',
            'budget': 650,
            'urgency': 'normal',
            'status': 'published',
            'target_info': json.dumps({
                'target_name': '债务人张某',
                'contact_phone': '138****5678',
                'contact_address': '北京市朝阳区某某街道123号',
                'debt_amount': 50000,
                'case_details': '购买商品后拖欠货款，经多次催收未果'
            }),
            'created_at': datetime.now() - timedelta(hours=2)
        },
        {
            'id': str(uuid.uuid4()),
            'publisher_id': user_publishers[0]['id'],
            'task_type': 'debt_collection',
            'title': '企业欠款催收 #002',
            'description': '企业间的货款纠纷，需要专业律师进行催收处理。涉及合同违约，金额较大。',
            'budget': 3500,
            'urgency': 'urgent',
            'status': 'published',
            'target_info': json.dumps({
                'target_name': '某贸易公司',
                'contact_phone': '010-12345678',
                'contact_address': '北京市海淀区科技园区',
                'debt_amount': 180000,
                'case_details': 'B2B贸易货款纠纷，合同明确但对方拖欠'
            }),
            'created_at': datetime.now() - timedelta(hours=1)
        },
        {
            'id': str(uuid.uuid4()),
            'publisher_id': user_publishers[1]['id'], 
            'task_type': 'contract_review',
            'title': '商务合同审查 #003',
            'description': '需要律师审查商务合作合同的条款和风险点，特别是违约责任和争议解决条款。',
            'budget': 1200,
            'urgency': 'normal',
            'status': 'published', 
            'target_info': json.dumps({
                'contract_type': '服务外包合同',
                'contract_value': 500000,
                'key_concerns': '违约责任、知识产权、保密条款',
                'review_deadline': '3个工作日内'
            }),
            'created_at': datetime.now() - timedelta(minutes=30)
        },
        {
            'id': str(uuid.uuid4()),
            'publisher_id': user_publishers[1]['id'],
            'task_type': 'legal_consultation', 
            'title': '法律咨询服务 #004',
            'description': '关于公司经营中的法律问题咨询和建议，涉及劳动法、公司法等多个领域。',
            'budget': 800,
            'urgency': 'normal',
            'status': 'published',
            'target_info': json.dumps({
                'consultation_type': '企业法律顾问咨询',
                'main_issues': '员工关系、合规审查、风险防控',
                'company_size': '中小企业（50-100人）',
                'urgency_level': '一般咨询'
            }),
            'created_at': datetime.now() - timedelta(minutes=45)
        },
        {
            'id': str(uuid.uuid4()),
            'publisher_id': user_publishers[0]['id'],
            'task_type': 'lawyer_letter',
            'title': '违约责任追究函 #005',
            'description': '合同违约后需要发送法律函件追究违约责任，要求对方承担相应的经济损失。',
            'budget': 950,
            'urgency': 'urgent',
            'status': 'published',
            'target_info': json.dumps({
                'target_name': '违约方企业',
                'contract_number': 'HT2024001',
                'violation_details': '延期交付导致损失',
                'claim_amount': 80000,
                'legal_basis': '合同法相关条款'
            }),
            'created_at': datetime.now() - timedelta(minutes=15)
        }
    ]
    
    # 生成任务插入SQL
    for task in test_tasks:
        sql_commands.append(f"""
INSERT INTO task_publish_records (id, publisher_id, task_type, title, description, budget, urgency, status, target_info, created_at, updated_at)
VALUES ('{task['id']}', '{task['publisher_id']}', '{task['task_type']}', '{task['title']}', 
        '{task['description']}', {task['budget']}, '{task['urgency']}', '{task['status']}', 
        '{task['target_info']}', '{task['created_at']}', '{task['created_at']}')
ON CONFLICT (id) DO NOTHING;
""")
    
    # 输出完整的SQL脚本
    print("-- 测试数据插入脚本")
    print("-- 创建时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("-- 说明: 此脚本创建测试用户和任务数据，用于验证系统功能")
    print()
    
    for cmd in sql_commands:
        print(cmd.strip())
        print()
    
    print("-- 验证数据插入")
    print("SELECT COUNT(*) as user_count FROM users WHERE phone LIKE '1380013800%';")
    print("SELECT COUNT(*) as task_count FROM task_publish_records WHERE status = 'published';")
    print("SELECT id, title, budget, urgency, status, created_at FROM task_publish_records WHERE status = 'published' ORDER BY created_at DESC;")
    print()
    
    print("-- 测试登录凭据:")
    print("-- 用户1: 手机号 13800138001, 密码 test123456")
    print("-- 用户2: 手机号 13800138002, 密码 test123456") 
    print("-- 律师1: 手机号 13800138003, 密码 test123456")
    print("-- 律师2: 手机号 13800138004, 密码 test123456")

if __name__ == "__main__":
    create_test_data()