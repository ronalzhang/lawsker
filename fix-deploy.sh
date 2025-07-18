#!/bin/bash

# 获取服务器信息
SERVER_IP="156.236.74.200"
SERVER_USER="root"
SERVER_PASS="abc123wascell"
APP_DIR="/root/lawsker"
BACKEND_APP_NAME="lawsker-backend"
FRONTEND_APP_NAME="lawsker-frontend"

echo "🔧 修复部署问题..."

# 1. 拉取最新代码
echo "📥 拉取最新修复代码..."
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "cd $APP_DIR && git pull origin main"

# 2. 安装前端依赖
echo "📦 安装前端依赖..."
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "cd $APP_DIR/frontend && npm install express --save"

# 3. 重启后端服务
echo "🔄 重启后端服务..."
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "pm2 restart $BACKEND_APP_NAME"

# 4. 重启前端服务
echo "🔄 重启前端服务..."
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "pm2 restart $FRONTEND_APP_NAME"

# 5. 检查服务状态
echo "✅ 检查服务状态..."
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "pm2 status"

# 6. 检查日志
echo "📋 检查最新日志..."
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "pm2 logs $BACKEND_APP_NAME --lines 3 --nostream"
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "pm2 logs $FRONTEND_APP_NAME --lines 3 --nostream"

echo "🎉 修复完成！"
echo "📍 网站地址: https://$SERVER_IP/"