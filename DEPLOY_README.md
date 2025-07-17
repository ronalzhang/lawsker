# Lawsker (律思客) 部署指南

## 快速部署

1. **配置部署参数**
   ```bash
   # 复制配置文件模板
   cp .env.deploy.example .env.deploy
   
   # 编辑配置文件
   nano .env.deploy
   ```

2. **运行部署脚本**
   ```bash
   ./deploy.sh
   ```

## 配置说明

### 必需配置
- `DEPLOY_SERVER_IP`: 服务器IP地址
- `DEPLOY_SERVER_USER`: 服务器用户名
- `DEPLOY_SERVER_PASS`: 服务器密码
- `DEPLOY_APP_DIR`: 应用部署目录

### 可选配置
- `DEPLOY_BACKEND_APP_NAME`: 后端PM2应用名称
- `DEPLOY_FRONTEND_APP_NAME`: 前端PM2应用名称

## 部署流程

1. **代码推送** - 推送到GitHub仓库
2. **服务器拉取** - 从GitHub拉取最新代码
3. **依赖安装** - 安装前端和后端依赖
4. **数据库迁移** - 自动运行数据库迁移
5. **应用重启** - 重启前端和后端服务
6. **状态检查** - 检查服务状态和日志
7. **访问测试** - 测试网站和API访问

## 手动操作

### 单独运行数据库迁移
```bash
./migrate.sh
```

### 手动重启服务
```bash
# 重启后端
pm2 restart lawsker-backend

# 重启前端
pm2 restart lawsker-frontend
```

### 查看日志
```bash
# 查看后端日志
pm2 logs lawsker-backend

# 查看前端日志
pm2 logs lawsker-frontend
```

## 服务地址

- **网站首页**: https://156.227.235.192/
- **管理后台**: https://156.227.235.192/admin-pro
- **API文档**: https://156.227.235.192/docs
- **健康检查**: https://156.227.235.192/api/v1/health

## 故障排除

### 常见问题

1. **服务器连接失败**
   - 检查服务器IP、用户名和密码
   - 确保sshpass已安装

2. **依赖安装失败**
   - 检查服务器网络连接
   - 手动登录服务器执行安装命令

3. **应用启动失败**
   - 检查PM2状态: `pm2 status`
   - 查看应用日志: `pm2 logs`

4. **数据库连接失败**
   - 检查数据库服务是否运行
   - 确认数据库配置正确

### 紧急恢复
```bash
# 登录服务器
ssh root@156.227.235.192

# 查看服务状态
pm2 status

# 重启所有服务
pm2 restart all

# 查看NGINX状态
systemctl status nginx
```