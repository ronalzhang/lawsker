# Lawsker系统Git部署指南

## 概述

本指南详细说明如何使用Git方式部署和维护Lawsker系统，替代Docker部署方案。通过Git部署可以更好地控制代码版本，便于日常维护和bug修复。

## 部署架构

```
服务器目录结构:
/root/lawsker/                    # 主项目目录
├── backend/                      # 后端代码
│   ├── venv/                    # Python虚拟环境
│   ├── app/                     # 应用代码
│   ├── migrations/              # 数据库迁移文件
│   └── requirements-prod.txt    # 生产环境依赖
├── frontend-vue/                # 用户端前端
│   ├── dist/                    # 构建输出
│   └── src/                     # 源代码
├── frontend-admin/              # 管理后台前端
│   ├── dist/                    # 构建输出
│   └── src/                     # 源代码
├── nginx/                       # Nginx配置
├── scripts/                     # 部署脚本
└── docs/                        # 文档

/root/lawsker-backups/           # 备份目录
├── lawsker-backup-20240730-1200/
├── lawsker-backup-20240730-1300/
└── ...

/var/log/                        # 日志目录
├── lawsker-deploy.log           # 部署日志
├── lawsker-update.log           # 更新日志
└── nginx/                       # Nginx日志
```

## 系统要求

### 服务器配置
- **操作系统**: CentOS 7+ / Ubuntu 18.04+
- **内存**: 最低4GB，推荐8GB+
- **磁盘**: 最低50GB，推荐100GB+
- **CPU**: 最低2核，推荐4核+
- **网络**: 公网IP，开放80、443端口

### 软件依赖
- Git 2.0+
- Python 3.8+
- Node.js 18+
- Nginx 1.18+
- PostgreSQL 12+ (或其他数据库)
- Redis 6.0+

## 首次部署

### 1. 准备服务器环境

```bash
# 更新系统
yum update -y  # CentOS
# 或
apt update && apt upgrade -y  # Ubuntu

# 安装基础工具
yum install -y git curl wget vim  # CentOS
# 或
apt install -y git curl wget vim  # Ubuntu
```

### 2. 下载部署脚本

```bash
# 创建临时目录
mkdir -p /tmp/lawsker-deploy
cd /tmp/lawsker-deploy

# 下载部署脚本
curl -O https://raw.githubusercontent.com/ronalzhang/lawsker/main/scripts/git-deploy.sh
chmod +x git-deploy.sh
```

### 3. 执行首次部署

```bash
# 执行完整部署
./git-deploy.sh deploy

# 或者分步执行
./git-deploy.sh help  # 查看帮助信息
```

### 4. 配置环境变量

部署完成后，需要编辑环境配置文件：

```bash
cd /root/lawsker
vim .env
```

配置示例：
```env
# 数据库配置
DATABASE_URL=postgresql://username:password@localhost:5432/lawsker
REDIS_URL=redis://localhost:6379/0

# 安全配置
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key

# 邮件配置
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=your-email-password

# 第三方服务
OPENAI_API_KEY=your-openai-key
WECHAT_PAY_MERCHANT_ID=your-merchant-id
```

### 5. 初始化数据库

```bash
cd /root/lawsker/backend
source venv/bin/activate

# 创建数据库表
python -c "
from app.database import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
"

# 执行初始化数据
python scripts/init_data.py
```

### 6. 验证部署

```bash
# 检查服务状态
systemctl status lawsker-backend
systemctl status nginx

# 检查端口监听
netstat -tlnp | grep :8000  # 后端服务
netstat -tlnp | grep :80    # Nginx

# 访问健康检查接口
curl http://localhost:8000/health
curl http://localhost/
```

## 日常更新流程

### 1. 代码提交和推送

在开发环境完成代码修改后：

```bash
# 添加修改的文件
git add .

# 提交更改
git commit -m "fix: 修复用户登录问题"

# 推送到远程仓库
git push origin main
```

### 2. 服务器更新

```bash
# 进入项目目录
cd /root/lawsker

# 执行更新脚本
./scripts/git-update.sh update

# 或者使用其他更新选项
./scripts/git-update.sh quick    # 快速更新（仅拉取代码）
./scripts/git-update.sh force    # 强制更新（覆盖本地更改）
```

### 3. 更新类型说明

更新脚本会自动检测更改类型并执行相应操作：

| 更改类型 | 检测条件 | 执行操作 |
|---------|---------|---------|
| 后端代码 | `backend/app/` 文件变更 | 重启后端服务 |
| 后端依赖 | `requirements*.txt` 变更 | 重新安装依赖 + 重启服务 |
| 前端代码 | `frontend-*/src/` 文件变更 | 重新构建 + 重载Nginx |
| 数据库迁移 | `migrations/` 文件变更 | 执行数据库迁移 |
| Nginx配置 | `nginx/` 文件变更 | 重载Nginx配置 |

## 回滚操作

### 1. 自动回滚

如果更新过程中出现错误，脚本会自动回滚到上一个版本：

```bash
# 更新失败时会自动触发回滚
[ERROR] 部署失败，开始回滚...
[INFO] 已回滚到备份: lawsker-backup-20240730-1200
```

### 2. 手动回滚

```bash
# 查看可用备份
ls -la /root/lawsker-backups/

# 手动回滚到指定版本
cd /root/lawsker
git log --oneline -10  # 查看提交历史
git reset --hard <commit-hash>  # 回滚到指定提交

# 重启服务
systemctl restart lawsker-backend
systemctl restart lawsker-worker
```

### 3. 数据库回滚

```bash
# 查看数据库备份
ls -la /root/lawsker-backups/*.sql

# 恢复数据库（谨慎操作）
# psql -h localhost -U username -d lawsker < /root/lawsker-backups/backup-file.sql
```

## 监控和维护

### 1. 服务状态监控

```bash
# 检查所有服务状态
./scripts/git-update.sh status

# 查看服务日志
journalctl -u lawsker-backend -f
journalctl -u nginx -f

# 查看应用日志
tail -f /var/log/lawsker-deploy.log
tail -f /var/log/lawsker-update.log
```

### 2. 性能监控

```bash
# 系统资源使用
htop
df -h
free -h

# 数据库连接
# psql -h localhost -U username -d lawsker -c "SELECT count(*) FROM pg_stat_activity;"

# Redis状态
redis-cli info
```

### 3. 定期维护任务

创建定期维护脚本：

```bash
# 创建维护脚本
cat > /root/lawsker/scripts/maintenance.sh << 'EOF'
#!/bin/bash

# 清理日志文件（保留30天）
find /var/log -name "*.log" -mtime +30 -delete

# 清理旧备份（保留10个）
cd /root/lawsker-backups
ls -t | tail -n +11 | xargs -r rm -rf

# 数据库维护
# psql -h localhost -U username -d lawsker -c "VACUUM ANALYZE;"

# 重启服务（可选，根据需要）
# systemctl restart lawsker-backend
EOF

chmod +x /root/lawsker/scripts/maintenance.sh

# 添加到crontab
echo "0 2 * * 0 /root/lawsker/scripts/maintenance.sh" | crontab -
```

## 故障排除

### 1. 常见问题

#### 服务启动失败
```bash
# 检查服务状态
systemctl status lawsker-backend

# 查看详细日志
journalctl -u lawsker-backend -n 50

# 检查端口占用
netstat -tlnp | grep :8000

# 手动启动测试
cd /root/lawsker/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 前端页面无法访问
```bash
# 检查Nginx状态
systemctl status nginx

# 测试Nginx配置
nginx -t

# 检查前端文件
ls -la /root/lawsker/frontend-vue/dist/
ls -la /root/lawsker/frontend-admin/dist/

# 重新构建前端
cd /root/lawsker/frontend-vue
npm run build
```

#### 数据库连接失败
```bash
# 检查数据库服务
systemctl status postgresql

# 测试连接
# psql -h localhost -U username -d lawsker

# 检查配置文件
cat /root/lawsker/.env | grep DATABASE
```

### 2. 日志分析

```bash
# 应用错误日志
grep -i error /var/log/lawsker-*.log

# Nginx错误日志
tail -f /var/log/nginx/error.log

# 系统日志
journalctl -f
```

### 3. 性能问题

```bash
# 检查系统负载
uptime
iostat 1 5

# 检查内存使用
free -h
ps aux --sort=-%mem | head -10

# 检查磁盘使用
df -h
du -sh /root/lawsker/*
```

## 安全配置

### 1. 防火墙设置

```bash
# CentOS/RHEL
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=443/tcp
firewall-cmd --reload

# Ubuntu
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 2. SSL证书配置

```bash
# 使用Let's Encrypt
yum install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.com

# 自动续期
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

### 3. 访问控制

```bash
# 限制SSH访问
vim /etc/ssh/sshd_config
# 添加: PermitRootLogin no
# 添加: AllowUsers your-user

# 重启SSH服务
systemctl restart sshd
```

## 备份策略

### 1. 代码备份

代码通过Git仓库自动备份，每次更新前会创建本地备份：

```bash
# 查看备份
ls -la /root/lawsker-backups/

# 手动创建备份
cp -r /root/lawsker /root/lawsker-backups/manual-backup-$(date +%Y%m%d-%H%M%S)
```

### 2. 数据库备份

```bash
# 创建数据库备份脚本
cat > /root/lawsker/scripts/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/root/lawsker-backups"
DATE=$(date +%Y%m%d-%H%M%S)
# pg_dump -h localhost -U username lawsker > $BACKUP_DIR/lawsker-db-$DATE.sql
# gzip $BACKUP_DIR/lawsker-db-$DATE.sql
EOF

chmod +x /root/lawsker/scripts/backup-db.sh

# 添加到定时任务
echo "0 1 * * * /root/lawsker/scripts/backup-db.sh" | crontab -
```

### 3. 文件备份

```bash
# 备份上传文件和配置
tar -czf /root/lawsker-backups/files-backup-$(date +%Y%m%d).tar.gz \
    /root/lawsker/.env \
    /root/lawsker/uploads/ \
    /etc/nginx/nginx.conf
```

## 最佳实践

### 1. 开发流程

1. **功能开发**: 在开发分支进行功能开发
2. **代码审查**: 通过Pull Request进行代码审查
3. **测试验证**: 在测试环境验证功能
4. **合并主分支**: 审查通过后合并到main分支
5. **生产部署**: 使用更新脚本部署到生产环境

### 2. 版本管理

```bash
# 使用语义化版本号
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3

# 创建发布分支
git checkout -b release/v1.2.3
git push origin release/v1.2.3
```

### 3. 监控告警

```bash
# 设置服务监控
cat > /root/lawsker/scripts/health-check.sh << 'EOF'
#!/bin/bash
if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "Backend service is down!" | mail -s "Lawsker Alert" admin@example.com
    systemctl restart lawsker-backend
fi
EOF

# 添加到定时任务
echo "*/5 * * * * /root/lawsker/scripts/health-check.sh" | crontab -
```

### 4. 文档维护

- 及时更新部署文档
- 记录重要的配置变更
- 维护故障排除手册
- 定期审查和优化部署流程

通过遵循这个Git部署指南，可以实现Lawsker系统的稳定部署和高效维护，确保系统的可靠性和可维护性。