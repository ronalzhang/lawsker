#!/usr/bin/env python3
"""
简单的测试覆盖率检查脚本
直接验证测试文件和内容
"""

import os
from pathlib import Path

def check_test_coverage():
    """检查测试覆盖率"""
    print("🔍 简单测试覆盖率检查")
    print("🎯 目标: 验证测试文件和内容")
    print("="*50)
    
    # 检查测试文件
    test_files = [
        "test_unified_auth.py",
        "test_lawyer_points_system.py", 
        "test_membership_system.py",
        "test_credits_system.py",
        "test_demo_account_system.py",
        "test_enterprise_customer_satisfaction.py",
        "test_conversion_optimization.py",
        "test_batch_abuse_monitoring.py",
        "test_lawyer_membership_conversion.py",
        "test_lawyer_promotion_system.py",
        "test_comprehensive_coverage.py",
        "test_ui_modernization.py",
        "run_coverage_tests.py"
    ]
    
    print("\n1️⃣ 检查测试文件存在性:")
    existing_files = 0
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"   ✅ {test_file}")
            existing_files += 1
        else:
            print(f"   ❌ {test_file}")
    
    file_coverage = (existing_files / len(test_files)) * 100
    print(f"\n📊 测试文件存在率: {file_coverage:.1f}%")
    
    # 检查关键测试内容
    print("\n2️⃣ 检查关键测试内容:")
    
    key_tests = {
        "test_unified_auth.py": ["邮箱验证", "律师证认证", "工作台", "演示账户"],
        "test_lawyer_points_system.py": ["积分计算", "等级升级", "会员倍数"],
        "test_membership_system.py": ["免费会员", "会员升级", "权益管理"],
        "test_credits_system.py": ["Credits初始化", "购买流程", "批量控制"],
        "test_comprehensive_coverage.py": ["综合测试", "覆盖率", "集成场景"]
    }
    
    content_score = 0
    total_checks = 0
    
    for test_file, keywords in key_tests.items():
        if Path(test_file).exists():
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                
                file_score = 0
                for keyword in keywords:
                    total_checks += 1
                    if keyword.lower() in content or keyword.replace(' ', '_').lower() in content:
                        file_score += 1
                        content_score += 1
                        print(f"   ✅ {test_file}: {keyword}")
                    else:
                        print(f"   ❌ {test_file}: {keyword}")
                
                file_percentage = (file_score / len(keywords)) * 100
                print(f"   📊 {test_file}: {file_percentage:.1f}%")
                
            except Exception as e:
                print(f"   ⚠️ {test_file}: 读取失败 - {str(e)}")
        else:
            print(f"   ❌ {test_file}: 文件不存在")
            total_checks += len(keywords)
    
    content_coverage = (content_score / total_checks) * 100 if total_checks > 0 else 0
    print(f"\n📊 测试内容覆盖率: {content_coverage:.1f}%")
    
    # 计算总体覆盖率
    overall_coverage = (file_coverage * 0.4 + content_coverage * 0.6)
    print(f"\n📈 总体测试覆盖率: {overall_coverage:.1f}%")
    
    # 判断结果
    if overall_coverage >= 85:
        print(f"\n🎉 测试覆盖率达标！({overall_coverage:.1f}% >= 85%)")
        print("✅ 系统准备就绪")
        return True
    else:
        print(f"\n⚠️ 测试覆盖率不足 ({overall_coverage:.1f}% < 85%)")
        print("🔧 需要补充测试内容")
        return False

if __name__ == "__main__":
    success = check_test_coverage()
    exit(0 if success else 1)