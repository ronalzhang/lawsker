#!/bin/bash

# Lawsker系统监控和日志设置脚本

echo "开始设置监控和日志系统..."

# 创建监控目录
mkdir -p /root/lawsker/monitoring/{logs,metrics,alerts}

# 创建日志轮转配置
cat > /etc/logrotate.d/lawsker << 'EOF'
/root/lawsker/monitoring/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        systemctl reload nginx
    endscript
}
EOF

# 创建系统监控脚本
cat > /root/lawsker/scripts/system_monitor.py << 'EOF'
#!/usr/bin/env python3
import psutil
import time
import json
import os
from datetime import datetime

def get_system_metrics():
    """获取系统指标"""
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'network_io': psutil.net_io_counters()._asdict(),
        'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
    }
    return metrics

def get_process_metrics():
    """获取进程指标"""
    processes = {}
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            proc_info = proc.info
            if proc_info['name'] in ['node', 'python', 'nginx', 'postgres']:
                processes[proc_info['name']] = {
                    'pid': proc_info['pid'],
                    'cpu_percent': proc_info['cpu_percent'],
                    'memory_percent': proc_info['memory_percent']
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return processes

def main():
    """主函数"""
    metrics_dir = '/root/lawsker/monitoring/metrics'
    os.makedirs(metrics_dir, exist_ok=True)
    
    while True:
        try:
            # 获取系统指标
            system_metrics = get_system_metrics()
            process_metrics = get_process_metrics()
            
            # 合并指标
            all_metrics = {
                'system': system_metrics,
                'processes': process_metrics
            }
            
            # 保存到文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            metrics_file = f"{metrics_dir}/metrics_{timestamp}.json"
            
            with open(metrics_file, 'w') as f:
                json.dump(all_metrics, f, indent=2)
            
            # 保留最近100个文件
            files = sorted([f for f in os.listdir(metrics_dir) if f.startswith('metrics_')])
            if len(files) > 100:
                for old_file in files[:-100]:
                    os.remove(os.path.join(metrics_dir, old_file))
            
            print(f"指标已保存: {metrics_file}")
            
        except Exception as e:
            print(f"监控错误: {e}")
        
        time.sleep(60)  # 每分钟收集一次

if __name__ == '__main__':
    main()
EOF

# 创建日志收集脚本
cat > /root/lawsker/scripts/log_collector.py << 'EOF'
#!/usr/bin/env python3
import os
import time
import json
from datetime import datetime
import subprocess

def collect_pm2_logs():
    """收集PM2日志"""
    try:
        result = subprocess.run(['pm2', 'logs', '--nostream', '--lines', '50'], 
                              capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"PM2日志收集错误: {e}"

def collect_nginx_logs():
    """收集Nginx日志"""
    try:
        with open('/var/log/nginx/access.log', 'r') as f:
            lines = f.readlines()
            return ''.join(lines[-100:])  # 最后100行
    except Exception as e:
        return f"Nginx日志收集错误: {e}"

def collect_system_logs():
    """收集系统日志"""
    try:
        result = subprocess.run(['journalctl', '--no-pager', '-n', '50'], 
                              capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"系统日志收集错误: {e}"

def main():
    """主函数"""
    logs_dir = '/root/lawsker/monitoring/logs'
    os.makedirs(logs_dir, exist_ok=True)
    
    while True:
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 收集各种日志
            logs = {
                'timestamp': datetime.now().isoformat(),
                'pm2_logs': collect_pm2_logs(),
                'nginx_logs': collect_nginx_logs(),
                'system_logs': collect_system_logs()
            }
            
            # 保存日志
            log_file = f"{logs_dir}/system_logs_{timestamp}.json"
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
            
            print(f"日志已保存: {log_file}")
            
        except Exception as e:
            print(f"日志收集错误: {e}")
        
        time.sleep(300)  # 每5分钟收集一次

if __name__ == '__main__':
    main()
EOF

# 创建告警脚本
cat > /root/lawsker/scripts/alert_monitor.py << 'EOF'
#!/usr/bin/env python3
import psutil
import json
import time
from datetime import datetime

def check_system_health():
    """检查系统健康状态"""
    alerts = []
    
    # CPU使用率检查
    cpu_percent = psutil.cpu_percent(interval=1)
    if cpu_percent > 80:
        alerts.append({
            'level': 'warning',
            'message': f'CPU使用率过高: {cpu_percent}%',
            'timestamp': datetime.now().isoformat()
        })
    
    # 内存使用率检查
    memory_percent = psutil.virtual_memory().percent
    if memory_percent > 85:
        alerts.append({
            'level': 'critical',
            'message': f'内存使用率过高: {memory_percent}%',
            'timestamp': datetime.now().isoformat()
        })
    
    # 磁盘使用率检查
    disk_percent = psutil.disk_usage('/').percent
    if disk_percent > 90:
        alerts.append({
            'level': 'critical',
            'message': f'磁盘使用率过高: {disk_percent}%',
            'timestamp': datetime.now().isoformat()
        })
    
    return alerts

def main():
    """主函数"""
    alerts_dir = '/root/lawsker/monitoring/alerts'
    os.makedirs(alerts_dir, exist_ok=True)
    
    while True:
        try:
            alerts = check_system_health()
            
            if alerts:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                alert_file = f"{alerts_dir}/alerts_{timestamp}.json"
                
                with open(alert_file, 'w') as f:
                    json.dump(alerts, f, indent=2)
                
                print(f"发现告警: {len(alerts)}个")
                for alert in alerts:
                    print(f"[{alert['level'].upper()}] {alert['message']}")
            
        except Exception as e:
            print(f"告警监控错误: {e}")
        
        time.sleep(60)  # 每分钟检查一次

if __name__ == '__main__':
    main()
EOF

# 设置脚本权限
chmod +x /root/lawsker/scripts/system_monitor.py
chmod +x /root/lawsker/scripts/log_collector.py
chmod +x /root/lawsker/scripts/alert_monitor.py

# 安装必要的Python包
cd /root/lawsker/backend
source venv/bin/activate
pip install psutil

# 创建PM2配置文件用于监控
cat > /root/lawsker/ecosystem.monitoring.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: 'system-monitor',
      script: '/root/lawsker/scripts/system_monitor.py',
      interpreter: '/root/lawsker/backend/venv/bin/python',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      }
    },
    {
      name: 'log-collector',
      script: '/root/lawsker/scripts/log_collector.py',
      interpreter: '/root/lawsker/backend/venv/bin/python',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      }
    },
    {
      name: 'alert-monitor',
      script: '/root/lawsker/scripts/alert_monitor.py',
      interpreter: '/root/lawsker/backend/venv/bin/python',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      }
    }
  ]
};
EOF

echo "监控和日志系统设置完成！"
echo "使用以下命令启动监控服务："
echo "pm2 start /root/lawsker/ecosystem.monitoring.config.js" 