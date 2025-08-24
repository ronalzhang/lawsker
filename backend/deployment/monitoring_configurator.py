"""
监控配置器
自动化部署和配置Prometheus、Grafana等监控组件
"""
import os
import json
import yaml
import shutil
import subprocess
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

from app.core.logging import get_logger
from app.services.grafana_service import GrafanaService

logger = get_logger(__name__)

@dataclass
class MonitoringConfig:
    """监控配置"""
    prometheus_port: int = 9090
    grafana_port: int = 3000
    alertmanager_port: int = 9093
    node_exporter_port: int = 9100
    retention_days: int = 30
    scrape_interval: str = "15s"
    evaluation_interval: str = "15s"
    alert_webhook: Optional[str] = None
    grafana_admin_password: str = "admin"
    enable_ssl: bool = True
    data_dir: str = "/opt/monitoring"

@dataclass
class MonitoringTarget:
    """监控目标"""
    job_name: str
    targets: List[str]
    metrics_path: str = "/metrics"
    scrape_interval: str = "15s"
    params: Optional[Dict[str, List[str]]] = None

class MonitoringConfigurator:
    """监控配置器"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.logger = get_logger(__name__)
        self.data_dir = Path(config.data_dir)
        self.prometheus_dir = self.data_dir / "prometheus"
        self.grafana_dir = self.data_dir / "grafana"
        self.alertmanager_dir = self.data_dir / "alertmanager"
        
    async def setup_monitoring_stack(self) -> Dict[str, Any]:
        """设置完整的监控堆栈"""
        self.logger.info("Setting up monitoring stack")
        
        setup_results = {
            "prometheus": {},
            "grafana": {},
            "alertmanager": {},
            "node_exporter": {},
            "targets": [],
            "status": "success",
            "errors": []
        }
        
        try:
            # 1. 创建目录结构
            await self._create_directories()
            
            # 2. 部署Prometheus
            prometheus_result = await self._deploy_prometheus()
            setup_results["prometheus"] = prometheus_result
            
            # 3. 部署Grafana
            grafana_result = await self._deploy_grafana()
            setup_results["grafana"] = grafana_result
            
            # 4. 部署Alertmanager
            alertmanager_result = await self._deploy_alertmanager()
            setup_results["alertmanager"] = alertmanager_result
            
            # 5. 部署Node Exporter
            node_exporter_result = await self._deploy_node_exporter()
            setup_results["node_exporter"] = node_exporter_result
            
            # 6. 配置监控目标
            targets_result = await self._configure_monitoring_targets()
            setup_results["targets"] = targets_result
            
            # 7. 验证监控堆栈
            verification_result = await self._verify_monitoring_stack()
            setup_results["verification"] = verification_result
            
            self.logger.info("Monitoring stack setup completed")
            return setup_results
            
        except Exception as e:
            self.logger.error(f"Monitoring stack setup failed: {str(e)}")
            setup_results["status"] = "error"
            setup_results["errors"].append(str(e))
            return setup_results
    
    async def _create_directories(self):
        """创建监控目录结构"""
        self.logger.info("Creating monitoring directories")
        
        directories = [
            self.data_dir,
            self.prometheus_dir,
            self.prometheus_dir / "data",
            self.prometheus_dir / "config",
            self.prometheus_dir / "rules",
            self.grafana_dir,
            self.grafana_dir / "data",
            self.grafana_dir / "dashboards",
            self.grafana_dir / "provisioning",
            self.grafana_dir / "provisioning" / "datasources",
            self.grafana_dir / "provisioning" / "dashboards",
            self.alertmanager_dir,
            self.alertmanager_dir / "data"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            # 设置适当的权限
            os.chmod(directory, 0o755)
    
    async def _deploy_prometheus(self) -> Dict[str, Any]:
        """部署Prometheus"""
        self.logger.info("Deploying Prometheus")
        
        try:
            # 1. 生成Prometheus配置
            prometheus_config = await self._generate_prometheus_config()
            config_file = self.prometheus_dir / "config" / "prometheus.yml"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(prometheus_config, f, default_flow_style=False, allow_unicode=True)
            
            # 2. 复制告警规则
            await self._copy_alert_rules()
            
            # 3. 创建Prometheus服务配置
            service_config = await self._create_prometheus_service()
            
            # 4. 启动Prometheus服务
            start_result = await self._start_prometheus_service()
            
            return {
                "status": "success",
                "config_file": str(config_file),
                "service_config": service_config,
                "start_result": start_result,
                "port": self.config.prometheus_port,
                "url": f"http://localhost:{self.config.prometheus_port}"
            }
            
        except Exception as e:
            self.logger.error(f"Prometheus deployment failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _generate_prometheus_config(self) -> Dict[str, Any]:
        """生成Prometheus配置"""
        config = {
            "global": {
                "scrape_interval": self.config.scrape_interval,
                "evaluation_interval": self.config.evaluation_interval,
                "external_labels": {
                    "cluster": "lawsker-prod",
                    "replica": "prometheus-1"
                }
            },
            "rule_files": [
                "rules/*.yml"
            ],
            "alerting": {
                "alertmanagers": [
                    {
                        "static_configs": [
                            {
                                "targets": [f"localhost:{self.config.alertmanager_port}"]
                            }
                        ]
                    }
                ]
            },
            "scrape_configs": [
                {
                    "job_name": "prometheus",
                    "static_configs": [
                        {
                            "targets": [f"localhost:{self.config.prometheus_port}"]
                        }
                    ]
                },
                {
                    "job_name": "node-exporter",
                    "static_configs": [
                        {
                            "targets": [f"localhost:{self.config.node_exporter_port}"]
                        }
                    ]
                },
                {
                    "job_name": "lawsker-backend",
                    "static_configs": [
                        {
                            "targets": ["localhost:8000"]
                        }
                    ],
                    "metrics_path": "/metrics",
                    "scrape_interval": "10s"
                },
                {
                    "job_name": "postgres",
                    "static_configs": [
                        {
                            "targets": ["localhost:9187"]
                        }
                    ]
                },
                {
                    "job_name": "redis",
                    "static_configs": [
                        {
                            "targets": ["localhost:9121"]
                        }
                    ]
                },
                {
                    "job_name": "nginx",
                    "static_configs": [
                        {
                            "targets": ["localhost:9113"]
                        }
                    ]
                }
            ],
            "storage": {
                "tsdb": {
                    "retention.time": f"{self.config.retention_days}d",
                    "retention.size": "10GB"
                }
            }
        }
        
        return config
    
    async def _copy_alert_rules(self):
        """复制告警规则文件"""
        source_rules = Path("monitoring/prometheus/rules")
        target_rules = self.prometheus_dir / "rules"
        
        if source_rules.exists():
            for rule_file in source_rules.glob("*.yml"):
                shutil.copy2(rule_file, target_rules)
                self.logger.info(f"Copied alert rule: {rule_file.name}")
    
    async def _create_prometheus_service(self) -> Dict[str, Any]:
        """创建Prometheus系统服务"""
        service_content = f"""[Unit]
Description=Prometheus Server
Documentation=https://prometheus.io/docs/
After=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/bin/prometheus \\
  --config.file={self.prometheus_dir}/config/prometheus.yml \\
  --storage.tsdb.path={self.prometheus_dir}/data \\
  --web.console.templates=/usr/local/share/prometheus/consoles \\
  --web.console.libraries=/usr/local/share/prometheus/console_libraries \\
  --web.listen-address=0.0.0.0:{self.config.prometheus_port} \\
  --web.external-url=http://localhost:{self.config.prometheus_port}/ \\
  --storage.tsdb.retention.time={self.config.retention_days}d
Restart=always
RestartSec=3
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path("/etc/systemd/system/prometheus.service")
        
        try:
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            # 重新加载systemd配置
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            subprocess.run(["sudo", "systemctl", "enable", "prometheus"], check=True)
            
            return {
                "status": "created",
                "service_file": str(service_file)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create Prometheus service: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _start_prometheus_service(self) -> Dict[str, Any]:
        """启动Prometheus服务"""
        try:
            # 检查服务是否已运行
            result = subprocess.run(
                ["sudo", "systemctl", "is-active", "prometheus"],
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip() == "active":
                self.logger.info("Prometheus service is already running")
                return {
                    "status": "already_running",
                    "message": "Prometheus service is already active"
                }
            
            # 启动服务
            subprocess.run(["sudo", "systemctl", "start", "prometheus"], check=True)
            
            # 等待服务启动
            await asyncio.sleep(5)
            
            # 验证服务状态
            result = subprocess.run(
                ["sudo", "systemctl", "is-active", "prometheus"],
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip() == "active":
                return {
                    "status": "started",
                    "message": "Prometheus service started successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to start Prometheus service"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to start Prometheus service: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _deploy_grafana(self) -> Dict[str, Any]:
        """部署Grafana"""
        self.logger.info("Deploying Grafana")
        
        try:
            # 1. 生成Grafana配置
            grafana_config = await self._generate_grafana_config()
            config_file = self.grafana_dir / "grafana.ini"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(grafana_config)
            
            # 2. 配置数据源
            await self._configure_grafana_datasources()
            
            # 3. 配置仪表盘
            await self._configure_grafana_dashboards()
            
            # 4. 创建Grafana服务
            service_config = await self._create_grafana_service()
            
            # 5. 启动Grafana服务
            start_result = await self._start_grafana_service()
            
            return {
                "status": "success",
                "config_file": str(config_file),
                "service_config": service_config,
                "start_result": start_result,
                "port": self.config.grafana_port,
                "url": f"http://localhost:{self.config.grafana_port}",
                "admin_password": self.config.grafana_admin_password
            }
            
        except Exception as e:
            self.logger.error(f"Grafana deployment failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _generate_grafana_config(self) -> str:
        """生成Grafana配置"""
        config = f"""[server]
http_port = {self.config.grafana_port}
domain = localhost
root_url = http://localhost:{self.config.grafana_port}/

[database]
type = sqlite3
path = {self.grafana_dir}/data/grafana.db

[security]
admin_user = admin
admin_password = {self.config.grafana_admin_password}
secret_key = SW2YcwTIb9zpOOhoPsMm

[users]
allow_sign_up = false
allow_org_create = false
auto_assign_org = true
auto_assign_org_role = Viewer

[auth.anonymous]
enabled = false

[log]
mode = file
level = info
root_path = {self.grafana_dir}/data/log

[paths]
data = {self.grafana_dir}/data
logs = {self.grafana_dir}/data/log
plugins = {self.grafana_dir}/data/plugins
provisioning = {self.grafana_dir}/provisioning

[alerting]
enabled = true

[unified_alerting]
enabled = true

[feature_toggles]
enable = ngalert
"""
        return config
    
    async def _configure_grafana_datasources(self):
        """配置Grafana数据源"""
        datasources_config = {
            "apiVersion": 1,
            "datasources": [
                {
                    "name": "Prometheus",
                    "type": "prometheus",
                    "access": "proxy",
                    "url": f"http://localhost:{self.config.prometheus_port}",
                    "isDefault": True,
                    "editable": True
                }
            ]
        }
        
        datasources_file = self.grafana_dir / "provisioning" / "datasources" / "datasources.yml"
        with open(datasources_file, 'w', encoding='utf-8') as f:
            yaml.dump(datasources_config, f, default_flow_style=False)
    
    async def _configure_grafana_dashboards(self):
        """配置Grafana仪表盘"""
        dashboards_config = {
            "apiVersion": 1,
            "providers": [
                {
                    "name": "lawsker-dashboards",
                    "orgId": 1,
                    "folder": "",
                    "type": "file",
                    "disableDeletion": False,
                    "updateIntervalSeconds": 10,
                    "allowUiUpdates": True,
                    "options": {
                        "path": str(self.grafana_dir / "dashboards")
                    }
                }
            ]
        }
        
        dashboards_file = self.grafana_dir / "provisioning" / "dashboards" / "dashboards.yml"
        with open(dashboards_file, 'w', encoding='utf-8') as f:
            yaml.dump(dashboards_config, f, default_flow_style=False)
    
    async def _create_grafana_service(self) -> Dict[str, Any]:
        """创建Grafana系统服务"""
        service_content = f"""[Unit]
Description=Grafana instance
Documentation=http://docs.grafana.org
Wants=network-online.target
After=network-online.target
After=postgresql.service mariadb.service mysql.service

[Service]
EnvironmentFile=/etc/default/grafana-server
User=grafana
Group=grafana
Type=simple
Restart=on-failure
WorkingDirectory=/usr/share/grafana
RuntimeDirectory=grafana
RuntimeDirectoryMode=0750
ExecStart=/usr/sbin/grafana-server \\
  --config={self.grafana_dir}/grafana.ini \\
  --pidfile=/var/run/grafana/grafana-server.pid \\
  --packaging=deb \\
  cfg:default.paths.logs={self.grafana_dir}/data/log \\
  cfg:default.paths.data={self.grafana_dir}/data \\
  cfg:default.paths.plugins={self.grafana_dir}/data/plugins \\
  cfg:default.paths.provisioning={self.grafana_dir}/provisioning

LimitNOFILE=10000
TimeoutStopSec=20

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path("/etc/systemd/system/grafana-server.service")
        
        try:
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            subprocess.run(["sudo", "systemctl", "enable", "grafana-server"], check=True)
            
            return {
                "status": "created",
                "service_file": str(service_file)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create Grafana service: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _start_grafana_service(self) -> Dict[str, Any]:
        """启动Grafana服务"""
        try:
            result = subprocess.run(
                ["sudo", "systemctl", "is-active", "grafana-server"],
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip() == "active":
                self.logger.info("Grafana service is already running")
                return {
                    "status": "already_running",
                    "message": "Grafana service is already active"
                }
            
            subprocess.run(["sudo", "systemctl", "start", "grafana-server"], check=True)
            await asyncio.sleep(10)  # Grafana需要更长时间启动
            
            result = subprocess.run(
                ["sudo", "systemctl", "is-active", "grafana-server"],
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip() == "active":
                return {
                    "status": "started",
                    "message": "Grafana service started successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to start Grafana service"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to start Grafana service: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _deploy_alertmanager(self) -> Dict[str, Any]:
        """部署Alertmanager"""
        self.logger.info("Deploying Alertmanager")
        
        try:
            # 生成Alertmanager配置
            alertmanager_config = await self._generate_alertmanager_config()
            config_file = self.alertmanager_dir / "alertmanager.yml"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(alertmanager_config, f, default_flow_style=False, allow_unicode=True)
            
            # 创建服务
            service_config = await self._create_alertmanager_service()
            
            # 启动服务
            start_result = await self._start_alertmanager_service()
            
            return {
                "status": "success",
                "config_file": str(config_file),
                "service_config": service_config,
                "start_result": start_result,
                "port": self.config.alertmanager_port,
                "url": f"http://localhost:{self.config.alertmanager_port}"
            }
            
        except Exception as e:
            self.logger.error(f"Alertmanager deployment failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _generate_alertmanager_config(self) -> Dict[str, Any]:
        """生成Alertmanager配置"""
        config = {
            "global": {
                "smtp_smarthost": "localhost:587",
                "smtp_from": "alerts@lawsker.com"
            },
            "route": {
                "group_by": ["alertname"],
                "group_wait": "10s",
                "group_interval": "10s",
                "repeat_interval": "1h",
                "receiver": "web.hook"
            },
            "receivers": [
                {
                    "name": "web.hook",
                    "webhook_configs": [
                        {
                            "url": self.config.alert_webhook or "http://localhost:8000/api/v1/alerts/webhook"
                        }
                    ]
                }
            ],
            "inhibit_rules": [
                {
                    "source_match": {
                        "severity": "critical"
                    },
                    "target_match": {
                        "severity": "warning"
                    },
                    "equal": ["alertname", "dev", "instance"]
                }
            ]
        }
        
        return config
    
    async def _create_alertmanager_service(self) -> Dict[str, Any]:
        """创建Alertmanager系统服务"""
        service_content = f"""[Unit]
Description=Alertmanager
Wants=network-online.target
After=network-online.target

[Service]
User=alertmanager
Group=alertmanager
Type=simple
ExecStart=/usr/local/bin/alertmanager \\
  --config.file={self.alertmanager_dir}/alertmanager.yml \\
  --storage.path={self.alertmanager_dir}/data \\
  --web.listen-address=0.0.0.0:{self.config.alertmanager_port}
Restart=always

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path("/etc/systemd/system/alertmanager.service")
        
        try:
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            subprocess.run(["sudo", "systemctl", "enable", "alertmanager"], check=True)
            
            return {
                "status": "created",
                "service_file": str(service_file)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create Alertmanager service: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _start_alertmanager_service(self) -> Dict[str, Any]:
        """启动Alertmanager服务"""
        try:
            result = subprocess.run(
                ["sudo", "systemctl", "is-active", "alertmanager"],
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip() == "active":
                return {
                    "status": "already_running",
                    "message": "Alertmanager service is already active"
                }
            
            subprocess.run(["sudo", "systemctl", "start", "alertmanager"], check=True)
            await asyncio.sleep(5)
            
            result = subprocess.run(
                ["sudo", "systemctl", "is-active", "alertmanager"],
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip() == "active":
                return {
                    "status": "started",
                    "message": "Alertmanager service started successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to start Alertmanager service"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to start Alertmanager service: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _deploy_node_exporter(self) -> Dict[str, Any]:
        """部署Node Exporter"""
        self.logger.info("Deploying Node Exporter")
        
        try:
            service_config = await self._create_node_exporter_service()
            start_result = await self._start_node_exporter_service()
            
            return {
                "status": "success",
                "service_config": service_config,
                "start_result": start_result,
                "port": self.config.node_exporter_port,
                "url": f"http://localhost:{self.config.node_exporter_port}"
            }
            
        except Exception as e:
            self.logger.error(f"Node Exporter deployment failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _create_node_exporter_service(self) -> Dict[str, Any]:
        """创建Node Exporter系统服务"""
        service_content = f"""[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter \\
  --web.listen-address=0.0.0.0:{self.config.node_exporter_port}
Restart=always

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path("/etc/systemd/system/node_exporter.service")
        
        try:
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            subprocess.run(["sudo", "systemctl", "enable", "node_exporter"], check=True)
            
            return {
                "status": "created",
                "service_file": str(service_file)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create Node Exporter service: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _start_node_exporter_service(self) -> Dict[str, Any]:
        """启动Node Exporter服务"""
        try:
            result = subprocess.run(
                ["sudo", "systemctl", "is-active", "node_exporter"],
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip() == "active":
                return {
                    "status": "already_running",
                    "message": "Node Exporter service is already active"
                }
            
            subprocess.run(["sudo", "systemctl", "start", "node_exporter"], check=True)
            await asyncio.sleep(3)
            
            result = subprocess.run(
                ["sudo", "systemctl", "is-active", "node_exporter"],
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip() == "active":
                return {
                    "status": "started",
                    "message": "Node Exporter service started successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to start Node Exporter service"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to start Node Exporter service: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _configure_monitoring_targets(self) -> List[Dict[str, Any]]:
        """配置监控目标自动发现"""
        self.logger.info("Configuring monitoring targets")
        
        targets = [
            MonitoringTarget(
                job_name="lawsker-backend",
                targets=["localhost:8000"],
                metrics_path="/metrics",
                scrape_interval="10s"
            ),
            MonitoringTarget(
                job_name="postgres-exporter",
                targets=["localhost:9187"],
                scrape_interval="30s"
            ),
            MonitoringTarget(
                job_name="redis-exporter",
                targets=["localhost:9121"],
                scrape_interval="30s"
            ),
            MonitoringTarget(
                job_name="nginx-exporter",
                targets=["localhost:9113"],
                scrape_interval="30s"
            )
        ]
        
        results = []
        
        for target in targets:
            try:
                # 验证目标可达性
                verification_result = await self._verify_monitoring_target(target)
                results.append({
                    "job_name": target.job_name,
                    "targets": target.targets,
                    "status": "configured" if verification_result else "unreachable",
                    "verification": verification_result
                })
                
            except Exception as e:
                self.logger.error(f"Failed to configure target {target.job_name}: {str(e)}")
                results.append({
                    "job_name": target.job_name,
                    "targets": target.targets,
                    "status": "error",
                    "message": str(e)
                })
        
        return results
    
    async def _verify_monitoring_target(self, target: MonitoringTarget) -> bool:
        """验证监控目标"""
        import aiohttp
        
        for target_url in target.targets:
            try:
                url = f"http://{target_url}{target.metrics_path}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            content = await response.text()
                            # 简单验证是否是Prometheus格式的指标
                            if "# HELP" in content or "# TYPE" in content:
                                self.logger.info(f"Target {target_url} is reachable and serving metrics")
                                return True
                            else:
                                self.logger.warning(f"Target {target_url} is reachable but not serving Prometheus metrics")
                                return False
                        else:
                            self.logger.warning(f"Target {target_url} returned status {response.status}")
                            return False
                            
            except Exception as e:
                self.logger.warning(f"Target {target_url} is not reachable: {str(e)}")
                return False
        
        return False
    
    async def _verify_monitoring_stack(self) -> Dict[str, Any]:
        """验证监控堆栈"""
        self.logger.info("Verifying monitoring stack")
        
        verification_results = {
            "prometheus": await self._verify_prometheus_health(),
            "grafana": await self._verify_grafana_health(),
            "alertmanager": await self._verify_alertmanager_health(),
            "node_exporter": await self._verify_node_exporter_health()
        }
        
        all_healthy = all(result["healthy"] for result in verification_results.values())
        
        return {
            "overall_status": "healthy" if all_healthy else "unhealthy",
            "components": verification_results
        }
    
    async def _verify_prometheus_health(self) -> Dict[str, Any]:
        """验证Prometheus健康状态"""
        import aiohttp
        
        try:
            url = f"http://localhost:{self.config.prometheus_port}/-/healthy"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        return {
                            "healthy": True,
                            "message": "Prometheus is healthy",
                            "url": f"http://localhost:{self.config.prometheus_port}"
                        }
                    else:
                        return {
                            "healthy": False,
                            "message": f"Prometheus health check failed with status {response.status}"
                        }
                        
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Prometheus health check failed: {str(e)}"
            }
    
    async def _verify_grafana_health(self) -> Dict[str, Any]:
        """验证Grafana健康状态"""
        import aiohttp
        
        try:
            url = f"http://localhost:{self.config.grafana_port}/api/health"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        return {
                            "healthy": True,
                            "message": "Grafana is healthy",
                            "url": f"http://localhost:{self.config.grafana_port}"
                        }
                    else:
                        return {
                            "healthy": False,
                            "message": f"Grafana health check failed with status {response.status}"
                        }
                        
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Grafana health check failed: {str(e)}"
            }
    
    async def _verify_alertmanager_health(self) -> Dict[str, Any]:
        """验证Alertmanager健康状态"""
        import aiohttp
        
        try:
            url = f"http://localhost:{self.config.alertmanager_port}/-/healthy"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        return {
                            "healthy": True,
                            "message": "Alertmanager is healthy",
                            "url": f"http://localhost:{self.config.alertmanager_port}"
                        }
                    else:
                        return {
                            "healthy": False,
                            "message": f"Alertmanager health check failed with status {response.status}"
                        }
                        
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Alertmanager health check failed: {str(e)}"
            }
    
    async def _verify_node_exporter_health(self) -> Dict[str, Any]:
        """验证Node Exporter健康状态"""
        import aiohttp
        
        try:
            url = f"http://localhost:{self.config.node_exporter_port}/metrics"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        content = await response.text()
                        if "node_" in content:
                            return {
                                "healthy": True,
                                "message": "Node Exporter is healthy",
                                "url": f"http://localhost:{self.config.node_exporter_port}"
                            }
                        else:
                            return {
                                "healthy": False,
                                "message": "Node Exporter is not serving node metrics"
                            }
                    else:
                        return {
                            "healthy": False,
                            "message": f"Node Exporter health check failed with status {response.status}"
                        }
                        
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Node Exporter health check failed: {str(e)}"
            }
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """获取监控系统状态"""
        self.logger.info("Getting monitoring system status")
        
        try:
            verification_result = await self._verify_monitoring_stack()
            
            return {
                "status": "success",
                "monitoring_stack": verification_result,
                "configuration": {
                    "prometheus_port": self.config.prometheus_port,
                    "grafana_port": self.config.grafana_port,
                    "alertmanager_port": self.config.alertmanager_port,
                    "node_exporter_port": self.config.node_exporter_port,
                    "retention_days": self.config.retention_days,
                    "data_directory": str(self.data_dir)
                },
                "urls": {
                    "prometheus": f"http://localhost:{self.config.prometheus_port}",
                    "grafana": f"http://localhost:{self.config.grafana_port}",
                    "alertmanager": f"http://localhost:{self.config.alertmanager_port}",
                    "node_exporter": f"http://localhost:{self.config.node_exporter_port}"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get monitoring status: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }