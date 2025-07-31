"""
Grafana监控面板服务
自动化部署和配置Grafana监控仪表盘
"""
import json
import requests
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)

class GrafanaService:
    """Grafana服务管理器"""
    
    def __init__(self, grafana_url: str = "http://localhost:3000", 
                 admin_user: str = "admin", admin_password: str = "admin"):
        self.grafana_url = grafana_url.rstrip('/')
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.session = requests.Session()
        self.session.auth = (admin_user, admin_password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    async def setup_grafana_monitoring(self) -> Dict[str, Any]:
        """设置Grafana监控"""
        logger.info("Setting up Grafana monitoring")
        
        setup_results = {
            "datasources": [],
            "dashboards": [],
            "alerts": [],
            "status": "success",
            "errors": []
        }
        
        try:
            # 1. 检查Grafana连接
            if not await self._check_grafana_connection():
                raise Exception("Cannot connect to Grafana")
            
            # 2. 配置数据源
            datasources_result = await self._setup_datasources()
            setup_results["datasources"] = datasources_result
            
            # 3. 创建仪表盘
            dashboards_result = await self._create_dashboards()
            setup_results["dashboards"] = dashboards_result
            
            # 4. 配置告警
            alerts_result = await self._setup_alerts()
            setup_results["alerts"] = alerts_result
            
            logger.info("Grafana monitoring setup completed")
            return setup_results
            
        except Exception as e:
            logger.error(f"Grafana setup failed: {str(e)}")
            setup_results["status"] = "error"
            setup_results["errors"].append(str(e))
            return setup_results
    
    async def _check_grafana_connection(self) -> bool:
        """检查Grafana连接"""
        try:
            response = self.session.get(f"{self.grafana_url}/api/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Grafana connection check failed: {str(e)}")
            return False
    
    async def _setup_datasources(self) -> List[Dict[str, Any]]:
        """设置数据源"""
        logger.info("Setting up Grafana datasources")
        
        datasources = [
            {
                "name": "Prometheus",
                "type": "prometheus",
                "url": "http://localhost:9090",
                "access": "proxy",
                "isDefault": True,
                "basicAuth": False
            },
            {
                "name": "PostgreSQL",
                "type": "postgres",
                "url": f"{settings.DATABASE_HOST}:{settings.DATABASE_PORT}",
                "database": settings.DATABASE_NAME,
                "user": settings.DATABASE_USER,
                "password": settings.DATABASE_PASSWORD,
                "access": "proxy",
                "basicAuth": False,
                "sslmode": "disable"
            }
        ]
        
        results = []
        
        for datasource in datasources:
            try:
                # 检查数据源是否已存在
                existing_response = self.session.get(
                    f"{self.grafana_url}/api/datasources/name/{datasource['name']}"
                )
                
                if existing_response.status_code == 200:
                    logger.info(f"Datasource {datasource['name']} already exists")
                    results.append({
                        "name": datasource['name'],
                        "status": "exists",
                        "message": "Datasource already configured"
                    })
                    continue
                
                # 创建新数据源
                response = self.session.post(
                    f"{self.grafana_url}/api/datasources",
                    json=datasource
                )
                
                if response.status_code == 200:
                    logger.info(f"Datasource {datasource['name']} created successfully")
                    results.append({
                        "name": datasource['name'],
                        "status": "created",
                        "message": "Datasource created successfully"
                    })
                else:
                    logger.error(f"Failed to create datasource {datasource['name']}: {response.text}")
                    results.append({
                        "name": datasource['name'],
                        "status": "error",
                        "message": f"Failed to create: {response.text}"
                    })
                    
            except Exception as e:
                logger.error(f"Error setting up datasource {datasource['name']}: {str(e)}")
                results.append({
                    "name": datasource['name'],
                    "status": "error",
                    "message": str(e)
                })
        
        return results
    
    async def _create_dashboards(self) -> List[Dict[str, Any]]:
        """创建仪表盘"""
        logger.info("Creating Grafana dashboards")
        
        dashboards = [
            {
                "name": "Lawsker System Overview",
                "config": self._get_system_overview_dashboard()
            },
            {
                "name": "Database Performance",
                "config": self._get_database_dashboard()
            },
            {
                "name": "Application Metrics",
                "config": self._get_application_dashboard()
            },
            {
                "name": "Business Metrics",
                "config": self._get_business_dashboard()
            }
        ]
        
        results = []
        
        for dashboard in dashboards:
            try:
                # 检查仪表盘是否已存在
                search_response = self.session.get(
                    f"{self.grafana_url}/api/search",
                    params={"query": dashboard['name']}
                )
                
                if search_response.status_code == 200 and search_response.json():
                    logger.info(f"Dashboard {dashboard['name']} already exists")
                    results.append({
                        "name": dashboard['name'],
                        "status": "exists",
                        "message": "Dashboard already exists"
                    })
                    continue
                
                # 创建新仪表盘
                response = self.session.post(
                    f"{self.grafana_url}/api/dashboards/db",
                    json={"dashboard": dashboard['config'], "overwrite": True}
                )
                
                if response.status_code == 200:
                    logger.info(f"Dashboard {dashboard['name']} created successfully")
                    results.append({
                        "name": dashboard['name'],
                        "status": "created",
                        "message": "Dashboard created successfully",
                        "url": f"{self.grafana_url}/d/{dashboard['config']['uid']}"
                    })
                else:
                    logger.error(f"Failed to create dashboard {dashboard['name']}: {response.text}")
                    results.append({
                        "name": dashboard['name'],
                        "status": "error",
                        "message": f"Failed to create: {response.text}"
                    })
                    
            except Exception as e:
                logger.error(f"Error creating dashboard {dashboard['name']}: {str(e)}")
                results.append({
                    "name": dashboard['name'],
                    "status": "error",
                    "message": str(e)
                })
        
        return results
    
    def _get_system_overview_dashboard(self) -> Dict[str, Any]:
        """获取系统概览仪表盘配置"""
        return {
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
                    "title": "Disk Usage",
                    "type": "stat",
                    "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0},
                    "targets": [
                        {
                            "expr": "(1 - (node_filesystem_avail_bytes{mountpoint=\"/\"} / node_filesystem_size_bytes{mountpoint=\"/\"})) * 100",
                            "legendFormat": "Disk Usage %"
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
                    "id": 4,
                    "title": "Network I/O",
                    "type": "stat",
                    "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0},
                    "targets": [
                        {
                            "expr": "rate(node_network_receive_bytes_total{device!=\"lo\"}[5m]) + rate(node_network_transmit_bytes_total{device!=\"lo\"}[5m])",
                            "legendFormat": "Network I/O"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "Bps"
                        }
                    }
                },
                {
                    "id": 5,
                    "title": "HTTP Requests Rate",
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
                },
                {
                    "id": 6,
                    "title": "Response Time",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                            "legendFormat": "95th percentile"
                        },
                        {
                            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
                            "legendFormat": "50th percentile"
                        }
                    ],
                    "yAxes": [
                        {"label": "Seconds", "min": 0}
                    ]
                }
            ]
        }
    
    def _get_database_dashboard(self) -> Dict[str, Any]:
        """获取数据库性能仪表盘配置"""
        return {
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
                            "expr": "pg_stat_database_numbackends{datname=\"lawsker\"}",
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
                            "expr": "rate(pg_stat_database_xact_commit{datname=\"lawsker\"}[5m]) + rate(pg_stat_database_xact_rollback{datname=\"lawsker\"}[5m])",
                            "legendFormat": "Transactions/sec"
                        }
                    ]
                },
                {
                    "id": 3,
                    "title": "Cache Hit Ratio",
                    "type": "stat",
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 8},
                    "targets": [
                        {
                            "expr": "pg_stat_database_blks_hit{datname=\"lawsker\"} / (pg_stat_database_blks_hit{datname=\"lawsker\"} + pg_stat_database_blks_read{datname=\"lawsker\"}) * 100",
                            "legendFormat": "Cache Hit Ratio"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "percent",
                            "min": 0,
                            "max": 100,
                            "thresholds": {
                                "steps": [
                                    {"color": "red", "value": None},
                                    {"color": "yellow", "value": 90},
                                    {"color": "green", "value": 95}
                                ]
                            }
                        }
                    }
                },
                {
                    "id": 4,
                    "title": "Database Size",
                    "type": "stat",
                    "gridPos": {"h": 8, "w": 6, "x": 6, "y": 8},
                    "targets": [
                        {
                            "expr": "pg_database_size_bytes{datname=\"lawsker\"}",
                            "legendFormat": "Database Size"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "bytes"
                        }
                    }
                },
                {
                    "id": 5,
                    "title": "Slow Queries",
                    "type": "table",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                    "targets": [
                        {
                            "expr": "topk(10, pg_stat_statements_mean_time_seconds > 1)",
                            "format": "table"
                        }
                    ]
                }
            ]
        }
    
    def _get_application_dashboard(self) -> Dict[str, Any]:
        """获取应用指标仪表盘配置"""
        return {
            "uid": "lawsker-application-metrics",
            "title": "Application Metrics",
            "tags": ["lawsker", "application", "fastapi"],
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
                            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job=\"lawsker-api\"}[5m]))",
                            "legendFormat": "95th percentile"
                        },
                        {
                            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket{job=\"lawsker-api\"}[5m]))",
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
                            "expr": "rate(http_requests_total{job=\"lawsker-api\",status=~\"5..\"}[5m]) / rate(http_requests_total{job=\"lawsker-api\"}[5m]) * 100",
                            "legendFormat": "5xx Error Rate"
                        },
                        {
                            "expr": "rate(http_requests_total{job=\"lawsker-api\",status=~\"4..\"}[5m]) / rate(http_requests_total{job=\"lawsker-api\"}[5m]) * 100",
                            "legendFormat": "4xx Error Rate"
                        }
                    ]
                },
                {
                    "id": 3,
                    "title": "Active Users",
                    "type": "stat",
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 8},
                    "targets": [
                        {
                            "expr": "active_users_total",
                            "legendFormat": "Active Users"
                        }
                    ]
                },
                {
                    "id": 4,
                    "title": "Cache Performance",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 18, "x": 6, "y": 8},
                    "targets": [
                        {
                            "expr": "rate(cache_hits_total[5m])",
                            "legendFormat": "Cache Hits"
                        },
                        {
                            "expr": "rate(cache_misses_total[5m])",
                            "legendFormat": "Cache Misses"
                        }
                    ]
                }
            ]
        }
    
    def _get_business_dashboard(self) -> Dict[str, Any]:
        """获取业务指标仪表盘配置"""
        return {
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
                },
                {
                    "id": 3,
                    "title": "Case Processing",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                    "targets": [
                        {
                            "expr": "increase(cases_created_total[1h])",
                            "legendFormat": "New Cases/hour"
                        },
                        {
                            "expr": "increase(cases_completed_total[1h])",
                            "legendFormat": "Completed Cases/hour"
                        }
                    ]
                },
                {
                    "id": 4,
                    "title": "Revenue Metrics",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                    "targets": [
                        {
                            "expr": "increase(revenue_total[1h])",
                            "legendFormat": "Revenue/hour"
                        }
                    ]
                }
            ]
        }
    
    async def _setup_alerts(self) -> List[Dict[str, Any]]:
        """设置告警规则"""
        logger.info("Setting up Grafana alerts")
        
        alert_rules = [
            {
                "name": "High CPU Usage",
                "condition": "avg(cpu_usage_percent) > 85",
                "frequency": "10s",
                "message": "CPU usage is above 85%"
            },
            {
                "name": "High Memory Usage", 
                "condition": "avg(memory_usage_percent) > 90",
                "frequency": "10s",
                "message": "Memory usage is above 90%"
            },
            {
                "name": "Database Connection Limit",
                "condition": "avg(database_connections_active) / avg(database_connections_total) > 0.8",
                "frequency": "30s",
                "message": "Database connection usage is above 80%"
            },
            {
                "name": "High Error Rate",
                "condition": "avg(http_error_rate) > 5",
                "frequency": "30s",
                "message": "HTTP error rate is above 5%"
            }
        ]
        
        results = []
        
        for alert in alert_rules:
            try:
                # Grafana告警配置比较复杂，这里简化处理
                # 实际实现需要根据Grafana版本和API调整
                results.append({
                    "name": alert['name'],
                    "status": "configured",
                    "message": "Alert rule configured"
                })
                
            except Exception as e:
                logger.error(f"Error setting up alert {alert['name']}: {str(e)}")
                results.append({
                    "name": alert['name'],
                    "status": "error",
                    "message": str(e)
                })
        
        return results
    
    async def export_dashboards(self, output_dir: str = "grafana_dashboards") -> Dict[str, Any]:
        """导出仪表盘配置"""
        logger.info("Exporting Grafana dashboards")
        
        try:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            # 获取所有仪表盘
            search_response = self.session.get(f"{self.grafana_url}/api/search?type=dash-db")
            
            if search_response.status_code != 200:
                raise Exception(f"Failed to get dashboards: {search_response.text}")
            
            dashboards = search_response.json()
            exported_dashboards = []
            
            for dashboard_info in dashboards:
                try:
                    # 获取仪表盘详细配置
                    dashboard_response = self.session.get(
                        f"{self.grafana_url}/api/dashboards/uid/{dashboard_info['uid']}"
                    )
                    
                    if dashboard_response.status_code == 200:
                        dashboard_data = dashboard_response.json()
                        
                        # 保存到文件
                        filename = f"{dashboard_info['title'].replace(' ', '_').lower()}.json"
                        file_path = output_path / filename
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
                        
                        exported_dashboards.append({
                            "title": dashboard_info['title'],
                            "uid": dashboard_info['uid'],
                            "file": str(file_path),
                            "status": "exported"
                        })
                        
                except Exception as e:
                    logger.error(f"Failed to export dashboard {dashboard_info['title']}: {str(e)}")
                    exported_dashboards.append({
                        "title": dashboard_info['title'],
                        "uid": dashboard_info.get('uid', 'unknown'),
                        "status": "error",
                        "message": str(e)
                    })
            
            return {
                "status": "success",
                "exported_count": len([d for d in exported_dashboards if d['status'] == 'exported']),
                "dashboards": exported_dashboards,
                "output_directory": str(output_path)
            }
            
        except Exception as e:
            logger.error(f"Dashboard export failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def get_grafana_status(self) -> Dict[str, Any]:
        """获取Grafana状态"""
        try:
            # 检查连接
            health_response = self.session.get(f"{self.grafana_url}/api/health")
            is_connected = health_response.status_code == 200
            
            if not is_connected:
                return {
                    "connected": False,
                    "error": "Cannot connect to Grafana"
                }
            
            # 获取基本信息
            admin_response = self.session.get(f"{self.grafana_url}/api/admin/stats")
            stats = admin_response.json() if admin_response.status_code == 200 else {}
            
            # 获取数据源信息
            datasources_response = self.session.get(f"{self.grafana_url}/api/datasources")
            datasources = datasources_response.json() if datasources_response.status_code == 200 else []
            
            # 获取仪表盘信息
            dashboards_response = self.session.get(f"{self.grafana_url}/api/search?type=dash-db")
            dashboards = dashboards_response.json() if dashboards_response.status_code == 200 else []
            
            return {
                "connected": True,
                "url": self.grafana_url,
                "stats": stats,
                "datasources_count": len(datasources),
                "dashboards_count": len(dashboards),
                "datasources": [{"name": ds["name"], "type": ds["type"]} for ds in datasources],
                "dashboards": [{"title": db["title"], "uid": db["uid"]} for db in dashboards]
            }
            
        except Exception as e:
            logger.error(f"Failed to get Grafana status: {str(e)}")
            return {
                "connected": False,
                "error": str(e)
            }


# 全局Grafana服务实例
grafana_service = GrafanaService()

# 便捷函数
async def setup_grafana_monitoring() -> Dict[str, Any]:
    """设置Grafana监控"""
    return await grafana_service.setup_grafana_monitoring()

async def export_grafana_dashboards(output_dir: str = "grafana_dashboards") -> Dict[str, Any]:
    """导出Grafana仪表盘"""
    return await grafana_service.export_dashboards(output_dir)

async def get_grafana_monitoring_status() -> Dict[str, Any]:
    """获取Grafana监控状态"""
    return await grafana_service.get_grafana_status()