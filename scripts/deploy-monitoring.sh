#!/bin/bash

# Lawsker监控系统部署脚本
set -e

echo "开始部署Lawsker监控系统..."

# 创建必要的目录
mkdir -p /var/log/lawsker
mkdir -p /etc/prometheus/rules
mkdir -p /etc/grafana/provisioning/datasources
mkdir -p /etc/grafana/provisioning/dashboards

# 安装监控组件
echo "安装监控组件..."

# 安装Node Exporter
if ! command -v node_exporter &> /dev/null; then
    wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz
    tar -xzf node_exporter-1.6.1.linux-amd64.tar.gz
    cp node_exporter-1.6.1.linux-amd64/node_exporter /usr/local/bin/
    rm -rf node_exporter-1.6.1.linux-amd64*
fi

# 安装PostgreSQL Exporter
if ! command -v postgres_exporter &> /dev/null; then
    wget https://github.com/prometheus-community/postgres_exporter/releases/download/v0.15.0/postgres_exporter-0.15.0.linux-amd64.tar.gz
    tar -xzf postgres_exporter-0.15.0.linux-amd64.tar.gz
    cp postgres_exporter-0.15.0.linux-amd64/postgres_exporter /usr/local/bin/
    rm -rf postgres_exporter-0.15.0.linux-amd64*
fi

# 安装Redis Exporter
if ! command -v redis_exporter &> /dev/null; then
    wget https://github.com/oliver006/redis_exporter/releases/download/v1.55.0/redis_exporter-v1.55.0.linux-amd64.tar.gz
    tar -xzf redis_exporter-v1.55.0.linux-amd64.tar.gz
    cp redis_exporter /usr/local/bin/
    rm redis_exporter redis_exporter-v1.55.0.linux-amd64.tar.gz
fi

# 安装Nginx Exporter
if ! command -v nginx-prometheus-exporter &> /dev/null; then
    wget https://github.com/nginxinc/nginx-prometheus-exporter/releases/download/v0.11.0/nginx-prometheus-exporter_0.11.0_linux_amd64.tar.gz
    tar -xzf nginx-prometheus-exporter_0.11.0_linux_amd64.tar.gz
    cp nginx-prometheus-exporter /usr/local/bin/
    rm nginx-prometheus-exporter nginx-prometheus-exporter_0.11.0_linux_amd64.tar.gz
fi

# 安装Blackbox Exporter (SSL证书监控)
if ! command -v blackbox_exporter &> /dev/null; then
    wget https://github.com/prometheus/blackbox_exporter/releases/download/v0.24.0/blackbox_exporter-0.24.0.linux-amd64.tar.gz
    tar -xzf blackbox_exporter-0.24.0.linux-amd64.tar.gz
    cp blackbox_exporter-0.24.0.linux-amd64/blackbox_exporter /usr/local/bin/
    rm -rf blackbox_exporter-0.24.0.linux-amd64*
fi

# 复制配置文件
echo "配置监控组件..."

# Prometheus配置
cp /root/lawsker/monitoring/prometheus/prometheus.yml /etc/prometheus/
cp /root/lawsker/monitoring/prometheus/lawsker-alerts.yml /etc/prometheus/rules/

# 创建systemd服务文件
cat > /etc/systemd/system/node-exporter.service << EOF
[Unit]
Description=Node Exporter
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/node_exporter
Restart=always

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/postgres-exporter.service << EOF
[Unit]
Description=PostgreSQL Exporter
After=network.target

[Service]
Type=simple
User=root
Environment="DATA_SOURCE_NAME=postgresql://lawsker:lawsker123@localhost:5432/lawsker?sslmode=disable"
ExecStart=/usr/local/bin/postgres_exporter
Restart=always

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/redis-exporter.service << EOF
[Unit]
Description=Redis Exporter
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/redis_exporter --redis.addr=localhost:6379
Restart=always

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/nginx-exporter.service << EOF
[Unit]
Description=Nginx Exporter
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/nginx-prometheus-exporter -nginx.scrape-uri=http://localhost/nginx_status
Restart=always

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/blackbox-exporter.service << EOF
[Unit]
Description=Blackbox Exporter
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/blackbox_exporter --config.file=/etc/blackbox_exporter/blackbox.yml
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 创建Blackbox配置
mkdir -p /etc/blackbox_exporter
cat > /etc/blackbox_exporter/blackbox.yml << EOF
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      preferred_ip_protocol: "ip4"
      valid_status_codes: [200, 301, 302, 404]
  http_post_2xx:
    prober: http
    timeout: 5s
    http:
      method: POST
      preferred_ip_protocol: "ip4"
  tcp_connect:
    prober: tcp
    timeout: 5s
  icmp:
    prober: icmp
    timeout: 5s
    icmp:
      preferred_ip_protocol: "ip4"
EOF

# 启动服务
echo "启动监控服务..."
systemctl daemon-reload
systemctl enable node-exporter postgres-exporter redis-exporter nginx-exporter blackbox-exporter
systemctl start node-exporter postgres-exporter redis-exporter nginx-exporter blackbox-exporter

# 配置Nginx状态页面
if ! grep -q "nginx_status" /etc/nginx/sites-enabled/lawsker.conf; then
    echo "配置Nginx状态页面..."
    cat >> /etc/nginx/sites-enabled/lawsker.conf << EOF

# Nginx状态页面（用于监控）
location /nginx_status {
    stub_status on;
    access_log off;
    allow 127.0.0.1;
    deny all;
}
EOF
    systemctl reload nginx
fi

echo "监控系统部署完成！"
echo "监控组件状态："
systemctl status node-exporter postgres-exporter redis-exporter nginx-exporter blackbox-exporter --no-pager 