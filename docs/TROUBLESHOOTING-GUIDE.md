# Lawsker故障排除指南

## 📋 目录

- [常见问题](#常见问题)
- [服务器问题](#服务器问题)
- [数据库问题](#数据库问题)
- [前端问题](#前端问题)
- [性能问题](#性能问题)
- [安全问题](#安全问题)
- [监控和日志](#监控和日志)

## 🚨 常见问题

### 1. 服务无法启动

**问题描述**: PM2启动服务失败

**排查步骤**:
```bash
# 检查PM2状态
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "pm2 status"

# 查看错误日志
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "pm2 logs --lines 50 --nostream"

# 检查端口占用
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "netstat -tulpn | grep :8000"
```

**解决方案**:
```bash
# 重启服务
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "pm2 restart lawsker-backend"

# 如果端口被占用，杀死进程
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "kill -9 \$(lsof -ti:8000)"

# 重新启动
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "cd /root/lawsker && source backend_env/bin/activate && pm2 start backend/main.py --name lawsker-backend"
```

### 2. 数据库连接失败

**问题描述**: 应用无法连接到PostgreSQL

**排查步骤**:
```bash
# 检查PostgreSQL状态
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "systemctl status postgresql"

# 检查数据库连接
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "sudo -u postgres psql -c 'SELECT version();'"

# 检查用户权限
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "sudo -u postgres psql -c '\du'"
```

**解决方案**:
```bash
# 重启PostgreSQL
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "systemctl restart postgresql"

# 重新创建用户（如果需要）
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "sudo -u postgres psql -c \"DROP USER IF EXISTS lawsker_user; CREATE USER lawsker_user WITH PASSWORD 'your_password';\""

# 授予权限
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE lawsker TO lawsker_user;\""
```

### 3. 前端页面无法访问

**问题描述**: 浏览器无法访问前端页面

**排查步骤**:
```bash
# 检查NGINX状态
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "systemctl status nginx"

# 检查NGINX配置
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "nginx -t"

# 检查前端服务状态
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "pm2 status | grep frontend"
```

**解决方案**:
```bash
# 重启NGINX
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "systemctl restart nginx"

# 重启前端服务
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "pm2 restart lawsker-frontend"
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "pm2 restart lawsker-admin"
```

## 🖥️ 服务器问题

### 1. 磁盘空间不足

**检查磁盘使用**:
```bash
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "df -h"
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "du -sh /root/lawsker/*"
```

**清理空间**:
```bash
# 清理日志文件
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "find /root/lawsker -name '*.log' -mtime +7 -delete"

# 清理PM2日志
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "pm2 flush"

# 清理系统日志
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "journalctl --vacuum-time=7d"
```

### 2. 内存不足

**检查内存使用**:
```bash
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "free -h"
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "ps aux --sort=-%mem | head -10"
```

**优化内存使用**:
```bash
# 重启占用内存最多的服务
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "pm2 restart all"

# 清理系统缓存
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "sync && echo 3 > /proc/sys/vm/drop_caches"
```

## 🗄️ 数据库问题

### 1. 数据库性能慢

**检查慢查询**:
```bash
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "sudo -u postgres psql lawsker -c \"SELECT query, state, query_start, now() - query_start as duration FROM pg_stat_activity WHERE state != 'idle' ORDER BY duration DESC;\""
```

**优化建议**:
```bash
# 更新统计信息
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "sudo -u postgres psql lawsker -c \"ANALYZE;\""

# 重建索引
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "sudo -u postgres psql lawsker -c \"REINDEX DATABASE lawsker;\""
```

### 2. 数据库连接数过多

**检查连接数**:
```bash
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "sudo -u postgres psql lawsker -c \"SELECT count(*) FROM pg_stat_activity;\""
```

**解决方案**:
```bash
# 终止空闲连接
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "sudo -u postgres psql lawsker -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND now() - state_change > interval '1 hour';\""
```

## 🔧 性能问题

### 1. API响应慢

**检查步骤**:
```bash
# 检查系统负载
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "uptime"

# 检查CPU使用率
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "top -bn1 | grep 'Cpu(s)'"

# 检查网络连接
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "netstat -an | grep :8000 | wc -l"
```

**优化方案**:
```bash
# 重启后端服务
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "pm2 restart lawsker-backend"

# 检查Redis状态
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "redis-cli ping"
```

## 📊 监控和日志

### 1. 查看应用日志

**PM2日志**:
```bash
# 查看所有服务日志
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "pm2 logs --lines 50 --nostream"

# 查看特定服务日志
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "pm2 logs lawsker-backend --lines 50 --nostream"
```

**系统日志**:
```bash
# 查看系统日志
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "journalctl -u nginx --lines 50 --nostream"
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "journalctl -u postgresql --lines 50 --nostream"
```

### 2. 监控系统状态

**实时监控**:
```bash
# 系统资源监控
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "htop"

# 网络连接监控
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "watch -n 1 'netstat -tuln | grep LISTEN'"
```

## 🆘 紧急处理

### 1. 服务完全不可用

**紧急恢复步骤**:
```bash
# 1. 重启所有服务
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "pm2 restart all"
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "systemctl restart nginx"
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "systemctl restart postgresql"
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "systemctl restart redis"

# 2. 检查服务状态
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "pm2 status"
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "systemctl status nginx postgresql redis"

# 3. 测试服务可用性
curl -f http://156.236.74.200/api/health
```

### 2. 数据恢复

**如果需要恢复数据**:
```bash
# 停止应用服务
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "pm2 stop all"

# 恢复数据库备份
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "sudo -u postgres psql lawsker < /path/to/backup.sql"

# 重启服务
sshpass -p 'Pr971V3j' ssh root@156.236.74.200 "pm2 start all"
```

## 📞 联系支持

如果以上方法都无法解决问题，请联系技术支持：

- **技术负责人**: tech-lead@lawsker.com
- **运维工程师**: devops@lawsker.com
- **紧急热线**: 400-xxx-xxxx

提供以下信息：
1. 问题描述和发生时间
2. 错误日志和截图
3. 已尝试的解决方案
4. 系统当前状态