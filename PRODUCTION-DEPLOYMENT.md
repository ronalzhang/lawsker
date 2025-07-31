# Lawsker生产环境Git部署指南

本文档详细说明了Lawsker系统基于Git的生产环境部署流程和配置要求。

> **重要更新**: 系统已从Docker部署方案迁移到Git部署方案，提供更好的版本控制和维护体验。

## 📋 目录

- [系统要求](#系统要求)
- [部署前准备](#部署前准备)
- [配置文件说明](#配置文件说明)
- [部署流程](#部署流程)
- [SSL证书配置](#ssl证书配置)
- [监控和日志](#监控和日志)
- [备份和恢复](#备份和恢复)
- [故障排除](#故障排除)
- [维护指南](#维护指南)

## 🖥️ 系统要求

### 硬件要求
- **CPU**: 4核心以上
- **内存**: 8GB以上（推荐16GB）
- **存储**: 100GB以上SSD硬盘
- **网络**: 100Mbps以上带宽

### 软件要求
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.0+

### 网络要求
- 开放端口：80 (HTTP), 443 (HTTPS), 22 (SSH)
- 域名解析配置完成
- SSL证书准备就绪

## 🚀 部署前准备

### 1. 服务器配置

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要软件
sudo apt install -y curl wget git vim htop

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 重启以应用用户组变更
sudo reboot
```

### 2. 防火墙配置

```bash
# Ubuntu/Debian
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 3. 域名配置

确保以下域名正确解析到服务器IP：
- `lawsker.com` - 主站点
- `www.lawsker.com` - 主站点（www）
- `api.lawsker.com` - API服务
- `admin.lawsker.com` - 管理后台
- `monitor.lawsker.com` - 监控面板
- `logs.lawsker.com` - 日志查看

## ⚙️ 配置文件说明

### 环境变量配置

复制并编辑生产环境配置文件：

```bash
cp .env.production .env.local
vim .env.local
```

**重要配置项说明：**

```bash
# 数据库密码（必须修改）
DB_PASSWORD=your-strong-database-password

# JWT密钥（必须修改）
JWT_SECRET_KEY=your-jwt-secret-key-change-this
SECRET_KEY=your-super-secret-key-change-this

# CSRF密钥（必须修改）
CSRF_SECRET_KEY=your-csrf-secret-key

# 加密密钥（必须修改，32字符）
ENCRYPTION_KEY=your-32-character-encryption-key

# 邮件配置
SMTP_HOST=smtp.aliyun.com
SMTP_USERNAME=noreply@lawsker.com
SMTP_PASSWORD=your-smtp-password

# 支付配置
WECHAT_PAY_MCH_ID=your-wechat-mch-id
WECHAT_PAY_KEY=your-wechat-pay-key
ALIPAY_APP_ID=your-alipay-app-id
```

### NGINX配置

NGINX配置文件位于 `nginx/nginx.conf`，主要配置项：

- **SSL证书路径**: `/etc/nginx/ssl/`
- **限流配置**: API限流、登录限流
- **负载均衡**: 后端服务负载均衡
- **安全头**: 各种安全响应头设置

### 数据库配置

PostgreSQL优化配置已包含在Docker Compose文件中：

- **连接数**: 200
- **共享缓冲区**: 256MB
- **有效缓存**: 1GB
- **工作内存**: 4MB

## 🔧 部署流程

### 1. 克隆代码

```bash
git clone https://github.com/your-org/lawsker.git
cd lawsker
```

### 2. 配置环境

```bash
# 复制并编辑环境配置
cp .env.production .env.local
vim .env.local

# 设置脚本执行权限
chmod +x scripts/*.sh
```

### 3. 生成SSL证书

```bash
# 方式1: 生成自签名证书（测试用）
./scripts/setup-ssl.sh self-signed

# 方式2: 使用Let's Encrypt（推荐）
./scripts/setup-ssl.sh letsencrypt
```

### 4. 执行部署

```bash
# 执行完整部署
./scripts/deploy-production.sh deploy

# 或指定版本部署
./scripts/deploy-production.sh deploy v1.0.0
```

### 5. 验证部署

```bash
# 检查服务状态
docker-compose -f docker-compose.prod.yml ps

# 执行健康检查
./scripts/deploy-production.sh health

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

## 🔒 SSL证书配置

### Let's Encrypt证书

```bash
# 获取证书
./scripts/setup-ssl.sh letsencrypt

# 验证证书
./scripts/setup-ssl.sh verify

# 手动续期
./scripts/setup-ssl.sh renew
```

### 自定义证书

如果使用自定义SSL证书，请将证书文件放置在 `nginx/ssl/` 目录：

```
nginx/ssl/
├── lawsker.com.crt
├── lawsker.com.key
├── admin.lawsker.com.crt
├── admin.lawsker.com.key
├── api.lawsker.com.crt
├── api.lawsker.com.key
├── monitor.lawsker.com.crt
├── monitor.lawsker.com.key
├── logs.lawsker.com.crt
└── logs.lawsker.com.key
```

## 📊 监控和日志

### 访问监控面板

- **Grafana**: https://monitor.lawsker.com
  - 用户名: admin
  - 密码: 在 `.env.local` 中的 `GRAFANA_PASSWORD`

- **Prometheus**: https://monitor.lawsker.com/prometheus

- **Kibana**: https://logs.lawsker.com

### 系统监控

```bash
# 执行系统检查
./scripts/system-monitor.sh all

# 生成监控报告
./scripts/system-monitor.sh report

# 检查特定组件
./scripts/system-monitor.sh docker
./scripts/system-monitor.sh database
./scripts/system-monitor.sh api
```

### 日志查看

```bash
# 查看所有服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f nginx

# 查看应用日志
tail -f backend/logs/app.log
tail -f nginx/logs/access.log
```

## 💾 备份和恢复

### 自动备份

部署脚本会在每次部署前自动创建备份：

```bash
# 手动创建备份
./scripts/deploy-production.sh backup
```

### 恢复数据

```bash
# 从备份恢复
./scripts/deploy-production.sh rollback backups/20240130_120000
```

### 备份内容

- PostgreSQL数据库
- Redis数据
- 上传文件
- 配置文件

## 🔧 故障排除

### 常见问题

#### 1. 服务启动失败

```bash
# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看错误日志
docker-compose -f docker-compose.prod.yml logs service_name

# 重启服务
docker-compose -f docker-compose.prod.yml restart service_name
```

#### 2. 数据库连接失败

```bash
# 检查数据库状态
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U lawsker_user

# 查看数据库日志
docker-compose -f docker-compose.prod.yml logs postgres

# 重启数据库
docker-compose -f docker-compose.prod.yml restart postgres
```

#### 3. SSL证书问题

```bash
# 验证证书
./scripts/setup-ssl.sh verify

# 重新生成证书
./scripts/setup-ssl.sh letsencrypt

# 检查NGINX配置
docker-compose -f docker-compose.prod.yml exec nginx nginx -t
```

#### 4. 性能问题

```bash
# 检查系统资源
./scripts/system-monitor.sh resources

# 查看数据库性能
docker-compose -f docker-compose.prod.yml exec postgres psql -U lawsker_user -d lawsker_prod -c "SELECT * FROM pg_stat_activity;"

# 检查Redis状态
docker-compose -f docker-compose.prod.yml exec redis redis-cli info
```

### 紧急恢复

如果系统出现严重问题，可以快速回滚：

```bash
# 停止所有服务
docker-compose -f docker-compose.prod.yml down

# 从最新备份恢复
./scripts/deploy-production.sh rollback $(ls -t backups/ | head -1)
```

## 🛠️ 维护指南

### 定期维护任务

#### 每日任务
- 检查系统状态
- 查看错误日志
- 监控资源使用

```bash
# 添加到crontab
0 9 * * * /path/to/lawsker/scripts/system-monitor.sh all >> /path/to/lawsker/logs/daily-check.log 2>&1
```

#### 每周任务
- 清理旧日志
- 检查备份完整性
- 更新系统补丁

```bash
# 系统清理
./scripts/system-monitor.sh cleanup

# 检查备份
ls -la backups/
```

#### 每月任务
- 更新SSL证书
- 数据库优化
- 安全扫描

```bash
# SSL证书续期
./scripts/setup-ssl.sh renew

# 数据库维护
docker-compose -f docker-compose.prod.yml exec postgres psql -U lawsker_user -d lawsker_prod -c "VACUUM ANALYZE;"
```

### 版本更新

```bash
# 拉取最新代码
git pull origin main

# 部署新版本
./scripts/deploy-production.sh deploy v1.1.0
```

### 扩容指南

#### 水平扩容

修改 `docker-compose.prod.yml` 中的副本数：

```yaml
backend:
  # ...
  deploy:
    replicas: 3
```

#### 垂直扩容

调整容器资源限制：

```yaml
backend:
  # ...
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
```

## 📞 技术支持

如果遇到部署问题，请：

1. 查看本文档的故障排除部分
2. 检查系统日志和错误信息
3. 联系技术支持团队

**联系方式：**
- 邮箱: tech-support@lawsker.com
- 电话: 400-xxx-xxxx
- 在线支持: https://support.lawsker.com

---

**注意事项：**
- 生产环境部署前请务必在测试环境验证
- 定期备份数据，确保数据安全
- 监控系统状态，及时处理异常
- 保持系统和依赖的及时更新