#!/usr/bin/env python3
"""
Grafana监控面板部署脚本
自动化安装、配置和部署Grafana监控系统
"""
import asyncio
import json
import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.grafana_service import grafana_service, setup_grafana_monitoring

def print_banner():
    """打印横幅"""
    print("=" * 60)
    print("📊 LAWSKER GRAFANA监控面板部署")
    print("=" * 60)
    print(f"📅 部署时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

def print_section_header(title: str):
    """打印章节标题"""
    print(f"\n{'='*20} {title} {'='*20}")

def check_prerequisites():
    """检查前置条件"""
    print("🔍 检查前置条件...")
    
    prerequisites = {
        "docker": "docker --version",
        "docker-compose": "docker-compose --version",
    }
    
    missing_tools = []
    
    for tool, command in prerequisites.items():
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

def create_grafana_config():
    """创建Grafana配置文件"""
    print("📝 创建Grafana配置文件...")
    
    config_dir = Path("config/grafana")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Grafana配置文件
    grafana_ini = """
[server]
protocol = http
http_addr = 0.0.0.0
http_port = 3000
domain = localhost
root_url = http://localhost:3000/

[database]
type = sqlite3
path = grafana.db

[session]
provider = file
provider_config = sessions

[analytics]
reporting_enabled = false
check_for_updates = false

[security]
admin_user = admin
admin_password = lawsker_admin_2024
secret_key = lawsker_grafana_secret_key_2024
disable_gravatar = true

[users]
allow_sign_up = false
allow_org_create = false
auto_assign_org = true
auto_assign_org_role = Viewer

[auth.anonymous]
enabled = false

[log]
mode = console
level = info

[paths]
data = /var/lib/grafana
logs = /var/log/grafana
plugins = /var/lib/grafana/plugins
provisioning = /etc/grafana/provisioning

[alerting]
enabled = true
execute_alerts = true

[unified_alerting]
enabled = true

[metrics]
enabled = true
interval_seconds = 10
"""
    
    with open(config_dir / "grafana.ini", "w", encoding="utf-8") as f:
        f.write(grafana_ini)
    
    print(f"  ✅ Grafana配置文件已创建: {config_dir / 'grafana.ini'}")
    
    # 数据源配置
    datasources_dir = config_dir / "provisioning" / "datasources"
    datasources_dir.mkdir(parents=True, exist_ok=True)
    
    datasources_config = """
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
    
  - name: PostgreSQL
    type: postgres
    access: proxy
    url: postgres:5432
    database: lawsker
    user: lawsker_user
    password: ${POSTGRES_PASSWORD}
    sslmode: disable
    editable: true
"""
    
    with open(datasources_dir / "datasources.yml", "w", encoding="utf-8") as f:
        f.write(datasources_config)
    
    print(f"  ✅ 数据源配置已创建: {datasources_dir / 'datasources.yml'}")
    
    # 仪表盘配置
    dashboards_dir = config_dir / "provisioning" / "dashboards"
    dashboards_dir.mkdir(parents=True, exist_ok=True)
    
    dashboards_config = """
apiVersion: 1

providers:
  - name: 'lawsker-dashboards'
    orgId: 1
    folder: 'Lawsker'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards/json
"""
    
    with open(dashboards_dir / "dashboards.yml", "w", encoding="utf-8") as f:
        f.write(dashboards_config)
    
    print(f"  ✅ 仪表盘配置已创建: {dashboards_dir / 'dashboards.yml'}")
    
    return True

def create_docker_compose():
    """创建Docker Compose配置"""
    print("🐳 创建Docker Compose配置...")
    
    docker_compose_content = """
version: '3.8'

services:
  grafana:
    image: grafana/grafana:latest
    container_name: lawsker-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=lawsker_admin_2024
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource,grafana-worldmap-panel
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-lawsker_password}
    volumes:
      - grafana-storage:/var/lib/grafana
      - ./config/grafana/grafana.ini:/etc/grafana/grafana.ini
      - ./config/grafana/provisioning:/etc/grafana/provisioning
      - ./grafana_dashboards:/etc/grafana/provisioning/dashboards/json
    networks:
      - lawsker-monitoring
    depends_on:
      - prometheus
      
  prometheus:
    image: prom/prometheus:latest
    container_name: lawsker-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=15d'
      - '--web.enable-lifecycle'
    volumes:
      - ./config/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-storage:/prometheus
    networks:
      - lawsker-monitoring
      
  node-exporter:
    image: prom/node-exporter:latest
    container_name: lawsker-node-exporter
    restart: unless-stopped
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    networks:
      - lawsker-monitoring

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: lawsker-postgres-exporter
    restart: unless-stopped
    ports:
      - "9187:9187"
    environment:
      - DATA_SOURCE_NAME=postgresql://lawsker_user:${POSTGRES_PASSWORD:-lawsker_password}@postgres:5432/lawsker?sslmode=disable
    networks:
      - lawsker-monitoring
    depends_on:
      - postgres

  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: lawsker-redis-exporter
    restart: unless-stopped
    ports:
      - "9121:9121"
    environment:
      - REDIS_ADDR=redis://redis:6379
    networks:
      - lawsker-monitoring
    depends_on:
      - redis

volumes:
  grafana-storage:
  prometheus-storage:

networks:
  lawsker-monitoring:
    driver: bridge
    external: false
"""
    
    with open("docker-compose.monitoring.yml", "w", encoding="utf-8") as f:
        f.write(docker_compose_content)
    
    print("  ✅ Docker Compose配置已创建: docker-compose.monitoring.yml")
    return True

def create_prometheus_config():
    """创建Prometheus配置"""
    print("📊 创建Prometheus配置...")
    
    config_dir = Path("config/prometheus")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    prometheus_config = """
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'lawsker-api'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']
"""
    
    with open(config_dir / "prometheus.yml", "w", encoding="utf-8") as f:
        f.write(prometheus_config)
    
    print(f"  ✅ Prometheus配置已创建: {config_dir / 'prometheus.yml'}")
    
    # 告警规则
    alert_rules = """
groups:
  - name: lawsker-alerts
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 85
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is above 85% for more than 2 minutes"

      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 90
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is above 90% for more than 2 minutes"

      - alert: DatabaseConnectionsHigh
        expr: pg_stat_database_numbackends{datname="lawsker"} > 80
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "High database connections"
          description: "Database has more than 80 active connections"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100 > 5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "HTTP 5xx error rate is above 5% for more than 2 minutes"
"""
    
    with open(config_dir / "alert_rules.yml", "w", encoding="utf-8") as f:
        f.write(alert_rules)
    
    print(f"  ✅ 告警规则已创建: {config_dir / 'alert_rules.yml'}")
    return True

def deploy_monitoring_stack():
    """部署监控栈"""
    print("🚀 部署监控栈...")
    
    try:
        # 停止现有服务
        print("  🛑 停止现有服务...")
        subprocess.run([
            "docker-compose", "-f", "docker-compose.monitoring.yml", "down"
        ], capture_output=True)
        
        # 启动服务
        print("  🚀 启动监控服务...")
        result = subprocess.run([
            "docker-compose", "-f", "docker-compose.monitoring.yml", "up", "-d"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"  ❌ 服务启动失败: {result.stderr}")
            return False
        
        print("  ✅ 监控服务启动成功")
        
        # 等待服务启动
        print("  ⏳ 等待服务启动...")
        time.sleep(30)
        
        # 检查服务状态
        print("  🔍 检查服务状态...")
        status_result = subprocess.run([
            "docker-compose", "-f", "docker-compose.monitoring.yml", "ps"
        ], capture_output=True, text=True)
        
        print("  📊 服务状态:")
        print(status_result.stdout)
        
        return True
        
    except Exception as e:
        print(f"  ❌ 部署失败: {str(e)}")
        return False

async def configure_grafana_dashboards():
    """配置Grafana仪表盘"""
    print("📊 配置Grafana仪表盘...")
    
    try:
        # 等待Grafana启动
        print("  ⏳ 等待Grafana启动...")
        max_retries = 30
        for i in range(max_retries):
            try:
                status = await grafana_service.get_grafana_status()
                if status.get("connected"):
                    print("  ✅ Grafana已启动")
                    break
            except:
                pass
            
            if i == max_retries - 1:
                print("  ❌ Grafana启动超时")
                return False
            
            time.sleep(10)
        
        # 设置监控
        print("  📊 设置监控仪表盘...")
        setup_result = await setup_grafana_monitoring()
        
        if setup_result.get("status") == "success":
            print("  ✅ 监控仪表盘设置成功")
            
            # 显示结果摘要
            datasources = setup_result.get("datasources", [])
            dashboards = setup_result.get("dashboards", [])
            alerts = setup_result.get("alerts", [])
            
            print(f"    📊 数据源: {len([d for d in datasources if d['status'] in ['created', 'exists']])} 个")
            print(f"    📈 仪表盘: {len([d for d in dashboards if d['status'] in ['created', 'exists']])} 个")
            print(f"    🚨 告警规则: {len([a for a in alerts if a['status'] == 'configured'])} 个")
            
            return True
        else:
            print(f"  ❌ 监控设置失败: {setup_result.get('errors', [])}")
            return False
            
    except Exception as e:
        print(f"  ❌ 配置失败: {str(e)}")
        return False

def create_dashboard_json_files():
    """创建仪表盘JSON文件"""
    print("📄 创建仪表盘JSON文件...")
    
    dashboards_dir = Path("grafana_dashboards")
    dashboards_dir.mkdir(exist_ok=True)
    
    # 这里可以添加预定义的仪表盘JSON文件
    # 由于篇幅限制，这里只创建一个示例
    
    sample_dashboard = {
        "dashboard": {
            "id": None,
            "title": "Lawsker System Overview",
            "tags": ["lawsker"],
            "timezone": "browser",
            "panels": [],
            "time": {
                "from": "now-6h",
                "to": "now"
            },
            "timepicker": {},
            "templating": {
                "list": []
            },
            "annotations": {
                "list": []
            },
            "refresh": "30s",
            "schemaVersion": 16,
            "version": 0
        }
    }
    
    with open(dashboards_dir / "system_overview.json", "w", encoding="utf-8") as f:
        json.dump(sample_dashboard, f, indent=2)
    
    print(f"  ✅ 示例仪表盘已创建: {dashboards_dir / 'system_overview.json'}")
    return True

def print_deployment_summary():
    """打印部署摘要"""
    print("\n" + "="*60)
    print("📋 部署摘要")
    print("="*60)
    print("🎉 Grafana监控系统部署完成！")
    print("\n📊 访问地址:")
    print("  🌐 Grafana: http://localhost:3000")
    print("    用户名: admin")
    print("    密码: lawsker_admin_2024")
    print("  📊 Prometheus: http://localhost:9090")
    print("  📈 Node Exporter: http://localhost:9100")
    print("\n📋 后续步骤:")
    print("  1. 访问Grafana并检查仪表盘")
    print("  2. 配置告警通知渠道")
    print("  3. 根据需要调整监控指标")
    print("  4. 设置数据备份策略")
    print("  5. 配置SSL证书（生产环境）")

def show_help():
    """显示帮助信息"""
    print("Grafana监控面板部署工具")
    print("\n用法:")
    print("  python deploy_grafana.py [选项]")
    print("\n选项:")
    print("  --deploy, -d    完整部署监控系统")
    print("  --config, -c    仅创建配置文件")
    print("  --status, -s    检查部署状态")
    print("  --help, -h      显示此帮助信息")

async def check_deployment_status():
    """检查部署状态"""
    print("🔍 检查部署状态...")
    
    try:
        # 检查Docker服务
        print("\n📊 Docker服务状态:")
        result = subprocess.run([
            "docker-compose", "-f", "docker-compose.monitoring.yml", "ps"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("  ❌ 无法获取Docker服务状态")
        
        # 检查Grafana状态
        print("\n📊 Grafana状态:")
        grafana_status = await grafana_service.get_grafana_status()
        
        if grafana_status.get("connected"):
            print("  ✅ Grafana连接正常")
            print(f"  📊 仪表盘数量: {grafana_status.get('dashboards_count', 0)}")
            print(f"  📈 数据源数量: {grafana_status.get('datasources_count', 0)}")
        else:
            print(f"  ❌ Grafana连接失败: {grafana_status.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 状态检查失败: {str(e)}")
        return False

async def main():
    """主函数"""
    print_banner()
    
    # 解析命令行参数
    args = sys.argv[1:]
    
    if not args or "--help" in args or "-h" in args:
        show_help()
        return
    
    try:
        if "--deploy" in args or "-d" in args:
            # 完整部署
            success = True
            
            # 检查前置条件
            if not check_prerequisites():
                success = False
            
            # 创建配置文件
            if success:
                print_section_header("创建配置文件")
                success = (
                    create_grafana_config() and
                    create_prometheus_config() and
                    create_docker_compose() and
                    create_dashboard_json_files()
                )
            
            # 部署监控栈
            if success:
                print_section_header("部署监控栈")
                success = deploy_monitoring_stack()
            
            # 配置Grafana
            if success:
                print_section_header("配置Grafana")
                success = await configure_grafana_dashboards()
            
            if success:
                print_deployment_summary()
                print("\n✅ Grafana监控系统部署成功")
            else:
                print("\n❌ Grafana监控系统部署失败")
            
        elif "--config" in args or "-c" in args:
            # 仅创建配置文件
            print_section_header("创建配置文件")
            success = (
                create_grafana_config() and
                create_prometheus_config() and
                create_docker_compose() and
                create_dashboard_json_files()
            )
            
            if success:
                print("\n✅ 配置文件创建完成")
            else:
                print("\n❌ 配置文件创建失败")
                
        elif "--status" in args or "-s" in args:
            # 检查状态
            success = await check_deployment_status()
            
        else:
            print("❌ 未知选项，使用 --help 查看帮助")
            success = False
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生未预期的错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())