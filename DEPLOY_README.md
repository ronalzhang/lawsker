# Lawsker (律思客) 部署指南

## 快速部署

1. **首次部署前先修复前端依赖**
   ```bash
   ./fix_frontend.sh
   ```

2. **日常代码部署**
   ```bash
   ./deploy.sh
   ```

## 配置说明

### 默认配置
- 服务器IP: 156.236.74.200
- 用户: root
- 应用目录: /root/lawsker
- 后端服务: lawsker-backend (端口8000)
- 前端服务: lawsker-frontend (端口6060)

### 自定义配置（可选）
```bash
# 复制配置文件模板
cp .env.deploy.example .env.deploy

# 编辑配置文件
nano .env.deploy
```

## 部署流程

1. **代码推送** - 推送到GitHub仓库
2. **服务器拉取** - 从GitHub拉取最新代码
3. **应用重启** - 重启前端和后端服务
4. **状态检查** - 检查服务状态和日志
5. **访问测试** - 测试网站和API访问

## 常用命令

### 手动重启服务
```bash
# 重启后端
pm2 restart lawsker-backend

# 重启前端
pm2 restart lawsker-frontend

# 重启所有服务
pm2 restart all
```

### 查看日志
```bash
# 查看后端日志
pm2 logs lawsker-backend

# 查看前端日志
pm2 logs lawsker-frontend

# 查看所有服务状态
pm2 status
```

## 服务地址

- **网站首页**: https://156.236.74.200/
- **管理后台**: https://156.236.74.200/admin-pro
- **API文档**: https://156.236.74.200/docs
- **健康检查**: https://156.236.74.200/api/v1/health

## 故障排除

### 前端服务启动失败
```bash
# 运行修复脚本
./fix_frontend.sh
```

### 后端服务问题
```bash
# 查看后端错误日志
pm2 logs lawsker-backend --err

# 重启后端服务
pm2 restart lawsker-backend
```

### 网络访问问题
```bash
# 检查NGINX状态
systemctl status nginx

# 重启NGINX
systemctl restart nginx
```