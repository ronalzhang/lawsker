#!/bin/bash

# SSL证书管理脚本
# 支持Let's Encrypt自动证书和手动证书管理

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

# 域名列表
DOMAINS=(
    "lawsker.com"
    "www.lawsker.com"
    "api.lawsker.com"
    "admin.lawsker.com"
    "monitor.lawsker.com"
    "logs.lawsker.com"
)

# 创建SSL目录
create_ssl_dir() {
    log_info "创建SSL证书目录..."
    mkdir -p nginx/ssl
    mkdir -p nginx/ssl/letsencrypt
    log_success "SSL目录创建完成"
}

# 生成自签名证书（用于开发和测试）
generate_self_signed() {
    log_info "生成自签名SSL证书..."
    
    create_ssl_dir
    
    for domain in "${DOMAINS[@]}"; do
        log_info "为 $domain 生成自签名证书..."
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "nginx/ssl/${domain}.key" \
            -out "nginx/ssl/${domain}.crt" \
            -subj "/C=CN/ST=Beijing/L=Beijing/O=Lawsker/CN=${domain}" \
            -config <(
                echo '[dn]'
                echo 'CN='$domain
                echo '[req]'
                echo 'distinguished_name = dn'
                echo '[extensions]'
                echo 'subjectAltName=DNS:'$domain
                echo '[v3_req]'
                echo 'subjectAltName=DNS:'$domain
            ) -extensions v3_req
        
        log_success "$domain 自签名证书生成完成"
    done
    
    log_warning "自签名证书仅用于开发和测试，生产环境请使用正式证书"
}

# 使用Let's Encrypt获取证书
setup_letsencrypt() {
    log_info "设置Let's Encrypt证书..."
    
    # 检查certbot是否安装
    if ! command -v certbot &> /dev/null; then
        log_info "安装certbot..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y certbot python3-certbot-nginx
        elif command -v yum &> /dev/null; then
            sudo yum install -y certbot python3-certbot-nginx
        elif command -v brew &> /dev/null; then
            brew install certbot
        else
            log_error "无法自动安装certbot，请手动安装"
            exit 1
        fi
    fi
    
    create_ssl_dir
    
    # 为每个域名获取证书
    for domain in "${DOMAINS[@]}"; do
        log_info "为 $domain 获取Let's Encrypt证书..."
        
        # 使用webroot模式获取证书
        certbot certonly \
            --webroot \
            --webroot-path=/var/www/html \
            --email admin@lawsker.com \
            --agree-tos \
            --no-eff-email \
            --domains $domain
        
        # 复制证书到nginx目录
        if [ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
            cp "/etc/letsencrypt/live/$domain/fullchain.pem" "nginx/ssl/${domain}.crt"
            cp "/etc/letsencrypt/live/$domain/privkey.pem" "nginx/ssl/${domain}.key"
            log_success "$domain Let's Encrypt证书设置完成"
        else
            log_error "$domain 证书获取失败"
        fi
    done
    
    # 设置自动续期
    setup_auto_renewal
}

# 设置证书自动续期
setup_auto_renewal() {
    log_info "设置证书自动续期..."
    
    # 创建续期脚本
    cat > scripts/renew-ssl.sh << 'EOF'
#!/bin/bash

# SSL证书自动续期脚本

log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1"
}

# 续期证书
log_info "开始续期SSL证书..."

if certbot renew --quiet; then
    log_info "证书续期成功"
    
    # 复制新证书到nginx目录
    for domain in lawsker.com www.lawsker.com api.lawsker.com admin.lawsker.com monitor.lawsker.com logs.lawsker.com; do
        if [ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
            cp "/etc/letsencrypt/live/$domain/fullchain.pem" "nginx/ssl/${domain}.crt"
            cp "/etc/letsencrypt/live/$domain/privkey.pem" "nginx/ssl/${domain}.key"
            log_info "$domain 证书已更新"
        fi
    done
    
    # 重新加载nginx配置
    if docker-compose -f docker-compose.prod.yml ps nginx | grep -q "Up"; then
        docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
        log_info "Nginx配置已重新加载"
    fi
    
    log_info "证书续期完成"
else
    log_error "证书续期失败"
    exit 1
fi
EOF
    
    chmod +x scripts/renew-ssl.sh
    
    # 添加到crontab（每天检查一次）
    (crontab -l 2>/dev/null; echo "0 2 * * * $(pwd)/scripts/renew-ssl.sh >> $(pwd)/logs/ssl-renewal.log 2>&1") | crontab -
    
    log_success "自动续期设置完成"
}

# 验证证书
verify_certificates() {
    log_info "验证SSL证书..."
    
    for domain in "${DOMAINS[@]}"; do
        cert_file="nginx/ssl/${domain}.crt"
        key_file="nginx/ssl/${domain}.key"
        
        if [ -f "$cert_file" ] && [ -f "$key_file" ]; then
            # 检查证书有效期
            expiry_date=$(openssl x509 -in "$cert_file" -noout -enddate | cut -d= -f2)
            expiry_timestamp=$(date -d "$expiry_date" +%s)
            current_timestamp=$(date +%s)
            days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
            
            if [ $days_until_expiry -gt 0 ]; then
                log_success "$domain 证书有效，剩余 $days_until_expiry 天"
            else
                log_error "$domain 证书已过期"
            fi
            
            # 检查证书和私钥是否匹配
            cert_hash=$(openssl x509 -in "$cert_file" -noout -modulus | openssl md5)
            key_hash=$(openssl rsa -in "$key_file" -noout -modulus | openssl md5)
            
            if [ "$cert_hash" = "$key_hash" ]; then
                log_success "$domain 证书和私钥匹配"
            else
                log_error "$domain 证书和私钥不匹配"
            fi
        else
            log_error "$domain 证书文件不存在"
        fi
    done
}

# 备份证书
backup_certificates() {
    log_info "备份SSL证书..."
    
    backup_dir="backups/ssl/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    if [ -d "nginx/ssl" ]; then
        cp -r nginx/ssl/* "$backup_dir/"
        log_success "证书备份完成: $backup_dir"
    else
        log_error "SSL目录不存在"
    fi
}

# 从备份恢复证书
restore_certificates() {
    backup_dir=$1
    
    if [ -z "$backup_dir" ]; then
        log_error "请指定备份目录"
        exit 1
    fi
    
    if [ ! -d "$backup_dir" ]; then
        log_error "备份目录不存在: $backup_dir"
        exit 1
    fi
    
    log_info "从备份恢复证书: $backup_dir"
    
    create_ssl_dir
    cp -r "$backup_dir"/* nginx/ssl/
    
    log_success "证书恢复完成"
}

# 显示帮助信息
show_help() {
    echo "SSL证书管理脚本"
    echo ""
    echo "使用方法: $0 <command> [options]"
    echo ""
    echo "命令:"
    echo "  self-signed          生成自签名证书（用于开发测试）"
    echo "  letsencrypt          使用Let's Encrypt获取证书"
    echo "  verify               验证现有证书"
    echo "  backup               备份证书"
    echo "  restore <backup_dir> 从备份恢复证书"
    echo "  renew                手动续期证书"
    echo "  help                 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 self-signed       # 生成自签名证书"
    echo "  $0 letsencrypt       # 获取Let's Encrypt证书"
    echo "  $0 verify            # 验证证书"
    echo "  $0 backup            # 备份证书"
}

# 主函数
main() {
    case "${1:-help}" in
        "self-signed")
            generate_self_signed
            ;;
        "letsencrypt")
            setup_letsencrypt
            ;;
        "verify")
            verify_certificates
            ;;
        "backup")
            backup_certificates
            ;;
        "restore")
            restore_certificates "$2"
            ;;
        "renew")
            if [ -f "scripts/renew-ssl.sh" ]; then
                ./scripts/renew-ssl.sh
            else
                log_error "续期脚本不存在，请先运行 letsencrypt 命令"
            fi
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"