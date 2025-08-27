# Lawsker运维手册

## 📞 紧急联系方式

### 主要联系人
- **技术负责人**: tech-lead@lawsker.com / 138-xxxx-xxxx
- **运维工程师**: devops@lawsker.com / 139-xxxx-xxxx  
- **产品负责人**: product@lawsker.com / 137-xxxx-xxxx
- **安全专员**: security@lawsker.com / 136-xxxx-xxxx

### 值班安排
- **主值班**: 7x24小时轮班制
- **备值班**: 技术负责人和运维工程师
- **升级路径**: 运维工程师 → 技术负责人 → CTO

## 🚨 故障响应流程

### 响应时间要求
- **P0 (系统完全不可用)**: 5分钟内响应，30分钟内恢复
- **P1 (核心功能异常)**: 15分钟内响应，2小时内恢复  
- **P2 (部分功能异常)**: 30分钟内响应，4小时内恢复
- **P3 (性能问题)**: 1小时内响应，24小时内恢复

### 故障处理步骤

#### 1. 故障发现和确认
```bash
# 检查系统整体状态
./scripts/system-monitor.sh all

# 检查服务状态
docker-compose -f docker-compose.prod.yml ps

# 检查关键服务健康状态
curl -f http://localhost/health
```

#### 2. 初步诊断
```bash
# 查看系统资源使用
top
free -h
df -h

# 查看服务日志
docker-compose -f docker-compose.prod.yml logs -f --tail=100

# 查看错误日志
tail -f backend/logs/error.log
tail -f nginx/logs/error.log
```

#### 3. 问题定位
```bash
# 检查数据库状态
docker-compose -f docker-compose.prod.yml exec postgres pg_isready
docker-compose -f docker-compose.prod.yml exec postgres psql -U lawsker_user -c "SELECT count(*) FROM pg_stat_activity;"

# 检查Redis状态
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
docker-compose -f docker-compose.prod.yml exec redis redis-cli info memory

# 检查网络连接
netstat -tuln | grep LISTEN
```

#### 4. 故障恢复
```bash
# 重启单个服务
docker-compose -f docker-compose.prod.yml restart <service_name>

# 重启所有服务
docker-compose -f docker-compose.prod.yml restart

# 如果需要回滚
./scripts/deploy-production.sh rollback <backup_dir>
```

## 🔧 常见问题处理

### 1. 服务不可用

**症状**: 用户无法访问网站，API返回5xx错误

**诊断步骤**:
```bash
# 1. 检查NGINX状态
docker-compose -f docker-compose.prod.yml ps nginx
curl -I http://localhost

# 2. 检查后端服务
docker-compose -f docker-compose.prod.yml ps backend
curl -f http://localhost:8000/health

# 3. 查看服务日志
docker-compose -f docker-compose.prod.yml logs nginx
docker-compose -f docker-compose.prod.yml logs backend
```

**解决方案**:
```bash
# 重启NGINX
docker-compose -f docker-compose.prod.yml restart nginx

# 重启后端服务
docker-compose -f docker-compose.prod.yml restart backend

# 如果问题持续，检查配置文件
docker-compose -f docker-compose.prod.yml exec nginx nginx -t
```

### 2. 数据库连接问题

**症状**: 应用报告数据库连接错误，查询超时

**诊断步骤**:
```bash
# 1. 检查数据库状态
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U lawsker_user

# 2. 检查连接数
docker-compose -f docker-compose.prod.yml exec postgres psql -U lawsker_user -d lawsker_prod -c "
SELECT count(*) as total_connections,
       count(*) FILTER (WHERE state = 'active') as active_connections,
       count(*) FILTER (WHERE state = 'idle') as idle_connections
FROM pg_stat_activity;"

# 3. 检查慢查询
docker-compose -f docker-compose.prod.yml exec postgres psql -U lawsker_user -d lawsker_prod -c "
SELECT query, state, query_start, now() - query_start as duration
FROM pg_stat_activity 
WHERE state != 'idle' AND query != '<IDLE>'
ORDER BY duration DESC LIMIT 10;"
```

**解决方案**:
```bash
# 终止长时间运行的查询
docker-compose -f docker-compose.prod.yml exec postgres psql -U lawsker_user -d lawsker_prod -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'active' AND now() - query_start > interval '5 minutes';"

# 重启数据库（谨慎操作）
docker-compose -f docker-compose.prod.yml restart postgres

# 检查数据库配置
docker-compose -f docker-compose.prod.yml exec postgres psql -U lawsker_user -d lawsker_prod -c "SHOW all;"
```

### 3. 内存不足

**症状**: 系统响应缓慢，OOM错误

**诊断步骤**:
```bash
# 1. 检查内存使用
free -h
ps aux --sort=-%mem | head -10

# 2. 检查容器内存使用
docker stats --no-stream

# 3. 检查系统日志
dmesg | grep -i "killed process"
journalctl -u docker --since "1 hour ago"
```

**解决方案**:
```bash
# 清理系统缓存
sync && echo 3 > /proc/sys/vm/drop_caches

# 重启内存使用最高的服务
docker-compose -f docker-compose.prod.yml restart backend

# 清理Docker资源
docker system prune -f
docker volume prune -f
```

### 4. 磁盘空间不足

**症状**: 磁盘使用率超过90%，写入操作失败

**诊断步骤**:
```bash
# 1. 检查磁盘使用
df -h
du -sh /* | sort -hr | head -10

# 2. 查找大文件
find / -type f -size +100M -exec ls -lh {} \; 2>/dev/null | head -10

# 3. 检查日志文件大小
du -sh logs/
du -sh backend/logs/
du -sh nginx/logs/
```

**解决方案**:
```bash
# 清理旧日志文件
find logs/ -name "*.log" -mtime +7 -delete
find backend/logs/ -name "*.log" -mtime +7 -delete
find nginx/logs/ -name "*.log" -mtime +7 -delete

# 清理Docker资源
docker system prune -a -f
docker volume prune -f

# 清理旧备份
find backups/ -type d -mtime +30 -exec rm -rf {} \;
```

### 5. SSL证书问题

**症状**: HTTPS访问失败，证书过期警告

**诊断步骤**:
```bash
# 1. 检查证书状态
./scripts/setup-ssl.sh verify

# 2. 检查证书有效期
openssl x509 -in nginx/ssl/lawsker.com.crt -noout -dates

# 3. 测试HTTPS连接
curl -I https://lawsker.com
openssl s_client -connect lawsker.com:443 -servername lawsker.com
```

**解决方案**:
```bash
# 续期Let's Encrypt证书
./scripts/setup-ssl.sh renew

# 重新生成自签名证书（测试环境）
./scripts/setup-ssl.sh self-signed

# 重新加载NGINX配置
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

## 📊 监控和告警

### 监控面板访问
- **Grafana**: https://monitor.lawsker.com
  - 用户名: admin
  - 密码: 见环境变量 `GRAFANA_PASSWORD`
- **Prometheus**: https://monitor.lawsker.com/prometheus
- **Kibana**: https://logs.lawsker.com

### 关键监控指标

#### 系统指标
- CPU使用率 < 80%
- 内存使用率 < 85%
- 磁盘使用率 < 90%
- 网络延迟 < 100ms

#### 应用指标
- API响应时间P95 < 2秒
- 错误率 < 3%
- 可用性 > 99.5%
- 并发用户数

#### 业务指标
- 用户注册转化率
- 支付处理成功率 > 95% (技术指标，非业务承诺)
- 案件处理时效

### 告警规则配置

告警规则文件位置: `monitoring/prometheus/rules/lawsker-alerts.yml`

主要告警类型:
- 系统资源告警
- 应用性能告警
- 安全事件告警
- 业务异常告警

## 💾 备份和恢复

### 自动备份策略

#### 数据库备份
```bash
# 每日自动备份（凌晨2点）
0 2 * * * /path/to/lawsker/scripts/deploy-production.sh backup

# 手动创建备份
./scripts/deploy-production.sh backup
```

#### 配置文件备份
- NGINX配置
- Docker Compose文件
- 环境变量文件
- SSL证书

### 恢复流程

#### 数据库恢复
```bash
# 1. 停止应用服务
docker-compose -f docker-compose.prod.yml stop backend

# 2. 恢复数据库
docker-compose -f docker-compose.prod.yml exec postgres psql -U lawsker_user -d lawsker_prod < backup/database.sql

# 3. 重启服务
docker-compose -f docker-compose.prod.yml start backend
```

#### 完整系统恢复
```bash
# 使用备份恢复整个系统
./scripts/deploy-production.sh rollback backups/20240130_120000
```

## 🔒 安全操作

### 安全检查清单

#### 日常安全检查
```bash
# 执行安全监控
./scripts/security-monitor.sh check

# 检查失败登录尝试
./scripts/security-monitor.sh logins

# 检查可疑IP活动
./scripts/security-monitor.sh ips

# 检查SSL证书状态
./scripts/security-monitor.sh ssl
```

#### 安全事件响应

**发现安全威胁时**:
1. 立即隔离受影响的系统
2. 收集和保存证据
3. 通知安全团队
4. 执行应急响应计划

**常见安全操作**:
```bash
# 封禁可疑IP
iptables -A INPUT -s <suspicious_ip> -j DROP

# 强制用户重新登录
# 清理Redis会话数据
docker-compose -f docker-compose.prod.yml exec redis redis-cli FLUSHDB

# 更新安全配置
./scripts/run_security_hardening.sh
```

## 📈 性能优化

### 性能监控
```bash
# 启动性能监控
./scripts/performance-monitor.sh start

# 生成性能报告
./scripts/performance-monitor.sh report 24h

# 获取优化建议
./scripts/performance-monitor.sh suggest
```

### 常见性能问题

#### 数据库性能优化
```bash
# 分析慢查询
docker-compose -f docker-compose.prod.yml exec postgres psql -U lawsker_user -d lawsker_prod -c "
SELECT query, calls, total_time, mean_time, rows
FROM pg_stat_statements
ORDER BY total_time DESC LIMIT 10;"

# 重建索引
docker-compose -f docker-compose.prod.yml exec postgres psql -U lawsker_user -d lawsker_prod -c "REINDEX DATABASE lawsker_prod;"

# 更新统计信息
docker-compose -f docker-compose.prod.yml exec postgres psql -U lawsker_user -d lawsker_prod -c "ANALYZE;"
```

#### 缓存优化
```bash
# 检查Redis内存使用
docker-compose -f docker-compose.prod.yml exec redis redis-cli info memory

# 清理过期缓存
docker-compose -f docker-compose.prod.yml exec redis redis-cli --scan --pattern "*" | xargs docker-compose -f docker-compose.prod.yml exec redis redis-cli del

# 优化缓存配置
# 编辑 redis/redis.conf
```

## 📋 维护计划

### 日常维护任务

#### 每日任务
- [ ] 检查系统状态和告警
- [ ] 查看错误日志
- [ ] 监控资源使用情况
- [ ] 验证备份完成

#### 每周任务
- [ ] 清理旧日志文件
- [ ] 检查SSL证书状态
- [ ] 更新系统补丁
- [ ] 性能报告分析

#### 每月任务
- [ ] 安全漏洞扫描
- [ ] 数据库维护和优化
- [ ] 容量规划评估
- [ ] 灾难恢复演练

### 维护窗口

**计划维护时间**: 每周日凌晨2:00-4:00

**维护流程**:
1. 提前通知用户
2. 创建系统备份
3. 执行维护操作
4. 验证系统功能
5. 发布维护完成通知

## 📞 升级和联系

### 问题升级路径

1. **L1 (运维工程师)**: 基础问题处理
2. **L2 (技术负责人)**: 复杂技术问题
3. **L3 (架构师/CTO)**: 架构级问题

### 外部支持联系

- **云服务商支持**: 根据使用的云平台
- **第三方服务支持**: 支付、短信等服务商
- **安全厂商支持**: 安全产品技术支持

---

**重要提醒**:
- 所有操作都要记录在案
- 重要操作前必须备份
- 遇到不确定的问题及时升级
- 保持文档和流程的及时更新