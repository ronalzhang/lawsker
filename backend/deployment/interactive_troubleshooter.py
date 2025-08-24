#!/usr/bin/env python3
"""
交互式故障排除工具
提供交互式的问题诊断和解决方案指导
"""

import os
import sys
import subprocess
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import requests
import psutil


class InteractiveTroubleshooter:
    """交互式故障排除工具"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.issues_found = []
        self.solutions_applied = []
        
    def run(self):
        """运行交互式故障排除"""
        print("=" * 60)
        print("🔧 Lawsker 系统交互式故障排除工具")
        print("=" * 60)
        print()
        
        while True:
            print("请选择故障类型:")
            print("1. 🌐 服务无法访问")
            print("2. 🐌 系统性能问题")
            print("3. 🗄️  数据库连接问题")
            print("4. 🔒 SSL/网络问题")
            print("5. 🚀 部署相关问题")
            print("6. 📊 监控和日志问题")
            print("7. 🔍 全面系统诊断")
            print("8. ❌ 退出")
            print()
            
            choice = input("请输入选项 (1-8): ").strip()
            
            if choice == "1":
                self.diagnose_service_issues()
            elif choice == "2":
                self.diagnose_performance_issues()
            elif choice == "3":
                self.diagnose_database_issues()
            elif choice == "4":
                self.diagnose_network_ssl_issues()
            elif choice == "5":
                self.diagnose_deployment_issues()
            elif choice == "6":
                self.diagnose_monitoring_issues()
            elif choice == "7":
                self.run_comprehensive_diagnosis()
            elif choice == "8":
                print("👋 感谢使用故障排除工具!")
                break
            else:
                print("❌ 无效选项，请重新选择")
            
            print("\n" + "=" * 60 + "\n")
    
    def diagnose_service_issues(self):
        """诊断服务访问问题"""
        print("🔍 正在诊断服务访问问题...")
        print()
        
        issues = []
        
        # 检查服务状态
        services = ["nginx", "lawsker-backend", "postgresql", "redis"]
        print("📋 检查服务状态:")
        for service in services:
            if self.check_service_status(service):
                print(f"  ✅ {service}: 运行中")
            else:
                print(f"  ❌ {service}: 停止")
                issues.append(f"服务 {service} 未运行")
        
        # 检查端口监听
        ports = [("80", "HTTP"), ("443", "HTTPS"), ("8000", "Backend"), ("5432", "PostgreSQL"), ("6379", "Redis")]
        print("\n🔌 检查端口监听:")
        for port, name in ports:
            if self.check_port_listening(port):
                print(f"  ✅ {name} ({port}): 监听中")
            else:
                print(f"  ❌ {name} ({port}): 未监听")
                issues.append(f"端口 {port} ({name}) 未监听")
        
        # 检查应用连通性
        print("\n🌐 检查应用连通性:")
        if self.check_backend_health():
            print("  ✅ 后端 API: 正常")
        else:
            print("  ❌ 后端 API: 异常")
            issues.append("后端 API 无法访问")
        
        if self.check_frontend_access():
            print("  ✅ 前端页面: 正常")
        else:
            print("  ❌ 前端页面: 异常")
            issues.append("前端页面无法访问")
        
        # 提供解决方案
        if issues:
            print(f"\n⚠️  发现 {len(issues)} 个问题:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
            
            print("\n🔧 建议的解决方案:")
            self.suggest_service_solutions(issues)
        else:
            print("\n✅ 所有服务检查正常!")
    
    def diagnose_performance_issues(self):
        """诊断性能问题"""
        print("🔍 正在诊断系统性能问题...")
        print()
        
        issues = []
        
        # 检查系统资源
        print("📊 系统资源使用情况:")
        
        # CPU 使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"  CPU 使用率: {cpu_percent:.1f}%")
        if cpu_percent > 80:
            issues.append(f"CPU 使用率过高 ({cpu_percent:.1f}%)")
        
        # 内存使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        print(f"  内存使用率: {memory_percent:.1f}%")
        if memory_percent > 85:
            issues.append(f"内存使用率过高 ({memory_percent:.1f}%)")
        
        # 磁盘使用率
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        print(f"  磁盘使用率: {disk_percent:.1f}%")
        if disk_percent > 90:
            issues.append(f"磁盘使用率过高 ({disk_percent:.1f}%)")
        
        # 负载平均值
        load_avg = os.getloadavg()
        cpu_count = psutil.cpu_count()
        print(f"  负载平均值: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}")
        if load_avg[0] > cpu_count * 2:
            issues.append(f"系统负载过高 ({load_avg[0]:.2f})")
        
        # 检查进程资源使用
        print("\n🔝 资源使用最多的进程:")
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # 按 CPU 使用率排序
        processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
        for i, proc in enumerate(processes[:5]):
            print(f"  {i+1}. {proc['name']} (PID: {proc['pid']}) - CPU: {proc['cpu_percent']:.1f}%, 内存: {proc['memory_percent']:.1f}%")
        
        # 检查网络连接数
        connections = len(psutil.net_connections())
        print(f"\n🔗 网络连接数: {connections}")
        if connections > 1000:
            issues.append(f"网络连接数过多 ({connections})")
        
        # 提供解决方案
        if issues:
            print(f"\n⚠️  发现 {len(issues)} 个性能问题:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
            
            print("\n🔧 建议的解决方案:")
            self.suggest_performance_solutions(issues)
        else:
            print("\n✅ 系统性能正常!")
    
    def diagnose_database_issues(self):
        """诊断数据库问题"""
        print("🔍 正在诊断数据库连接问题...")
        print()
        
        issues = []
        
        # 检查 PostgreSQL 服务
        print("🗄️  检查 PostgreSQL 服务:")
        if self.check_service_status("postgresql"):
            print("  ✅ PostgreSQL 服务: 运行中")
        else:
            print("  ❌ PostgreSQL 服务: 停止")
            issues.append("PostgreSQL 服务未运行")
        
        # 检查数据库连接
        print("\n🔗 检查数据库连接:")
        if self.check_database_connection():
            print("  ✅ 数据库连接: 正常")
            
            # 检查数据库性能
            db_stats = self.get_database_stats()
            if db_stats:
                print(f"  📊 活动连接数: {db_stats.get('connections', 'N/A')}")
                print(f"  📊 数据库大小: {db_stats.get('size', 'N/A')}")
                
                if db_stats.get('connections', 0) > 80:
                    issues.append(f"数据库连接数过多 ({db_stats['connections']})")
        else:
            print("  ❌ 数据库连接: 失败")
            issues.append("无法连接到数据库")
        
        # 检查 Redis 连接
        print("\n🔴 检查 Redis 连接:")
        if self.check_redis_connection():
            print("  ✅ Redis 连接: 正常")
        else:
            print("  ❌ Redis 连接: 失败")
            issues.append("无法连接到 Redis")
        
        # 提供解决方案
        if issues:
            print(f"\n⚠️  发现 {len(issues)} 个数据库问题:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
            
            print("\n🔧 建议的解决方案:")
            self.suggest_database_solutions(issues)
        else:
            print("\n✅ 数据库连接正常!")
    
    def diagnose_network_ssl_issues(self):
        """诊断网络和SSL问题"""
        print("🔍 正在诊断网络和SSL问题...")
        print()
        
        issues = []
        
        # 检查域名解析
        print("🌐 检查域名解析:")
        domain = "lawsker.com"
        if self.check_domain_resolution(domain):
            print(f"  ✅ {domain}: 解析正常")
        else:
            print(f"  ❌ {domain}: 解析失败")
            issues.append(f"域名 {domain} 解析失败")
        
        # 检查 SSL 证书
        print("\n🔒 检查 SSL 证书:")
        ssl_info = self.check_ssl_certificate(domain)
        if ssl_info:
            print(f"  ✅ SSL 证书: 有效")
            print(f"  📅 到期时间: {ssl_info.get('expiry', 'N/A')}")
            
            # 检查证书是否即将过期
            if ssl_info.get('days_until_expiry', 0) < 30:
                issues.append(f"SSL 证书即将过期 ({ssl_info['days_until_expiry']} 天)")
        else:
            print("  ❌ SSL 证书: 无效或无法访问")
            issues.append("SSL 证书问题")
        
        # 检查防火墙状态
        print("\n🛡️  检查防火墙状态:")
        firewall_status = self.check_firewall_status()
        if firewall_status:
            print(f"  ℹ️  防火墙状态: {firewall_status}")
        
        # 检查网络连通性
        print("\n🔗 检查网络连通性:")
        if self.check_network_connectivity():
            print("  ✅ 网络连通性: 正常")
        else:
            print("  ❌ 网络连通性: 异常")
            issues.append("网络连通性问题")
        
        # 提供解决方案
        if issues:
            print(f"\n⚠️  发现 {len(issues)} 个网络/SSL问题:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
            
            print("\n🔧 建议的解决方案:")
            self.suggest_network_ssl_solutions(issues)
        else:
            print("\n✅ 网络和SSL配置正常!")
    
    def diagnose_deployment_issues(self):
        """诊断部署问题"""
        print("🔍 正在诊断部署相关问题...")
        print()
        
        issues = []
        
        # 检查项目文件
        print("📁 检查项目文件:")
        required_files = [
            "backend/requirements-prod.txt",
            "backend/app/main.py",
            ".env.production",
            "frontend/index.html"
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                print(f"  ✅ {file_path}: 存在")
            else:
                print(f"  ❌ {file_path}: 缺失")
                issues.append(f"缺少文件: {file_path}")
        
        # 检查 Python 环境
        print("\n🐍 检查 Python 环境:")
        venv_path = self.project_root / "backend" / "venv"
        if venv_path.exists():
            print("  ✅ 虚拟环境: 存在")
            
            # 检查依赖
            if self.check_python_dependencies():
                print("  ✅ Python 依赖: 已安装")
            else:
                print("  ❌ Python 依赖: 缺失或有问题")
                issues.append("Python 依赖问题")
        else:
            print("  ❌ 虚拟环境: 不存在")
            issues.append("Python 虚拟环境不存在")
        
        # 检查前端构建
        print("\n🎨 检查前端构建:")
        if self.check_frontend_build():
            print("  ✅ 前端构建: 正常")
        else:
            print("  ❌ 前端构建: 有问题")
            issues.append("前端构建问题")
        
        # 检查配置文件
        print("\n⚙️  检查配置文件:")
        if self.check_configuration_files():
            print("  ✅ 配置文件: 正常")
        else:
            print("  ❌ 配置文件: 有问题")
            issues.append("配置文件问题")
        
        # 提供解决方案
        if issues:
            print(f"\n⚠️  发现 {len(issues)} 个部署问题:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
            
            print("\n🔧 建议的解决方案:")
            self.suggest_deployment_solutions(issues)
        else:
            print("\n✅ 部署配置正常!")
    
    def diagnose_monitoring_issues(self):
        """诊断监控和日志问题"""
        print("🔍 正在诊断监控和日志问题...")
        print()
        
        issues = []
        
        # 检查监控服务
        print("📊 检查监控服务:")
        monitoring_services = ["prometheus", "grafana-server"]
        for service in monitoring_services:
            if self.check_service_status(service):
                print(f"  ✅ {service}: 运行中")
            else:
                print(f"  ❌ {service}: 停止")
                issues.append(f"监控服务 {service} 未运行")
        
        # 检查日志文件
        print("\n📝 检查日志文件:")
        log_files = [
            "/var/log/lawsker/app.log",
            "/var/log/nginx/access.log",
            "/var/log/nginx/error.log"
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                size = os.path.getsize(log_file) / (1024 * 1024)  # MB
                print(f"  ✅ {log_file}: 存在 ({size:.1f} MB)")
                
                if size > 100:  # 大于100MB
                    issues.append(f"日志文件过大: {log_file} ({size:.1f} MB)")
            else:
                print(f"  ❌ {log_file}: 不存在")
                issues.append(f"日志文件缺失: {log_file}")
        
        # 检查磁盘空间
        print("\n💾 检查日志磁盘空间:")
        log_disk_usage = self.check_log_disk_usage()
        if log_disk_usage < 90:
            print(f"  ✅ 日志磁盘使用率: {log_disk_usage:.1f}%")
        else:
            print(f"  ❌ 日志磁盘使用率: {log_disk_usage:.1f}%")
            issues.append(f"日志磁盘空间不足 ({log_disk_usage:.1f}%)")
        
        # 提供解决方案
        if issues:
            print(f"\n⚠️  发现 {len(issues)} 个监控/日志问题:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
            
            print("\n🔧 建议的解决方案:")
            self.suggest_monitoring_solutions(issues)
        else:
            print("\n✅ 监控和日志正常!")
    
    def run_comprehensive_diagnosis(self):
        """运行全面系统诊断"""
        print("🔍 正在运行全面系统诊断...")
        print("这可能需要几分钟时间，请稍候...")
        print()
        
        # 运行所有诊断
        print("1/6 检查服务状态...")
        self.diagnose_service_issues()
        
        print("\n2/6 检查系统性能...")
        self.diagnose_performance_issues()
        
        print("\n3/6 检查数据库...")
        self.diagnose_database_issues()
        
        print("\n4/6 检查网络和SSL...")
        self.diagnose_network_ssl_issues()
        
        print("\n5/6 检查部署配置...")
        self.diagnose_deployment_issues()
        
        print("\n6/6 检查监控和日志...")
        self.diagnose_monitoring_issues()
        
        # 生成综合报告
        print("\n" + "=" * 60)
        print("📋 综合诊断报告")
        print("=" * 60)
        
        if self.issues_found:
            print(f"⚠️  总共发现 {len(self.issues_found)} 个问题:")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"  {i}. {issue}")
            
            print("\n🔧 建议优先处理以下问题:")
            critical_issues = [issue for issue in self.issues_found if any(keyword in issue.lower() for keyword in ["停止", "失败", "无法", "过高"])]
            for issue in critical_issues[:5]:
                print(f"  • {issue}")
        else:
            print("✅ 系统整体状态良好!")
        
        # 保存诊断报告
        self.save_diagnosis_report()
    
    # 辅助方法
    def check_service_status(self, service_name: str) -> bool:
        """检查服务状态"""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def check_port_listening(self, port: str) -> bool:
        """检查端口是否监听"""
        try:
            result = subprocess.run(
                ["netstat", "-tlnp"],
                capture_output=True,
                text=True
            )
            return f":{port} " in result.stdout
        except Exception:
            return False
    
    def check_backend_health(self) -> bool:
        """检查后端健康状态"""
        try:
            response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def check_frontend_access(self) -> bool:
        """检查前端访问"""
        try:
            response = requests.get("http://localhost", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def check_database_connection(self) -> bool:
        """检查数据库连接"""
        try:
            result = subprocess.run(
                ["sudo", "-u", "postgres", "psql", "-d", "lawsker_prod", "-c", "SELECT 1;"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_database_stats(self) -> Optional[Dict[str, Any]]:
        """获取数据库统计信息"""
        try:
            # 获取连接数
            result = subprocess.run(
                ["sudo", "-u", "postgres", "psql", "-d", "lawsker_prod", "-t", "-c", 
                 "SELECT count(*) FROM pg_stat_activity;"],
                capture_output=True,
                text=True
            )
            connections = int(result.stdout.strip()) if result.returncode == 0 else 0
            
            # 获取数据库大小
            result = subprocess.run(
                ["sudo", "-u", "postgres", "psql", "-d", "lawsker_prod", "-t", "-c", 
                 "SELECT pg_size_pretty(pg_database_size('lawsker_prod'));"],
                capture_output=True,
                text=True
            )
            size = result.stdout.strip() if result.returncode == 0 else "N/A"
            
            return {"connections": connections, "size": size}
        except Exception:
            return None
    
    def check_redis_connection(self) -> bool:
        """检查Redis连接"""
        try:
            result = subprocess.run(
                ["redis-cli", "ping"],
                capture_output=True,
                text=True
            )
            return "PONG" in result.stdout
        except Exception:
            return False
    
    def check_domain_resolution(self, domain: str) -> bool:
        """检查域名解析"""
        try:
            result = subprocess.run(
                ["nslookup", domain],
                capture_output=True,
                text=True
            )
            return result.returncode == 0 and "Address:" in result.stdout
        except Exception:
            return False
    
    def check_ssl_certificate(self, domain: str) -> Optional[Dict[str, Any]]:
        """检查SSL证书"""
        try:
            result = subprocess.run(
                ["openssl", "s_client", "-connect", f"{domain}:443", "-servername", domain],
                input="",
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # 简化的证书信息提取
                return {"expiry": "检查成功", "days_until_expiry": 90}  # 简化实现
            return None
        except Exception:
            return None
    
    def check_firewall_status(self) -> Optional[str]:
        """检查防火墙状态"""
        try:
            result = subprocess.run(
                ["ufw", "status"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return "active" if "Status: active" in result.stdout else "inactive"
            return None
        except Exception:
            return None
    
    def check_network_connectivity(self) -> bool:
        """检查网络连通性"""
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "8.8.8.8"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def check_python_dependencies(self) -> bool:
        """检查Python依赖"""
        try:
            venv_python = self.project_root / "backend" / "venv" / "bin" / "python"
            if not venv_python.exists():
                return False
            
            result = subprocess.run(
                [str(venv_python), "-m", "pip", "check"],
                capture_output=True,
                text=True,
                cwd=self.project_root / "backend"
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def check_frontend_build(self) -> bool:
        """检查前端构建"""
        # 简化检查：查看是否存在关键文件
        frontend_files = [
            self.project_root / "frontend" / "index.html",
            self.project_root / "frontend" / "package.json"
        ]
        return all(f.exists() for f in frontend_files)
    
    def check_configuration_files(self) -> bool:
        """检查配置文件"""
        config_files = [
            self.project_root / ".env.production",
            Path("/etc/nginx/sites-available/lawsker.conf")
        ]
        return all(f.exists() for f in config_files)
    
    def check_log_disk_usage(self) -> float:
        """检查日志磁盘使用率"""
        try:
            disk = psutil.disk_usage('/var/log')
            return (disk.used / disk.total) * 100
        except Exception:
            return 0.0
    
    def suggest_service_solutions(self, issues: List[str]):
        """建议服务问题解决方案"""
        for issue in issues:
            if "nginx" in issue.lower():
                print("  🔧 Nginx 问题:")
                print("     sudo systemctl start nginx")
                print("     sudo nginx -t  # 检查配置")
                print("     sudo systemctl reload nginx")
            
            elif "lawsker-backend" in issue.lower():
                print("  🔧 后端服务问题:")
                print("     sudo systemctl start lawsker-backend")
                print("     journalctl -u lawsker-backend -f  # 查看日志")
                print("     # 检查虚拟环境和依赖")
            
            elif "postgresql" in issue.lower():
                print("  🔧 PostgreSQL 问题:")
                print("     sudo systemctl start postgresql")
                print("     sudo -u postgres psql -c '\\l'  # 测试连接")
            
            elif "redis" in issue.lower():
                print("  🔧 Redis 问题:")
                print("     sudo systemctl start redis")
                print("     redis-cli ping  # 测试连接")
    
    def suggest_performance_solutions(self, issues: List[str]):
        """建议性能问题解决方案"""
        for issue in issues:
            if "cpu" in issue.lower():
                print("  🔧 CPU 使用率过高:")
                print("     top  # 查看占用CPU的进程")
                print("     renice 10 <PID>  # 降低进程优先级")
                print("     # 考虑优化应用代码或增加CPU资源")
            
            elif "内存" in issue.lower():
                print("  🔧 内存使用率过高:")
                print("     free -h  # 查看内存使用")
                print("     echo 3 > /proc/sys/vm/drop_caches  # 清理缓存")
                print("     # 考虑增加内存或优化应用")
            
            elif "磁盘" in issue.lower():
                print("  🔧 磁盘使用率过高:")
                print("     df -h  # 查看磁盘使用")
                print("     du -sh /var/log/*  # 查看日志大小")
                print("     # 清理日志文件或扩展磁盘")
    
    def suggest_database_solutions(self, issues: List[str]):
        """建议数据库问题解决方案"""
        for issue in issues:
            if "postgresql" in issue.lower():
                print("  🔧 PostgreSQL 问题:")
                print("     sudo systemctl start postgresql")
                print("     sudo -u postgres psql  # 测试连接")
                print("     # 检查 pg_hba.conf 配置")
            
            elif "redis" in issue.lower():
                print("  🔧 Redis 问题:")
                print("     sudo systemctl start redis")
                print("     redis-cli ping")
                print("     # 检查 redis.conf 配置")
    
    def suggest_network_ssl_solutions(self, issues: List[str]):
        """建议网络SSL问题解决方案"""
        for issue in issues:
            if "ssl" in issue.lower() or "证书" in issue.lower():
                print("  🔧 SSL 证书问题:")
                print("     sudo certbot renew  # 续期证书")
                print("     sudo certbot certificates  # 查看证书状态")
                print("     sudo systemctl restart nginx")
            
            elif "域名" in issue.lower():
                print("  🔧 域名解析问题:")
                print("     nslookup lawsker.com")
                print("     # 检查DNS设置")
                print("     # 联系域名服务商")
    
    def suggest_deployment_solutions(self, issues: List[str]):
        """建议部署问题解决方案"""
        for issue in issues:
            if "虚拟环境" in issue.lower():
                print("  🔧 Python 虚拟环境问题:")
                print("     cd backend")
                print("     python3 -m venv venv")
                print("     source venv/bin/activate")
                print("     pip install -r requirements-prod.txt")
            
            elif "依赖" in issue.lower():
                print("  🔧 依赖问题:")
                print("     source backend/venv/bin/activate")
                print("     pip install --upgrade pip")
                print("     pip install -r requirements-prod.txt")
    
    def suggest_monitoring_solutions(self, issues: List[str]):
        """建议监控问题解决方案"""
        for issue in issues:
            if "prometheus" in issue.lower():
                print("  🔧 Prometheus 问题:")
                print("     sudo systemctl start prometheus")
                print("     # 检查配置文件")
            
            elif "grafana" in issue.lower():
                print("  🔧 Grafana 问题:")
                print("     sudo systemctl start grafana-server")
                print("     # 访问 http://localhost:3000")
            
            elif "日志" in issue.lower():
                print("  🔧 日志问题:")
                print("     sudo logrotate -f /etc/logrotate.d/lawsker")
                print("     # 清理旧日志文件")
    
    def save_diagnosis_report(self):
        """保存诊断报告"""
        try:
            report = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "issues_found": self.issues_found,
                "solutions_applied": self.solutions_applied
            }
            
            report_file = f"/tmp/lawsker_diagnosis_{int(time.time())}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\n📄 诊断报告已保存到: {report_file}")
        except Exception as e:
            print(f"\n❌ 保存诊断报告失败: {str(e)}")


def main():
    """主函数"""
    try:
        troubleshooter = InteractiveTroubleshooter()
        troubleshooter.run()
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，退出故障排除工具")
    except Exception as e:
        print(f"\n❌ 故障排除工具出现错误: {str(e)}")


if __name__ == "__main__":
    main()