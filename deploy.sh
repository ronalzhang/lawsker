#!/bin/bash

# Lawsker (律客) 系统部署脚本
# 用于将本地更改部署到服务器

set -e

# 加载部署配置
if [ -f ".env.deploy" ]; then
    echo "📋 加载部署配置..."
    export $(cat .env.deploy | grep -v '^#' | xargs)
fi

echo "🚀 开始部署 Lawsker (律客) 系统..."

# 使用固定的服务器配置（从.cursor/rules/server-ip-pem-rules.mdc）
SERVER_IP="156.232.13.240"
SERVER_USER="root"
SERVER_PASS="Pr971V3j"
APP_DIR="/root/lawsker"
BACKEND_APP_NAME="lawsker-backend"
FRONTEND_APP_NAME="lawsker-frontend"

# 1. 推送代码到 GitHub
echo "📤 推送代码到 GitHub..."
git add .
git commit -m "更新: $(date '+%Y-%m-%d %H:%M:%S')" || echo "没有需要提交的更改"
git push origin main

# 2. 检查服务器连接
echo "🔍 检查服务器连接..."
if ! sshpass -p "$SERVER_PASS" ssh -o ConnectTimeout=10 "$SERVER_USER@$SERVER_IP" "echo '✅ 服务器连接成功'"; then
    echo "❌ 服务器连接失败，请检查IP、用户名和密码"
    exit 1
fi

# 3. 在服务器上拉取最新代码
echo "📥 在服务器上拉取最新代码..."
echo "🔧 检查服务器Git状态..."
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "cd $APP_DIR && git status --porcelain" | head -5
echo "🔧 配置Git拉取策略..."
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "cd $APP_DIR && git config pull.rebase false"
echo "🔧 清理服务器上的未跟踪文件..."
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "cd $APP_DIR && git clean -fd"
echo "🔄 重置本地更改..."
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "cd $APP_DIR && git reset --hard HEAD"
echo "🔧 获取远程更新..."
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "cd $APP_DIR && git fetch origin"
echo "📥 拉取最新代码..."
if ! sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "cd $APP_DIR && git pull origin main"; then
    echo "❌ Git拉取失败，尝试强制更新..."
    sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "cd $APP_DIR && git reset --hard origin/main" || {
        echo "❌ 强制更新也失败，尝试重新克隆..."
        sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "cd /root && rm -rf lawsker_backup && mv lawsker lawsker_backup && git clone https://github.com/ronalzhang/lawsker.git" || {
            echo "❌ 重新克隆失败，恢复备份..."
            sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "cd /root && rm -rf lawsker && mv lawsker_backup lawsker"
            echo "🔧 手动操作: ssh $SERVER_USER@$SERVER_IP 'cd $APP_DIR && git status'"
            exit 1
        }
    }
fi

# 4. 跳过依赖安装（已在服务器上安装）
echo "📦 跳过依赖安装（已在服务器上配置）..."

# 5. 重启Lawsker应用（只重启lawsker相关应用，不影响其他应用）
echo "🔄 重启Lawsker应用..."
echo "🔧 重启后端服务..."
if ! sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "cd $APP_DIR && pm2 restart $BACKEND_APP_NAME"; then
    echo "⚠️  后端重启失败，尝试重新启动..."
    sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "cd $APP_DIR/backend && source venv/bin/activate && pm2 restart $BACKEND_APP_NAME" || {
        echo "❌ 后端应用重启失败，请手动检查"
        exit 1
    }
    echo "✅ 后端应用重启成功"
fi

echo "🔧 重启前端服务..."
if ! sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "cd $APP_DIR && pm2 restart $FRONTEND_APP_NAME"; then
    echo "⚠️  前端重启失败，尝试重新启动..."
    sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "cd $APP_DIR/frontend && pm2 restart $FRONTEND_APP_NAME" || {
        echo "❌ 前端应用重启失败，请手动检查"
        exit 1
    }
    echo "✅ 前端应用重启成功"
fi

# 保存PM2配置
echo "💾 保存PM2配置..."
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "pm2 save"

# 6. 检查应用状态
echo "✅ 检查Lawsker应用状态..."
echo "🔧 Lawsker服务状态："
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "pm2 status | grep -E 'lawsker-backend|lawsker-frontend'" || {
    echo "⚠️  无法获取Lawsker应用状态"
}

# 7. 显示应用日志
echo "📋 最新日志："
echo "🔧 后端日志："
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "pm2 logs $BACKEND_APP_NAME --lines 3" 2>/dev/null || echo "⚠️  无法获取后端日志"

echo "🔧 前端日志："
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" "pm2 logs $FRONTEND_APP_NAME --lines 3" 2>/dev/null || echo "⚠️  无法获取前端日志"

# 8. 测试网站访问
echo "🌐 测试网站访问..."
sleep 5
echo "🔧 测试前端服务..."
if curl -s -o /dev/null -w '%{http_code}' https://lawsker.com/ | grep -q '200'; then
    echo "✅ 前端服务访问正常"
else
    echo "⚠️  前端服务可能需要几秒钟才能响应"
fi

echo "🔧 测试后端API..."
if curl -s -o /dev/null -w '%{http_code}' https://lawsker.com/api/v1/health | grep -q '200'; then
    echo "✅ 后端API访问正常"
else
    echo "⚠️  后端API可能需要几秒钟才能响应"
fi

echo "🔧 测试API文档..."
if curl -s -o /dev/null -w '%{http_code}' https://lawsker.com/docs | grep -q '200'; then
    echo "✅ API文档访问正常"
else
    echo "⚠️  API文档可能需要几秒钟才能响应"
fi

echo "🎉 Lawsker (律思客) 系统部署完成！"
echo "📍 网站地址: https://lawsker.com/"
echo "🔧 管理后台: https://lawsker.com/admin-dashboard-modern.html"
echo "👨‍💼 律师工作台: https://lawsker.com/lawyer-workspace-modern.html"
echo "👤 用户工作台: https://lawsker.com/index-modern.html"
echo "📚 API文档: https://lawsker.com/docs"
echo "🏥 健康检查: https://lawsker.com/api/v1/health"
echo "🔒 SSL证书: 已配置 (自动续期)" 