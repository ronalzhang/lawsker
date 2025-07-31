# Prometheus监控系统

## 概述

Prometheus监控系统为Lawsker平台提供全面的监控和告警能力，包括HTTP请求监控、数据库性能监控、系统资源监控和业务指标监控。

## 核心组件

### 1. PrometheusMetrics (指标收集器)

负责定义和收集各种监控指标。

**主要指标类型：**

#### HTTP请求指标
- `http_requests_total`: HTTP请求总数 (Counter)
- `http_request_duration_seconds`: HTTP请求响应时间 (Histogram)
- `http_requests_in_progress`: 正在处理的HTTP请求数 (Gauge)

#### 数据库指标
- `db_connections_active`: 活跃数据库连接数 (Gauge)
- `db_connections_idle`: 空闲数据库连接数 (Gauge)
- `db_connections_total`: 总数据库连接数 (Gauge)
- `db_query_duration_seconds`: 数据库查询响应时间 (Histogram)

#### 业务指标
- `users_total`: 用户总数 (Gauge)
- `cases_total`: 案件总数 (Gauge)
- `cases_created_total`: 创建的案件总数 (Counter)
- `transactions_total`: 交易总数 (Counter)
- `transaction_amount_total`: 交易金额总计 (Counter)
- `lawyer_response_time_seconds`: 律师响应时间 (Histogram)

#### 系统资源指标
- `system_cpu_usage_percent`: CPU使用率 (Gauge)
- `system_memory_usage_bytes`: 内存使用量 (Gauge)
- `system_disk_usage_bytes`: 磁盘使用量 (Gauge)
- `system_network_bytes_total`: 网络流量总计 (Counter)

#### Redis指标
- `redis_queue_length`: Redis队列长度 (Gauge)
- `redis_operations_total`: Redis操作总数 (Counter)

#### WebSocket指标
- `websocket_connections_active`: 活跃WebSocket连接数 (Gauge)
- `websocket_messages_total`: WebSocket消息总数 (Counter)

#### 应用指标
- `app_info`: 应用信息 (Info)
- `app_uptime_seconds`: 应用运行时间 (Gauge)
- `app_status`: 应用状态 (Enum)

### 2. PrometheusMiddleware (HTTP监控中间件)

自动收集HTTP请求指标的中间件。

**功能特性：**
- 自动记录所有HTTP请求的响应时间和状态码
- 路径标准化避免高基数问题
- 排除不需要监控的路径（如/metrics、/health等）
- 异常处理和错误指标记录

**使用示例：**
```python
from app.middlewares.prometheus_middleware import PrometheusMiddleware

app.add_middleware(PrometheusMiddleware)
```

### 3. DatabaseMonitor (数据库监控)

提供数据库查询性能监控功能。

**监控装饰器：**
```python
from app.core.db_monitor import monitor_db_query

@monitor_db_query("select")
async def get_users():
    # 数据库查询代码
    pass
```

**手动监控：**
```python
from app.core.db_monitor import db_monitor

db_monitor.monitor_query_execution("insert", 0.5, True)
```

### 4. MetricsCollector (指标收集服务)

定期收集和更新各种监控指标。

**收集频率：**
- 系统指标：每30秒
- 数据库指标：每30秒
- Redis指标：每30秒
- 业务指标：每5分钟

**使用示例：**
```python
from app.services.metrics_collector import record_business_event

# 记录业务事件
record_business_event("case_created", user_type="client")
record_business_event("transaction", transaction_type="payment", status="success", amount=1000.0)
```

## API接口

### 监控指标接口

**基础路径：** `/api/v1/metrics`

#### 1. 获取Prometheus指标
```http
GET /metrics
Content-Type: text/plain; version=0.0.4; charset=utf-8
```

#### 2. 获取指标收集器状态
```http
GET /status
Authorization: Bearer <admin_token>
```

#### 3. 手动触发业务指标收集
```http
POST /collect/business
Authorization: Bearer <admin_token>
```

#### 4. 手动触发数据库指标收集
```http
POST /collect/database
Authorization: Bearer <admin_token>
```

#### 5. 手动触发系统指标收集
```http
POST /collect/system
Authorization: Bearer <admin_token>
```

#### 6. 获取指标摘要
```http
GET /summary
Authorization: Bearer <admin_token>
```

#### 7. 记录业务事件
```http
POST /record/business-event
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "event_type": "case_created",
  "user_type": "client"
}
```

#### 8. 监控健康检查
```http
GET /health/metrics
```

## 部署配置

### 1. Prometheus服务器配置

**prometheus.yml:**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'lawsker-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/v1/metrics/metrics'
    scrape_interval: 30s
```

### 2. 告警规则配置

**alert_rules.yml:**
```yaml
groups:
  - name: http_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "HTTP错误率过高"
```

### 3. AlertManager配置

**alertmanager.yml:**
```yaml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@lawsker.com'

route:
  group_by: ['alertname', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://localhost:8000/api/v1/alerts/webhook'
```

### 4. Docker Compose部署

```bash
cd backend/monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

**服务端口：**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin123)
- AlertManager: http://localhost:9093

## 告警规则

### 1. HTTP请求告警
- **HighErrorRate**: HTTP 5xx错误率 > 10%
- **HighResponseTime**: 95%响应时间 > 2秒
- **HighRequestRate**: 请求率 > 100 req/s

### 2. 数据库告警
- **DatabaseConnectionHigh**: 活跃连接数 > 80
- **DatabaseSlowQuery**: 95%查询时间 > 1秒
- **DatabaseDown**: 数据库服务不可用

### 3. 系统资源告警
- **HighCPUUsage**: CPU使用率 > 80%
- **HighMemoryUsage**: 内存使用率 > 85%
- **LowDiskSpace**: 磁盘可用空间 < 10%

### 4. 业务告警
- **LowUserActivity**: 案件创建率 < 0.1/hour
- **HighTransactionFailureRate**: 交易失败率 > 5%
- **SlowLawyerResponse**: 律师响应时间 > 1小时

### 5. Redis告警
- **RedisDown**: Redis服务不可用
- **RedisQueueBacklog**: 队列长度 > 10000
- **RedisHighMemoryUsage**: 内存使用率 > 90%

## 监控仪表盘

### Grafana仪表盘

推荐创建以下仪表盘：

#### 1. 系统概览仪表盘
- HTTP请求量和错误率
- 响应时间分布
- 系统资源使用情况
- 应用状态和运行时间

#### 2. 数据库性能仪表盘
- 数据库连接池状态
- 查询响应时间
- 慢查询统计
- 数据库负载

#### 3. 业务指标仪表盘
- 用户注册和活跃度
- 案件创建和处理统计
- 交易量和成功率
- 律师响应时间

#### 4. 基础设施仪表盘
- 服务器资源使用
- 网络流量
- 磁盘I/O
- Redis性能

## 性能优化

### 1. 指标收集优化
- 合理设置收集频率
- 避免高基数标签
- 使用直方图而非摘要
- 定期清理过期指标

### 2. 存储优化
- 设置合适的数据保留期
- 使用远程存储
- 压缩历史数据
- 分片存储

### 3. 查询优化
- 使用记录规则预计算
- 优化PromQL查询
- 缓存频繁查询
- 限制查询范围

## 最佳实践

### 1. 指标命名
- 使用描述性名称
- 遵循Prometheus命名约定
- 避免高基数标签
- 使用一致的标签

### 2. 告警设计
- 设置合理的阈值
- 避免告警风暴
- 使用告警抑制规则
- 分级告警通知

### 3. 仪表盘设计
- 关注关键指标
- 使用合适的图表类型
- 提供上下文信息
- 定期更新和优化

### 4. 运维管理
- 定期备份配置
- 监控监控系统本身
- 建立运维文档
- 培训团队成员

## 故障排除

### 1. 指标收集问题
- 检查指标收集器状态
- 查看应用日志
- 验证网络连接
- 检查权限配置

### 2. 告警问题
- 检查告警规则语法
- 验证AlertManager配置
- 测试通知渠道
- 查看告警历史

### 3. 性能问题
- 检查指标基数
- 优化查询语句
- 调整收集频率
- 增加资源配置

## 测试

运行测试脚本验证功能：

```bash
cd backend
python test_prometheus_metrics.py
```

测试覆盖：
- Prometheus指标收集
- 系统指标收集
- 数据库监控
- 指标收集器
- 指标导出
- API端点

## 更新日志

### v1.0.0 (2024-01-30)
- 实现Prometheus指标收集器
- 添加HTTP监控中间件
- 实现数据库查询监控
- 添加系统资源监控
- 创建指标收集服务
- 提供完整的API接口
- 配置告警规则和通知
- 支持Docker部署