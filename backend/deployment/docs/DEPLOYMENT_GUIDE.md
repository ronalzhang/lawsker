# Lawsker 系统部署指南

## 概述

本指南详细介绍了如何部署 Lawsker 系统，包括环境准备、依赖安装、配置设置和部署验证等完整流程。

## 目录

1. [系统要求](#系统要求)
2. [环境准备](#环境准备)
3. [快速部署](#快速部署)
4. [详细部署步骤](#详细部署步骤)
5. [配置说明](#配置说明)
6. [部署验证](#部署验证)
7. [故障排除](#故障排除)
8. [维护和更新](#维护和更新)

## 系统要求

### 硬件要求

- **CPU**: 最少 2 核，推荐 4 核或以上
- **内存**: 最少 4GB，推荐 8GB 或以上
- **存储**: 最少 50GB 可用空间，推荐 100GB 或以上
- **网络**: 稳定的互联网连接

### 软件要求

- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **Python**: 3.8 或以上版本
- **Node.js**: 16.0 或以上版本
- **PostgreSQL**: 12.0 或以上版本
- **Redis**: 6.0 或以上版本
- **Nginx**: 1.18 或以上版本

### 域名和SSL

- 已注册的域名（如 lawsker.com）
- DNS 解析指向服务器 IP
- 用于 SSL 证书申请的邮箱地址

## 环境准备

### 1. 系统更新

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

### 2. 安装基础软件

```bash
# Ubuntu/Debian
sudo apt install -y git curl wget vim htop

# CentOS/RHEL
sudo yum install -y git curl wget vim htop
```

### 3. 安装 Python 3.8+

```bash
# Ubuntu/Debian
sudo apt install -y python3 python3-pip python3-venv python3-dev

# CentOS/RHEL
sudo yum install -y python3 python3-pip python3-devel
```

### 4. 安装 Node.js

```bash
# 使用 NodeSource 仓库
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 或使用 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 18
nvm use 18
```

### 5. 安装 PostgreSQL

```bash
# Ubuntu/Debian
sudo apt install -y postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install -y postgresql-server postgresql-contrib
sudo postgresql-setup initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### 6. 安装 Redis

```bash
# Ubuntu/Debian
sudo apt install -y redis-server

# CentOS/RHEL
sudo yum install -y redis
sudo systemctl enable redis
sudo systemctl start redis
```

### 7. 安装 Nginx

```bash
# Ubuntu/Debian
sudo apt install -y nginx

# CentOS/RHEL
sudo yum install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

## 快速部署

如果您想快速部署系统，可以使用我们提供的自动化部署脚本：

```bash
# 1. 克隆项目
git clone https://github.com/your-org/lawsker.git
cd lawsker

# 2. 设置环境变量
cp .env.production.example .env.production
# 编辑 .env.production 文件，设置必要的配置

# 3. 运行自动化部署
sudo python3 backend/deployment/deployment_orchestrator.py

# 4. 验证部署
python3 backend/deployment/run_integration_tests.py e2e --environment production
```

## 详细部署步骤

### 步骤 1: 获取源代码

```bash
# 克隆项目仓库
git clone https://github.com/your-org/lawsker.git
cd lawsker

# 切换到生产分支（如果有）
git checkout production
```

### 步骤 2: 配置环境变量

```bash
# 复制环境配置文件
cp .env.production.example .env.production

# 编辑配置文件
vim .env.production
```

必要的环境变量配置：

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=lawsker_prod
DB_USER=lawsker_user
DB_PASSWORD=your_secure_password
POSTGRES_PASSWORD=your_postgres_password

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# 应用配置
SECRET_KEY=your_secret_key_here
DEBUG=false
ENVIRONMENT=production

# SSL 配置
SSL_EMAIL=admin@lawsker.com
SSL_STAGING=false

# 监控配置
GRAFANA_PASSWORD=your_grafana_password

# 邮件配置（可选）
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@lawsker.com
SMTP_PASSWORD=your_smtp_password
```

### 步骤 3: 创建部署配置

```bash
# 创建部署配置文件
cat > backend/deployment/production_config.json << EOF
{
  "project_root": "/opt/lawsker",
  "server_ip": "your_server_ip",
  "server_user": "root",
  "deploy_path": "/opt/lawsker",
  "domains": ["lawsker.com", "admin.lawsker.com"],
  "ssl_enabled": true,
  "monitoring_enabled": true,
  "backup_enabled": true,
  "parallel_execution": true,
  "max_workers": 3
}
EOF
```

### 步骤 4: 执行部署

```bash
# 使用部署编排器执行完整部署
cd backend/deployment
python3 deployment_orchestrator.py --config production_config.json

# 或者分步骤执行
python3 dependency_manager.py --install
python3 database_configurator.py --setup
python3 frontend_builder.py --build-all
python3 ssl_configurator.py --setup
python3 monitoring_configurator.py --setup
```

### 步骤 5: 配置系统服务

#### 配置后端服务

```bash
# 创建 systemd 服务文件
sudo tee /etc/systemd/system/lawsker-backend.service > /dev/null << EOF
[Unit]
Description=Lawsker Backend API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/lawsker
Environment=PATH=/opt/lawsker/backend/venv/bin
ExecStart=/opt/lawsker/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable lawsker-backend
sudo systemctl start lawsker-backend
```

#### 配置 Nginx

```bash
# 创建 Nginx 配置
sudo tee /etc/nginx/sites-available/lawsker.conf > /dev/null << EOF
server {
    listen 80;
    server_name lawsker.com www.lawsker.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name lawsker.com www.lawsker.com;

    ssl_certificate /etc/letsencrypt/live/lawsker.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lawsker.com/privkey.pem;
    
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 前端静态文件
    location / {
        root /var/www/lawsker/frontend;
        try_files \$uri \$uri/ /index.html;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # WebSocket 支持
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# 启用站点
sudo ln -sf /etc/nginx/sites-available/lawsker.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 步骤 6: 设置监控

```bash
# 启动 Prometheus
sudo systemctl start prometheus
sudo systemctl enable prometheus

# 启动 Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

# 配置防火墙（如果需要）
sudo ufw allow 9090  # Prometheus
sudo ufw allow 3000  # Grafana
```

## 配置说明

### 数据库配置

#### PostgreSQL 优化配置

编辑 `/etc/postgresql/12/main/postgresql.conf`：

```ini
# 内存配置
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# 连接配置
max_connections = 100
listen_addresses = 'localhost'

# 日志配置
log_statement = 'all'
log_duration = on
log_min_duration_statement = 1000

# 性能配置
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

#### 数据库用户和权限

```sql
-- 创建数据库用户
CREATE USER lawsker_user WITH PASSWORD 'your_secure_password';

-- 创建数据库
CREATE DATABASE lawsker_prod OWNER lawsker_user;

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE lawsker_prod TO lawsker_user;

-- 创建只读用户（用于监控）
CREATE USER lawsker_readonly WITH PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE lawsker_prod TO lawsker_readonly;
GRANT USAGE ON SCHEMA public TO lawsker_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO lawsker_readonly;
```

### Redis 配置

编辑 `/etc/redis/redis.conf`：

```ini
# 内存配置
maxmemory 512mb
maxmemory-policy allkeys-lru

# 持久化配置
save 900 1
save 300 10
save 60 10000

# 安全配置
requirepass your_redis_password
bind 127.0.0.1

# 日志配置
loglevel notice
logfile /var/log/redis/redis-server.log
```

### 应用配置

#### 后端配置文件

创建 `backend/app/config/production.py`：

```python
import os
from .base import BaseConfig

class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False
    
    # 数据库配置
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Redis 配置
    REDIS_URL = os.getenv('REDIS_URL')
    
    # 安全配置
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    
    # 邮件配置
    MAIL_SERVER = os.getenv('SMTP_HOST')
    MAIL_PORT = int(os.getenv('SMTP_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('SMTP_USER')
    MAIL_PASSWORD = os.getenv('SMTP_PASSWORD')
    
    # 文件上传配置
    UPLOAD_FOLDER = '/opt/lawsker/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = '/var/log/lawsker/app.log'
```

## 部署验证

### 自动化验证

```bash
# 运行完整的部署验证测试
python3 backend/deployment/run_integration_tests.py e2e --environment production

# 运行性能测试
python3 backend/deployment/run_integration_tests.py performance --environment production

# 生成测试报告
python3 backend/deployment/run_integration_tests.py summary --days 1
```

### 手动验证

#### 1. 检查服务状态

```bash
# 检查系统服务
sudo systemctl status lawsker-backend
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis

# 检查端口监听
sudo netstat -tlnp | grep -E ':(80|443|8000|5432|6379|9090|3000)'
```

#### 2. 检查应用健康

```bash
# 检查后端 API
curl -f http://localhost:8000/api/v1/health

# 检查前端页面
curl -f https://lawsker.com/

# 检查数据库连接
psql -h localhost -U lawsker_user -d lawsker_prod -c "SELECT version();"

# 检查 Redis 连接
redis-cli ping
```

#### 3. 检查 SSL 证书

```bash
# 检查证书有效性
openssl s_client -connect lawsker.com:443 -servername lawsker.com < /dev/null 2>/dev/null | openssl x509 -noout -dates

# 检查证书评级
curl -s "https://api.ssllabs.com/api/v3/analyze?host=lawsker.com" | jq '.endpoints[0].grade'
```

#### 4. 检查监控系统

```bash
# 检查 Prometheus 目标
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# 检查 Grafana 健康状态
curl -f http://localhost:3000/api/health
```

## 故障排除

### 常见问题和解决方案

#### 1. 数据库连接失败

**症状**: 应用无法连接到数据库

**解决方案**:
```bash
# 检查 PostgreSQL 服务状态
sudo systemctl status postgresql

# 检查数据库配置
sudo -u postgres psql -c "\l"

# 检查用户权限
sudo -u postgres psql -c "\du"

# 重启数据库服务
sudo systemctl restart postgresql
```

#### 2. SSL 证书申请失败

**症状**: Let's Encrypt 证书申请失败

**解决方案**:
```bash
# 检查域名解析
nslookup lawsker.com

# 检查防火墙设置
sudo ufw status

# 手动申请证书
sudo certbot certonly --nginx -d lawsker.com -d www.lawsker.com

# 检查证书文件
sudo ls -la /etc/letsencrypt/live/lawsker.com/
```

#### 3. 前端构建失败

**症状**: TypeScript 编译错误或构建失败

**解决方案**:
```bash
# 检查 Node.js 版本
node --version
npm --version

# 清理缓存
npm cache clean --force

# 重新安装依赖
rm -rf node_modules package-lock.json
npm install

# 手动构建
npm run build
```

#### 4. 性能问题

**症状**: 响应时间慢或资源使用率高

**解决方案**:
```bash
# 检查系统资源
htop
df -h
free -h

# 检查数据库性能
sudo -u postgres psql -d lawsker_prod -c "SELECT * FROM pg_stat_activity;"

# 优化数据库
sudo -u postgres psql -d lawsker_prod -c "VACUUM ANALYZE;"

# 检查应用日志
tail -f /var/log/lawsker/app.log
```

### 日志文件位置

- **应用日志**: `/var/log/lawsker/app.log`
- **Nginx 日志**: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`
- **PostgreSQL 日志**: `/var/log/postgresql/postgresql-12-main.log`
- **Redis 日志**: `/var/log/redis/redis-server.log`
- **系统日志**: `/var/log/syslog`

### 监控和告警

#### Prometheus 告警规则

创建 `/etc/prometheus/rules/lawsker.yml`：

```yaml
groups:
  - name: lawsker
    rules:
      - alert: HighResponseTime
        expr: http_request_duration_seconds{quantile="0.95"} > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          
      - alert: DatabaseConnectionError
        expr: up{job="postgresql"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failed"
          
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
```

## 维护和更新

### 定期维护任务

#### 每日任务

```bash
#!/bin/bash
# daily_maintenance.sh

# 检查磁盘空间
df -h | awk '$5 > 80 {print "Warning: " $1 " is " $5 " full"}'

# 检查服务状态
systemctl is-active --quiet lawsker-backend || echo "Backend service is down"
systemctl is-active --quiet nginx || echo "Nginx service is down"
systemctl is-active --quiet postgresql || echo "PostgreSQL service is down"

# 清理日志文件
find /var/log/lawsker -name "*.log" -mtime +30 -delete

# 数据库维护
sudo -u postgres psql -d lawsker_prod -c "VACUUM ANALYZE;"
```

#### 每周任务

```bash
#!/bin/bash
# weekly_maintenance.sh

# 更新系统包
apt update && apt list --upgradable

# 检查 SSL 证书有效期
certbot certificates

# 数据库备份
pg_dump -h localhost -U lawsker_user lawsker_prod | gzip > /backup/lawsker_$(date +%Y%m%d).sql.gz

# 清理旧备份
find /backup -name "lawsker_*.sql.gz" -mtime +30 -delete
```

### 应用更新流程

#### 1. 准备更新

```bash
# 创建备份
sudo systemctl stop lawsker-backend
pg_dump -h localhost -U lawsker_user lawsker_prod > /backup/pre_update_$(date +%Y%m%d_%H%M%S).sql

# 备份当前代码
cp -r /opt/lawsker /backup/lawsker_backup_$(date +%Y%m%d_%H%M%S)
```

#### 2. 执行更新

```bash
# 拉取最新代码
cd /opt/lawsker
git fetch origin
git checkout production
git pull origin production

# 更新依赖
source backend/venv/bin/activate
pip install -r backend/requirements-prod.txt

# 运行数据库迁移
alembic upgrade head

# 构建前端
cd frontend
npm install
npm run build
```

#### 3. 验证更新

```bash
# 启动服务
sudo systemctl start lawsker-backend

# 运行测试
python3 backend/deployment/run_integration_tests.py e2e --environment production

# 检查应用健康
curl -f https://lawsker.com/api/v1/health
```

### 回滚流程

如果更新出现问题，可以使用以下步骤回滚：

```bash
# 停止服务
sudo systemctl stop lawsker-backend

# 恢复代码
rm -rf /opt/lawsker
cp -r /backup/lawsker_backup_YYYYMMDD_HHMMSS /opt/lawsker

# 恢复数据库
psql -h localhost -U lawsker_user -d lawsker_prod < /backup/pre_update_YYYYMMDD_HHMMSS.sql

# 启动服务
sudo systemctl start lawsker-backend

# 验证回滚
curl -f https://lawsker.com/api/v1/health
```

## 安全最佳实践

### 1. 系统安全

```bash
# 配置防火墙
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# 禁用 root SSH 登录
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# 配置自动安全更新
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 2. 应用安全

```bash
# 设置文件权限
sudo chown -R www-data:www-data /opt/lawsker
sudo chmod -R 755 /opt/lawsker
sudo chmod -R 644 /opt/lawsker/frontend

# 保护敏感文件
sudo chmod 600 /opt/lawsker/.env.production
sudo chown root:root /opt/lawsker/.env.production
```

### 3. 数据库安全

```sql
-- 限制数据库连接
ALTER SYSTEM SET listen_addresses = 'localhost';

-- 设置连接限制
ALTER USER lawsker_user CONNECTION LIMIT 50;

-- 启用行级安全
ALTER TABLE sensitive_table ENABLE ROW LEVEL SECURITY;
```

## 性能优化

### 1. 数据库优化

```sql
-- 创建索引
CREATE INDEX CONCURRENTLY idx_cases_created_at ON cases(created_at);
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

-- 分析表统计信息
ANALYZE;

-- 查看慢查询
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

### 2. 应用优化

```python
# 配置连接池
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,
    'max_overflow': 30,
    'pool_timeout': 30,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}

# 启用缓存
CACHE_TYPE = 'redis'
CACHE_REDIS_URL = 'redis://localhost:6379/1'
CACHE_DEFAULT_TIMEOUT = 300
```

### 3. Nginx 优化

```nginx
# 启用 gzip 压缩
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

# 配置缓存
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# 配置连接池
upstream backend {
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}
```

## 总结

本指南涵盖了 Lawsker 系统部署的完整流程，从环境准备到生产运维。请根据您的具体环境和需求调整相关配置。

如果在部署过程中遇到问题，请参考故障排除部分或联系技术支持团队。

---

**文档版本**: 1.0  
**最后更新**: 2024年8月24日  
**维护者**: Lawsker 技术团队