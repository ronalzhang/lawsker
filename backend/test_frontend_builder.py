#!/usr/bin/env python3
"""
前端构建器测试脚本
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from deployment.frontend_builder import FrontendBuilder, FrontendProject, create_default_projects


def test_node_environment():
    """测试Node.js环境检查"""
    print("=== 测试Node.js环境检查 ===")
    
    projects = create_default_projects()
    builder = FrontendBuilder(projects)
    
    result = builder.check_node_environment()
    print(f"Node.js环境检查结果: {'通过' if result else '失败'}")
    
    return result


def test_project_info():
    """测试项目信息获取"""
    print("\n=== 测试项目信息获取 ===")
    
    projects = create_default_projects()
    builder = FrontendBuilder(projects, base_path=".")
    
    for project in projects:
        print(f"\n--- 项目: {project.name} ---")
        info = builder.get_project_info(project)
        print(json.dumps(info, indent=2, ensure_ascii=False))


def test_version_compare():
    """测试版本比较功能"""
    print("\n=== 测试版本比较 ===")
    
    builder = FrontendBuilder([])
    
    test_cases = [
        ("18.0.0", "18.0.0", True),
        ("18.1.0", "18.0.0", True),
        ("17.9.0", "18.0.0", False),
        ("20.0.0", "18.0.0", True),
        ("8.5.0", "8.0.0", True),
        ("7.9.0", "8.0.0", False)
    ]
    
    for v1, v2, expected in test_cases:
        result = builder._version_compare(v1, v2)
        status = "✓" if result == expected else "✗"
        print(f"{status} {v1} >= {v2}: {result} (期望: {expected})")


def test_build_monitoring():
    """测试构建监控功能"""
    print("\n=== 测试构建监控 ===")
    
    # 创建临时测试项目
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建测试项目结构
        test_project_path = temp_path / "test-project"
        test_project_path.mkdir()
        
        # 创建package.json
        package_json = {
            "name": "test-project",
            "version": "1.0.0",
            "scripts": {
                "build": "echo 'Build completed'"
            },
            "dependencies": {
                "vue": "^3.0.0"
            },
            "devDependencies": {
                "typescript": "^5.0.0"
            }
        }
        
        with open(test_project_path / "package.json", 'w', encoding='utf-8') as f:
            json.dump(package_json, f, indent=2)
        
        # 创建测试项目配置
        test_project = FrontendProject(
            name="test-project",
            path="test-project",
            build_command="echo 'Test build'",
            output_dir="dist",
            nginx_root="/tmp/test",
            domain="test.local"
        )
        
        builder = FrontendBuilder([test_project], base_path=str(temp_path))
        
        # 获取项目信息
        info = builder.get_project_info(test_project)
        print("测试项目信息:")
        print(json.dumps(info, indent=2, ensure_ascii=False))


def test_env_file_loading():
    """测试环境变量文件加载"""
    print("\n=== 测试环境变量文件加载 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        env_file = Path(temp_dir) / ".env.test"
        
        # 创建测试环境文件
        env_content = """
# 测试环境变量
NODE_ENV=production
API_URL=https://api.test.com
DEBUG=false
SECRET_KEY="test-secret-123"
"""
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        builder = FrontendBuilder([])
        env = {}
        builder._load_env_file(env_file, env)
        
        print("加载的环境变量:")
        for key, value in env.items():
            print(f"  {key}={value}")


def main():
    """主测试函数"""
    print("前端构建器测试开始...")
    
    try:
        # 测试Node.js环境
        node_ok = test_node_environment()
        
        # 测试版本比较
        test_version_compare()
        
        # 测试项目信息获取
        test_project_info()
        
        # 测试构建监控
        test_build_monitoring()
        
        # 测试环境变量加载
        test_env_file_loading()
        
        print("\n=== 测试总结 ===")
        print(f"Node.js环境: {'可用' if node_ok else '不可用'}")
        print("其他功能测试完成")
        
        if node_ok:
            print("\n建议: 可以继续进行实际的前端项目构建测试")
        else:
            print("\n建议: 请先安装Node.js 18+和npm 8+")
            
    except Exception as e:
        print(f"测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()