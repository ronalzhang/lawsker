#!/bin/bash
# =============================================================================
# Lawsker 服务器部署脚本 - 156.232.13.240
# 使用PostgreSQL数据库和PM2管理应用
# =============================================================================

set -e

# 服务器配置
SERVER_IP="156.232.13.240"
SERVER_PASSWORD="Pr971V3j"
SERVER_USER="root"
APP_DIR="/root/lawsker"
DOMAIN="lawsker.com"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# 显示Logo
show_logo() {
    echo -e "${PURPLE}"
    echo "██╗      █████╗ ██╗    ██╗███████╗██╗  ██╗███████╗██████╗ "
    echo "██║     ██╔══██╗██║    ██║██╔════╝██║ ██╔╝██╔════╝██╔══██╗"
    echo "██║     ███████║██║ █╗ ██║███████╗█████╔╝ █████╗  ██████╔╝"
    echo "██║     ██╔══██║██║███╗██║╚════██║██╔═██╗ ██╔══╝  ██╔══██╗"
    echo "███████╗██║  ██║╚███╔███╔╝███████║██║  ██╗███████╗██║  ██║"
    echo "╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝"
    echo -e "${NC}"
    echo -e "${BLUE}🚀 Lawsker 服务器部署 - $SERVER_IP${NC}"
    echo -e "${BLUE}📅 部署时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo
}

# 执行远程命令
run_remote() {
    local cmd="$1"
    log_info "执行远程命令: $cmd"
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "$cmd"
}

# 上传文件到服务器
upload_files() {
    local local_path="$1"
    local remote_path="$2"
    log_info "上传文件: $local_path -> $remote_path"
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r "$local_path" $SERVER_USER@$SERVER_IP:"$remote_path"
}

# 检查服务器连接
check_server_connection() {
    log_step "检查服务器连接"
    if run_remote "echo 'Server connection successful'"; then
        log_success "服务器连接正常"
    else
        log_error "无法连接到服务器"
        exit 1
    fi
}

# 检查服务器环境
check_server_environment() {
    log_step "检查服务器环境"
    
    # 检查操作系统
    run_remote "cat /etc/os-release | head -2"
    
    # 检查Python
    if run_remote "python3 --version"; then
        log_success "Python3 已安装"
    else
        log_error "Python3 未安装"
        exit 1
    fi
    
    # 检查Node.js
    if run_remote "node --version"; then
        log_success "Node.js 已安装"
    else
        log_error "Node.js 未安装"
        exit 1
    fi
    
    # 检查PM2
    if run_remote "pm2 --version"; then
        log_success "PM2 已安装"
    else
        log_warning "PM2 未安装，将自动安装"
        run_remote "npm install -g pm2"
    fi
    
    # 检查PostgreSQL
    if run_remote "psql --version"; then
        log_success "PostgreSQL 已安装"
    else
        log_error "PostgreSQL 未安装"
        exit 1
    fi
    
    # 检查Nginx
    if run_remote "nginx -v"; then
        log_success "Nginx 已安装"
    else
        log_warning "Nginx 未安装，将自动安装"
        run_remote "apt update && apt install -y nginx"
    fi
}

# 停止现有应用
stop_existing_apps() {
    log_step "停止现有应用"
    run_remote "pm2 stop all || true"
    run_remote "pm2 delete all || true"
    run_remote "systemctl stop nginx || true"
}

# 备份现有数据
backup_existing_data() {
    log_step "备份现有数据"
    local backup_timestamp=$(date +%Y%m%d_%H%M%S)
    
    # 备份数据库
    run_remote "pg_dump lawsker > /root/backup_lawsker_$backup_timestamp.sql 2>/dev/null || echo 'No existing database to backup'"
    
    # 备份应用文件
    run_remote "if [ -d '$APP_DIR' ]; then tar -czf /root/backup_app_$backup_timestamp.tar.gz -C $APP_DIR . 2>/dev/null || true; fi"
    
    log_success "数据备份完成"
}

# 创建应用目录
create_app_directory() {
    log_step "创建应用目录"
    run_remote "mkdir -p $APP_DIR"
    run_remote "mkdir -p $APP_DIR/backend"
    run_remote "mkdir -p $APP_DIR/frontend"
    run_remote "mkdir -p /var/log/lawsker"
    run_remote "mkdir -p /var/backups/lawsker"
}

# 上传应用代码
upload_application_code() {
    log_step "上传应用代码"
    
    # 创建临时打包文件
    log_info "打包应用代码..."
    tar -czf /tmp/lawsker_backend.tar.gz backend/
    tar -czf /tmp/lawsker_frontend.tar.gz frontend/
    
    # 上传后端代码
    upload_files "/tmp/lawsker_backend.tar.gz" "/root/"
    run_remote "cd $APP_DIR && tar -xzf /root/lawsker_backend.tar.gz"
    
    # 上传前端代码
    upload_files "/tmp/lawsker_frontend.tar.gz" "/root/"
    run_remote "cd $APP_DIR && tar -xzf /root/lawsker_frontend.tar.gz"
    
    # 上传配置文件
    upload_files ".env.production" "$APP_DIR/.env"
    
    # 清理临时文件
    rm -f /tmp/lawsker_backend.tar.gz /tmp/lawsker_frontend.tar.gz
    
    log_success "应用代码上传完成"
}

# 配置PostgreSQL数据库
setup_postgresql() {
    log_step "配置PostgreSQL数据库"
    
    # 创建数据库和用户
    run_remote "sudo -u postgres psql -c \"CREATE DATABASE lawsker;\" || echo 'Database may already exist'"
    run_remote "sudo -u postgres psql -c \"CREATE USER lawsker_user WITH PASSWORD 'lawsker_password';\" || echo 'User may already exist'"
    run_remote "sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE lawsker TO lawsker_user;\""
    run_remote "sudo -u postgres psql -c \"ALTER USER lawsker_user CREATEDB;\""
    
    log_success "PostgreSQL配置完成"
}

# 安装后端依赖
install_backend_dependencies() {
    log_step "安装后端依赖"
    
    # 创建虚拟环境
    run_remote "cd $APP_DIR/backend && python3 -m venv venv"
    
    # 安装依赖
    run_remote "cd $APP_DIR/backend && source venv/bin/activate && pip install --upgrade pip"
    run_remote "cd $APP_DIR/backend && source venv/bin/activate && pip install -r requirements-prod.txt"
    
    log_success "后端依赖安装完成"
}

# 执行数据库迁移
run_database_migration() {
    log_step "执行数据库迁移"
    
    # 更新环境变量为PostgreSQL
    run_remote "cd $APP_DIR && sed -i 's/mysql:/postgresql:/' .env"
    run_remote "cd $APP_DIR && echo 'DATABASE_URL=postgresql://lawsker_user:lawsker_password@localhost:5432/lawsker' >> .env"
    
    # 执行迁移
    run_remote "cd $APP_DIR/backend && source venv/bin/activate && python run_migration.py"
    
    log_success "数据库迁移完成"
}

# 配置PM2应用
configure_pm2_apps() {
    log_step "配置PM2应用"
    
    # 创建PM2配置文件
    run_remote "cat > $APP_DIR/ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: 'lawsker-backend',
      cwd: '$APP_DIR/backend',
      script: 'venv/bin/python',
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8000',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '$APP_DIR/backend'
      },
      error_file: '/var/log/lawsker/backend-error.log',
      out_file: '/var/log/lawsker/backend-out.log',
      log_file: '/var/log/lawsker/backend-combined.log',
      time: true
    }
  ]
};
EOF"
    
    log_success "PM2配置完成"
}

# 配置Nginx
configure_nginx() {
    log_step "配置Nginx"
    
    # 创建Nginx配置
    run_remote "cat > /etc/nginx/sites-available/lawsker << 'EOF'
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    root $APP_DIR/frontend;
    index index-modern.html index.html;
    
    # 日志配置
    access_log /var/log/lawsker/nginx_access.log;
    error_log /var/log/lawsker/nginx_error.log;
    
    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # WebSocket支持
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # 静态文件
    location / {
        try_files \$uri \$uri/ /index-modern.html;
    }
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control 'public, immutable';
        add_header Vary 'Accept-Encoding';
    }
    
    # 健康检查
    location /health {
        access_log off;
        return 200 'healthy\n';
        add_header Content-Type text/plain;
    }
}
EOF"
    
    # 启用站点
    run_remote "ln -sf /etc/nginx/sites-available/lawsker /etc/nginx/sites-enabled/"
    run_remote "rm -f /etc/nginx/sites-enabled/default"
    
    # 测试Nginx配置
    run_remote "nginx -t"
    
    log_success "Nginx配置完成"
}

# 启动应用服务
start_services() {
    log_step "启动应用服务"
    
    # 启动PostgreSQL
    run_remote "systemctl start postgresql"
    run_remote "systemctl enable postgresql"
    
    # 启动后端应用
    run_remote "cd $APP_DIR && pm2 start ecosystem.config.js"
    run_remote "pm2 save"
    run_remote "pm2 startup"
    
    # 启动Nginx
    run_remote "systemctl start nginx"
    run_remote "systemctl enable nginx"
    
    log_success "服务启动完成"
}

# 验证部署
verify_deployment() {
    log_step "验证部署"
    
    # 等待服务启动
    sleep 10
    
    # 检查PM2状态
    log_info "检查PM2应用状态:"
    run_remote "pm2 status --nostream"
    
    # 检查服务状态
    log_info "检查系统服务状态:"
    run_remote "systemctl is-active postgresql nginx"
    
    # 检查端口
    log_info "检查端口监听:"
    run_remote "netstat -tuln | grep -E ':80|:8000|:5432'"
    
    # 测试API
    log_info "测试API健康检查:"
    if run_remote "curl -f http://localhost:8000/api/v1/health"; then
        log_success "API健康检查通过"
    else
        log_warning "API健康检查失败"
    fi
    
    # 测试前端
    log_info "测试前端访问:"
    if run_remote "curl -f http://localhost/"; then
        log_success "前端访问正常"
    else
        log_warning "前端访问失败"
    fi
    
    log_success "部署验证完成"
}

# 显示部署信息
show_deployment_info() {
    echo
    echo "=== Lawsker 部署完成 ==="
    echo
    echo "🌐 服务器信息:"
    echo "  - IP地址: $SERVER_IP"
    echo "  - 应用目录: $APP_DIR"
    echo "  - 数据库: PostgreSQL"
    echo "  - 进程管理: PM2"
    echo
    echo "🌐 访问地址:"
    echo "  - 主站: http://$DOMAIN"
    echo "  - 管理后台: http://$DOMAIN/admin-dashboard-modern.html"
    echo "  - 律师工作台: http://$DOMAIN/lawyer-workspace-modern.html"
    echo "  - 用户工作台: http://$DOMAIN/index-modern.html"
    echo
    echo "🔧 API地址:"
    echo "  - API根路径: http://$DOMAIN/api"
    echo "  - 健康检查: http://$DOMAIN/api/v1/health"
    echo
    echo "🔧 管理命令:"
    echo "  - 查看应用状态: sshpass -p '$SERVER_PASSWORD' ssh $SERVER_USER@$SERVER_IP 'pm2 status --nostream'"
    echo "  - 重启后端: sshpass -p '$SERVER_PASSWORD' ssh $SERVER_USER@$SERVER_IP 'pm2 restart lawsker-backend'"
    echo "  - 查看日志: sshpass -p '$SERVER_PASSWORD' ssh $SERVER_USER@$SERVER_IP 'pm2 logs lawsker-backend --lines 50 --nostream'"
    echo "  - 重启Nginx: sshpass -p '$SERVER_PASSWORD' ssh $SERVER_USER@$SERVER_IP 'systemctl restart nginx'"
    echo
    echo "📁 重要路径:"
    echo "  - 应用目录: $APP_DIR"
    echo "  - 日志目录: /var/log/lawsker"
    echo "  - 备份目录: /var/backups/lawsker"
    echo
}

# 错误处理
handle_error() {
    local exit_code=$?
    log_error "部署过程中发生错误 (退出码: $exit_code)"
    
    # 尝试获取错误日志
    log_info "获取错误日志..."
    run_remote "pm2 logs --lines 20 --nostream || true"
    
    echo
    echo "❌ 部署失败！"
    echo "🔧 请检查服务器日志获取详细信息"
    
    exit $exit_code
}

# 主函数
main() {
    # 设置错误处理
    trap handle_error ERR
    
    # 显示欢迎信息
    show_logo
    
    # 确认部署
    echo "=== 部署确认信息 ==="
    echo "🌐 服务器IP: $SERVER_IP"
    echo "📁 应用目录: $APP_DIR"
    echo "🗄️ 数据库: PostgreSQL"
    echo "🔧 进程管理: PM2"
    echo
    
    read -p "确认开始部署? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "部署已取消"
        exit 0
    fi
    
    # 执行部署流程
    check_server_connection
    check_server_environment
    stop_existing_apps
    backup_existing_data
    create_app_directory
    upload_application_code
    setup_postgresql
    install_backend_dependencies
    run_database_migration
    configure_pm2_apps
    configure_nginx
    start_services
    verify_deployment
    show_deployment_info
    
    echo
    log_success "🎉 Lawsker系统部署完成！"
    echo -e "${GREEN}✅ 系统已成功部署到 http://$DOMAIN${NC}"
}

# 检查依赖
check_dependencies() {
    if ! command -v sshpass &> /dev/null; then
        log_error "sshpass 未安装，请先安装: brew install sshpass (macOS) 或 apt install sshpass (Ubuntu)"
        exit 1
    fi
}

# 执行主函数
check_dependencies
main "$@"