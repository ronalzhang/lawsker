#!/bin/bash

# 部署哈希系统脚本
# 更新服务器代码并运行数据库迁移

echo "🚀 开始部署哈希系统..."

# 服务器信息
SERVER_IP="156.236.74.200"
SERVER_USER="root"
SERVER_PASS="Pr971V3j"
PROJECT_DIR="/root/lawsker"

# 1. 更新服务器代码
echo "📥 更新服务器代码..."
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /root/lawsker
git pull origin main
echo "✅ 代码更新完成"
EOF

# 2. 运行数据库迁移
echo "🗄️ 运行数据库迁移..."
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /root/lawsker

# 激活虚拟环境
source venv/bin/activate

# 运行数据库迁移
echo "执行数据库迁移..."
psql -U postgres -d lawsker -f backend/migrations/013_add_user_hash_field.sql

echo "✅ 数据库迁移完成"
EOF

# 3. 重启应用服务
echo "🔄 重启应用服务..."
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /root/lawsker

# 重启后端服务
pm2 restart lawsker-backend

# 重启前端服务
pm2 restart lawsker-frontend

echo "✅ 服务重启完成"
EOF

# 4. 检查服务状态
echo "📊 检查服务状态..."
sshpass -p "$SERVER_PASS" ssh "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /root/lawsker
pm2 status
echo "✅ 服务状态检查完成"
EOF

echo "🎉 哈希系统部署完成！"
echo ""
echo "📋 部署内容："
echo "✅ 10位哈希值个人化工作台系统"
echo "✅ 统一律师和用户访问逻辑"
echo "✅ 数据库user_hash字段添加"
echo "✅ 后端哈希生成API"
echo "✅ 前端哈希系统集成"
echo "✅ 通用工作台页面"
echo ""
echo "🌐 测试地址："
echo "https://lawsker.com/test-personalized"
echo ""
echo "📝 使用说明："
echo "1. 访问测试页面"
echo "2. 使用测试账号登录"
echo "3. 观察URL变化为 /workspace/{哈希值}"
echo "4. 验证工作台内容正确加载" 