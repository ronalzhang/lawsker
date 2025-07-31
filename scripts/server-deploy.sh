#!/bin/bash

# Lawsker系统服务器部署脚本 - 适配PM2环境
# 服务器: 156.236.74.200
# 使用PM2管理应用，每个应用运行在各自的虚拟环境中

set -e

# 服务器配置
SERVER_IP="156.236.74.200"
SERVER_USER="root"
SERVER_PASSWORD="Pr971V3j"
DEPLOY_DIR="/root/lawsker"
REPO_URL="https://github.com/ronalzhang/lawsker.git"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
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

# 检查服务器连接
check_server_connection() {
    log "检查服务器连接..."
    
    if ! command -v sshpass &> /dev/null; then
        error "sshpass未安装，正在安装..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install sshpass
        else
            sudo apt-get install -y sshpass || sudo yum install -y sshpass
        fi
    fi
    
    if remote_exec "echo 'SSH连接正常'"; then
        log "服务器连接成功"
    else
        error "无法连接到服务器 $SERVER_IP"
        exit 1
    fi
}

# 检查服务器环境
check_server_environment() {
    log "检查服务器环境..."
    
    # 检查Git
    if ! remote_exec "command -v git"; then
        log "安装Git..."
        remote_exec "yum install -y git || apt-get install -y git"
    fi
    
    # 检查Python3
    if ! remote_exec "command -v python3"; then
        log "安装Python3..."
        remote_exec "yum install -y python3 python3-pip || apt-get install -y python3 python3-pip"
    fi
    
    # 检查Node.js
    if ! remote_exec "command -v node"; then
        log "安装Node.js..."
        remote_exec "curl -fsSL https://rpm.nodesource.com/setup_18.x | bash - && yum install -y nodejs || (curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && apt-get install -y nodejs)"
    fi
    
    # 检查PM2
    if ! remote_exec "command -v pm2"; then
        log "安装PM2..."
        remote_exec "npm install -g pm2"
    fi
    
    # 检查Nginx
    if ! remote_exec "command -v nginx"; then
        log "安装Nginx..."
        remote_exec "yum install -y nginx || apt-get install -y nginx"
    fi
    
    log "服务器环境检查完成"
}

# 部署代码
deploy_code() {
    log "部署代码到服务器..."
    
    # 检查部署目录是否存在
    if remote_exec "[ -d '$DEPLOY_DIR' ]"; then
        log "更新现有代码..."
        remote_exec "cd $DEPLOY_DIR && git stash && git pull origin main && git stash pop || true"
    else
        log "首次克隆代码..."
        remote_exec "git clone $REPO_URL $DEPLOY_DIR"
    fi
    
    log "代码部署完成"
}

# 设置后端环境
setup_backend() {
    log "设置后端环境..."
    
    remote_exec "cd $DEPLOY_DIR/backend && {
        # 创建虚拟环境
        if [ ! -d 'venv' ]; then
            python3 -m venv venv
        fi
        
        # 激活虚拟环境并安装依赖
        source venv/bin/activate
        pip install -r requirements-prod.txt
        
        # 创建环境配置文件
        if [ ! -f '.env' ]; then
            cp ../.env.production .env
        fi
    }"
    
    log "后端环境设置完成"
}

# 构建前端
build_frontend() {
    log "构建前端项目..."
    
    # 构建用户端前端
    remote_exec "cd $DEPLOY_DIR/frontend-vue && {
        npm install
        npm run build
    }"
    
    # 构建管理后台前端
    remote_exec "cd $DEPLOY_DIR/frontend-admin && {
        npm install
        npm run build
    }"
    
    log "前端构建完成"
}

# 配置Nginx
configure_nginx() {
    log "配置Nginx..."
    
    # 备份原有配置
    remote_exec "[ -f '/etc/nginx/nginx.conf' ] && cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.\$(date +%Y%m%d) || true"
    
    # 复制新配置
    remote_exec "cp $DEPLOY_DIR/nginx/nginx.conf /etc/nginx/nginx.conf"
    
    # 测试配置
    remote_exec "nginx -t"
    
    log "Nginx配置完成"
}

# 创建PM2配置文件
create_pm2_config() {
    log "创建PM2配置文件..."
    
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
        NODE_ENV: 'production',
        PYTHONPATH: '$DEPLOY_DIR/backend'
      },
      error_file: '/var/log/pm2/lawsker-backend-error.log',
      out_file: '/var/log/pm2/lawsker-backend-out.log',
      log_file: '/var/log/pm2/lawsker-backend.log',
      time: true,
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    },
    {
      name: 'lawsker-worker',
      cwd: '$DEPLOY_DIR/backend',
      script: 'venv/bin/python',
      args: '-m celery -A app.celery worker --loglevel=info',
      interpreter: 'none',
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '$DEPLOY_DIR/backend'
      },
      error_file: '/var/log/pm2/lawsker-worker-error.log',
      out_file: '/var/log/pm2/lawsker-worker-out.log',
      log_file: '/var/log/pm2/lawsker-worker.log',
      time: true,
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '512M'
    }
  ]
};
EOF"
    
    log "PM2配置文件创建完成"
}

# 启动服务
start_services() {
    log "启动服务..."
    
    # 创建日志目录
    remote_exec "mkdir -p /var/log/pm2"
    
    # 停止现有服务
    remote_exec "cd $DEPLOY_DIR && pm2 delete all || true"
    
    # 启动新服务
    remote_exec "cd $DEPLOY_DIR && pm2 start ecosystem.config.js"
    
    # 保存PM2配置
    remote_exec "pm2 save"
    
    # 设置PM2开机自启
    remote_exec "pm2 startup || true"
    
    # 启动Nginx
    remote_exec "systemctl enable nginx && systemctl start nginx"
    
    log "服务启动完成"
}

# 健康检查
health_check() {
    log "执行健康检查..."
    
    sleep 10  # 等待服务启动
    
    # 检查PM2服务状态
    if remote_exec "pm2 status | grep -E '(lawsker-backend|lawsker-worker)' | grep -q online"; then
        log "PM2服务运行正常"
    else
        error "PM2服务状态异常"
        remote_exec "pm2 status"
        return 1
    fi
    
    # 检查后端API
    if remote_exec "curl -f http://localhost:8000/health"; then
        log "后端API健康检查通过"
    else
        error "后端API健康检查失败"
        remote_exec "pm2 logs lawsker-backend --lines 20 --nostream"
        return 1
    fi
    
    # 检查前端页面
    if remote_exec "curl -f http://localhost/"; then
        log "前端页面健康检查通过"
    else
        warning "前端页面可能存在问题"
        remote_exec "nginx -t && systemctl status nginx"
    fi
    
    log "健康检查完成"
}

# 显示服务状态
show_status() {
    log "显示服务状态..."
    
    echo "=== PM2服务状态 ==="
    remote_exec "pm2 status"
    
    echo ""
    echo "=== Nginx状态 ==="
    remote_exec "systemctl status nginx --no-pager -l"
    
    echo ""
    echo "=== 系统资源使用 ==="
    remote_exec "free -h && df -h $DEPLOY_DIR"
    
    echo ""
    echo "=== 最近日志 ==="
    remote_exec "pm2 logs --lines 10 --nostream"
}

# 主函数
main() {
    log "开始Lawsker系统服务器部署..."
    
    check_server_connection
    check_server_environment
    deploy_code
    setup_backend
    build_frontend
    configure_nginx
    create_pm2_config
    start_services
    
    if health_check; then
        log "部署成功完成！"
        log "访问地址: http://$SERVER_IP"
        show_status
    else
        error "部署完成但健康检查失败"
        show_status
        exit 1
    fi
}

# 更新函数
update_code() {
    log "更新代码..."
    
    check_server_connection
    deploy_code
    setup_backend
    build_frontend
    
    # 重启服务
    remote_exec "cd $DEPLOY_DIR && pm2 restart all"
    
    sleep 5
    health_check
    log "代码更新完成"
}

# 重启服务
restart_services() {
    log "重启服务..."
    
    check_server_connection
    remote_exec "cd $DEPLOY_DIR && pm2 restart all"
    remote_exec "systemctl reload nginx"
    
    sleep 5
    health_check
    log "服务重启完成"
}

# 查看日志
show_logs() {
    local service="${1:-all}"
    local lines="${2:-50}"
    
    log "查看服务日志..."
    
    if [ "$service" = "all" ]; then
        remote_exec "pm2 logs --lines $lines --nostream"
    else
        remote_exec "pm2 logs $service --lines $lines --nostream"
    fi
}

# 显示帮助信息
show_help() {
    echo "Lawsker系统服务器部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  deploy        执行完整部署（默认）"
    echo "  update        更新代码并重启服务"
    echo "  restart       重启所有服务"
    echo "  status        显示服务状态"
    echo "  logs [service] [lines]  查看日志"
    echo "  help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 deploy"
    echo "  $0 update"
    echo "  $0 logs lawsker-backend 100"
    echo ""
    echo "服务器信息:"
    echo "  IP: $SERVER_IP"
    echo "  用户: $SERVER_USER"
    echo "  部署目录: $DEPLOY_DIR"
    echo ""
}

# 根据参数执行相应操作
case "${1:-deploy}" in
    deploy)
        main
        ;;
    update)
        update_code
        ;;
    restart)
        restart_services
        ;;
    status)
        check_server_connection
        show_status
        ;;
    logs)
        check_server_connection
        show_logs "$2" "$3"
        ;;
    help)
        show_help
        ;;
    *)
        echo "未知选项: $1"
        show_help
        exit 1
        ;;
esac