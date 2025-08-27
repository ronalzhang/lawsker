# Lawsker数据库迁移系统

## 概述

本系统确保**100%成功率，零数据丢失**的数据库迁移，为Lawsker业务优化方案提供安全可靠的数据库升级服务。

## 系统特性

### 🛡️ 安全保障
- **自动备份**: 迁移前自动创建完整数据库备份
- **事务保护**: 所有操作在数据库事务中执行
- **自动回滚**: 失败时自动回滚到迁移前状态
- **数据验证**: 迁移前后进行完整的数据完整性检查

### 🔍 全面验证
- **结构验证**: 检查所有新表、字段、索引、约束的创建
- **数据验证**: 验证初始数据插入和现有数据完整性
- **业务验证**: 测试业务逻辑和数据关系
- **性能验证**: 检查索引效果和查询性能

### 📊 实时监控
- **状态监控**: 实时监控迁移进度和系统状态
- **性能监控**: 跟踪数据库性能指标
- **问题检测**: 自动检测和报告潜在问题
- **历史记录**: 完整的迁移历史和状态记录

### 🔄 灵活回滚
- **选择性回滚**: 只删除新创建的表和字段
- **紧急回滚**: 从备份完全恢复数据库
- **验证回滚**: 确保回滚操作的完整性

## 文件结构

```
backend/
├── migration_manager.py           # 核心迁移管理器
├── migration_verification.py     # 迁移验证工具
├── migration_rollback.py         # 回滚管理工具
├── migration_status_monitor.py   # 状态监控工具
├── execute_safe_migration.py     # 安全迁移执行器
├── run_complete_migration.sh     # 完整迁移脚本
├── migrations/
│   └── 013_business_optimization_tables.sql  # 业务优化迁移脚本
└── README_MIGRATION_SYSTEM.md    # 本文档
```

## 使用方法

### 方法1: 一键执行（推荐）

```bash
# 执行完整的安全迁移流程
./backend/run_complete_migration.sh
```

### 方法2: 分步执行

```bash
# 1. 执行安全迁移
python3 backend/execute_safe_migration.py

# 2. 验证迁移结果
python3 backend/migration_verification.py

# 3. 监控系统状态
python3 backend/migration_status_monitor.py
```

### 方法3: 单独使用各工具

```bash
# 只执行迁移（不推荐，缺少安全保障）
python3 backend/migration_manager.py

# 只验证现有迁移
python3 backend/migration_verification.py

# 回滚迁移
python3 backend/migration_rollback.py

# 监控状态
python3 backend/migration_status_monitor.py
```

## 迁移内容

本次迁移将创建以下数据库结构：

### 新增表（13张）

1. **认证系统表**
   - `lawyer_certification_requests` - 律师认证申请
   - `workspace_mappings` - 工作台映射
   - `demo_accounts` - 演示账户

2. **律师等级系统表**
   - `lawyer_levels` - 律师等级配置
   - `lawyer_level_details` - 律师等级详情
   - `lawyer_point_transactions` - 积分变动记录
   - `lawyer_online_sessions` - 在线时间记录

3. **会员系统表**
   - `user_memberships` - 用户会员
   - `lawyer_memberships` - 律师会员

4. **Credits系统表**
   - `user_credits` - 用户Credits
   - `credit_purchase_records` - Credits购买记录

5. **惩罚系统表**
   - `lawyer_case_declines` - 律师拒绝记录
   - `lawyer_assignment_suspensions` - 暂停派单记录

6. **企业服务表**
   - `enterprise_clients` - 企业客户
   - `enterprise_service_packages` - 企业服务套餐
   - `enterprise_subscriptions` - 企业订阅记录
   - `collection_success_stats` - 催收统计

### 扩展现有表

- **users表**: 添加`workspace_id`、`account_type`、`email_verified`、`registration_source`字段

### 初始数据

- 10级律师等级配置数据
- 演示账户数据
- 企业服务套餐数据
- 为现有用户初始化新系统数据

## 安全机制

### 1. 备份策略
- 使用`pg_dump`创建完整的SQL备份
- 备份文件包含时间戳，便于识别
- 验证备份文件完整性

### 2. 事务管理
- 所有DDL和DML操作在单个事务中执行
- 任何错误都会触发完整回滚
- 事务提交前进行最终验证

### 3. 数据验证
- **迁移前验证**: 记录现有数据状态
- **迁移中验证**: 逐步验证每个操作
- **迁移后验证**: 全面检查数据完整性

### 4. 错误处理
- 详细的错误日志记录
- 自动回滚机制
- 紧急恢复选项

## 验证项目

### 结构验证
- ✅ 所有新表创建成功
- ✅ 所有新字段添加成功
- ✅ 所有索引创建成功
- ✅ 所有约束创建成功
- ✅ 所有触发器创建成功

### 数据验证
- ✅ 初始数据插入成功
- ✅ 现有数据完整性保持
- ✅ 外键关系正确
- ✅ 数据类型正确

### 业务验证
- ✅ 律师等级逻辑正确
- ✅ 演示账户数据结构正确
- ✅ 积分计算逻辑可用
- ✅ Credits系统可用

## 监控指标

### 系统指标
- 数据库连接状态
- 迁移表存在状态
- 数据完整性状态
- 活跃连接数

### 性能指标
- 数据库大小
- 表数量
- 索引数量
- 缓存命中率

## 回滚选项

### 选择性回滚（推荐）
- 只删除新创建的表和字段
- 保留原有数据不变
- 快速安全

### 紧急回滚
- 从备份完全恢复数据库
- 适用于严重问题
- 会丢失迁移后的所有更改

## 故障排除

### 常见问题

1. **连接失败**
   ```bash
   # 检查数据库连接
   psql $DATABASE_URL -c "SELECT 1"
   ```

2. **权限不足**
   ```bash
   # 检查用户权限
   psql $DATABASE_URL -c "SELECT current_user, session_user"
   ```

3. **磁盘空间不足**
   ```bash
   # 检查磁盘空间
   df -h
   ```

4. **备份失败**
   ```bash
   # 手动创建备份
   pg_dump $DATABASE_URL > manual_backup.sql
   ```

### 日志文件

- `migration.log` - 迁移过程日志
- `safe_migration_*.log` - 安全迁移执行日志
- `migration_results.json` - 迁移结果记录
- `migration_verification_report_*.json` - 验证报告
- `migration_monitoring_report_*.json` - 监控报告

### 恢复步骤

1. **检查系统状态**
   ```bash
   python3 backend/migration_status_monitor.py
   ```

2. **运行验证**
   ```bash
   python3 backend/migration_verification.py
   ```

3. **如需回滚**
   ```bash
   python3 backend/migration_rollback.py
   ```

## 最佳实践

### 迁移前
1. 确保数据库有足够的磁盘空间
2. 在非高峰时间执行迁移
3. 通知相关人员迁移计划
4. 准备回滚计划

### 迁移中
1. 不要中断迁移过程
2. 监控系统资源使用
3. 关注错误日志
4. 保持网络连接稳定

### 迁移后
1. 运行完整验证
2. 监控系统性能
3. 测试关键功能
4. 保留备份文件

## 技术支持

如遇到问题，请：

1. 查看相关日志文件
2. 运行状态监控工具
3. 检查系统资源
4. 联系技术支持团队

## 版本信息

- **版本**: 1.0.0
- **创建日期**: 2025-01-25
- **适用于**: Lawsker业务优化方案
- **数据库**: PostgreSQL 12+
- **Python**: 3.8+

---

**重要提醒**: 本系统经过严格测试，但在生产环境使用前，建议先在测试环境验证。