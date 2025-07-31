#!/bin/bash

# 灰度发布管理脚本
# 支持蓝绿部署、滚动更新和金丝雀发布

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

# 配置文件路径
CONFIG_FILE="config/canary-config.yml"
DEPLOYMENT_LOG="logs/canary-deployment.log"

# 创建日志目录
mkdir -p logs

# 记录部署日志
log_deployment() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$DEPLOYMENT_LOG"
}

# 检查配置文件
check_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "配置文件不存在: $CONFIG_FILE"
        exit 1
    fi
    log_success "配置文件检查通过"
}

# 获取当前部署状态
get_deployment_status() {
    if [ -f "deployment-status.json" ]; then
        cat deployment-status.json
    else
        echo '{"phase": "none", "percentage": 0, "status": "not_started"}'
    fi
}

# 更新部署状态
update_deployment_status() {
    local phase=$1
    local percentage=$2
    local status=$3
    
    cat > deployment-status.json << EOF
{
    "phase": "$phase",
    "percentage": $percentage,
    "status": "$status",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "version": "${VERSION:-latest}"
}
EOF
    
    log_deployment "状态更新: $phase ($percentage%) - $status"
}

# 检查系统健康状态
check_health() {
    log_info "检查系统健康状态..."
    
    # 检查API健康状态
    if ! curl -f -s http://localhost/health > /dev/null; then
        log_error "API健康检查失败"
        return 1
    fi
    
    # 检查数据库连接
    if ! docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U lawsker_user > /dev/null 2>&1; then
        log_error "数据库连接检查失败"
        return 1
    fi
    
    # 检查Redis连接
    if ! docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping | grep -q "PONG"; then
        log_error "Redis连接检查失败"
        return 1
    fi
    
    log_success "系统健康检查通过"
    return 0
}

# 获取监控指标
get_metrics() {
    local metric_name=$1
    local time_range=${2:-"5m"}
    
    # 从Prometheus获取指标
    local prometheus_url="http://localhost:9090"
    local query=""
    
    case $metric_name in
        "error_rate")
            query="rate(http_requests_total{status=~\"5..\"}[${time_range}]) / rate(http_requests_total[${time_range}])"
            ;;
        "response_time_p95")
            query="histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[${time_range}]))"
            ;;
        "availability")
            query="up"
            ;;
        *)
            log_error "未知的监控指标: $metric_name"
            return 1
            ;;
    esac
    
    # 查询Prometheus
    local result=$(curl -s "${prometheus_url}/api/v1/query?query=${query}" | jq -r '.data.result[0].value[1] // "0"')
    echo "$result"
}

# 检查回滚条件
check_rollback_conditions() {
    log_info "检查回滚条件..."
    
    # 错误率检查
    local error_rate=$(get_metrics "error_rate")
    if (( $(echo "$error_rate > 0.1" | bc -l) )); then
        log_warning "错误率过高: $error_rate"
        return 1
    fi
    
    # 响应时间检查
    local response_time=$(get_metrics "response_time_p95")
    if (( $(echo "$response_time > 5" | bc -l) )); then
        log_warning "响应时间过长: ${response_time}s"
        return 1
    fi
    
    # 可用性检查
    local availability=$(get_metrics "availability")
    if (( $(echo "$availability < 0.99" | bc -l) )); then
        log_warning "可用性过低: $availability"
        return 1
    fi
    
    log_success "监控指标正常"
    return 0
}

# 发送通知
send_notification() {
    local event=$1
    local message=$2
    
    log_info "发送通知: $event"
    
    # 邮件通知
    if command -v mail &> /dev/null; then
        echo "$message" | mail -s "Lawsker灰度发布通知: $event" devops@lawsker.com
    fi
    
    # Slack通知（如果配置了webhook）
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"Lawsker灰度发布通知: $event\\n$message\"}" \
            "$SLACK_WEBHOOK_URL"
    fi
    
    log_deployment "通知已发送: $event - $message"
}

# 配置流量分割
configure_traffic_split() {
    local percentage=$1
    local version=${2:-"new"}
    
    log_info "配置流量分割: $percentage% -> $version"
    
    # 更新NGINX配置实现流量分割
    cat > nginx/conf.d/traffic-split.conf << EOF
# 流量分割配置
upstream backend_old {
    server backend-old:8000 weight=$((100 - percentage));
}

upstream backend_new {
    server backend-new:8000 weight=$percentage;
}

upstream backend_split {
    server backend-old:8000 weight=$((100 - percentage));
    server backend-new:8000 weight=$percentage;
}
EOF
    
    # 重新加载NGINX配置
    docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
    
    log_success "流量分割配置完成: $percentage%"
}

# 部署新版本
deploy_new_version() {
    local version=$1
    
    log_info "部署新版本: $version"
    
    # 构建新版本镜像
    docker build -f backend/Dockerfile.prod -t lawsker/backend:$version backend/
    docker build -f frontend-vue/Dockerfile.prod -t lawsker/frontend-user:$version frontend-vue/
    docker build -f frontend-admin/Dockerfile.prod -t lawsker/frontend-admin:$version frontend-admin/
    
    # 启动新版本容器（蓝绿部署）
    docker-compose -f docker-compose.canary.yml up -d
    
    # 等待服务启动
    sleep 30
    
    # 健康检查
    if ! check_health; then
        log_error "新版本健康检查失败"
        return 1
    fi
    
    log_success "新版本部署完成: $version"
}

# 执行灰度发布阶段
execute_phase() {
    local phase_name=$1
    local percentage=$2
    local duration=$3
    
    log_info "开始执行阶段: $phase_name ($percentage%)"
    
    # 更新部署状态
    update_deployment_status "$phase_name" "$percentage" "in_progress"
    
    # 配置流量分割
    configure_traffic_split "$percentage"
    
    # 发送开始通知
    send_notification "phase_start" "开始执行灰度发布阶段: $phase_name ($percentage%)"
    
    # 监控阶段
    local start_time=$(date +%s)
    local duration_seconds=$(echo "$duration" | sed 's/h/*3600/g; s/m/*60/g; s/s//g' | bc)
    
    while true; do
        current_time=$(date +%s)
        elapsed=$((current_time - start_time))
        
        # 检查是否达到持续时间
        if [ $elapsed -ge $duration_seconds ]; then
            log_info "阶段 $phase_name 持续时间已达到"
            break
        fi
        
        # 检查回滚条件
        if ! check_rollback_conditions; then
            log_warning "触发回滚条件，开始回滚"
            rollback_deployment
            return 1
        fi
        
        # 等待下次检查
        sleep 60
    done
    
    # 更新状态为完成
    update_deployment_status "$phase_name" "$percentage" "completed"
    
    # 发送完成通知
    send_notification "phase_complete" "灰度发布阶段完成: $phase_name ($percentage%)"
    
    log_success "阶段 $phase_name 执行完成"
}

# 回滚部署
rollback_deployment() {
    log_warning "开始回滚部署..."
    
    # 更新状态
    update_deployment_status "rollback" "0" "in_progress"
    
    # 将流量切回旧版本
    configure_traffic_split "0" "old"
    
    # 停止新版本容器
    docker-compose -f docker-compose.canary.yml down
    
    # 发送回滚通知
    send_notification "rollback_triggered" "灰度发布已回滚到旧版本"
    
    # 更新状态
    update_deployment_status "rollback" "0" "completed"
    
    log_success "回滚完成"
}

# 完成部署
complete_deployment() {
    log_info "完成灰度发布..."
    
    # 将所有流量切换到新版本
    configure_traffic_split "100" "new"
    
    # 停止旧版本容器
    docker-compose -f docker-compose.prod.yml down
    
    # 将新版本重命名为生产版本
    docker tag lawsker/backend:${VERSION} lawsker/backend:latest
    docker tag lawsker/frontend-user:${VERSION} lawsker/frontend-user:latest
    docker tag lawsker/frontend-admin:${VERSION} lawsker/frontend-admin:latest
    
    # 启动生产环境
    docker-compose -f docker-compose.prod.yml up -d
    
    # 更新状态
    update_deployment_status "production" "100" "completed"
    
    # 发送完成通知
    send_notification "deployment_complete" "灰度发布已完成，所有用户已迁移到新版本"
    
    log_success "灰度发布完成"
}

# 获取用户反馈
collect_feedback() {
    log_info "收集用户反馈..."
    
    # 创建反馈收集API端点
    cat > backend/app/api/v1/endpoints/feedback.py << 'EOF'
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.models.feedback import Feedback
from app.core.auth import get_current_user

router = APIRouter()

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """提交用户反馈"""
    db_feedback = Feedback(
        user_id=current_user.id,
        type=feedback.type,
        content=feedback.content,
        rating=feedback.rating,
        deployment_phase=feedback.deployment_phase
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    return db_feedback

@router.get("/feedback/stats")
async def get_feedback_stats(db: Session = Depends(get_db)):
    """获取反馈统计"""
    total_feedback = db.query(Feedback).count()
    avg_rating = db.query(func.avg(Feedback.rating)).scalar() or 0
    
    return {
        "total_feedback": total_feedback,
        "average_rating": round(avg_rating, 2),
        "feedback_by_phase": db.query(
            Feedback.deployment_phase,
            func.count(Feedback.id),
            func.avg(Feedback.rating)
        ).group_by(Feedback.deployment_phase).all()
    }
EOF
    
    log_success "用户反馈收集系统已配置"
}

# 生成部署报告
generate_report() {
    log_info "生成部署报告..."
    
    local report_file="reports/canary-deployment-$(date +%Y%m%d_%H%M%S).md"
    mkdir -p reports
    
    cat > "$report_file" << EOF
# 灰度发布报告

## 基本信息
- 部署时间: $(date)
- 版本: ${VERSION:-latest}
- 部署策略: 灰度发布

## 部署阶段
$(cat deployment-status.json | jq -r '.')

## 监控指标
- 错误率: $(get_metrics "error_rate")
- 响应时间(P95): $(get_metrics "response_time_p95")s
- 可用性: $(get_metrics "availability")

## 系统状态
- API健康状态: $(curl -f -s http://localhost/health && echo "正常" || echo "异常")
- 数据库状态: $(docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U lawsker_user && echo "正常" || echo "异常")
- Redis状态: $(docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping)

## 用户反馈
$(curl -s http://localhost/api/v1/feedback/stats | jq -r '.')

## 部署日志
\`\`\`
$(tail -50 "$DEPLOYMENT_LOG")
\`\`\`
EOF
    
    log_success "部署报告已生成: $report_file"
}

# 显示帮助信息
show_help() {
    echo "灰度发布管理脚本"
    echo ""
    echo "使用方法: $0 <command> [options]"
    echo ""
    echo "命令:"
    echo "  start <version>      开始灰度发布"
    echo "  status               查看部署状态"
    echo "  next                 进入下一阶段"
    echo "  rollback             回滚到旧版本"
    echo "  complete             完成部署"
    echo "  monitor              监控部署状态"
    echo "  feedback             收集用户反馈"
    echo "  report               生成部署报告"
    echo "  help                 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start v1.1.0      # 开始灰度发布版本v1.1.0"
    echo "  $0 status            # 查看当前部署状态"
    echo "  $0 next              # 进入下一个发布阶段"
    echo "  $0 rollback          # 回滚部署"
}

# 主函数
main() {
    VERSION=${2:-latest}
    
    case "${1:-help}" in
        "start")
            check_config
            log_info "开始灰度发布版本: $VERSION"
            deploy_new_version "$VERSION"
            execute_phase "alpha" 5 "24h"
            ;;
        "status")
            get_deployment_status | jq '.'
            ;;
        "next")
            current_status=$(get_deployment_status)
            current_phase=$(echo "$current_status" | jq -r '.phase')
            
            case "$current_phase" in
                "alpha")
                    execute_phase "beta" 20 "48h"
                    ;;
                "beta")
                    execute_phase "gamma" 50 "72h"
                    ;;
                "gamma")
                    complete_deployment
                    ;;
                *)
                    log_error "无法确定下一阶段"
                    ;;
            esac
            ;;
        "rollback")
            rollback_deployment
            ;;
        "complete")
            complete_deployment
            ;;
        "monitor")
            while true; do
                check_rollback_conditions
                sleep 60
            done
            ;;
        "feedback")
            collect_feedback
            ;;
        "report")
            generate_report
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"