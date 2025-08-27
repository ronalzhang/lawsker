#!/bin/bash
# =============================================================================
# Lawsker 生产环境完整部署脚本 - lawsker.com
# 包括数据库迁移、后端部署、前端部署、SSL配置、监控设置
# =============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 配置变量
DOMAIN="lawsker.com"
APP_DIR="/var/www/lawsker"
BACKEND_DIR="/opt/lawsker/backend"
LOG_DIR="/var/log/lawsker"
BACKUP_DIR="/var/backups/lawsker"

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
    echo -e "${BLUE}🚀 Lawsker 生产环境部署 - lawsker.com${NC}"
    echo -e "${BLUE}📅 部署时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo
}

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" >> /tmp/deploy.log
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $1" >> /tmp/deploy.log
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $1" >> /tmp/deploy.log
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >> /tmp/deploy.log
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [STEP] $1" >> /tmp/deploy.log
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "请不要使用root用户运行此脚本"
        exit 1
    fi
}

# 检查系统要求
check_requirements() {
    log_step "检查系统要求"
    
    # 检查操作系统
    if [[ ! -f /etc/os-release ]]; then
        log_error "无法识别操作系统"
        exit 1
    fi
    
    . /etc/os-release
    log_info "操作系统: $NAME $VERSION"
    
    # 检查必要的命令
    local required_commands=("python3" "pip3" "node" "npm" "mysql" "redis-cli" "nginx" "git" "curl")
    for cmd in "${required_commands[@]}"; do
        if ! command -v $cmd &> /dev/null; then
            log_error "$cmd 未安装"
            exit 1
        fi
    done
    
    log_success "系统要求检查通过"
}

# 创建必要的目录
create_directories() {
    log_step "创建必要的目录"
    
    sudo mkdir -p $APP_DIR
    sudo mkdir -p $BACKEND_DIR
    sudo mkdir -p $LOG_DIR
    sudo mkdir -p $BACKUP_DIR
    sudo mkdir -p /etc/nginx/ssl
    
    # 设置权限
    sudo chown -R $USER:$USER $BACKEND_DIR
    sudo chown -R www-data:www-data $APP_DIR
    sudo chown -R $USER:$USER $LOG_DIR
    sudo chown -R $USER:$USER $BACKUP_DIR
    
    log_success "目录创建完成"
}

# 备份现有数据
backup_existing_data() {
    log_step "备份现有数据"
    
    local backup_timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/lawsker_backup_$backup_timestamp.sql"
    
    # 检查数据库是否存在
    if mysql -e "USE lawsker;" 2>/dev/null; then
        log_info "备份现有数据库..."
        mysqldump -u root -p lawsker > $backup_file
        if [[ $? -eq 0 ]]; then
            log_success "数据库备份完成: $backup_file"
        else
            log_warning "数据库备份失败，继续部署"
        fi
    else
        log_info "数据库不存在，跳过备份"
    fi
    
    # 备份现有前端文件
    if [[ -d $APP_DIR ]]; then
        log_info "备份现有前端文件..."
        sudo tar -czf $BACKUP_DIR/frontend_backup_$backup_timestamp.tar.gz -C $APP_DIR . 2>/dev/null || true
        log_success "前端文件备份完成"
    fi
}

# 停止现有服务
stop_services() {
    log_step "停止现有服务"
    
    sudo systemctl stop lawsker-backend || true
    sudo systemctl stop nginx || true
    
    log_success "服务停止完成"
}

# 部署后端代码
deploy_backend() {
    log_step "部署后端代码"
    
    # 复制后端代码
    log_info "复制后端代码到 $BACKEND_DIR"
    cp -r backend/* $BACKEND_DIR/
    
    # 进入后端目录
    cd $BACKEND_DIR
    
    # 创建虚拟环境
    log_info "创建Python虚拟环境"
    python3 -m venv venv
    source venv/bin/activate
    
    # 安装依赖
    log_info "安装Python依赖"
    pip install --upgrade pip
    pip install -r requirements-prod.txt
    
    # 复制环境配置
    log_info "配置环境变量"
    cp /home/$USER/lawsker/.env.production .env
    
    # 执行数据库迁移
    log_info "执行数据库迁移"
    python run_migration.py
    
    # 运行测试
    log_info "运行后端测试"
    python run_final_test_suite.py
    
    log_success "后端部署完成"
    cd - > /dev/null
}

# 部署前端代码
deploy_frontend() {
    log_step "部署前端代码"
    
    # 复制前端文件
    log_info "复制前端文件到 $APP_DIR"
    sudo cp -r frontend/* $APP_DIR/
    
    # 设置权限
    sudo chown -R www-data:www-data $APP_DIR
    sudo chmod -R 755 $APP_DIR
    
    # 优化静态文件
    log_info "优化静态文件"
    sudo find $APP_DIR -name "*.js" -exec gzip -k {} \;
    sudo find $APP_DIR -name "*.css" -exec gzip -k {} \;
    
    log_success "前端部署完成"
}

# 创建systemd服务
create_systemd_service() {
    log_step "创建systemd服务"
    
    sudo tee /etc/systemd/system/lawsker-backend.service > /dev/null <<EOF
[Unit]
Description=Lawsker Backend Service
After=network.target mysql.service redis.service
Wants=mysql.service redis.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$BACKEND_DIR
Environment=PATH=$BACKEND_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=$BACKEND_DIR/.env
ExecStart=$BACKEND_DIR/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=lawsker-backend

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$BACKEND_DIR $LOG_DIR

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable lawsker-backend
    
    log_success "systemd服务创建完成"
}

# 配置Nginx
configure_nginx() {
    log_step "配置Nginx"
    
    # 创建Nginx配置
    sudo tee /etc/nginx/sites-available/lawsker > /dev/null <<EOF
# Lawsker Nginx配置 - lawsker.com
upstream backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

# HTTP重定向到HTTPS
server {
    listen 80;
    server_name lawsker.com www.lawsker.com;
    return 301 https://lawsker.com\$request_uri;
}

# 主站点配置
server {
    listen 443 ssl http2;
    server_name lawsker.com www.lawsker.com;
    
    # SSL配置
    ssl_certificate /etc/nginx/ssl/lawsker.com.crt;
    ssl_certificate_key /etc/nginx/ssl/lawsker.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # 根目录
    root $APP_DIR;
    index index-modern.html index.html;
    
    # 日志配置
    access_log $LOG_DIR/nginx_access.log;
    error_log $LOG_DIR/nginx_error.log;
    
    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header Vary "Accept-Encoding";
        try_files \$uri \$uri.gz \$uri =404;
    }
    
    # API代理
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket支持
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # 前端路由
    location / {
        try_files \$uri \$uri/ /index-modern.html;
    }
    
    # 健康检查
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

    # 启用站点
    sudo ln -sf /etc/nginx/sites-available/lawsker /etc/nginx/sites-enabled/
    
    # 删除默认站点
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # 测试Nginx配置
    sudo nginx -t
    if [[ $? -ne 0 ]]; then
        log_error "Nginx配置测试失败"
        exit 1
    fi
    
    log_success "Nginx配置完成"
}

# 配置SSL证书
setup_ssl() {
    log_step "配置SSL证书"
    
    # 检查是否已有证书
    if [[ -f /etc/nginx/ssl/lawsker.com.crt && -f /etc/nginx/ssl/lawsker.com.key ]]; then
        log_info "SSL证书已存在，跳过配置"
        return 0
    fi
    
    # 使用Let's Encrypt获取证书
    if command -v certbot &> /dev/null; then
        log_info "使用Let's Encrypt获取SSL证书"
        sudo certbot certonly --nginx -d lawsker.com -d www.lawsker.com --non-interactive --agree-tos --email admin@lawsker.com
        
        # 复制证书到nginx目录
        sudo cp /etc/letsencrypt/live/lawsker.com/fullchain.pem /etc/nginx/ssl/lawsker.com.crt
        sudo cp /etc/letsencrypt/live/lawsker.com/privkey.pem /etc/nginx/ssl/lawsker.com.key
        
        # 设置自动续期
        echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
        
        log_success "SSL证书配置完成"
    else
        log_warning "Certbot未安装，请手动配置SSL证书"
        # 创建自签名证书用于测试
        sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout /etc/nginx/ssl/lawsker.com.key \
            -out /etc/nginx/ssl/lawsker.com.crt \
            -subj "/C=CN/ST=Beijing/L=Beijing/O=Lawsker/CN=lawsker.com"
        log_info "已创建自签名证书用于测试"
    fi
}

# 配置数据库
setup_database() {
    log_step "配置数据库"
    
    # 启动MySQL服务
    sudo systemctl start mysql
    sudo systemctl enable mysql
    
    # 创建数据库和用户（如果不存在）
    mysql -u root -e "CREATE DATABASE IF NOT EXISTS lawsker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || true
    mysql -u root -e "CREATE USER IF NOT EXISTS 'lawsker_user'@'localhost' IDENTIFIED BY 'lawsker_password';" 2>/dev/null || true
    mysql -u root -e "GRANT ALL PRIVILEGES ON lawsker.* TO 'lawsker_user'@'localhost';" 2>/dev/null || true
    mysql -u root -e "FLUSH PRIVILEGES;" 2>/dev/null || true
    
    log_success "数据库配置完成"
}

# 配置Redis
setup_redis() {
    log_step "配置Redis"
    
    # 启动Redis服务
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    
    # 测试Redis连接
    redis-cli ping > /dev/null
    if [[ $? -eq 0 ]]; then
        log_success "Redis配置完成"
    else
        log_error "Redis配置失败"
        exit 1
    fi
}

# 启动服务
start_services() {
    log_step "启动服务"
    
    # 启动后端服务
    sudo systemctl start lawsker-backend
    sleep 5
    
    # 检查后端服务状态
    if systemctl is-active --quiet lawsker-backend; then
        log_success "后端服务启动成功"
    else
        log_error "后端服务启动失败"
        sudo journalctl -u lawsker-backend --no-pager -n 20
        exit 1
    fi
    
    # 启动Nginx
    sudo systemctl start nginx
    sudo systemctl enable nginx
    
    # 检查Nginx状态
    if systemctl is-active --quiet nginx; then
        log_success "Nginx启动成功"
    else
        log_error "Nginx启动失败"
        sudo journalctl -u nginx --no-pager -n 20
        exit 1
    fi
}

# 配置监控
setup_monitoring() {
    log_step "配置监控"
    
    # 创建监控脚本
    sudo tee /usr/local/bin/lawsker-monitor.sh > /dev/null <<'EOF'
#!/bin/bash
LOG_FILE="/var/log/lawsker/monitor.log"

# 检查后端服务
if ! systemctl is-active --quiet lawsker-backend; then
    echo "$(date): Backend service is down, restarting..." >> $LOG_FILE
    systemctl restart lawsker-backend
fi

# 检查Nginx
if ! systemctl is-active --quiet nginx; then
    echo "$(date): Nginx is down, restarting..." >> $LOG_FILE
    systemctl restart nginx
fi

# 检查MySQL
if ! systemctl is-active --quiet mysql; then
    echo "$(date): MySQL is down, restarting..." >> $LOG_FILE
    systemctl restart mysql
fi

# 检查Redis
if ! systemctl is-active --quiet redis-server; then
    echo "$(date): Redis is down, restarting..." >> $LOG_FILE
    systemctl restart redis-server
fi

# 检查磁盘空间
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [[ $DISK_USAGE -gt 90 ]]; then
    echo "$(date): Disk usage is high: ${DISK_USAGE}%" >> $LOG_FILE
fi

# 检查内存使用
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.2f", $3*100/$2}')
if (( $(echo "$MEMORY_USAGE > 90" | bc -l) )); then
    echo "$(date): Memory usage is high: ${MEMORY_USAGE}%" >> $LOG_FILE
fi
EOF

    sudo chmod +x /usr/local/bin/lawsker-monitor.sh
    
    # 添加到crontab
    (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/lawsker-monitor.sh") | crontab -
    
    log_success "监控配置完成"
}

# 验证部署
verify_deployment() {
    log_step "验证部署"
    
    # 检查服务状态
    local services=("lawsker-backend" "nginx" "mysql" "redis-server")
    for service in "${services[@]}"; do
        if systemctl is-active --quiet $service; then
            log_success "$service 服务运行正常"
        else
            log_error "$service 服务未运行"
            return 1
        fi
    done
    
    # 检查端口
    local ports=("8000" "80" "443" "3306" "6379")
    for port in "${ports[@]}"; do
        if netstat -tuln | grep -q ":$port"; then
            log_success "端口 $port 正常监听"
        else
            log_warning "端口 $port 未监听"
        fi
    done
    
    # 测试API连接
    sleep 10  # 等待服务完全启动
    
    if curl -f -k https://lawsker.com/api/v1/health > /dev/null 2>&1; then
        log_success "API健康检查通过"
    elif curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        log_success "后端API健康检查通过"
    else
        log_warning "API健康检查失败，请检查后端服务"
    fi
    
    # 测试前端访问
    if curl -f -k https://lawsker.com > /dev/null 2>&1; then
        log_success "前端页面访问正常"
    elif curl -f http://lawsker.com > /dev/null 2>&1; then
        log_success "前端页面访问正常（HTTP）"
    else
        log_warning "前端页面访问失败"
    fi
    
    log_success "部署验证完成"
}

# 显示部署信息
show_deployment_info() {
    echo
    echo "=== Lawsker 部署完成 ==="
    echo
    echo "🌐 网站地址:"
    echo "  - 主站: https://lawsker.com"
    echo "  - 管理后台: https://lawsker.com/admin-dashboard-modern.html"
    echo "  - 律师工作台: https://lawsker.com/lawyer-workspace-modern.html"
    echo "  - 用户工作台: https://lawsker.com/index-modern.html"
    echo
    echo "🔧 API地址:"
    echo "  - API根路径: https://lawsker.com/api"
    echo "  - 健康检查: https://lawsker.com/api/v1/health"
    echo "  - WebSocket: wss://lawsker.com/ws"
    echo
    echo "📊 服务状态:"
    echo "  - 后端服务: $(systemctl is-active lawsker-backend)"
    echo "  - Nginx: $(systemctl is-active nginx)"
    echo "  - MySQL: $(systemctl is-active mysql)"
    echo "  - Redis: $(systemctl is-active redis-server)"
    echo
    echo "📁 重要路径:"
    echo "  - 前端文件: $APP_DIR"
    echo "  - 后端代码: $BACKEND_DIR"
    echo "  - 日志目录: $LOG_DIR"
    echo "  - 备份目录: $BACKUP_DIR"
    echo "  - SSL证书: /etc/nginx/ssl/"
    echo
    echo "🔧 管理命令:"
    echo "  - 重启后端: sudo systemctl restart lawsker-backend"
    echo "  - 查看后端日志: sudo journalctl -u lawsker-backend -f"
    echo "  - 重启Nginx: sudo systemctl restart nginx"
    echo "  - 查看Nginx日志: sudo tail -f $LOG_DIR/nginx_access.log"
    echo "  - 查看监控日志: tail -f $LOG_DIR/monitor.log"
    echo
    echo "📋 部署日志: /tmp/deploy.log"
    echo
    log_success "🎉 Lawsker系统已成功部署到 lawsker.com！"
}

# 错误处理
cleanup_on_error() {
    log_error "部署过程中发生错误，正在清理..."
    sudo systemctl stop lawsker-backend || true
    sudo systemctl stop nginx || true
    exit 1
}

# 主函数
main() {
    show_logo
    
    log_info "开始Lawsker生产环境部署..."
    
    # 设置错误处理
    trap cleanup_on_error ERR
    
    # 执行部署步骤
    check_root
    check_requirements
    create_directories
    backup_existing_data
    stop_services
    setup_database
    setup_redis
    deploy_backend
    deploy_frontend
    create_systemd_service
    configure_nginx
    setup_ssl
    start_services
    setup_monitoring
    verify_deployment
    show_deployment_info
    
    log_success "部署完成！"
}

# 执行主函数
main "$@"