#!/usr/bin/env python3
"""
配置模板定义 - 预定义的配置模板
包含常用的配置文件模板，如Nginx、数据库、应用配置等
"""

import os
from typing import Dict, Any
from configuration_manager import ConfigurationManager


class ConfigTemplates:
    """配置模板管理类"""
    
    def __init__(self, config_manager: ConfigurationManager):
        self.config_manager = config_manager
    
    def create_all_templates(self) -> bool:
        """创建所有预定义模板"""
        templates = [
            self._create_nginx_site_template,
            self._create_nginx_ssl_template,
            self._create_database_config_template,
            self._create_app_config_template,
            self._create_systemd_service_template,
            self._create_prometheus_config_template,
            self._create_grafana_config_template,
            self._create_redis_config_template,
            self._create_env_file_template
        ]
        
        success_count = 0
        for template_func in templates:
            if template_func():
                success_count += 1
        
        return success_count == len(templates)
    
    def _create_nginx_site_template(self) -> bool:
        """创建Nginx站点配置模板"""
        template_content = """# Nginx configuration for {{ app_name }}
server {
    listen 80;
    server_name {{ domain }};
    
    {% if ssl_enabled %}
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name {{ domain }};
    
    # SSL Configuration
    ssl_certificate {{ ssl_cert_path }};
    ssl_certificate_key {{ ssl_key_path }};
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    {% endif %}
    
    # Logging
    access_log {{ log_path }}/{{ app_name }}_access.log;
    error_log {{ log_path }}/{{ app_name }}_error.log;
    
    # Client settings
    client_max_body_size {{ max_body_size | default('10M') }};
    
    # API endpoints
    location /api/ {
        proxy_pass {{ backend_url }};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout {{ proxy_timeout | default('30s') }};
        proxy_send_timeout {{ proxy_timeout | default('30s') }};
        proxy_read_timeout {{ proxy_timeout | default('30s') }};
    }
    
    # WebSocket support
    location /ws/ {
        proxy_pass {{ backend_url }};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files
    location /static/ {
        alias {{ static_path }}/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        
        # Gzip compression
        gzip on;
        gzip_vary on;
        gzip_types text/css application/javascript application/json image/svg+xml;
    }
    
    # Frontend application
    location / {
        root {{ frontend_path }};
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }
}"""
        
        return self.config_manager.create_template(
            name="nginx_site",
            template_content=template_content,
            variables={
                "app_name": "lawsker",
                "domain": "lawsker.com",
                "ssl_enabled": True,
                "ssl_cert_path": "/etc/letsencrypt/live/lawsker.com/fullchain.pem",
                "ssl_key_path": "/etc/letsencrypt/live/lawsker.com/privkey.pem",
                "backend_url": "http://127.0.0.1:8000",
                "static_path": "/opt/lawsker/static",
                "frontend_path": "/opt/lawsker/frontend",
                "log_path": "/var/log/nginx",
                "max_body_size": "10M",
                "proxy_timeout": "30s"
            },
            target_path="/etc/nginx/sites-available/lawsker.com",
            permissions="644",
            owner="root",
            group="root"
        )
    
    def _create_nginx_ssl_template(self) -> bool:
        """创建Nginx SSL配置模板"""
        template_content = """# SSL configuration snippet for {{ domain }}
ssl_certificate {{ ssl_cert_path }};
ssl_certificate_key {{ ssl_key_path }};

# SSL protocols and ciphers
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;

# SSL session settings
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_session_tickets off;

# OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;
ssl_trusted_certificate {{ ssl_cert_path }};

# Security headers
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header X-Frame-Options DENY always;
add_header X-Content-Type-Options nosniff always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' wss: https:;" always;"""
        
        return self.config_manager.create_template(
            name="nginx_ssl",
            template_content=template_content,
            variables={
                "domain": "lawsker.com",
                "ssl_cert_path": "/etc/letsencrypt/live/lawsker.com/fullchain.pem",
                "ssl_key_path": "/etc/letsencrypt/live/lawsker.com/privkey.pem"
            },
            target_path="/etc/nginx/snippets/ssl-lawsker.com.conf",
            permissions="644",
            owner="root",
            group="root"
        )
    
    def _create_database_config_template(self) -> bool:
        """创建数据库配置模板"""
        template_content = """# PostgreSQL configuration for {{ app_name }}
# Connection settings
host = {{ db_host }}
port = {{ db_port }}
database = {{ db_name }}
user = {{ db_user }}
password = {{ db_password }}

# Connection pool settings
pool_size = {{ pool_size | default(20) }}
max_overflow = {{ max_overflow | default(30) }}
pool_timeout = {{ pool_timeout | default(30) }}
pool_recycle = {{ pool_recycle | default(3600) }}
pool_pre_ping = {{ pool_pre_ping | default('true') }}

# SSL settings
sslmode = {{ ssl_mode | default('require') }}
{% if ssl_cert_path %}
sslcert = {{ ssl_cert_path }}
{% endif %}
{% if ssl_key_path %}
sslkey = {{ ssl_key_path }}
{% endif %}
{% if ssl_ca_path %}
sslrootcert = {{ ssl_ca_path }}
{% endif %}

# Performance settings
statement_timeout = {{ statement_timeout | default('30s') }}
lock_timeout = {{ lock_timeout | default('10s') }}
idle_in_transaction_session_timeout = {{ idle_timeout | default('60s') }}

# Logging
log_statement = {{ log_statement | default('none') }}
log_min_duration_statement = {{ log_min_duration | default(1000) }}"""
        
        return self.config_manager.create_template(
            name="database_config",
            template_content=template_content,
            variables={
                "app_name": "lawsker",
                "db_host": "localhost",
                "db_port": 5432,
                "db_name": "lawsker_prod",
                "db_user": "lawsker_user",
                "db_password": "${DB_PASSWORD}",
                "pool_size": 20,
                "max_overflow": 30,
                "pool_timeout": 30,
                "pool_recycle": 3600,
                "ssl_mode": "require"
            },
            target_path="/opt/lawsker/config/database.conf",
            permissions="600",
            owner="lawsker",
            group="lawsker"
        )
    
    def _create_app_config_template(self) -> bool:
        """创建应用配置模板"""
        template_content = """# {{ app_name }} Application Configuration

[app]
name = {{ app_name }}
version = {{ app_version | default('1.0.0') }}
environment = {{ environment }}
debug = {{ debug | default('false') }}
secret_key = {{ secret_key }}

[server]
host = {{ server_host | default('0.0.0.0') }}
port = {{ server_port | default(8000) }}
workers = {{ workers | default(4) }}
worker_class = {{ worker_class | default('uvicorn.workers.UvicornWorker') }}
timeout = {{ timeout | default(30) }}
keepalive = {{ keepalive | default(5) }}

[database]
url = {{ database_url }}
echo = {{ db_echo | default('false') }}
pool_size = {{ db_pool_size | default(20) }}
max_overflow = {{ db_max_overflow | default(30) }}

[redis]
url = {{ redis_url }}
max_connections = {{ redis_max_connections | default(100) }}
socket_timeout = {{ redis_timeout | default(5) }}

[security]
cors_origins = {{ cors_origins | default('[]') }}
allowed_hosts = {{ allowed_hosts | default('["*"]') }}
csrf_secret = {{ csrf_secret }}
session_timeout = {{ session_timeout | default(3600) }}

[logging]
level = {{ log_level | default('INFO') }}
format = {{ log_format | default('%(asctime)s - %(name)s - %(levelname)s - %(message)s') }}
file = {{ log_file | default('/var/log/lawsker/app.log') }}
max_size = {{ log_max_size | default('10MB') }}
backup_count = {{ log_backup_count | default(5) }}

[monitoring]
prometheus_enabled = {{ prometheus_enabled | default('true') }}
prometheus_port = {{ prometheus_port | default(9090) }}
health_check_interval = {{ health_check_interval | default(30) }}

[features]
ai_enabled = {{ ai_enabled | default('true') }}
payment_enabled = {{ payment_enabled | default('true') }}
notification_enabled = {{ notification_enabled | default('true') }}
audit_enabled = {{ audit_enabled | default('true') }}"""
        
        return self.config_manager.create_template(
            name="app_config",
            template_content=template_content,
            variables={
                "app_name": "lawsker",
                "app_version": "1.0.0",
                "environment": "production",
                "debug": False,
                "secret_key": "${SECRET_KEY}",
                "server_host": "0.0.0.0",
                "server_port": 8000,
                "workers": 4,
                "database_url": "${DATABASE_URL}",
                "redis_url": "${REDIS_URL}",
                "cors_origins": '["https://lawsker.com", "https://admin.lawsker.com"]',
                "csrf_secret": "${CSRF_SECRET}",
                "log_level": "INFO"
            },
            target_path="/opt/lawsker/config/app.conf",
            permissions="600",
            owner="lawsker",
            group="lawsker"
        )
    
    def _create_systemd_service_template(self) -> bool:
        """创建Systemd服务配置模板"""
        template_content = """[Unit]
Description={{ app_name }} {{ service_description | default('Application') }}
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=notify
User={{ service_user | default('lawsker') }}
Group={{ service_group | default('lawsker') }}
WorkingDirectory={{ working_directory }}
Environment=PATH={{ venv_path }}/bin
ExecStart={{ venv_path }}/bin/{{ start_command }}
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec={{ stop_timeout | default(5) }}
PrivateTmp=true
Restart={{ restart_policy | default('on-failure') }}
RestartSec={{ restart_delay | default(5) }}

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths={{ working_directory }} /var/log/{{ app_name }}
PrivateDevices=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

# Resource limits
LimitNOFILE={{ max_files | default(65536) }}
LimitNPROC={{ max_processes | default(4096) }}

[Install]
WantedBy=multi-user.target"""
        
        return self.config_manager.create_template(
            name="systemd_service",
            template_content=template_content,
            variables={
                "app_name": "lawsker",
                "service_description": "Lawsker Legal Platform",
                "service_user": "lawsker",
                "service_group": "lawsker",
                "working_directory": "/opt/lawsker",
                "venv_path": "/opt/lawsker/venv",
                "start_command": "gunicorn app.main:app --config gunicorn.conf.py",
                "stop_timeout": 5,
                "restart_policy": "on-failure",
                "restart_delay": 5,
                "max_files": 65536,
                "max_processes": 4096
            },
            target_path="/etc/systemd/system/lawsker.service",
            permissions="644",
            owner="root",
            group="root"
        )
    
    def _create_prometheus_config_template(self) -> bool:
        """创建Prometheus配置模板"""
        template_content = """# Prometheus configuration for {{ app_name }}
global:
  scrape_interval: {{ scrape_interval | default('15s') }}
  evaluation_interval: {{ evaluation_interval | default('15s') }}
  external_labels:
    monitor: '{{ app_name }}-monitor'

rule_files:
  - "{{ rules_path }}/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          {% for target in alertmanager_targets %}
          - {{ target }}
          {% endfor %}

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:{{ prometheus_port | default(9090) }}']

  - job_name: '{{ app_name }}-backend'
    static_configs:
      - targets: ['{{ backend_host }}:{{ backend_port }}']
    metrics_path: /metrics
    scrape_interval: {{ backend_scrape_interval | default('30s') }}

  - job_name: 'postgresql'
    static_configs:
      - targets: ['{{ db_host }}:{{ db_exporter_port | default(9187) }}']
    scrape_interval: {{ db_scrape_interval | default('30s') }}

  - job_name: 'redis'
    static_configs:
      - targets: ['{{ redis_host }}:{{ redis_exporter_port | default(9121) }}']
    scrape_interval: {{ redis_scrape_interval | default('30s') }}

  - job_name: 'nginx'
    static_configs:
      - targets: ['{{ nginx_host }}:{{ nginx_exporter_port | default(9113) }}']
    scrape_interval: {{ nginx_scrape_interval | default('30s') }}

  - job_name: 'node'
    static_configs:
      - targets: ['{{ node_host }}:{{ node_exporter_port | default(9100) }}']
    scrape_interval: {{ node_scrape_interval | default('30s') }}"""
        
        return self.config_manager.create_template(
            name="prometheus_config",
            template_content=template_content,
            variables={
                "app_name": "lawsker",
                "scrape_interval": "15s",
                "evaluation_interval": "15s",
                "rules_path": "/opt/prometheus/rules",
                "alertmanager_targets": ["localhost:9093"],
                "prometheus_port": 9090,
                "backend_host": "localhost",
                "backend_port": 8000,
                "db_host": "localhost",
                "redis_host": "localhost",
                "nginx_host": "localhost",
                "node_host": "localhost"
            },
            target_path="/opt/prometheus/prometheus.yml",
            permissions="644",
            owner="prometheus",
            group="prometheus"
        )
    
    def _create_grafana_config_template(self) -> bool:
        """创建Grafana配置模板"""
        template_content = """# Grafana configuration for {{ app_name }}
[default]
instance_name = {{ app_name }}-grafana

[server]
protocol = {{ protocol | default('http') }}
http_addr = {{ http_addr | default('0.0.0.0') }}
http_port = {{ http_port | default(3000) }}
domain = {{ domain }}
root_url = {{ root_url }}
serve_from_sub_path = {{ serve_from_sub_path | default('false') }}

[database]
type = {{ db_type | default('sqlite3') }}
host = {{ db_host | default('127.0.0.1:3306') }}
name = {{ db_name | default('grafana') }}
user = {{ db_user | default('root') }}
password = {{ db_password | default('') }}
path = {{ db_path | default('/var/lib/grafana/grafana.db') }}

[security]
admin_user = {{ admin_user | default('admin') }}
admin_password = {{ admin_password }}
secret_key = {{ secret_key }}
disable_gravatar = {{ disable_gravatar | default('true') }}
cookie_secure = {{ cookie_secure | default('false') }}
cookie_samesite = {{ cookie_samesite | default('lax') }}

[users]
allow_sign_up = {{ allow_sign_up | default('false') }}
allow_org_create = {{ allow_org_create | default('false') }}
auto_assign_org = {{ auto_assign_org | default('true') }}
auto_assign_org_role = {{ auto_assign_org_role | default('Viewer') }}

[auth]
disable_login_form = {{ disable_login_form | default('false') }}
disable_signout_menu = {{ disable_signout_menu | default('false') }}

[auth.anonymous]
enabled = {{ anonymous_enabled | default('false') }}
org_name = {{ anonymous_org_name | default('Main Org.') }}
org_role = {{ anonymous_org_role | default('Viewer') }}

[logging]
mode = {{ log_mode | default('console file') }}
level = {{ log_level | default('info') }}
filters = {{ log_filters | default('') }}

[paths]
data = {{ data_path | default('/var/lib/grafana') }}
logs = {{ logs_path | default('/var/log/grafana') }}
plugins = {{ plugins_path | default('/var/lib/grafana/plugins') }}
provisioning = {{ provisioning_path | default('/etc/grafana/provisioning') }}

[alerting]
enabled = {{ alerting_enabled | default('true') }}
execute_alerts = {{ execute_alerts | default('true') }}

[metrics]
enabled = {{ metrics_enabled | default('true') }}
interval_seconds = {{ metrics_interval | default(10) }}"""
        
        return self.config_manager.create_template(
            name="grafana_config",
            template_content=template_content,
            variables={
                "app_name": "lawsker",
                "protocol": "http",
                "http_addr": "0.0.0.0",
                "http_port": 3000,
                "domain": "monitor.lawsker.com",
                "root_url": "https://monitor.lawsker.com/",
                "admin_user": "admin",
                "admin_password": "${GRAFANA_ADMIN_PASSWORD}",
                "secret_key": "${GRAFANA_SECRET_KEY}",
                "allow_sign_up": False,
                "anonymous_enabled": False,
                "log_level": "info",
                "alerting_enabled": True,
                "metrics_enabled": True
            },
            target_path="/etc/grafana/grafana.ini",
            permissions="640",
            owner="grafana",
            group="grafana"
        )
    
    def _create_redis_config_template(self) -> bool:
        """创建Redis配置模板"""
        template_content = """# Redis configuration for {{ app_name }}
bind {{ bind_address | default('127.0.0.1') }}
port {{ port | default(6379) }}
timeout {{ timeout | default(0) }}
tcp-keepalive {{ tcp_keepalive | default(300) }}

# General
daemonize {{ daemonize | default('yes') }}
supervised {{ supervised | default('systemd') }}
pidfile {{ pidfile | default('/var/run/redis/redis-server.pid') }}
loglevel {{ loglevel | default('notice') }}
logfile {{ logfile | default('/var/log/redis/redis-server.log') }}

# Snapshotting
save {{ save_rules | default('900 1 300 10 60 10000') }}
stop-writes-on-bgsave-error {{ stop_writes_on_bgsave_error | default('yes') }}
rdbcompression {{ rdbcompression | default('yes') }}
rdbchecksum {{ rdbchecksum | default('yes') }}
dbfilename {{ dbfilename | default('dump.rdb') }}
dir {{ dir | default('/var/lib/redis') }}

# Security
{% if requirepass %}
requirepass {{ requirepass }}
{% endif %}
{% if rename_commands %}
{% for old_cmd, new_cmd in rename_commands.items() %}
rename-command {{ old_cmd }} {{ new_cmd }}
{% endfor %}
{% endif %}

# Memory management
maxmemory {{ maxmemory | default('256mb') }}
maxmemory-policy {{ maxmemory_policy | default('allkeys-lru') }}

# Append only file
appendonly {{ appendonly | default('yes') }}
appendfilename {{ appendfilename | default('appendonly.aof') }}
appendfsync {{ appendfsync | default('everysec') }}
no-appendfsync-on-rewrite {{ no_appendfsync_on_rewrite | default('no') }}
auto-aof-rewrite-percentage {{ auto_aof_rewrite_percentage | default(100) }}
auto-aof-rewrite-min-size {{ auto_aof_rewrite_min_size | default('64mb') }}

# Slow log
slowlog-log-slower-than {{ slowlog_log_slower_than | default(10000) }}
slowlog-max-len {{ slowlog_max_len | default(128) }}

# Client output buffer limits
client-output-buffer-limit normal {{ client_output_buffer_normal | default('0 0 0') }}
client-output-buffer-limit replica {{ client_output_buffer_replica | default('256mb 64mb 60') }}
client-output-buffer-limit pubsub {{ client_output_buffer_pubsub | default('32mb 8mb 60') }}

# Advanced config
hz {{ hz | default(10) }}
dynamic-hz {{ dynamic_hz | default('yes') }}
aof-rewrite-incremental-fsync {{ aof_rewrite_incremental_fsync | default('yes') }}"""
        
        return self.config_manager.create_template(
            name="redis_config",
            template_content=template_content,
            variables={
                "app_name": "lawsker",
                "bind_address": "127.0.0.1",
                "port": 6379,
                "timeout": 0,
                "daemonize": "yes",
                "supervised": "systemd",
                "loglevel": "notice",
                "logfile": "/var/log/redis/redis-server.log",
                "save_rules": "900 1 300 10 60 10000",
                "maxmemory": "256mb",
                "maxmemory_policy": "allkeys-lru",
                "appendonly": "yes",
                "appendfsync": "everysec"
            },
            target_path="/etc/redis/redis.conf",
            permissions="640",
            owner="redis",
            group="redis"
        )
    
    def _create_env_file_template(self) -> bool:
        """创建环境变量文件模板"""
        template_content = """# {{ app_name }} Environment Configuration
# Environment: {{ environment }}
# Generated: {{ generation_time }}

# Application settings
APP_NAME={{ app_name }}
APP_VERSION={{ app_version | default('1.0.0') }}
ENVIRONMENT={{ environment }}
DEBUG={{ debug | default('false') }}
SECRET_KEY={{ secret_key }}

# Server settings
HOST={{ host | default('0.0.0.0') }}
PORT={{ port | default(8000) }}
WORKERS={{ workers | default(4) }}

# Database settings
DATABASE_URL={{ database_url }}
DB_ECHO={{ db_echo | default('false') }}
DB_POOL_SIZE={{ db_pool_size | default(20) }}
DB_MAX_OVERFLOW={{ db_max_overflow | default(30) }}

# Redis settings
REDIS_URL={{ redis_url }}
REDIS_MAX_CONNECTIONS={{ redis_max_connections | default(100) }}

# Security settings
CSRF_SECRET={{ csrf_secret }}
SESSION_TIMEOUT={{ session_timeout | default(3600) }}
CORS_ORIGINS={{ cors_origins | default('[]') }}

# External services
{% if smtp_host %}
SMTP_HOST={{ smtp_host }}
SMTP_PORT={{ smtp_port | default(587) }}
SMTP_USER={{ smtp_user }}
SMTP_PASSWORD={{ smtp_password }}
SMTP_TLS={{ smtp_tls | default('true') }}
{% endif %}

{% if ai_api_key %}
AI_API_KEY={{ ai_api_key }}
AI_API_URL={{ ai_api_url }}
{% endif %}

{% if payment_api_key %}
PAYMENT_API_KEY={{ payment_api_key }}
PAYMENT_API_URL={{ payment_api_url }}
{% endif %}

# Monitoring settings
PROMETHEUS_ENABLED={{ prometheus_enabled | default('true') }}
PROMETHEUS_PORT={{ prometheus_port | default(9090) }}
GRAFANA_ADMIN_PASSWORD={{ grafana_admin_password }}

# Logging settings
LOG_LEVEL={{ log_level | default('INFO') }}
LOG_FILE={{ log_file | default('/var/log/lawsker/app.log') }}

# Feature flags
AI_ENABLED={{ ai_enabled | default('true') }}
PAYMENT_ENABLED={{ payment_enabled | default('true') }}
NOTIFICATION_ENABLED={{ notification_enabled | default('true') }}
AUDIT_ENABLED={{ audit_enabled | default('true') }}"""
        
        return self.config_manager.create_template(
            name="env_file",
            template_content=template_content,
            variables={
                "app_name": "lawsker",
                "app_version": "1.0.0",
                "environment": "production",
                "generation_time": "{{ generation_time }}",
                "debug": False,
                "secret_key": "${SECRET_KEY}",
                "host": "0.0.0.0",
                "port": 8000,
                "workers": 4,
                "database_url": "${DATABASE_URL}",
                "redis_url": "${REDIS_URL}",
                "csrf_secret": "${CSRF_SECRET}",
                "cors_origins": '["https://lawsker.com"]',
                "log_level": "INFO",
                "prometheus_enabled": True,
                "ai_enabled": True,
                "payment_enabled": True
            },
            target_path="/opt/lawsker/.env",
            permissions="600",
            owner="lawsker",
            group="lawsker"
        )


def main():
    """主函数 - 用于测试"""
    import logging
    from configuration_manager import ConfigurationManager
    
    logging.basicConfig(level=logging.INFO)
    
    # 创建配置管理器和模板管理器
    config_manager = ConfigurationManager()
    templates = ConfigTemplates(config_manager)
    
    # 创建所有模板
    if templates.create_all_templates():
        print("All configuration templates created successfully!")
    else:
        print("Some templates failed to create")


if __name__ == "__main__":
    main()