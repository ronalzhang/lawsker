"""
Grafana仪表板管理器
自动化管理Grafana仪表板的创建、更新、备份和恢复
"""
import os
import json
import yaml
import shutil
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class DashboardTemplate:
    """仪表板模板"""
    name: str
    uid: str
    title: str
    tags: List[str]
    template_file: str
    variables: Optional[Dict[str, Any]] = None

@dataclass
class DataSourceConfig:
    """数据源配置"""
    name: str
    type: str
    url: str
    access: str = "proxy"
    is_default: bool = False
    basic_auth: bool = False
    database: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None

class GrafanaDashboardManager:
    """Grafana仪表板管理器"""
    
    def __init__(self, grafana_url: str = "http://localhost:3000", 
                 admin_user: str = "admin", admin_password: str = "admin"):
        self.grafana_url = grafana_url.rstrip('/')
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.logger = get_logger(__name__)
        self.session = None
        self.templates_dir = Path("monitoring/grafana/dashboards")
        self.backup_dir = Path("monitoring/grafana/backups")
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            auth=aiohttp.BasicAuth(self.admin_user, self.admin_password),
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def setup_dashboard_management(self) -> Dict[str, Any]:
        """设置仪表板管理"""
        self.logger.info("Setting up Grafana dashboard management")
        
        setup_results = {
            "datasources": [],
            "dashboards": [],
            "templates": [],
            "backup_config": {},
            "status": "success",
            "errors": []
        }
        
        try:
            # 1. 检查Grafana连接
            if not await self._check_grafana_connection():
                raise Exception("Cannot connect to Grafana")
            
            # 2. 创建目录结构
            await self._create_directories()
            
            # 3. 配置数据源
            datasources_result = await self._setup_datasources()
            setup_results["datasources"] = datasources_result
            
            # 4. 导入仪表板模板
            templates_result = await self._import_dashboard_templates()
            setup_results["templates"] = templates_result
            
            # 5. 创建默认仪表板
            dashboards_result = await self._create_default_dashboards()
            setup_results["dashboards"] = dashboards_result
            
            # 6. 配置备份
            backup_result = await self._setup_backup_configuration()
            setup_results["backup_config"] = backup_result
            
            self.logger.info("Dashboard management setup completed")
            return setup_results
            
        except Exception as e:
            self.logger.error(f"Dashboard management setup failed: {str(e)}")
            setup_results["status"] = "error"
            setup_results["errors"].append(str(e))
            return setup_results
    
    async def _check_grafana_connection(self) -> bool:
        """检查Grafana连接"""
        try:
            async with self.session.get(f"{self.grafana_url}/api/health") as response:
                return response.status == 200
        except Exception as e:
            self.logger.error(f"Grafana connection check failed: {str(e)}")
            return False
    
    async def _create_directories(self):
        """创建目录结构"""
        directories = [
            self.templates_dir,
            self.backup_dir,
            Path("monitoring/grafana/provisioning/dashboards"),
            Path("monitoring/grafana/provisioning/datasources")
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def _setup_datasources(self) -> List[Dict[str, Any]]:
        """设置数据源"""
        self.logger.info("Setting up Grafana datasources")
        
        datasources = [
            DataSourceConfig(
                name="Prometheus",
                type="prometheus",
                url="http://localhost:9090",
                is_default=True
            ),
            DataSourceConfig(
                name="PostgreSQL",
                type="postgres",
                url="localhost:5432",
                database="lawsker_prod",
                user="lawsker_user",
                password="your_password"  # 应该从环境变量获取
            ),
            DataSourceConfig(
                name="Loki",
                type="loki",
                url="http://localhost:3100"
            )
        ]
        
        results = []
        
        for datasource in datasources:
            try:
                result = await self._create_or_update_datasource(datasource)
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Error setting up datasource {datasource.name}: {str(e)}")
                results.append({
                    "name": datasource.name,
                    "status": "error",
                    "message": str(e)
                })
        
        return results
    
    async def _create_or_update_datasource(self, datasource: DataSourceConfig) -> Dict[str, Any]:
        """创建或更新数据源"""
        # 检查数据源是否已存在
        async with self.session.get(f"{self.grafana_url}/api/datasources/name/{datasource.name}") as response:
            if response.status == 200:
                existing_ds = await response.json()
                self.logger.info(f"Datasource {datasource.name} already exists, updating...")
                
                # 更新数据源
                update_data = self._build_datasource_config(datasource)
                update_data["id"] = existing_ds["id"]
                
                async with self.session.put(
                    f"{self.grafana_url}/api/datasources/{existing_ds['id']}",
                    json=update_data
                ) as update_response:
                    if update_response.status == 200:
                        return {
                            "name": datasource.name,
                            "status": "updated",
                            "message": "Datasource updated successfully"
                        }
                    else:
                        error_text = await update_response.text()
                        return {
                            "name": datasource.name,
                            "status": "error",
                            "message": f"Failed to update: {error_text}"
                        }
            
            elif response.status == 404:
                # 创建新数据源
                create_data = self._build_datasource_config(datasource)
                
                async with self.session.post(
                    f"{self.grafana_url}/api/datasources",
                    json=create_data
                ) as create_response:
                    if create_response.status == 200:
                        return {
                            "name": datasource.name,
                            "status": "created",
                            "message": "Datasource created successfully"
                        }
                    else:
                        error_text = await create_response.text()
                        return {
                            "name": datasource.name,
                            "status": "error",
                            "message": f"Failed to create: {error_text}"
                        }
            
            else:
                error_text = await response.text()
                return {
                    "name": datasource.name,
                    "status": "error",
                    "message": f"Failed to check existing datasource: {error_text}"
                }
    
    def _build_datasource_config(self, datasource: DataSourceConfig) -> Dict[str, Any]:
        """构建数据源配置"""
        config = {
            "name": datasource.name,
            "type": datasource.type,
            "url": datasource.url,
            "access": datasource.access,
            "isDefault": datasource.is_default,
            "basicAuth": datasource.basic_auth
        }
        
        if datasource.database:
            config["database"] = datasource.database
        
        if datasource.user:
            config["user"] = datasource.user
        
        if datasource.password:
            config["secureJsonData"] = {
                "password": datasource.password
            }
        
        return config
    
    async def _import_dashboard_templates(self) -> List[Dict[str, Any]]:
        """导入仪表板模板"""
        self.logger.info("Importing dashboard templates")
        
        # 创建默认模板
        await self._create_default_templates()
        
        results = []
        
        # 扫描模板目录
        if self.templates_dir.exists():
            for template_file in self.templates_dir.glob("*.json"):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                    
                    result = await self._validate_dashboard_template(template_data, template_file.name)
                    results.append(result)
                    
                except Exception as e:
                    self.logger.error(f"Error importing template {template_file.name}: {str(e)}")
                    results.append({
                        "template": template_file.name,
                        "status": "error",
                        "message": str(e)
                    })
        
        return results
    
    async def _create_default_templates(self):
        """创建默认仪表板模板"""
        templates = {
            "system_overview.json": self._get_system_overview_template(),
            "application_metrics.json": self._get_application_metrics_template(),
            "database_performance.json": self._get_database_performance_template(),
            "business_metrics.json": self._get_business_metrics_template(),
            "security_monitoring.json": self._get_security_monitoring_template()
        }
        
        for filename, template in templates.items():
            template_file = self.templates_dir / filename
            
            if not template_file.exists():
                with open(template_file, 'w', encoding='utf-8') as f:
                    json.dump(template, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"Created template: {filename}")
    
    def _get_system_overview_template(self) -> Dict[str, Any]:
        """获取系统概览模板"""
        return {
            "dashboard": {
                "uid": "lawsker-system-overview",
                "title": "Lawsker System Overview",
                "tags": ["lawsker", "system", "overview"],
                "timezone": "browser",
                "refresh": "30s",
                "time": {
                    "from": "now-1h",
                    "to": "now"
                },
                "panels": [
                    {
                        "id": 1,
                        "title": "CPU Usage",
                        "type": "stat",
                        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                        "targets": [
                            {
                                "expr": "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
                                "legendFormat": "CPU Usage %"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "percent",
                                "min": 0,
                                "max": 100,
                                "thresholds": {
                                    "steps": [
                                        {"color": "green", "value": None},
                                        {"color": "yellow", "value": 70},
                                        {"color": "red", "value": 85}
                                    ]
                                }
                            }
                        }
                    },
                    {
                        "id": 2,
                        "title": "Memory Usage",
                        "type": "stat",
                        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0},
                        "targets": [
                            {
                                "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
                                "legendFormat": "Memory Usage %"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "percent",
                                "min": 0,
                                "max": 100,
                                "thresholds": {
                                    "steps": [
                                        {"color": "green", "value": None},
                                        {"color": "yellow", "value": 80},
                                        {"color": "red", "value": 90}
                                    ]
                                }
                            }
                        }
                    },
                    {
                        "id": 3,
                        "title": "HTTP Request Rate",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                        "targets": [
                            {
                                "expr": "rate(http_requests_total[5m])",
                                "legendFormat": "{{method}} {{status}}"
                            }
                        ],
                        "yAxes": [
                            {"label": "Requests/sec", "min": 0}
                        ]
                    }
                ]
            }
        }
    
    def _get_application_metrics_template(self) -> Dict[str, Any]:
        """获取应用指标模板"""
        return {
            "dashboard": {
                "uid": "lawsker-application-metrics",
                "title": "Lawsker Application Metrics",
                "tags": ["lawsker", "application", "api"],
                "timezone": "browser",
                "refresh": "30s",
                "time": {
                    "from": "now-1h",
                    "to": "now"
                },
                "panels": [
                    {
                        "id": 1,
                        "title": "API Response Times",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job=\"lawsker-backend\"}[5m]))",
                                "legendFormat": "95th percentile"
                            },
                            {
                                "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket{job=\"lawsker-backend\"}[5m]))",
                                "legendFormat": "Median"
                            }
                        ]
                    },
                    {
                        "id": 2,
                        "title": "Error Rate",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                        "targets": [
                            {
                                "expr": "rate(http_requests_total{job=\"lawsker-backend\",status=~\"5..\"}[5m]) / rate(http_requests_total{job=\"lawsker-backend\"}[5m]) * 100",
                                "legendFormat": "5xx Error Rate"
                            }
                        ]
                    }
                ]
            }
        }
    
    def _get_database_performance_template(self) -> Dict[str, Any]:
        """获取数据库性能模板"""
        return {
            "dashboard": {
                "uid": "lawsker-database-performance",
                "title": "Database Performance",
                "tags": ["lawsker", "database", "postgresql"],
                "timezone": "browser",
                "refresh": "30s",
                "time": {
                    "from": "now-1h",
                    "to": "now"
                },
                "panels": [
                    {
                        "id": 1,
                        "title": "Database Connections",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "targets": [
                            {
                                "expr": "pg_stat_database_numbackends{datname=\"lawsker_prod\"}",
                                "legendFormat": "Active Connections"
                            }
                        ]
                    },
                    {
                        "id": 2,
                        "title": "Query Rate",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                        "targets": [
                            {
                                "expr": "rate(pg_stat_database_xact_commit{datname=\"lawsker_prod\"}[5m]) + rate(pg_stat_database_xact_rollback{datname=\"lawsker_prod\"}[5m])",
                                "legendFormat": "Transactions/sec"
                            }
                        ]
                    }
                ]
            }
        }
    
    def _get_business_metrics_template(self) -> Dict[str, Any]:
        """获取业务指标模板"""
        return {
            "dashboard": {
                "uid": "lawsker-business-metrics",
                "title": "Business Metrics",
                "tags": ["lawsker", "business", "kpi"],
                "timezone": "browser",
                "refresh": "5m",
                "time": {
                    "from": "now-24h",
                    "to": "now"
                },
                "panels": [
                    {
                        "id": 1,
                        "title": "Daily Active Users",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "targets": [
                            {
                                "expr": "daily_active_users",
                                "legendFormat": "DAU"
                            }
                        ]
                    },
                    {
                        "id": 2,
                        "title": "New Registrations",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                        "targets": [
                            {
                                "expr": "increase(user_registrations_total[1h])",
                                "legendFormat": "New Users/hour"
                            }
                        ]
                    }
                ]
            }
        }
    
    def _get_security_monitoring_template(self) -> Dict[str, Any]:
        """获取安全监控模板"""
        return {
            "dashboard": {
                "uid": "lawsker-security-monitoring",
                "title": "Security Monitoring",
                "tags": ["lawsker", "security", "monitoring"],
                "timezone": "browser",
                "refresh": "1m",
                "time": {
                    "from": "now-1h",
                    "to": "now"
                },
                "panels": [
                    {
                        "id": 1,
                        "title": "Failed Login Attempts",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "targets": [
                            {
                                "expr": "increase(failed_login_attempts_total[5m])",
                                "legendFormat": "Failed Logins"
                            }
                        ]
                    },
                    {
                        "id": 2,
                        "title": "Rate Limit Violations",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                        "targets": [
                            {
                                "expr": "increase(rate_limit_exceeded_total[1m])",
                                "legendFormat": "Rate Limit Hits"
                            }
                        ]
                    }
                ]
            }
        }
    
    async def _validate_dashboard_template(self, template_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """验证仪表板模板"""
        try:
            # 基本结构验证
            if "dashboard" not in template_data:
                return {
                    "template": filename,
                    "status": "error",
                    "message": "Missing 'dashboard' key in template"
                }
            
            dashboard = template_data["dashboard"]
            required_fields = ["uid", "title", "panels"]
            
            for field in required_fields:
                if field not in dashboard:
                    return {
                        "template": filename,
                        "status": "error",
                        "message": f"Missing required field: {field}"
                    }
            
            # 验证面板配置
            panels = dashboard.get("panels", [])
            for panel in panels:
                if "id" not in panel or "title" not in panel:
                    return {
                        "template": filename,
                        "status": "error",
                        "message": "Panel missing required fields (id, title)"
                    }
            
            return {
                "template": filename,
                "status": "valid",
                "message": "Template validation passed",
                "panels_count": len(panels)
            }
            
        except Exception as e:
            return {
                "template": filename,
                "status": "error",
                "message": f"Template validation failed: {str(e)}"
            }
    
    async def _create_default_dashboards(self) -> List[Dict[str, Any]]:
        """创建默认仪表板"""
        self.logger.info("Creating default dashboards")
        
        results = []
        
        # 获取所有模板文件
        if self.templates_dir.exists():
            for template_file in self.templates_dir.glob("*.json"):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                    
                    result = await self._create_dashboard_from_template(template_data, template_file.name)
                    results.append(result)
                    
                except Exception as e:
                    self.logger.error(f"Error creating dashboard from {template_file.name}: {str(e)}")
                    results.append({
                        "template": template_file.name,
                        "status": "error",
                        "message": str(e)
                    })
        
        return results
    
    async def _create_dashboard_from_template(self, template_data: Dict[str, Any], template_name: str) -> Dict[str, Any]:
        """从模板创建仪表板"""
        try:
            dashboard = template_data["dashboard"]
            dashboard_uid = dashboard["uid"]
            
            # 检查仪表板是否已存在
            async with self.session.get(f"{self.grafana_url}/api/dashboards/uid/{dashboard_uid}") as response:
                if response.status == 200:
                    self.logger.info(f"Dashboard {dashboard['title']} already exists, updating...")
                    
                    # 更新现有仪表板
                    update_data = {
                        "dashboard": dashboard,
                        "overwrite": True
                    }
                    
                    async with self.session.post(
                        f"{self.grafana_url}/api/dashboards/db",
                        json=update_data
                    ) as update_response:
                        if update_response.status == 200:
                            response_data = await update_response.json()
                            return {
                                "template": template_name,
                                "dashboard_title": dashboard["title"],
                                "dashboard_uid": dashboard_uid,
                                "status": "updated",
                                "url": f"{self.grafana_url}/d/{dashboard_uid}",
                                "message": "Dashboard updated successfully"
                            }
                        else:
                            error_text = await update_response.text()
                            return {
                                "template": template_name,
                                "status": "error",
                                "message": f"Failed to update dashboard: {error_text}"
                            }
                
                elif response.status == 404:
                    # 创建新仪表板
                    create_data = {
                        "dashboard": dashboard,
                        "overwrite": False
                    }
                    
                    async with self.session.post(
                        f"{self.grafana_url}/api/dashboards/db",
                        json=create_data
                    ) as create_response:
                        if create_response.status == 200:
                            response_data = await create_response.json()
                            return {
                                "template": template_name,
                                "dashboard_title": dashboard["title"],
                                "dashboard_uid": dashboard_uid,
                                "status": "created",
                                "url": f"{self.grafana_url}/d/{dashboard_uid}",
                                "message": "Dashboard created successfully"
                            }
                        else:
                            error_text = await create_response.text()
                            return {
                                "template": template_name,
                                "status": "error",
                                "message": f"Failed to create dashboard: {error_text}"
                            }
                
                else:
                    error_text = await response.text()
                    return {
                        "template": template_name,
                        "status": "error",
                        "message": f"Failed to check existing dashboard: {error_text}"
                    }
                    
        except Exception as e:
            return {
                "template": template_name,
                "status": "error",
                "message": f"Dashboard creation failed: {str(e)}"
            }
    
    async def _setup_backup_configuration(self) -> Dict[str, Any]:
        """设置备份配置"""
        self.logger.info("Setting up backup configuration")
        
        try:
            # 创建备份目录
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建备份脚本
            backup_script = await self._create_backup_script()
            
            # 设置定时备份（可选）
            cron_config = await self._setup_backup_cron()
            
            return {
                "status": "success",
                "backup_directory": str(self.backup_dir),
                "backup_script": backup_script,
                "cron_config": cron_config,
                "message": "Backup configuration completed"
            }
            
        except Exception as e:
            self.logger.error(f"Backup configuration failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _create_backup_script(self) -> str:
        """创建备份脚本"""
        script_content = f"""#!/bin/bash
# Grafana Dashboard Backup Script
# Generated automatically by GrafanaDashboardManager

GRAFANA_URL="{self.grafana_url}"
BACKUP_DIR="{self.backup_dir}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/grafana_backup_$TIMESTAMP.tar.gz"

echo "Starting Grafana backup at $(date)"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Export all dashboards
python3 -c "
import asyncio
from backend.deployment.grafana_dashboard_manager import GrafanaDashboardManager

async def backup():
    async with GrafanaDashboardManager('{self.grafana_url}', '{self.admin_user}', '{self.admin_password}') as manager:
        result = await manager.backup_all_dashboards('$BACKUP_DIR/dashboards_$TIMESTAMP')
        print(f'Backup result: {{result}}')

asyncio.run(backup())
"

# Create compressed archive
if [ -d "$BACKUP_DIR/dashboards_$TIMESTAMP" ]; then
    tar -czf "$BACKUP_FILE" -C "$BACKUP_DIR" "dashboards_$TIMESTAMP"
    rm -rf "$BACKUP_DIR/dashboards_$TIMESTAMP"
    echo "Backup completed: $BACKUP_FILE"
else
    echo "Backup failed: No dashboards directory created"
    exit 1
fi

# Clean up old backups (keep last 7 days)
find "$BACKUP_DIR" -name "grafana_backup_*.tar.gz" -mtime +7 -delete

echo "Backup process completed at $(date)"
"""
        
        script_file = Path("scripts/backup-grafana-dashboards.sh")
        script_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        # 设置执行权限
        os.chmod(script_file, 0o755)
        
        return str(script_file)
    
    async def _setup_backup_cron(self) -> Dict[str, Any]:
        """设置定时备份"""
        try:
            cron_entry = "0 2 * * * /path/to/scripts/backup-grafana-dashboards.sh >> /var/log/grafana-backup.log 2>&1"
            
            return {
                "status": "configured",
                "cron_entry": cron_entry,
                "schedule": "Daily at 2:00 AM",
                "log_file": "/var/log/grafana-backup.log",
                "message": "Add this entry to crontab manually: crontab -e"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def backup_all_dashboards(self, output_dir: str) -> Dict[str, Any]:
        """备份所有仪表板"""
        self.logger.info("Backing up all dashboards")
        
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 获取所有仪表板
            async with self.session.get(f"{self.grafana_url}/api/search?type=dash-db") as response:
                if response.status != 200:
                    raise Exception(f"Failed to get dashboards list: {await response.text()}")
                
                dashboards = await response.json()
            
            backed_up_dashboards = []
            
            for dashboard_info in dashboards:
                try:
                    # 获取仪表板详细配置
                    async with self.session.get(
                        f"{self.grafana_url}/api/dashboards/uid/{dashboard_info['uid']}"
                    ) as dashboard_response:
                        if dashboard_response.status == 200:
                            dashboard_data = await dashboard_response.json()
                            
                            # 保存到文件
                            filename = f"{dashboard_info['title'].replace(' ', '_').lower()}.json"
                            file_path = output_path / filename
                            
                            with open(file_path, 'w', encoding='utf-8') as f:
                                json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
                            
                            backed_up_dashboards.append({
                                "title": dashboard_info['title'],
                                "uid": dashboard_info['uid'],
                                "file": str(file_path),
                                "status": "backed_up"
                            })
                            
                except Exception as e:
                    self.logger.error(f"Failed to backup dashboard {dashboard_info['title']}: {str(e)}")
                    backed_up_dashboards.append({
                        "title": dashboard_info['title'],
                        "uid": dashboard_info.get('uid', 'unknown'),
                        "status": "error",
                        "message": str(e)
                    })
            
            return {
                "status": "success",
                "backed_up_count": len([d for d in backed_up_dashboards if d['status'] == 'backed_up']),
                "dashboards": backed_up_dashboards,
                "output_directory": str(output_path),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Dashboard backup failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def restore_dashboards(self, backup_dir: str) -> Dict[str, Any]:
        """恢复仪表板"""
        self.logger.info(f"Restoring dashboards from {backup_dir}")
        
        try:
            backup_path = Path(backup_dir)
            
            if not backup_path.exists():
                raise Exception(f"Backup directory does not exist: {backup_dir}")
            
            restored_dashboards = []
            
            for dashboard_file in backup_path.glob("*.json"):
                try:
                    with open(dashboard_file, 'r', encoding='utf-8') as f:
                        dashboard_data = json.load(f)
                    
                    # 恢复仪表板
                    restore_data = {
                        "dashboard": dashboard_data["dashboard"],
                        "overwrite": True
                    }
                    
                    async with self.session.post(
                        f"{self.grafana_url}/api/dashboards/db",
                        json=restore_data
                    ) as response:
                        if response.status == 200:
                            response_data = await response.json()
                            restored_dashboards.append({
                                "file": dashboard_file.name,
                                "title": dashboard_data["dashboard"]["title"],
                                "uid": dashboard_data["dashboard"]["uid"],
                                "status": "restored",
                                "url": f"{self.grafana_url}/d/{dashboard_data['dashboard']['uid']}"
                            })
                        else:
                            error_text = await response.text()
                            restored_dashboards.append({
                                "file": dashboard_file.name,
                                "status": "error",
                                "message": f"Failed to restore: {error_text}"
                            })
                            
                except Exception as e:
                    self.logger.error(f"Failed to restore dashboard {dashboard_file.name}: {str(e)}")
                    restored_dashboards.append({
                        "file": dashboard_file.name,
                        "status": "error",
                        "message": str(e)
                    })
            
            return {
                "status": "success",
                "restored_count": len([d for d in restored_dashboards if d['status'] == 'restored']),
                "dashboards": restored_dashboards,
                "backup_directory": str(backup_path)
            }
            
        except Exception as e:
            self.logger.error(f"Dashboard restore failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def get_dashboard_status(self) -> Dict[str, Any]:
        """获取仪表板状态"""
        try:
            # 获取所有仪表板
            async with self.session.get(f"{self.grafana_url}/api/search?type=dash-db") as response:
                if response.status != 200:
                    raise Exception(f"Failed to get dashboards: {await response.text()}")
                
                dashboards = await response.json()
            
            # 获取数据源
            async with self.session.get(f"{self.grafana_url}/api/datasources") as response:
                if response.status != 200:
                    raise Exception(f"Failed to get datasources: {await response.text()}")
                
                datasources = await response.json()
            
            return {
                "status": "success",
                "dashboards_count": len(dashboards),
                "datasources_count": len(datasources),
                "dashboards": [
                    {
                        "title": db["title"],
                        "uid": db["uid"],
                        "url": f"{self.grafana_url}/d/{db['uid']}"
                    }
                    for db in dashboards
                ],
                "datasources": [
                    {
                        "name": ds["name"],
                        "type": ds["type"],
                        "url": ds.get("url", "")
                    }
                    for ds in datasources
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get dashboard status: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }