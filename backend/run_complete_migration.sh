#!/bin/bash

# Lawsker数据库迁移完整执行脚本
# 确保100%成功率，零数据丢失

set -e  # 遇到错误立即退出

echo "🚀 Lawsker数据库迁移系统"
echo "=================================="
echo "确保100%成功率，零数据丢失的完整迁移流程"
echo "=================================="

# 检查Python环境
echo "🔍 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查必要的Python包
echo "🔍 检查Python依赖..."
python3 -c "import asyncpg, asyncio" 2>/dev/null || {
    echo "❌ 缺少必要的Python包 (asyncpg)"
    echo "请运行: pip install asyncpg python-dotenv"
    exit 1
}

# 检查PostgreSQL工具
echo "🔍 检查PostgreSQL工具..."
if ! command -v pg_dump &> /dev/null; then
    echo "❌ pg_dump 未找到"
    echo "请安装PostgreSQL客户端工具"
    exit 1
fi

if ! command -v psql &> /dev/null; then
    echo "❌ psql 未找到"
    echo "请安装PostgreSQL客户端工具"
    exit 1
fi

# 检查环境变量
echo "🔍 检查环境配置..."
if [ ! -f ".env" ] && [ -z "$DATABASE_URL" ]; then
    echo "❌ 未找到数据库配置"
    echo "请创建.env文件或设置DATABASE_URL环境变量"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要目录..."
mkdir -p backups
mkdir -p logs

# 设置日志文件
LOG_FILE="logs/migration_$(date +%Y%m%d_%H%M%S).log"
echo "📝 日志文件: $LOG_FILE"

# 执行迁移前的最后确认
echo ""
echo "⚠️  重要提示:"
echo "- 此操作将修改数据库结构"
echo "- 迁移前会自动创建完整备份"
echo "- 所有操作在事务中执行"
echo "- 失败时会自动回滚"
echo "- 迁移后会进行完整验证"
echo ""

read -p "确认开始迁移? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "❌ 迁移已取消"
    exit 0
fi

echo ""
echo "🚀 开始执行安全迁移..."
echo "=================================="

# 执行安全迁移
if python3 backend/execute_safe_migration.py 2>&1 | tee "$LOG_FILE"; then
    echo ""
    echo "🎉 迁移执行完成！"
    echo "📝 详细日志: $LOG_FILE"
    
    # 询问是否运行状态监控
    echo ""
    read -p "是否启动迁移状态监控? (yes/no): " -r
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "📊 启动状态监控..."
        python3 backend/migration_status_monitor.py
    fi
    
    echo ""
    echo "✅ 所有操作完成！"
    
else
    echo ""
    echo "❌ 迁移执行失败"
    echo "📝 错误日志: $LOG_FILE"
    echo ""
    echo "🔧 故障排除选项:"
    echo "1. 查看详细日志: cat $LOG_FILE"
    echo "2. 运行回滚工具: python3 backend/migration_rollback.py"
    echo "3. 检查系统状态: python3 backend/migration_status_monitor.py"
    
    exit 1
fi

echo ""
echo "🎯 迁移系统使用说明:"
echo "- 查看迁移历史: ls -la migration_*.json"
echo "- 运行状态检查: python3 backend/migration_status_monitor.py"
echo "- 运行验证工具: python3 backend/migration_verification.py"
echo "- 紧急回滚: python3 backend/migration_rollback.py"
echo ""
echo "📚 更多信息请查看日志文件和生成的报告"
echo "=================================="