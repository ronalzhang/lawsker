# Lawsker灰度发布指南

本文档详细说明了Lawsker系统的灰度发布流程、监控策略和回滚机制。

## 📋 目录

- [灰度发布概述](#灰度发布概述)
- [发布策略](#发布策略)
- [发布流程](#发布流程)
- [监控和告警](#监控和告警)
- [用户反馈收集](#用户反馈收集)
- [回滚机制](#回滚机制)
- [最佳实践](#最佳实践)

## 🎯 灰度发布概述

灰度发布（Canary Deployment）是一种风险控制的部署策略，通过逐步将新版本推送给部分用户，在确保系统稳定性的前提下完成全量发布。

### 核心优势

- **风险控制**: 限制新版本的影响范围
- **快速反馈**: 及时发现和修复问题
- **平滑过渡**: 避免全量发布的冲击
- **数据驱动**: 基于监控指标做决策

## 🚀 发布策略

### 分阶段发布

我们采用四阶段灰度发布策略：

#### 1. Alpha阶段 (5%用户)
- **目标用户**: 内部测试用户、管理员
- **持续时间**: 24小时
- **主要目标**: 验证基本功能和稳定性

#### 2. Beta阶段 (20%用户)
- **目标用户**: 活跃律师用户
- **持续时间**: 48小时
- **主要目标**: 验证核心业务流程

#### 3. Gamma阶段 (50%用户)
- **目标用户**: 普通用户
- **持续时间**: 72小时
- **主要目标**: 验证系统承载能力

#### 4. Production阶段 (100%用户)
- **目标用户**: 全部用户
- **持续时间**: 持续运行
- **主要目标**: 完成全量发布

### 用户分组策略

```yaml
# 用户分组配置
user_groups:
  internal:
    - user_type: "admin"
    - user_type: "internal_tester"
    
  beta_users:
    - user_type: "lawyer"
    - last_login: ">= 7 days"
    - case_count: ">= 10"
    
  regular_users:
    - user_type: "user"
    - registration_date: ">= 30 days"
```

## 🔄 发布流程

### 1. 准备阶段

```bash
# 检查配置
./scripts/canary-deployment.sh status

# 验证环境
./scripts/system-monitor.sh all
```

### 2. 开始灰度发布

```bash
# 启动灰度发布
./scripts/canary-deployment.sh start v1.1.0

# 开始监控
./scripts/canary-monitor.sh start &
```

### 3. 阶段推进

```bash
# 进入下一阶段
./scripts/canary-deployment.sh next

# 检查状态
./scripts/canary-deployment.sh status
```

### 4. 完成发布

```bash
# 完成全量发布
./scripts/canary-deployment.sh complete

# 生成报告
./scripts/canary-deployment.sh report
```

## 📊 监控和告警

### 关键指标

#### 系统性能指标
- **错误率**: < 5%
- **响应时间P95**: < 3秒
- **可用性**: > 99.5%
- **吞吐量**: 监控请求处理能力

#### 业务指标
- **用户活跃度**: 对比新旧版本
- **功能使用率**: 核心功能使用情况
- **转化率**: 关键业务流程转化

#### 资源指标
- **CPU使用率**: < 80%
- **内存使用率**: < 90%
- **数据库连接数**: < 80
- **Redis内存使用**: < 90%

### 自动回滚条件

系统会在以下情况自动触发回滚：

```yaml
rollback_conditions:
  - metric: "error_rate"
    threshold: 0.1        # 10%
    duration: "5m"
    
  - metric: "response_time_p95"
    threshold: 5000       # 5秒
    duration: "10m"
    
  - metric: "availability"
    threshold: 0.99       # 99%
    duration: "5m"
```

### 告警通知

- **Slack通知**: 实时告警推送
- **邮件通知**: 重要事件通知
- **短信通知**: 紧急情况通知

## 📝 用户反馈收集

### 反馈类型

- **Bug报告**: 功能异常和错误
- **功能建议**: 改进建议
- **用户体验**: 界面和交互反馈
- **性能问题**: 响应速度和稳定性

### 反馈收集方式

#### 1. 主动收集
```javascript
// 前端反馈组件
<FeedbackModal 
  deploymentPhase="beta"
  deploymentVersion="v1.1.0"
  onSubmit={handleFeedbackSubmit}
/>
```

#### 2. 被动收集
- 错误日志自动收集
- 性能指标自动记录
- 用户行为数据分析

### 反馈分析

```bash
# 查看反馈统计
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.lawsker.com/api/v1/canary/feedback/stats?deployment_phase=beta"

# 生成反馈报告
./scripts/canary-deployment.sh feedback
```

## 🔄 回滚机制

### 自动回滚

系统监控脚本会持续监控关键指标，在检测到异常时自动触发回滚：

```bash
# 监控脚本会自动执行
./scripts/canary-deployment.sh rollback
```

### 手动回滚

```bash
# 立即回滚
./scripts/canary-deployment.sh rollback

# 查看回滚状态
./scripts/canary-deployment.sh status
```

### 回滚流程

1. **流量切换**: 将所有流量切回旧版本
2. **服务停止**: 停止新版本服务
3. **数据恢复**: 如需要，恢复数据状态
4. **通知发送**: 通知相关人员
5. **问题分析**: 分析回滚原因

## 📈 最佳实践

### 发布前准备

1. **充分测试**: 在测试环境完整验证
2. **备份数据**: 确保数据安全
3. **准备回滚**: 制定详细回滚计划
4. **团队准备**: 确保关键人员在线

### 发布过程中

1. **密切监控**: 实时关注系统指标
2. **快速响应**: 及时处理用户反馈
3. **记录日志**: 详细记录发布过程
4. **沟通协调**: 保持团队沟通

### 发布后总结

1. **数据分析**: 分析发布效果
2. **经验总结**: 记录经验教训
3. **流程优化**: 持续改进发布流程
4. **文档更新**: 更新相关文档

## 🛠️ 故障排除

### 常见问题

#### 1. 流量分割不生效

```bash
# 检查NGINX配置
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# 重新加载配置
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

#### 2. 监控指标异常

```bash
# 检查Prometheus状态
curl http://localhost:9090/-/healthy

# 查看监控日志
tail -f logs/canary-monitor.log
```

#### 3. 自动回滚失败

```bash
# 手动执行回滚
./scripts/canary-deployment.sh rollback

# 检查服务状态
docker-compose -f docker-compose.prod.yml ps
```

### 紧急处理

如果遇到严重问题：

1. **立即回滚**: 不要犹豫，先保证服务可用
2. **通知团队**: 及时通知相关人员
3. **保留现场**: 保存日志和监控数据
4. **问题分析**: 事后详细分析原因

## 📞 联系支持

如果在灰度发布过程中遇到问题：

- **技术支持**: tech-support@lawsker.com
- **紧急热线**: 400-xxx-xxxx
- **Slack频道**: #deployment-support

---

**重要提醒**:
- 灰度发布是一个持续的过程，需要耐心和细心
- 始终以用户体验为优先考虑
- 数据驱动决策，避免主观判断
- 保持团队沟通，确保信息同步