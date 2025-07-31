# Lawsker系统优化设计文档

## 系统架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Lawsker优化后架构                          │
├─────────────────────────────────────────────────────────────┤
│  前端层 (Frontend Layer)                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │   用户端界面      │  │   管理后台       │  │   移动端界面      ││
│  │  Vue.js 3 +     │  │  Vue.js 3 +     │  │  响应式设计      ││
│  │  TypeScript     │  │  ECharts +      │  │  PWA支持        ││
│  │  Element Plus   │  │  WebSocket      │  │                ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
├─────────────────────────────────────────────────────────────┤
│  网关层 (Gateway Layer)                                      │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  NGINX + SSL + 负载均衡 + 限流 + CSRF保护                │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  应用层 (Application Layer)                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │   业务API服务    │  │   实时推送服务   │  │   数据采集服务   ││
│  │  FastAPI +      │  │  WebSocket +    │  │  访问日志 +     ││
│  │  JWT认证 +      │  │  Redis发布订阅   │  │  行为追踪       ││
│  │  权限控制       │  │                 │  │                ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
├─────────────────────────────────────────────────────────────┤
│  服务层 (Service Layer)                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │   AI服务        │  │   支付服务       │  │   通知服务       ││
│  │  OpenAI +       │  │  微信支付 +     │  │  邮件 + 短信 +  ││
│  │  Deepseek       │  │  支付宝         │  │  WebSocket      ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
├─────────────────────────────────────────────────────────────┤
│  数据层 (Data Layer)                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │   PostgreSQL    │  │   Redis缓存     │  │   文件存储       ││
│  │  主数据库 +     │  │  会话 + 缓存 +  │  │  MinIO +        ││
│  │  读写分离       │  │  消息队列       │  │  CDN加速        ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
├─────────────────────────────────────────────────────────────┤
│  监控层 (Monitoring Layer)                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Prometheus + Grafana + ELK + 告警系统                  │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件设计

### 1. 前端架构设计

#### 1.1 用户端界面重构

**技术栈选择**:
- Vue.js 3 + Composition API
- TypeScript (类型安全)
- Vite (快速构建)
- Element Plus (UI组件库)
- Pinia (状态管理)
- Vue Router 4 (路由管理)

**项目结构**:
```
frontend-user/
├── src/
│   ├── components/          # 通用组件
│   │   ├── common/         # 基础组件
│   │   ├── business/       # 业务组件
│   │   └── layout/         # 布局组件
│   ├── views/              # 页面组件
│   │   ├── auth/          # 认证相关
│   │   ├── workspace/     # 工作台
│   │   ├── tasks/         # 任务管理
│   │   └── profile/       # 个人中心
│   ├── composables/        # 组合式API
│   ├── stores/            # 状态管理
│   ├── router/            # 路由配置
│   ├── api/               # API接口
│   ├── utils/             # 工具函数
│   ├── types/             # TypeScript类型
│   └── assets/            # 静态资源
├── public/                # 公共资源
└── dist/                 # 构建输出
```

#### 1.2 管理后台架构

**特殊需求考虑**:
- 大数据量表格展示
- 实时数据更新
- 复杂图表可视化
- 多维度数据分析

**技术栈增强**:
```typescript
// 管理后台专用依赖
{
  "dependencies": {
    "vue": "^3.3.0",
    "typescript": "^5.0.0",
    "element-plus": "^2.4.0",
    "echarts": "^5.4.0",
    "socket.io-client": "^4.7.0",
    "@tanstack/vue-table": "^8.10.0",
    "vue-leaflet": "^0.10.0",
    "dayjs": "^1.11.0",
    "lodash-es": "^4.17.0",
    "xlsx": "^0.18.0"
  }
}
```

### 2. 后端架构优化

#### 2.1 安全性增强设计

**认证机制升级**:
```python
# 新的认证架构
class SecurityConfig:
    # HttpOnly Cookie配置
    COOKIE_SETTINGS = {
        "httponly": True,
        "secure": True,
        "samesite": "strict",
        "max_age": 86400  # 24小时
    }
    
    # CSRF保护
    CSRF_SECRET_KEY = "your-csrf-secret"
    CSRF_TOKEN_LOCATION = ["cookies", "headers"]
    
    # 限流配置
    RATE_LIMIT_STORAGE_URL = "redis://localhost:6379"
    DEFAULT_RATE_LIMIT = "100/hour"
    
    # JWT配置
    JWT_ALGORITHM = "RS256"  # 使用RSA算法
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
```

**API安全中间件**:
```python
class SecurityMiddleware:
    async def __call__(self, request: Request, call_next):
        # 1. IP白名单检查
        if not self.check_ip_whitelist(request.client.host):
            raise HTTPException(403, "IP not allowed")
        
        # 2. 请求限流
        if not await self.check_rate_limit(request):
            raise HTTPException(429, "Rate limit exceeded")
        
        # 3. CSRF检查
        if request.method in ["POST", "PUT", "DELETE"]:
            if not self.verify_csrf_token(request):
                raise HTTPException(403, "CSRF token invalid")
        
        # 4. 请求日志
        await self.log_request(request)
        
        response = await call_next(request)
        
        # 5. 响应头安全设置
        self.set_security_headers(response)
        
        return response
```

#### 2.2 数据采集系统设计

**访问日志采集器**:
```python
class AccessLogCollector:
    def __init__(self):
        self.redis_client = redis.Redis()
        self.batch_size = 100
        self.batch_timeout = 5  # 秒
        
    async def collect_access_log(self, log_data: dict):
        """收集访问日志"""
        # 1. 数据预处理
        processed_data = await self.preprocess_log(log_data)
        
        # 2. 批量写入Redis队列
        await self.redis_client.lpush("access_logs", json.dumps(processed_data))
        
        # 3. 触发批量处理
        if await self.redis_client.llen("access_logs") >= self.batch_size:
            await self.process_batch()
    
    async def process_batch(self):
        """批量处理日志"""
        logs = []
        for _ in range(self.batch_size):
            log_data = await self.redis_client.rpop("access_logs")
            if log_data:
                logs.append(json.loads(log_data))
        
        if logs:
            await self.batch_insert_to_db(logs)
            await self.update_realtime_stats(logs)
```

**实时数据推送系统**:
```python
class RealtimeDataPusher:
    def __init__(self):
        self.websocket_manager = WebSocketManager()
        self.redis_pubsub = redis.Redis().pubsub()
        
    async def start_listening(self):
        """开始监听数据变化"""
        await self.redis_pubsub.subscribe("stats_update", "alert")
        
        async for message in self.redis_pubsub.listen():
            if message["type"] == "message":
                await self.handle_message(message)
    
    async def handle_message(self, message):
        """处理消息并推送"""
        channel = message["channel"].decode()
        data = json.loads(message["data"])
        
        if channel == "stats_update":
            await self.websocket_manager.broadcast_stats(data)
        elif channel == "alert":
            await self.websocket_manager.send_alert(data)
```

### 3. 数据库优化设计

#### 3.1 查询优化策略

**索引优化**:
```sql
-- 访问日志表索引优化
CREATE INDEX CONCURRENTLY idx_access_logs_user_time 
ON access_logs(user_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_access_logs_ip_time 
ON access_logs(ip_address, created_at DESC);

CREATE INDEX CONCURRENTLY idx_access_logs_path_time 
ON access_logs(path, created_at DESC);

-- 用户表复合索引
CREATE INDEX CONCURRENTLY idx_users_role_status 
ON users(role, status) WHERE status = 'active';

-- 案件表索引优化
CREATE INDEX CONCURRENTLY idx_cases_status_created 
ON cases(status, created_at DESC) WHERE status IN ('pending', 'assigned');
```

**分区表设计**:
```sql
-- 访问日志按月分区
CREATE TABLE access_logs (
    id UUID DEFAULT gen_random_uuid(),
    user_id UUID,
    ip_address INET NOT NULL,
    path VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    -- 其他字段...
) PARTITION BY RANGE (created_at);

-- 创建分区
CREATE TABLE access_logs_2024_01 PARTITION OF access_logs
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE access_logs_2024_02 PARTITION OF access_logs
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

#### 3.2 缓存策略设计

**多层缓存架构**:
```python
class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis()
        self.local_cache = {}  # 进程内缓存
        
    async def get(self, key: str, fetch_func=None):
        """多层缓存获取"""
        # 1. 进程内缓存
        if key in self.local_cache:
            return self.local_cache[key]
        
        # 2. Redis缓存
        cached = await self.redis_client.get(key)
        if cached:
            data = json.loads(cached)
            self.local_cache[key] = data  # 回填本地缓存
            return data
        
        # 3. 数据库查询
        if fetch_func:
            data = await fetch_func()
            await self.set(key, data, expire=300)
            return data
        
        return None
    
    async def set(self, key: str, value: any, expire: int = 300):
        """设置缓存"""
        # 设置Redis缓存
        await self.redis_client.setex(key, expire, json.dumps(value))
        
        # 设置本地缓存
        self.local_cache[key] = value
        
        # 本地缓存清理策略
        if len(self.local_cache) > 1000:
            # 清理最老的50%
            keys_to_remove = list(self.local_cache.keys())[:500]
            for k in keys_to_remove:
                del self.local_cache[k]
```

### 4. 监控和运维设计

#### 4.1 监控指标体系

**系统指标监控**:
```python
from prometheus_client import Counter, Histogram, Gauge

# 定义监控指标
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_USERS = Gauge('active_users_total', 'Number of active users')
DATABASE_CONNECTIONS = Gauge('database_connections_active', 'Active database connections')

class MetricsCollector:
    @staticmethod
    def record_request(method: str, endpoint: str, status: int, duration: float):
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        REQUEST_DURATION.observe(duration)
    
    @staticmethod
    def update_active_users(count: int):
        ACTIVE_USERS.set(count)
    
    @staticmethod
    def update_db_connections(count: int):
        DATABASE_CONNECTIONS.set(count)
```

**业务指标监控**:
```python
# 业务指标定义
CASE_CREATED = Counter('cases_created_total', 'Total cases created', ['user_type'])
LAWYER_RESPONSE_TIME = Histogram('lawyer_response_time_seconds', 'Lawyer response time')
PAYMENT_SUCCESS_RATE = Gauge('payment_success_rate', 'Payment success rate')

class BusinessMetrics:
    @staticmethod
    def record_case_creation(user_type: str):
        CASE_CREATED.labels(user_type=user_type).inc()
    
    @staticmethod
    def record_lawyer_response(response_time: float):
        LAWYER_RESPONSE_TIME.observe(response_time)
    
    @staticmethod
    def update_payment_success_rate(rate: float):
        PAYMENT_SUCCESS_RATE.set(rate)
```

#### 4.2 告警系统设计

**告警规则配置**:
```yaml
# alerting_rules.yml
groups:
  - name: lawsker_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"
      
      - alert: DatabaseConnectionHigh
        expr: database_connections_active > 80
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Database connections high"
          description: "Database connections: {{ $value }}"
      
      - alert: DiskSpaceHigh
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Disk space low"
          description: "Disk space usage is above 90%"
```

## 数据流设计

### 1. 用户访问数据流

```
用户请求 → NGINX → 访问日志中间件 → 业务处理 → 响应
    ↓
访问日志收集器 → Redis队列 → 批量处理 → PostgreSQL
    ↓
实时统计计算 → Redis发布 → WebSocket推送 → 管理后台更新
```

### 2. 实时监控数据流

```
系统指标采集 → Prometheus → 告警规则检查 → 告警通知
    ↓
Grafana仪表盘 ← Prometheus查询 ← 指标存储
    ↓
管理后台 ← WebSocket推送 ← 实时数据处理
```

## 安全设计

### 1. 认证授权流程

```
用户登录 → 验证凭据 → 生成JWT + 设置HttpOnly Cookie
    ↓
请求API → 验证Cookie → 检查权限 → 执行业务逻辑
    ↓
记录审计日志 → 更新用户活动 → 返回响应
```

### 2. 数据保护策略

- **传输加密**: 全站HTTPS，TLS 1.3
- **存储加密**: 敏感字段AES-256加密
- **访问控制**: RBAC权限模型
- **审计日志**: 完整的操作记录
- **数据脱敏**: 日志中敏感信息脱敏

## 性能优化设计

### 1. 前端性能优化

- **代码分割**: 路由级别的懒加载
- **资源优化**: 图片压缩、CDN加速
- **缓存策略**: 浏览器缓存、Service Worker
- **虚拟滚动**: 大数据量表格优化

### 2. 后端性能优化

- **数据库优化**: 索引优化、查询优化、连接池
- **缓存策略**: 多层缓存、缓存预热
- **异步处理**: Celery任务队列
- **负载均衡**: NGINX负载均衡

## 部署架构设计

### 1. 容器化部署

```dockerfile
# 前端Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

### 2. 服务编排

```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/lawsker
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=lawsker
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
  
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  postgres_data:
  redis_data:
  grafana_data:
```

这个设计文档为系统优化提供了完整的技术架构和实现方案，确保优化过程有明确的技术指导和标准。