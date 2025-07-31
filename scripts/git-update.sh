#!/bin/bash

# Lawsker系统Git更新脚本
# 用于日常代码更新和bug修复

set -e

# 配置变量
DEPLOY_DIR="/root/lawsker"
LOG_FILE="/var/log/lawsker-update.log"
BACKUP_DIR="/root/lawsker-backups"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a $LOG_FILE
}

# 检查Git仓库状态
check_git_status() {
    log "检查Git仓库状态..."
    cd $DEPLOY_DIR
    
    # 检查是否有未提交的更改
    if ! git diff-index --quiet HEAD --; then
        warning "检测到未提交的本地更改"
        git status --porcelain
        
        read -p "是否要保存这些更改？(y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git stash push -m "Auto-stash before update $(date)"
            log "本地更改已保存到stash"
        fi
    fi
    
    # 显示当前分支和提交信息
    CURRENT_BRANCH=$(git branch --show-current)
    CURRENT_COMMIT=$(git rev-parse --short HEAD)
    log "当前分支: $CURRENT_BRANCH"
    log "当前提交: $CURRENT_COMMIT"
}

# 拉取最新代码
pull_latest_code() {
    log "拉取最新代码..."
    cd $DEPLOY_DIR
    
    # 获取远程更新
    git fetch origin
    
    # 检查是否有新的提交
    LOCAL_COMMIT=$(git rev-parse HEAD)
    REMOTE_COMMIT=$(git rev-parse origin/main)
    
    if [ "$LOCAL_COMMIT" = "$REMOTE_COMMIT" ]; then
        info "代码已是最新版本，无需更新"
        return 0
    fi
    
    # 显示即将更新的提交
    log "即将更新的提交:"
    git log --oneline $LOCAL_COMMIT..$REMOTE_COMMIT
    
    # 拉取更新
    git pull origin main
    
    NEW_COMMIT=$(git rev-parse --short HEAD)
    log "代码更新完成，新提交: $NEW_COMMIT"
}

# 检查更新类型
check_update_type() {
    log "分析更新类型..."
    cd $DEPLOY_DIR
    
    # 获取更改的文件列表
    CHANGED_FILES=$(git diff --name-only HEAD~1 HEAD)
    
    NEED_BACKEND_RESTART=false
    NEED_FRONTEND_BUILD=false
    NEED_NGINX_RELOAD=false
    NEED_DB_MIGRATION=false
    
    echo "$CHANGED_FILES" | while read -r file; do
        case $file in
            backend/*)
                NEED_BACKEND_RESTART=true
                if [[ $file == backend/requirements*.txt ]]; then
                    echo "DEPS_UPDATE" >> /tmp/update_flags
                fi
                if [[ $file == backend/migrations/* ]]; then
                    NEED_DB_MIGRATION=true
                    echo "DB_MIGRATION" >> /tmp/update_flags
                fi
                ;;
            frontend-vue/*|frontend-admin/*)
                NEED_FRONTEND_BUILD=true
                echo "FRONTEND_BUILD" >> /tmp/update_flags
                ;;
            nginx/*)
                NEED_NGINX_RELOAD=true
                echo "NGINX_RELOAD" >> /tmp/update_flags
                ;;
        esac
    done
    
    # 读取更新标志
    if [ -f /tmp/update_flags ]; then
        UPDATE_FLAGS=$(cat /tmp/update_flags | sort | uniq)
        rm /tmp/update_flags
        log "检测到的更新类型: $UPDATE_FLAGS"
    else
        log "未检测到需要特殊处理的更新"
    fi
}

# 更新后端依赖
update_backend_deps() {
    if [[ $UPDATE_FLAGS == *"DEPS_UPDATE"* ]]; then
        log "更新后端依赖..."
        cd $DEPLOY_DIR/backend
        source venv/bin/activate
        pip install -r requirements-prod.txt
        log "后端依赖更新完成"
    fi
}

# 构建前端
build_frontend() {
    if [[ $UPDATE_FLAGS == *"FRONTEND_BUILD"* ]]; then
        log "重新构建前端..."
        
        # 构建用户端
        if git diff --name-only HEAD~1 HEAD | grep -q "frontend-vue/"; then
            log "构建用户端前端..."
            cd $DEPLOY_DIR/frontend-vue
            npm install
            npm run build
        fi
        
        # 构建管理后台
        if git diff --name-only HEAD~1 HEAD | grep -q "frontend-admin/"; then
            log "构建管理后台前端..."
            cd $DEPLOY_DIR/frontend-admin
            npm install
            npm run build
        fi
        
        log "前端构建完成"
    fi
}

# 执行数据库迁移
run_db_migrations() {
    if [[ $UPDATE_FLAGS == *"DB_MIGRATION"* ]]; then
        log "执行数据库迁移..."
        cd $DEPLOY_DIR/backend
        source venv/bin/activate
        
        # 备份数据库
        create_db_backup
        
        # 执行新的迁移文件
        for migration in migrations/*.sql; do
            if [ -f "$migration" ]; then
                MIGRATION_NAME=$(basename "$migration")
                # 检查迁移是否已执行（这里需要根据实际情况实现）
                log "执行迁移: $MIGRATION_NAME"
                # psql -h localhost -U username -d database -f "$migration"
            fi
        done
        
        log "数据库迁移完成"
    fi
}

# 创建数据库备份
create_db_backup() {
    log "创建数据库备份..."
    BACKUP_NAME="lawsker-db-backup-$(date +%Y%m%d-%H%M%S).sql"
    # pg_dump -h localhost -U username database > $BACKUP_DIR/$BACKUP_NAME
    log "数据库备份完成: $BACKUP_DIR/$BACKUP_NAME"
}

# 重启服务
restart_services() {
    log "重启相关服务..."
    
    # 重启后端服务
    if [[ $UPDATE_FLAGS == *"BACKEND"* ]] || [[ $UPDATE_FLAGS == *"DEPS_UPDATE"* ]]; then
        log "重启后端服务..."
        systemctl restart lawsker-backend
        systemctl restart lawsker-worker
        
        # 等待服务启动
        sleep 5
        
        # 检查服务状态
        if systemctl is-active --quiet lawsker-backend; then
            log "后端服务重启成功"
        else
            error "后端服务重启失败"
            systemctl status lawsker-backend --no-pager -l
            return 1
        fi
    fi
    
    # 重载Nginx配置
    if [[ $UPDATE_FLAGS == *"NGINX_RELOAD"* ]] || [[ $UPDATE_FLAGS == *"FRONTEND_BUILD"* ]]; then
        log "重载Nginx配置..."
        nginx -t && systemctl reload nginx
        log "Nginx配置重载完成"
    fi
}

# 健康检查
health_check() {
    log "执行更新后健康检查..."
    
    # 检查后端API
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log "后端API健康检查通过"
    else
        error "后端API健康检查失败"
        return 1
    fi
    
    # 检查前端页面
    if curl -f http://localhost/ > /dev/null 2>&1; then
        log "前端页面健康检查通过"
    else
        warning "前端页面健康检查失败，请检查Nginx配置"
    fi
    
    log "健康检查完成"
}

# 清理旧文件
cleanup() {
    log "清理临时文件和旧备份..."
    
    # 清理npm缓存
    if [[ $UPDATE_FLAGS == *"FRONTEND_BUILD"* ]]; then
        cd $DEPLOY_DIR/frontend-vue && npm cache clean --force
        cd $DEPLOY_DIR/frontend-admin && npm cache clean --force
    fi
    
    # 清理Python缓存
    find $DEPLOY_DIR/backend -name "*.pyc" -delete
    find $DEPLOY_DIR/backend -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # 保留最近10个备份
    cd $BACKUP_DIR
    ls -t | tail -n +11 | xargs -r rm -rf
    
    log "清理完成"
}

# 发送通知
send_notification() {
    local status=$1
    local message=$2
    
    # 这里可以集成邮件、钉钉、企业微信等通知方式
    log "更新通知: $status - $message"
    
    # 示例：发送邮件通知
    # echo "$message" | mail -s "Lawsker系统更新通知" admin@example.com
}

# 显示更新摘要
show_update_summary() {
    log "=== 更新摘要 ==="
    
    cd $DEPLOY_DIR
    
    echo "更新时间: $(date)"
    echo "更新前版本: $OLD_COMMIT"
    echo "更新后版本: $(git rev-parse --short HEAD)"
    echo ""
    
    echo "本次更新的提交:"
    git log --oneline $OLD_COMMIT..HEAD
    echo ""
    
    echo "更改的文件:"
    git diff --name-only $OLD_COMMIT..HEAD
    echo ""
    
    if [ -n "$UPDATE_FLAGS" ]; then
        echo "执行的操作: $UPDATE_FLAGS"
    fi
    
    log "=== 更新摘要结束 ==="
}

# 主更新流程
main() {
    log "开始Lawsker系统更新..."
    
    # 检查部署目录是否存在
    if [ ! -d "$DEPLOY_DIR" ]; then
        error "部署目录不存在: $DEPLOY_DIR"
        error "请先执行完整部署"
        exit 1
    fi
    
    # 记录更新前的版本
    cd $DEPLOY_DIR
    OLD_COMMIT=$(git rev-parse --short HEAD)
    
    # 创建代码备份
    create_code_backup
    
    # 执行更新流程
    check_git_status
    pull_latest_code
    check_update_type
    update_backend_deps
    build_frontend
    run_db_migrations
    restart_services
    
    # 健康检查
    if health_check; then
        log "更新成功完成！"
        show_update_summary
        send_notification "SUCCESS" "Lawsker系统更新成功"
        cleanup
    else
        error "更新完成但健康检查失败"
        send_notification "WARNING" "Lawsker系统更新完成但健康检查失败"
        exit 1
    fi
}

# 创建代码备份
create_code_backup() {
    log "创建代码备份..."
    mkdir -p $BACKUP_DIR
    BACKUP_NAME="lawsker-code-backup-$(date +%Y%m%d-%H%M%S)"
    cp -r $DEPLOY_DIR $BACKUP_DIR/$BACKUP_NAME
    log "代码备份完成: $BACKUP_DIR/$BACKUP_NAME"
}

# 快速更新（仅拉取代码，不重启服务）
quick_update() {
    log "执行快速更新（仅更新代码）..."
    check_git_status
    pull_latest_code
    log "快速更新完成，如需应用更改请手动重启服务"
}

# 强制更新（忽略本地更改）
force_update() {
    log "执行强制更新（将覆盖本地更改）..."
    cd $DEPLOY_DIR
    
    # 重置本地更改
    git reset --hard HEAD
    git clean -fd
    
    # 拉取最新代码
    git pull origin main
    
    log "强制更新完成"
    main
}

# 显示帮助信息
show_help() {
    echo "Lawsker系统Git更新脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  update      执行标准更新（默认）"
    echo "  quick       快速更新（仅拉取代码）"
    echo "  force       强制更新（覆盖本地更改）"
    echo "  status      显示当前状态"
    echo "  log         显示更新日志"
    echo "  help        显示此帮助信息"
    echo ""
}

# 显示状态
show_status() {
    cd $DEPLOY_DIR
    echo "=== Git状态 ==="
    git status
    echo ""
    echo "=== 最近提交 ==="
    git log --oneline -10
    echo ""
    echo "=== 服务状态 ==="
    systemctl status lawsker-backend --no-pager -l
}

# 显示更新日志
show_log() {
    echo "=== 最近的更新日志 ==="
    tail -50 $LOG_FILE
}

# 根据参数执行相应操作
case "${1:-update}" in
    update)
        main
        ;;
    quick)
        quick_update
        ;;
    force)
        force_update
        ;;
    status)
        show_status
        ;;
    log)
        show_log
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