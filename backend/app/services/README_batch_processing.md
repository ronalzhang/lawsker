# 批量数据处理系统

## 概述

批量数据处理系统为Lawsker平台提供高效的大数据量处理能力，包括批量插入、数据清理、分页查询和数据导出等功能。

## 核心组件

### 1. BatchDataProcessor (批量数据处理器)

负责高效的批量数据插入和清理操作。

**主要功能：**
- 批量插入访问日志和用户活动数据
- 自动处理数据冲突和重复
- 分批处理避免内存溢出
- 旧数据清理和归档

**使用示例：**
```python
from app.services.batch_data_processor import batch_data_processor

# 批量插入访问日志
logs = [{"user_id": "123", "ip_address": "192.168.1.1", ...}]
inserted_count = await batch_data_processor.batch_insert_access_logs(logs)

# 清理90天前的访问日志
deleted_count = await batch_data_processor.cleanup_old_access_logs(90)
```

### 2. PaginationService (分页服务)

提供高效的大数据量分页查询功能。

**主要功能：**
- 标准分页查询（适用于一般场景）
- 游标分页查询（适用于实时数据和大数据量）
- 专门的访问日志和用户活动分页接口
- 表统计信息查询

**使用示例：**
```python
from app.services.pagination_service import pagination_service

# 标准分页查询
result = await pagination_service.paginate_access_logs(
    page=1, 
    page_size=20,
    user_id="123"
)

# 游标分页查询（适用于实时数据）
cursor_result = await pagination_service.cursor_paginate_query(
    query="SELECT * FROM access_logs",
    cursor_field="created_at",
    page_size=20
)
```

### 3. DataExportService (数据导出服务)

提供高性能的数据导出功能，支持多种格式。

**主要功能：**
- CSV和Excel格式导出
- 流式处理避免内存溢出
- 自动数据类型处理
- 统计报表生成
- 导出文件管理

**使用示例：**
```python
from app.services.data_export_service import data_export_service

# 导出访问日志到CSV
file_path = await data_export_service.export_access_logs(
    start_date=start_date,
    end_date=end_date,
    format="csv"
)

# 导出统计报表到Excel
report_path = await data_export_service.export_statistics_report(
    start_date=start_date,
    end_date=end_date,
    format="excel"
)
```

### 4. ScheduledTaskManager (定时任务管理器)

管理自动化的数据清理和维护任务。

**主要功能：**
- 自动数据清理（每日凌晨2点）
- 导出文件清理（每日凌晨3点）
- 系统健康检查（每5分钟）
- 手动任务执行

**使用示例：**
```python
from app.services.scheduled_tasks import run_manual_cleanup

# 手动执行清理任务
result = await run_manual_cleanup("access_logs", days_to_keep=90)
```

## API接口

### 批量处理管理接口

**基础路径：** `/api/v1/batch-processing`

#### 1. 获取队列状态
```http
GET /queue-status
```

#### 2. 获取定时任务状态
```http
GET /scheduled-tasks/status
```

#### 3. 手动执行清理任务
```http
POST /cleanup
Content-Type: application/json

{
  "task_type": "access_logs",
  "days_to_keep": 90
}
```

#### 4. 导出数据
```http
POST /export
Content-Type: application/json

{
  "export_type": "access_logs",
  "format": "csv",
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2024-01-31T23:59:59"
}
```

#### 5. 下载导出文件
```http
GET /download?file_path=/path/to/export/file.csv
```

#### 6. 分页查询访问日志
```http
GET /access-logs?page=1&page_size=20&user_id=123
```

#### 7. 分页查询用户活动
```http
GET /user-activities?page=1&page_size=20&action=login
```

#### 8. 获取表统计信息
```http
GET /table-stats/access_logs
```

## 性能优化特性

### 1. 批量插入优化
- 使用PostgreSQL的批量INSERT
- ON CONFLICT处理重复数据
- 分批处理避免内存问题
- 错误恢复机制

### 2. 分页查询优化
- 复合索引支持
- 游标分页避免OFFSET性能问题
- 查询结果缓存
- 自动统计信息更新

### 3. 数据导出优化
- 流式查询避免内存溢出
- 分块处理大数据量
- 自动数据类型转换
- 压缩和打包支持

### 4. 数据清理优化
- 分批删除避免长时间锁表
- 归档功能保留历史数据
- 自动化定时清理
- 清理进度监控

## 配置参数

### BatchDataProcessor配置
```python
batch_size = 500          # 批量处理大小
max_batch_size = 2000     # 最大批量大小
cleanup_batch_size = 1000 # 清理任务批量大小
```

### PaginationService配置
```python
default_page_size = 20    # 默认页面大小
max_page_size = 1000      # 最大页面大小
```

### DataExportService配置
```python
chunk_size = 1000         # 流式处理块大小
max_export_rows = 100000  # 最大导出行数
```

### ScheduledTaskManager配置
```python
# 数据保留策略
access_logs_retention = 90      # 访问日志保留90天
user_activities_retention = 180 # 用户活动保留180天
export_files_retention = 7      # 导出文件保留7天
```

## 监控和告警

### 1. 队列监控
- Redis队列长度监控
- 处理速度监控
- 错误率统计

### 2. 性能监控
- 批量插入性能
- 查询响应时间
- 导出任务耗时

### 3. 存储监控
- 数据库表大小
- 索引使用情况
- 磁盘空间使用

### 4. 告警规则
- 队列积压告警（>10000条）
- 处理失败率告警（>5%）
- 磁盘空间告警（>90%）

## 最佳实践

### 1. 批量插入
- 合理设置批量大小（建议500-2000）
- 使用事务确保数据一致性
- 处理重复数据冲突
- 监控插入性能

### 2. 分页查询
- 优先使用游标分页处理实时数据
- 合理设置页面大小
- 利用索引优化查询
- 缓存频繁查询结果

### 3. 数据导出
- 限制导出数据量
- 使用流式处理
- 定期清理导出文件
- 提供下载进度反馈

### 4. 数据清理
- 制定合理的数据保留策略
- 使用归档而非直接删除重要数据
- 在低峰期执行清理任务
- 监控清理任务执行状态

## 故障排除

### 1. 批量插入失败
- 检查数据格式和约束
- 查看数据库连接状态
- 检查磁盘空间
- 查看错误日志

### 2. 分页查询慢
- 检查索引使用情况
- 优化查询条件
- 考虑使用游标分页
- 检查数据库统计信息

### 3. 导出任务超时
- 减少导出数据量
- 检查系统资源使用
- 优化查询性能
- 增加超时时间

### 4. 清理任务异常
- 检查数据库锁状态
- 查看磁盘空间
- 检查任务调度状态
- 查看清理日志

## 测试

运行测试脚本验证功能：

```bash
cd backend
python test_batch_processing.py
```

测试覆盖：
- 批量插入功能
- 分页查询功能
- 数据导出功能
- 数据清理功能
- 表统计信息
- 手动任务执行

## 更新日志

### v1.0.0 (2024-01-30)
- 实现批量数据处理器
- 添加分页服务
- 实现数据导出服务
- 添加定时任务管理器
- 提供完整的API接口
- 添加性能优化和监控功能