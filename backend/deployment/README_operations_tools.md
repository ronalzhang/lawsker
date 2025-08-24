# 运维工具集使用指南

本文档介绍Lawsker系统运维工具集的使用方法，包括系统监控、故障诊断和自动化运维功能。

## 工具概述

### 1. 系统监控工具 (SystemMonitor)
- 实时监控系统资源使用情况
- 检查服务状态和健康度
- 收集性能指标和异常检测
- 支持告警规则和通知

### 2. 故障诊断工具 (FaultDiagnosisEngine)
- 自动诊断常见系统问题
- 分析日志文件和错误模式
- 提供修复建议和自动修复
- 维护故障知识库

### 3. 自动化运维工具 (AutomatedOperations)
- 定时执行监控和诊断任务
- 自动恢复故障服务
- 系统维护和清理
- 告警通知和报告生成

## 安装依赖

```bash
# 安装Python依赖
pip install -r requirements-ops.txt

# 或者使用系统包管理器
sudo apt-get install python3-psutil python3-requests python3-schedule
```

## 快速开始

### 使用命令行工具

```bash
# 进入部署目录
cd backend/deployment

# 生成系统监控报告
python ops_cli.py monitor --report

# 执行故障诊断
python ops_cli.py diagnose --report

# 查看运维状态
python ops_cli.py ops --status

# 启动自动化运维守护进程
python ops_cli.py ops --daemon
```

### 直接使用Python模块

```python
from system_monitor import SystemMonitor
from fault_diagnosis import FaultDiagnosisEngine
from automated_operations import AutomatedOperations

# 系统监控
monitor = SystemMonitor()
report = monitor.generate_report()
print(f"系统健康状态: {report['summary']['system_health']}")

# 故障诊断
engine = FaultDiagnosisEngine()
diagnosis = engine.diagnose_system_issues()
for issue in diagnosis:
    print(f"发现问题: {issue.title}")

# 自动化运维
ops = AutomatedOperations()
ops.start_scheduler()  # 启动后台任务调度
```

## 详细使用说明

### 系统监控

#### 生成监控报告
```bash
# 生成完整监控报告
python ops_cli.py monitor --report

# 保存报告到文件
python ops_cli.py monitor --report --output monitoring_report.json

# 使用自定义配置
python ops_cli.py monitor --report --config custom_config.json
```

#### 启动监控守护进程
```bash
# 启动持续监控
python ops_cli.py monitor --daemon

# 后台运行
nohup python ops_cli.py monitor --daemon > monitor.log 2>&1 &
```

#### 监控配置示例
```json
{
  "monitoring_interval": 30,
  "metrics_retention_hours": 24,
  "services": [
    {
      "name": "nginx",
      "process_name": "nginx",
      "port": 80,
      "health_check_url": "http://localhost/health"
    },
    {
      "name": "postgresql",
      "process_name": "postgres",
      "port": 5432
    }
  ],
  "alert_rules": [
    {
      "name": "高CPU使用率",
      "metric": "cpu_percent",
      "threshold": 80.0,
      "operator": ">=",
      "severity": "warning"
    }
  ]
}
```

### 故障诊断

#### 执行系统诊断
```bash
# 完整系统诊断
python ops_cli.py diagnose --report

# 保存诊断报告
python ops_cli.py diagnose --report --output diagnosis_report.json
```

#### 分析日志文件
```bash
# 分析Nginx错误日志
python ops_cli.py diagnose --analyze-logs /var/log/nginx/error.log

# 分析最近12小时的日志
python ops_cli.py diagnose --analyze-logs /var/log/syslog --hours 12
```

#### 自动修复问题
```bash
# 自动修复内存问题
python ops_cli.py diagnose --auto-fix high_memory_usage

# 自动修复服务问题
python ops_cli.py diagnose --auto-fix service_down_nginx
```

#### 诊断配置示例
```json
{
  "log_files": [
    "/var/log/syslog",
    "/var/log/nginx/error.log",
    "/var/log/postgresql/postgresql.log"
  ],
  "analysis_window_hours": 24,
  "auto_fix_enabled": true,
  "notification_webhook": "https://hooks.slack.com/services/..."
}
```

### 自动化运维

#### 查看运维状态
```bash
# 显示当前状态
python ops_cli.py ops --status

# 保存状态到文件
python ops_cli.py ops --status --output ops_status.json
```

#### 执行特定任务
```bash
# 执行系统监控任务
python ops_cli.py ops --task system_monitoring

# 执行故障诊断任务
python ops_cli.py ops --task fault_diagnosis

# 执行日志清理任务
python ops_cli.py ops --task log_cleanup
```

#### 启动自动化运维
```bash
# 启动任务调度器
python ops_cli.py ops --daemon

# 后台运行
nohup python ops_cli.py ops --daemon > ops.log 2>&1 &
```

#### 运维配置示例
```json
{
  "monitoring": {
    "enabled": true,
    "interval_minutes": 5,
    "alert_threshold": {
      "cpu_percent": 80,
      "memory_percent": 85,
      "disk_percent": 90
    }
  },
  "notifications": {
    "email": {
      "enabled": true,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "username": "alerts@lawsker.com",
      "password": "your_password",
      "to_addresses": ["admin@lawsker.com"]
    }
  },
  "auto_recovery": {
    "enabled": true,
    "max_attempts": 3,
    "services": ["nginx", "postgresql", "redis"]
  }
}
```

## 系统集成

### Systemd服务配置

创建系统服务文件 `/etc/systemd/system/lawsker-ops.service`:

```ini
[Unit]
Description=Lawsker Operations Service
After=network.target

[Service]
Type=simple
User=lawsker
WorkingDirectory=/opt/lawsker/backend/deployment
ExecStart=/usr/bin/python3 ops_cli.py ops --daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用和启动服务:
```bash
sudo systemctl enable lawsker-ops
sudo systemctl start lawsker-ops
sudo systemctl status lawsker-ops
```

### Cron任务配置

添加到crontab (`crontab -e`):
```bash
# 每5分钟执行监控检查
*/5 * * * * /opt/lawsker/backend/deployment/ops_cli.py ops --task health_check

# 每6小时执行故障诊断
0 */6 * * * /opt/lawsker/backend/deployment/ops_cli.py ops --task fault_diagnosis

# 每周日凌晨2点清理日志
0 2 * * 0 /opt/lawsker/backend/deployment/ops_cli.py ops --task log_cleanup
```

### Nginx监控配置

在Nginx配置中添加状态页面:
```nginx
server {
    listen 80;
    server_name localhost;
    
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    location /nginx_status {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        deny all;
    }
}
```

## 告警和通知

### 邮件告警配置
```json
{
  "notifications": {
    "email": {
      "enabled": true,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "username": "your_email@gmail.com",
      "password": "your_app_password",
      "from_address": "lawsker-ops@your-domain.com",
      "to_addresses": [
        "admin@your-domain.com",
        "ops@your-domain.com"
      ]
    }
  }
}
```

### Webhook告警配置
```json
{
  "notifications": {
    "webhook": {
      "enabled": true,
      "url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
      "timeout": 10
    }
  }
}
```

### Slack集成示例
```python
import requests

def send_slack_alert(message, webhook_url):
    payload = {
        "text": f"🚨 Lawsker运维告警",
        "attachments": [
            {
                "color": "danger",
                "fields": [
                    {
                        "title": "告警信息",
                        "value": message,
                        "short": False
                    }
                ]
            }
        ]
    }
    requests.post(webhook_url, json=payload)
```

## 故障排除

### 常见问题

1. **权限问题**
   ```bash
   # 确保运行用户有足够权限
   sudo chown -R lawsker:lawsker /opt/lawsker/backend/deployment
   sudo chmod +x /opt/lawsker/backend/deployment/*.py
   ```

2. **依赖缺失**
   ```bash
   # 检查Python模块
   python3 -c "import psutil, requests, schedule"
   
   # 安装缺失的模块
   pip3 install psutil requests schedule
   ```

3. **配置文件错误**
   ```bash
   # 验证JSON配置文件语法
   python3 -m json.tool config.json
   ```

4. **日志文件权限**
   ```bash
   # 确保可以读取日志文件
   sudo chmod 644 /var/log/nginx/error.log
   sudo chmod 644 /var/log/syslog
   ```

### 调试模式

启用详细日志输出:
```bash
# 使用详细模式
python ops_cli.py monitor --report --verbose

# 查看调试信息
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from system_monitor import SystemMonitor
monitor = SystemMonitor()
report = monitor.generate_report()
"
```

### 性能优化

1. **监控间隔调整**
   - 生产环境建议5-10分钟间隔
   - 测试环境可以使用1分钟间隔

2. **日志文件大小限制**
   - 设置合理的日志保留时间
   - 使用日志轮转避免文件过大

3. **数据库优化**
   - 定期清理历史数据
   - 为查询字段添加索引

## 最佳实践

1. **监控策略**
   - 设置合理的告警阈值
   - 避免告警风暴
   - 定期审查告警规则

2. **故障处理**
   - 建立故障响应流程
   - 维护故障知识库
   - 定期演练故障恢复

3. **自动化程度**
   - 从简单任务开始自动化
   - 保留人工干预能力
   - 记录所有自动化操作

4. **安全考虑**
   - 限制工具运行权限
   - 加密敏感配置信息
   - 审计所有运维操作

## 扩展开发

### 添加新的监控指标
```python
def collect_custom_metrics(self):
    """收集自定义指标"""
    # 实现自定义指标收集逻辑
    return {
        "custom_metric": value,
        "another_metric": another_value
    }
```

### 添加新的诊断规则
```python
new_rule = KnowledgeBaseEntry(
    issue_pattern=r"your_pattern",
    title="问题标题",
    category="category",
    severity="warning",
    description="问题描述",
    symptoms=["症状1", "症状2"],
    solutions=["解决方案1", "解决方案2"],
    keywords=["关键词1", "关键词2"]
)
```

### 添加新的自动化任务
```python
def execute_custom_task(self):
    """执行自定义任务"""
    try:
        # 实现任务逻辑
        return True
    except Exception as e:
        logger.error(f"自定义任务失败: {e}")
        return False
```

## 支持和反馈

如有问题或建议，请联系:
- 技术支持: tech-support@lawsker.com
- 运维团队: ops@lawsker.com
- 项目仓库: https://github.com/lawsker/system-ops