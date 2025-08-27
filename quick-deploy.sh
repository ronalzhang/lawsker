#!/bin/bash

# Lawsker 一键部署脚本
# 适用于已有基础环境的快速部署

set -e

echo "🚀 开始部署Lawsker业务优化系统..."

# 1. 检查环境
echo "📋 检查部署环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL 未安装"
    exit 1
fi

echo "✅ 环境检查通过"

# 2. 创建数据库（如果不存在）
echo "🗄️ 配置数据库..."
DB_NAME="lawsker_prod"
DB_USER="lawsker_user"
DB_PASSWORD="lawsker_2025_prod"

# 创建数据库和用户
sudo -u postgres psql << EOF
SELECT 'CREATE DATABASE $DB_NAME' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\q
EOF

echo "✅ 数据库配置完成"

# 3. 执行数据库迁移
echo "📊 执行数据库迁移..."
export PGPASSWORD=$DB_PASSWORD
psql -h localhost -U $DB_USER -d $DB_NAME -f database-setup-complete.sql

echo "✅ 数据库迁移完成"

# 4. 安装Python依赖
echo "🐍 安装Python依赖..."
cd backend
if [[ ! -d "venv" ]]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-prod.txt

echo "✅ Python依赖安装完成"

# 5. 创建环境配置
echo "⚙️ 创建环境配置..."
cat > .env << EOF
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
REDIS_URL=redis://localhost:6379/0
APP_ENV=production
APP_DEBUG=false
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
EOF

echo "✅ 环境配置完成"

# 6. 运行测试
echo "🧪 运行系统测试..."
python run_final_test_suite.py

echo "✅ 系统测试通过"

# 7. 启动服务
echo "🚀 启动服务..."

# 启动后端服务（后台运行）
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!

echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"

# 8. 启动前端服务（如果需要）
cd ../frontend
if command -v python3 -m http.server &> /dev/null; then
    nohup python3 -m http.server 3000 > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "✅ 前端服务已启动 (PID: $FRONTEND_PID)"
fi

# 9. 验证部署
echo "🔍 验证部署状态..."
sleep 5

# 检查后端健康状态
if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "✅ 后端服务运行正常"
else
    echo "❌ 后端服务启动失败"
    exit 1
fi

# 10. 显示部署信息
echo ""
echo "🎉 Lawsker业务优化系统部署完成！"
echo ""
echo "=== 服务信息 ==="
echo "后端服务: http://localhost:8000"
echo "前端服务: http://localhost:3000"
echo "API文档: http://localhost:8000/docs"
echo ""
echo "=== 数据库信息 ==="
echo "数据库名: $DB_NAME"
echo "用户名: $DB_USER"
echo "密码: $DB_PASSWORD"
echo ""
echo "=== 管理命令 ==="
echo "查看后端日志: tail -f logs/backend.log"
echo "查看前端日志: tail -f logs/frontend.log"
echo "停止后端服务: kill $BACKEND_PID"
if [[ -n "$FRONTEND_PID" ]]; then
    echo "停止前端服务: kill $FRONTEND_PID"
fi
echo ""
echo "=== 访问地址 ==="
echo "管理后台: http://localhost:3000/admin-dashboard-modern.html"
echo "用户界面: http://localhost:3000/index-modern.html"
echo "律师工作台: http://localhost:3000/lawyer-workspace-modern.html"
echo "Credits管理: http://localhost:3000/credits-management-modern.html"
echo ""
echo "🎯 系统已就绪，可以开始使用！"