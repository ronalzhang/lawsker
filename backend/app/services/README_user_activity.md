# 用户行为追踪系统

## 概述

用户行为追踪系统记录用户在系统中的关键操作行为，用于用户行为分析、审计和业务优化。支持Redis队列批量处理，提高性能。

## 功能特性

### ✅ 已实现功能

1. **全面行为记录**
   - 登录/登出行为
   - 案件相关操作（创建、查看、更新、分配等）
   - 支付相关操作（创建、成功、失败）
   - 文档相关操作（生成、审核、批准、发送）
   - 提现相关操作（申请、批准、拒绝）
   - 配置更新操作

2. **Redis队列批量处理**
   - 使用Redis队列缓存用户活动数据
   - 批量写入数据库，提高性能
   - 支持Redis故障时降级到直接数据库写入

3. **灵活的数据结构**
   - 支持JSON格式的详细信息存储
   - 记录IP地址和用户代理信息
   - 支持目标资源的类型和ID关联

4. **统计分析功能**
   - 用户活动统计
   - 活动类型分布分析
   - 时间段活动趋势

## 活动类型定义

```python
class ActivityType(str, Enum):
    # 认证相关
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    
    # 案件相关
    CASE_CREATE = "case_create"
    CASE_VIEW = "case_view"
    CASE_UPDATE = "case_update"
    CASE_DELETE = "case_delete"
    CASE_ASSIGN = "case_assign"
    CASE_GRAB = "case_grab"
    CASE_COMPLETE = "case_complete"
    
    # 支付相关
    PAYMENT_CREATE = "payment_create"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    
    # 文档相关
    DOCUMENT_GENERATE = "document_generate"
    DOCUMENT_REVIEW = "document_review"
    DOCUMENT_APPROVE = "document_approve"
    DOCUMENT_REJECT = "document_reject"
    DOCUMENT_SEND = "document_send"
    
    # 提现相关
    WITHDRAWAL_REQUEST = "withdrawal_request"
    WITHDRAWAL_APPROVE = "withdrawal_approve"
    WITHDRAWAL_REJECT = "withdrawal_reject"
    
    # 其他
    CONFIG_UPDATE = "config_update"
    PROFILE_UPDATE = "profile_update"
    PASSWORD_CHANGE = "password_change"
```

## 数据库表结构

```sql
CREATE TABLE user_activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    session_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);
```

## Redis队列

- **队列名称**: `user_activities_queue`
- **数据格式**: JSON字符串
- **批量大小**: 30条记录
- **处理间隔**: 20秒

## API监控端点

### 获取用户活动队列状态
```http
GET /api/v1/admin/user-activities/queue-status
Authorization: Bearer <token>
```

### 获取用户活动统计
```http
GET /api/v1/admin/user-activities/statistics?days=7
Authorization: Bearer <token>
```

### 获取特定用户活动详情
```http
GET /api/v1/admin/user-activities/user/{user_id}?days=30
Authorization: Bearer <token>
```

## 使用方法

### 1. 基础使用

```python
from app.services.user_activity_tracker import track_login, track_case_action

# 记录用户登录
await track_login(
    user_id="user-123",
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0..."
)

# 记录案件操作
await track_case_action(
    user_id="user-123",
    action="create",
    case_id="case-456",
    details={"case_amount": 50000.0},
    ip_address="192.168.1.100"
)
```

### 2. 在API端点中集成

```python
from fastapi import Request
from app.services.user_activity_tracker import track_case_action

@router.post("/cases/")
async def create_case(
    request: CaseCreateRequest,
    http_request: Request,
    current_user: Dict = Depends(get_current_user)
):
    # 业务逻辑
    case = await case_service.create_case(...)
    
    # 记录用户行为
    try:
        ip_address = http_request.client.host if http_request.client else "unknown"
        await track_case_action(
            user_id=str(current_user["id"]),
            action="create",
            case_id=str(case.id),
            details={"case_amount": float(request.case_amount)},
            ip_address=ip_address
        )
    except Exception:
        # 记录失败不影响主要业务
        pass
    
    return case
```

### 3. 获取用户活动统计

```python
from app.services.user_activity_tracker import get_user_activity_stats

# 获取用户30天内的活动统计
stats = await get_user_activity_stats("user-123", days=30)
print(f"总活动数: {stats['total_activities']}")
print(f"活动分布: {stats['activity_breakdown']}")
```

## 配置参数

在 `UserActivityTracker` 类中可以配置：

```python
class UserActivityTracker:
    def __init__(self):
        self.batch_size = 30        # 批量处理大小
        self.queue_name = "user_activities_queue"
```

在 `UserActivityProcessor` 类中可以配置：

```python
class UserActivityProcessor:
    def __init__(self):
        self.batch_size = 50            # 批量处理大小
        self.process_interval = 20      # 处理间隔(秒)
```

## 性能优化

1. **批量处理**: 使用Redis队列批量写入数据库
2. **异步处理**: 不阻塞主要业务流程
3. **故障降级**: Redis不可用时直接写数据库
4. **数据压缩**: JSON格式存储详细信息

## 监控指标

- 队列长度
- 处理速度
- 数据库写入成功率
- 今日活动量
- 总活动量
- 活跃用户数

## 数据分析示例

### 用户活跃度分析
```sql
-- 最活跃用户（按活动数量）
SELECT 
    user_id,
    COUNT(*) as activity_count,
    COUNT(DISTINCT action) as action_types
FROM user_activity_logs 
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY user_id
ORDER BY activity_count DESC
LIMIT 10;
```

### 功能使用情况分析
```sql
-- 功能使用频率统计
SELECT 
    action,
    COUNT(*) as usage_count,
    COUNT(DISTINCT user_id) as user_count
FROM user_activity_logs 
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY action
ORDER BY usage_count DESC;
```

### 用户行为路径分析
```sql
-- 用户操作序列分析
SELECT 
    user_id,
    action,
    resource_type,
    created_at,
    LAG(action) OVER (PARTITION BY user_id ORDER BY created_at) as prev_action
FROM user_activity_logs 
WHERE user_id = 'specific-user-id'
ORDER BY created_at;
```

## 测试

运行测试脚本：
```bash
cd backend
python test_user_activity_tracker.py
```

## 故障排除

### Redis连接失败
- 检查Redis服务是否运行
- 验证Redis连接配置
- 查看应用日志中的错误信息

### 数据库写入失败
- 检查数据库连接
- 验证user_activity_logs表是否存在
- 查看数据库日志

### 队列积压
- 检查UserActivityProcessor是否正常运行
- 调整批量处理参数
- 监控数据库性能

## 扩展功能

### 实时告警
可以基于用户行为设置实时告警：

```python
async def check_suspicious_activity(user_id: str):
    """检查可疑活动"""
    # 检查短时间内大量操作
    recent_activities = await get_recent_user_activities(user_id, minutes=5)
    if len(recent_activities) > 50:
        await send_security_alert(f"用户 {user_id} 短时间内操作过于频繁")
```

### 用户画像分析
基于用户行为数据构建用户画像：

```python
async def build_user_profile(user_id: str):
    """构建用户画像"""
    stats = await get_user_activity_stats(user_id, days=90)
    
    profile = {
        "activity_level": "high" if stats["total_activities"] > 100 else "low",
        "primary_functions": get_top_actions(stats["activity_breakdown"]),
        "usage_pattern": analyze_time_pattern(user_id),
        "risk_score": calculate_risk_score(stats)
    }
    
    return profile
```

## 版本历史

- **v1.0**: 基础用户行为记录
- **v1.1**: 添加Redis队列批量处理
- **v1.2**: 增加监控API和统计功能
- **v1.3**: 优化性能和错误处理
- **v1.4**: 添加便捷方法和测试脚本