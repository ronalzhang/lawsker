# Lawsker 验证脚本使用指南

## 📋 概述

根据你的部署架构（本地开发 + 服务器生产），我们提供了三种不同的验证脚本：

## 🔧 脚本类型

### 1. 本地远程测试脚本 ✅ (推荐在本地使用)
```bash
./scripts/test-production-remote.sh
```

**用途**: 从本地 macOS 测试生产环境 (lawsker.com)
**优点**: 
- 无需服务器访问权限
- 测试用户实际访问体验
- 检查 SSL、DNS、响应时间等

**最新测试结果**: 83.3% 通过率 ✅

### 2. 服务器端验证脚本 (需要在服务器上运行)
```bash
# 在服务器上运行
./scripts/server-verification.sh
```

**用途**: 在 Linux 服务器上检查内部状态
**检查项目**:
- PM2 进程状态
- 数据库连接
- 系统资源使用
- 应用日志
- SSL 证书

### 3. 远程服务器日志检查脚本 (需要配置)
```bash
# 复制并配置
cp scripts/check-server-logs.sh scripts/check-server-logs-local.sh
# 编辑配置服务器信息
vim scripts/check-server-logs-local.sh
# 运行
./scripts/check-server-logs-local.sh
```

## 📊 当前生产环境状态分析

基于最新测试结果 (2025-08-25 02:21:11):

### ✅ 运行正常的功能
- 网站主页访问 (200)
- API 健康检查 (200) 
- SSL 证书有效 (到期: 2025-10-29)
- 用户认证端点 (401 - 正确的未登录响应)
- 安全头配置 (X-Frame-Options, HSTS 等)
- 响应时间优秀 (< 1秒)
- 移动端兼容性良好

### ⚠️ 需要关注的问题
1. **API 文档访问异常** (500 错误)
   - `/docs` 和 `/redoc` 返回 500 错误
   - 可能是 FastAPI 文档生成问题

2. **部分 API 端点不存在** (404 错误)
   - `/api/v1/documents` 
   - `/api/v1/users`
   - 可能是路由配置问题

3. **404 页面处理异常**
   - 不存在的页面返回 500 而不是 404

## 🔧 问题排查建议

### 1. 立即检查服务器日志
```bash
# 在服务器上运行
tail -50 ~/.pm2/logs/lawsker-backend-error.log
```

### 2. 检查 API 路由配置
查看后端路由是否正确注册了这些端点：
- `/api/v1/documents`
- `/api/v1/users`
- `/docs`
- `/redoc`

### 3. 检查 FastAPI 文档配置
确认 FastAPI 应用的文档配置是否正确。

## 📅 建议的监控频率

### 日常监控 (每天)
```bash
./scripts/test-production-remote.sh
```

### 深度检查 (每周)
```bash
# 在服务器上运行
./scripts/server-verification.sh
```

### 紧急情况
如果生产环境出现问题，按以下顺序执行：

1. **快速状态检查**
   ```bash
   ./scripts/test-production-remote.sh
   ```

2. **服务器内部检查** (需要服务器访问)
   ```bash
   ./scripts/server-verification.sh
   ```

3. **详细日志分析** (需要配置)
   ```bash
   ./scripts/check-server-logs-local.sh
   ```

## 🎯 成功标准

### 优秀 (90%+ 通过率)
- 所有核心功能正常
- 响应时间 < 1秒
- 无严重错误

### 良好 (70-90% 通过率) ← **当前状态**
- 核心功能正常
- 部分非关键功能有问题
- 需要关注和修复

### 需要立即处理 (< 70% 通过率)
- 核心功能异常
- 网站无法访问
- 严重性能问题

## 📝 报告文件位置

所有测试都会生成详细报告：
- `/tmp/lawsker_production_test_report.txt` - 生产环境测试报告
- `/tmp/lawsker_server_verification_report.txt` - 服务器验证报告

## 🚨 紧急联系流程

如果发现严重问题：
1. 立即运行验证脚本确认问题
2. 查看生成的报告文件
3. 检查服务器日志
4. 根据问题类型采取相应措施

## 💡 最佳实践

1. **定期监控**: 每天至少运行一次远程测试
2. **问题跟踪**: 记录每次测试的通过率变化
3. **预防性维护**: 定期检查 SSL 证书、磁盘空间等
4. **文档更新**: 发现新问题时更新此指南

---

**注意**: 当前生产环境整体运行良好 (83.3% 通过率)，主要问题集中在 API 文档和部分端点配置上，不影响核心业务功能。