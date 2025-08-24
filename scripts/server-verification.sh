#!/bin/bash

# Lawsker 服务器端验证脚本
# 此脚本应该在生产服务器上运行，用于检查系统状态

# 🎨 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 📊 统计变量
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# 🔧 辅助函数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED_CHECKS++))
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED_CHECKS++))
}

log_section() {
    echo -e "\n${PURPLE}🔍 $1${NC}"
    echo "=================================================="
}

check_result() {
    ((TOTAL_CHECKS++))
    if [ $1 -eq 0 ]; then
        log_success "$2"
    else
        log_error "$3"
    fi
}

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                Lawsker 服务器端验证                           ║"
echo "║                    $(date '+%Y-%m-%d %H:%M:%S')                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 🔍 1. 系统环境检查
log_section "系统环境检查"

log_info "操作系统信息..."
if [ -f /etc/os-release ]; then
    os_info=$(grep PRETTY_NAME /etc/os-release | cut -d'"' -f2)
    log_success "操作系统: $os_info"
    ((PASSED_CHECKS++))
else
    log_warning "无法获取操作系统信息"
fi
((TOTAL_CHECKS++))

log_info "系统负载..."
load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
log_success "系统负载: $load_avg"
((PASSED_CHECKS++))
((TOTAL_CHECKS++))

# 🔍 2. PM2 进程检查
log_section "PM2 进程检查"

if command -v pm2 > /dev/null 2>&1; then
    log_info "检查 PM2 进程状态..."
    pm2 status > /tmp/pm2_status.txt 2>&1
    
    # 检查后端服务
    if grep -q "lawsker-backend.*online" /tmp/pm2_status.txt; then
        log_success "后端服务运行正常"
        ((PASSED_CHECKS++))
    else
        log_error "后端服务状态异常"
        ((FAILED_CHECKS++))
    fi
    ((TOTAL_CHECKS++))
    
    # 检查前端服务
    if grep -q "lawsker-frontend.*online" /tmp/pm2_status.txt; then
        log_success "前端服务运行正常"
        ((PASSED_CHECKS++))
    else
        log_error "前端服务状态异常"
        ((FAILED_CHECKS++))
    fi
    ((TOTAL_CHECKS++))
    
    # 显示 PM2 状态
    echo -e "${YELLOW}PM2 进程详情:${NC}"
    pm2 status
else
    log_error "PM2 未安装"
    ((FAILED_CHECKS++))
    ((TOTAL_CHECKS++))
fi

# 🔍 3. 端口检查
log_section "端口检查"

ports=(80 443 8000 6060 3306 6379)
for port in "${ports[@]}"; do
    log_info "检查端口 $port..."
    if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
        log_success "端口 $port 正在监听"
        ((PASSED_CHECKS++))
    else
        log_warning "端口 $port 未被占用"
    fi
    ((TOTAL_CHECKS++))
done

# 🔍 4. 数据库连接检查
log_section "数据库连接检查"

# MySQL 检查
log_info "检查 MySQL 连接..."
if command -v mysqladmin > /dev/null 2>&1; then
    if mysqladmin ping -h localhost -u root -p123abc74531 > /dev/null 2>&1; then
        log_success "MySQL 连接正常"
        ((PASSED_CHECKS++))
    else
        log_error "MySQL 连接失败"
        ((FAILED_CHECKS++))
    fi
else
    log_warning "mysqladmin 命令不存在"
fi
((TOTAL_CHECKS++))

# Redis 检查
log_info "检查 Redis 连接..."
if command -v redis-cli > /dev/null 2>&1; then
    if redis-cli ping 2>/dev/null | grep -q "PONG"; then
        log_success "Redis 连接正常"
        ((PASSED_CHECKS++))
    else
        log_error "Redis 连接失败"
        ((FAILED_CHECKS++))
    fi
else
    log_warning "redis-cli 命令不存在"
fi
((TOTAL_CHECKS++))

# 🔍 5. 网络服务测试
log_section "网络服务测试"

# 测试本地服务
services=(
    "http://localhost:6060:前端服务"
    "http://localhost:8000/api/v1/health:后端API"
    "https://localhost:HTTPS服务"
)

for service_info in "${services[@]}"; do
    IFS=':' read -r url desc <<< "$service_info"
    log_info "测试 $desc..."
    
    if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url" | grep -q "200\|301\|302"; then
        log_success "$desc 响应正常"
        ((PASSED_CHECKS++))
    else
        log_error "$desc 无响应"
        ((FAILED_CHECKS++))
    fi
    ((TOTAL_CHECKS++))
done

# 🔍 6. SSL 证书检查
log_section "SSL 证书检查"

log_info "检查 SSL 证书文件..."
if [ -f /etc/letsencrypt/live/lawsker.com/fullchain.pem ]; then
    cert_expiry=$(openssl x509 -enddate -noout -in /etc/letsencrypt/live/lawsker.com/fullchain.pem | cut -d= -f2)
    log_success "SSL 证书存在，到期时间: $cert_expiry"
    ((PASSED_CHECKS++))
    
    # 检查证书是否即将过期 (30天内)
    expiry_timestamp=$(date -d "$cert_expiry" +%s 2>/dev/null)
    current_timestamp=$(date +%s)
    days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
    
    if [ $days_until_expiry -gt 30 ]; then
        log_success "SSL 证书有效期充足 ($days_until_expiry 天)"
        ((PASSED_CHECKS++))
    else
        log_warning "SSL 证书即将过期 ($days_until_expiry 天)"
    fi
    ((TOTAL_CHECKS++))
else
    log_error "SSL 证书文件不存在"
    ((FAILED_CHECKS++))
fi
((TOTAL_CHECKS++))

# 🔍 7. 系统资源检查
log_section "系统资源检查"

# 磁盘空间
log_info "检查磁盘空间..."
disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $disk_usage -lt 80 ]; then
    log_success "磁盘空间充足 (使用率: ${disk_usage}%)"
    ((PASSED_CHECKS++))
else
    log_warning "磁盘空间不足 (使用率: ${disk_usage}%)"
fi
((TOTAL_CHECKS++))

# 内存使用
log_info "检查内存使用..."
if command -v free > /dev/null 2>&1; then
    memory_usage=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')
    memory_usage_int=${memory_usage%.*}
    if [ $memory_usage_int -lt 80 ]; then
        log_success "内存使用正常 (使用率: ${memory_usage}%)"
        ((PASSED_CHECKS++))
    else
        log_warning "内存使用较高 (使用率: ${memory_usage}%)"
    fi
else
    log_warning "free 命令不可用"
fi
((TOTAL_CHECKS++))

# 🔍 8. 日志检查
log_section "应用日志检查"

# 后端日志
log_info "检查后端日志..."
if [ -f ~/.pm2/logs/lawsker-backend-error.log ]; then
    error_count=$(tail -100 ~/.pm2/logs/lawsker-backend-error.log | grep -i "error\|exception\|traceback" | wc -l)
    if [ $error_count -lt 5 ]; then
        log_success "后端错误日志正常 (错误数: $error_count)"
        ((PASSED_CHECKS++))
    else
        log_warning "后端存在较多错误 (错误数: $error_count)"
    fi
    
    echo -e "${YELLOW}最近的后端日志:${NC}"
    tail -10 ~/.pm2/logs/lawsker-backend-error.log
else
    log_error "后端错误日志文件不存在"
    ((FAILED_CHECKS++))
fi
((TOTAL_CHECKS++))

# 前端日志
log_info "检查前端日志..."
if [ -f ~/.pm2/logs/lawsker-frontend-error.log ]; then
    error_count=$(tail -100 ~/.pm2/logs/lawsker-frontend-error.log | grep -i "error\|exception" | wc -l)
    if [ $error_count -lt 5 ]; then
        log_success "前端错误日志正常 (错误数: $error_count)"
        ((PASSED_CHECKS++))
    else
        log_warning "前端存在较多错误 (错误数: $error_count)"
    fi
    
    echo -e "${YELLOW}最近的前端日志:${NC}"
    tail -10 ~/.pm2/logs/lawsker-frontend-error.log
else
    log_error "前端错误日志文件不存在"
    ((FAILED_CHECKS++))
fi
((TOTAL_CHECKS++))

# 🔍 9. Nginx 检查
log_section "Nginx 检查"

log_info "检查 Nginx 状态..."
if systemctl is-active --quiet nginx 2>/dev/null; then
    log_success "Nginx 服务运行正常"
    ((PASSED_CHECKS++))
elif service nginx status > /dev/null 2>&1; then
    log_success "Nginx 服务运行正常"
    ((PASSED_CHECKS++))
else
    log_error "Nginx 服务未运行"
    ((FAILED_CHECKS++))
fi
((TOTAL_CHECKS++))

# 检查 Nginx 配置
log_info "检查 Nginx 配置..."
if nginx -t > /dev/null 2>&1; then
    log_success "Nginx 配置文件语法正确"
    ((PASSED_CHECKS++))
else
    log_error "Nginx 配置文件语法错误"
    ((FAILED_CHECKS++))
fi
((TOTAL_CHECKS++))

# 🔍 10. 系统服务检查
log_section "系统服务检查"

services=("mysql" "redis-server" "nginx")
for service in "${services[@]}"; do
    log_info "检查 $service 服务..."
    if systemctl is-active --quiet $service 2>/dev/null; then
        log_success "$service 服务运行正常"
        ((PASSED_CHECKS++))
    elif service $service status > /dev/null 2>&1; then
        log_success "$service 服务运行正常"
        ((PASSED_CHECKS++))
    else
        log_warning "$service 服务状态未知或未运行"
    fi
    ((TOTAL_CHECKS++))
done

# 📊 最终报告
echo -e "\n${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                        验证报告                               ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║ 总检查项目: $TOTAL_CHECKS                                          ║"
echo "║ 通过检查: $PASSED_CHECKS                                           ║"
echo "║ 失败检查: $FAILED_CHECKS                                           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 计算成功率
if [ $TOTAL_CHECKS -gt 0 ]; then
    success_rate=$(echo "scale=1; $PASSED_CHECKS * 100 / $TOTAL_CHECKS" | bc)
    echo -e "${BLUE}📊 系统健康度: ${success_rate}%${NC}"
    
    if (( $(echo "$success_rate >= 90" | bc -l) )); then
        echo -e "${GREEN}🎉 服务器运行状况优秀！${NC}"
    elif (( $(echo "$success_rate >= 70" | bc -l) )); then
        echo -e "${YELLOW}⚠️  服务器运行状况良好，但需要关注一些问题${NC}"
    else
        echo -e "${RED}🚨 服务器存在严重问题，需要立即处理！${NC}"
    fi
fi

# 生成详细报告
echo -e "\n${BLUE}📝 生成详细报告...${NC}"
{
    echo "Lawsker 服务器验证报告"
    echo "生成时间: $(date)"
    echo "服务器: $(hostname)"
    echo "=========================="
    echo "总检查项目: $TOTAL_CHECKS"
    echo "通过检查: $PASSED_CHECKS"
    echo "失败检查: $FAILED_CHECKS"
    echo "成功率: ${success_rate}%"
    echo ""
    echo "系统信息:"
    uname -a
    echo ""
    if command -v pm2 > /dev/null 2>&1; then
        echo "PM2 进程状态:"
        pm2 status
    fi
    echo ""
    echo "磁盘使用:"
    df -h
    echo ""
    echo "内存使用:"
    free -h 2>/dev/null || echo "free 命令不可用"
    echo ""
    echo "网络端口:"
    netstat -tuln 2>/dev/null | grep -E ':(80|443|8000|6060|3306|6379) ' || ss -tuln 2>/dev/null | grep -E ':(80|443|8000|6060|3306|6379) '
} > /tmp/lawsker_server_verification_report.txt

echo -e "${GREEN}✅ 详细报告已保存到: /tmp/lawsker_server_verification_report.txt${NC}"

# 清理临时文件
rm -f /tmp/pm2_status.txt

echo -e "\n${YELLOW}💡 使用建议:${NC}"
echo -e "${YELLOW}   - 定期运行此脚本监控服务器状态${NC}"
echo -e "${YELLOW}   - 关注错误日志中的异常信息${NC}"
echo -e "${YELLOW}   - 及时处理资源使用过高的问题${NC}"
echo -e "${YELLOW}   - 确保 SSL 证书及时续期${NC}"

exit 0