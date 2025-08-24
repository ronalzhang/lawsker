#!/bin/bash

# SSL Certificate System Setup Script
# Comprehensive SSL certificate management for Lawsker deployment

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_DIR="$PROJECT_ROOT/backend/deployment"
VENV_PATH="$PROJECT_ROOT/backend/venv"
LOG_FILE="/var/log/ssl-setup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${1}" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root for SSL certificate management"
        exit 1
    fi
}

# Install system dependencies
install_dependencies() {
    log_info "Installing system dependencies..."
    
    # Update package list
    apt-get update
    
    # Install required packages
    apt-get install -y \
        certbot \
        python3-certbot-nginx \
        nginx \
        python3-pip \
        python3-venv \
        openssl \
        cron
    
    log_success "System dependencies installed"
}

# Setup Python virtual environment
setup_python_env() {
    log_info "Setting up Python environment..."
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "$VENV_PATH" ]]; then
        python3 -m venv "$VENV_PATH"
        log_info "Created Python virtual environment"
    fi
    
    # Activate virtual environment
    source "$VENV_PATH/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install SSL management dependencies
    pip install \
        dnspython==2.4.2 \
        requests==2.31.0 \
        jinja2==3.1.2 \
        PyYAML==6.0.1 \
        schedule==1.2.0 \
        cryptography==41.0.7
    
    log_success "Python environment setup complete"
}

# Create SSL configuration
create_ssl_config() {
    local domains="$1"
    local email="$2"
    local staging="${3:-false}"
    
    log_info "Creating SSL configuration..."
    
    # Create configuration directory
    mkdir -p /etc/ssl-deployment
    
    # Create configuration file
    cat > /etc/ssl-deployment/config.yaml << EOF
# SSL Deployment Configuration for Lawsker
domains:
$(echo "$domains" | tr ',' '\n' | sed 's/^/  - /')

email: $email
staging: $staging
cert_path: /etc/letsencrypt/live

applications:
  - name: lawsker-main
    domain: $(echo "$domains" | cut -d',' -f1)
    upstream_port: 8000
    root_path: /var/www/lawsker
    client_max_body_size: 10M
    
  - name: lawsker-api
    domain: api.$(echo "$domains" | cut -d',' -f1)
    upstream_port: 8001
    client_max_body_size: 50M
    
  - name: lawsker-admin
    domain: admin.$(echo "$domains" | cut -d',' -f1)
    upstream_port: 8002
    root_path: /var/www/lawsker-admin

# SSL Security Settings
ssl_protocols:
  - TLSv1.2
  - TLSv1.3

# Renewal Settings
renewal_threshold_days: 30
critical_threshold_days: 7
check_interval_hours: 24
backup_enabled: true
backup_path: /var/backups/ssl-certificates

# Notification Settings (configure as needed)
email_notifications: false
# smtp_server: smtp.gmail.com
# smtp_port: 587
# smtp_username: notifications@$(echo "$domains" | cut -d',' -f1)
# smtp_password: your-app-password
# notification_emails:
#   - admin@$(echo "$domains" | cut -d',' -f1)
EOF
    
    log_success "SSL configuration created at /etc/ssl-deployment/config.yaml"
}

# Deploy SSL system
deploy_ssl_system() {
    log_info "Deploying SSL certificate system..."
    
    # Activate Python environment
    source "$VENV_PATH/bin/activate"
    
    # Change to deployment directory
    cd "$DEPLOYMENT_DIR"
    
    # Run SSL deployment
    python3 ssl_deployment_manager.py \
        --config /etc/ssl-deployment/config.yaml \
        --action deploy
    
    if [[ $? -eq 0 ]]; then
        log_success "SSL system deployment completed"
    else
        log_error "SSL system deployment failed"
        return 1
    fi
}

# Setup SSL renewal cron job
setup_cron_job() {
    log_info "Setting up SSL renewal cron job..."
    
    # Create renewal script
    cat > /usr/local/bin/ssl-renewal-check << EOF
#!/bin/bash
source "$VENV_PATH/bin/activate"
cd "$DEPLOYMENT_DIR"
python3 ssl_deployment_manager.py --config /etc/ssl-deployment/config.yaml --action status >> /var/log/ssl-renewal-check.log 2>&1
EOF
    
    chmod +x /usr/local/bin/ssl-renewal-check
    
    # Add cron job (run twice daily)
    (crontab -l 2>/dev/null; echo "0 2,14 * * * /usr/local/bin/ssl-renewal-check") | crontab -
    
    log_success "SSL renewal cron job configured"
}

# Create systemd service for renewal system
create_systemd_service() {
    log_info "Creating systemd service for SSL renewal system..."
    
    cat > /etc/systemd/system/ssl-renewal.service << EOF
[Unit]
Description=SSL Certificate Renewal System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$DEPLOYMENT_DIR
Environment=PATH=$VENV_PATH/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$VENV_PATH/bin/python ssl_renewal_system.py --config /etc/ssl-deployment/config.yaml --action start-scheduler --daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable ssl-renewal.service
    
    log_success "SSL renewal systemd service created and enabled"
}

# Verify SSL setup
verify_ssl_setup() {
    log_info "Verifying SSL setup..."
    
    # Activate Python environment
    source "$VENV_PATH/bin/activate"
    
    # Change to deployment directory
    cd "$DEPLOYMENT_DIR"
    
    # Run verification
    python3 ssl_deployment_manager.py \
        --config /etc/ssl-deployment/config.yaml \
        --action verify
    
    if [[ $? -eq 0 ]]; then
        log_success "SSL setup verification completed"
    else
        log_warning "SSL setup verification found issues"
    fi
}

# Show SSL status
show_ssl_status() {
    log_info "Checking SSL system status..."
    
    # Activate Python environment
    source "$VENV_PATH/bin/activate"
    
    # Change to deployment directory
    cd "$DEPLOYMENT_DIR"
    
    # Show status
    python3 ssl_deployment_manager.py \
        --config /etc/ssl-deployment/config.yaml \
        --action status
}

# Main setup function
setup_ssl_system() {
    local domains="$1"
    local email="$2"
    local staging="${3:-false}"
    
    log_info "Starting SSL certificate system setup..."
    log_info "Domains: $domains"
    log_info "Email: $email"
    log_info "Staging: $staging"
    
    # Check prerequisites
    check_root
    
    # Install dependencies
    install_dependencies
    
    # Setup Python environment
    setup_python_env
    
    # Create SSL configuration
    create_ssl_config "$domains" "$email" "$staging"
    
    # Deploy SSL system
    deploy_ssl_system
    
    # Setup automation
    setup_cron_job
    create_systemd_service
    
    # Verify setup
    verify_ssl_setup
    
    log_success "SSL certificate system setup completed!"
    log_info "Configuration file: /etc/ssl-deployment/config.yaml"
    log_info "Log file: $LOG_FILE"
    log_info "Renewal service: systemctl status ssl-renewal"
    log_info "Manual status check: $0 status"
}

# Usage information
show_usage() {
    cat << EOF
Usage: $0 [COMMAND] [OPTIONS]

Commands:
    setup DOMAINS EMAIL [--staging]    Setup complete SSL system
    status                             Show SSL system status
    verify                             Verify SSL configuration
    renew                              Force certificate renewal
    help                               Show this help message

Examples:
    $0 setup "lawsker.com,api.lawsker.com,admin.lawsker.com" "admin@lawsker.com"
    $0 setup "lawsker.com" "admin@lawsker.com" --staging
    $0 status
    $0 verify
    $0 renew

Options:
    --staging                          Use Let's Encrypt staging environment
    --help                             Show this help message

EOF
}

# Main script logic
main() {
    # Create log file
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"
    
    case "${1:-help}" in
        setup)
            if [[ $# -lt 3 ]]; then
                log_error "Usage: $0 setup DOMAINS EMAIL [--staging]"
                exit 1
            fi
            
            domains="$2"
            email="$3"
            staging="false"
            
            if [[ "${4:-}" == "--staging" ]]; then
                staging="true"
            fi
            
            setup_ssl_system "$domains" "$email" "$staging"
            ;;
            
        status)
            show_ssl_status
            ;;
            
        verify)
            verify_ssl_setup
            ;;
            
        renew)
            log_info "Forcing certificate renewal..."
            source "$VENV_PATH/bin/activate"
            cd "$DEPLOYMENT_DIR"
            python3 ssl_deployment_manager.py \
                --config /etc/ssl-deployment/config.yaml \
                --action deploy
            ;;
            
        help|--help|-h)
            show_usage
            ;;
            
        *)
            log_error "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"