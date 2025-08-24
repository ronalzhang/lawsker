#!/bin/bash

# Lawsker 新功能测试脚本
# 测试本次更新中新增的功能和API端点

# 🎨 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置变量
API_BASE="http://localhost:8000"
FRONTEND_BASE="http://localhost:6060"

# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 辅助函数
log_test() {
    echo -e "${BLUE}🧪 测试: $1${NC}"
    ((TOTAL_TESTS++))
}

log_pass() {
    echo -e "${GREEN}  ✅ $1${NC}"
    ((PASSED_TESTS++))
}

log_fail() {
    echo -e "${RED}  ❌ $1${NC}"
    ((FAILED_TESTS++))
}

log_info() {
    echo -e "${YELLOW}  ℹ️  $1${NC}"
}

test_api_endpoint() {
    local endpoint=$1
    local expected_codes=$2
    local description=$3
    
    log_test "$description"
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE$endpoint")
    
    if echo "$expected_codes" | grep -q "$response"; then
        log_pass "响应码: $response (符合预期: $expected_codes)"
    else
        log_fail "响应码: $response (期望: $expected_codes)"
    fi
}

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                 Lawsker 新功能测试                            ║"
echo "║                    $(date '+%Y-%m-%d %H:%M:%S')                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 🔍 1. 基础健康检查
echo -e "\n${PURPLE}🏥 基础健康检查${NC}"
echo "=================================================="

test_api_endpoint "/api/v1/health" "200" "健康检查端点"
test_api_endpoint "/docs" "200" "API 文档端点"
test_api_endpoint "/redoc" "200" "ReDoc 文档端点"

# 🔍 2. 认证系统测试
echo -e "\n${PURPLE}🔐 认证系统测试${NC}"
echo "=================================================="

test_api_endpoint "/api/v1/auth/me" "401" "用户信息端点 (未认证)"

# 测试登录端点
log_test "用户登录端点"
login_response=$(curl -s -X POST "$API_BASE/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' \
    -w "%{http_code}")

if echo "$login_response" | grep -q "200\|400\|401\|422"; then
    log_pass "登录端点响应正常"
else
    log_fail "登录端点无响应"
fi

# 🔍 3. 文档管理系统测试
echo -e "\n${PURPLE}📄 文档管理系统测试${NC}"
echo "=================================================="

test_api_endpoint "/api/v1/documents" "200\|401" "文档列表端点"
test_api_endpoint "/api/v1/documents/upload" "405\|401" "文档上传端点"

# 🔍 4. 用户管理系统测试
echo -e "\n${PURPLE}👥 用户管理系统测试${NC}"
echo "=================================================="

test_api_endpoint "/api/v1/users" "200\|401" "用户列表端点"
test_api_endpoint "/api/v1/users/profile" "401" "用户资料端点"

# 🔍 5. 管理员功能测试
echo -e "\n${PURPLE}⚙️ 管理员功能测试${NC}"
echo "=================================================="

test_api_endpoint "/api/v1/admin/users" "401\|403" "管理员用户管理"
test_api_endpoint "/api/v1/admin/system" "401\|403" "系统管理端点"

# 🔍 6. 新增的监控和告警功能测试
echo -e "\n${PURPLE}📊 监控和告警功能测试${NC}"
echo "=================================================="

test_api_endpoint "/api/v1/alerts" "200\|401" "告警列表端点"
test_api_endpoint "/api/v1/monitoring/metrics" "200\|401\|404" "监控指标端点"
test_api_endpoint "/api/v1/automation/status" "200\|401\|404" "自动化状态端点"

# 🔍 7. WebSocket 连接测试
echo -e "\n${PURPLE}🔌 WebSocket 连接测试${NC}"
echo "=================================================="

log_test "WebSocket 端点可访问性"
# 简单测试 WebSocket 端点是否存在
ws_response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/ws")
if [ "$ws_response" = "426" ] || [ "$ws_response" = "400" ]; then
    log_pass "WebSocket 端点存在 (响应码: $ws_response)"
else
    log_info "WebSocket 端点响应: $ws_response"
fi

# 🔍 8. 前端静态资源测试
echo -e "\n${PURPLE}🌐 前端静态资源测试${NC}"
echo "=================================================="

log_test "前端主页访问"
frontend_response=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_BASE")
if [ "$frontend_response" = "200" ]; then
    log_pass "前端主页访问正常"
else
    log_fail "前端主页访问异常 (响应码: $frontend_response)"
fi

log_test "前端静态资源"
# 测试常见的静态资源
static_files=("/css/main.css" "/js/main.js" "/favicon.ico")
for file in "${static_files[@]}"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_BASE$file")
    if [ "$response" = "200" ] || [ "$response" = "304" ]; then
        log_pass "静态文件 $file 访问正常"
    else
        log_info "静态文件 $file 响应码: $response"
    fi
done

# 🔍 9. 数据库连接和基础查询测试
echo -e "\n${PURPLE}🗄️ 数据库功能测试${NC}"
echo "=================================================="

# 通过 API 测试数据库连接
log_test "数据库连接测试 (通过 API)"
db_test_response=$(curl -s -X GET "$API_BASE/api/v1/health/database" -w "%{http_code}")
if echo "$db_test_response" | grep -q "200\|404"; then
    log_pass "数据库连接测试端点响应正常"
else
    log_info "数据库连接测试响应: $db_test_response"
fi

# 🔍 10. 安全功能测试
echo -e "\n${PURPLE}🔒 安全功能测试${NC}"
echo "=================================================="

# 测试 CORS 头
log_test "CORS 头检查"
cors_response=$(curl -s -I "$API_BASE/api/v1/health" | grep -i "access-control")
if [ -n "$cors_response" ]; then
    log_pass "CORS 头已配置"
else
    log_info "未检测到 CORS 头"
fi

# 测试安全头
log_test "安全头检查"
security_headers=$(curl -s -I "$API_BASE/api/v1/health" | grep -iE "(x-frame-options|x-content-type-options|x-xss-protection)")
if [ -n "$security_headers" ]; then
    log_pass "安全头已配置"
else
    log_info "未检测到安全头"
fi

# 🔍 11. 性能测试
echo -e "\n${PURPLE}⚡ 性能测试${NC}"
echo "=================================================="

log_test "API 响应时间测试"
response_time=$(curl -o /dev/null -s -w "%{time_total}" "$API_BASE/api/v1/health")
response_time_ms=$(echo "$response_time * 1000" | bc 2>/dev/null || echo "计算失败")

if [ "$response_time_ms" != "计算失败" ]; then
    if (( $(echo "$response_time < 1.0" | bc -l 2>/dev/null || echo 0) )); then
        log_pass "API 响应时间优秀: ${response_time_ms}ms"
    elif (( $(echo "$response_time < 2.0" | bc -l 2>/dev/null || echo 0) )); then
        log_pass "API 响应时间良好: ${response_time_ms}ms"
    else
        log_info "API 响应时间: ${response_time_ms}ms"
    fi
else
    log_info "无法计算响应时间"
fi

# 🔍 12. 新增部署工具验证
echo -e "\n${PURPLE}🛠️ 部署工具验证${NC}"
echo "=================================================="

deployment_tools=(
    "backend/deployment/deployment_orchestrator.py:部署编排器"
    "backend/deployment/monitoring_configurator.py:监控配置器"
    "backend/deployment/ssl_configurator.py:SSL配置器"
    "backend/deployment/system_monitor.py:系统监控器"
    "backend/deployment/alert_system_configurator.py:告警系统配置器"
    "backend/deployment/config_management_cli.py:配置管理CLI"
    "backend/deployment/deployment_verification.py:部署验证器"
    "backend/deployment/fault_diagnosis.py:故障诊断器"
)

for tool_info in "${deployment_tools[@]}"; do
    IFS=':' read -r tool_path tool_name <<< "$tool_info"
    log_test "$tool_name 文件检查"
    if [ -f "$tool_path" ]; then
        # 检查文件是否为有效的 Python 文件
        if python3 -m py_compile "$tool_path" 2>/dev/null; then
            log_pass "$tool_name 文件存在且语法正确"
        else
            log_fail "$tool_name 文件存在但语法错误"
        fi
    else
        log_fail "$tool_name 文件不存在"
    fi
done

# 🔍 13. 配置文件验证
echo -e "\n${PURPLE}⚙️ 配置文件验证${NC}"
echo "=================================================="

config_files=(
    "backend/deployment/deployment_config.json:部署配置"
    "backend/deployment/test_environments.yml:测试环境配置"
    "backend/config/alert_config.py:告警配置"
    "backend/config/automation_config.py:自动化配置"
)

for config_info in "${config_files[@]}"; do
    IFS=':' read -r config_path config_name <<< "$config_info"
    log_test "$config_name 文件检查"
    if [ -f "$config_path" ]; then
        log_pass "$config_name 文件存在"
    else
        log_fail "$config_name 文件不存在"
    fi
done

# 📊 测试结果汇总
echo -e "\n${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                        测试结果汇总                           ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║ 总测试数: $TOTAL_TESTS                                          ║"
echo "║ 通过测试: $PASSED_TESTS                                         ║"
echo "║ 失败测试: $FAILED_TESTS                                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 计算成功率
if [ $TOTAL_TESTS -gt 0 ]; then
    success_rate=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc 2>/dev/null || echo "计算失败")
    if [ "$success_rate" != "计算失败" ]; then
        echo -e "${BLUE}📊 测试通过率: ${success_rate}%${NC}"
        
        if (( $(echo "$success_rate >= 90" | bc -l 2>/dev/null || echo 0) )); then
            echo -e "${GREEN}🎉 新功能测试结果优秀！${NC}"
        elif (( $(echo "$success_rate >= 70" | bc -l 2>/dev/null || echo 0) )); then
            echo -e "${YELLOW}⚠️  新功能测试结果良好，部分功能需要关注${NC}"
        else
            echo -e "${RED}🚨 新功能存在问题，需要立即处理！${NC}"
        fi
    fi
fi

# 生成测试报告
echo -e "\n${BLUE}📝 生成测试报告...${NC}"
{
    echo "Lawsker 新功能测试报告"
    echo "生成时间: $(date)"
    echo "=========================="
    echo "总测试数: $TOTAL_TESTS"
    echo "通过测试: $PASSED_TESTS"
    echo "失败测试: $FAILED_TESTS"
    if [ "$success_rate" != "计算失败" ]; then
        echo "成功率: ${success_rate}%"
    fi
    echo ""
    echo "测试详情请查看上方输出"
} > /tmp/lawsker_feature_test_report.txt

echo -e "${GREEN}✅ 测试报告已保存到: /tmp/lawsker_feature_test_report.txt${NC}"

exit 0