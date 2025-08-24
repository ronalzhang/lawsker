#!/bin/bash

# Lawsker 服务器端部署验证脚本
# 用于在 Linux 服务器上全面检查系统运行状况和功能实现
# 注意：此脚本应在服务器上运行，不是在本地 macOS 环境

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
echo "║                 Lawsker 系统部署验证                          ║"
echo "║                    $(date '+%Y-%m-%d %H:%M:%S')                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 🔍 1. 基础系统检查
log_section "基础系统检查"

# 检查 PM2 进程状态
log_info "检查 PM2 进程状态..."
if command -v pm2 > /dev/null 2>&1; then
    pm2 status > /tmp/pm2_status.txt 2>&1
    if grep -q "lawsker-backend.*online" /tmp/pm2_status.txt && grep -q "lawsker-frontend.*online" /tmp/pm2_status.txt; then
        log_success "PM2 服务运行正常"
        ((PASSED_CHECKS++))
    else
        log_error "PM2 服务状态异常"
        ((FAILED_CHECKS++))
    fi
else
    log_error "PM2 未安装或不在 PATH 中"
    ((FAILED_CHECKS++))
fi
((TOTAL_CHECKS++))

# 检查端口占用
log_info "检查关键端口占用..."
for port in 8000 6060 80 443 3306 6379; do
    if netstat -tuln | grep -q ":$port "; then
        log_success "端口 $port 正在使用"
        ((PASSED_CHECKS++))
    else
        log_warning "端口 $port 未被占用"
    fi
    ((TOTAL_CHECKS++))
done

# 🌐 2. 网络连接测试
log_section "网络连接测试"

# 测试前端访问
log_info "测试前端服务访问..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:6060 | grep -q "200\|301\|302"; then
    log_success "前端服务响应正常"
    ((PASSED_CHECKS++))
else
    log_error "前端服务无响应"
    ((FAILED_CHECKS++))
fi
((TOTAL_CHECKS++))

# 测试后端 API
log_info "测试后端 API 访问..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health | grep -q "200"; then
    log_success "后端 API 响应正常"
    ((PASSED_CHECKS++))
else
    log_error "后端 API 无响应"
    ((FAILED_CHECKS++))
fi
((TOTAL_CHECKS++))

# 测试 HTTPS 访问
log_info "测试 HTTPS 访问..."
if curl -s -k -o /dev/null -w "%{http_code}" https://localhost | grep -q "200\|301\|302"; then
    log_success "HTTPS 访问正常"
    ((PASSED_CHECKS++))
else
    log_error "HTTPS 访问异常"
    ((FAILED_CHECKS++))
fi
((TOTAL_CHECKS++))

# 🗄️ 3. 数据库连接测试
log_section "数据库连接测试"

# 测试 MySQL 连接
log_info "测试 MySQL 数据库连接..."
if mysqladmin ping -h localhost -u root -p123abc74531 > /dev/null 2>&1; then
    log_success "MySQL 数据库连接正常"
    ((PASSED_CHECKS++))
else
    log_error "MySQL 数据库连接失败"
    ((FAILED_CHECKS++))
fi
((TOTAL_CHECKS++))

# 测试 Redis 连接
log_info "测试 Redis 连接..."
if redis-cli ping | grep -q "PONG"; then
    log_success "Redis 连接正常"
    ((PASSED_CHECKS++))
else
    log_error "Redis 连接失败"
    ((FAILED_CHECKS++))
fi
((TOTAL_CHECKS++))

# 📊 4. 应用功能测试
log_section "应用功能测试"

# 测试用户认证 API
log_info "测试用户认证 API..."
auth_response=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' \
    -w "%{http_code}")
if echo "$auth_response" | grep -q "200\|400\|401"; then
    log_success "认证 API 响应正常"
    ((PASSED_CHECKS++))
else
    log_error "认证 API 无响应"
    ((FAILED_CHECKS++))
fi
((TOTAL_CHECKS++))

# 测试文档上传 API
log_info "测试文档管理 API..."
doc_response=$(curl -s -X GET http://localhost:8000/api/v1/documents \
    -w "%{http_code}")
if echo "$doc_response" | grep -q "200\|401"; then
    log_success "文档管理 API 响应正常"
    ((PASSED_CHECKS++))
else
    log_error "文档管理 API 无响应"
    ((FAILED_CHECKS++))
fi
((TOTAL_CHECKS++))

# 📝 5. 日志检查
log_section "系统日志检查"

# 检查后端错误日志
log_info "检查后端错误日志..."
if [ -f ~/.pm2/logs/lawsker-backend-error.log ]; then
    error_count=$(tail -100 ~/.pm2/logs/lawsker-backend-error.log | grep -i "error\|exception\|traceback" | wc -l)
    if [ $error_count -lt 5 ]; then
        log_success "后端错误日志正常 (错误数: $error_count)"
        ((PASSED_CHECKS++))
    else
        log_warning "后端存在较多错误 (错误数: $error_count)"
    fi
else
    log_error "后端错误日志文件不存在"
    ((FAILED_CHECKS++))
fi
((TOTAL_CHECKS++))

# 检查前端错误日志
log_info "检查前端错误日志..."
if [ -f ~/.pm2/logs/lawsker-frontend-error.log ]; then
    error_count=$(tail -100 ~/.pm2/logs/lawsker-frontend-error.log | grep -i "error\|exception" | wc -l)
    if [ $error_count -lt 5 ]; then
        log_success "前端错误日志正常 (错误数: $error_count)"
        ((PASSED_CHECKS++))
    else
        log_warning "前端存在较多错误 (错误数: $error_count)"
    fi
else
    log_error "前端错误日志文件不存在"
    ((FAILED_CHECKS++))
fi
((TOTAL_CHECKS++))

# 🔒 6. 安全检查
log_section "安全配置检查"

# 检查 SSL 证书
log_info "检查 SSL 证书..."
if [ -f /etc/letsencrypt/live/lawsker.com/fullchain.pem ]; then
    cert_expiry=$(openssl x509 -enddate -noout -in /etc/letsencrypt/live/lawsker.com/fullchain.pem | cut -d= -f2)
    log_success "SSL 证书存在，到期时间: $cert_expiry"
    ((PASSED_CHECKS++))
else
    log_error "SSL 证书文件不存在"
    ((FAILED_CHECKS++))
fi
((TOTAL_CHECKS++))

# 检查防火墙状态
log_info "检查防火墙状态..."
if command -v ufw > /dev/null 2>&1; then
    if ufw status | grep -q "Status: active"; then
        log_success "防火墙已启用"
        ((PASSED_CHECKS++))
    else
        log_warning "防火墙未启用"
    fi
else
    log_warning "UFW 防火墙未安装"
fi
((TOTAL_CHECKS++))

# 💾 7. 系统资源检查
log_section "系统资源检查"

# 检查磁盘空间
log_info "检查磁盘空间..."
disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $disk_usage -lt 80 ]; then
    log_success "磁盘空间充足 (使用率: ${disk_usage}%)"
    ((PASSED_CHECKS++))
else
    log_warning "磁盘空间不足 (使用率: ${disk_usage}%)"
fi
((TOTAL_CHECKS++))

# 检查内存使用
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
    log_warning "free 命令不可用 (非 Linux 系统)"
fi
((TOTAL_CHECKS++))

# 📈 8. 性能检查
log_section "性能检查"

# 检查 API 响应时间
log_info "检查 API 响应时间..."
response_time=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:8000/api/v1/health)
response_time_ms=$(echo "$response_time * 1000" | bc)
if (( $(echo "$response_time < 2.0" | bc -l) )); then
    log_success "API 响应时间正常 (${response_time_ms}ms)"
    ((PASSED_CHECKS++))
else
    log_warning "API 响应时间较慢 (${response_time_ms}ms)"
fi
((TOTAL_CHECKS++))

# 🎯 9. 新功能验证
log_section "新功能验证"

# 检查新增的部署工具
log_info "检查部署工具..."
deployment_tools=(
    "backend/deployment/deployment_orchestrator.py"
    "backend/deployment/monitoring_configurator.py"
    "backend/deployment/ssl_configurator.py"
    "backend/deployment/system_monitor.py"
)

for tool in "${deployment_tools[@]}"; do
    if [ -f "$tool" ]; then
        log_success "部署工具存在: $(basename $tool)"
        ((PASSED_CHECKS++))
    else
        log_error "部署工具缺失: $(basename $tool)"
        ((FAILED_CHECKS++))
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
        echo -e "${GREEN}🎉 系统运行状况优秀！${NC}"
    elif (( $(echo "$success_rate >= 70" | bc -l) )); then
        echo -e "${YELLOW}⚠️  系统运行状况良好，但需要关注一些问题${NC}"
    else
        echo -e "${RED}🚨 系统存在严重问题，需要立即处理！${NC}"
    fi
fi

# 生成详细报告
echo -e "\n${BLUE}📝 生成详细报告...${NC}"
{
    echo "Lawsker 系统验证报告"
    echo "生成时间: $(date)"
    echo "=========================="
    echo "总检查项目: $TOTAL_CHECKS"
    echo "通过检查: $PASSED_CHECKS"
    echo "失败检查: $FAILED_CHECKS"
    echo "成功率: ${success_rate}%"
    echo ""
    echo "PM2 进程状态:"
    pm2 status
    echo ""
    echo "最近的错误日志:"
    if [ -f ~/.pm2/logs/lawsker-backend-error.log ]; then
        echo "=== 后端错误日志 ==="
        tail -20 ~/.pm2/logs/lawsker-backend-error.log
    fi
    if [ -f ~/.pm2/logs/lawsker-frontend-error.log ]; then
        echo "=== 前端错误日志 ==="
        tail -20 ~/.pm2/logs/lawsker-frontend-error.log
    fi
} > /tmp/lawsker_verification_report.txt

echo -e "${GREEN}✅ 详细报告已保存到: /tmp/lawsker_verification_report.txt${NC}"

# 清理临时文件
rm -f /tmp/pm2_status.txt

exit 0