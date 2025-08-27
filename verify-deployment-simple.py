#!/usr/bin/env python3
"""
Lawsker 简化部署验证脚本
验证服务器上的应用是否正常运行
"""
import subprocess
import sys
import time
from datetime import datetime

# 服务器配置
SERVER_IP = "156.232.13.240"
SERVER_PASSWORD = "Pr971V3j"
SERVER_USER = "root"
DOMAIN = "lawsker.com"

def run_remote_command(command):
    """执行远程命令"""
    full_command = f"sshpass -p '{SERVER_PASSWORD}' ssh -o StrictHostKeyChecking=no {SERVER_USER}@{SERVER_IP} '{command}'"
    try:
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timeout"
    except Exception as e:
        return False, "", str(e)

def log_result(test_name, success, message=""):
    """记录测试结果"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if message and not success:
        print(f"   详情: {message}")

def main():
    """主验证函数"""
    print("🚀 Lawsker 部署验证")
    print(f"📅 验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 服务器: {SERVER_IP}")
    print("=" * 50)
    
    total_tests = 0
    passed_tests = 0
    
    # 1. 测试服务器连接
    total_tests += 1
    success, stdout, stderr = run_remote_command("echo 'Connection test'")
    log_result("服务器连接", success, stderr if not success else "")
    if success:
        passed_tests += 1
    
    # 2. 检查PM2状态
    total_tests += 1
    success, stdout, stderr = run_remote_command("pm2 status --nostream")
    log_result("PM2应用状态", success, stderr if not success else "")
    if success:
        passed_tests += 1
        if "lawsker-backend" in stdout and "online" in stdout:
            print("   ✅ lawsker-backend 运行正常")
        else:
            print("   ⚠️ lawsker-backend 状态异常")
    
    # 3. 检查PostgreSQL
    total_tests += 1
    success, stdout, stderr = run_remote_command("systemctl is-active postgresql")
    log_result("PostgreSQL服务", success, stderr if not success else "")
    if success:
        passed_tests += 1
    
    # 4. 检查Nginx
    total_tests += 1
    success, stdout, stderr = run_remote_command("systemctl is-active nginx")
    log_result("Nginx服务", success, stderr if not success else "")
    if success:
        passed_tests += 1
    
    # 5. 检查端口监听
    total_tests += 1
    success, stdout, stderr = run_remote_command("netstat -tuln | grep -E ':80|:8000|:5432'")
    log_result("端口监听", success, "未找到预期端口" if not success else "")
    if success:
        passed_tests += 1
        print(f"   监听端口: {stdout.strip()}")
    
    # 6. 测试API健康检查
    total_tests += 1
    success, stdout, stderr = run_remote_command("curl -f -s http://localhost:8000/api/v1/health")
    log_result("API健康检查", success, stderr if not success else "")
    if success:
        passed_tests += 1
        print(f"   API响应: {stdout.strip()}")
    
    # 7. 测试前端访问
    total_tests += 1
    success, stdout, stderr = run_remote_command("curl -f -s -I http://localhost/")
    log_result("前端页面访问", success, stderr if not success else "")
    if success:
        passed_tests += 1
    
    # 8. 检查数据库连接
    total_tests += 1
    success, stdout, stderr = run_remote_command("sudo -u postgres psql -d lawsker -c 'SELECT 1;'")
    log_result("数据库连接", success, stderr if not success else "")
    if success:
        passed_tests += 1
    
    # 9. 检查应用日志
    total_tests += 1
    success, stdout, stderr = run_remote_command("pm2 logs lawsker-backend --lines 5 --nostream")
    log_result("应用日志检查", success, stderr if not success else "")
    if success:
        passed_tests += 1
        if "error" not in stdout.lower() and "exception" not in stdout.lower():
            print("   ✅ 日志正常，无错误信息")
        else:
            print("   ⚠️ 日志中发现错误信息")
    
    # 10. 检查磁盘空间
    total_tests += 1
    success, stdout, stderr = run_remote_command("df -h / | tail -1")
    log_result("磁盘空间检查", success, stderr if not success else "")
    if success:
        passed_tests += 1
        usage = stdout.split()[4] if stdout else "未知"
        print(f"   磁盘使用率: {usage}")
    
    # 显示总结
    print("\n" + "=" * 50)
    print("📊 验证结果总结")
    print("=" * 50)
    print(f"总测试数: {total_tests}")
    print(f"✅ 通过: {passed_tests}")
    print(f"❌ 失败: {total_tests - passed_tests}")
    print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！系统运行正常。")
        print(f"🌐 访问地址: http://{DOMAIN}")
        return 0
    elif passed_tests >= total_tests * 0.8:
        print("\n⚠️ 大部分测试通过，系统基本正常，但有一些问题需要关注。")
        return 1
    else:
        print("\n❌ 多项测试失败，系统可能存在严重问题。")
        return 2

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ 验证被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 验证过程发生错误: {e}")
        sys.exit(1)