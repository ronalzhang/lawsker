#!/usr/bin/env python3
"""
Nginx配置管理器 - NginxConfigManager类
负责虚拟主机配置生成、负载均衡和反向代理配置、SSL证书分配管理和配置热重载验证
"""

import os
import sys
import json
import logging
import asyncio
import subprocess
import shutil
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
from datetime import datetime
from enum import Enum
import yaml
import tempfile
from jinja2 import Template, Environment, FileSystemLoader
import ipaddress
import socket

# 导入应用管理器
from .application_manager import ApplicationManager, ApplicationConfig, ApplicationInstance


class NginxConfigType(Enum):
    """Nginx配置类型枚举"""
    STATIC = "static"  # 静态文件服务
    PROXY = "proxy"    # 反向代理
    LOAD_BALANCER = "load_balancer"  # 负载均衡
    REDIRECT = "redirect"  # 重定向


class LoadBalanceMethod(Enum):
    """负载均衡方法枚举"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONN = "least_conn"
    IP_HASH = "ip_hash"
    WEIGHTED = "weighted"


@dataclass
class UpstreamServer:
    """上游服务器配置"""
    host: str = "127.0.0.1"
    port: int = 8000
    weight: int = 1
    max_fails: int = 3
    fail_timeout: str = "30s"
    backup: bool = False
    down: bool = False


@dataclass
class LoadBalancerConfig:
    """负载均衡配置"""
    name: str
    method: LoadBalanceMethod = LoadBalanceMethod.ROUND_ROBIN
    servers: List[UpstreamServer] = field(default_factory=list)
    keepalive: int = 32
    keepalive_requests: int = 100
    keepalive_timeout: str = "60s"


@dataclass
class SSLCertificateConfig:
    """SSL证书配置"""
    domain: str
    cert_path: str = "/etc/letsencrypt/live"
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    chain_file: Optional[str] = None
    auto_renewal: bool = True
    staging: bool = False


@dataclass
class SecurityConfig:
    """安全配置"""
    # SSL配置
    ssl_protocols: List[str] = field(default_factory=lambda: ["TLSv1.2", "TLSv1.3"])
    ssl_ciphers: str = "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384"
    ssl_prefer_server_ciphers: bool = False
    ssl_session_cache: str = "shared:SSL:10m"
    ssl_session_timeout: str = "10m"
    ssl_stapling: bool = True
    
    # 安全头
    hsts_max_age: int = 31536000
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True
    frame_options: str = "DENY"
    content_type_options: str = "nosniff"
    xss_protection: str = "1; mode=block"
    referrer_policy: str = "strict-origin-when-cross-origin"
    
    # 访问控制
    allowed_ips: List[str] = field(default_factory=list)
    denied_ips: List[str] = field(default_factory=list)
    rate_limit_zone: Optional[str] = None
    rate_limit_requests: str = "10r/s"
    
    # 其他安全设置
    server_tokens: bool = False
    hide_version: bool = True


@dataclass
class LocationConfig:
    """Location配置"""
    path: str
    config_type: NginxConfigType
    
    # 静态文件配置
    root: Optional[str] = None
    index: List[str] = field(default_factory=lambda: ["index.html", "index.htm"])
    try_files: Optional[str] = None
    
    # 代理配置
    proxy_pass: Optional[str] = None
    proxy_set_headers: Dict[str, str] = field(default_factory=dict)
    proxy_timeout: int = 60
    proxy_buffering: bool = True
    proxy_buffer_size: str = "4k"
    proxy_buffers: str = "8 4k"
    
    # 缓存配置
    expires: Optional[str] = None
    cache_control: Optional[str] = None
    
    # 访问控制
    auth_basic: Optional[str] = None
    auth_basic_user_file: Optional[str] = None
    allow_ips: List[str] = field(default_factory=list)
    deny_ips: List[str] = field(default_factory=list)
    
    # 自定义配置
    custom_config: List[str] = field(default_factory=list)


@dataclass
class VirtualHostConfig:
    """虚拟主机配置"""
    name: str
    domain: str
    port: int = 80
    ssl_port: int = 443
    ssl_enabled: bool = False
    ssl_certificate: Optional[SSLCertificateConfig] = None
    
    # 基本配置
    server_name_aliases: List[str] = field(default_factory=list)
    default_server: bool = False
    
    # 日志配置
    access_log: str = "/var/log/nginx/access.log"
    error_log: str = "/var/log/nginx/error.log"
    log_level: str = "warn"
    
    # 客户端配置
    client_max_body_size: str = "10M"
    client_body_timeout: str = "60s"
    client_header_timeout: str = "60s"
    
    # Location配置
    locations: List[LocationConfig] = field(default_factory=list)
    
    # 负载均衡配置
    load_balancer: Optional[LoadBalancerConfig] = None
    
    # 安全配置
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # 自定义配置
    custom_server_config: List[str] = field(default_factory=list)


class NginxConfigManager:
    """
    Nginx配置管理器
    
    负责：
    - 实现虚拟主机配置生成
    - 添加负载均衡和反向代理配置
    - 创建SSL证书分配和管理
    - 实现配置热重载和验证
    """
    
    def __init__(self, 
                 nginx_path: str = "/etc/nginx",
                 sites_available: str = "/etc/nginx/sites-available",
                 sites_enabled: str = "/etc/nginx/sites-enabled",
                 application_manager: Optional[ApplicationManager] = None):
        
        self.nginx_path = Path(nginx_path)
        self.sites_available = Path(sites_available)
        self.sites_enabled = Path(sites_enabled)
        self.application_manager = application_manager
        
        self.logger = self._setup_logger()
        
        # 确保目录存在
        self.sites_available.mkdir(parents=True, exist_ok=True)
        self.sites_enabled.mkdir(parents=True, exist_ok=True)
        
        # 虚拟主机配置注册表
        self.virtual_hosts: Dict[str, VirtualHostConfig] = {}
        self.domain_registry: Dict[str, str] = {}  # 域名到虚拟主机的映射
        self.port_registry: Dict[int, Set[str]] = {}  # 端口到虚拟主机的映射
        
        # 负载均衡器注册表
        self.load_balancers: Dict[str, LoadBalancerConfig] = {}
        
        # SSL证书注册表
        self.ssl_certificates: Dict[str, SSLCertificateConfig] = {}
        
        # 模板环境
        self.template_env = self._setup_template_environment()
        
        # 加载现有配置
        self._load_existing_configurations()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # 文件处理器
            log_file = self.nginx_path / "nginx_config_manager.log"
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _setup_template_environment(self) -> Environment:
        """设置Jinja2模板环境"""
        template_dir = Path(__file__).parent / "nginx_templates"
        template_dir.mkdir(exist_ok=True)
        
        # 创建默认模板
        self._create_default_templates(template_dir)
        
        return Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def _create_default_templates(self, template_dir: Path):
        """创建默认Nginx配置模板"""
        
        # 虚拟主机模板
        vhost_template = '''
# Virtual Host Configuration for {{ vhost.domain }}
# Generated by Nginx Config Manager at {{ timestamp }}

{% if vhost.load_balancer %}
# Upstream configuration for {{ vhost.load_balancer.name }}
upstream {{ vhost.load_balancer.name }} {
    {% if vhost.load_balancer.method.value == 'least_conn' %}
    least_conn;
    {% elif vhost.load_balancer.method.value == 'ip_hash' %}
    ip_hash;
    {% endif %}
    
    {% for server in vhost.load_balancer.servers %}
    server {{ server.host }}:{{ server.port }}{% if server.weight != 1 %} weight={{ server.weight }}{% endif %}{% if server.max_fails != 3 %} max_fails={{ server.max_fails }}{% endif %}{% if server.fail_timeout != '30s' %} fail_timeout={{ server.fail_timeout }}{% endif %}{% if server.backup %} backup{% endif %}{% if server.down %} down{% endif %};
    {% endfor %}
    
    keepalive {{ vhost.load_balancer.keepalive }};
    keepalive_requests {{ vhost.load_balancer.keepalive_requests }};
    keepalive_timeout {{ vhost.load_balancer.keepalive_timeout }};
}
{% endif %}

{% if vhost.port == 80 or not vhost.ssl_enabled %}
# HTTP Server Block
server {
    listen {{ vhost.port }}{% if vhost.default_server %} default_server{% endif %};
    server_name {{ vhost.domain }}{% for alias in vhost.server_name_aliases %} {{ alias }}{% endfor %};
    
    {% if vhost.ssl_enabled %}
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
    {% else %}
    # HTTP Configuration
    {% include 'server_common.conf.j2' %}
    {% endif %}
}
{% endif %}

{% if vhost.ssl_enabled and vhost.ssl_certificate %}
# HTTPS Server Block
server {
    listen {{ vhost.ssl_port }} ssl http2{% if vhost.default_server %} default_server{% endif %};
    server_name {{ vhost.domain }}{% for alias in vhost.server_name_aliases %} {{ alias }}{% endfor %};
    
    # SSL Certificate Configuration
    {% if vhost.ssl_certificate.cert_file %}
    ssl_certificate {{ vhost.ssl_certificate.cert_file }};
    ssl_certificate_key {{ vhost.ssl_certificate.key_file }};
    {% if vhost.ssl_certificate.chain_file %}
    ssl_trusted_certificate {{ vhost.ssl_certificate.chain_file }};
    {% endif %}
    {% else %}
    ssl_certificate {{ vhost.ssl_certificate.cert_path }}/{{ vhost.ssl_certificate.domain }}/fullchain.pem;
    ssl_certificate_key {{ vhost.ssl_certificate.cert_path }}/{{ vhost.ssl_certificate.domain }}/privkey.pem;
    ssl_trusted_certificate {{ vhost.ssl_certificate.cert_path }}/{{ vhost.ssl_certificate.domain }}/chain.pem;
    {% endif %}
    
    # SSL Security Configuration
    ssl_protocols {{ vhost.security.ssl_protocols | join(' ') }};
    ssl_ciphers {{ vhost.security.ssl_ciphers }};
    ssl_prefer_server_ciphers {{ 'on' if vhost.security.ssl_prefer_server_ciphers else 'off' }};
    ssl_session_cache {{ vhost.security.ssl_session_cache }};
    ssl_session_timeout {{ vhost.security.ssl_session_timeout }};
    
    {% if vhost.security.ssl_stapling %}
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    {% endif %}
    
    # Security Headers
    add_header Strict-Transport-Security "max-age={{ vhost.security.hsts_max_age }}{% if vhost.security.hsts_include_subdomains %}; includeSubDomains{% endif %}{% if vhost.security.hsts_preload %}; preload{% endif %}" always;
    add_header X-Frame-Options {{ vhost.security.frame_options }} always;
    add_header X-Content-Type-Options {{ vhost.security.content_type_options }} always;
    add_header X-XSS-Protection "{{ vhost.security.xss_protection }}" always;
    add_header Referrer-Policy "{{ vhost.security.referrer_policy }}" always;
    
    {% include 'server_common.conf.j2' %}
}
{% endif %}
'''
        
        # 通用服务器配置模板
        server_common_template = '''
    # Basic Configuration
    client_max_body_size {{ vhost.client_max_body_size }};
    client_body_timeout {{ vhost.client_body_timeout }};
    client_header_timeout {{ vhost.client_header_timeout }};
    
    # Logging
    access_log {{ vhost.access_log }};
    error_log {{ vhost.error_log }} {{ vhost.log_level }};
    
    # Server Tokens
    server_tokens {{ 'on' if not vhost.security.server_tokens else 'off' }};
    
    {% if vhost.security.rate_limit_zone %}
    # Rate Limiting
    limit_req zone={{ vhost.security.rate_limit_zone }} burst=10 nodelay;
    {% endif %}
    
    {% if vhost.security.allowed_ips or vhost.security.denied_ips %}
    # IP Access Control
    {% for ip in vhost.security.allowed_ips %}
    allow {{ ip }};
    {% endfor %}
    {% for ip in vhost.security.denied_ips %}
    deny {{ ip }};
    {% endfor %}
    {% if vhost.security.allowed_ips %}
    deny all;
    {% endif %}
    {% endif %}
    
    {% for config_line in vhost.custom_server_config %}
    {{ config_line }}
    {% endfor %}
    
    {% for location in vhost.locations %}
    # Location: {{ location.path }}
    location {{ location.path }} {
        {% if location.config_type.value == 'static' %}
        {% if location.root %}
        root {{ location.root }};
        {% endif %}
        {% if location.index %}
        index {{ location.index | join(' ') }};
        {% endif %}
        {% if location.try_files %}
        try_files {{ location.try_files }};
        {% endif %}
        {% if location.expires %}
        expires {{ location.expires }};
        {% endif %}
        {% if location.cache_control %}
        add_header Cache-Control "{{ location.cache_control }}";
        {% endif %}
        
        {% elif location.config_type.value == 'proxy' %}
        {% if location.proxy_pass %}
        proxy_pass {{ location.proxy_pass }};
        {% elif vhost.load_balancer %}
        proxy_pass http://{{ vhost.load_balancer.name }};
        {% endif %}
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        {% for header, value in location.proxy_set_headers.items() %}
        proxy_set_header {{ header }} {{ value }};
        {% endfor %}
        
        proxy_connect_timeout {{ location.proxy_timeout }}s;
        proxy_send_timeout {{ location.proxy_timeout }}s;
        proxy_read_timeout {{ location.proxy_timeout }}s;
        
        {% if location.proxy_buffering %}
        proxy_buffering on;
        proxy_buffer_size {{ location.proxy_buffer_size }};
        proxy_buffers {{ location.proxy_buffers }};
        {% else %}
        proxy_buffering off;
        {% endif %}
        
        {% elif location.config_type.value == 'redirect' %}
        return 301 {{ location.proxy_pass }};
        {% endif %}
        
        {% if location.auth_basic %}
        auth_basic "{{ location.auth_basic }}";
        auth_basic_user_file {{ location.auth_basic_user_file }};
        {% endif %}
        
        {% if location.allow_ips or location.deny_ips %}
        {% for ip in location.allow_ips %}
        allow {{ ip }};
        {% endfor %}
        {% for ip in location.deny_ips %}
        deny {{ ip }};
        {% endfor %}
        {% if location.allow_ips %}
        deny all;
        {% endif %}
        {% endif %}
        
        {% for config_line in location.custom_config %}
        {{ config_line }}
        {% endfor %}
    }
    
    {% endfor %}
    
    # Health check endpoint
    location /nginx-health {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }
    
    # Security: Hide server information and prevent access to hidden files
    location ~ /\\. {
        deny all;
        access_log off;
        log_not_found off;
    }
'''
        
        # 写入模板文件
        (template_dir / "vhost.conf.j2").write_text(vhost_template.strip())
        (template_dir / "server_common.conf.j2").write_text(server_common_template.strip())
    
    def _load_existing_configurations(self):
        """加载现有的Nginx配置"""
        try:
            # 扫描sites-available目录
            for config_file in self.sites_available.glob("*.conf"):
                try:
                    # 这里可以实现配置文件解析逻辑
                    # 暂时跳过，因为解析Nginx配置比较复杂
                    pass
                except Exception as e:
                    self.logger.warning(f"Failed to parse existing config {config_file}: {str(e)}")
            
            self.logger.info("Loaded existing Nginx configurations")
            
        except Exception as e:
            self.logger.error(f"Failed to load existing configurations: {str(e)}")
    
    def create_virtual_host(self, config: VirtualHostConfig) -> bool:
        """
        创建虚拟主机配置
        
        Args:
            config: 虚拟主机配置
            
        Returns:
            创建是否成功
        """
        try:
            # 检查域名冲突
            if self._check_domain_conflict(config.domain, config.name):
                self.logger.error(f"Domain {config.domain} already in use")
                return False
            
            # 检查端口冲突
            if self._check_port_conflict(config.port, config.name):
                self.logger.error(f"Port {config.port} already in use")
                return False
            
            if config.ssl_enabled and self._check_port_conflict(config.ssl_port, config.name):
                self.logger.error(f"SSL port {config.ssl_port} already in use")
                return False
            
            # 验证配置
            validation_errors = self._validate_virtual_host_config(config)
            if validation_errors:
                self.logger.error(f"Configuration validation failed: {validation_errors}")
                return False
            
            # 注册虚拟主机
            self.virtual_hosts[config.name] = config
            self.domain_registry[config.domain] = config.name
            
            # 注册端口
            if config.port not in self.port_registry:
                self.port_registry[config.port] = set()
            self.port_registry[config.port].add(config.name)
            
            if config.ssl_enabled:
                if config.ssl_port not in self.port_registry:
                    self.port_registry[config.ssl_port] = set()
                self.port_registry[config.ssl_port].add(config.name)
            
            # 注册SSL证书
            if config.ssl_certificate:
                self.ssl_certificates[config.ssl_certificate.domain] = config.ssl_certificate
            
            # 注册负载均衡器
            if config.load_balancer:
                self.load_balancers[config.load_balancer.name] = config.load_balancer
            
            self.logger.info(f"Virtual host {config.name} created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create virtual host {config.name}: {str(e)}")
            return False
    
    def update_virtual_host(self, name: str, config: VirtualHostConfig) -> bool:
        """
        更新虚拟主机配置
        
        Args:
            name: 虚拟主机名称
            config: 新的配置
            
        Returns:
            更新是否成功
        """
        try:
            if name not in self.virtual_hosts:
                self.logger.error(f"Virtual host {name} not found")
                return False
            
            old_config = self.virtual_hosts[name]
            
            # 清理旧的注册信息
            self._cleanup_virtual_host_registry(old_config)
            
            # 创建新配置
            config.name = name  # 确保名称一致
            return self.create_virtual_host(config)
            
        except Exception as e:
            self.logger.error(f"Failed to update virtual host {name}: {str(e)}")
            return False
    
    def delete_virtual_host(self, name: str) -> bool:
        """
        删除虚拟主机配置
        
        Args:
            name: 虚拟主机名称
            
        Returns:
            删除是否成功
        """
        try:
            if name not in self.virtual_hosts:
                self.logger.error(f"Virtual host {name} not found")
                return False
            
            config = self.virtual_hosts[name]
            
            # 清理注册信息
            self._cleanup_virtual_host_registry(config)
            
            # 删除配置文件
            config_file = self.sites_available / f"{name}.conf"
            if config_file.exists():
                config_file.unlink()
            
            # 删除启用的符号链接
            enabled_file = self.sites_enabled / f"{name}.conf"
            if enabled_file.exists() or enabled_file.is_symlink():
                enabled_file.unlink()
            
            # 从注册表中移除
            del self.virtual_hosts[name]
            
            self.logger.info(f"Virtual host {name} deleted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete virtual host {name}: {str(e)}")
            return False
    
    def _cleanup_virtual_host_registry(self, config: VirtualHostConfig):
        """清理虚拟主机注册信息"""
        # 清理域名注册
        if config.domain in self.domain_registry:
            del self.domain_registry[config.domain]
        
        # 清理端口注册
        if config.port in self.port_registry:
            self.port_registry[config.port].discard(config.name)
            if not self.port_registry[config.port]:
                del self.port_registry[config.port]
        
        if config.ssl_enabled and config.ssl_port in self.port_registry:
            self.port_registry[config.ssl_port].discard(config.name)
            if not self.port_registry[config.ssl_port]:
                del self.port_registry[config.ssl_port]
        
        # 清理SSL证书注册
        if config.ssl_certificate and config.ssl_certificate.domain in self.ssl_certificates:
            del self.ssl_certificates[config.ssl_certificate.domain]
        
        # 清理负载均衡器注册
        if config.load_balancer and config.load_balancer.name in self.load_balancers:
            del self.load_balancers[config.load_balancer.name]
    
    def _check_domain_conflict(self, domain: str, exclude_vhost: str = None) -> bool:
        """检查域名冲突"""
        if domain in self.domain_registry:
            return self.domain_registry[domain] != exclude_vhost
        return False
    
    def _check_port_conflict(self, port: int, exclude_vhost: str = None) -> bool:
        """检查端口冲突"""
        if port in self.port_registry:
            vhosts = self.port_registry[port].copy()
            if exclude_vhost:
                vhosts.discard(exclude_vhost)
            return len(vhosts) > 0
        return False
    
    def _validate_virtual_host_config(self, config: VirtualHostConfig) -> List[str]:
        """验证虚拟主机配置"""
        errors = []
        
        # 检查必填字段
        if not config.name:
            errors.append("Virtual host name is required")
        
        if not config.domain:
            errors.append("Domain is required")
        
        # 检查端口范围
        if config.port < 1 or config.port > 65535:
            errors.append("Port must be between 1 and 65535")
        
        if config.ssl_enabled and (config.ssl_port < 1 or config.ssl_port > 65535):
            errors.append("SSL port must be between 1 and 65535")
        
        # 检查SSL配置
        if config.ssl_enabled and not config.ssl_certificate:
            errors.append("SSL certificate configuration is required when SSL is enabled")
        
        # 检查Location配置
        for location in config.locations:
            if location.config_type == NginxConfigType.STATIC and not location.root:
                errors.append(f"Root path is required for static location {location.path}")
            
            if location.config_type == NginxConfigType.PROXY and not location.proxy_pass and not config.load_balancer:
                errors.append(f"Proxy pass or load balancer is required for proxy location {location.path}")
        
        # 检查负载均衡配置
        if config.load_balancer:
            if not config.load_balancer.servers:
                errors.append("Load balancer must have at least one server")
            
            for server in config.load_balancer.servers:
                if server.port < 1 or server.port > 65535:
                    errors.append(f"Upstream server port must be between 1 and 65535: {server.host}:{server.port}")
        
        return errors
    
    def generate_configuration(self, vhost_name: str) -> Optional[str]:
        """
        生成虚拟主机配置文件内容
        
        Args:
            vhost_name: 虚拟主机名称
            
        Returns:
            配置文件内容，失败时返回None
        """
        try:
            if vhost_name not in self.virtual_hosts:
                self.logger.error(f"Virtual host {vhost_name} not found")
                return None
            
            vhost = self.virtual_hosts[vhost_name]
            
            template = self.template_env.get_template("vhost.conf.j2")
            
            config_content = template.render(
                vhost=vhost,
                timestamp=datetime.now().isoformat()
            )
            
            return config_content
            
        except Exception as e:
            self.logger.error(f"Failed to generate configuration for {vhost_name}: {str(e)}")
            return None
    
    def write_configuration(self, vhost_name: str) -> bool:
        """
        写入虚拟主机配置文件
        
        Args:
            vhost_name: 虚拟主机名称
            
        Returns:
            写入是否成功
        """
        try:
            config_content = self.generate_configuration(vhost_name)
            if not config_content:
                return False
            
            # 写入sites-available
            config_file = self.sites_available / f"{vhost_name}.conf"
            config_file.write_text(config_content)
            
            self.logger.info(f"Configuration written for {vhost_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to write configuration for {vhost_name}: {str(e)}")
            return False
    
    def enable_virtual_host(self, vhost_name: str) -> bool:
        """
        启用虚拟主机（创建符号链接）
        
        Args:
            vhost_name: 虚拟主机名称
            
        Returns:
            启用是否成功
        """
        try:
            if vhost_name not in self.virtual_hosts:
                self.logger.error(f"Virtual host {vhost_name} not found")
                return False
            
            available_file = self.sites_available / f"{vhost_name}.conf"
            enabled_file = self.sites_enabled / f"{vhost_name}.conf"
            
            if not available_file.exists():
                self.logger.error(f"Configuration file not found: {available_file}")
                return False
            
            # 删除现有符号链接
            if enabled_file.exists() or enabled_file.is_symlink():
                enabled_file.unlink()
            
            # 创建新符号链接
            enabled_file.symlink_to(available_file)
            
            self.logger.info(f"Virtual host {vhost_name} enabled")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enable virtual host {vhost_name}: {str(e)}")
            return False
    
    def disable_virtual_host(self, vhost_name: str) -> bool:
        """
        禁用虚拟主机（删除符号链接）
        
        Args:
            vhost_name: 虚拟主机名称
            
        Returns:
            禁用是否成功
        """
        try:
            enabled_file = self.sites_enabled / f"{vhost_name}.conf"
            
            if enabled_file.exists() or enabled_file.is_symlink():
                enabled_file.unlink()
                self.logger.info(f"Virtual host {vhost_name} disabled")
            else:
                self.logger.info(f"Virtual host {vhost_name} was not enabled")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disable virtual host {vhost_name}: {str(e)}")
            return False
    
    def validate_configuration(self, vhost_name: Optional[str] = None) -> bool:
        """
        验证Nginx配置语法
        
        Args:
            vhost_name: 特定虚拟主机名称，None表示验证所有配置
            
        Returns:
            验证是否通过
        """
        try:
            if vhost_name:
                # 验证特定虚拟主机配置
                config_content = self.generate_configuration(vhost_name)
                if not config_content:
                    return False
                
                # 创建临时文件进行验证
                with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as temp_file:
                    temp_file.write(config_content)
                    temp_file_path = temp_file.name
                
                try:
                    # 使用nginx -t验证配置
                    result = subprocess.run(
                        ['nginx', '-t', '-c', temp_file_path],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        self.logger.info(f"Configuration validation passed for {vhost_name}")
                        return True
                    else:
                        self.logger.error(f"Configuration validation failed for {vhost_name}: {result.stderr}")
                        return False
                        
                finally:
                    # 清理临时文件
                    Path(temp_file_path).unlink(missing_ok=True)
            
            else:
                # 验证整个Nginx配置
                result = subprocess.run(
                    ['nginx', '-t'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    self.logger.info("Nginx configuration validation passed")
                    return True
                else:
                    self.logger.error(f"Nginx configuration validation failed: {result.stderr}")
                    return False
                    
        except subprocess.TimeoutExpired:
            self.logger.error("Configuration validation timed out")
            return False
        except FileNotFoundError:
            self.logger.error("Nginx binary not found")
            return False
        except Exception as e:
            self.logger.error(f"Configuration validation error: {str(e)}")
            return False
    
    def reload_nginx(self) -> bool:
        """
        重载Nginx配置
        
        Returns:
            重载是否成功
        """
        try:
            # 先验证配置
            if not self.validate_configuration():
                self.logger.error("Cannot reload Nginx: configuration validation failed")
                return False
            
            # 重载Nginx
            result = subprocess.run(
                ['systemctl', 'reload', 'nginx'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.logger.info("Nginx reloaded successfully")
                return True
            else:
                self.logger.error(f"Nginx reload failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Nginx reload timed out")
            return False
        except Exception as e:
            self.logger.error(f"Nginx reload error: {str(e)}")
            return False
    
    def deploy_virtual_host(self, vhost_name: str) -> bool:
        """
        部署虚拟主机（写入配置、启用、重载）
        
        Args:
            vhost_name: 虚拟主机名称
            
        Returns:
            部署是否成功
        """
        try:
            # 写入配置
            if not self.write_configuration(vhost_name):
                return False
            
            # 启用虚拟主机
            if not self.enable_virtual_host(vhost_name):
                return False
            
            # 重载Nginx
            if not self.reload_nginx():
                return False
            
            self.logger.info(f"Virtual host {vhost_name} deployed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deploy virtual host {vhost_name}: {str(e)}")
            return False
    
    def deploy_all_virtual_hosts(self) -> Dict[str, bool]:
        """
        部署所有虚拟主机
        
        Returns:
            部署结果字典
        """
        results = {}
        
        try:
            # 写入所有配置
            for vhost_name in self.virtual_hosts:
                success = self.write_configuration(vhost_name)
                if success:
                    self.enable_virtual_host(vhost_name)
                results[vhost_name] = success
            
            # 统一重载Nginx
            if any(results.values()):
                reload_success = self.reload_nginx()
                if not reload_success:
                    # 如果重载失败，标记所有部署为失败
                    results = {name: False for name in results}
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to deploy virtual hosts: {str(e)}")
            return {name: False for name in self.virtual_hosts}
    
    def create_load_balancer(self, config: LoadBalancerConfig) -> bool:
        """
        创建负载均衡器配置
        
        Args:
            config: 负载均衡器配置
            
        Returns:
            创建是否成功
        """
        try:
            # 验证配置
            if not config.servers:
                self.logger.error("Load balancer must have at least one server")
                return False
            
            # 检查服务器可用性
            for server in config.servers:
                if not self._check_server_availability(server.host, server.port):
                    self.logger.warning(f"Server {server.host}:{server.port} is not available")
            
            # 注册负载均衡器
            self.load_balancers[config.name] = config
            
            self.logger.info(f"Load balancer {config.name} created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create load balancer {config.name}: {str(e)}")
            return False
    
    def _check_server_availability(self, host: str, port: int, timeout: int = 5) -> bool:
        """检查服务器可用性"""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.error, socket.timeout):
            return False
    
    def sync_with_application_manager(self) -> bool:
        """
        与应用管理器同步配置
        
        Returns:
            同步是否成功
        """
        try:
            if not self.application_manager:
                self.logger.warning("Application manager not configured")
                return False
            
            # 获取应用列表
            applications = self.application_manager.discover_applications()
            
            for app_info in applications:
                app_name = app_info["name"]
                
                # 检查是否已有虚拟主机配置
                if app_name not in self.virtual_hosts:
                    # 创建默认虚拟主机配置
                    vhost_config = self._create_default_vhost_from_app(app_info)
                    if vhost_config:
                        self.create_virtual_host(vhost_config)
                        self.logger.info(f"Created virtual host for application {app_name}")
                else:
                    # 更新现有配置
                    self._update_vhost_from_app(app_name, app_info)
            
            self.logger.info("Synchronized with application manager")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to sync with application manager: {str(e)}")
            return False
    
    def _create_default_vhost_from_app(self, app_info: Dict[str, Any]) -> Optional[VirtualHostConfig]:
        """从应用信息创建默认虚拟主机配置"""
        try:
            app_name = app_info["name"]
            port = app_info.get("port")
            domain = app_info.get("domain")
            
            if not port or not domain:
                self.logger.warning(f"Application {app_name} missing port or domain configuration")
                return None
            
            # 创建基本配置
            vhost_config = VirtualHostConfig(
                name=app_name,
                domain=domain,
                ssl_enabled=True,
                ssl_certificate=SSLCertificateConfig(domain=domain)
            )
            
            # 添加代理Location
            proxy_location = LocationConfig(
                path="/",
                config_type=NginxConfigType.PROXY,
                proxy_pass=f"http://127.0.0.1:{port}"
            )
            vhost_config.locations.append(proxy_location)
            
            return vhost_config
            
        except Exception as e:
            self.logger.error(f"Failed to create default vhost from app info: {str(e)}")
            return None
    
    def _update_vhost_from_app(self, vhost_name: str, app_info: Dict[str, Any]):
        """从应用信息更新虚拟主机配置"""
        try:
            if vhost_name not in self.virtual_hosts:
                return
            
            vhost = self.virtual_hosts[vhost_name]
            port = app_info.get("port")
            
            if port:
                # 更新代理端口
                for location in vhost.locations:
                    if location.config_type == NginxConfigType.PROXY and location.proxy_pass:
                        location.proxy_pass = f"http://127.0.0.1:{port}"
            
        except Exception as e:
            self.logger.error(f"Failed to update vhost from app info: {str(e)}")
    
    def get_virtual_host_status(self, vhost_name: str) -> Optional[Dict[str, Any]]:
        """
        获取虚拟主机状态
        
        Args:
            vhost_name: 虚拟主机名称
            
        Returns:
            状态信息字典
        """
        if vhost_name not in self.virtual_hosts:
            return None
        
        vhost = self.virtual_hosts[vhost_name]
        
        # 检查配置文件状态
        available_file = self.sites_available / f"{vhost_name}.conf"
        enabled_file = self.sites_enabled / f"{vhost_name}.conf"
        
        status = {
            "name": vhost_name,
            "domain": vhost.domain,
            "port": vhost.port,
            "ssl_enabled": vhost.ssl_enabled,
            "ssl_port": vhost.ssl_port if vhost.ssl_enabled else None,
            "config_exists": available_file.exists(),
            "enabled": enabled_file.exists() or enabled_file.is_symlink(),
            "locations": len(vhost.locations),
            "load_balancer": vhost.load_balancer.name if vhost.load_balancer else None
        }
        
        # 检查SSL证书状态
        if vhost.ssl_certificate:
            cert_info = self._check_ssl_certificate_status(vhost.ssl_certificate)
            status["ssl_certificate"] = cert_info
        
        return status
    
    def _check_ssl_certificate_status(self, ssl_cert: SSLCertificateConfig) -> Dict[str, Any]:
        """检查SSL证书状态"""
        cert_info = {
            "domain": ssl_cert.domain,
            "auto_renewal": ssl_cert.auto_renewal,
            "staging": ssl_cert.staging
        }
        
        try:
            if ssl_cert.cert_file:
                cert_path = Path(ssl_cert.cert_file)
            else:
                cert_path = Path(ssl_cert.cert_path) / ssl_cert.domain / "fullchain.pem"
            
            cert_info["cert_exists"] = cert_path.exists()
            
            if cert_path.exists():
                # 检查证书有效期
                result = subprocess.run(
                    ['openssl', 'x509', '-in', str(cert_path), '-noout', '-dates'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    cert_info["cert_valid"] = True
                    cert_info["cert_dates"] = result.stdout.strip()
                else:
                    cert_info["cert_valid"] = False
            
        except Exception as e:
            cert_info["error"] = str(e)
        
        return cert_info
    
    def list_virtual_hosts(self) -> List[Dict[str, Any]]:
        """
        列出所有虚拟主机
        
        Returns:
            虚拟主机状态列表
        """
        return [
            self.get_virtual_host_status(vhost_name)
            for vhost_name in self.virtual_hosts
        ]
    
    def backup_configurations(self, backup_dir: str) -> bool:
        """
        备份Nginx配置
        
        Args:
            backup_dir: 备份目录
            
        Returns:
            备份是否成功
        """
        try:
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_subdir = backup_path / f"nginx_backup_{timestamp}"
            backup_subdir.mkdir()
            
            # 备份sites-available
            sites_available_backup = backup_subdir / "sites-available"
            shutil.copytree(self.sites_available, sites_available_backup)
            
            # 备份sites-enabled
            sites_enabled_backup = backup_subdir / "sites-enabled"
            shutil.copytree(self.sites_enabled, sites_enabled_backup)
            
            # 备份主配置文件
            main_config = self.nginx_path / "nginx.conf"
            if main_config.exists():
                shutil.copy2(main_config, backup_subdir / "nginx.conf")
            
            # 保存虚拟主机注册信息
            registry_info = {
                "virtual_hosts": {name: asdict(vhost) for name, vhost in self.virtual_hosts.items()},
                "domain_registry": self.domain_registry,
                "port_registry": {str(port): list(vhosts) for port, vhosts in self.port_registry.items()},
                "load_balancers": {name: asdict(lb) for name, lb in self.load_balancers.items()},
                "ssl_certificates": {name: asdict(cert) for name, cert in self.ssl_certificates.items()}
            }
            
            registry_file = backup_subdir / "registry.json"
            registry_file.write_text(json.dumps(registry_info, indent=2, default=str))
            
            self.logger.info(f"Nginx configurations backed up to {backup_subdir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to backup configurations: {str(e)}")
            return False


# 示例配置创建函数
def create_sample_virtual_hosts() -> List[VirtualHostConfig]:
    """创建示例虚拟主机配置"""
    
    # 主站配置
    main_site = VirtualHostConfig(
        name="lawsker-main",
        domain="lawsker.com",
        ssl_enabled=True,
        ssl_certificate=SSLCertificateConfig(domain="lawsker.com"),
        server_name_aliases=["www.lawsker.com"],
        default_server=True
    )
    
    # 添加前端代理Location
    main_site.locations.append(LocationConfig(
        path="/",
        config_type=NginxConfigType.PROXY,
        proxy_pass="http://127.0.0.1:6060"
    ))
    
    # 添加API代理Location
    main_site.locations.append(LocationConfig(
        path="/api/",
        config_type=NginxConfigType.PROXY,
        proxy_pass="http://127.0.0.1:8000"
    ))
    
    # 管理后台配置
    admin_site = VirtualHostConfig(
        name="lawsker-admin",
        domain="admin.lawsker.com",
        ssl_enabled=True,
        ssl_certificate=SSLCertificateConfig(domain="admin.lawsker.com")
    )
    
    # 添加管理后台代理Location
    admin_site.locations.append(LocationConfig(
        path="/",
        config_type=NginxConfigType.PROXY,
        proxy_pass="http://127.0.0.1:6061"
    ))
    
    # 添加API代理Location
    admin_site.locations.append(LocationConfig(
        path="/api/",
        config_type=NginxConfigType.PROXY,
        proxy_pass="http://127.0.0.1:8000"
    ))
    
    # API服务配置（带负载均衡）
    api_site = VirtualHostConfig(
        name="lawsker-api",
        domain="api.lawsker.com",
        ssl_enabled=True,
        ssl_certificate=SSLCertificateConfig(domain="api.lawsker.com")
    )
    
    # 创建负载均衡器
    api_load_balancer = LoadBalancerConfig(
        name="api_backend",
        method=LoadBalanceMethod.LEAST_CONN,
        servers=[
            UpstreamServer(host="127.0.0.1", port=8000, weight=2),
            UpstreamServer(host="127.0.0.1", port=8001, weight=1)
        ]
    )
    api_site.load_balancer = api_load_balancer
    
    # 添加API Location
    api_site.locations.append(LocationConfig(
        path="/",
        config_type=NginxConfigType.PROXY
    ))
    
    return [main_site, admin_site, api_site]


if __name__ == "__main__":
    # 测试代码
    async def main():
        manager = NginxConfigManager()
        
        # 创建示例虚拟主机
        sample_vhosts = create_sample_virtual_hosts()
        
        for vhost in sample_vhosts:
            success = manager.create_virtual_host(vhost)
            print(f"Create virtual host {vhost.name}: {success}")
        
        # 生成配置
        for vhost_name in manager.virtual_hosts:
            config_content = manager.generate_configuration(vhost_name)
            if config_content:
                print(f"\n=== Configuration for {vhost_name} ===")
                print(config_content[:500] + "..." if len(config_content) > 500 else config_content)
        
        # 列出虚拟主机
        vhosts = manager.list_virtual_hosts()
        print(f"\nVirtual hosts: {len(vhosts)}")
        for vhost in vhosts:
            print(f"- {vhost['name']}: {vhost['domain']} (SSL: {vhost['ssl_enabled']})")
    
    asyncio.run(main())