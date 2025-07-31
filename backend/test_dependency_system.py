#!/usr/bin/env python3
"""
依赖管理系统测试脚本
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from deployment.dependency_manager import DependencyManager
from deployment.dependency_validator import DependencyValidator


def test_dependency_manager():
    """测试依赖管理器"""
    print("测试依赖管理器...")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建测试requirements文件
        test_requirements = temp_path / "test_requirements.txt"
        test_requirements.write_text("""
# 测试依赖
fastapi==0.104.1
pydantic==2.5.0
redis==5.0.1
""")
        
        # 创建依赖管理器
        venv_path = temp_path / "test_venv"
        manager = DependencyManager(
            requirements_file=str(test_requirements),
            venv_path=str(venv_path),
            project_root=str(temp_path)
        )
        
        # 测试虚拟环境创建
        print("  - 测试虚拟环境创建...")
        success = manager.create_virtual_environment()
        print(f"    结果: {'✓' if success else '✗'}")
        
        # 测试获取虚拟环境信息
        print("  - 测试获取虚拟环境信息...")
        venv_info = manager.get_virtual_environment_info()
        if venv_info:
            print(f"    Python版本: {venv_info.python_version}")
            print(f"    Pip版本: {venv_info.pip_version}")
            print(f"    路径: {venv_info.path}")
        else:
            print("    ✗ 无法获取虚拟环境信息")
        
        # 测试依赖信息获取
        print("  - 测试依赖信息获取...")
        dep_info = manager.get_dependency_info()
        print(f"    发现依赖包: {len(dep_info)}")
        for name, info in dep_info.items():
            print(f"      {name}: {info.version}")
        
        print("依赖管理器测试完成\n")
        return success


def test_dependency_validator():
    """测试依赖验证器"""
    print("测试依赖验证器...")
    
    # 使用实际的requirements文件进行测试
    requirements_file = Path(__file__).parent / "requirements.txt"
    if not requirements_file.exists():
        print("  ✗ requirements.txt文件不存在，跳过验证器测试")
        return False
    
    # 创建临时虚拟环境路径
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_path = Path(temp_dir) / "validator_test_venv"
        
        # 创建依赖管理器
        manager = DependencyManager(
            requirements_file=str(requirements_file),
            venv_path=str(venv_path),
            project_root=str(Path(__file__).parent)
        )
        
        # 创建验证器
        validator = DependencyValidator(manager)
        
        # 测试依赖信息获取
        print("  - 测试依赖信息获取...")
        dep_info = manager.get_dependency_info()
        print(f"    发现依赖包: {len(dep_info)}")
        
        # 测试单个包兼容性检查
        print("  - 测试单个包兼容性检查...")
        if 'fastapi' in dep_info:
            check_result = validator.check_package_compatibility('fastapi')
            print(f"    FastAPI兼容性: {check_result.compatibility_level}")
        
        # 测试安装报告生成
        print("  - 测试安装报告生成...")
        try:
            report = validator.generate_installation_report()
            print(f"    报告生成成功，包含 {report['summary']['total_required']} 个要求的包")
        except Exception as e:
            print(f"    ✗ 报告生成失败: {str(e)}")
        
        # 测试问题诊断
        print("  - 测试问题诊断...")
        try:
            diagnosis = validator.diagnose_dependency_issues()
            print(f"    诊断完成，发现 {len(diagnosis.get('missing_packages', []))} 个缺失包")
        except Exception as e:
            print(f"    ✗ 诊断失败: {str(e)}")
        
        print("依赖验证器测试完成\n")
        return True


def test_command_line_script():
    """测试命令行脚本"""
    print("测试命令行脚本...")
    
    script_path = Path(__file__).parent / "scripts" / "validate_dependencies.py"
    if not script_path.exists():
        print("  ✗ 命令行脚本不存在")
        return False
    
    # 测试脚本帮助信息
    print("  - 测试脚本帮助信息...")
    import subprocess
    try:
        result = subprocess.run([
            sys.executable, str(script_path), "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "依赖验证和诊断工具" in result.stdout:
            print("    ✓ 帮助信息正常")
        else:
            print("    ✗ 帮助信息异常")
            return False
    except Exception as e:
        print(f"    ✗ 脚本执行失败: {str(e)}")
        return False
    
    print("命令行脚本测试完成\n")
    return True


def main():
    """主测试函数"""
    print("="*60)
    print("依赖管理系统测试")
    print("="*60)
    
    results = []
    
    # 测试依赖管理器
    results.append(test_dependency_manager())
    
    # 测试依赖验证器
    results.append(test_dependency_validator())
    
    # 测试命令行脚本
    results.append(test_command_line_script())
    
    # 总结
    print("="*60)
    print("测试总结")
    print("="*60)
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"测试通过: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("✓ 所有测试通过！")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())