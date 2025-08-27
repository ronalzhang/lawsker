#!/usr/bin/env python3
"""
快速测试覆盖率验证脚本
验证Lawsker业务优化系统新增功能测试覆盖率是否达到85%标准
"""

import os
import sys
from pathlib import Path

def main():
    """主函数"""
    print("🔍 Lawsker 业务优化系统快速测试覆盖率验证")
    print("🎯 目标: 新增功能测试覆盖率 > 85%")
    print("="*60)
    
    # 运行覆盖率验证
    backend_path = Path("backend")
    if not backend_path.exists():
        print("❌ backend目录不存在")
        return 1
    
    # 切换到backend目录并运行验证
    original_cwd = os.getcwd()
    try:
        os.chdir(backend_path)
        
        # 运行验证脚本
        import subprocess
        result = subprocess.run([
            sys.executable, "verify_test_coverage.py"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        return result.returncode
        
    except Exception as e:
        print(f"❌ 验证执行失败: {str(e)}")
        return 1
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    exit_code = main()
    
    if exit_code == 0:
        print("\n🎊 快速验证通过！")
        print("💡 下一步: 可以运行完整测试套件")
        print("   命令: ./backend/run_tests.sh")
    else:
        print("\n💥 快速验证失败！")
        print("🔧 请根据上述建议改进测试覆盖率")
    
    sys.exit(exit_code)