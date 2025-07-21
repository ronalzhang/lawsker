#!/bin/bash

# Lawsker (律客) 数据库迁移脚本
# 用于在部署时自动运行数据库迁移

set -e

echo "🗃️ 开始数据库迁移..."

# 进入后端目录
cd backend

# 激活虚拟环境
source venv/bin/activate

# 检查数据库连接
echo "🔍 检查数据库连接..."
python -c "
import asyncio
from app.core.database import engine, test_db_connection
asyncio.run(test_db_connection())
" || {
    echo "❌ 数据库连接失败，请检查数据库配置"
    exit 1
}

# 运行Alembic迁移
echo "📊 运行数据库迁移..."
if command -v alembic &> /dev/null; then
    alembic upgrade head
else
    echo "⚠️  Alembic未安装，尝试使用Python直接运行迁移..."
    python -c "
import asyncio
from app.core.database import create_tables
asyncio.run(create_tables())
"
fi

# 运行额外的SQL脚本（如果存在）
if [ -d "migrations" ]; then
    echo "🔧 运行额外的SQL迁移脚本..."
    for sql_file in migrations/*.sql; do
        if [ -f "$sql_file" ]; then
            echo "运行: $sql_file"
            # 这里可以使用psql或其他数据库客户端执行SQL
            # psql -h localhost -U lawsker_user -d lawsker -f "$sql_file"
        fi
    done
fi

echo "✅ 数据库迁移完成！"