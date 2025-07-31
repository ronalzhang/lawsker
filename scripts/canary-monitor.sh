#!/bin/bash

# 灰度发布监控脚本
# 实时监控系统指标并在必要时触发自动回滚

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
PROMETHEUS_URL="http://localhost:9090"
ALERT_WEBHOOK="${SLACK_WEBHOOK_URL:-}"
MONITOR_INTERVAL=60  # 监控间隔（秒）
LOG_FILE="logs/canary-monitor.log"

# 创建日志目录
mkdir -p logs

# 记录监控日志
log_monitor() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 查询Prometheus指标
query_prometheus() {
    local query=$1
    local result=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=${query}" | jq -r '.data.result[0].value[1] // "0"')
    echo "$result"
}

# 获取系统指标
get_system_metrics() {
    local metrics_file="metrics/current-metrics.json"
    mkdir -p metrics
    
    # 错误率
    local error_rate=$(query_prometheus 'rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])')
    
    # 响应时间P95
    local response_time_p95=$(query_prometheus 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))')
    
    # 响应时间P99
    local response_time_p99=$(query_prometheus 'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))')
    
    # 可用性
    local availability=$(query_prometheus 'up{job="lawsker-backend"}')
    
    # 请求量
    local request_rate=$(query_prometheus 'rate(http_requests_total[5m])')
    
    # CPU使用率
    local cpu_usage=$(query_prometheus '100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)')
    
    # 内存使用率
    local memory_usage=$(query_prometheus '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100')
    
    # 数据库连接数
    local db_connections=$(query_prometheus 'pg_stat_database_numbackends')
    
    # Redis内存使用率
    local redis_memory=$(query_prometheus 'redis_memory_used_bytes / redis_memory_max_bytes * 100')
    
    # 生成指标JSON
    cat > "$metrics_file" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "error_rate": $error_rate,
    "response_time_p95": $response_time_p95,
    "response_time_p99": $response_time_p99,
    "availability": $availability,
    "request_rate": $request_rate,
    "cpu_usage": $cpu_usage,
    "memory_usage": $memory_usage,
    "db_connections": $db_connections,
    "redis_memory_usage": $redis_memory
}
EOF
    
    echo "$metrics_file"
}

# 检查阈值
check_thresholds() {
    local metrics_file=$1
    local violations=()
    
    # 读取指标
    local error_rate=$(jq -r '.error_rate' "$metrics_file")
    local response_time_p95=$(jq -r '.response_time_p95' "$metrics_file")
    local availability=$(jq -r '.availability' "$metrics_file")
    local cpu_usage=$(jq -r '.cpu_usage' "$metrics_file")
    local memory_usage=$(jq -r '.memory_usage' "$metrics_file")
    
    # 检查错误率阈值 (5%)
    if (( $(echo "$error_rate > 0.05" | bc -l) )); then
        violations+=("错误率过高: ${error_rate}")
        log_warning "错误率阈值违规: $error_rate > 0.05"
    fi
    
    # 检查响应时间阈值 (3秒)
    if (( $(echo "$response_time_p95 > 3" | bc -l) )); then
        violations+=("响应时间过长: ${response_time_p95}s")
        log_warning "响应时间阈值违规: $response_time_p95 > 3s"
    fi
    
    # 检查可用性阈值 (99.5%)
    if (( $(echo "$availability < 0.995" | bc -l) )); then
        violations+=("可用性过低: ${availability}")
        log_warning "可用性阈值违规: $availability < 0.995"
    fi
    
    # 检查CPU使用率阈值 (80%)
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
        violations+=("CPU使用率过高: ${cpu_usage}%")
        log_warning "CPU使用率阈值违规: $cpu_usage > 80%"
    fi
    
    # 检查内存使用率阈值 (90%)
    if (( $(echo "$memory_usage > 90" | bc -l) )); then
        violations+=("内存使用率过高: ${memory_usage}%")
        log_warning "内存使用率阈值违规: $memory_usage > 90%"
    fi
    
    # 返回违规数量
    echo "${#violations[@]}"
    
    # 如果有违规，记录详情
    if [ ${#violations[@]} -gt 0 ]; then
        log_monitor "阈值违规检测到: ${violations[*]}"
        return 1
    fi
    
    return 0
}

# 发送告警
send_alert() {
    local severity=$1
    local message=$2
    local metrics_file=$3
    
    log_error "发送告警: [$severity] $message"
    
    # 构建告警消息
    local alert_data=$(cat << EOF
{
    "text": "🚨 Lawsker灰度发布告警",
    "attachments": [
        {
            "color": "danger",
            "fields": [
                {
                    "title": "告警级别",
                    "value": "$severity",
                    "short": true
                },
                {
                    "title": "告警信息",
                    "value": "$message",
                    "short": false
                },
                {
                    "title": "时间",
                    "value": "$(date)",
                    "short": true
                }
            ]
        }
    ]
}
EOF
)
    
    # 发送到Slack
    if [ -n "$ALERT_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "$alert_data" \
            "$ALERT_WEBHOOK"
    fi
    
    # 发送邮件告警
    if command -v mail &> /dev/null; then
        echo "$message" | mail -s "Lawsker灰度发布告警: $severity" devops@lawsker.com
    fi
    
    # 记录到告警日志
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$severity] $message" >> "logs/alerts.log"
}

# 触发自动回滚
trigger_rollback() {
    local reason=$1
    
    log_error "触发自动回滚: $reason"
    
    # 发送回滚告警
    send_alert "CRITICAL" "自动回滚已触发: $reason" ""
    
    # 执行回滚
    if [ -f "scripts/canary-deployment.sh" ]; then
        ./scripts/canary-deployment.sh rollback
    else
        log_error "回滚脚本不存在"
        return 1
    fi
    
    log_success "自动回滚完成"
}

# 生成监控报告
generate_monitoring_report() {
    local report_file="reports/monitoring-$(date +%Y%m%d_%H%M%S).json"
    mkdir -p reports
    
    # 获取最近的指标
    local metrics_file=$(get_system_metrics)
    
    # 计算统计信息
    local avg_error_rate=$(jq -s 'map(.error_rate) | add / length' metrics/current-metrics-*.json 2>/dev/null || echo "0")
    local max_response_time=$(jq -s 'map(.response_time_p95) | max' metrics/current-metrics-*.json 2>/dev/null || echo "0")
    local min_availability=$(jq -s 'map(.availability) | min' metrics/current-metrics-*.json 2>/dev/null || echo "1")
    
    cat > "$report_file" << EOF
{
    "report_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "monitoring_period": "last_24h",
    "current_metrics": $(cat "$metrics_file"),
    "summary": {
        "average_error_rate": $avg_error_rate,
        "max_response_time": $max_response_time,
        "min_availability": $min_availability,
        "total_alerts": $(wc -l < logs/alerts.log 2>/dev/null || echo "0")
    },
    "deployment_status": $(cat deployment-status.json 2>/dev/null || echo '{}'),
    "recommendations": []
}
EOF
    
    log_success "监控报告已生成: $report_file"
    echo "$report_file"
}

# 主监控循环
monitor_loop() {
    log_info "开始灰度发布监控..."
    
    local consecutive_violations=0
    local max_violations=3  # 连续违规次数阈值
    
    while true; do
        # 获取当前指标
        local metrics_file=$(get_system_metrics)
        log_monitor "指标收集完成: $metrics_file"
        
        # 检查阈值
        if check_thresholds "$metrics_file"; then
            log_success "所有指标正常"
            consecutive_violations=0
        else
            consecutive_violations=$((consecutive_violations + 1))
            log_warning "阈值违规 ($consecutive_violations/$max_violations)"
            
            # 如果连续违规达到阈值，触发回滚
            if [ $consecutive_violations -ge $max_violations ]; then
                trigger_rollback "连续 $consecutive_violations 次阈值违规"
                break
            fi
        fi
        
        # 等待下次检查
        sleep $MONITOR_INTERVAL
    done
}

# 显示当前状态
show_status() {
    log_info "当前监控状态:"
    
    if [ -f "metrics/current-metrics.json" ]; then
        echo "最新指标:"
        jq '.' metrics/current-metrics.json
    else
        echo "暂无指标数据"
    fi
    
    if [ -f "deployment-status.json" ]; then
        echo "部署状态:"
        jq '.' deployment-status.json
    else
        echo "暂无部署状态"
    fi
    
    if [ -f "logs/alerts.log" ]; then
        echo "最近告警:"
        tail -5 logs/alerts.log
    else
        echo "暂无告警记录"
    fi
}

# 显示帮助信息
show_help() {
    echo "灰度发布监控脚本"
    echo ""
    echo "使用方法: $0 <command>"
    echo ""
    echo "命令:"
    echo "  start                开始监控"
    echo "  status               显示当前状态"
    echo "  metrics              获取当前指标"
    echo "  check                检查阈值"
    echo "  report               生成监控报告"
    echo "  test-alert           测试告警"
    echo "  help                 显示此帮助信息"
}

# 主函数
main() {
    case "${1:-help}" in
        "start")
            monitor_loop
            ;;
        "status")
            show_status
            ;;
        "metrics")
            metrics_file=$(get_system_metrics)
            jq '.' "$metrics_file"
            ;;
        "check")
            metrics_file=$(get_system_metrics)
            if check_thresholds "$metrics_file"; then
                log_success "所有阈值检查通过"
            else
                log_warning "发现阈值违规"
                exit 1
            fi
            ;;
        "report")
            generate_monitoring_report
            ;;
        "test-alert")
            send_alert "TEST" "这是一个测试告警" ""
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"