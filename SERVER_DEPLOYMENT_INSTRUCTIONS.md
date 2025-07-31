# Lawsker系统服务器部署说明

## 🚀 快速部署指南

### 服务器信息
- **IP地址**: 156.236.74.200
- **用户**: root
- **密码**: Pr971V3j
- **部署目录**: /root/lawsker
- **管理方式**: PM2 + 虚拟环境

### 1. 本地环境准备

确保本地安装了sshpass：

```bash
# macOS
brew install sshpass

# Ubuntu/Debian
sudo apt-get install sshpass

# CentOS/RHEL
sudo yum install sshpass
```

### 2. 一键部署

从本地执行部署：

```bash
# 完整部署（提交代码 + 部署到服务器）
./scripts/deploy-to-server.sh "feat: 初始部署"

# 或者使用专用服务器部署脚本
./scripts/server-deploy.sh deploy
```

### 3. 验证部署

```bash
# 检查服务状态
./scripts/deploy-to-server.sh status

# 查看服务日志
./scripts/deploy-to-server.sh logs

# 或者直接在服务器上检查
sshpass -p "Pr971V3j" ssh root@156.236.74.200 "pm2 status"
```

### 4. 访问应用

- **网站地址**: http://156.236.74.200
- **管理后台**: http://156.236.74.200/admin  
- **API文档**: http://156.236.74.200:8000/docs

## 📝 日常维护

### 代码更新

当您修复bug或添加新功能后：

```bash
# 方式1: 本地一键更新
./scripts/deploy-to-server.sh "fix: 修复某个问题"

# 方式2: 仅更新代码（不重启服务）
./scripts/deploy-to-server.sh update

# 方式3: 仅重启服务
./scripts/deploy-to-server.sh restart
```

### 服务管理

```bash
# 查看PM2服务状态
sshpass -p "Pr971V3j" ssh root@156.236.74.200 "pm2 status"

# 重启所有服务
sshpass -p "Pr971V3j" ssh root@156.236.74.200 "pm2 restart all"

# 查看服务日志
sshpass -p "Pr971V3j" ssh root@156.236.74.200 "pm2 logs --lines 50 --nostream"

# 查看特定服务日志
sshpass -p "Pr971V3j" ssh root@156.236.74.200 "pm2 logs lawsker-backend --lines 50 --nostream"
```

### 监控和调试

```bash
# 查看系统资源
sshpass -p "Pr971V3j" ssh root@156.236.74.200 "free -h && df -h"

# 查看网络连接
sshpass -p "Pr971V3j" ssh root@156.236.74.200 "netstat -tlnp | grep :8000"

# 测试API健康状态
sshpass -p "Pr971V3j" ssh root@156.236.74.200 "curl -f http://localhost:8000/health"
```

## 🔧 配置说明

### 修改部署脚本配置

如果需要修改服务器IP等配置，编辑：

```bash
vim scripts/commit-and-deploy.sh
```

修改以下变量：
```bash
REMOTE_SERVER="your-server-ip"      # 您的服务器IP
REMOTE_USER="root"                  # SSH用户名
DEPLOY_DIR="/root/lawsker"          # 部署目录
```

### SSL证书配置

```bash
# 安装Let's Encrypt证书
yum install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.com

# 自动续期
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

## 🚨 故障排除

### 常见问题

1. **服务启动失败**
```bash
# 检查日志
journalctl -u lawsker-backend -n 50
# 检查端口占用
netstat -tlnp | grep :8000
```

2. **前端无法访问**
```bash
# 检查Nginx配置
nginx -t
# 重启Nginx
systemctl restart nginx
```

3. **数据库连接失败**
```bash
# 检查数据库服务
systemctl status postgresql
# 测试连接
psql -h localhost -U username -d lawsker
```

### 获取帮助

如果遇到问题，可以：
1. 查看日志文件：`/var/log/lawsker-*.log`
2. 检查服务状态：`./scripts/git-update.sh status`
3. 联系技术支持

## 📞 联系信息

- **项目地址**: https://github.com/ronalzhang/lawsker
- **技术文档**: 查看 `docs/` 目录
- **部署指南**: `docs/GIT_DEPLOYMENT_GUIDE.md`

---

**注意**: 首次部署可能需要10-20分钟，请耐心等待。部署完成后，系统会自动启动所有服务。