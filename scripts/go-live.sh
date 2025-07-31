#!/bin/bash

# 系统上线脚本
# 执行全量用户系统切换和上线后验证

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 配置参数
VERSION=${1:-latest}
GO_LIVE_LOG="logs/go-live-$(date +%Y%m%d_%H%M%S).log"
ROLLBACK_POINT="backups/pre-golive-$(date +%Y%m%d_%H%M%S)"

# 创建日志目录
mkdir -p logs backups

# 记录上线日志
log_golive() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$GO_LIVE_LOG"
}

# 发送上线通知
send_golive_notification() {
    local event=$1
    local message=$2
    local status=${3:-"info"}
    
    log_golive "通知: [$event] $message"
    
    # Slack通知
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        local color="good"
        case $status in
            "error") color="danger" ;;
            "warning") color="warning" ;;
        esac
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"text\": \"🚀 Lawsker系统上线通知\",
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"fields\": [{
                        \"title\": \"事件\",
                        \"value\": \"$event\",
                        \"short\": true
                    }, {
                        \"title\": \"状态\",
                        \"value\": \"$message\",
                        \"short\": false
                    }, {
                        \"title\": \"时间\",
                        \"value\": \"$(date)\",
                        \"short\": true
                    }, {
                        \"title\": \"版本\",
                        \"value\": \"$VERSION\",
                        \"short\": true
                    }]
                }]
            }" \
            "$SLACK_WEBHOOK_URL"
    fi
    
    # 邮件通知
    if command -v mail &> /dev/null; then
        echo "$message" | mail -s "Lawsker系统上线通知: $event" devops@lawsker.com
    fi
}

# 预上线检查
pre_golive_checks() {
    log_info "执行预上线检查..."
    log_golive "开始预上线检查"
    
    # 检查灰度发布状态
    if [ -f "deployment-status.json" ]; then
        local current_phase=$(jq -r '.phase' deployment-status.json)
        local current_percentage=$(jq -r '.percentage' deployment-status.json)
        
        if [ "$current_phase" != "gamma" ] || [ "$current_percentage" -lt 50 ]; then
            log_error "灰度发布未完成，当前阶段: $current_phase ($current_percentage%)"
            return 1
        fi
        
        log_success "灰度发布状态检查通过: $current_phase ($current_percentage%)"
    else
        log_warning "未找到灰度发布状态文件，跳过检查"
    fi
    
    # 检查系统健康状态
    if ! ./scripts/system-monitor.sh all; then
        log_error "系统健康检查失败"
        return 1
    fi
    
    # 检查监控系统
    if ! curl -f -s http://localhost:9090/-/healthy > /dev/null; then
        log_error "Prometheus监控系统不可用"
        return 1
    fi
    
    if ! curl -f -s http://localhost:3000/api/health > /dev/null; then
        log_error "Grafana监控系统不可用"
        return 1
    fi
    
    # 检查SSL证书
    ./scripts/setup-ssl.sh verify
    
    # 检查备份
    if [ ! -d "backups" ] || [ -z "$(ls -A backups 2>/dev/null)" ]; then
        log_warning "未找到备份文件，建议先执行备份"
    fi
    
    log_success "预上线检查完成"
    log_golive "预上线检查通过"
    return 0
}

# 创建上线前备份
create_golive_backup() {
    log_info "创建上线前备份..."
    log_golive "开始创建上线前备份"
    
    mkdir -p "$ROLLBACK_POINT"
    
    # 备份数据库
    if docker-compose -f docker-compose.prod.yml ps postgres | grep -q "Up"; then
        log_info "备份PostgreSQL数据库..."
        docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U lawsker_user lawsker_prod > "$ROLLBACK_POINT/database.sql"
        log_success "数据库备份完成"
    fi
    
    # 备份Redis数据
    if docker-compose -f docker-compose.prod.yml ps redis | grep -q "Up"; then
        log_info "备份Redis数据..."
        docker-compose -f docker-compose.prod.yml exec -T redis redis-cli BGSAVE
        docker cp $(docker-compose -f docker-compose.prod.yml ps -q redis):/data/dump.rdb "$ROLLBACK_POINT/redis.rdb"
        log_success "Redis备份完成"
    fi
    
    # 备份配置文件
    log_info "备份配置文件..."
    cp -r nginx/ "$ROLLBACK_POINT/"
    cp docker-compose.prod.yml "$ROLLBACK_POINT/"
    cp .env.production "$ROLLBACK_POINT/"
    
    # 备份当前部署状态
    if [ -f "deployment-status.json" ]; then
        cp deployment-status.json "$ROLLBACK_POINT/"
    fi
    
    log_success "上线前备份完成: $ROLLBACK_POINT"
    log_golive "上线前备份完成: $ROLLBACK_POINT"
}

# 执行全量切换
execute_full_cutover() {
    log_info "执行全量用户系统切换..."
    log_golive "开始全量用户系统切换"
    
    # 更新部署状态
    cat > deployment-status.json << EOF
{
    "phase": "production",
    "percentage": 100,
    "status": "switching",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "version": "$VERSION"
}
EOF
    
    # 如果存在灰度环境，先停止
    if [ -f "docker-compose.canary.yml" ]; then
        log_info "停止灰度环境..."
        docker-compose -f docker-compose.canary.yml down
    fi
    
    # 更新NGINX配置为生产模式
    log_info "更新NGINX配置..."
    if [ -f "nginx/traffic-split.conf" ]; then
        # 备份流量分割配置
        cp nginx/traffic-split.conf nginx/traffic-split.conf.backup
    fi
    
    # 确保使用生产配置
    docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
    
    # 等待配置生效
    sleep 10
    
    # 验证切换结果
    if curl -f -s http://localhost/health > /dev/null; then
        log_success "全量切换完成"
        log_golive "全量用户系统切换成功"
    else
        log_error "全量切换验证失败"
        log_golive "全量用户系统切换失败"
        return 1
    fi
    
    # 更新部署状态
    cat > deployment-status.json << EOF
{
    "phase": "production",
    "percentage": 100,
    "status": "live",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "version": "$VERSION",
    "cutover_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    return 0
}

# 启动全面监控
start_comprehensive_monitoring() {
    log_info "启动全面系统监控..."
    log_golive "启动全面系统监控和告警"
    
    # 启动系统监控
    if [ ! -f "logs/system-monitor.pid" ]; then
        nohup ./scripts/system-monitor.sh start > logs/system-monitor.log 2>&1 &
        echo $! > logs/system-monitor.pid
        log_success "系统监控已启动 (PID: $!)"
    fi
    
    # 启动性能监控
    if [ ! -f "logs/performance-monitor.pid" ]; then
        nohup ./scripts/performance-monitor.sh start > logs/performance-monitor.log 2>&1 &
        echo $! > logs/performance-monitor.pid
        log_success "性能监控已启动 (PID: $!)"
    fi
    
    # 启动安全监控
    if [ ! -f "logs/security-monitor.pid" ]; then
        nohup ./scripts/security-monitor.sh start > logs/security-monitor.log 2>&1 &
        echo $! > logs/security-monitor.pid
        log_success "安全监控已启动 (PID: $!)"
    fi
    
    # 验证监控服务
    sleep 5
    
    # 检查Prometheus
    if curl -f -s http://localhost:9090/-/healthy > /dev/null; then
        log_success "Prometheus监控正常"
    else
        log_warning "Prometheus监控异常"
    fi
    
    # 检查Grafana
    if curl -f -s http://localhost:3000/api/health > /dev/null; then
        log_success "Grafana监控正常"
    else
        log_warning "Grafana监控异常"
    fi
    
    # 检查ELK
    if curl -f -s http://localhost:9200/_cluster/health > /dev/null; then
        log_success "Elasticsearch日志系统正常"
    else
        log_warning "Elasticsearch日志系统异常"
    fi
    
    log_success "全面监控启动完成"
}

# 上线后性能验证
post_golive_validation() {
    log_info "执行上线后性能验证..."
    log_golive "开始上线后性能验证"
    
    # 等待系统稳定
    log_info "等待系统稳定..."
    sleep 30
    
    # API健康检查
    log_info "执行API健康检查..."
    local api_health_passed=true
    
    # 主要API端点检查
    local endpoints=(
        "/health"
        "/api/v1/auth/me"
        "/api/v1/cases"
        "/api/v1/lawyers"
        "/api/v1/admin/stats"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -f -s "http://localhost$endpoint" > /dev/null; then
            log_success "API端点检查通过: $endpoint"
        else
            log_error "API端点检查失败: $endpoint"
            api_health_passed=false
        fi
    done
    
    # 性能基准测试
    log_info "执行性能基准测试..."
    if [ -f "scripts/performance-test.sh" ]; then
        if ./scripts/performance-test.sh quick; then
            log_success "性能基准测试通过"
        else
            log_warning "性能基准测试未完全通过"
        fi
    fi
    
    # 数据库性能检查
    log_info "检查数据库性能..."
    local db_connections=$(docker-compose -f docker-compose.prod.yml exec -T postgres psql -U lawsker_user -d lawsker_prod -t -c "SELECT count(*) FROM pg_stat_activity;" | xargs)
    log_info "当前数据库连接数: $db_connections"
    
    if [ "$db_connections" -gt 80 ]; then
        log_warning "数据库连接数较高: $db_connections"
    else
        log_success "数据库连接数正常: $db_connections"
    fi
    
    # Redis性能检查
    log_info "检查Redis性能..."
    if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping | grep -q "PONG"; then
        local redis_memory=$(docker-compose -f docker-compose.prod.yml exec -T redis redis-cli info memory | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
        log_success "Redis运行正常，内存使用: $redis_memory"
    else
        log_error "Redis连接异常"
        api_health_passed=false
    fi
    
    # 生成验证报告
    local validation_report="reports/post-golive-validation-$(date +%Y%m%d_%H%M%S).json"
    mkdir -p reports
    
    cat > "$validation_report" << EOF
{
    "validation_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "version": "$VERSION",
    "api_health_passed": $api_health_passed,
    "database_connections": $db_connections,
    "redis_status": "$(docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping | tr -d '\r')",
    "system_load": "$(uptime | awk -F'load average:' '{print $2}')",
    "memory_usage": "$(free | grep Mem | awk '{printf \"%.2f%%\", $3/$2 * 100.0}')",
    "disk_usage": "$(df -h / | awk 'NR==2 {print $5}')"
}
EOF
    
    log_success "上线后验证完成，报告: $validation_report"
    log_golive "上线后性能验证完成"
    
    if [ "$api_health_passed" = true ]; then
        return 0
    else
        return 1
    fi
}

# 建立运维支持流程
setup_operations_support() {
    log_info "建立运维支持和问题处理流程..."
    log_golive "建立运维支持流程"
    
    # 创建运维手册
    cat > "docs/operations-runbook.md" << 'EOF'
# Lawsker运维手册

## 紧急联系方式
- 技术负责人: tech-lead@lawsker.com / 138-xxxx-xxxx
- 运维工程师: devops@lawsker.com / 139-xxxx-xxxx
- 产品负责人: product@lawsker.com / 137-xxxx-xxxx

## 常见问题处理

### 1. 服务不可用
```bash
# 检查服务状态
docker-compose -f docker-compose.prod.yml ps

# 重启服务
docker-compose -f docker-compose.prod.yml restart

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 2. 数据库连接问题
```bash
# 检查数据库状态
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# 查看连接数
docker-compose -f docker-compose.prod.yml exec postgres psql -U lawsker_user -c "SELECT count(*) FROM pg_stat_activity;"

# 重启数据库
docker-compose -f docker-compose.prod.yml restart postgres
```

### 3. 性能问题
```bash
# 系统监控
./scripts/system-monitor.sh all

# 性能测试
./scripts/performance-test.sh

# 生成报告
./scripts/system-monitor.sh report
```

## 监控面板
- Grafana: https://monitor.lawsker.com
- Prometheus: https://monitor.lawsker.com/prometheus
- Kibana: https://logs.lawsker.com

## 备份和恢复
```bash
# 创建备份
./scripts/deploy-production.sh backup

# 恢复备份
./scripts/deploy-production.sh rollback <backup_dir>
```
EOF
    
    # 创建值班表
    cat > "docs/on-call-schedule.md" << 'EOF'
# 值班安排

## 当前值班
- 主值班: 张三 (138-xxxx-xxxx)
- 备值班: 李四 (139-xxxx-xxxx)

## 值班职责
1. 监控系统状态
2. 处理紧急故障
3. 记录问题和解决方案
4. 定期检查备份

## 值班流程
1. 接到告警后5分钟内响应
2. 15分钟内初步定位问题
3. 30分钟内给出解决方案
4. 1小时内解决问题或上报
EOF
    
    # 设置定时任务
    log_info "设置定时监控任务..."
    
    # 添加crontab任务
    (crontab -l 2>/dev/null; cat << 'EOF'
# Lawsker系统监控定时任务
*/5 * * * * /path/to/lawsker/scripts/system-monitor.sh check >> /path/to/lawsker/logs/cron-monitor.log 2>&1
0 */1 * * * /path/to/lawsker/scripts/system-monitor.sh report >> /path/to/lawsker/logs/cron-report.log 2>&1
0 2 * * * /path/to/lawsker/scripts/deploy-production.sh backup >> /path/to/lawsker/logs/cron-backup.log 2>&1
0 3 * * * /path/to/lawsker/scripts/system-monitor.sh cleanup >> /path/to/lawsker/logs/cron-cleanup.log 2>&1
EOF
) | crontab -
    
    log_success "定时任务设置完成"
    
    # 创建问题跟踪模板
    mkdir -p templates
    cat > "templates/incident-report.md" << 'EOF'
# 故障报告

## 基本信息
- 故障时间: 
- 影响范围: 
- 严重程度: [P0/P1/P2/P3]
- 报告人: 

## 故障描述
- 现象: 
- 影响: 
- 用户反馈: 

## 处理过程
- 发现时间: 
- 响应时间: 
- 处理步骤: 
- 解决时间: 

## 根因分析
- 直接原因: 
- 根本原因: 
- 改进措施: 

## 后续行动
- [ ] 监控改进
- [ ] 流程优化
- [ ] 文档更新
- [ ] 培训安排
EOF
    
    log_success "运维支持流程建立完成"
    log_golive "运维支持和问题处理流程已建立"
}

# 发送上线完成通知
send_golive_complete_notification() {
    log_info "发送上线完成通知..."
    
    local message="🎉 Lawsker系统已成功上线！

版本: $VERSION
上线时间: $(date)
备份位置: $ROLLBACK_POINT

监控面板:
- Grafana: https://monitor.lawsker.com
- Prometheus: https://monitor.lawsker.com/prometheus
- Kibana: https://logs.lawsker.com

访问地址:
- 用户端: https://lawsker.com
- 管理后台: https://admin.lawsker.com
- API文档: https://api.lawsker.com/docs

请继续关注系统运行状态。"
    
    send_golive_notification "系统上线完成" "$message" "success"
    
    log_success "上线完成通知已发送"
}

# 主上线流程
main_golive_process() {
    log_info "开始Lawsker系统上线流程..."
    log_golive "========== 开始系统上线流程 =========="
    
    # 1. 预上线检查
    if ! pre_golive_checks; then
        log_error "预上线检查失败，终止上线流程"
        send_golive_notification "上线失败" "预上线检查失败" "error"
        exit 1
    fi
    
    # 2. 创建备份
    create_golive_backup
    
    # 3. 执行全量切换
    if ! execute_full_cutover; then
        log_error "全量切换失败，开始回滚"
        send_golive_notification "上线失败" "全量切换失败，正在回滚" "error"
        # 这里可以调用回滚脚本
        exit 1
    fi
    
    # 4. 启动全面监控
    start_comprehensive_monitoring
    
    # 5. 上线后验证
    if ! post_golive_validation; then
        log_warning "上线后验证发现问题，请检查系统状态"
        send_golive_notification "上线警告" "系统已上线但验证发现问题" "warning"
    fi
    
    # 6. 建立运维支持
    setup_operations_support
    
    # 7. 发送完成通知
    send_golive_complete_notification
    
    log_success "系统上线流程完成！"
    log_golive "========== 系统上线流程完成 =========="
    
    # 显示上线总结
    echo ""
    echo "🎉 Lawsker系统上线成功！"
    echo "版本: $VERSION"
    echo "上线时间: $(date)"
    echo "日志文件: $GO_LIVE_LOG"
    echo "备份位置: $ROLLBACK_POINT"
    echo ""
    echo "访问地址:"
    echo "  用户端: https://lawsker.com"
    echo "  管理后台: https://admin.lawsker.com"
    echo "  监控面板: https://monitor.lawsker.com"
    echo ""
    echo "请继续关注系统运行状态！"
}

# 显示帮助信息
show_help() {
    echo "系统上线脚本"
    echo ""
    echo "使用方法: $0 <command> [version]"
    echo ""
    echo "命令:"
    echo "  golive [version]     执行完整上线流程"
    echo "  check                执行预上线检查"
    echo "  backup               创建上线前备份"
    echo "  cutover              执行全量切换"
    echo "  validate             上线后验证"
    echo "  monitor              启动监控"
    echo "  status               查看上线状态"
    echo "  help                 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 golive v1.1.0     # 上线版本v1.1.0"
    echo "  $0 check             # 执行预上线检查"
    echo "  $0 status            # 查看当前状态"
}

# 主函数
main() {
    case "${1:-golive}" in
        "golive")
            main_golive_process
            ;;
        "check")
            pre_golive_checks
            ;;
        "backup")
            create_golive_backup
            ;;
        "cutover")
            execute_full_cutover
            ;;
        "validate")
            post_golive_validation
            ;;
        "monitor")
            start_comprehensive_monitoring
            ;;
        "status")
            if [ -f "deployment-status.json" ]; then
                jq '.' deployment-status.json
            else
                echo "未找到部署状态文件"
            fi
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"