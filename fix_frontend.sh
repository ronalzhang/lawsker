#!/bin/bash

# 修复前端依赖问题的一次性脚本

set -e

echo "🔧 修复前端依赖问题..."

# 配置信息
SERVER_IP="${DEPLOY_SERVER_IP:-156.236.74.200}"
SERVER_USER="${DEPLOY_SERVER_USER:-root}"
SERVER_PASS="${DEPLOY_SERVER_PASS:-Pr971V3j}"
APP_DIR="${DEPLOY_APP_DIR:-/root/lawsker}"
FRONTEND_APP_NAME="${DEPLOY_FRONTEND_APP_NAME:-lawsker-frontend}"

# 检查服务器连接
echo "🔍 检查服务器连接..."
if ! sshpass -p "$SERVER_PASS" ssh -o ConnectTimeout=10 "$SERVER_USER@$SERVER_IP" "echo '✅ 服务器连接成功'"; then
    echo "❌ 服务器连接失败"
    exit 1
fi

# 停止前端服务
echo "⏹️  停止前端服务..."
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "cd $APP_DIR && pm2 stop $FRONTEND_APP_NAME 2>/dev/null || true"

# 安装前端依赖
echo "📦 安装前端依赖..."
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "cd $APP_DIR/frontend && npm install --production"

# 重启前端服务
echo "🔄 重启前端服务..."
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "cd $APP_DIR && pm2 start $FRONTEND_APP_NAME"

# 检查服务状态
echo "✅ 检查服务状态..."
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "pm2 status | grep $FRONTEND_APP_NAME"

# 显示日志
echo "📋 前端日志："
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "pm2 logs $FRONTEND_APP_NAME --lines 3 --nostream" 2>/dev/null || echo "⚠️  无法获取日志"

echo "🎉 前端依赖修复完成！"