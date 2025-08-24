#!/usr/bin/env python3
"""
测试数据生成器
为集成测试生成各种测试数据和场景
"""

import os
import json
import random
import string
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import uuid


class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.test_data_dir = self.project_root / "backend" / "deployment" / "test_data"
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_user_data(self, count: int = 10) -> List[Dict[str, Any]]:
        """生成用户测试数据"""
        users = []
        
        for i in range(count):
            user = {
                "id": str(uuid.uuid4()),
                "username": f"test_user_{i:03d}",
                "email": f"test_user_{i:03d}@example.com",
                "phone": f"1{random.randint(3000000000, 9999999999)}",
                "full_name": f"测试用户 {i:03d}",
                "user_type": random.choice(["individual", "institution"]),
                "status": random.choice(["active", "inactive", "pending"]),
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                "last_login": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "profile": {
                    "avatar": f"https://example.com/avatars/user_{i:03d}.jpg",
                    "bio": f"这是测试用户 {i:03d} 的个人简介",
                    "location": random.choice(["北京", "上海", "广州", "深圳", "杭州"]),
                    "verified": random.choice([True, False])
                }
            }
            users.append(user)
        
        return users
    
    def generate_case_data(self, count: int = 20) -> List[Dict[str, Any]]:
        """生成案例测试数据"""
        cases = []
        case_types = ["合同纠纷", "劳动争议", "交通事故", "房产纠纷", "知识产权"]
        case_statuses = ["pending", "in_progress", "completed", "cancelled"]
        
        for i in range(count):
            case = {
                "id": str(uuid.uuid4()),
                "case_number": f"CASE{datetime.now().year}{i:06d}",
                "title": f"测试案例 {i:03d} - {random.choice(case_types)}",
                "description": f"这是一个关于{random.choice(case_types)}的测试案例，用于验证系统功能。",
                "case_type": random.choice(case_types),
                "status": random.choice(case_statuses),
                "priority": random.choice(["low", "medium", "high", "urgent"]),
                "client_id": str(uuid.uuid4()),
                "lawyer_id": str(uuid.uuid4()) if random.choice([True, False]) else None,
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 180))).isoformat(),
                "updated_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "deadline": (datetime.now() + timedelta(days=random.randint(30, 365))).isoformat(),
                "budget": {
                    "amount": random.randint(1000, 50000),
                    "currency": "CNY",
                    "payment_status": random.choice(["pending", "partial", "paid"])
                },
                "documents": [
                    {
                        "id": str(uuid.uuid4()),
                        "name": f"document_{j}.pdf",
                        "type": "pdf",
                        "size": random.randint(100000, 5000000),
                        "uploaded_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
                    }
                    for j in range(random.randint(1, 5))
                ],
                "timeline": [
                    {
                        "id": str(uuid.uuid4()),
                        "event": f"案例事件 {j}",
                        "description": f"这是案例的第 {j} 个重要事件",
                        "timestamp": (datetime.now() - timedelta(days=random.randint(0, 60))).isoformat(),
                        "user_id": str(uuid.uuid4())
                    }
                    for j in range(random.randint(1, 8))
                ]
            }
            cases.append(case)
        
        return cases
    
    def generate_lawyer_data(self, count: int = 5) -> List[Dict[str, Any]]:
        """生成律师测试数据"""
        lawyers = []
        specialties = ["民事诉讼", "刑事辩护", "公司法务", "知识产权", "劳动法", "房地产法"]
        
        for i in range(count):
            lawyer = {
                "id": str(uuid.uuid4()),
                "license_number": f"L{random.randint(100000, 999999)}",
                "full_name": f"测试律师 {i:03d}",
                "email": f"lawyer_{i:03d}@lawfirm.com",
                "phone": f"1{random.randint(3000000000, 9999999999)}",
                "specialties": random.sample(specialties, random.randint(1, 3)),
                "experience_years": random.randint(1, 30),
                "education": [
                    {
                        "degree": "法学学士",
                        "school": "某某大学法学院",
                        "year": random.randint(1990, 2020)
                    },
                    {
                        "degree": "法学硕士",
                        "school": "某某大学法学院",
                        "year": random.randint(1992, 2022)
                    }
                ],
                "certifications": [
                    {
                        "name": "律师执业证",
                        "issuer": "司法部",
                        "date": (datetime.now() - timedelta(days=random.randint(365, 3650))).isoformat()
                    }
                ],
                "rating": round(random.uniform(3.0, 5.0), 1),
                "cases_handled": random.randint(10, 500),
                "success_rate": round(random.uniform(0.7, 0.95), 2),
                "hourly_rate": random.randint(200, 2000),
                "availability": random.choice(["available", "busy", "unavailable"]),
                "created_at": (datetime.now() - timedelta(days=random.randint(30, 1095))).isoformat(),
                "profile": {
                    "bio": f"资深律师，专注于{random.choice(specialties)}领域，具有丰富的执业经验。",
                    "languages": ["中文", "英文"],
                    "office_address": f"某某市某某区某某街道 {random.randint(1, 999)} 号",
                    "verified": True
                }
            }
            lawyers.append(lawyer)
        
        return lawyers
    
    def generate_document_data(self, count: int = 50) -> List[Dict[str, Any]]:
        """生成文档测试数据"""
        documents = []
        doc_types = ["contract", "evidence", "legal_brief", "court_filing", "correspondence"]
        file_extensions = ["pdf", "doc", "docx", "jpg", "png"]
        
        for i in range(count):
            doc_type = random.choice(doc_types)
            extension = random.choice(file_extensions)
            
            document = {
                "id": str(uuid.uuid4()),
                "name": f"test_document_{i:03d}.{extension}",
                "original_name": f"测试文档_{i:03d}.{extension}",
                "type": doc_type,
                "file_extension": extension,
                "size": random.randint(10000, 10000000),
                "mime_type": self._get_mime_type(extension),
                "case_id": str(uuid.uuid4()),
                "uploaded_by": str(uuid.uuid4()),
                "uploaded_at": (datetime.now() - timedelta(days=random.randint(0, 90))).isoformat(),
                "status": random.choice(["pending", "processed", "approved", "rejected"]),
                "tags": random.sample(["重要", "紧急", "证据", "合同", "法院文件"], random.randint(0, 3)),
                "metadata": {
                    "pages": random.randint(1, 50) if extension == "pdf" else None,
                    "word_count": random.randint(100, 5000) if extension in ["doc", "docx"] else None,
                    "resolution": f"{random.randint(1920, 4096)}x{random.randint(1080, 2160)}" if extension in ["jpg", "png"] else None
                },
                "access_permissions": {
                    "public": False,
                    "client_access": True,
                    "lawyer_access": True,
                    "admin_access": True
                },
                "version": "1.0",
                "checksum": self._generate_checksum()
            }
            documents.append(document)
        
        return documents
    
    def generate_payment_data(self, count: int = 30) -> List[Dict[str, Any]]:
        """生成支付测试数据"""
        payments = []
        payment_methods = ["alipay", "wechat", "bank_transfer", "credit_card"]
        payment_statuses = ["pending", "processing", "completed", "failed", "refunded"]
        
        for i in range(count):
            payment = {
                "id": str(uuid.uuid4()),
                "transaction_id": f"TXN{datetime.now().year}{i:08d}",
                "case_id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "amount": random.randint(100, 50000),
                "currency": "CNY",
                "payment_method": random.choice(payment_methods),
                "status": random.choice(payment_statuses),
                "description": f"案例服务费用支付 - 测试交易 {i:03d}",
                "created_at": (datetime.now() - timedelta(days=random.randint(0, 180))).isoformat(),
                "updated_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "paid_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat() if random.choice([True, False]) else None,
                "refunded_at": None,
                "fee": random.randint(1, 100),
                "gateway_response": {
                    "gateway_id": str(uuid.uuid4()),
                    "gateway_status": "success",
                    "gateway_message": "Payment processed successfully"
                } if random.choice([True, False]) else None
            }
            payments.append(payment)
        
        return payments
    
    def generate_notification_data(self, count: int = 100) -> List[Dict[str, Any]]:
        """生成通知测试数据"""
        notifications = []
        notification_types = ["case_update", "payment_reminder", "document_uploaded", "lawyer_assigned", "system_alert"]
        
        for i in range(count):
            notification = {
                "id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "type": random.choice(notification_types),
                "title": f"测试通知 {i:03d}",
                "message": f"这是一条测试通知消息，用于验证通知系统功能。通知编号：{i:03d}",
                "read": random.choice([True, False]),
                "priority": random.choice(["low", "medium", "high"]),
                "created_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "read_at": (datetime.now() - timedelta(days=random.randint(0, 15))).isoformat() if random.choice([True, False]) else None,
                "data": {
                    "case_id": str(uuid.uuid4()) if random.choice([True, False]) else None,
                    "document_id": str(uuid.uuid4()) if random.choice([True, False]) else None,
                    "action_url": f"/cases/{uuid.uuid4()}" if random.choice([True, False]) else None
                },
                "channels": random.sample(["email", "sms", "push", "in_app"], random.randint(1, 3))
            }
            notifications.append(notification)
        
        return notifications
    
    def generate_api_test_scenarios(self) -> List[Dict[str, Any]]:
        """生成API测试场景"""
        scenarios = [
            {
                "name": "用户注册流程",
                "description": "测试用户注册的完整流程",
                "steps": [
                    {
                        "method": "POST",
                        "endpoint": "/api/v1/auth/register",
                        "data": {
                            "username": "test_user_001",
                            "email": "test@example.com",
                            "password": "test_password_123",
                            "phone": "13800138000"
                        },
                        "expected_status": 201
                    },
                    {
                        "method": "POST",
                        "endpoint": "/api/v1/auth/verify-email",
                        "data": {
                            "email": "test@example.com",
                            "verification_code": "123456"
                        },
                        "expected_status": 200
                    }
                ]
            },
            {
                "name": "用户登录流程",
                "description": "测试用户登录和认证",
                "steps": [
                    {
                        "method": "POST",
                        "endpoint": "/api/v1/auth/login",
                        "data": {
                            "username": "test_user_001",
                            "password": "test_password_123"
                        },
                        "expected_status": 200
                    },
                    {
                        "method": "GET",
                        "endpoint": "/api/v1/users/me",
                        "headers": {
                            "Authorization": "Bearer {token}"
                        },
                        "expected_status": 200
                    }
                ]
            },
            {
                "name": "案例创建流程",
                "description": "测试案例创建的完整流程",
                "steps": [
                    {
                        "method": "POST",
                        "endpoint": "/api/v1/cases",
                        "data": {
                            "title": "测试案例",
                            "description": "这是一个测试案例",
                            "case_type": "合同纠纷",
                            "priority": "medium"
                        },
                        "expected_status": 201
                    },
                    {
                        "method": "GET",
                        "endpoint": "/api/v1/cases/{case_id}",
                        "expected_status": 200
                    }
                ]
            },
            {
                "name": "文档上传流程",
                "description": "测试文档上传功能",
                "steps": [
                    {
                        "method": "POST",
                        "endpoint": "/api/v1/upload",
                        "files": {
                            "file": "test_document.pdf"
                        },
                        "expected_status": 201
                    },
                    {
                        "method": "GET",
                        "endpoint": "/api/v1/documents/{document_id}",
                        "expected_status": 200
                    }
                ]
            }
        ]
        
        return scenarios
    
    def generate_performance_test_data(self) -> Dict[str, Any]:
        """生成性能测试数据"""
        return {
            "load_test_endpoints": [
                {
                    "endpoint": "/api/v1/health",
                    "method": "GET",
                    "weight": 10,
                    "expected_response_time_ms": 100
                },
                {
                    "endpoint": "/api/v1/statistics",
                    "method": "GET",
                    "weight": 5,
                    "expected_response_time_ms": 500
                },
                {
                    "endpoint": "/api/v1/cases",
                    "method": "GET",
                    "weight": 8,
                    "expected_response_time_ms": 300
                },
                {
                    "endpoint": "/",
                    "method": "GET",
                    "weight": 15,
                    "expected_response_time_ms": 200
                }
            ],
            "stress_test_scenarios": [
                {
                    "name": "高并发用户访问",
                    "concurrent_users": 100,
                    "duration_seconds": 300,
                    "ramp_up_seconds": 60
                },
                {
                    "name": "数据库压力测试",
                    "concurrent_users": 50,
                    "duration_seconds": 600,
                    "target_endpoints": ["/api/v1/cases", "/api/v1/users"]
                }
            ],
            "performance_thresholds": {
                "response_time_p95_ms": 1000,
                "response_time_p99_ms": 2000,
                "throughput_rps": 100,
                "error_rate_percent": 1,
                "cpu_usage_percent": 80,
                "memory_usage_percent": 80
            }
        }
    
    def save_test_data(self, data_type: str, data: Any) -> str:
        """保存测试数据到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{data_type}_{timestamp}.json"
        filepath = self.test_data_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        return str(filepath)
    
    def generate_all_test_data(self) -> Dict[str, str]:
        """生成所有测试数据"""
        generated_files = {}
        
        # 生成各种测试数据
        test_data_generators = {
            "users": lambda: self.generate_user_data(20),
            "cases": lambda: self.generate_case_data(50),
            "lawyers": lambda: self.generate_lawyer_data(10),
            "documents": lambda: self.generate_document_data(100),
            "payments": lambda: self.generate_payment_data(50),
            "notifications": lambda: self.generate_notification_data(200),
            "api_scenarios": lambda: self.generate_api_test_scenarios(),
            "performance_data": lambda: self.generate_performance_test_data()
        }
        
        for data_type, generator in test_data_generators.items():
            try:
                data = generator()
                filepath = self.save_test_data(data_type, data)
                generated_files[data_type] = filepath
                print(f"Generated {data_type} test data: {filepath}")
            except Exception as e:
                print(f"Failed to generate {data_type} test data: {str(e)}")
        
        return generated_files
    
    def _get_mime_type(self, extension: str) -> str:
        """获取文件MIME类型"""
        mime_types = {
            "pdf": "application/pdf",
            "doc": "application/msword",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "jpg": "image/jpeg",
            "png": "image/png",
            "txt": "text/plain"
        }
        return mime_types.get(extension, "application/octet-stream")
    
    def _generate_checksum(self) -> str:
        """生成文件校验和"""
        return ''.join(random.choices(string.hexdigits.lower(), k=32))


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Data Generator")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--data-type", choices=["users", "cases", "lawyers", "documents", "payments", "notifications", "all"], 
                       default="all", help="Type of test data to generate")
    parser.add_argument("--count", type=int, default=10, help="Number of records to generate")
    
    args = parser.parse_args()
    
    generator = TestDataGenerator(args.project_root)
    
    if args.data_type == "all":
        generated_files = generator.generate_all_test_data()
        print(f"\nGenerated {len(generated_files)} test data files:")
        for data_type, filepath in generated_files.items():
            print(f"  {data_type}: {filepath}")
    else:
        # 生成特定类型的测试数据
        generators = {
            "users": generator.generate_user_data,
            "cases": generator.generate_case_data,
            "lawyers": generator.generate_lawyer_data,
            "documents": generator.generate_document_data,
            "payments": generator.generate_payment_data,
            "notifications": generator.generate_notification_data
        }
        
        if args.data_type in generators:
            data = generators[args.data_type](args.count)
            filepath = generator.save_test_data(args.data_type, data)
            print(f"Generated {args.data_type} test data: {filepath}")
        else:
            print(f"Unknown data type: {args.data_type}")


if __name__ == "__main__":
    main()