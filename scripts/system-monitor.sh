#!/bin/bash

# 系统监控脚本
# 用于监控系统状态和服务健康状况

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

# 检查Docker服务状态
check_docker_services() {
    log_info "检查Docker服务状态..."
    
    services=("nginx" "backend" "postgres" "redis" "prometheus" "grafana" "elasticsearch" "logstash" "kibana")
    
    for service in "${services[@]}"; do
        if docker-compose -f docker-compose.prod.yml ps "$service" | grep -q "Up"; then
            log_success "$service 服务运行正常"
        else
            log_error "$service 服务未正常运行"
            # 尝试重启服务
            log_info "尝试重启 $service 服务..."
            docker-compose -f docker-compose.prod.yml restart "$service"
        fi
    done
}

# 检查系统资源使用情况
check_system_resources() {
    log_info "检查系统资源使用情况..."
    
    # CPU使用率
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
        log_warning "CPU使用率过高: ${cpu_usage}%"
    else
        log_success "CPU使用率正常: ${cpu_usage}%"
    fi
    
    # 内存使用率
    memory_info=$(free | grep Mem)
    total_memory=$(echo $memory_info | awk '{print $2}')
    used_memory=$(echo $memory_info | awk '{print $3}')
    memory_usage=$(echo "scale=2; $used_memory * 100 / $total_memory" | bc)
    
    if (( $(echo "$memory_usage > 90" | bc -l) )); then
        log_warning "内存使用率过高: ${memory_usage}%"
    else
        log_success "内存使用率正常: ${memory_usage}%"
    fi
    
    # 磁盘使用率
    disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        log_warning "磁盘使用率过高: ${disk_usage}%"
    else
        log_success "磁盘使用率正常: ${disk_usage}%"
    fi
}

# 检查网络连接
check_network() {
    log_info "检查网络连接..."
    
    # 检查外网连接
    if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        log_success "外网连接正常"
    else
        log_error "外网连接异常"
    fi
    
    # 检查DNS解析
    if nslookup google.com > /dev/null 2>&1; then
        log_success "DNS解析正常"
    else
        log_error "DNS解析异常"
    fi
}

# 检查数据库连接
check_database() {
    log_info "检查数据库连接..."
    
    # PostgreSQL连接检查
    if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U lawsker_user -d lawsker_prod > /dev/null 2>&1; then
        log_success "PostgreSQL连接正常"
        
        # 检查数据库大小
        db_size=$(docker-compose -f docker-compose.prod.yml exec -T postgres psql -U lawsker_user -d lawsker_prod -t -c "SELECT pg_size_pretty(pg_database_size('lawsker_prod'));" | xargs)
        log_info "数据库大小: $db_size"
        
        # 检查连接数
        connection_count=$(docker-compose -f docker-compose.prod.yml exec -T postgres psql -U lawsker_user -d lawsker_prod -t -c "SELECT count(*) FROM pg_stat_activity;" | xargs)
        log_info "当前连接数: $connection_count"
        
        if [ "$connection_count" -gt 80 ]; then
            log_warning "数据库连接数过高: $connection_count"
        fi
    else
        log_error "PostgreSQL连接异常"
    fi
    
    # Redis连接检查
    if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping | grep -q "PONG"; then
        log_success "Redis连接正常"
        
        # 检查Redis内存使用
        redis_memory=$(docker-compose -f docker-compose.prod.yml exec -T redis redis-cli info memory | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
        log_info "Redis内存使用: $redis_memory"
    else
        log_error "Redis连接异常"
    fi
}

# 检查API健康状态
check_api_health() {
    log_info "检查API健康状态..."
    
    # 检查主API
    if curl -f -s http://localhost/health > /dev/null; then
        log_success "主API健康检查通过"
    else
        log_error "主API健康检查失败"
    fi
    
    # 检查管理API
    if curl -f -s http://localhost/api/v1/admin/health > /dev/null; then
        log_success "管理API健康检查通过"
    else
        log_error "管理API健康检查失败"
    fi
}

# 检查SSL证书状态
check_ssl_certificates() {
    log_info "检查SSL证书状态..."
    
    domains=("lawsker.com" "admin.lawsker.com" "api.lawsker.com" "monitor.lawsker.com" "logs.lawsker.com")
    
    for domain in "${domains[@]}"; do
        cert_file="nginx/ssl/${domain}.crt"
        
        if [ -f "$cert_file" ]; then
            expiry_date=$(openssl x509 -in "$cert_file" -noout -enddate | cut -d= -f2)
            expiry_timestamp=$(date -d "$expiry_date" +%s)
            current_timestamp=$(date +%s)
            days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
            
            if [ $days_until_expiry -lt 30 ]; then
                log_warning "$domain SSL证书将在 $days_until_expiry 天后过期"
            elif [ $days_until_expiry -lt 0 ]; then
                log_error "$domain SSL证书已过期"
            else
                log_success "$domain SSL证书有效，剩余 $days_until_expiry 天"
            fi
        else
            log_error "$domain SSL证书文件不存在"
        fi
    done
}

# 检查日志文件大小
check_log_files() {
    log_info "检查日志文件大小..."
    
    log_dirs=("backend/logs" "nginx/logs")
    
    for log_dir in "${log_dirs[@]}"; do
        if [ -d "$log_dir" ]; then
            total_size=$(du -sh "$log_dir" | cut -f1)
            log_info "$log_dir 总大小: $total_size"
            
            # 检查是否有过大的日志文件
            find "$log_dir" -name "*.log" -size +100M -exec ls -lh {} \; | while read line; do
                log_warning "发现大日志文件: $line"
            done
        fi
    done
}

# 检查备份状态
check_backup_status() {
    log_info "检查备份状态..."
    
    if [ -d "backups" ]; then
        # 检查最近的备份
        latest_backup=$(find backups -type d -name "20*" | sort | tail -1)
        if [ -n "$latest_backup" ]; then
            backup_date=$(basename "$latest_backup")
            log_info "最新备份: $backup_date"
            
            # 检查备份是否过旧（超过7天）
            backup_timestamp=$(date -d "${backup_date:0:8}" +%s)
            current_timestamp=$(date +%s)
            days_since_backup=$(( (current_timestamp - backup_timestamp) / 86400 ))
            
            if [ $days_since_backup -gt 7 ]; then
                log_warning "备份过旧，距离上次备份 $days_since_backup 天"
            else
                log_success "备份状态正常"
            fi
        else
            log_warning "未找到备份文件"
        fi
    else
        log_warning "备份目录不存在"
    fi
}

# 生成监控报告
generate_report() {
    log_info "生成监控报告..."
    
    report_file="logs/monitor-report-$(date +%Y%m%d_%H%M%S).txt"
    mkdir -p logs
    
    {
        echo "Lawsker系统监控报告"
        echo "生成时间: $(date)"
        echo "=================================="
        echo ""
        
        echo "系统信息:"
        echo "- 主机名: $(hostname)"
        echo "- 系统版本: $(uname -a)"
        echo "- 运行时间: $(uptime)"
        echo ""
        
        echo "Docker服务状态:"
        docker-compose -f docker-compose.prod.yml ps
        echo ""
        
        echo "系统资源使用:"
        echo "- CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')"
        echo "- 内存: $(free -h | grep Mem)"
        echo "- 磁盘: $(df -h /)"
        echo ""
        
        echo "网络状态:"
        echo "- 网络接口: $(ip addr show | grep inet)"
        echo "- 网络连接: $(netstat -tuln | grep LISTEN | wc -l) 个监听端口"
        echo ""
        
        echo "数据库状态:"
        if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U lawsker_user -d lawsker_prod > /dev/null 2>&1; then
            echo "- PostgreSQL: 运行正常"
            echo "- 数据库大小: $(docker-compose -f docker-compose.prod.yml exec -T postgres psql -U lawsker_user -d lawsker_prod -t -c "SELECT pg_size_pretty(pg_database_size('lawsker_prod'));" | xargs)"
        else
            echo "- PostgreSQL: 连接异常"
        fi
        
        if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping | grep -q "PONG"; then
            echo "- Redis: 运行正常"
        else
            echo "- Redis: 连接异常"
        fi
        echo ""
        
        echo "日志文件大小:"
        for log_dir in backend/logs nginx/logs; do
            if [ -d "$log_dir" ]; then
                echo "- $log_dir: $(du -sh "$log_dir" | cut -f1)"
            fi
        done
        
    } > "$report_file"
    
    log_success "监控报告已生成: $report_file"
}

# 清理系统
cleanup_system() {
    log_info "清理系统..."
    
    # 清理Docker
    log_info "清理Docker资源..."
    docker system prune -f
    
    # 清理旧日志
    log_info "清理旧日志文件..."
    find backend/logs -name "*.log" -mtime +30 -delete 2>/dev/null || true
    find nginx/logs -name "*.log" -mtime +30 -delete 2>/dev/null || true
    
    # 清理旧备份
    log_info "清理旧备份文件..."
    find backups -type d -name "20*" -mtime +30 -exec rm -rf {} \; 2>/dev/null || true
    
    log_success "系统清理完成"
}

# 显示帮助信息
show_help() {
    echo "系统监控脚本"
    echo ""
    echo "使用方法: $0 <command>"
    echo ""
    echo "命令:"
    echo "  all          执行所有检查"
    echo "  docker       检查Docker服务"
    echo "  resources    检查系统资源"
    echo "  network      检查网络连接"
    echo "  database     检查数据库"
    echo "  api          检查API健康状态"
    echo "  ssl          检查SSL证书"
    echo "  logs         检查日志文件"
    echo "  backup       检查备份状态"
    echo "  report       生成监控报告"
    echo "  cleanup      清理系统"
    echo "  help         显示此帮助信息"
}

# 主函数
main() {
    case "${1:-all}" in
        "all")
            check_docker_services
            check_system_resources
            check_network
            check_database
            check_api_health
            check_ssl_certificates
            check_log_files
            check_backup_status
            ;;
        "docker")
            check_docker_services
            ;;
        "resources")
            check_system_resources
            ;;
        "network")
            check_network
            ;;
        "database")
            check_database
            ;;
        "api")
            check_api_health
            ;;
        "ssl")
            check_ssl_certificates
            ;;
        "logs")
            check_log_files
            ;;
        "backup")
            check_backup_status
            ;;
        "report")
            generate_report
            ;;
        "cleanup")
            cleanup_system
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"