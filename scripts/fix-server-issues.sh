#!/bin/bash

# 修复服务器部署问题的脚本

SERVER_IP="156.236.74.200"
SERVER_USER="root"
SERVER_PASSWORD="Pr971V3j"
DEPLOY_DIR="/root/lawsker"

# 执行远程命令
remote_exec() {
    local cmd="$1"
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "$cmd"
}

echo "🔧 修复服务器环境问题..."

# 1. 安装python3-venv
echo "安装python3-venv..."
remote_exec "apt update && apt install -y python3.10-venv python3-pip || yum install -y python3-venv python3-pip"

# 2. 重新创建Python虚拟环境
echo "重新创建Python虚拟环境..."
remote_exec "cd $DEPLOY_DIR/backend && {
    rm -rf venv
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements-prod.txt
}"

# 3. 创建简化的环境配置文件
echo "创建环境配置文件..."
remote_exec "cd $DEPLOY_DIR && cat > .env << 'EOF'
# 基础配置
APP_NAME=Lawsker
APP_ENV=production
DEBUG=false
HOST=0.0.0.0
PORT=8000

# 数据库配置（使用SQLite作为临时方案）
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/lawsker

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 安全配置
SECRET_KEY=lawsker-secret-key-change-in-production
JWT_SECRET_KEY=lawsker-jwt-secret-key
JWT_ALGORITHM=HS256

# 日志配置
LOG_LEVEL=INFO
EOF"

# 4. 创建简化的PM2配置
echo "创建PM2配置..."
remote_exec "cd $DEPLOY_DIR && cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: 'lawsker-backend',
      cwd: '$DEPLOY_DIR/backend',
      script: 'venv/bin/python',
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8000',
      interpreter: 'none',
      env: {
        PYTHONPATH: '$DEPLOY_DIR/backend'
      },
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '512M'
    }
  ]
};
EOF"

# 5. 启动服务
echo "启动Lawsker后端服务..."
remote_exec "cd $DEPLOY_DIR && {
    pm2 delete lawsker-backend || true
    pm2 start ecosystem.config.js
    pm2 save
}"

# 6. 等待服务启动并检查
echo "等待服务启动..."
sleep 10

echo "检查服务状态..."
remote_exec "pm2 status"

echo "检查后端健康状态..."
if remote_exec "curl -f http://localhost:8000/health"; then
    echo "✅ 后端服务启动成功！"
else
    echo "❌ 后端服务启动失败，查看日志："
    remote_exec "pm2 logs lawsker-backend --lines 20 --nostream"
fi

echo "🎉 修复完成！"