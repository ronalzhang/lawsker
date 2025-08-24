# Lawsker 系统故障排除指南

## 概述

本指南提供了 Lawsker 系统常见问题的诊断和解决方案，帮助运维人员快速定位和解决系统故障。

## 目录

1. [快速诊断工具](#快速诊断工具)
2. [服务相关问题](#服务相关问题)
3. [数据库问题](#数据库问题)
4. [网络和SSL问题](#网络和ssl问题)
5. [性能问题](#性能问题)
6. [部署问题](#部署问题)
7. [监控和日志问题](#监控和日志问题)
8. [常用命令参考](#常用命令参考)

## 快速诊断工具

### 系统健康检查脚本

```bash
#!/bin/bash
# quick_diagnosis.sh - 快速诊断脚本

echo "=== Lawsker 系统快速诊断 $(date) ==="

# 1. 检查关键服务状态
echo "1. 服务状态检查:"
services=("nginx" "lawsker-backend" "postgresql" "redis")
for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service"; then
        echo "  ✓ $service: 运行中"
    else
        echo "  ✗ $service: 停止 - $(systemctl is-failed $service)"
    fi
done

# 2. 检查端口监听
echo -e "\n2. 端口监听检查:"
ports=("80:HTTP" "443:HTTPS" "8000:Backend" "5432:PostgreSQL" "6379:Redis")
for port_info in "${ports[@]}"; do
    port=$(echo $port_info | cut -d: -f1)
    name=$(echo $port_info | cut -d: -f2)
    if netstat -tlnp | grep -q ":$port "; then
        echo "  ✓ $name ($port): 监听中"
    else
        echo "  ✗ $name ($port): 未监听"
    fi
done

# 3. 检查系统资源
echo -e "\n3. 系统资源检查:"
# CPU 使用率
cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
echo "  CPU 使用率: ${cpu_usage}%"

# 内存使用率
memory_usage=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
echo "  内存使用率: ${memory_usage}%"

# 磁盘使用率
disk_usage=$(df / | awk 'NR==2{print $5}')
echo "  磁盘使用率: $disk_usage"

# 负载平均值
load_avg=$(uptime | awk '{print $(NF-2) " " $(NF-1) " " $NF}')
echo "  负载平均值: $load_avg"

# 4. 检查应用连通性
echo -e "\n4. 应用连通性检查:"
if curl -sf http://localhost:8000/api/v1/health > /dev/null; then
    echo "  ✓ 后端 API: 正常"
else
    echo "  ✗ 后端 API: 异常"
fi

if curl -sf https://lawsker.com > /dev/null 2>&1; then
    echo "  ✓ 前端页面: 正常"
else
    echo "  ✗ 前端页面: 异常"
fi

# 5. 检查数据库连接
echo -e "\n5. 数据库连接检查:"
if sudo -u postgres psql -d lawsker_prod -c "SELECT 1;" > /dev/null 2>&1; then
    echo "  ✓ PostgreSQL: 连接正常"
else
    echo "  ✗ PostgreSQL: 连接失败"
fi

if redis-cli ping > /dev/null 2>&1; then
    echo "  ✓ Redis: 连接正常"
else
    echo "  ✗ Redis: 连接失败"
fi

# 6. 检查最近的错误日志
echo -e "\n6. 最近的错误日志:"
echo "  应用错误 (最近10条):"
tail -n 10 /var/log/lawsker/error.log 2>/dev/null | grep -i error | tail -n 3 || echo "    无错误日志"

echo "  Nginx 错误 (最近3条):"
tail -n 10 /var/log/nginx/error.log 2>/dev/null | tail -n 3 || echo "    无错误日志"

echo -e "\n=== 诊断完成 ==="
```

### 日志分析工具

```bash
#!/bin/bash
# log_analyzer.sh - 日志分析工具

LOG_FILE="$1"
TIME_RANGE="${2:-1h}"  # 默认分析最近1小时

if [ -z "$LOG_FILE" ]; then
    echo "用法: $0 <log_file> [time_range]"
    echo "示例: $0 /var/log/nginx/access.log 1h"
    exit 1
fi

echo "=== 日志分析: $LOG_FILE (最近 $TIME_RANGE) ==="

# 根据时间范围过滤日志
case $TIME_RANGE in
    "1h") time_filter="-1 hour" ;;
    "6h") time_filter="-6 hours" ;;
    "1d") time_filter="-1 day" ;;
    *) time_filter="-1 hour" ;;
esac

# 分析 Nginx 访问日志
if [[ "$LOG_FILE" == *"access.log"* ]]; then
    echo "1. 访问量统计:"
    awk -v date="$(date -d "$time_filter" '+%d/%b/%Y:%H')" '$4 >= "["date {count++} END {print "  总访问量:", count+0}' "$LOG_FILE"
    
    echo -e "\n2. 状态码分布:"
    awk -v date="$(date -d "$time_filter" '+%d/%b/%Y:%H')" '$4 >= "["date {print $9}' "$LOG_FILE" | sort | uniq -c | sort -nr | head -5 | awk '{printf "  %s: %d\n", $2, $1}'
    
    echo -e "\n3. 访问最多的IP:"
    awk -v date="$(date -d "$time_filter" '+%d/%b/%Y:%H')" '$4 >= "["date {print $1}' "$LOG_FILE" | sort | uniq -c | sort -nr | head -5 | awk '{printf "  %s: %d 次\n", $2, $1}'
    
    echo -e "\n4. 访问最多的页面:"
    awk -v date="$(date -d "$time_filter" '+%d/%b/%Y:%H')" '$4 >= "["date {print $7}' "$LOG_FILE" | sort | uniq -c | sort -nr | head -5 | awk '{printf "  %s: %d 次\n", $2, $1}'

# 分析应用错误日志
elif [[ "$LOG_FILE" == *"error.log"* ]]; then
    echo "1. 错误级别统计:"
    grep -i "error\|warning\|critical" "$LOG_FILE" | awk '{print $3}' | sort | uniq -c | sort -nr
    
    echo -e "\n2. 最近的错误信息:"
    tail -n 20 "$LOG_FILE" | grep -i error | tail -n 5
    
    echo -e "\n3. 错误频率分析:"
    grep -i error "$LOG_FILE" | awk '{print $1" "$2}' | cut -c1-13 | sort | uniq -c | sort -nr | head -5
fi

echo -e "\n=== 分析完成 ==="
```

## 服务相关问题

### 问题1: 后端服务无法启动

**症状**:
- `systemctl start lawsker-backend` 失败
- 服务状态显示 "failed" 或 "inactive"

**诊断步骤**:

```bash
# 1. 查看服务状态
systemctl status lawsker-backend -l

# 2. 查看服务日志
journalctl -u lawsker-backend -f

# 3. 检查配置文件
cat /etc/systemd/system/lawsker-backend.service

# 4. 手动启动测试
cd /opt/lawsker
source backend/venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**常见原因和解决方案**:

1. **端口被占用**:
```bash
# 查找占用端口的进程
sudo lsof -i :8000
# 或
sudo netstat -tlnp | grep :8000

# 终止占用进程
sudo kill -9 <PID>
```

2. **Python 虚拟环境问题**:
```bash
# 重新创建虚拟环境
cd /opt/lawsker/backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-prod.txt
```

3. **权限问题**:
```bash
# 修复文件权限
sudo chown -R www-data:www-data /opt/lawsker
sudo chmod +x /opt/lawsker/backend/venv/bin/uvicorn
```

4. **环境变量缺失**:
```bash
# 检查环境变量文件
cat /opt/lawsker/.env.production

# 确保包含必要的配置
grep -E "DB_|REDIS_|SECRET_KEY" /opt/lawsker/.env.production
```

### 问题2: Nginx 配置错误

**症状**:
- 网站无法访问
- 502 Bad Gateway 错误
- SSL 证书错误

**诊断步骤**:

```bash
# 1. 测试 Nginx 配置
sudo nginx -t

# 2. 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log

# 3. 检查 Nginx 状态
systemctl status nginx

# 4. 检查站点配置
cat /etc/nginx/sites-available/lawsker.conf
```

**解决方案**:

1. **配置语法错误**:
```bash
# 修复配置文件后重新加载
sudo nginx -t
sudo systemctl reload nginx
```

2. **上游服务器不可用**:
```bash
# 检查后端服务
curl http://localhost:8000/api/v1/health

# 重启后端服务
sudo systemctl restart lawsker-backend
```

3. **SSL 证书问题**:
```bash
# 检查证书文件
sudo ls -la /etc/letsencrypt/live/lawsker.com/

# 重新申请证书
sudo certbot certonly --nginx -d lawsker.com
```

### 问题3: 服务频繁重启

**症状**:
- 服务状态显示频繁的启动和停止
- 应用间歇性不可用

**诊断步骤**:

```bash
# 1. 查看服务重启历史
journalctl -u lawsker-backend --since "1 hour ago" | grep -E "Started|Stopped"

# 2. 检查系统资源
top
free -h
df -h

# 3. 查看 OOM 杀死记录
dmesg | grep -i "killed process"
grep -i "out of memory" /var/log/syslog

# 4. 检查应用内存使用
ps aux | grep uvicorn
```

**解决方案**:

1. **内存不足导致 OOM**:
```bash
# 增加 swap 空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久启用
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

2. **应用内存泄漏**:
```bash
# 配置服务自动重启
sudo systemctl edit lawsker-backend

# 添加以下内容
[Service]
Restart=always
RestartSec=10
MemoryMax=1G
```

3. **配置应用内存限制**:
```python
# 在应用配置中添加
import resource

# 限制内存使用 (1GB)
resource.setrlimit(resource.RLIMIT_AS, (1024*1024*1024, 1024*1024*1024))
```

## 数据库问题

### 问题1: 数据库连接失败

**症状**:
- 应用报告数据库连接错误
- "connection refused" 或 "authentication failed" 错误

**诊断步骤**:

```bash
# 1. 检查 PostgreSQL 服务状态
systemctl status postgresql

# 2. 检查数据库进程
ps aux | grep postgres

# 3. 检查端口监听
netstat -tlnp | grep :5432

# 4. 测试数据库连接
sudo -u postgres psql -c "\l"
psql -h localhost -U lawsker_user -d lawsker_prod -c "SELECT version();"

# 5. 查看数据库日志
sudo tail -f /var/log/postgresql/postgresql-12-main.log
```

**解决方案**:

1. **服务未启动**:
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

2. **认证配置问题**:
```bash
# 检查 pg_hba.conf
sudo cat /etc/postgresql/12/main/pg_hba.conf

# 确保包含以下行
# local   all             lawsker_user                            md5
# host    all             lawsker_user    127.0.0.1/32           md5

# 重新加载配置
sudo systemctl reload postgresql
```

3. **用户权限问题**:
```sql
-- 连接到 PostgreSQL
sudo -u postgres psql

-- 检查用户
\du

-- 重新设置密码
ALTER USER lawsker_user WITH PASSWORD 'new_password';

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE lawsker_prod TO lawsker_user;
```

### 问题2: 数据库性能问题

**症状**:
- 查询响应缓慢
- 应用超时错误
- 数据库 CPU 使用率高

**诊断步骤**:

```sql
-- 1. 查看当前活动连接
SELECT pid, usename, application_name, client_addr, state, query_start, query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start;

-- 2. 查看慢查询
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY mean_time DESC
LIMIT 10;

-- 3. 查看锁等待
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.usename AS blocked_user,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.usename AS blocking_user,
       blocked_activity.query AS blocked_statement,
       blocking_activity.query AS current_statement_in_blocking_process
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- 4. 查看表统计信息
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del, n_tup_hot_upd
FROM pg_stat_user_tables
ORDER BY n_tup_ins + n_tup_upd + n_tup_del DESC;
```

**解决方案**:

1. **终止长时间运行的查询**:
```sql
-- 终止特定查询
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid = <PID>;

-- 终止所有长时间运行的查询
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state != 'idle'
  AND query_start < now() - interval '5 minutes';
```

2. **优化数据库配置**:
```bash
# 编辑 postgresql.conf
sudo vim /etc/postgresql/12/main/postgresql.conf

# 优化配置
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB

# 重启服务
sudo systemctl restart postgresql
```

3. **执行数据库维护**:
```sql
-- 分析表统计信息
ANALYZE;

-- 清理死元组
VACUUM ANALYZE;

-- 重建索引
REINDEX DATABASE lawsker_prod;
```

### 问题3: 数据库磁盘空间不足

**症状**:
- 写入操作失败
- "No space left on device" 错误

**诊断步骤**:

```bash
# 1. 检查磁盘使用情况
df -h

# 2. 查看数据库大小
sudo -u postgres psql -c "
SELECT pg_database.datname,
       pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
ORDER BY pg_database_size(pg_database.datname) DESC;"

# 3. 查看表大小
sudo -u postgres psql -d lawsker_prod -c "
SELECT tablename,
       pg_size_pretty(pg_total_relation_size(tablename::regclass)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::regclass) DESC;"

# 4. 查看 WAL 文件
sudo ls -lh /var/lib/postgresql/12/main/pg_wal/
```

**解决方案**:

1. **清理 WAL 文件**:
```sql
-- 检查 WAL 设置
SHOW wal_keep_segments;
SHOW max_wal_size;

-- 手动清理 WAL
SELECT pg_switch_wal();
CHECKPOINT;
```

2. **清理旧数据**:
```sql
-- 删除旧的日志记录
DELETE FROM access_logs WHERE created_at < now() - interval '30 days';

-- 清理临时表
DROP TABLE IF EXISTS temp_table_name;

-- 执行 VACUUM
VACUUM FULL;
```

3. **扩展磁盘空间**:
```bash
# 如果使用 LVM
sudo lvextend -L +10G /dev/vg0/lv_root
sudo resize2fs /dev/vg0/lv_root

# 或者添加新的数据目录
sudo mkdir /data/postgresql
sudo chown postgres:postgres /data/postgresql
sudo -u postgres initdb -D /data/postgresql
```

## 网络和SSL问题

### 问题1: SSL 证书过期或无效

**症状**:
- 浏览器显示证书错误
- HTTPS 连接失败

**诊断步骤**:

```bash
# 1. 检查证书有效期
openssl x509 -in /etc/letsencrypt/live/lawsker.com/cert.pem -noout -dates

# 2. 检查证书详情
openssl x509 -in /etc/letsencrypt/live/lawsker.com/cert.pem -noout -text

# 3. 测试 SSL 连接
openssl s_client -connect lawsker.com:443 -servername lawsker.com

# 4. 检查 Certbot 状态
sudo certbot certificates

# 5. 查看 Certbot 日志
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

**解决方案**:

1. **手动续期证书**:
```bash
# 续期所有证书
sudo certbot renew

# 续期特定证书
sudo certbot renew --cert-name lawsker.com

# 强制续期
sudo certbot renew --force-renewal
```

2. **重新申请证书**:
```bash
# 删除现有证书
sudo certbot delete --cert-name lawsker.com

# 重新申请
sudo certbot certonly --nginx -d lawsker.com -d www.lawsker.com

# 重启 Nginx
sudo systemctl restart nginx
```

3. **设置自动续期**:
```bash
# 添加 cron 任务
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

# 或使用 systemd timer
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### 问题2: 域名解析问题

**症状**:
- 域名无法访问
- DNS 解析失败

**诊断步骤**:

```bash
# 1. 检查域名解析
nslookup lawsker.com
dig lawsker.com

# 2. 检查不同 DNS 服务器
nslookup lawsker.com 8.8.8.8
nslookup lawsker.com 1.1.1.1

# 3. 检查本地 DNS 配置
cat /etc/resolv.conf

# 4. 测试网络连通性
ping lawsker.com
traceroute lawsker.com

# 5. 检查防火墙规则
sudo ufw status
sudo iptables -L
```

**解决方案**:

1. **DNS 缓存问题**:
```bash
# 清理本地 DNS 缓存
sudo systemctl restart systemd-resolved

# 或者
sudo service networking restart
```

2. **防火墙阻塞**:
```bash
# 检查并开放必要端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload
```

3. **域名配置问题**:
```bash
# 检查域名注册商的 DNS 设置
# 确保 A 记录指向正确的 IP 地址
# 确保 CNAME 记录配置正确
```

### 问题3: 网络连接超时

**症状**:
- 请求超时
- 连接被重置

**诊断步骤**:

```bash
# 1. 检查网络连接
netstat -an | grep ESTABLISHED | wc -l
ss -tuln

# 2. 检查连接限制
ulimit -n
cat /proc/sys/fs/file-max

# 3. 检查 TCP 连接状态
netstat -an | awk '/^tcp/ {print $6}' | sort | uniq -c

# 4. 监控网络流量
iftop
nethogs

# 5. 检查系统负载
uptime
iostat 1 5
```

**解决方案**:

1. **调整连接限制**:
```bash
# 临时调整
ulimit -n 65535

# 永久调整
echo "* soft nofile 65535" >> /etc/security/limits.conf
echo "* hard nofile 65535" >> /etc/security/limits.conf
```

2. **优化 TCP 参数**:
```bash
# 编辑 /etc/sysctl.conf
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_keepalive_time = 1200

# 应用配置
sudo sysctl -p
```

3. **配置 Nginx 连接池**:
```nginx
upstream backend {
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

server {
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
```

## 性能问题

### 问题1: 响应时间过长

**症状**:
- API 响应缓慢
- 页面加载时间长

**诊断步骤**:

```bash
# 1. 测试 API 响应时间
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/health

# curl-format.txt 内容:
#     time_namelookup:  %{time_namelookup}\n
#        time_connect:  %{time_connect}\n
#     time_appconnect:  %{time_appconnect}\n
#    time_pretransfer:  %{time_pretransfer}\n
#       time_redirect:  %{time_redirect}\n
#  time_starttransfer:  %{time_starttransfer}\n
#                     ----------\n
#          time_total:  %{time_total}\n

# 2. 检查系统负载
top
htop
iostat -x 1 5

# 3. 分析应用性能
# 使用 Python 性能分析工具
pip install py-spy
py-spy top --pid $(pgrep -f uvicorn)

# 4. 检查数据库查询性能
sudo -u postgres psql -d lawsker_prod -c "
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;"
```

**解决方案**:

1. **启用应用缓存**:
```python
# 在应用中添加 Redis 缓存
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=1)

def cache_result(timeout=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, timeout, json.dumps(result, default=str))
            return result
        return wrapper
    return decorator
```

2. **优化数据库查询**:
```sql
-- 添加索引
CREATE INDEX CONCURRENTLY idx_cases_user_id ON cases(user_id);
CREATE INDEX CONCURRENTLY idx_documents_case_id ON documents(case_id);

-- 优化查询
EXPLAIN ANALYZE SELECT * FROM cases WHERE user_id = 123;
```

3. **配置 Nginx 缓存**:
```nginx
# 添加缓存配置
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;

location /api/v1/statistics {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_key "$scheme$request_method$host$request_uri";
    proxy_pass http://backend;
}
```

### 问题2: 内存使用过高

**症状**:
- 系统内存不足
- 应用被 OOM Killer 终止

**诊断步骤**:

```bash
# 1. 检查内存使用情况
free -h
cat /proc/meminfo

# 2. 查看进程内存使用
ps aux --sort=-%mem | head -10
pmap -x $(pgrep -f uvicorn)

# 3. 检查内存泄漏
valgrind --tool=memcheck --leak-check=full python app.py

# 4. 监控内存使用趋势
sar -r 1 60

# 5. 检查 OOM 记录
dmesg | grep -i "killed process"
grep -i "out of memory" /var/log/syslog
```

**解决方案**:

1. **优化应用内存使用**:
```python
# 配置数据库连接池
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_timeout': 30,
    'pool_recycle': 3600
}

# 限制请求大小
from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()

@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    if request.headers.get("content-length"):
        content_length = int(request.headers["content-length"])
        if content_length > 16 * 1024 * 1024:  # 16MB limit
            return Response("Request too large", status_code=413)
    return await call_next(request)
```

2. **配置系统内存管理**:
```bash
# 调整 swappiness
echo 'vm.swappiness=10' >> /etc/sysctl.conf

# 配置 OOM 分数
echo -1000 > /proc/$(pgrep -f postgres)/oom_score_adj
echo -500 > /proc/$(pgrep -f uvicorn)/oom_score_adj
```

3. **添加内存监控**:
```bash
#!/bin/bash
# memory_monitor.sh
while true; do
    mem_usage=$(free | awk 'NR==2{printf "%.2f", $3*100/$2}')
    if (( $(echo "$mem_usage > 85" | bc -l) )); then
        echo "$(date): Memory usage high: ${mem_usage}%" >> /var/log/memory_alert.log
        # 可以添加告警通知
    fi
    sleep 60
done
```

### 问题3: CPU 使用率过高

**症状**:
- 系统响应缓慢
- CPU 使用率持续高于 80%

**诊断步骤**:

```bash
# 1. 查看 CPU 使用情况
top
htop
sar -u 1 60

# 2. 查看进程 CPU 使用
ps aux --sort=-%cpu | head -10

# 3. 分析 CPU 使用模式
iostat -c 1 10
vmstat 1 10

# 4. 查看系统调用
strace -p $(pgrep -f uvicorn) -c

# 5. 分析应用性能瓶颈
py-spy record -o profile.svg --pid $(pgrep -f uvicorn) --duration 60
```

**解决方案**:

1. **优化应用代码**:
```python
# 使用异步处理
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

async def cpu_intensive_task():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, blocking_function)
    return result

# 添加请求限流
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/v1/data")
@limiter.limit("10/minute")
async def get_data(request: Request):
    return {"data": "example"}
```

2. **配置进程优先级**:
```bash
# 降低非关键进程优先级
renice 10 $(pgrep -f "log_processor")

# 提高关键进程优先级
renice -5 $(pgrep -f uvicorn)
```

3. **启用 CPU 亲和性**:
```bash
# 绑定进程到特定 CPU 核心
taskset -cp 0,1 $(pgrep -f uvicorn)
taskset -cp 2,3 $(pgrep -f postgres)
```

## 部署问题

### 问题1: 部署脚本执行失败

**症状**:
- 自动化部署中断
- 组件部署失败

**诊断步骤**:

```bash
# 1. 查看部署日志
tail -f /var/log/lawsker/deployment.log

# 2. 检查部署状态
python3 backend/deployment/deployment_orchestrator.py --status

# 3. 验证环境配置
python3 backend/deployment/run_integration_tests.py e2e --environment staging

# 4. 检查依赖安装
source backend/venv/bin/activate
pip check

# 5. 验证数据库迁移
cd backend
alembic current
alembic history
```

**解决方案**:

1. **重新运行失败的组件**:
```bash
# 单独运行失败的组件
python3 backend/deployment/dependency_manager.py --install
python3 backend/deployment/database_configurator.py --setup
python3 backend/deployment/frontend_builder.py --build-all
```

2. **修复依赖问题**:
```bash
# 清理并重新安装依赖
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-prod.txt
```

3. **回滚到上一个版本**:
```bash
# 使用部署回滚脚本
python3 backend/deployment/deployment_rollback.py --rollback-to latest-stable
```

### 问题2: 前端构建失败

**症状**:
- TypeScript 编译错误
- 依赖安装失败

**诊断步骤**:

```bash
# 1. 检查 Node.js 版本
node --version
npm --version

# 2. 查看构建日志
cd frontend
npm run build 2>&1 | tee build.log

# 3. 检查依赖
npm ls
npm audit

# 4. 清理缓存
npm cache clean --force
rm -rf node_modules package-lock.json
```

**解决方案**:

1. **修复 TypeScript 错误**:
```bash
# 使用自动修复工具
python3 backend/deployment/typescript_fixer.py --fix-all

# 手动修复常见错误
# 添加类型定义
npm install --save-dev @types/node @types/react

# 更新 tsconfig.json
{
  "compilerOptions": {
    "strict": false,
    "skipLibCheck": true,
    "allowSyntheticDefaultImports": true
  }
}
```

2. **解决依赖冲突**:
```bash
# 使用 npm 修复
npm audit fix

# 强制解决冲突
npm install --legacy-peer-deps

# 或使用 yarn
npm install -g yarn
yarn install
```

### 问题3: 数据库迁移失败

**症状**:
- Alembic 迁移错误
- 数据库结构不一致

**诊断步骤**:

```bash
# 1. 检查迁移状态
cd backend
alembic current
alembic history --verbose

# 2. 检查数据库连接
alembic show current

# 3. 验证迁移文件
alembic check

# 4. 查看迁移日志
tail -f /var/log/lawsker/migration.log
```

**解决方案**:

1. **修复迁移冲突**:
```bash
# 标记当前状态
alembic stamp head

# 生成新的迁移
alembic revision --autogenerate -m "fix_migration_conflict"

# 手动编辑迁移文件解决冲突
vim alembic/versions/xxx_fix_migration_conflict.py
```

2. **重置迁移历史**:
```bash
# 备份数据库
pg_dump -h localhost -U lawsker_user lawsker_prod > backup.sql

# 删除迁移历史
alembic downgrade base

# 重新应用迁移
alembic upgrade head
```

## 监控和日志问题

### 问题1: Prometheus 数据收集异常

**症状**:
- 监控数据缺失
- 目标服务器状态为 DOWN

**诊断步骤**:

```bash
# 1. 检查 Prometheus 服务
systemctl status prometheus
curl http://localhost:9090/api/v1/targets

# 2. 检查配置文件
cat /etc/prometheus/prometheus.yml

# 3. 验证目标可达性
curl http://localhost:8000/metrics
curl http://localhost:9100/metrics  # node_exporter

# 4. 查看 Prometheus 日志
journalctl -u prometheus -f
```

**解决方案**:

1. **修复配置问题**:
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'lawsker-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
```

2. **重启相关服务**:
```bash
sudo systemctl restart prometheus
sudo systemctl restart node_exporter
```

### 问题2: 日志轮转问题

**症状**:
- 日志文件过大
- 磁盘空间不足

**解决方案**:

```bash
# 配置 logrotate
sudo tee /etc/logrotate.d/lawsker > /dev/null << EOF
/var/log/lawsker/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload lawsker-backend
    endscript
}
EOF

# 手动执行轮转
sudo logrotate -f /etc/logrotate.d/lawsker
```

## 常用命令参考

### 系统监控命令

```bash
# 系统资源监控
top                    # 实时进程监控
htop                   # 增强版 top
iotop                  # I/O 监控
iftop                  # 网络流量监控
nethogs                # 按进程网络使用
vmstat 1 10           # 虚拟内存统计
iostat -x 1 10        # I/O 统计
sar -u 1 60           # CPU 使用统计

# 磁盘和文件系统
df -h                  # 磁盘使用情况
du -sh /path          # 目录大小
lsof                   # 打开文件列表
fuser -v /path        # 使用文件的进程

# 网络诊断
netstat -tlnp         # 监听端口
ss -tuln              # Socket 统计
nmap localhost        # 端口扫描
tcpdump -i eth0       # 网络包捕获
```

### 服务管理命令

```bash
# Systemd 服务管理
systemctl status service_name
systemctl start service_name
systemctl stop service_name
systemctl restart service_name
systemctl reload service_name
systemctl enable service_name
systemctl disable service_name

# 查看服务日志
journalctl -u service_name
journalctl -u service_name -f
journalctl -u service_name --since "1 hour ago"
```

### 数据库管理命令

```bash
# PostgreSQL 管理
sudo -u postgres psql                    # 连接数据库
sudo -u postgres createdb dbname         # 创建数据库
sudo -u postgres dropdb dbname           # 删除数据库
pg_dump dbname > backup.sql              # 备份数据库
psql dbname < backup.sql                 # 恢复数据库

# 常用 SQL 查询
\l                     # 列出数据库
\dt                    # 列出表
\du                    # 列出用户
\q                     # 退出
```

### 日志分析命令

```bash
# 日志查看和分析
tail -f /var/log/file.log                # 实时查看日志
grep "ERROR" /var/log/file.log           # 搜索错误
awk '{print $1}' /var/log/access.log     # 提取字段
sort /var/log/file.log | uniq -c         # 统计重复行
sed 's/old/new/g' file.log               # 替换文本
```

### 性能分析命令

```bash
# 进程分析
ps aux --sort=-%cpu                      # 按 CPU 使用排序
ps aux --sort=-%mem                      # 按内存使用排序
pgrep -f process_name                    # 查找进程 PID
pkill -f process_name                    # 终止进程

# 系统调用跟踪
strace -p PID                            # 跟踪进程系统调用
ltrace -p PID                            # 跟踪库函数调用
```

---

**文档版本**: 1.0  
**最后更新**: 2024年8月24日  
**维护者**: Lawsker 技术团队