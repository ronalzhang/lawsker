# 访问日志中间件

## 概述

访问日志中间件自动记录所有HTTP请求的详细信息，用于系统访问分析和监控。支持Redis队列批量处理，提高性能。

## 功能特性

### ✅ 已实现功能

1. **自动访问记录**
   - 记录所有HTTP请求的详细信息
   - 包含IP地址、用户代理、响应时间等
   - 自动解析设备类型、浏览器、操作系统

2. **Redis队列批量处理**
   - 使用Redis队列缓存访问日志
   - 批量写入数据库，提高性能
   - 支持Redis故障时降级到直接数据库写入

3. **地理位置识别**
   - 基础的IP地址地理位置识别
   - 支持内网IP识别
   - 可扩展集成第三方IP地址库

4. **用户身份识别**
   - 从JWT token提取用户ID
   - 生成会话ID用于用户行为分析
   - 支持匿名用户访问记录

5. **智能过滤**
   - 自动过滤静态资源请求
   - 排除健康检查和文档页面
   - 可配置的过滤规则

## 数据库表结构

```sql
CREATE TABLE access_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(64),
    ip_address INET NOT NULL,
    user_agent TEXT,
    referer TEXT,
    request_path VARCHAR(500) NOT NULL,
    request_method VARCHAR(10) DEFAULT 'GET',
    status_code INTEGER DEFAULT 200,
    response_time INTEGER, -- 响应时间(毫秒)
    device_type VARCHAR(20), -- mobile/desktop/tablet
    browser VARCHAR(50),
    os VARCHAR(50),
    country VARCHAR(50),
    region VARCHAR(50),
    city VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Redis队列

- **队列名称**: `access_logs_queue`
- **数据格式**: JSON字符串
- **批量大小**: 50条记录
- **处理间隔**: 30秒

## API监控端点

### 获取队列状态
```http
GET /api/v1/admin/access-logs/queue-status
Authorization: Bearer <token>
```

### 获取访问统计
```http
GET /api/v1/admin/access-logs/statistics?days=7
Authorization: Bearer <token>
```

## 配置参数

在 `AccessLoggerMiddleware` 类中可以配置：

```python
class AccessLoggerMiddleware:
    def __init__(self, app):
        self.app = app
        self.batch_size = 50        # 批量处理大小
        self.batch_timeout = 5      # 批量处理超时时间(秒)
```

在 `AccessLogProcessor` 类中可以配置：

```python
class AccessLogProcessor:
    def __init__(self):
        self.batch_size = 100           # 批量处理大小
        self.process_interval = 30      # 处理间隔(秒)
```

## 性能优化

1. **批量处理**: 使用Redis队列批量写入数据库
2. **异步处理**: 不阻塞HTTP请求处理
3. **智能过滤**: 排除不必要的请求记录
4. **故障降级**: Redis不可用时直接写数据库

## 监控指标

- 队列长度
- 处理速度
- 数据库写入成功率
- 今日访问量
- 总访问量

## 使用示例

### 启动服务
中间件会在FastAPI应用启动时自动注册和启动。

### 查看日志
```python
# 查看最近的访问日志
SELECT * FROM access_logs ORDER BY created_at DESC LIMIT 10;

# 统计今日访问量
SELECT COUNT(*) FROM access_logs WHERE DATE(created_at) = CURRENT_DATE;

# 统计设备类型分布
SELECT device_type, COUNT(*) FROM access_logs GROUP BY device_type;
```

### 监控队列
```python
import redis.asyncio as redis

redis_client = redis.from_url("redis://localhost:6379")
queue_length = await redis_client.llen("access_logs_queue")
print(f"队列长度: {queue_length}")
```

## 测试

运行测试脚本：
```bash
cd backend
python test_access_logger.py
```

## 故障排除

### Redis连接失败
- 检查Redis服务是否运行
- 验证Redis连接配置
- 查看应用日志中的错误信息

### 数据库写入失败
- 检查数据库连接
- 验证access_logs表是否存在
- 查看数据库日志

### 队列积压
- 检查AccessLogProcessor是否正常运行
- 调整批量处理参数
- 监控数据库性能

## 扩展功能

### 集成IP地址库
可以集成MaxMind GeoIP等第三方服务：

```python
def _get_location_info(self, ip_address: str) -> tuple:
    # 集成MaxMind GeoIP
    import geoip2.database
    
    try:
        with geoip2.database.Reader('GeoLite2-City.mmdb') as reader:
            response = reader.city(ip_address)
            return (
                response.country.name,
                response.subdivisions.most_specific.name,
                response.city.name
            )
    except:
        return ("未知", "未知", "未知")
```

### 用户行为分析
基于访问日志数据进行用户行为分析：

```python
# 用户访问路径分析
SELECT 
    user_id,
    request_path,
    created_at,
    LAG(request_path) OVER (PARTITION BY user_id ORDER BY created_at) as prev_path
FROM access_logs 
WHERE user_id IS NOT NULL
ORDER BY user_id, created_at;
```

## 版本历史

- **v1.0**: 基础访问日志记录
- **v1.1**: 添加Redis队列批量处理
- **v1.2**: 增加监控API和统计功能
- **v1.3**: 优化性能和错误处理