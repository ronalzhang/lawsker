# Lawsker 系统常见问题解答 (FAQ)

## 概述

本文档收集了 Lawsker 系统部署、运维和使用过程中的常见问题及其解决方案。

## 目录

1. [部署相关问题](#部署相关问题)
2. [服务运行问题](#服务运行问题)
3. [数据库问题](#数据库问题)
4. [网络和SSL问题](#网络和ssl问题)
5. [性能问题](#性能问题)
6. [监控和日志问题](#监控和日志问题)
7. [用户和权限问题](#用户和权限问题)
8. [备份和恢复问题](#备份和恢复问题)

## 部署相关问题

### Q1: 部署脚本执行失败，提示权限不足

**问题描述**: 运行部署脚本时出现 "Permission denied" 错误。

**解决方案**:
```bash
# 1. 确保脚本有执行权限
chmod +x backend/deployment/deployment_orchestrator.py

# 2. 使用 sudo 运行需要管理员权限的操作
sudo python3 backend/deployment/deployment_orchestrator.py

# 3. 检查文件所有者
sudo chown -R $USER:$USER /opt/lawsker
```

### Q2: Python 虚拟环境创建失败

**问题描述**: 创建 Python 虚拟环境时出错。

**解决方案**:
```bash
# 1. 确保安装了 python3-venv
sudo apt install python3-venv python3-dev

# 2. 清理旧的虚拟环境
rm -rf backend/venv

# 3. 重新创建虚拟环境
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-prod.txt
```

### Q3: 前端构建失败，TypeScript 错误

**问题描述**: 前端构建时出现 TypeScript 编译错误。

**解决方案**:
```bash
# 1. 使用自动修复工具
python3 backend/deployment/typescript_fixer.py --fix-all

# 2. 手动安装类型定义
cd frontend
npm install --save-dev @types/node @types/react @types/react-dom

# 3. 更新 tsconfig.json 配置
{
  "compilerOptions": {
    "strict": false,
    "skipLibCheck": true,
    "allowSyntheticDefaultImports": true,
    "esModuleInterop": true
  }
}

# 4. 清理缓存重新构建
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Q4: 数据库迁移失败

**问题描述**: Alembic 数据库迁移执行失败。

**解决方案**:
```bash
# 1. 检查数据库连接
cd backend
source venv/bin/activate
alembic current

# 2. 如果是版本冲突，标记当前状态
alembic stamp head

# 3. 生成新的迁移文件
alembic revision --autogenerate -m "fix_migration"

# 4. 手动编辑迁移文件解决冲突
vim alembic/versions/xxx_fix_migration.py

# 5. 执行迁移
alembic upgrade head
```

### Q5: SSL 证书申请失败

**问题描述**: Let's Encrypt 证书申请失败。

**解决方案**:
```bash
# 1. 检查域名解析
nslookup lawsker.com

# 2. 确保防火墙开放 80 和 443 端口
sudo ufw allow 80
sudo ufw allow 443

# 3. 停止 Nginx 服务
sudo systemctl stop nginx

# 4. 使用 standalone 模式申请证书
sudo certbot certonly --standalone -d lawsker.com -d www.lawsker.com

# 5. 重启 Nginx
sudo systemctl start nginx
```

## 服务运行问题

### Q6: 后端服务启动失败

**问题描述**: `systemctl start lawsker-backend` 失败。

**解决方案**:
```bash
# 1. 查看详细错误信息
systemctl status lawsker-backend -l
journalctl -u lawsker-backend -f

# 2. 检查端口占用
sudo lsof -i :8000
sudo netstat -tlnp | grep :8000

# 3. 手动启动测试
cd /opt/lawsker
source backend/venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 4. 检查环境变量
cat .env.production
```

### Q7: Nginx 502 Bad Gateway 错误

**问题描述**: 访问网站时出现 502 错误。

**解决方案**:
```bash
# 1. 检查后端服务状态
systemctl status lawsker-backend

# 2. 测试后端连接
curl http://localhost:8000/api/v1/health

# 3. 检查 Nginx 配置
sudo nginx -t

# 4. 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log

# 5. 重启服务
sudo systemctl restart lawsker-backend
sudo systemctl restart nginx
```

### Q8: 服务频繁重启

**问题描述**: 服务不稳定，经常自动重启。

**解决方案**:
```bash
# 1. 检查系统资源
free -h
df -h
top

# 2. 查看 OOM 记录
dmesg | grep -i "killed process"
grep -i "out of memory" /var/log/syslog

# 3. 增加内存限制
sudo systemctl edit lawsker-backend
# 添加:
[Service]
MemoryMax=2G
Restart=always
RestartSec=10

# 4. 添加 swap 空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## 数据库问题

### Q9: 数据库连接被拒绝

**问题描述**: 应用无法连接到 PostgreSQL 数据库。

**解决方案**:
```bash
# 1. 检查 PostgreSQL 服务
systemctl status postgresql

# 2. 检查端口监听
sudo netstat -tlnp | grep :5432

# 3. 测试本地连接
sudo -u postgres psql -c "\l"

# 4. 检查认证配置
sudo vim /etc/postgresql/12/main/pg_hba.conf
# 确保包含:
# local   all             lawsker_user                            md5
# host    all             lawsker_user    127.0.0.1/32           md5

# 5. 重新加载配置
sudo systemctl reload postgresql
```

### Q10: 数据库查询缓慢

**问题描述**: 数据库查询响应时间过长。

**解决方案**:
```sql
-- 1. 查看慢查询
SELECT query, mean_time, calls
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY mean_time DESC
LIMIT 10;

-- 2. 分析查询计划
EXPLAIN ANALYZE SELECT * FROM cases WHERE user_id = 123;

-- 3. 添加索引
CREATE INDEX CONCURRENTLY idx_cases_user_id ON cases(user_id);

-- 4. 更新统计信息
ANALYZE;

-- 5. 清理死元组
VACUUM ANALYZE;
```

### Q11: 数据库连接数过多

**问题描述**: 数据库连接数达到上限。

**解决方案**:
```sql
-- 1. 查看当前连接
SELECT count(*) FROM pg_stat_activity;

-- 2. 查看连接详情
SELECT pid, usename, application_name, client_addr, state
FROM pg_stat_activity
WHERE state != 'idle';

-- 3. 终止空闲连接
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND query_start < now() - interval '1 hour';

-- 4. 调整连接池配置
-- 在应用配置中设置:
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_timeout': 30,
    'pool_recycle': 3600
}
```

## 网络和SSL问题

### Q12: HTTPS 访问显示证书错误

**问题描述**: 浏览器显示 SSL 证书无效或过期。

**解决方案**:
```bash
# 1. 检查证书状态
sudo certbot certificates

# 2. 检查证书有效期
openssl x509 -in /etc/letsencrypt/live/lawsker.com/cert.pem -noout -dates

# 3. 续期证书
sudo certbot renew

# 4. 如果续期失败，重新申请
sudo certbot delete --cert-name lawsker.com
sudo certbot certonly --nginx -d lawsker.com -d www.lawsker.com

# 5. 重启 Nginx
sudo systemctl restart nginx
```

### Q13: 域名无法访问

**问题描述**: 域名解析失败或无法访问。

**解决方案**:
```bash
# 1. 检查域名解析
nslookup lawsker.com
dig lawsker.com

# 2. 检查不同 DNS 服务器
nslookup lawsker.com 8.8.8.8

# 3. 清理本地 DNS 缓存
sudo systemctl restart systemd-resolved

# 4. 检查防火墙
sudo ufw status
sudo iptables -L

# 5. 测试网络连通性
ping lawsker.com
traceroute lawsker.com
```

### Q14: 网站访问速度慢

**问题描述**: 网站加载速度慢，响应时间长。

**解决方案**:
```bash
# 1. 启用 Nginx 压缩
# 在 nginx.conf 中添加:
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript;

# 2. 配置缓存
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# 3. 启用 HTTP/2
listen 443 ssl http2;

# 4. 优化数据库查询
# 添加适当的索引
# 使用连接池
# 启用查询缓存

# 5. 使用 CDN
# 配置静态资源 CDN
# 启用浏览器缓存
```

## 性能问题

### Q15: CPU 使用率过高

**问题描述**: 服务器 CPU 使用率持续很高。

**解决方案**:
```bash
# 1. 查看占用 CPU 的进程
top
htop
ps aux --sort=-%cpu | head -10

# 2. 分析应用性能
pip install py-spy
py-spy top --pid $(pgrep -f uvicorn)

# 3. 优化应用代码
# 使用异步处理
# 添加缓存
# 优化数据库查询

# 4. 调整进程优先级
renice 10 $(pgrep -f "non_critical_process")

# 5. 考虑水平扩展
# 添加负载均衡
# 部署多个应用实例
```

### Q16: 内存使用率过高

**问题描述**: 系统内存不足，应用被 OOM Killer 终止。

**解决方案**:
```bash
# 1. 查看内存使用
free -h
ps aux --sort=-%mem | head -10

# 2. 清理系统缓存
echo 3 > /proc/sys/vm/drop_caches

# 3. 添加 swap 空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 4. 优化应用内存使用
# 配置连接池大小
# 限制请求大小
# 使用内存分析工具

# 5. 调整系统参数
echo 'vm.swappiness=10' >> /etc/sysctl.conf
sysctl -p
```

### Q17: 磁盘空间不足

**问题描述**: 磁盘使用率过高，影响系统运行。

**解决方案**:
```bash
# 1. 查看磁盘使用情况
df -h
du -sh /var/log/*
du -sh /opt/lawsker/*

# 2. 清理日志文件
sudo logrotate -f /etc/logrotate.d/lawsker
find /var/log -name "*.log" -mtime +7 -delete

# 3. 清理临时文件
find /tmp -type f -atime +7 -delete
find /var/tmp -type f -atime +7 -delete

# 4. 清理应用缓存
rm -rf /opt/lawsker/backend/__pycache__/*
npm cache clean --force

# 5. 扩展磁盘空间
# 如果使用 LVM:
sudo lvextend -L +10G /dev/vg0/lv_root
sudo resize2fs /dev/vg0/lv_root
```

## 监控和日志问题

### Q18: Prometheus 无法收集数据

**问题描述**: Prometheus 监控面板显示目标服务器状态为 DOWN。

**解决方案**:
```bash
# 1. 检查 Prometheus 服务
systemctl status prometheus

# 2. 检查配置文件
sudo vim /etc/prometheus/prometheus.yml

# 3. 验证目标可达性
curl http://localhost:8000/metrics
curl http://localhost:9100/metrics

# 4. 检查防火墙
sudo ufw allow from 127.0.0.1 to any port 9090

# 5. 重启服务
sudo systemctl restart prometheus
```

### Q19: Grafana 无法访问

**问题描述**: 无法访问 Grafana 监控面板。

**解决方案**:
```bash
# 1. 检查 Grafana 服务
systemctl status grafana-server

# 2. 检查端口监听
sudo netstat -tlnp | grep :3000

# 3. 检查配置文件
sudo vim /etc/grafana/grafana.ini

# 4. 重置管理员密码
sudo grafana-cli admin reset-admin-password admin

# 5. 重启服务
sudo systemctl restart grafana-server
```

### Q20: 日志文件过大

**问题描述**: 日志文件占用大量磁盘空间。

**解决方案**:
```bash
# 1. 配置日志轮转
sudo vim /etc/logrotate.d/lawsker
# 内容:
/var/log/lawsker/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
}

# 2. 手动执行轮转
sudo logrotate -f /etc/logrotate.d/lawsker

# 3. 清理旧日志
find /var/log -name "*.log" -mtime +30 -delete

# 4. 调整应用日志级别
# 在生产环境设置为 INFO 或 WARNING
LOG_LEVEL=INFO
```

## 用户和权限问题

### Q21: 文件权限错误

**问题描述**: 应用无法读写文件，提示权限不足。

**解决方案**:
```bash
# 1. 检查文件所有者
ls -la /opt/lawsker

# 2. 修复文件权限
sudo chown -R www-data:www-data /opt/lawsker
sudo chmod -R 755 /opt/lawsker
sudo chmod -R 644 /opt/lawsker/frontend

# 3. 设置上传目录权限
sudo mkdir -p /opt/lawsker/uploads
sudo chown -R www-data:www-data /opt/lawsker/uploads
sudo chmod -R 755 /opt/lawsker/uploads

# 4. 保护敏感文件
sudo chmod 600 /opt/lawsker/.env.production
sudo chown root:root /opt/lawsker/.env.production
```

### Q22: 数据库用户权限问题

**问题描述**: 数据库操作失败，提示权限不足。

**解决方案**:
```sql
-- 1. 连接到 PostgreSQL
sudo -u postgres psql

-- 2. 检查用户权限
\du

-- 3. 授予必要权限
GRANT ALL PRIVILEGES ON DATABASE lawsker_prod TO lawsker_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO lawsker_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO lawsker_user;

-- 4. 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO lawsker_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO lawsker_user;
```

## 备份和恢复问题

### Q23: 数据库备份失败

**问题描述**: 自动备份脚本执行失败。

**解决方案**:
```bash
# 1. 检查备份脚本权限
chmod +x /opt/lawsker/scripts/backup_database.sh

# 2. 检查备份目录
sudo mkdir -p /backup/database
sudo chown postgres:postgres /backup/database

# 3. 测试手动备份
pg_dump -h localhost -U lawsker_user lawsker_prod > /backup/test_backup.sql

# 4. 检查 cron 任务
crontab -l
sudo crontab -l

# 5. 查看备份日志
tail -f /var/log/backup.log
```

### Q24: 数据库恢复失败

**问题描述**: 从备份恢复数据库时出错。

**解决方案**:
```bash
# 1. 检查备份文件完整性
file /backup/lawsker_backup.sql.gz
gunzip -t /backup/lawsker_backup.sql.gz

# 2. 停止应用服务
sudo systemctl stop lawsker-backend

# 3. 创建新数据库
sudo -u postgres psql -c "DROP DATABASE IF EXISTS lawsker_prod;"
sudo -u postgres psql -c "CREATE DATABASE lawsker_prod OWNER lawsker_user;"

# 4. 恢复数据
gunzip -c /backup/lawsker_backup.sql.gz | sudo -u postgres psql -d lawsker_prod

# 5. 验证恢复结果
sudo -u postgres psql -d lawsker_prod -c "\dt"

# 6. 重启应用
sudo systemctl start lawsker-backend
```

## 其他常见问题

### Q25: 如何查看系统整体状态？

**解决方案**:
```bash
# 使用交互式故障排除工具
python3 backend/deployment/interactive_troubleshooter.py

# 或运行快速诊断
python3 backend/deployment/run_integration_tests.py e2e --environment production

# 查看系统资源
htop
df -h
free -h
systemctl status nginx lawsker-backend postgresql redis
```

### Q26: 如何进行性能调优？

**解决方案**:
```bash
# 1. 数据库优化
sudo -u postgres psql -d lawsker_prod -c "VACUUM ANALYZE;"

# 2. 添加数据库索引
CREATE INDEX CONCURRENTLY idx_cases_user_status ON cases(user_id, status);

# 3. 启用应用缓存
# 配置 Redis 缓存
# 使用 @cache_result 装饰器

# 4. 优化 Nginx 配置
# 启用 gzip 压缩
# 配置静态文件缓存
# 启用 HTTP/2

# 5. 系统级优化
echo 'net.core.somaxconn = 65535' >> /etc/sysctl.conf
sysctl -p
```

### Q27: 如何设置监控告警？

**解决方案**:
```yaml
# 1. 配置 Prometheus 告警规则
# /etc/prometheus/rules/lawsker.yml
groups:
  - name: lawsker
    rules:
      - alert: HighResponseTime
        expr: http_request_duration_seconds{quantile="0.95"} > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API response time too high"

# 2. 配置 Alertmanager
# /etc/alertmanager/alertmanager.yml
route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://localhost:5001/'

# 3. 重启服务
sudo systemctl restart prometheus
sudo systemctl restart alertmanager
```

### Q28: 如何进行安全加固？

**解决方案**:
```bash
# 1. 系统安全
sudo ufw enable
sudo ufw default deny incoming
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# 2. SSH 安全
sudo vim /etc/ssh/sshd_config
# PermitRootLogin no
# PasswordAuthentication no
# PubkeyAuthentication yes

# 3. 应用安全
# 设置强密码
# 启用 HTTPS
# 配置 CSRF 保护
# 输入验证和过滤

# 4. 数据库安全
# 限制数据库连接
# 使用强密码
# 启用 SSL 连接
# 定期更新

# 5. 定期安全更新
sudo apt update && sudo apt upgrade
```

---

## 获取帮助

如果以上解决方案无法解决您的问题，请：

1. **查看详细日志**: 
   - 应用日志: `/var/log/lawsker/`
   - 系统日志: `/var/log/syslog`
   - 服务日志: `journalctl -u service_name`

2. **使用诊断工具**:
   ```bash
   python3 backend/deployment/interactive_troubleshooter.py
   ```

3. **联系技术支持**:
   - 邮箱: tech-support@lawsker.com
   - 电话: +86-xxx-xxxx-xxxx
   - 在线文档: https://docs.lawsker.com

4. **提交问题报告**:
   - GitHub Issues: https://github.com/lawsker/lawsker/issues
   - 包含错误日志和系统信息

---

**文档版本**: 1.0  
**最后更新**: 2024年8月24日  
**维护者**: Lawsker 技术团队