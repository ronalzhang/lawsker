#!/bin/bash

# Lawsker 生产环境远程测试脚本
# 从本地测试 lawsker.com 的功能

# 🎨 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置变量
DOMAIN="lawsker.com"
API_BASE="https://$DOMAIN"
FRONTEND_BASE="https://$DOMAIN"

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

test_url() {
    local url=$1
    local expected_codes=$2
    local description=$3
    local timeout=${4:-10}
    
    log_test "$description"
    
    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $timeout --max-time $timeout "$url")
    
    if echo "$expected_codes" | grep -q "$response"; then
        log_pass "响应码: $response (符合预期: $expected_codes)"
    else
        log_fail "响应码: $response (期望: $expected_codes)"
    fi
}

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              Lawsker 生产环境远程测试                         ║"
echo "║                 域名: $DOMAIN                        ║"
echo "║                    $(date '+%Y-%m-%d %H:%M:%S')                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 🔍 1. 基础连接测试
echo -e "\n${PURPLE}🌐 基础连接测试${NC}"
echo "=================================================="

test_url "$FRONTEND_BASE" "200" "网站主页访问"
test_url "$API_BASE/api/v1/health" "200" "API 健康检查"
test_url "$API_BASE/docs" "200" "API 文档访问"
test_url "$API_BASE/redoc" "200" "ReDoc 文档访问"

# 🔍 2. HTTPS 和 SSL 测试
echo -e "\n${PURPLE}🔒 HTTPS 和 SSL 测试${NC}"
echo "=================================================="

log_test "SSL 证书验证"
ssl_info=$(curl -s -I "$FRONTEND_BASE" 2>&1)
if echo "$ssl_info" | grep -q "HTTP/"; then
    log_pass "SSL 连接成功"
else
    log_fail "SSL 连接失败"
fi

log_test "SSL 证书详情检查"
cert_info=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
if [ -n "$cert_info" ]; then
    log_pass "SSL 证书有效"
    echo -e "${YELLOW}    证书信息: $cert_info${NC}"
else
    log_fail "无法获取 SSL 证书信息"
fi

# 🔍 3. API 端点测试
echo -e "\n${PURPLE}🔌 API 端点测试${NC}"
echo "=================================================="

test_url "$API_BASE/api/v1/auth/me" "401" "用户认证端点 (未登录)"
test_url "$API_BASE/api/v1/documents" "200\|401" "文档管理端点"
test_url "$API_BASE/api/v1/users" "200\|401" "用户管理端点"

# 测试登录端点
log_test "用户登录端点"
login_response=$(curl -s -X POST "$API_BASE/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' \
    -w "%{http_code}" \
    --connect-timeout 10)

if echo "$login_response" | grep -q "200\|400\|401\|422"; then
    log_pass "登录端点响应正常"
else
    log_fail "登录端点无响应"
fi

# 🔍 4. 性能测试
echo -e "\n${PURPLE}⚡ 性能测试${NC}"
echo "=================================================="

log_test "网站响应时间"
response_time=$(curl -o /dev/null -s -w "%{time_total}" --connect-timeout 10 "$FRONTEND_BASE")
response_time_ms=$(echo "$response_time * 1000" | bc 2>/dev/null || echo "计算失败")

if [ "$response_time_ms" != "计算失败" ]; then
    if (( $(echo "$response_time < 2.0" | bc -l 2>/dev/null || echo 0) )); then
        log_pass "网站响应时间优秀: ${response_time_ms}ms"
    elif (( $(echo "$response_time < 5.0" | bc -l 2>/dev/null || echo 0) )); then
        log_pass "网站响应时间良好: ${response_time_ms}ms"
    else
        log_info "网站响应时间: ${response_time_ms}ms"
    fi
else
    log_info "无法计算响应时间"
fi

log_test "API 响应时间"
api_response_time=$(curl -o /dev/null -s -w "%{time_total}" --connect-timeout 10 "$API_BASE/api/v1/health")
api_response_time_ms=$(echo "$api_response_time * 1000" | bc 2>/dev/null || echo "计算失败")

if [ "$api_response_time_ms" != "计算失败" ]; then
    if (( $(echo "$api_response_time < 1.0" | bc -l 2>/dev/null || echo 0) )); then
        log_pass "API 响应时间优秀: ${api_response_time_ms}ms"
    elif (( $(echo "$api_response_time < 2.0" | bc -l 2>/dev/null || echo 0) )); then
        log_pass "API 响应时间良好: ${api_response_time_ms}ms"
    else
        log_info "API 响应时间: ${api_response_time_ms}ms"
    fi
else
    log_info "无法计算 API 响应时间"
fi

# 🔍 5. 安全头检查
echo -e "\n${PURPLE}🛡️ 安全头检查${NC}"
echo "=================================================="

log_test "安全响应头检查"
headers=$(curl -s -I "$FRONTEND_BASE")

# 检查各种安全头
security_headers=(
    "X-Frame-Options:X-Frame-Options 头"
    "X-Content-Type-Options:X-Content-Type-Options 头"
    "X-XSS-Protection:X-XSS-Protection 头"
    "Strict-Transport-Security:HSTS 头"
    "Content-Security-Policy:CSP 头"
)

for header_info in "${security_headers[@]}"; do
    IFS=':' read -r header_name header_desc <<< "$header_info"
    if echo "$headers" | grep -qi "$header_name"; then
        log_pass "$header_desc 已配置"
    else
        log_info "$header_desc 未检测到"
    fi
done

# 🔍 6. 域名和 DNS 检查
echo -e "\n${PURPLE}🌍 域名和 DNS 检查${NC}"
echo "=================================================="

log_test "域名解析检查"
dns_result=$(nslookup $DOMAIN 2>/dev/null | grep "Address" | tail -1)
if [ -n "$dns_result" ]; then
    log_pass "域名解析正常: $dns_result"
else
    log_fail "域名解析失败"
fi

log_test "CDN/代理检查"
server_header=$(echo "$headers" | grep -i "server:" | head -1)
if [ -n "$server_header" ]; then
    log_info "服务器信息: $server_header"
else
    log_info "未检测到服务器信息"
fi

# 🔍 7. 可用性测试
echo -e "\n${PURPLE}📱 可用性测试${NC}"
echo "=================================================="

# 测试不同的 HTTP 方法
log_test "HTTP 方法支持"
options_response=$(curl -s -X OPTIONS "$API_BASE/api/v1/health" -w "%{http_code}" -o /dev/null)
if [ "$options_response" = "200" ] || [ "$options_response" = "405" ]; then
    log_pass "HTTP OPTIONS 方法响应正常"
else
    log_info "HTTP OPTIONS 响应: $options_response"
fi

# 测试错误页面
log_test "404 错误页面"
error_response=$(curl -s -w "%{http_code}" -o /dev/null "$FRONTEND_BASE/nonexistent-page")
if [ "$error_response" = "404" ]; then
    log_pass "404 错误页面正常"
else
    log_info "404 页面响应: $error_response"
fi

# 🔍 8. 移动端兼容性
echo -e "\n${PURPLE}📱 移动端兼容性${NC}"
echo "=================================================="

log_test "移动端 User-Agent 测试"
mobile_response=$(curl -s -w "%{http_code}" -o /dev/null \
    -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15" \
    "$FRONTEND_BASE")
if [ "$mobile_response" = "200" ]; then
    log_pass "移动端访问正常"
else
    log_info "移动端访问响应: $mobile_response"
fi

# 📊 测试结果汇总
echo -e "\n${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    生产环境测试结果                           ║"
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
            echo -e "${GREEN}🎉 生产环境运行状况优秀！${NC}"
        elif (( $(echo "$success_rate >= 70" | bc -l 2>/dev/null || echo 0) )); then
            echo -e "${YELLOW}⚠️  生产环境运行状况良好，部分功能需要关注${NC}"
        else
            echo -e "${RED}🚨 生产环境存在问题，需要立即处理！${NC}"
        fi
    fi
fi

# 生成测试报告
echo -e "\n${BLUE}📝 生成测试报告...${NC}"
{
    echo "Lawsker 生产环境测试报告"
    echo "域名: $DOMAIN"
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
    echo ""
    echo "建议："
    echo "1. 如果测试通过率低于 90%，请检查服务器状态"
    echo "2. 定期运行此脚本监控生产环境"
    echo "3. 关注响应时间和安全头配置"
} > /tmp/lawsker_production_test_report.txt

echo -e "${GREEN}✅ 测试报告已保存到: /tmp/lawsker_production_test_report.txt${NC}"

echo -e "\n${YELLOW}💡 提示:${NC}"
echo -e "${YELLOW}   - 此脚本从本地测试生产环境 ($DOMAIN)${NC}"
echo -e "${YELLOW}   - 如需检查服务器内部状态，请使用服务器端验证脚本${NC}"
echo -e "${YELLOW}   - 建议定期运行此脚本监控生产环境健康状况${NC}"

exit 0