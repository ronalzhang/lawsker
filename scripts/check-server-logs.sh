#!/bin/bash

# 远程服务器日志检查脚本
# 用于检查服务器上的应用运行状况和日志

# 🎨 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ⚠️ 注意：这个脚本需要配置服务器信息后才能使用
# 请复制为 check-server-logs-local.sh 并填入实际的服务器信息

SERVER_HOST="YOUR_SERVER_IP"
SERVER_USER="YOUR_USERNAME"

if [ "$SERVER_HOST" = "YOUR_SERVER_IP" ]; then
    echo -e "${RED}❌ 请先配置服务器信息！${NC}"
    echo -e "${YELLOW}1. 复制此文件为 check-server-logs-local.sh${NC}"
    echo -e "${YELLOW}2. 修改 SERVER_HOST 和 SERVER_USER 变量${NC}"
    echo -e "${YELLOW}3. 运行 ./scripts/check-server-logs-local.sh${NC}"
    exit 1
fi

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                 远程服务器状态检查                            ║"
echo "║                    $(date '+%Y-%m-%d %H:%M:%S')                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 🔍 1. 检查服务器连接
echo -e "${BLUE}🔍 检查服务器连接...${NC}"
if ssh -o ConnectTimeout=10 $SERVER_USER@$SERVER_HOST "echo '连接成功'" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 服务器连接成功${NC}"
else
    echo -e "${RED}❌ 服务器连接失败${NC}"
    exit 1
fi

# 🔍 2. 检查 PM2 进程状态
echo -e "\n${PURPLE}📊 PM2 进程状态${NC}"
echo "=================================================="
ssh $SERVER_USER@$SERVER_HOST "pm2 status"

# 🔍 3. 检查系统资源
echo -e "\n${PURPLE}💾 系统资源使用情况${NC}"
echo "=================================================="
ssh $SERVER_USER@$SERVER_HOST "
echo '=== CPU 使用率 ==='
top -bn1 | grep 'Cpu(s)' | awk '{print \$2}' | sed 's/%us,//'

echo -e '\n=== 内存使用情况 ==='
free -h

echo -e '\n=== 磁盘使用情况 ==='
df -h

echo -e '\n=== 网络连接 ==='
netstat -tuln | grep -E ':(80|443|8000|6060|3306|6379) '
"

# 🔍 4. 检查应用日志
echo -e "\n${PURPLE}📝 应用日志检查${NC}"
echo "=================================================="

echo -e "${BLUE}🔧 后端服务日志 (最近20行):${NC}"
ssh $SERVER_USER@$SERVER_HOST "
if [ -f ~/.pm2/logs/lawsker-backend-out.log ]; then
    echo '=== 后端输出日志 ==='
    tail -20 ~/.pm2/logs/lawsker-backend-out.log
else
    echo '后端输出日志文件不存在'
fi

if [ -f ~/.pm2/logs/lawsker-backend-error.log ]; then
    echo -e '\n=== 后端错误日志 ==='
    tail -20 ~/.pm2/logs/lawsker-backend-error.log
else
    echo '后端错误日志文件不存在'
fi
"

echo -e "\n${BLUE}🌐 前端服务日志 (最近20行):${NC}"
ssh $SERVER_USER@$SERVER_HOST "
if [ -f ~/.pm2/logs/lawsker-frontend-out.log ]; then
    echo '=== 前端输出日志 ==='
    tail -20 ~/.pm2/logs/lawsker-frontend-out.log
else
    echo '前端输出日志文件不存在'
fi

if [ -f ~/.pm2/logs/lawsker-frontend-error.log ]; then
    echo -e '\n=== 前端错误日志 ==='
    tail -20 ~/.pm2/logs/lawsker-frontend-error.log
else
    echo '前端错误日志文件不存在'
fi
"

# 🔍 5. 检查 Nginx 状态和日志
echo -e "\n${PURPLE}🌐 Nginx 状态和日志${NC}"
echo "=================================================="
ssh $SERVER_USER@$SERVER_HOST "
echo '=== Nginx 进程状态 ==='
ps aux | grep nginx | grep -v grep

echo -e '\n=== Nginx 访问日志 (最近10行) ==='
if [ -f /var/log/nginx/access.log ]; then
    sudo tail -10 /var/log/nginx/access.log
else
    echo 'Nginx 访问日志文件不存在'
fi

echo -e '\n=== Nginx 错误日志 (最近10行) ==='
if [ -f /var/log/nginx/error.log ]; then
    sudo tail -10 /var/log/nginx/error.log
else
    echo 'Nginx 错误日志文件不存在'
fi
"

# 🔍 6. 检查数据库状态
echo -e "\n${PURPLE}🗄️ 数据库状态${NC}"
echo "=================================================="
ssh $SERVER_USER@$SERVER_HOST "
echo '=== MySQL 进程状态 ==='
ps aux | grep mysql | grep -v grep

echo -e '\n=== Redis 进程状态 ==='
ps aux | grep redis | grep -v grep

echo -e '\n=== MySQL 连接测试 ==='
if command -v mysqladmin > /dev/null; then
    mysqladmin ping -h localhost -u root -p123abc74531 2>/dev/null && echo 'MySQL 连接正常' || echo 'MySQL 连接失败'
else
    echo 'mysqladmin 命令不存在'
fi

echo -e '\n=== Redis 连接测试 ==='
if command -v redis-cli > /dev/null; then
    redis-cli ping 2>/dev/null && echo 'Redis 连接正常' || echo 'Redis 连接失败'
else
    echo 'redis-cli 命令不存在'
fi
"

# 🔍 7. 检查 SSL 证书
echo -e "\n${PURPLE}🔒 SSL 证书状态${NC}"
echo "=================================================="
ssh $SERVER_USER@$SERVER_HOST "
if [ -f /etc/letsencrypt/live/lawsker.com/fullchain.pem ]; then
    echo '=== SSL 证书信息 ==='
    openssl x509 -in /etc/letsencrypt/live/lawsker.com/fullchain.pem -text -noout | grep -E 'Subject:|Not Before|Not After'
    
    echo -e '\n=== 证书到期时间 ==='
    openssl x509 -enddate -noout -in /etc/letsencrypt/live/lawsker.com/fullchain.pem
else
    echo 'SSL 证书文件不存在'
fi
"

# 🔍 8. 网络连接测试
echo -e "\n${PURPLE}🌐 网络连接测试${NC}"
echo "=================================================="
ssh $SERVER_USER@$SERVER_HOST "
echo '=== 本地服务测试 ==='
echo '前端服务 (端口 6060):'
curl -s -o /dev/null -w 'HTTP状态码: %{http_code}, 响应时间: %{time_total}s\n' http://localhost:6060 || echo '前端服务无响应'

echo '后端服务 (端口 8000):'
curl -s -o /dev/null -w 'HTTP状态码: %{http_code}, 响应时间: %{time_total}s\n' http://localhost:8000/api/v1/health || echo '后端服务无响应'

echo 'HTTPS 服务 (端口 443):'
curl -s -k -o /dev/null -w 'HTTP状态码: %{http_code}, 响应时间: %{time_total}s\n' https://localhost || echo 'HTTPS 服务无响应'
"

# 🔍 9. 检查最近的系统错误
echo -e "\n${PURPLE}🚨 系统错误检查${NC}"
echo "=================================================="
ssh $SERVER_USER@$SERVER_HOST "
echo '=== 系统日志中的错误 (最近10条) ==='
if [ -f /var/log/syslog ]; then
    sudo grep -i error /var/log/syslog | tail -10
else
    echo '系统日志文件不存在'
fi

echo -e '\n=== 内核消息中的错误 ==='
dmesg | grep -i error | tail -5 || echo '无内核错误消息'
"

# 🔍 10. 生成服务器状态报告
echo -e "\n${BLUE}📝 生成服务器状态报告...${NC}"
ssh $SERVER_USER@$SERVER_HOST "
{
    echo 'Lawsker 服务器状态报告'
    echo '生成时间: \$(date)'
    echo '=========================='
    echo ''
    echo '=== PM2 进程状态 ==='
    pm2 status
    echo ''
    echo '=== 系统资源 ==='
    echo '内存使用:'
    free -h
    echo '磁盘使用:'
    df -h
    echo ''
    echo '=== 最近错误 ==='
    echo '后端错误 (最近5行):'
    if [ -f ~/.pm2/logs/lawsker-backend-error.log ]; then
        tail -5 ~/.pm2/logs/lawsker-backend-error.log
    fi
    echo '前端错误 (最近5行):'
    if [ -f ~/.pm2/logs/lawsker-frontend-error.log ]; then
        tail -5 ~/.pm2/logs/lawsker-frontend-error.log
    fi
} > /tmp/lawsker_server_report.txt

echo '服务器状态报告已保存到: /tmp/lawsker_server_report.txt'
"

echo -e "\n${GREEN}✅ 服务器状态检查完成！${NC}"
echo -e "${YELLOW}💡 提示: 如需查看完整报告，请登录服务器查看 /tmp/lawsker_server_report.txt${NC}"