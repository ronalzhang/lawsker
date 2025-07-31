#!/bin/bash

# Lawsker系统代码提交和部署脚本
# 用于本地开发完成后提交代码并部署到服务器

set -e

# 配置变量
REMOTE_SERVER="your-server-ip"
REMOTE_USER="root"
DEPLOY_DIR="/root/lawsker"
LOCAL_BRANCH="main"
REMOTE_BRANCH="main"

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

# 检查Git状态
check_git_status() {
    log "检查Git仓库状态..."
    
    # 检查是否在Git仓库中
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        error "当前目录不是Git仓库"
        exit 1
    fi
    
    # 检查当前分支
    CURRENT_BRANCH=$(git branch --show-current)
    if [ "$CURRENT_BRANCH" != "$LOCAL_BRANCH" ]; then
        warning "当前分支是 $CURRENT_BRANCH，不是 $LOCAL_BRANCH"
        read -p "是否继续？(y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # 检查是否有未跟踪的文件
    if [ -n "$(git ls-files --others --exclude-standard)" ]; then
        warning "检测到未跟踪的文件:"
        git ls-files --others --exclude-standard
        read -p "是否添加这些文件？(y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git add .
        fi
    fi
    
    # 检查是否有未提交的更改
    if ! git diff-index --quiet HEAD --; then
        log "检测到未提交的更改:"
        git status --porcelain
    else
        info "没有未提交的更改"
        return 0
    fi
}

# 提交代码
commit_changes() {
    log "准备提交代码..."
    
    # 显示更改摘要
    echo "=== 更改摘要 ==="
    git diff --stat
    echo ""
    
    # 获取提交信息
    if [ -n "$1" ]; then
        COMMIT_MESSAGE="$1"
    else
        echo "请输入提交信息:"
        read -r COMMIT_MESSAGE
        
        if [ -z "$COMMIT_MESSAGE" ]; then
            error "提交信息不能为空"
            exit 1
        fi
    fi
    
    # 执行提交
    git add .
    git commit -m "$COMMIT_MESSAGE"
    
    log "代码提交完成: $COMMIT_MESSAGE"
}

# 推送到远程仓库
push_to_remote() {
    log "推送代码到远程仓库..."
    
    # 检查远程仓库状态
    git fetch origin
    
    # 检查是否需要合并
    LOCAL_COMMIT=$(git rev-parse HEAD)
    REMOTE_COMMIT=$(git rev-parse origin/$REMOTE_BRANCH)
    
    if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
        BEHIND_COUNT=$(git rev-list --count HEAD..origin/$REMOTE_BRANCH)
        AHEAD_COUNT=$(git rev-list --count origin/$REMOTE_BRANCH..HEAD)
        
        if [ "$BEHIND_COUNT" -gt 0 ]; then
            warning "本地分支落后远程 $BEHIND_COUNT 个提交"
            read -p "是否先拉取远程更新？(y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                git pull origin $REMOTE_BRANCH
            fi
        fi
        
        if [ "$AHEAD_COUNT" -gt 0 ]; then
            log "本地分支领先远程 $AHEAD_COUNT 个提交，准备推送"
        fi
    fi
    
    # 推送代码
    git push origin $LOCAL_BRANCH
    
    log "代码推送完成"
}

# 部署到服务器
deploy_to_server() {
    log "开始部署到服务器..."
    
    # 检查SSH连接
    if ! ssh -o ConnectTimeout=10 $REMOTE_USER@$REMOTE_SERVER "echo 'SSH连接正常'" > /dev/null 2>&1; then
        error "无法连接到服务器 $REMOTE_USER@$REMOTE_SERVER"
        error "请检查SSH配置和网络连接"
        exit 1
    fi
    
    # 在服务器上执行更新
    log "在服务器上执行更新..."
    ssh $REMOTE_USER@$REMOTE_SERVER << EOF
        set -e
        
        # 检查部署目录
        if [ ! -d "$DEPLOY_DIR" ]; then
            echo "部署目录不存在，执行首次部署..."
            curl -fsSL https://raw.githubusercontent.com/ronalzhang/lawsker/main/scripts/git-deploy.sh | bash -s deploy
        else
            echo "执行代码更新..."
            cd $DEPLOY_DIR
            ./scripts/git-update.sh update
        fi
EOF
    
    if [ $? -eq 0 ]; then
        log "服务器部署成功"
    else
        error "服务器部署失败"
        exit 1
    fi
}

# 验证部署
verify_deployment() {
    log "验证部署结果..."
    
    # 检查服务器健康状态
    if ssh $REMOTE_USER@$REMOTE_SERVER "curl -f http://localhost:8000/health" > /dev/null 2>&1; then
        log "后端服务运行正常"
    else
        error "后端服务健康检查失败"
        return 1
    fi
    
    if ssh $REMOTE_USER@$REMOTE_SERVER "curl -f http://localhost/" > /dev/null 2>&1; then
        log "前端服务运行正常"
    else
        warning "前端服务可能存在问题"
    fi
    
    # 获取部署信息
    DEPLOY_INFO=$(ssh $REMOTE_USER@$REMOTE_SERVER "cd $DEPLOY_DIR && git log --oneline -1")
    log "当前部署版本: $DEPLOY_INFO"
    
    log "部署验证完成"
}

# 发送部署通知
send_notification() {
    local status=$1
    local message=$2
    
    log "发送部署通知: $status"
    
    # 这里可以集成各种通知方式
    # 例如：钉钉、企业微信、邮件等
    
    # 示例：发送到钉钉群
    # curl -X POST "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN" \
    #      -H "Content-Type: application/json" \
    #      -d "{\"msgtype\": \"text\", \"text\": {\"content\": \"$message\"}}"
    
    info "通知已发送"
}

# 显示部署摘要
show_deployment_summary() {
    echo ""
    echo "=== 部署摘要 ==="
    echo "部署时间: $(date)"
    echo "本地分支: $CURRENT_BRANCH"
    echo "远程分支: $REMOTE_BRANCH"
    echo "服务器: $REMOTE_USER@$REMOTE_SERVER"
    echo "部署目录: $DEPLOY_DIR"
    
    if [ -n "$COMMIT_MESSAGE" ]; then
        echo "提交信息: $COMMIT_MESSAGE"
    fi
    
    echo "最新提交: $(git log --oneline -1)"
    echo "=== 部署摘要结束 ==="
    echo ""
}

# 主函数
main() {
    log "开始Lawsker系统提交和部署流程..."
    
    # 检查参数
    COMMIT_MESSAGE="$1"
    
    # 执行部署流程
    check_git_status
    
    # 如果有更改，则提交
    if ! git diff-index --quiet HEAD --; then
        commit_changes "$COMMIT_MESSAGE"
        push_to_remote
    else
        log "没有新的更改需要提交"
        # 仍然推送以确保远程是最新的
        push_to_remote
    fi
    
    # 部署到服务器
    deploy_to_server
    
    # 验证部署
    if verify_deployment; then
        log "部署成功完成！"
        show_deployment_summary
        send_notification "SUCCESS" "Lawsker系统部署成功"
    else
        error "部署验证失败"
        send_notification "FAILED" "Lawsker系统部署失败"
        exit 1
    fi
}

# 仅提交不部署
commit_only() {
    log "仅提交代码，不部署..."
    check_git_status
    
    if ! git diff-index --quiet HEAD --; then
        commit_changes "$1"
        push_to_remote
        log "代码提交完成"
    else
        log "没有新的更改需要提交"
    fi
}

# 仅部署不提交
deploy_only() {
    log "仅部署，不提交新代码..."
    deploy_to_server
    verify_deployment
    log "部署完成"
}

# 快速部署（跳过验证）
quick_deploy() {
    log "快速部署模式..."
    check_git_status
    
    if ! git diff-index --quiet HEAD --; then
        commit_changes "$1"
        push_to_remote
    fi
    
    deploy_to_server
    log "快速部署完成"
}

# 显示帮助信息
show_help() {
    echo "Lawsker系统提交和部署脚本"
    echo ""
    echo "用法: $0 [选项] [提交信息]"
    echo ""
    echo "选项:"
    echo "  deploy        完整的提交和部署流程（默认）"
    echo "  commit        仅提交代码，不部署"
    echo "  deploy-only   仅部署，不提交新代码"
    echo "  quick         快速部署（跳过验证）"
    echo "  status        显示当前状态"
    echo "  help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 \"fix: 修复用户登录问题\""
    echo "  $0 commit \"feat: 添加新功能\""
    echo "  $0 deploy-only"
    echo ""
    echo "配置:"
    echo "  服务器: $REMOTE_USER@$REMOTE_SERVER"
    echo "  部署目录: $DEPLOY_DIR"
    echo "  分支: $LOCAL_BRANCH -> $REMOTE_BRANCH"
    echo ""
}

# 显示状态
show_status() {
    echo "=== 本地Git状态 ==="
    git status
    echo ""
    
    echo "=== 远程服务器状态 ==="
    if ssh $REMOTE_USER@$REMOTE_SERVER "cd $DEPLOY_DIR && pwd && git log --oneline -5" 2>/dev/null; then
        echo ""
        echo "=== 服务状态 ==="
        ssh $REMOTE_USER@$REMOTE_SERVER "systemctl is-active lawsker-backend nginx" 2>/dev/null || echo "无法获取服务状态"
    else
        echo "无法连接到远程服务器或部署目录不存在"
    fi
}

# 配置检查
check_config() {
    log "检查配置..."
    
    if [ "$REMOTE_SERVER" = "your-server-ip" ]; then
        error "请先配置服务器IP地址"
        echo "编辑脚本文件，修改 REMOTE_SERVER 变量"
        exit 1
    fi
    
    # 检查SSH密钥
    if ! ssh-add -l > /dev/null 2>&1; then
        warning "SSH agent未运行或没有加载密钥"
        echo "请确保SSH密钥已配置并可以免密登录服务器"
    fi
}

# 根据参数执行相应操作
case "${1:-deploy}" in
    deploy)
        check_config
        main "$2"
        ;;
    commit)
        commit_only "$2"
        ;;
    deploy-only)
        check_config
        deploy_only
        ;;
    quick)
        check_config
        quick_deploy "$2"
        ;;
    status)
        show_status
        ;;
    help)
        show_help
        ;;
    *)
        # 如果第一个参数不是命令，则作为提交信息处理
        if [[ "$1" != -* ]]; then
            check_config
            main "$1"
        else
            echo "未知选项: $1"
            show_help
            exit 1
        fi
        ;;
esac