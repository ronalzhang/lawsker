#!/usr/bin/env python3
"""
安全配置加固脚本
检查和应用安全配置加固措施
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.security_hardening import (
    run_security_hardening_check,
    validate_environment_security,
    configure_security_middleware
)
from config.security_config import (
    get_security_config,
    validate_security_config,
    security_settings
)

def print_banner():
    """打印横幅"""
    print("=" * 60)
    print("🔒 LAWSKER系统安全配置加固")
    print("=" * 60)
    print(f"📅 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌍 环境: {security_settings.ENVIRONMENT}")
    print("=" * 60)

def check_system_requirements():
    """检查系统要求"""
    print("\n🔍 检查系统要求...")
    
    requirements = {
        "python": "python3 --version",
        "openssl": "openssl version",
        "nginx": "nginx -v",
    }
    
    missing_tools = []
    
    for tool, command in requirements.items():
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"  ✅ {tool}: 已安装")
            else:
                print(f"  ❌ {tool}: 未找到")
                missing_tools.append(tool)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"  ❌ {tool}: 未找到")
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"\n⚠️  缺少工具: {', '.join(missing_tools)}")
        print("请安装缺少的工具后重新运行")
        return False
    
    return True

def check_environment_variables():
    """检查环境变量"""
    print("\n🔍 检查环境变量...")
    
    required_vars = [
        "SECRET_KEY",
        "ENCRYPTION_MASTER_KEY",
        "DB_PASSWORD",
        "ENVIRONMENT"
    ]
    
    missing_vars = []
    weak_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"  ❌ {var}: 未设置")
        elif len(value) < 32 and var in ["SECRET_KEY", "ENCRYPTION_MASTER_KEY"]:
            weak_vars.append(var)
            print(f"  ⚠️  {var}: 强度不足 (长度: {len(value)})")
        else:
            print(f"  ✅ {var}: 已设置")
    
    if missing_vars:
        print(f"\n❌ 缺少必需的环境变量: {', '.join(missing_vars)}")
        return False
    
    if weak_vars:
        print(f"\n⚠️  以下变量强度不足: {', '.join(weak_vars)}")
        print("建议使用至少32个字符的强密钥")
    
    return True

def generate_ssl_certificate():
    """生成自签名SSL证书（开发环境）"""
    if security_settings.ENVIRONMENT == "production":
        print("⚠️  生产环境请使用正式的SSL证书")
        return True
    
    print("\n🔐 生成SSL证书...")
    
    cert_dir = Path("certs")
    cert_dir.mkdir(exist_ok=True)
    
    cert_file = cert_dir / "server.crt"
    key_file = cert_dir / "server.key"
    
    if cert_file.exists() and key_file.exists():
        print("  ✅ SSL证书已存在")
        return True
    
    try:
        # 生成私钥
        subprocess.run([
            "openssl", "genrsa", "-out", str(key_file), "2048"
        ], check=True, capture_output=True)
        
        # 生成证书
        subprocess.run([
            "openssl", "req", "-new", "-x509", "-key", str(key_file),
            "-out", str(cert_file), "-days", "365", "-subj",
            "/C=CN/ST=Beijing/L=Beijing/O=Lawsker/CN=localhost"
        ], check=True, capture_output=True)
        
        print(f"  ✅ SSL证书已生成: {cert_file}")
        print(f"  ✅ SSL私钥已生成: {key_file}")
        
        # 设置环境变量
        os.environ["SSL_CERT_FILE"] = str(cert_file)
        os.environ["SSL_KEY_FILE"] = str(key_file)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"  ❌ SSL证书生成失败: {e}")
        return False

def create_security_config_files():
    """创建安全配置文件"""
    print("\n📝 创建安全配置文件...")
    
    config_dir = Path("config/security")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建nginx安全配置
    nginx_config = """
# Nginx安全配置
server {
    listen 443 ssl http2;
    server_name lawsker.com;
    
    # SSL配置
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # 隐藏服务器信息
    server_tokens off;
    
    # 限制请求大小
    client_max_body_size 10M;
    
    # 限流配置
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
    
    location /api/v1/auth/login {
        limit_req zone=login burst=3 nodelay;
        proxy_pass http://backend;
    }
    
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://backend;
    }
    
    # 静态文件
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# HTTP重定向到HTTPS
server {
    listen 80;
    server_name lawsker.com;
    return 301 https://$server_name$request_uri;
}
"""
    
    with open(config_dir / "nginx.conf", "w", encoding="utf-8") as f:
        f.write(nginx_config)
    
    print(f"  ✅ Nginx配置已创建: {config_dir / 'nginx.conf'}")
    
    # 创建防火墙配置
    firewall_config = """#!/bin/bash
# 防火墙安全配置

# 清除现有规则
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X

# 设置默认策略
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# 允许本地回环
iptables -A INPUT -i lo -j ACCEPT

# 允许已建立的连接
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# 允许SSH (端口22)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# 允许HTTP和HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# 允许数据库连接（仅本地）
iptables -A INPUT -p tcp -s 127.0.0.1 --dport 5432 -j ACCEPT

# 允许Redis连接（仅本地）
iptables -A INPUT -p tcp -s 127.0.0.1 --dport 6379 -j ACCEPT

# 防止DDoS攻击
iptables -A INPUT -p tcp --dport 80 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT

# 保存规则
iptables-save > /etc/iptables/rules.v4

echo "防火墙配置已应用"
"""
    
    with open(config_dir / "firewall.sh", "w", encoding="utf-8") as f:
        f.write(firewall_config)
    
    os.chmod(config_dir / "firewall.sh", 0o755)
    print(f"  ✅ 防火墙配置已创建: {config_dir / 'firewall.sh'}")
    
    return True

def run_security_checks():
    """运行安全检查"""
    print("\n🔍 运行安全检查...")
    
    try:
        # 验证环境安全
        validate_environment_security()
        print("  ✅ 环境安全验证通过")
        
        # 验证安全配置
        validate_security_config()
        print("  ✅ 安全配置验证通过")
        
        # 运行详细安全检查
        results = run_security_hardening_check()
        
        print(f"\n📊 安全检查结果:")
        print(f"  总体状态: {'✅ 通过' if results['overall_status'] == 'pass' else '❌ 失败'}")
        
        for check_name, check_result in results["checks"].items():
            status_icon = "✅" if check_result["status"] == "pass" else "❌"
            print(f"  {status_icon} {check_name.replace('_', ' ').title()}: {check_result['message']}")
        
        return results["overall_status"] == "pass"
        
    except Exception as e:
        print(f"  ❌ 安全检查失败: {str(e)}")
        return False

def generate_security_report():
    """生成安全报告"""
    print("\n📄 生成安全报告...")
    
    try:
        # 获取安全配置
        config = get_security_config()
        
        # 运行安全检查
        check_results = run_security_hardening_check()
        
        # 生成报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "environment": security_settings.ENVIRONMENT,
            "security_config": config,
            "security_checks": check_results,
            "recommendations": [
                "定期更新系统和依赖包",
                "监控安全日志和异常活动",
                "定期进行安全扫描和渗透测试",
                "实施数据备份和恢复计划",
                "培训员工安全意识",
                "建立安全事件响应流程"
            ]
        }
        
        # 保存报告
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = reports_dir / f"security_hardening_report_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ 安全报告已生成: {report_file}")
        return True
        
    except Exception as e:
        print(f"  ❌ 报告生成失败: {str(e)}")
        return False

def apply_security_hardening():
    """应用安全加固措施"""
    print("\n🔧 应用安全加固措施...")
    
    success_count = 0
    total_count = 0
    
    # 1. 检查系统要求
    total_count += 1
    if check_system_requirements():
        success_count += 1
    
    # 2. 检查环境变量
    total_count += 1
    if check_environment_variables():
        success_count += 1
    
    # 3. 生成SSL证书
    total_count += 1
    if generate_ssl_certificate():
        success_count += 1
    
    # 4. 创建配置文件
    total_count += 1
    if create_security_config_files():
        success_count += 1
    
    # 5. 运行安全检查
    total_count += 1
    if run_security_checks():
        success_count += 1
    
    # 6. 生成安全报告
    total_count += 1
    if generate_security_report():
        success_count += 1
    
    print(f"\n📊 安全加固完成: {success_count}/{total_count} 项成功")
    
    if success_count == total_count:
        print("🎉 所有安全加固措施已成功应用！")
        return True
    else:
        print("⚠️  部分安全加固措施未能完成，请检查错误信息")
        return False

def main():
    """主函数"""
    print_banner()
    
    try:
        success = apply_security_hardening()
        
        if success:
            print("\n✅ 安全配置加固完成")
            print("\n📋 后续步骤:")
            print("  1. 检查生成的配置文件")
            print("  2. 根据环境调整配置参数")
            print("  3. 重启相关服务")
            print("  4. 进行安全测试验证")
            sys.exit(0)
        else:
            print("\n❌ 安全配置加固失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生未预期的错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()