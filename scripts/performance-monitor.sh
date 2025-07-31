#!/bin/bash

# 性能监控脚本
# 专门用于监控系统性能指标

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
MONITOR_INTERVAL=30
LOG_FILE="logs/performance-monitor.log"
METRICS_DIR="metrics/performance"

# 创建目录
mkdir -p logs metrics/performance

# 记录性能日志
log_performance() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 查询Prometheus指标
query_prometheus() {
    local query=$1
    local result=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=${query}" | jq -r '.data.result[0].value[1] // "0"')
    echo "$result"
}

# 获取系统性能指标
collect_system_metrics() {
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local metrics_file="$METRICS_DIR/system-$(date +%Y%m%d_%H%M%S).json"
    
    log_info "收集系统性能指标..."
    
    # CPU指标
    local cpu_usage=$(query_prometheus '100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)')
    local cpu_load_1m=$(query_prometheus 'node_load1')
    local cpu_load_5m=$(query_prometheus 'node_load5')
    local cpu_load_15m=$(query_prometheus 'node_load15')
    
    # 内存指标
    local memory_total=$(query_prometheus 'node_memory_MemTotal_bytes')
    local memory_available=$(query_prometheus 'node_memory_MemAvailable_bytes')
    local memory_usage=$(echo "scale=2; (1 - $memory_available / $memory_total) * 100" | bc)
    
    # 磁盘指标
    local disk_usage=$(query_prometheus '100 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} * 100)')
    local disk_io_read=$(query_prometheus 'rate(node_disk_read_bytes_total[5m])')
    local disk_io_write=$(query_prometheus 'rate(node_disk_written_bytes_total[5m])')
    
    # 网络指标
    local network_in=$(query_prometheus 'rate(node_network_receive_bytes_total[5m])')
    local network_out=$(query_prometheus 'rate(node_network_transmit_bytes_total[5m])')
    
    # 生成指标JSON
    cat > "$metrics_file" << EOF
{
    "timestamp": "$timestamp",
    "system": {
        "cpu": {
            "usage_percent": $cpu_usage,
            "load_1m": $cpu_load_1m,
            "load_5m": $cpu_load_5m,
            "load_15m": $cpu_load_15m
        },
        "memory": {
            "total_bytes": $memory_total,
            "available_bytes": $memory_available,
            "usage_percent": $memory_usage
        },
        "disk": {
            "usage_percent": $disk_usage,
            "io_read_bytes_per_sec": $disk_io_read,
            "io_write_bytes_per_sec": $disk_io_write
        },
        "network": {
            "in_bytes_per_sec": $network_in,
            "out_bytes_per_sec": $network_out
        }
    }
}
EOF
    
    log_performance "系统指标收集完成: $metrics_file"
    echo "$metrics_file"
}

# 获取应用性能指标
collect_application_metrics() {
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local metrics_file="$METRICS_DIR/application-$(date +%Y%m%d_%H%M%S).json"
    
    log_info "收集应用性能指标..."
    
    # HTTP请求指标
    local request_rate=$(query_prometheus 'rate(http_requests_total[5m])')
    local error_rate=$(query_prometheus 'rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])')
    local response_time_p50=$(query_prometheus 'histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))')
    local response_time_p95=$(query_prometheus 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))')
    local response_time_p99=$(query_prometheus 'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))')
    
    # 数据库指标
    local db_connections=$(query_prometheus 'pg_stat_database_numbackends')
    local db_query_time=$(query_prometheus 'pg_stat_database_blk_read_time + pg_stat_database_blk_write_time')
    local db_cache_hit_ratio=$(query_prometheus 'pg_stat_database_blks_hit / (pg_stat_database_blks_hit + pg_stat_database_blks_read)')
    
    # Redis指标
    local redis_memory_usage=$(query_prometheus 'redis_memory_used_bytes')
    local redis_connected_clients=$(query_prometheus 'redis_connected_clients')
    local redis_ops_per_sec=$(query_prometheus 'rate(redis_commands_processed_total[5m])')
    
    # 应用指标
    local active_users=$(query_prometheus 'active_users_total')
    local concurrent_sessions=$(query_prometheus 'concurrent_sessions_total')
    
    cat > "$metrics_file" << EOF
{
    "timestamp": "$timestamp",
    "application": {
        "http": {
            "request_rate": $request_rate,
            "error_rate": $error_rate,
            "response_time": {
                "p50": $response_time_p50,
                "p95": $response_time_p95,
                "p99": $response_time_p99
            }
        },
        "database": {
            "connections": $db_connections,
            "query_time_ms": $db_query_time,
            "cache_hit_ratio": $db_cache_hit_ratio
        },
        "redis": {
            "memory_usage_bytes": $redis_memory_usage,
            "connected_clients": $redis_connected_clients,
            "ops_per_sec": $redis_ops_per_sec
        },
        "users": {
            "active_users": $active_users,
            "concurrent_sessions": $concurrent_sessions
        }
    }
}
EOF
    
    log_performance "应用指标收集完成: $metrics_file"
    echo "$metrics_file"
}

# 获取业务性能指标
collect_business_metrics() {
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local metrics_file="$METRICS_DIR/business-$(date +%Y%m%d_%H%M%S).json"
    
    log_info "收集业务性能指标..."
    
    # 用户行为指标
    local user_registrations=$(query_prometheus 'increase(user_registrations_total[1h])')
    local user_logins=$(query_prometheus 'increase(user_logins_total[1h])')
    local case_creations=$(query_prometheus 'increase(case_creations_total[1h])')
    local payment_success=$(query_prometheus 'increase(payment_success_total[1h])')
    local payment_failures=$(query_prometheus 'increase(payment_failures_total[1h])')
    
    # 转化率指标
    local registration_conversion=$(echo "scale=4; $user_registrations / ($user_registrations + $user_logins)" | bc)
    local payment_success_rate=$(echo "scale=4; $payment_success / ($payment_success + $payment_failures)" | bc)
    
    cat > "$metrics_file" << EOF
{
    "timestamp": "$timestamp",
    "business": {
        "user_activity": {
            "registrations_per_hour": $user_registrations,
            "logins_per_hour": $user_logins,
            "case_creations_per_hour": $case_creations
        },
        "payments": {
            "success_per_hour": $payment_success,
            "failures_per_hour": $payment_failures,
            "success_rate": $payment_success_rate
        },
        "conversions": {
            "registration_rate": $registration_conversion
        }
    }
}
EOF
    
    log_performance "业务指标收集完成: $metrics_file"
    echo "$metrics_file"
}

# 性能阈值检查
check_performance_thresholds() {
    local system_file=$1
    local app_file=$2
    local violations=()
    
    log_info "检查性能阈值..."
    
    # 读取系统指标
    local cpu_usage=$(jq -r '.system.cpu.usage_percent' "$system_file")
    local memory_usage=$(jq -r '.system.memory.usage_percent' "$app_file")
    local disk_usage=$(jq -r '.system.disk.usage_percent' "$system_file")
    
    # 读取应用指标
    local error_rate=$(jq -r '.application.http.error_rate' "$app_file")
    local response_time_p95=$(jq -r '.application.http.response_time.p95' "$app_file")
    local db_connections=$(jq -r '.application.database.connections' "$app_file")
    
    # CPU使用率检查 (80%)
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
        violations+=("CPU使用率过高: ${cpu_usage}%")
        log_warning "CPU使用率阈值违规: $cpu_usage% > 80%"
    fi
    
    # 内存使用率检查 (85%)
    if (( $(echo "$memory_usage > 85" | bc -l) )); then
        violations+=("内存使用率过高: ${memory_usage}%")
        log_warning "内存使用率阈值违规: $memory_usage% > 85%"
    fi
    
    # 磁盘使用率检查 (90%)
    if (( $(echo "$disk_usage > 90" | bc -l) )); then
        violations+=("磁盘使用率过高: ${disk_usage}%")
        log_warning "磁盘使用率阈值违规: $disk_usage% > 90%"
    fi
    
    # 错误率检查 (3%)
    if (( $(echo "$error_rate > 0.03" | bc -l) )); then
        violations+=("错误率过高: ${error_rate}")
        log_warning "错误率阈值违规: $error_rate > 0.03"
    fi
    
    # 响应时间检查 (2秒)
    if (( $(echo "$response_time_p95 > 2" | bc -l) )); then
        violations+=("响应时间过长: ${response_time_p95}s")
        log_warning "响应时间阈值违规: $response_time_p95s > 2s"
    fi
    
    # 数据库连接数检查 (70)
    if (( $(echo "$db_connections > 70" | bc -l) )); then
        violations+=("数据库连接数过高: ${db_connections}")
        log_warning "数据库连接数阈值违规: $db_connections > 70"
    fi
    
    # 记录违规情况
    if [ ${#violations[@]} -gt 0 ]; then
        log_performance "性能阈值违规: ${violations[*]}"
        return 1
    else
        log_success "所有性能指标正常"
        return 0
    fi
}

# 生成性能报告
generate_performance_report() {
    local period=${1:-"1h"}
    local report_file="reports/performance-report-$(date +%Y%m%d_%H%M%S).json"
    mkdir -p reports
    
    log_info "生成性能报告 (周期: $period)..."
    
    # 计算时间范围
    local end_time=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local start_time
    case $period in
        "1h") start_time=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) ;;
        "24h") start_time=$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ) ;;
        "7d") start_time=$(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%SZ) ;;
        *) start_time=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) ;;
    esac
    
    # 聚合指标
    local avg_cpu=$(query_prometheus "avg_over_time(100 - (avg by(instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)[$period])")
    local max_memory=$(query_prometheus "max_over_time((1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100[$period])")
    local avg_response_time=$(query_prometheus "avg_over_time(histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))[$period])")
    local max_error_rate=$(query_prometheus "max_over_time(rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m])[$period])")
    
    cat > "$report_file" << EOF
{
    "report_time": "$end_time",
    "period": "$period",
    "time_range": {
        "start": "$start_time",
        "end": "$end_time"
    },
    "summary": {
        "avg_cpu_usage": $avg_cpu,
        "max_memory_usage": $max_memory,
        "avg_response_time": $avg_response_time,
        "max_error_rate": $max_error_rate
    },
    "recommendations": []
}
EOF
    
    # 添加建议
    local recommendations=()
    
    if (( $(echo "$avg_cpu > 70" | bc -l) )); then
        recommendations+=("考虑增加CPU资源或优化CPU密集型操作")
    fi
    
    if (( $(echo "$max_memory > 80" | bc -l) )); then
        recommendations+=("考虑增加内存资源或优化内存使用")
    fi
    
    if (( $(echo "$avg_response_time > 1.5" | bc -l) )); then
        recommendations+=("优化API响应时间，检查数据库查询和缓存策略")
    fi
    
    if (( $(echo "$max_error_rate > 0.02" | bc -l) )); then
        recommendations+=("调查错误原因，改进错误处理机制")
    fi
    
    # 更新报告
    local recommendations_json=$(printf '%s\n' "${recommendations[@]}" | jq -R . | jq -s .)
    jq ".recommendations = $recommendations_json" "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log_success "性能报告已生成: $report_file"
    echo "$report_file"
}

# 性能优化建议
suggest_optimizations() {
    log_info "分析性能数据并提供优化建议..."
    
    # 获取最新指标
    local latest_system=$(ls -t $METRICS_DIR/system-*.json | head -1)
    local latest_app=$(ls -t $METRICS_DIR/application-*.json | head -1)
    
    if [ -z "$latest_system" ] || [ -z "$latest_app" ]; then
        log_warning "未找到性能指标数据"
        return 1
    fi
    
    # 分析CPU使用情况
    local cpu_usage=$(jq -r '.system.cpu.usage_percent' "$latest_system")
    if (( $(echo "$cpu_usage > 70" | bc -l) )); then
        echo "🔧 CPU优化建议:"
        echo "  - 检查CPU密集型进程"
        echo "  - 考虑增加CPU核心数"
        echo "  - 优化算法复杂度"
    fi
    
    # 分析内存使用情况
    local memory_usage=$(jq -r '.system.memory.usage_percent' "$latest_system")
    if (( $(echo "$memory_usage > 80" | bc -l) )); then
        echo "🔧 内存优化建议:"
        echo "  - 检查内存泄漏"
        echo "  - 优化缓存策略"
        echo "  - 增加内存容量"
    fi
    
    # 分析响应时间
    local response_time=$(jq -r '.application.http.response_time.p95' "$latest_app")
    if (( $(echo "$response_time > 1" | bc -l) )); then
        echo "🔧 响应时间优化建议:"
        echo "  - 优化数据库查询"
        echo "  - 增加缓存层"
        echo "  - 使用CDN加速静态资源"
    fi
    
    # 分析数据库性能
    local db_connections=$(jq -r '.application.database.connections' "$latest_app")
    if (( $(echo "$db_connections > 50" | bc -l) )); then
        echo "🔧 数据库优化建议:"
        echo "  - 优化连接池配置"
        echo "  - 检查慢查询"
        echo "  - 考虑读写分离"
    fi
}

# 启动性能监控
start_monitoring() {
    log_info "启动性能监控..."
    
    while true; do
        # 收集指标
        local system_file=$(collect_system_metrics)
        local app_file=$(collect_application_metrics)
        local business_file=$(collect_business_metrics)
        
        # 检查阈值
        if ! check_performance_thresholds "$system_file" "$app_file"; then
            log_warning "发现性能问题，建议检查系统状态"
        fi
        
        # 等待下次收集
        sleep $MONITOR_INTERVAL
    done
}

# 显示帮助信息
show_help() {
    echo "性能监控脚本"
    echo ""
    echo "使用方法: $0 <command> [options]"
    echo ""
    echo "命令:"
    echo "  start                开始性能监控"
    echo "  collect              收集一次性能指标"
    echo "  check                检查性能阈值"
    echo "  report [period]      生成性能报告"
    echo "  suggest              提供优化建议"
    echo "  cleanup              清理旧指标文件"
    echo "  help                 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start             # 启动持续监控"
    echo "  $0 report 24h        # 生成24小时性能报告"
    echo "  $0 suggest           # 获取优化建议"
}

# 主函数
main() {
    case "${1:-help}" in
        "start")
            start_monitoring
            ;;
        "collect")
            collect_system_metrics
            collect_application_metrics
            collect_business_metrics
            ;;
        "check")
            latest_system=$(ls -t $METRICS_DIR/system-*.json | head -1)
            latest_app=$(ls -t $METRICS_DIR/application-*.json | head -1)
            if [ -n "$latest_system" ] && [ -n "$latest_app" ]; then
                check_performance_thresholds "$latest_system" "$latest_app"
            else
                log_error "未找到性能指标文件，请先运行 collect"
            fi
            ;;
        "report")
            generate_performance_report "${2:-1h}"
            ;;
        "suggest")
            suggest_optimizations
            ;;
        "cleanup")
            find $METRICS_DIR -name "*.json" -mtime +7 -delete
            log_success "清理完成"
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"