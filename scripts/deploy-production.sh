#!/bin/bash

# Lawsker生产环境部署脚本
# 使用方法: ./scripts/deploy-production.sh [version]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 检查必要的工具
check_requirements() {
    log_info "检查部署环境..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    if [ ! -f ".env.production" ]; then
        log_error "生产环境配置文件 .env.production 不存在"
        exit 1
    fi
    
    log_success "环境检查通过"
}

# 备份当前数据
backup_data() {
    log_info "备份当前数据..."
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 备份数据库
    if docker-compose -f docker-compose.prod.yml ps postgres | grep -q "Up"; then
        log_info "备份PostgreSQL数据库..."
        docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U lawsker_user lawsker_prod > "$BACKUP_DIR/database.sql"
        log_success "数据库备份完成: $BACKUP_DIR/database.sql"
    fi
    
    # 备份Redis数据
    if docker-compose -f docker-compose.prod.yml ps redis | grep -q "Up"; then
        log_info "备份Redis数据..."
        docker-compose -f docker-compose.prod.yml exec -T redis redis-cli BGSAVE
        docker cp $(docker-compose -f docker-compose.prod.yml ps -q redis):/data/dump.rdb "$BACKUP_DIR/redis.rdb"
        log_success "Redis备份完成: $BACKUP_DIR/redis.rdb"
    fi
    
    # 备份上传文件
    if [ -d "backend/uploads" ]; then
        log_info "备份上传文件..."
        tar -czf "$BACKUP_DIR/uploads.tar.gz" backend/uploads/
        log_success "上传文件备份完成: $BACKUP_DIR/uploads.tar.gz"
    fi
    
    log_success "数据备份完成，备份目录: $BACKUP_DIR"
}

# 构建镜像
build_images() {
    log_info "构建Docker镜像..."
    
    VERSION=${1:-latest}
    
    # 构建后端镜像
    log_info "构建后端镜像..."
    docker build -f backend/Dockerfile.prod -t lawsker/backend:$VERSION backend/
    
    # 构建用户端前端镜像
    log_info "构建用户端前端镜像..."
    docker build -f frontend-vue/Dockerfile.prod -t lawsker/frontend-user:$VERSION frontend-vue/
    
    # 构建管理后台镜像
    log_info "构建管理后台镜像..."
    docker build -f frontend-admin/Dockerfile.prod -t lawsker/frontend-admin:$VERSION frontend-admin/
    
    log_success "镜像构建完成"
}

# 更新配置文件
update_configs() {
    log_info "更新配置文件..."
    
    # 检查SSL证书
    if [ ! -d "nginx/ssl" ]; then
        log_warning "SSL证书目录不存在，创建自签名证书用于测试"
        mkdir -p nginx/ssl
        
        # 生成自签名证书（仅用于测试）
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/lawsker.com.key \
            -out nginx/ssl/lawsker.com.crt \
            -subj "/C=CN/ST=Beijing/L=Beijing/O=Lawsker/CN=lawsker.com"
        
        # 复制证书给其他域名
        cp nginx/ssl/lawsker.com.crt nginx/ssl/admin.lawsker.com.crt
        cp nginx/ssl/lawsker.com.key nginx/ssl/admin.lawsker.com.key
        cp nginx/ssl/lawsker.com.crt nginx/ssl/api.lawsker.com.crt
        cp nginx/ssl/lawsker.com.key nginx/ssl/api.lawsker.com.key
        cp nginx/ssl/lawsker.com.crt nginx/ssl/monitor.lawsker.com.crt
        cp nginx/ssl/lawsker.com.key nginx/ssl/monitor.lawsker.com.key
        cp nginx/ssl/lawsker.com.crt nginx/ssl/logs.lawsker.com.crt
        cp nginx/ssl/lawsker.com.key nginx/ssl/logs.lawsker.com.key
        
        log_warning "请在生产环境中使用正式的SSL证书"
    fi
    
    # 创建必要的目录
    mkdir -p nginx/logs
    mkdir -p backend/logs
    mkdir -p backend/uploads
    mkdir -p database/backups
    
    log_success "配置文件更新完成"
}

# 运行数据库迁移
run_migrations() {
    log_info "运行数据库迁移..."
    
    # 等待数据库启动
    log_info "等待数据库启动..."
    sleep 30
    
    # 运行迁移
    docker-compose -f docker-compose.prod.yml exec -T backend python -m alembic upgrade head
    
    log_success "数据库迁移完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 检查服务状态
    services=("nginx" "backend" "postgres" "redis" "prometheus" "grafana")
    
    for service in "${services[@]}"; do
        if docker-compose -f docker-compose.prod.yml ps "$service" | grep -q "Up"; then
            log_success "$service 服务运行正常"
        else
            log_error "$service 服务未正常运行"
            return 1
        fi
    done
    
    # 检查API健康状态
    log_info "检查API健康状态..."
    sleep 10
    
    if curl -f http://localhost/health > /dev/null 2>&1; then
        log_success "API健康检查通过"
    else
        log_error "API健康检查失败"
        return 1
    fi
    
    log_success "所有健康检查通过"
}

# 部署函数
deploy() {
    VERSION=${1:-latest}
    
    log_info "开始部署Lawsker生产环境 (版本: $VERSION)"
    
    # 检查环境
    check_requirements
    
    # 备份数据
    backup_data
    
    # 构建镜像
    build_images "$VERSION"
    
    # 更新配置
    update_configs
    
    # 停止旧服务
    log_info "停止旧服务..."
    docker-compose -f docker-compose.prod.yml down
    
    # 启动新服务
    log_info "启动新服务..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # 运行迁移
    run_migrations
    
    # 健康检查
    health_check
    
    log_success "部署完成！"
    log_info "访问地址:"
    log_info "  用户端: https://lawsker.com"
    log_info "  管理后台: https://admin.lawsker.com"
    log_info "  API文档: https://api.lawsker.com/docs"
    log_info "  监控面板: https://monitor.lawsker.com"
    log_info "  日志查看: https://logs.lawsker.com"
}

# 回滚函数
rollback() {
    BACKUP_DIR=$1
    
    if [ -z "$BACKUP_DIR" ]; then
        log_error "请指定备份目录"
        exit 1
    fi
    
    if [ ! -d "$BACKUP_DIR" ]; then
        log_error "备份目录不存在: $BACKUP_DIR"
        exit 1
    fi
    
    log_info "开始回滚到备份: $BACKUP_DIR"
    
    # 停止服务
    docker-compose -f docker-compose.prod.yml down
    
    # 恢复数据库
    if [ -f "$BACKUP_DIR/database.sql" ]; then
        log_info "恢复数据库..."
        docker-compose -f docker-compose.prod.yml up -d postgres
        sleep 30
        docker-compose -f docker-compose.prod.yml exec -T postgres psql -U lawsker_user -d lawsker_prod < "$BACKUP_DIR/database.sql"
    fi
    
    # 恢复Redis
    if [ -f "$BACKUP_DIR/redis.rdb" ]; then
        log_info "恢复Redis数据..."
        docker cp "$BACKUP_DIR/redis.rdb" $(docker-compose -f docker-compose.prod.yml ps -q redis):/data/dump.rdb
    fi
    
    # 恢复上传文件
    if [ -f "$BACKUP_DIR/uploads.tar.gz" ]; then
        log_info "恢复上传文件..."
        tar -xzf "$BACKUP_DIR/uploads.tar.gz"
    fi
    
    # 重启服务
    docker-compose -f docker-compose.prod.yml up -d
    
    log_success "回滚完成"
}

# 主函数
main() {
    case "${1:-deploy}" in
        "deploy")
            deploy "$2"
            ;;
        "rollback")
            rollback "$2"
            ;;
        "backup")
            backup_data
            ;;
        "health")
            health_check
            ;;
        *)
            echo "使用方法: $0 {deploy|rollback|backup|health} [参数]"
            echo "  deploy [version]     - 部署指定版本（默认latest）"
            echo "  rollback <backup_dir> - 回滚到指定备份"
            echo "  backup               - 仅备份数据"
            echo "  health               - 健康检查"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"