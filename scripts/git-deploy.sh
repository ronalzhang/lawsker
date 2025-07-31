#!/bin/bash

# Lawsker系统Git部署脚本
# 用于在服务器上部署和更新Lawsker系统

set -e

# 配置变量
REPO_URL="https://github.com/ronalzhang/lawsker.git"
DEPLOY_DIR="/root/lawsker"
BRANCH="main"
BACKUP_DIR="/root/lawsker-backups"
LOG_FILE="/var/log/lawsker-deploy.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a $LOG_FILE
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a $LOG_FILE
}

# 检查是否为root用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "请使用root用户运行此脚本"
        exit 1
    fi
}

# 检查系统依赖
check_dependencies() {
    log "检查系统依赖..."
    
    # 检查Git
    if ! command -v git &> /dev/null; then
        error "Git未安装，正在安装..."
        yum install -y git || apt-get install -y git
    fi
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        error "Node.js未安装，正在安装..."
        curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
        yum install -y nodejs || apt-get install -y nodejs
    fi
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        error "Python3未安装，正在安装..."
        yum install -y python3 python3-pip || apt-get install -y python3 python3-pip
    fi
    
    # 检查Nginx
    if ! command -v nginx &> /dev/null; then
        warning "Nginx未安装，正在安装..."
        yum install -y nginx || apt-get install -y nginx
    fi
    
    log "系统依赖检查完成"
}

# 创建备份
create_backup() {
    if [ -d "$DEPLOY_DIR" ]; then
        log "创建当前版本备份..."
        mkdir -p $BACKUP_DIR
        BACKUP_NAME="lawsker-backup-$(date +%Y%m%d-%H%M%S)"
        cp -r $DEPLOY_DIR $BACKUP_DIR/$BACKUP_NAME
        log "备份创建完成: $BACKUP_DIR/$BACKUP_NAME"
        
        # 保留最近5个备份
        cd $BACKUP_DIR
        ls -t | tail -n +6 | xargs -r rm -rf
    fi
}

# 克隆或更新代码
deploy_code() {
    log "开始部署代码..."
    
    if [ ! -d "$DEPLOY_DIR" ]; then
        log "首次部署，克隆代码库..."
        git clone $REPO_URL $DEPLOY_DIR
        cd $DEPLOY_DIR
        git checkout $BRANCH
    else
        log "更新现有代码..."
        cd $DEPLOY_DIR
        
        # 保存本地修改
        git stash
        
        # 拉取最新代码
        git fetch origin
        git checkout $BRANCH
        git pull origin $BRANCH
        
        # 恢复本地修改（如果有）
        git stash pop || true
    fi
    
    log "代码部署完成"
}

# 安装后端依赖
install_backend_deps() {
    log "安装后端依赖..."
    cd $DEPLOY_DIR/backend
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    # 激活虚拟环境并安装依赖
    source venv/bin/activate
    pip install -r requirements-prod.txt
    
    log "后端依赖安装完成"
}

# 构建前端
build_frontend() {
    log "构建前端项目..."
    
    # 构建用户端前端
    cd $DEPLOY_DIR/frontend-vue
    npm install
    npm run build
    
    # 构建管理后台前端
    cd $DEPLOY_DIR/frontend-admin
    npm install
    npm run build
    
    log "前端构建完成"
}

# 配置Nginx
configure_nginx() {
    log "配置Nginx..."
    
    # 备份原有配置
    if [ -f "/etc/nginx/nginx.conf" ]; then
        cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d)
    fi
    
    # 复制新配置
    cp $DEPLOY_DIR/nginx/nginx.conf /etc/nginx/nginx.conf
    
    # 创建站点配置目录
    mkdir -p /etc/nginx/sites-available
    mkdir -p /etc/nginx/sites-enabled
    
    # 测试配置
    nginx -t
    
    log "Nginx配置完成"
}

# 配置环境变量
setup_environment() {
    log "配置环境变量..."
    
    cd $DEPLOY_DIR
    
    # 复制生产环境配置
    if [ ! -f ".env" ]; then
        cp .env.production .env
        warning "请编辑 .env 文件配置数据库和其他服务连接信息"
    fi
    
    log "环境变量配置完成"
}

# 数据库迁移
run_migrations() {
    log "执行数据库迁移..."
    
    cd $DEPLOY_DIR/backend
    source venv/bin/activate
    
    # 运行数据库迁移脚本
    for migration in migrations/*.sql; do
        if [ -f "$migration" ]; then
            log "执行迁移: $migration"
            # 这里需要根据实际数据库配置执行SQL
            # psql -h localhost -U username -d database -f "$migration"
        fi
    done
    
    log "数据库迁移完成"
}

# 启动服务
start_services() {
    log "启动服务..."
    
    # 启动后端服务
    cd $DEPLOY_DIR/backend
    source venv/bin/activate
    
    # 使用systemd管理服务
    create_systemd_services
    
    # 启动服务
    systemctl daemon-reload
    systemctl enable lawsker-backend
    systemctl start lawsker-backend
    
    # 启动Nginx
    systemctl enable nginx
    systemctl start nginx
    
    log "服务启动完成"
}

# 创建systemd服务文件
create_systemd_services() {
    log "创建systemd服务文件..."
    
    # 后端服务
    cat > /etc/systemd/system/lawsker-backend.service << EOF
[Unit]
Description=Lawsker Backend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$DEPLOY_DIR/backend
Environment=PATH=$DEPLOY_DIR/backend/venv/bin
ExecStart=$DEPLOY_DIR/backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    # Celery Worker服务
    cat > /etc/systemd/system/lawsker-worker.service << EOF
[Unit]
Description=Lawsker Celery Worker
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$DEPLOY_DIR/backend
Environment=PATH=$DEPLOY_DIR/backend/venv/bin
ExecStart=$DEPLOY_DIR/backend/venv/bin/celery -A app.celery worker --loglevel=info
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    log "systemd服务文件创建完成"
}

# 健康检查
health_check() {
    log "执行健康检查..."
    
    # 检查后端服务
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log "后端服务运行正常"
    else
        error "后端服务健康检查失败"
        return 1
    fi
    
    # 检查Nginx
    if systemctl is-active --quiet nginx; then
        log "Nginx服务运行正常"
    else
        error "Nginx服务未运行"
        return 1
    fi
    
    log "健康检查通过"
}

# 回滚函数
rollback() {
    error "部署失败，开始回滚..."
    
    # 停止服务
    systemctl stop lawsker-backend || true
    systemctl stop lawsker-worker || true
    
    # 恢复最新备份
    LATEST_BACKUP=$(ls -t $BACKUP_DIR | head -n 1)
    if [ -n "$LATEST_BACKUP" ]; then
        rm -rf $DEPLOY_DIR
        cp -r $BACKUP_DIR/$LATEST_BACKUP $DEPLOY_DIR
        log "已回滚到备份: $LATEST_BACKUP"
        
        # 重启服务
        systemctl start lawsker-backend
        systemctl start lawsker-worker
    else
        error "没有找到可用的备份"
    fi
}

# 主函数
main() {
    log "开始Lawsker系统部署..."
    
    # 设置错误处理
    trap rollback ERR
    
    check_root
    check_dependencies
    create_backup
    deploy_code
    install_backend_deps
    build_frontend
    configure_nginx
    setup_environment
    run_migrations
    start_services
    
    # 健康检查
    sleep 10
    if health_check; then
        log "部署成功完成！"
        log "访问地址: http://your-domain.com"
        log "管理后台: http://your-domain.com/admin"
    else
        error "部署完成但健康检查失败"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo "Lawsker系统Git部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  deploy    执行完整部署"
    echo "  update    仅更新代码"
    echo "  rollback  回滚到上一个版本"
    echo "  status    检查服务状态"
    echo "  help      显示此帮助信息"
    echo ""
}

# 更新函数
update_only() {
    log "执行代码更新..."
    create_backup
    deploy_code
    install_backend_deps
    build_frontend
    
    # 重启服务
    systemctl restart lawsker-backend
    systemctl restart lawsker-worker
    systemctl reload nginx
    
    sleep 5
    health_check
    log "更新完成"
}

# 状态检查
check_status() {
    echo "=== Lawsker系统状态 ==="
    echo ""
    
    echo "后端服务状态:"
    systemctl status lawsker-backend --no-pager -l
    echo ""
    
    echo "Worker服务状态:"
    systemctl status lawsker-worker --no-pager -l
    echo ""
    
    echo "Nginx服务状态:"
    systemctl status nginx --no-pager -l
    echo ""
    
    echo "磁盘使用情况:"
    df -h $DEPLOY_DIR
    echo ""
    
    echo "最近的部署日志:"
    tail -20 $LOG_FILE
}

# 根据参数执行相应操作
case "${1:-deploy}" in
    deploy)
        main
        ;;
    update)
        update_only
        ;;
    rollback)
        rollback
        ;;
    status)
        check_status
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