# Lawsker监控配置指南

## 📋 目录

- [监控架构概述](#监控架构概述)
- [Prometheus配置](#prometheus配置)
- [Grafana仪表盘](#grafana仪表盘)
- [告警规则配置](#告警规则配置)
- [日志监控](#日志监控)
- [应用性能监控](#应用性能监控)
- [基础设施监控](#基础设施监控)
- [监控最佳实践](#监控最佳实践)

## 🏗️ 监控架构概述

### 监控技术栈
```
┌─────────────────────────────────────────────────────────────┐
│                    Lawsker监控架构                          │
├─────────────────────────────────────────────────────────────┤
│  告警层 (Alerting Layer)                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │   邮件告警       │  │   Slack通知     │  │   钉钉告警       ││
│  │  SMTP Server    │  │  Webhook API    │  │  Webhook API    ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
├─────────────────────────────────────────────────────────────┤
│  可视化层 (Visualization Layer)                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Grafana Dashboard (端口: 3000)                        │ │
│  │  - 系统概览仪表盘                                        │ │
│  │  - 应用性能仪表盘                                        │ │
│  │  - 业务指标仪表盘                                        │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  指标收集层 (Metrics Collection Layer)                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │   Prometheus    │  │   Node Exporter │  │   Redis Exporter││
│  │   (端口: 9090)   │  │   (端口: 9100)   │  │   (端口: 9121)  ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │ Postgres Export │  │  Nginx Exporter │  │  Custom Metrics ││
│  │   (端口: 9187)   │  │   (端口: 9113)   │  │   (应用内置)     ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
├─────────────────────────────────────────────────────────────┤
│  日志收集层 (Log Collection Layer)                          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  ELK Stack (Elasticsearch + Logstash + Kibana)         │ │
│  │  - 应用日志收集和分析                                     │ │
│  │  - 访问日志分析                                          │ │
│  │  - 错误日志监控                                          │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  应用层 (Application Layer)                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │   FastAPI       │  │   PostgreSQL    │  │   Redis         ││
│  │   (端口: 8000)   │  │   (端口: 5432)   │  │   (端口: 6379)  ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 监控指标分类
- **系统指标**: CPU、内存、磁盘、网络
- **应用指标**: 请求量、响应时间、错误率
- **业务指标**: 用户注册、案件创建、支付成功率
- **基础设施指标**: 数据库连接、缓存命中率

## 📊 Prometheus配置

### 主配置文件
```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'lawsker-production'
    environment: 'prod'

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  # Prometheus自身监控
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 30s
    metrics_path: /metrics

  # 应用监控
  - job_name: 'lawsker-backend'
    static_configs:
      - targets: ['backend:8000']
    scrape_interval: 15s
    metrics_path: /metrics
    scrape_timeout: 10s

  # 系统监控
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 30s

  # 数据库监控
  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s

  # Redis监控
  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 30s

  # NGINX监控
  - job_name: 'nginx-exporter'
    static_configs:
      - targets: ['nginx-exporter:9113']
    scrape_interval: 30s

  # 自定义业务指标
  - job_name: 'lawsker-business-metrics'
    static_configs:
      - targets: ['backend:8000']
    scrape_interval: 60s
    metrics_path: /business-metrics
```

### 应用指标暴露
```python
# backend/app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CollectorRegistry, CONTENT_TYPE_LATEST
from fastapi import Response
import time

# 创建指标注册表
registry = CollectorRegistry()

# HTTP请求指标
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=registry
)

# 业务指标
user_registrations_total = Counter(
    'user_registrations_total',
    'Total user registrations',
    ['user_type'],
    registry=registry
)

cases_created_total = Counter(
    'cases_created_total',
    'Total cases created',
    ['case_type'],
    registry=registry
)

active_users_gauge = Gauge(
    'active_users_current',
    'Current number of active users',
    registry=registry
)

# 数据库指标
database_connections_active = Gauge(
    'database_connections_active',
    'Active database connections',
    registry=registry
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    registry=registry
)

# 缓存指标
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type'],
    registry=registry
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type'],
    registry=registry
)

class MetricsCollector:
    """指标收集器"""
    
    @staticmethod
    def record_http_request(method: str, endpoint: str, status_code: int, duration: float):
        """记录HTTP请求指标"""
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    @staticmethod
    def record_user_registration(user_type: str):
        """记录用户注册"""
        user_registrations_total.labels(user_type=user_type).inc()
    
    @staticmethod
    def record_case_creation(case_type: str):
        """记录案件创建"""
        cases_created_total.labels(case_type=case_type).inc()
    
    @staticmethod
    def update_active_users(count: int):
        """更新活跃用户数"""
        active_users_gauge.set(count)
    
    @staticmethod
    def record_database_query(query_type: str, duration: float):
        """记录数据库查询"""
        database_query_duration_seconds.labels(query_type=query_type).observe(duration)
    
    @staticmethod
    def update_database_connections(count: int):
        """更新数据库连接数"""
        database_connections_active.set(count)

# 指标端点
async def metrics_endpoint():
    """Prometheus指标端点"""
    return Response(
        generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST
    )
```

### 中间件集成
```python
# backend/app/middlewares/metrics_middleware.py
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.metrics import MetricsCollector

class MetricsMiddleware(BaseHTTPMiddleware):
    """指标收集中间件"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        # 计算请求处理时间
        process_time = time.time() - start_time
        
        # 记录指标
        MetricsCollector.record_http_request(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
            duration=process_time
        )
        
        return response
```

## 📈 Grafana仪表盘

### 系统概览仪表盘
```json
{
  "dashboard": {
    "title": "Lawsker系统概览",
    "tags": ["lawsker", "overview"],
    "panels": [
      {
        "title": "HTTP请求量",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m]))",
            "legendFormat": "RPS"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "reqps"
          }
        }
      },
      {
        "title": "响应时间",
        "type": "stat",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "P95"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "s"
          }
        }
      },
      {
        "title": "错误率",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status_code=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m])) * 100",
            "legendFormat": "Error Rate"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent"
          }
        }
      },
      {
        "title": "活跃用户数",
        "type": "stat",
        "targets": [
          {
            "expr": "active_users_current",
            "legendFormat": "Active Users"
          }
        ]
      }
    ]
  }
}
```

### 应用性能仪表盘
```json
{
  "dashboard": {
    "title": "Lawsker应用性能",
    "panels": [
      {
        "title": "请求量趋势",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (endpoint)",
            "legendFormat": "{{endpoint}}"
          }
        ],
        "yAxes": [
          {
            "label": "Requests/sec",
            "min": 0
          }
        ]
      },
      {
        "title": "响应时间分布",
        "type": "heatmap",
        "targets": [
          {
            "expr": "sum(rate(http_request_duration_seconds_bucket[5m])) by (le)",
            "format": "heatmap",
            "legendFormat": "{{le}}"
          }
        ]
      },
      {
        "title": "数据库连接池",
        "type": "graph",
        "targets": [
          {
            "expr": "database_connections_active",
            "legendFormat": "Active Connections"
          }
        ]
      },
      {
        "title": "缓存命中率",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(cache_hits_total[5m])) / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m]))) * 100",
            "legendFormat": "Hit Rate"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent"
          }
        }
      }
    ]
  }
}
```

### 业务指标仪表盘
```json
{
  "dashboard": {
    "title": "Lawsker业务指标",
    "panels": [
      {
        "title": "用户注册趋势",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(user_registrations_total[1h])) by (user_type)",
            "legendFormat": "{{user_type}}"
          }
        ]
      },
      {
        "title": "案件创建统计",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum(increase(cases_created_total[24h])) by (case_type)",
            "legendFormat": "{{case_type}}"
          }
        ]
      },
      {
        "title": "支付成功率",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(payment_success_total[5m])) / sum(rate(payment_attempts_total[5m])) * 100",
            "legendFormat": "Success Rate"
          }
        ]
      }
    ]
  }
}
```

## 🚨 告警规则配置

### 告警规则文件
```yaml
# monitoring/prometheus/rules/lawsker-alerts.yml
groups:
  - name: lawsker.rules
    rules:
      # 高错误率告警
      - alert: HighErrorRate
        expr: |
          (
            sum(rate(http_requests_total{status_code=~"5.."}[5m])) /
            sum(rate(http_requests_total[5m]))
          ) * 100 > 5
        for: 2m
        labels:
          severity: critical
          service: lawsker-backend
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }}% for the last 5 minutes"

      # 响应时间过长告警
      - alert: HighResponseTime
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
          ) > 2
        for: 5m
        labels:
          severity: warning
          service: lawsker-backend
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"

      # 数据库连接数过高
      - alert: HighDatabaseConnections
        expr: database_connections_active > 80
        for: 3m
        labels:
          severity: warning
          service: postgresql
        annotations:
          summary: "High database connections"
          description: "Database connections: {{ $value }}"

      # 磁盘空间不足
      - alert: DiskSpaceLow
        expr: |
          (
            node_filesystem_avail_bytes{mountpoint="/"} /
            node_filesystem_size_bytes{mountpoint="/"}
          ) * 100 < 10
        for: 5m
        labels:
          severity: critical
          service: system
        annotations:
          summary: "Disk space low"
          description: "Disk space usage is above 90%"

      # 内存使用率过高
      - alert: HighMemoryUsage
        expr: |
          (
            1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)
          ) * 100 > 85
        for: 5m
        labels:
          severity: warning
          service: system
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}%"

      # CPU使用率过高
      - alert: HighCPUUsage
        expr: |
          100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
          service: system
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value }}%"

      # 服务不可用
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
          description: "{{ $labels.job }} service is down"

      # Redis连接失败
      - alert: RedisDown
        expr: redis_up == 0
        for: 1m
        labels:
          severity: critical
          service: redis
        annotations:
          summary: "Redis is down"
          description: "Redis service is not responding"

      # 业务指标告警
      - alert: LowUserRegistration
        expr: |
          sum(rate(user_registrations_total[1h])) < 0.1
        for: 30m
        labels:
          severity: warning
          service: business
        annotations:
          summary: "Low user registration rate"
          description: "User registration rate is {{ $value }} per hour"

      - alert: HighPaymentFailureRate
        expr: |
          (
            sum(rate(payment_failures_total[5m])) /
            sum(rate(payment_attempts_total[5m]))
          ) * 100 > 10
        for: 5m
        labels:
          severity: critical
          service: payment
        annotations:
          summary: "High payment failure rate"
          description: "Payment failure rate is {{ $value }}%"
```

### Alertmanager配置
```yaml
# monitoring/alertmanager/alertmanager.yml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@lawsker.com'
  smtp_auth_username: 'alerts@lawsker.com'
  smtp_auth_password: 'your-app-password'

route:
  group_by: ['alertname', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
    - match:
        severity: warning
      receiver: 'warning-alerts'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://localhost:5001/'

  - name: 'critical-alerts'
    email_configs:
      - to: 'admin@lawsker.com'
        subject: '🚨 Critical Alert: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Labels: {{ .Labels }}
          {{ end }}
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts'
        title: '🚨 Critical Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

  - name: 'warning-alerts'
    email_configs:
      - to: 'devops@lawsker.com'
        subject: '⚠️ Warning Alert: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          {{ end }}

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'service']
```

## 📋 日志监控

### ELK Stack配置

#### Elasticsearch配置
```yaml
# monitoring/elasticsearch/elasticsearch.yml
cluster.name: lawsker-logs
node.name: elasticsearch-1
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
network.host: 0.0.0.0
http.port: 9200
discovery.type: single-node

# 索引设置
index.number_of_shards: 1
index.number_of_replicas: 0

# 内存设置
bootstrap.memory_lock: true
```

#### Logstash配置
```ruby
# monitoring/logstash/logstash.conf
input {
  beats {
    port => 5044
  }
  
  file {
    path => "/var/log/lawsker/application.log"
    start_position => "beginning"
    codec => json
    tags => ["application"]
  }
  
  file {
    path => "/var/log/nginx/access.log"
    start_position => "beginning"
    tags => ["nginx", "access"]
  }
  
  file {
    path => "/var/log/nginx/error.log"
    start_position => "beginning"
    tags => ["nginx", "error"]
  }
}

filter {
  if "application" in [tags] {
    json {
      source => "message"
    }
    
    date {
      match => [ "timestamp", "ISO8601" ]
    }
    
    if [level] == "ERROR" {
      mutate {
        add_tag => ["error"]
      }
    }
  }
  
  if "nginx" in [tags] and "access" in [tags] {
    grok {
      match => { 
        "message" => "%{NGINXACCESS}"
      }
    }
    
    date {
      match => [ "timestamp", "dd/MMM/yyyy:HH:mm:ss Z" ]
    }
    
    mutate {
      convert => { "response" => "integer" }
      convert => { "bytes" => "integer" }
      convert => { "responsetime" => "float" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "lawsker-logs-%{+YYYY.MM.dd}"
  }
  
  if [level] == "ERROR" or [response] >= 500 {
    email {
      to => "devops@lawsker.com"
      subject => "Lawsker Error Alert"
      body => "Error detected: %{message}"
    }
  }
}
```

#### Kibana仪表盘
```json
{
  "version": "7.15.0",
  "objects": [
    {
      "id": "lawsker-logs-dashboard",
      "type": "dashboard",
      "attributes": {
        "title": "Lawsker日志分析",
        "panelsJSON": "[{\"version\":\"7.15.0\",\"panelIndex\":\"1\",\"gridData\":{\"x\":0,\"y\":0,\"w\":24,\"h\":15},\"panelRefName\":\"panel_1\",\"embeddableConfig\":{}}]",
        "optionsJSON": "{\"useMargins\":true,\"syncColors\":false,\"hidePanelTitles\":false}",
        "version": 1,
        "timeRestore": false,
        "kibanaSavedObjectMeta": {
          "searchSourceJSON": "{\"query\":{\"query\":\"\",\"language\":\"kuery\"},\"filter\":[]}"
        }
      }
    }
  ]
}
```

## 🔍 应用性能监控

### APM集成
```python
# backend/app/core/apm.py
from elasticapm.contrib.starlette import make_apm_client, ElasticAPM
from elasticapm import capture_span, capture_message
import elasticapm

# APM客户端配置
apm_config = {
    'SERVICE_NAME': 'lawsker-backend',
    'SECRET_TOKEN': 'your-secret-token',
    'SERVER_URL': 'http://apm-server:8200',
    'ENVIRONMENT': 'production',
    'DEBUG': False,
    'CAPTURE_BODY': 'errors',
    'TRANSACTION_SAMPLE_RATE': 0.1,
    'CENTRAL_CONFIG': True,
}

apm_client = make_apm_client(apm_config)

class APMMonitor:
    """APM监控工具"""
    
    @staticmethod
    def capture_database_query(query_type: str):
        """捕获数据库查询"""
        def decorator(func):
            @capture_span(span_type='db', span_subtype='postgresql')
            def wrapper(*args, **kwargs):
                elasticapm.label(query_type=query_type)
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def capture_external_request(service_name: str):
        """捕获外部请求"""
        def decorator(func):
            @capture_span(span_type='external', span_subtype='http')
            def wrapper(*args, **kwargs):
                elasticapm.label(service=service_name)
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def capture_business_transaction(transaction_name: str):
        """捕获业务事务"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                elasticapm.set_transaction_name(transaction_name)
                return func(*args, **kwargs)
            return wrapper
        return decorator

# 使用示例
@APMMonitor.capture_database_query('user_query')
async def get_user_by_id(user_id: int):
    # 数据库查询逻辑
    pass

@APMMonitor.capture_external_request('payment_service')
async def process_payment(payment_data: dict):
    # 外部支付服务调用
    pass
```

### 自定义性能指标
```python
# backend/app/services/performance_monitor.py
import time
import asyncio
from typing import Dict, List
from datetime import datetime, timedelta
from app.core.metrics import MetricsCollector

class PerformanceMonitor:
    """性能监控服务"""
    
    def __init__(self):
        self.metrics_buffer = []
        self.collection_interval = 60  # 60秒收集一次
    
    async def start_monitoring(self):
        """开始性能监控"""
        while True:
            try:
                await self._collect_system_metrics()
                await self._collect_application_metrics()
                await self._collect_business_metrics()
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                print(f"Performance monitoring error: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_system_metrics(self):
        """收集系统指标"""
        import psutil
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # 磁盘使用率
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        
        # 网络IO
        network = psutil.net_io_counters()
        
        # 更新指标
        # 这里可以发送到Prometheus或其他监控系统
        print(f"System Metrics - CPU: {cpu_percent}%, Memory: {memory_percent}%, Disk: {disk_percent}%")
    
    async def _collect_application_metrics(self):
        """收集应用指标"""
        # 数据库连接池状态
        # db_pool_status = await self.get_db_pool_status()
        
        # 缓存命中率
        # cache_stats = await self.get_cache_stats()
        
        # 活跃用户数
        # active_users = await self.get_active_users_count()
        
        # MetricsCollector.update_active_users(active_users)
        pass
    
    async def _collect_business_metrics(self):
        """收集业务指标"""
        # 今日注册用户数
        # today_registrations = await self.get_today_registrations()
        
        # 今日案件创建数
        # today_cases = await self.get_today_cases()
        
        # 支付成功率
        # payment_success_rate = await self.get_payment_success_rate()
        
        pass
```

## 🖥️ 基础设施监控

### Node Exporter配置
```yaml
# monitoring/node-exporter/docker-compose.yml
version: '3.8'
services:
  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    restart: unless-stopped
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    ports:
      - "9100:9100"
    networks:
      - monitoring
```

### PostgreSQL Exporter配置
```yaml
# monitoring/postgres-exporter/docker-compose.yml
version: '3.8'
services:
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: postgres-exporter
    restart: unless-stopped
    environment:
      DATA_SOURCE_NAME: "postgresql://postgres:password@postgres:5432/lawsker?sslmode=disable"
      PG_EXPORTER_EXTEND_QUERY_PATH: "/etc/postgres_exporter/queries.yaml"
    volumes:
      - ./queries.yaml:/etc/postgres_exporter/queries.yaml:ro
    ports:
      - "9187:9187"
    networks:
      - monitoring
```

### 自定义查询配置
```yaml
# monitoring/postgres-exporter/queries.yaml
pg_database:
  query: "SELECT pg_database.datname, pg_database_size(pg_database.datname) as size FROM pg_database"
  master: true
  metrics:
    - datname:
        usage: "LABEL"
        description: "Name of the database"
    - size:
        usage: "GAUGE"
        description: "Disk space used by the database"

pg_stat_user_tables:
  query: |
    SELECT
      schemaname,
      relname,
      seq_scan,
      seq_tup_read,
      idx_scan,
      idx_tup_fetch,
      n_tup_ins,
      n_tup_upd,
      n_tup_del
    FROM pg_stat_user_tables
  master: true
  metrics:
    - schemaname:
        usage: "LABEL"
        description: "Name of the schema"
    - relname:
        usage: "LABEL"
        description: "Name of the table"
    - seq_scan:
        usage: "COUNTER"
        description: "Number of sequential scans"
    - seq_tup_read:
        usage: "COUNTER"
        description: "Number of live rows fetched by sequential scans"
    - idx_scan:
        usage: "COUNTER"
        description: "Number of index scans"
    - idx_tup_fetch:
        usage: "COUNTER"
        description: "Number of live rows fetched by index scans"
    - n_tup_ins:
        usage: "COUNTER"
        description: "Number of rows inserted"
    - n_tup_upd:
        usage: "COUNTER"
        description: "Number of rows updated"
    - n_tup_del:
        usage: "COUNTER"
        description: "Number of rows deleted"

pg_stat_activity:
  query: |
    SELECT
      datname,
      state,
      COUNT(*) as connections
    FROM pg_stat_activity
    WHERE state IS NOT NULL
    GROUP BY datname, state
  master: true
  metrics:
    - datname:
        usage: "LABEL"
        description: "Database name"
    - state:
        usage: "LABEL"
        description: "Connection state"
    - connections:
        usage: "GAUGE"
        description: "Number of connections in this state"
```

## 🏆 监控最佳实践

### 监控策略
1. **四个黄金信号**
   - 延迟 (Latency): 请求处理时间
   - 流量 (Traffic): 请求量
   - 错误 (Errors): 错误率
   - 饱和度 (Saturation): 资源使用率

2. **监控层次**
   - 基础设施监控: 服务器、网络、存储
   - 应用监控: 应用性能、业务指标
   - 用户体验监控: 前端性能、用户行为

3. **告警策略**
   - 基于症状而非原因告警
   - 设置合理的告警阈值
   - 避免告警疲劳
   - 建立告警升级机制

### 监控部署脚本
```bash
#!/bin/bash
# scripts/deploy-monitoring.sh

echo "部署Lawsker监控系统..."

# 创建监控目录
mkdir -p monitoring/{prometheus,grafana,alertmanager,exporters}

# 部署Prometheus
echo "部署Prometheus..."
docker run -d \
  --name prometheus \
  --restart unless-stopped \
  -p 9090:9090 \
  -v $(pwd)/monitoring/prometheus:/etc/prometheus \
  prom/prometheus:latest \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --web.console.libraries=/etc/prometheus/console_libraries \
  --web.console.templates=/etc/prometheus/consoles \
  --storage.tsdb.retention.time=30d \
  --web.enable-lifecycle

# 部署Grafana
echo "部署Grafana..."
docker run -d \
  --name grafana \
  --restart unless-stopped \
  -p 3000:3000 \
  -v grafana-storage:/var/lib/grafana \
  -e "GF_SECURITY_ADMIN_PASSWORD=admin123" \
  grafana/grafana:latest

# 部署Node Exporter
echo "部署Node Exporter..."
docker run -d \
  --name node-exporter \
  --restart unless-stopped \
  -p 9100:9100 \
  --pid="host" \
  -v "/:/host:ro,rslave" \
  prom/node-exporter:latest \
  --path.rootfs=/host

# 部署Alertmanager
echo "部署Alertmanager..."
docker run -d \
  --name alertmanager \
  --restart unless-stopped \
  -p 9093:9093 \
  -v $(pwd)/monitoring/alertmanager:/etc/alertmanager \
  prom/alertmanager:latest \
  --config.file=/etc/alertmanager/alertmanager.yml \
  --storage.path=/alertmanager

echo "监控系统部署完成！"
echo "Prometheus: http://localhost:9090"
echo "Grafana: http://localhost:3000 (admin/admin123)"
echo "Alertmanager: http://localhost:9093"
```

### 监控维护脚本
```bash
#!/bin/bash
# scripts/monitoring-maintenance.sh

# 清理过期数据
cleanup_old_data() {
    echo "清理过期监控数据..."
    
    # 清理Prometheus数据 (保留30天)
    find /var/lib/prometheus -name "*.db" -mtime +30 -delete
    
    # 清理日志文件 (保留7天)
    find /var/log/monitoring -name "*.log" -mtime +7 -delete
    
    echo "数据清理完成"
}

# 备份监控配置
backup_config() {
    echo "备份监控配置..."
    
    BACKUP_DIR="/backup/monitoring/$(date +%Y%m%d)"
    mkdir -p $BACKUP_DIR
    
    # 备份Prometheus配置
    cp -r monitoring/prometheus $BACKUP_DIR/
    
    # 备份Grafana仪表盘
    cp -r monitoring/grafana $BACKUP_DIR/
    
    # 备份告警规则
    cp -r monitoring/alertmanager $BACKUP_DIR/
    
    echo "配置备份完成: $BACKUP_DIR"
}

# 健康检查
health_check() {
    echo "执行监控系统健康检查..."
    
    # 检查Prometheus
    if curl -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
        echo "✅ Prometheus健康"
    else
        echo "❌ Prometheus异常"
    fi
    
    # 检查Grafana
    if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
        echo "✅ Grafana健康"
    else
        echo "❌ Grafana异常"
    fi
    
    # 检查Alertmanager
    if curl -f http://localhost:9093/-/healthy > /dev/null 2>&1; then
        echo "✅ Alertmanager健康"
    else
        echo "❌ Alertmanager异常"
    fi
}

# 主函数
main() {
    case "$1" in
        "cleanup")
            cleanup_old_data
            ;;
        "backup")
            backup_config
            ;;
        "health")
            health_check
            ;;
        *)
            echo "使用方法: $0 {cleanup|backup|health}"
            exit 1
            ;;
    esac
}

main "$@"
```

---

**文档版本**: v1.0
**最后更新**: 2024-01-30
**维护团队**: DevOps团队

**重要提醒**: 监控系统是保障服务稳定性的重要工具，请定期检查监控配置的有效性，及时调整告警阈值，确保监控系统本身的高可用性。