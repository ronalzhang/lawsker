# Lawsker 部署验证指南

## 📋 概述

本指南提供了全面的部署验证流程，确保 Lawsker 系统在部署后正常运行。

## 🔧 验证工具

### 1. 本地验证脚本
```bash
# 验证本地开发环境
./scripts/verify-deployment.sh
```

### 2. 远程服务器检查脚本
```bash
# 复制模板并配置服务器信息
cp scripts/check-server-logs.sh scripts/check-server-logs-local.sh

# 编辑配置
vim scripts/check-server-logs-local.sh
# 修改 SERVER_HOST 和 SERVER_USER

# 运行远程检查
./scripts/check-server-logs-local.sh
```

### 3. 新功能测试脚本
```bash
# 测试新增功能
./scripts/test-new-features.sh
```

## 🔍 验证检查清单

### ✅ 基础系统检查
- [ ] PM2 进程状态正常
- [ ] 关键端口正在监听 (80, 443, 8000, 6060, 3306, 6379)
- [ ] 系统资源使用正常 (CPU < 80%, 内存 < 80%, 磁盘 < 80%)

### ✅ 网络连接检查
- [ ] 前端服务响应正常 (http://localhost:6060)
- [ ] 后端 API 响应正常 (http://localhost:8000/api/v1/health)
- [ ] HTTPS 访问正常 (https://lawsker.com)
- [ ] API 文档可访问 (https://lawsker.com/docs)

### ✅ 数据库连接检查
- [ ] MySQL 数据库连接正常
- [ ] Redis 缓存连接正常
- [ ] 数据库查询响应正常

### ✅ 安全配置检查
- [ ] SSL 证书有效且未过期
- [ ] 防火墙配置正确
- [ ] 安全头配置正确 (CORS, X-Frame-Options 等)

### ✅ 应用功能检查
- [ ] 用户认证系统正常
- [ ] 文档管理功能正常
- [ ] 管理员功能可访问
- [ ] WebSocket 连接正常

### ✅ 新增功能检查
- [ ] 监控和告警系统
- [ ] 自动化运维工具
- [ ] 部署编排器
- [ ] 配置管理系统
- [ ] 故障诊断工具

### ✅ 日志检查
- [ ] 后端错误日志无严重错误
- [ ] 前端错误日志无严重错误
- [ ] Nginx 访问和错误日志正常
- [ ] 系统日志无异常

## 🚨 常见问题排查

### 1. 服务无法启动
```bash
# 检查 PM2 状态
pm2 status

# 查看错误日志
pm2 logs lawsker-backend
pm2 logs lawsker-frontend

# 重启服务
pm2 restart lawsker-backend
pm2 restart lawsker-frontend
```

### 2. 数据库连接失败
```bash
# 检查 MySQL 状态
sudo systemctl status mysql

# 测试连接
mysqladmin ping -h localhost -u root -p

# 检查 Redis 状态
redis-cli ping
```

### 3. SSL 证书问题
```bash
# 检查证书状态
sudo certbot certificates

# 手动续期
sudo certbot renew

# 重启 Nginx
sudo systemctl restart nginx
```

### 4. 端口占用问题
```bash
# 检查端口占用
netstat -tuln | grep -E ':(80|443|8000|6060)'

# 查找占用进程
sudo lsof -i :8000
```

## 📊 性能基准

### 响应时间标准
- API 健康检查: < 100ms
- 用户认证: < 500ms
- 文档上传: < 2s
- 页面加载: < 1s

### 资源使用标准
- CPU 使用率: < 70%
- 内存使用率: < 80%
- 磁盘使用率: < 80%
- 网络延迟: < 50ms

## 🔄 持续监控

### 1. 自动化监控
```bash
# 设置定时任务
crontab -e

# 每5分钟检查一次系统状态
*/5 * * * * /path/to/scripts/verify-deployment.sh > /var/log/lawsker-monitor.log 2>&1
```

### 2. 告警配置
- 服务下线告警
- 资源使用过高告警
- 错误日志异常告警
- SSL 证书即将过期告警

## 📝 验证报告

每次部署后，验证脚本会生成详细报告：

- **本地验证报告**: `/tmp/lawsker_verification_report.txt`
- **服务器状态报告**: `/tmp/lawsker_server_report.txt`
- **功能测试报告**: `/tmp/lawsker_feature_test_report.txt`

## 🔐 安全注意事项

1. **部署脚本安全**
   - 永远不要将包含敏感信息的部署脚本提交到 Git
   - 使用模板文件 (*.template) 供团队参考
   - 个人配置文件 (*-local.sh) 已加入 .gitignore

2. **服务器访问安全**
   - 使用 SSH 密钥认证
   - 定期更换密码和密钥
   - 限制 SSH 访问 IP

3. **数据库安全**
   - 使用强密码
   - 限制数据库访问权限
   - 定期备份数据

## 🎯 部署后验证流程

1. **立即验证** (部署完成后 5 分钟内)
   ```bash
   ./scripts/verify-deployment.sh
   ./scripts/test-new-features.sh
   ```

2. **深度验证** (部署完成后 30 分钟内)
   ```bash
   ./scripts/check-server-logs-local.sh
   ```

3. **持续监控** (部署完成后持续)
   - 监控系统资源使用
   - 检查错误日志
   - 验证关键功能

## 📞 支持联系

如果验证过程中发现问题：

1. 查看相关日志文件
2. 参考故障排查指南
3. 使用交互式故障诊断工具
4. 联系技术支持团队

---

**注意**: 本指南应该在每次重大部署后执行，确保系统稳定性和可靠性。