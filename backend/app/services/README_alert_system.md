# 告警系统实现文档

## 概述

本文档描述了Lawsker系统的基础告警机制实现，包括告警规则配置、通知渠道、状态管理和去重功能。

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │───▶│  AlertManager   │───▶│ Notification    │
│   (监控指标)     │    │   (告警管理)     │    │   Channels      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Redis缓存     │    │   邮件/短信     │
                       │   (状态存储)     │    │   WebSocket     │
                       └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │   (历史记录)     │
                       └─────────────────┘
```

## 核心组件

### 1. AlertManager (告警管理器)

**文件**: `app/services/alert_manager.py`

**主要功能**:
- 告警数据解析和处理
- 重复告警检测和去重
- 告警状态管理（活跃/已解决/静默）
- 通知渠道协调
- 告警历史记录

**关键方法**:
```python
async def process_alert(alert_data: Dict) -> bool
async def silence_alert(alert_id: str, duration_minutes: int) -> bool
async def resolve_alert(alert_id: str) -> bool
async def get_active_alerts() -> List[AlertData]
```

### 2. NotificationChannels (通知渠道)

**文件**: `app/services/notification_channels.py`

**支持的通知方式**:
- **邮件通知**: SMTP邮件发送，支持HTML模板
- **短信通知**: HTTP API短信发送
- **WebSocket通知**: 实时推送到管理后台
- **钉钉通知**: 钉钉群机器人消息
- **Slack通知**: Slack Webhook消息

**通知渠道选择逻辑**:
- `critical`: 所有渠道（邮件+短信+WebSocket）
- `warning`: 邮件+WebSocket
- `info`: 仅WebSocket

### 3. Alert Models (数据模型)

**文件**: `app/models/alert.py`

**数据表**:
- `alerts`: 告警记录表
- `alert_rules`: 告警规则表
- `alert_notifications`: 通知记录表
- `alert_silences`: 静默记录表

### 4. Alert API (API接口)

**文件**: `app/api/v1/endpoints/alerts.py`

**主要端点**:
- `GET /alerts/`: 获取告警列表
- `GET /alerts/active`: 获取活跃告警
- `GET /alerts/stats`: 获取告警统计
- `POST /alerts/webhook`: Prometheus webhook接收
- `POST /alerts/{id}/silence`: 静默告警
- `POST /alerts/{id}/resolve`: 解决告警

## 配置说明

### 1. 告警规则配置

**文件**: `backend/config/alerting_rules.yml`

```yaml
groups:
  - name: lawsker_system_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "系统错误率过高"
          description: "错误率为 {{ $value | humanizePercentage }}"
```

### 2. 环境变量配置

```bash
# 邮件配置
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=alerts@lawsker.com
SMTP_PASSWORD=your_password
ALERT_FROM_EMAIL=alerts@lawsker.com

# 收件人配置
ALERT_EMAIL_CRITICAL=["admin@lawsker.com", "ops@lawsker.com"]
ALERT_EMAIL_WARNING=["admin@lawsker.com"]

# 短信配置
SMS_API_URL=https://sms.example.com/send
SMS_API_KEY=your_sms_api_key
ALERT_SMS_PHONES=["13800138000"]

# Redis配置
REDIS_URL=redis://localhost:6379
```

## 使用方法

### 1. 初始化告警系统

```python
from app.services.alert_manager import alert_manager

# 在应用启动时初始化
await alert_manager.initialize()
```

### 2. 处理Prometheus告警

```python
# Prometheus webhook数据格式
webhook_data = {
    "receiver": "lawsker-alerts",
    "status": "firing",
    "alerts": [
        {
            "alertname": "HighErrorRate",
            "status": "firing",
            "labels": {
                "severity": "critical",
                "service": "lawsker-api"
            },
            "annotations": {
                "summary": "系统错误率过高",
                "description": "错误率超过10%阈值"
            }
        }
    ]
}

# 处理告警
for alert in webhook_data["alerts"]:
    await alert_manager.process_alert(alert)
```

### 3. 手动操作告警

```python
# 静默告警60分钟
await alert_manager.silence_alert("alert_id", 60)

# 手动解决告警
await alert_manager.resolve_alert("alert_id")

# 获取活跃告警
active_alerts = await alert_manager.get_active_alerts()
```

## 告警去重机制

### 去重策略

1. **基于告警ID**: 相同的`alertname`和`instance`组合
2. **时间窗口**: 5分钟内的相同告警被视为重复
3. **状态检查**: 只有状态相同的告警才会被去重

### 去重逻辑

```python
async def _is_duplicate_alert(self, alert: AlertData) -> bool:
    if alert.alert_id in self.active_alerts:
        existing_alert = self.active_alerts[alert.alert_id]
        time_diff = alert.timestamp - existing_alert.timestamp
        
        if (existing_alert.status == alert.status and 
            time_diff < timedelta(minutes=5)):
            return True
    
    return False
```

## 告警状态管理

### 状态类型

- `FIRING`: 告警触发中
- `RESOLVED`: 告警已解决
- `SILENCED`: 告警已静默

### 状态转换

```
FIRING ──┐
         ├──▶ RESOLVED
         └──▶ SILENCED ──▶ FIRING (静默期结束)
```

## 通知模板

### 邮件模板

支持HTML格式，包含以下信息：
- 告警名称和严重级别
- 服务名称和状态
- 详细描述和处理手册链接
- 时间戳和标签信息

### 短信模板

简洁格式，包含关键信息：
```
【Lawsker告警】HighErrorRate
级别: CRITICAL
服务: lawsker-api
消息: 系统错误率过高
时间: 01-15 14:30
```

## 监控指标

### 告警系统自身指标

```python
# 告警处理计数
alert_processed_total = Counter('alerts_processed_total', 'Total processed alerts')

# 通知发送计数
notification_sent_total = Counter('notifications_sent_total', 'Total sent notifications', ['channel'])

# 告警处理延迟
alert_processing_duration = Histogram('alert_processing_duration_seconds', 'Alert processing duration')
```

## 数据库表结构

### alerts表

```sql
CREATE TABLE alerts (
    id UUID PRIMARY KEY,
    alert_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    message TEXT,
    description TEXT,
    service VARCHAR(100),
    labels JSONB,
    annotations JSONB,
    created_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE
);
```

### 索引优化

```sql
CREATE INDEX idx_alerts_alert_id ON alerts(alert_id);
CREATE INDEX idx_alerts_severity_created ON alerts(severity, created_at);
CREATE INDEX idx_alerts_status ON alerts(status);
```

## 性能优化

### 1. 批量处理

- 告警数据批量写入数据库
- 通知批量发送，避免频繁API调用

### 2. 缓存策略

- Redis缓存活跃告警状态
- 本地缓存告警历史记录

### 3. 异步处理

- 所有I/O操作使用异步方式
- 通知发送并发执行

## 故障处理

### 常见问题

1. **通知发送失败**
   - 检查SMTP/SMS配置
   - 查看错误日志
   - 验证网络连接

2. **告警重复发送**
   - 检查去重逻辑
   - 确认Redis连接状态
   - 调整去重时间窗口

3. **数据库连接问题**
   - 检查数据库连接池配置
   - 监控数据库性能
   - 实施连接重试机制

### 日志记录

```python
import logging

logger = logging.getLogger(__name__)

# 告警处理日志
logger.info(f"处理告警: {alert.name} ({alert.severity})")

# 错误日志
logger.error(f"发送通知失败: {e}")

# 调试日志
logger.debug(f"告警去重检查: {alert.alert_id}")
```

## 扩展功能

### 1. 告警升级

当告警在指定时间内未被处理时，自动升级通知级别。

### 2. 告警抑制

根据规则抑制低优先级告警，避免告警风暴。

### 3. 告警分组

将相关告警分组处理，减少通知噪音。

### 4. 自定义通知渠道

支持添加新的通知渠道，如企业微信、飞书等。

## 测试

### 单元测试

```bash
# 运行告警系统测试
python -m pytest backend/test_alert_system.py -v
```

### 集成测试

```bash
# 测试完整告警流程
python backend/test_alert_system.py
```

### 手动测试

```bash
# 发送测试告警
curl -X POST http://localhost:8000/api/v1/alerts/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "alerts": [{
      "alertname": "TestAlert",
      "status": "firing",
      "labels": {"severity": "warning"},
      "annotations": {"summary": "测试告警"}
    }]
  }'
```

## 部署说明

### 1. 数据库迁移

```bash
# 执行告警表创建迁移
psql -d lawsker -f backend/migrations/011_create_alert_tables.sql
```

### 2. 配置Prometheus

```yaml
# prometheus.yml
rule_files:
  - "alerting_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - lawsker-api:8000
```

### 3. 环境变量设置

确保所有必要的环境变量已正确配置，特别是通知渠道相关的配置。

## 总结

基础告警机制已完整实现，包括：

✅ **告警规则配置文件** - 支持Prometheus格式的告警规则
✅ **邮件和短信告警通知** - 多渠道通知支持
✅ **告警状态管理和去重** - 完整的状态管理和重复告警过滤
✅ **告警历史记录功能** - 数据库持久化存储

系统具备企业级告警管理能力，支持高并发、高可用的告警处理需求。