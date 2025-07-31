#!/bin/bash

# 安全监控脚本
# 专门用于监控系统安全状态和威胁检测

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
MONITOR_INTERVAL=60
LOG_FILE="logs/security-monitor.log"
SECURITY_DIR="security/monitoring"
ALERT_THRESHOLD_FAILED_LOGINS=10
ALERT_THRESHOLD_RATE_LIMIT=100

# 创建目录
mkdir -p logs security/monitoring

# 记录安全日志
log_security() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 发送安全告警
send_security_alert() {
    local severity=$1
    local event=$2
    local details=$3
    
    log_error "安全告警: [$severity] $event - $details"
    log_security "ALERT [$severity] $event: $details"
    
    # Slack告警
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        local color="danger"
        case $severity in
            "INFO") color="good" ;;
            "WARNING") color="warning" ;;
        esac
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"text\": \"🚨 Lawsker安全告警\",
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"fields\": [{
                        \"title\": \"严重程度\",
                        \"value\": \"$severity\",
                        \"short\": true
                    }, {
                        \"title\": \"事件类型\",
                        \"value\": \"$event\",
                        \"short\": true
                    }, {
                        \"title\": \"详细信息\",
                        \"value\": \"$details\",
                        \"short\": false
                    }, {
                        \"title\": \"时间\",
                        \"value\": \"$(date)\",
                        \"short\": true
                    }]
                }]
            }" \
            "$SLACK_WEBHOOK_URL"
    fi
    
    # 邮件告警
    if command -v mail &> /dev/null; then
        echo "安全告警详情:
        
严重程度: $severity
事件类型: $event
详细信息: $details
发生时间: $(date)
服务器: $(hostname)

请立即检查系统安全状态。" | mail -s "Lawsker安全告警: $event" security@lawsker.com
    fi
}

# 检查失败登录尝试
check_failed_logins() {
    log_info "检查失败登录尝试..."
    
    # 从应用日志中提取失败登录
    local failed_logins_5min=0
    local failed_logins_1hour=0
    
    if [ -f "backend/logs/app.log" ]; then
        # 最近5分钟的失败登录
        failed_logins_5min=$(grep "$(date -d '5 minutes ago' '+%Y-%m-%d %H:%M')" backend/logs/app.log | grep -c "LOGIN_FAILED" || echo "0")
        
        # 最近1小时的失败登录
        failed_logins_1hour=$(grep "$(date -d '1 hour ago' '+%Y-%m-%d %H')" backend/logs/app.log | grep -c "LOGIN_FAILED" || echo "0")
    fi
    
    # 检查阈值
    if [ "$failed_logins_5min" -gt "$ALERT_THRESHOLD_FAILED_LOGINS" ]; then
        send_security_alert "CRITICAL" "暴力破解攻击" "5分钟内失败登录尝试: $failed_logins_5min 次"
    elif [ "$failed_logins_1hour" -gt $((ALERT_THRESHOLD_FAILED_LOGINS * 6)) ]; then
        send_security_alert "WARNING" "异常登录活动" "1小时内失败登录尝试: $failed_logins_1hour 次"
    fi
    
    # 记录统计
    cat > "$SECURITY_DIR/failed_logins.json" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "failed_logins_5min": $failed_logins_5min,
    "failed_logins_1hour": $failed_logins_1hour,
    "threshold_5min": $ALERT_THRESHOLD_FAILED_LOGINS,
    "threshold_1hour": $((ALERT_THRESHOLD_FAILED_LOGINS * 6))
}
EOF
    
    log_success "失败登录检查完成: 5分钟内 $failed_logins_5min 次，1小时内 $failed_logins_1hour 次"
}

# 检查可疑IP活动
check_suspicious_ips() {
    log_info "检查可疑IP活动..."
    
    local suspicious_ips=()
    local current_time=$(date +%s)
    
    # 分析NGINX访问日志
    if [ -f "nginx/logs/access.log" ]; then
        # 获取最近1小时的高频访问IP
        local high_freq_ips=$(tail -10000 nginx/logs/access.log | \
            awk -v cutoff=$((current_time - 3600)) '
            {
                # 解析时间戳
                gsub(/\[|\]/, "", $4)
                cmd = "date -d \"" $4 "\" +%s"
                cmd | getline timestamp
                close(cmd)
                
                if (timestamp > cutoff) {
                    count[$1]++
                }
            }
            END {
                for (ip in count) {
                    if (count[ip] > 1000) {  # 1小时内超过1000次请求
                        print ip, count[ip]
                    }
                }
            }')
        
        # 检查异常状态码
        local error_ips=$(tail -10000 nginx/logs/access.log | \
            awk '$9 >= 400 && $9 < 500 { count[$1]++ } 
                 END { for (ip in count) if (count[ip] > 50) print ip, count[ip] }')
        
        # 处理可疑IP
        if [ -n "$high_freq_ips" ]; then
            while read -r ip count; do
                suspicious_ips+=("$ip (高频访问: $count 次)")
                log_warning "发现高频访问IP: $ip ($count 次/小时)"
            done <<< "$high_freq_ips"
        fi
        
        if [ -n "$error_ips" ]; then
            while read -r ip count; do
                suspicious_ips+=("$ip (异常请求: $count 次)")
                log_warning "发现异常请求IP: $ip ($count 次4xx错误)"
            done <<< "$error_ips"
        fi
    fi
    
    # 生成可疑IP报告
    cat > "$SECURITY_DIR/suspicious_ips.json" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "suspicious_ips": [
$(printf '        "%s"' "${suspicious_ips[@]}" | sed 's/$/,/' | sed '$s/,$//')
    ],
    "total_count": ${#suspicious_ips[@]}
}
EOF
    
    # 发送告警
    if [ ${#suspicious_ips[@]} -gt 0 ]; then
        send_security_alert "WARNING" "可疑IP活动" "发现 ${#suspicious_ips[@]} 个可疑IP: ${suspicious_ips[*]}"
    fi
    
    log_success "可疑IP检查完成: 发现 ${#suspicious_ips[@]} 个可疑IP"
}

# 检查SSL证书状态
check_ssl_certificates() {
    log_info "检查SSL证书状态..."
    
    local cert_issues=()
    local domains=("lawsker.com" "admin.lawsker.com" "api.lawsker.com" "monitor.lawsker.com")
    
    for domain in "${domains[@]}"; do
        local cert_file="nginx/ssl/${domain}.crt"
        
        if [ -f "$cert_file" ]; then
            # 检查证书有效期
            local expiry_date=$(openssl x509 -in "$cert_file" -noout -enddate | cut -d= -f2)
            local expiry_timestamp=$(date -d "$expiry_date" +%s)
            local current_timestamp=$(date +%s)
            local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
            
            if [ $days_until_expiry -lt 0 ]; then
                cert_issues+=("$domain: 证书已过期")
                send_security_alert "CRITICAL" "SSL证书过期" "$domain 证书已过期"
            elif [ $days_until_expiry -lt 30 ]; then
                cert_issues+=("$domain: 证书将在 $days_until_expiry 天后过期")
                send_security_alert "WARNING" "SSL证书即将过期" "$domain 证书将在 $days_until_expiry 天后过期"
            fi
            
            # 检查证书强度
            local key_size=$(openssl x509 -in "$cert_file" -noout -text | grep "Public-Key:" | grep -o '[0-9]*')
            if [ "$key_size" -lt 2048 ]; then
                cert_issues+=("$domain: 证书密钥长度不足 ($key_size bits)")
                send_security_alert "WARNING" "SSL证书强度不足" "$domain 证书密钥长度: $key_size bits"
            fi
        else
            cert_issues+=("$domain: 证书文件不存在")
            send_security_alert "CRITICAL" "SSL证书缺失" "$domain 证书文件不存在"
        fi
    done
    
    # 生成证书状态报告
    cat > "$SECURITY_DIR/ssl_status.json" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "certificate_issues": [
$(printf '        "%s"' "${cert_issues[@]}" | sed 's/$/,/' | sed '$s/,$//')
    ],
    "total_issues": ${#cert_issues[@]}
}
EOF
    
    log_success "SSL证书检查完成: 发现 ${#cert_issues[@]} 个问题"
}

# 检查系统漏洞
check_system_vulnerabilities() {
    log_info "检查系统漏洞..."
    
    local vulnerabilities=()
    
    # 检查Docker容器安全
    if command -v docker &> /dev/null; then
        # 检查特权容器
        local privileged_containers=$(docker ps --format "table {{.Names}}\t{{.Status}}" --filter "label=privileged=true" | tail -n +2)
        if [ -n "$privileged_containers" ]; then
            vulnerabilities+=("发现特权容器运行")
            log_warning "发现特权容器: $privileged_containers"
        fi
        
        # 检查容器镜像漏洞（如果安装了trivy）
        if command -v trivy &> /dev/null; then
            local high_vulns=$(trivy image --severity HIGH,CRITICAL lawsker/backend:latest 2>/dev/null | grep -c "HIGH\|CRITICAL" || echo "0")
            if [ "$high_vulns" -gt 0 ]; then
                vulnerabilities+=("容器镜像存在 $high_vulns 个高危漏洞")
                send_security_alert "WARNING" "容器镜像漏洞" "发现 $high_vulns 个高危漏洞"
            fi
        fi
    fi
    
    # 检查开放端口
    local open_ports=$(netstat -tuln | grep LISTEN | awk '{print $4}' | cut -d: -f2 | sort -n | uniq)
    local unexpected_ports=()
    local expected_ports=("22" "80" "443" "3000" "5432" "6379" "9090")
    
    while read -r port; do
        if [[ ! " ${expected_ports[@]} " =~ " ${port} " ]]; then
            unexpected_ports+=("$port")
        fi
    done <<< "$open_ports"
    
    if [ ${#unexpected_ports[@]} -gt 0 ]; then
        vulnerabilities+=("发现意外开放端口: ${unexpected_ports[*]}")
        log_warning "发现意外开放端口: ${unexpected_ports[*]}"
    fi
    
    # 检查文件权限
    local sensitive_files=("/etc/passwd" "/etc/shadow" "/etc/ssh/sshd_config")
    for file in "${sensitive_files[@]}"; do
        if [ -f "$file" ]; then
            local perms=$(stat -c "%a" "$file")
            case "$file" in
                "/etc/shadow")
                    if [ "$perms" != "640" ] && [ "$perms" != "600" ]; then
                        vulnerabilities+=("$file 权限不安全: $perms")
                    fi
                    ;;
                "/etc/passwd")
                    if [ "$perms" != "644" ]; then
                        vulnerabilities+=("$file 权限不安全: $perms")
                    fi
                    ;;
                "/etc/ssh/sshd_config")
                    if [ "$perms" != "600" ] && [ "$perms" != "644" ]; then
                        vulnerabilities+=("$file 权限不安全: $perms")
                    fi
                    ;;
            esac
        fi
    done
    
    # 生成漏洞报告
    cat > "$SECURITY_DIR/vulnerabilities.json" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "vulnerabilities": [
$(printf '        "%s"' "${vulnerabilities[@]}" | sed 's/$/,/' | sed '$s/,$//')
    ],
    "total_count": ${#vulnerabilities[@]},
    "open_ports": [$(echo "$open_ports" | tr '\n' ',' | sed 's/,$//')],
    "unexpected_ports": [$(printf '"%s",' "${unexpected_ports[@]}" | sed 's/,$/')]
}
EOF
    
    if [ ${#vulnerabilities[@]} -gt 0 ]; then
        send_security_alert "WARNING" "系统漏洞检测" "发现 ${#vulnerabilities[@]} 个潜在安全问题"
    fi
    
    log_success "系统漏洞检查完成: 发现 ${#vulnerabilities[@]} 个问题"
}

# 检查访问控制
check_access_control() {
    log_info "检查访问控制..."
    
    local access_issues=()
    
    # 检查管理后台访问
    if [ -f "nginx/logs/access.log" ]; then
        # 检查管理后台的异常访问
        local admin_access=$(tail -1000 nginx/logs/access.log | grep "admin.lawsker.com" | wc -l)
        local admin_errors=$(tail -1000 nginx/logs/access.log | grep "admin.lawsker.com" | grep -E " (401|403|404) " | wc -l)
        
        if [ "$admin_errors" -gt 10 ]; then
            access_issues+=("管理后台异常访问尝试: $admin_errors 次")
            send_security_alert "WARNING" "管理后台异常访问" "发现 $admin_errors 次异常访问尝试"
        fi
    fi
    
    # 检查API访问模式
    if [ -f "backend/logs/app.log" ]; then
        # 检查API滥用
        local api_abuse=$(grep "$(date '+%Y-%m-%d %H')" backend/logs/app.log | grep -c "RATE_LIMIT_EXCEEDED" || echo "0")
        if [ "$api_abuse" -gt "$ALERT_THRESHOLD_RATE_LIMIT" ]; then
            access_issues+=("API限流触发频繁: $api_abuse 次")
            send_security_alert "WARNING" "API滥用检测" "1小时内限流触发 $api_abuse 次"
        fi
    fi
    
    # 检查数据库访问
    if docker-compose -f docker-compose.prod.yml ps postgres | grep -q "Up"; then
        local db_connections=$(docker-compose -f docker-compose.prod.yml exec -T postgres psql -U lawsker_user -d lawsker_prod -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" | xargs)
        if [ "$db_connections" -gt 50 ]; then
            access_issues+=("数据库活跃连接过多: $db_connections")
            log_warning "数据库活跃连接数: $db_connections"
        fi
    fi
    
    # 生成访问控制报告
    cat > "$SECURITY_DIR/access_control.json" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "access_issues": [
$(printf '        "%s"' "${access_issues[@]}" | sed 's/$/,/' | sed '$s/,$//')
    ],
    "total_issues": ${#access_issues[@]}
}
EOF
    
    log_success "访问控制检查完成: 发现 ${#access_issues[@]} 个问题"
}

# 生成安全报告
generate_security_report() {
    local report_file="reports/security-report-$(date +%Y%m%d_%H%M%S).json"
    mkdir -p reports
    
    log_info "生成安全报告..."
    
    # 汇总所有安全检查结果
    local failed_logins=$(jq -r '.failed_logins_1hour // 0' "$SECURITY_DIR/failed_logins.json" 2>/dev/null || echo "0")
    local suspicious_ips=$(jq -r '.total_count // 0' "$SECURITY_DIR/suspicious_ips.json" 2>/dev/null || echo "0")
    local cert_issues=$(jq -r '.total_issues // 0' "$SECURITY_DIR/ssl_status.json" 2>/dev/null || echo "0")
    local vulnerabilities=$(jq -r '.total_count // 0' "$SECURITY_DIR/vulnerabilities.json" 2>/dev/null || echo "0")
    local access_issues=$(jq -r '.total_issues // 0' "$SECURITY_DIR/access_control.json" 2>/dev/null || echo "0")
    
    # 计算安全评分 (100分制)
    local security_score=100
    security_score=$((security_score - failed_logins / 10))
    security_score=$((security_score - suspicious_ips * 5))
    security_score=$((security_score - cert_issues * 10))
    security_score=$((security_score - vulnerabilities * 5))
    security_score=$((security_score - access_issues * 3))
    
    # 确保评分不低于0
    if [ "$security_score" -lt 0 ]; then
        security_score=0
    fi
    
    cat > "$report_file" << EOF
{
    "report_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "security_score": $security_score,
    "summary": {
        "failed_logins_1hour": $failed_logins,
        "suspicious_ips": $suspicious_ips,
        "certificate_issues": $cert_issues,
        "vulnerabilities": $vulnerabilities,
        "access_control_issues": $access_issues
    },
    "status": "$([ "$security_score" -gt 80 ] && echo "GOOD" || [ "$security_score" -gt 60 ] && echo "WARNING" || echo "CRITICAL")",
    "recommendations": []
}
EOF
    
    # 添加建议
    local recommendations=()
    
    if [ "$failed_logins" -gt 20 ]; then
        recommendations+=("加强登录安全策略，考虑实施账户锁定机制")
    fi
    
    if [ "$suspicious_ips" -gt 0 ]; then
        recommendations+=("审查可疑IP活动，考虑实施IP黑名单")
    fi
    
    if [ "$cert_issues" -gt 0 ]; then
        recommendations+=("及时更新SSL证书，确保证书安全性")
    fi
    
    if [ "$vulnerabilities" -gt 0 ]; then
        recommendations+=("修复系统漏洞，加强系统安全配置")
    fi
    
    # 更新报告
    local recommendations_json=$(printf '%s\n' "${recommendations[@]}" | jq -R . | jq -s .)
    jq ".recommendations = $recommendations_json" "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log_success "安全报告已生成: $report_file (安全评分: $security_score/100)"
    echo "$report_file"
}

# 启动安全监控
start_security_monitoring() {
    log_info "启动安全监控..."
    log_security "安全监控启动"
    
    while true; do
        log_info "执行安全检查循环..."
        
        # 执行各项安全检查
        check_failed_logins
        check_suspicious_ips
        check_ssl_certificates
        check_system_vulnerabilities
        check_access_control
        
        # 生成报告
        generate_security_report
        
        log_success "安全检查循环完成，等待下次检查..."
        sleep $MONITOR_INTERVAL
    done
}

# 显示帮助信息
show_help() {
    echo "安全监控脚本"
    echo ""
    echo "使用方法: $0 <command>"
    echo ""
    echo "命令:"
    echo "  start                开始安全监控"
    echo "  check                执行一次完整安全检查"
    echo "  logins               检查失败登录"
    echo "  ips                  检查可疑IP"
    echo "  ssl                  检查SSL证书"
    echo "  vulns                检查系统漏洞"
    echo "  access               检查访问控制"
    echo "  report               生成安全报告"
    echo "  cleanup              清理旧监控文件"
    echo "  help                 显示此帮助信息"
}

# 主函数
main() {
    case "${1:-help}" in
        "start")
            start_security_monitoring
            ;;
        "check")
            check_failed_logins
            check_suspicious_ips
            check_ssl_certificates
            check_system_vulnerabilities
            check_access_control
            generate_security_report
            ;;
        "logins")
            check_failed_logins
            ;;
        "ips")
            check_suspicious_ips
            ;;
        "ssl")
            check_ssl_certificates
            ;;
        "vulns")
            check_system_vulnerabilities
            ;;
        "access")
            check_access_control
            ;;
        "report")
            generate_security_report
            ;;
        "cleanup")
            find $SECURITY_DIR -name "*.json" -mtime +30 -delete
            find logs -name "security-*.log" -mtime +30 -delete
            log_success "安全监控文件清理完成"
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"