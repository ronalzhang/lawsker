#!/bin/bash

# Lawsker系统一键部署脚本
# 从本地提交代码并部署到服务器 156.236.74.200

set -e

# 服务器配置
SERVER_IP="156.236.74.200"
SERVER_USER="root"
SERVER_PASSWORD="Pr971V3j"
DEPLOY_DIR="/root/lawsker"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# 执行远程命令
remote_exec() {
    local cmd="$1"
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "$cmd"
}

# 检查本地Git状态
check_local_git() {
    log "检查本地Git状态..."
    
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        error "当前目录不是Git仓库"
        exit 1
    fi
    
    # 检查是否有未提交的更改
    if ! git diff-index --quiet HEAD --; then
        warning "检测到未提交的更改"
        git status --porcelain
        
        read -p "是否提交这些更改？(y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            local commit_msg="${1:-自动提交: $(date '+%Y-%m-%d %H:%M:%S')}"
            git add .
            git commit -m "$commit_msg"
            log "代码已提交: $commit_msg"
        else
            error "请先提交或暂存本地更改"
            exit 1
        fi
    fi
}

# 推送代码到GitHub
push_to_github() {
    log "推送代码到GitHub..."
    
    git push origin main
    
    log "代码推送完成"
}

# 在服务器上更新代码
update_server_code() {
    log "在服务器上更新代码..."
    
    # 检查服务器连接
    if ! command -v sshpass &> /dev/null; then
        error "sshpass未安装，请先安装: brew install sshpass"
        exit 1
    fi
    
    # 检查部署目录是否存在
    if remote_exec "[ -d '$DEPLOY_DIR' ]"; then
        log "更新现有代码..."
        remote_exec "cd $DEPLOY_DIR && git stash && git pull origin main && git stash pop || true"
    else
        log "首次克隆代码..."
        remote_exec "git clone https://github.com/ronalzhang/lawsker.git $DEPLOY_DIR"
    fi
    
    log "服务器代码更新完成"
}

# 重启服务器服务
restart_server_services() {
    log "重启服务器服务..."
    
    # 检查PM2是否安装
    if ! remote_exec "command -v pm2 > /dev/null"; then
        warning "PM2未安装，正在安装..."
        remote_exec "npm install -g pm2"
    fi
    
    # 进入项目目录并重启服务
    remote_exec "cd $DEPLOY_DIR && {
        # 如果是首次部署，需要先安装依赖
        if [ ! -d 'backend/venv' ]; then
            echo '首次部署，安装依赖...'
            cd backend
            python3 -m venv venv
            source venv/bin/activate
            pip install -r requirements-prod.txt
            cd ..
        fi
        
        # 构建前端（如果需要）
        if [ -d 'frontend-vue' ] && [ ! -d 'frontend-vue/dist' ]; then
            echo '构建前端...'
            cd frontend-vue && npm install && npm run build && cd ..
        fi
        
        if [ -d 'frontend-admin' ] && [ ! -d 'frontend-admin/dist' ]; then
            echo '构建管理后台...'
            cd frontend-admin && npm install && npm run build && cd ..
        fi
        
        # 重启PM2服务
        pm2 restart all || {
            echo '启动新的PM2服务...'
            # 创建PM2配置文件
            cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: 'lawsker-backend',
      cwd: '$DEPLOY_DIR/backend',
      script: 'venv/bin/python',
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8000',
      interpreter: 'none',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    }
  ]
};
EOF
            pm2 start ecosystem.config.js
            pm2 save
        }
    }"
    
    log "服务重启完成"
}

# 检查服务状态
check_server_status() {
    log "检查服务器状态..."
    
    echo "=== PM2服务状态 ==="
    remote_exec "pm2 status"
    
    echo ""
    echo "=== 服务健康检查 ==="
    
    # 等待服务启动
    sleep 5
    
    if remote_exec "curl -f http://localhost:8000/health" > /dev/null 2>&1; then
        log "✅ 后端服务运行正常"
    else
        error "❌ 后端服务健康检查失败"
        echo "查看错误日志:"
        remote_exec "pm2 logs lawsker-backend --lines 10 --nostream"
    fi
    
    if remote_exec "curl -f http://localhost/" > /dev/null 2>&1; then
        log "✅ 前端服务运行正常"
    else
        warning "⚠️  前端服务可能存在问题"
    fi
    
    echo ""
    echo "=== 访问地址 ==="
    echo "🌐 网站地址: http://$SERVER_IP"
    echo "🔧 管理后台: http://$SERVER_IP/admin"
    echo "📊 API文档: http://$SERVER_IP:8000/docs"
}

# 主函数
main() {
    local commit_message="$1"
    
    log "🚀 开始Lawsker系统部署流程..."
    
    # 1. 检查并提交本地代码
    check_local_git "$commit_message"
    
    # 2. 推送到GitHub
    push_to_github
    
    # 3. 在服务器上更新代码
    update_server_code
    
    # 4. 重启服务器服务
    restart_server_services
    
    # 5. 检查服务状态
    check_server_status
    
    log "🎉 部署完成！"
}

# 仅更新代码（不重启服务）
update_only() {
    log "仅更新服务器代码..."
    
    check_local_git "$1"
    push_to_github
    update_server_code
    
    log "代码更新完成，如需应用更改请运行: $0 restart"
}

# 仅重启服务
restart_only() {
    log "仅重启服务器服务..."
    
    restart_server_services
    check_server_status
    
    log "服务重启完成"
}

# 查看服务器状态
status_only() {
    log "查看服务器状态..."
    
    check_server_status
}

# 查看服务器日志
show_logs() {
    local service="${1:-all}"
    local lines="${2:-50}"
    
    log "查看服务器日志..."
    
    if [ "$service" = "all" ]; then
        remote_exec "pm2 logs --lines $lines --nostream"
    else
        remote_exec "pm2 logs $service --lines $lines --nostream"
    fi
}

# 显示帮助信息
show_help() {
    echo "🚀 Lawsker系统一键部署脚本"
    echo ""
    echo "用法: $0 [选项] [提交信息]"
    echo ""
    echo "选项:"
    echo "  deploy        完整部署流程（默认）"
    echo "  update        仅更新代码"
    echo "  restart       仅重启服务"
    echo "  status        查看服务状态"
    echo "  logs [service] [lines]  查看日志"
    echo "  help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 \"fix: 修复用户登录问题\""
    echo "  $0 deploy \"feat: 添加新功能\""
    echo "  $0 update"
    echo "  $0 restart"
    echo "  $0 logs lawsker-backend 100"
    echo ""
    echo "服务器信息:"
    echo "  🖥️  IP: $SERVER_IP"
    echo "  👤 用户: $SERVER_USER"
    echo "  📁 目录: $DEPLOY_DIR"
    echo ""
}

# 根据参数执行相应操作
case "${1:-deploy}" in
    deploy)
        main "$2"
        ;;
    update)
        update_only "$2"
        ;;
    restart)
        restart_only
        ;;
    status)
        status_only
        ;;
    logs)
        show_logs "$2" "$3"
        ;;
    help)
        show_help
        ;;
    *)
        # 如果第一个参数不是命令，则作为提交信息处理
        if [[ "$1" != -* ]]; then
            main "$1"
        else
            echo "未知选项: $1"
            show_help
            exit 1
        fi
        ;;
esac