"""
ELK Stack日志聚合服务
部署和配置Elasticsearch、Logstash、Kibana日志收集系统
"""
import json
import requests
import asyncio
import subprocess
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger(__name__)

class ELKService:
    """ELK Stack服务管理器"""
    
    def __init__(self, 
                 elasticsearch_url: str = "http://localhost:9200",
                 kibana_url: str = "http://localhost:5601",
                 logstash_url: str = "http://localhost:9600"):
        self.elasticsearch_url = elasticsearch_url.rstrip('/')
        self.kibana_url = kibana_url.rstrip('/')
        self.logstash_url = logstash_url.rstrip('/')
        
    async def setup_elk_stack(self) -> Dict[str, Any]:
        """设置ELK Stack"""
        logger.info("Setting up ELK Stack")
        
        setup_results = {
            "elasticsearch": {},
            "logstash": {},
            "kibana": {},
            "indices": [],
            "dashboards": [],
            "status": "success",
            "errors": []
        }
        
        try:
            # 1. 配置Elasticsearch
            elasticsearch_result = await self._setup_elasticsearch()
            setup_results["elasticsearch"] = elasticsearch_result
            
            # 2. 配置Logstash
            logstash_result = await self._setup_logstash()
            setup_results["logstash"] = logstash_result
            
            # 3. 配置Kibana
            kibana_result = await self._setup_kibana()
            setup_results["kibana"] = kibana_result
            
            # 4. 创建索引模板
            indices_result = await self._create_index_templates()
            setup_results["indices"] = indices_result
            
            # 5. 创建Kibana仪表盘
            dashboards_result = await self._create_kibana_dashboards()
            setup_results["dashboards"] = dashboards_result
            
            logger.info("ELK Stack setup completed")
            return setup_results
            
        except Exception as e:
            logger.error(f"ELK Stack setup failed: {str(e)}")
            setup_results["status"] = "error"
            setup_results["errors"].append(str(e))
            return setup_results
    
    async def _setup_elasticsearch(self) -> Dict[str, Any]:
        """设置Elasticsearch"""
        logger.info("Setting up Elasticsearch")
        
        try:
            # 检查Elasticsearch连接
            response = requests.get(f"{self.elasticsearch_url}/_cluster/health", timeout=10)
            
            if response.status_code != 200:
                return {
                    "status": "error",
                    "message": "Cannot connect to Elasticsearch"
                }
            
            cluster_health = response.json()
            
            # 创建索引生命周期策略
            await self._create_ilm_policies()
            
            # 配置集群设置
            await self._configure_cluster_settings()
            
            return {
                "status": "success",
                "cluster_name": cluster_health.get("cluster_name"),
                "cluster_status": cluster_health.get("status"),
                "number_of_nodes": cluster_health.get("number_of_nodes"),
                "message": "Elasticsearch configured successfully"
            }
            
        except Exception as e:
            logger.error(f"Elasticsearch setup failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _create_ilm_policies(self):
        """创建索引生命周期管理策略"""
        logger.info("Creating ILM policies")
        
        # 应用日志策略
        app_logs_policy = {
            "policy": {
                "phases": {
                    "hot": {
                        "actions": {
                            "rollover": {
                                "max_size": "1GB",
                                "max_age": "1d"
                            }
                        }
                    },
                    "warm": {
                        "min_age": "7d",
                        "actions": {
                            "allocate": {
                                "number_of_replicas": 0
                            }
                        }
                    },
                    "delete": {
                        "min_age": "30d"
                    }
                }
            }
        }
        
        # 访问日志策略
        access_logs_policy = {
            "policy": {
                "phases": {
                    "hot": {
                        "actions": {
                            "rollover": {
                                "max_size": "2GB",
                                "max_age": "1d"
                            }
                        }
                    },
                    "warm": {
                        "min_age": "3d",
                        "actions": {
                            "allocate": {
                                "number_of_replicas": 0
                            }
                        }
                    },
                    "delete": {
                        "min_age": "90d"
                    }
                }
            }
        }
        
        policies = {
            "lawsker-app-logs-policy": app_logs_policy,
            "lawsker-access-logs-policy": access_logs_policy
        }
        
        for policy_name, policy_config in policies.items():
            try:
                response = requests.put(
                    f"{self.elasticsearch_url}/_ilm/policy/{policy_name}",
                    json=policy_config,
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"ILM policy {policy_name} created successfully")
                else:
                    logger.error(f"Failed to create ILM policy {policy_name}: {response.text}")
                    
            except Exception as e:
                logger.error(f"Error creating ILM policy {policy_name}: {str(e)}")
    
    async def _configure_cluster_settings(self):
        """配置集群设置"""
        logger.info("Configuring cluster settings")
        
        cluster_settings = {
            "persistent": {
                "cluster.routing.allocation.disk.watermark.low": "85%",
                "cluster.routing.allocation.disk.watermark.high": "90%",
                "cluster.routing.allocation.disk.watermark.flood_stage": "95%",
                "indices.recovery.max_bytes_per_sec": "100mb"
            }
        }
        
        try:
            response = requests.put(
                f"{self.elasticsearch_url}/_cluster/settings",
                json=cluster_settings,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Cluster settings configured successfully")
            else:
                logger.error(f"Failed to configure cluster settings: {response.text}")
                
        except Exception as e:
            logger.error(f"Error configuring cluster settings: {str(e)}")
    
    async def _setup_logstash(self) -> Dict[str, Any]:
        """设置Logstash"""
        logger.info("Setting up Logstash")
        
        try:
            # 检查Logstash连接
            response = requests.get(f"{self.logstash_url}/_node/stats", timeout=10)
            
            if response.status_code != 200:
                return {
                    "status": "error",
                    "message": "Cannot connect to Logstash"
                }
            
            stats = response.json()
            
            return {
                "status": "success",
                "version": stats.get("version"),
                "pipeline": stats.get("pipeline", {}).get("main", {}),
                "message": "Logstash is running"
            }
            
        except Exception as e:
            logger.error(f"Logstash setup failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _setup_kibana(self) -> Dict[str, Any]:
        """设置Kibana"""
        logger.info("Setting up Kibana")
        
        try:
            # 检查Kibana连接
            response = requests.get(f"{self.kibana_url}/api/status", timeout=10)
            
            if response.status_code != 200:
                return {
                    "status": "error",
                    "message": "Cannot connect to Kibana"
                }
            
            status = response.json()
            
            # 创建索引模式
            await self._create_index_patterns()
            
            return {
                "status": "success",
                "version": status.get("version", {}).get("number"),
                "overall_status": status.get("status", {}).get("overall", {}).get("level"),
                "message": "Kibana configured successfully"
            }
            
        except Exception as e:
            logger.error(f"Kibana setup failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _create_index_patterns(self):
        """创建Kibana索引模式"""
        logger.info("Creating Kibana index patterns")
        
        index_patterns = [
            {
                "id": "lawsker-app-logs-*",
                "title": "lawsker-app-logs-*",
                "timeFieldName": "@timestamp"
            },
            {
                "id": "lawsker-access-logs-*",
                "title": "lawsker-access-logs-*",
                "timeFieldName": "@timestamp"
            },
            {
                "id": "lawsker-security-logs-*",
                "title": "lawsker-security-logs-*",
                "timeFieldName": "@timestamp"
            }
        ]
        
        for pattern in index_patterns:
            try:
                # Kibana API需要特定的头部
                headers = {
                    'Content-Type': 'application/json',
                    'kbn-xsrf': 'true'
                }
                
                response = requests.post(
                    f"{self.kibana_url}/api/saved_objects/index-pattern/{pattern['id']}",
                    json={
                        "attributes": {
                            "title": pattern["title"],
                            "timeFieldName": pattern["timeFieldName"]
                        }
                    },
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code in [200, 201, 409]:  # 409表示已存在
                    logger.info(f"Index pattern {pattern['title']} created/exists")
                else:
                    logger.error(f"Failed to create index pattern {pattern['title']}: {response.text}")
                    
            except Exception as e:
                logger.error(f"Error creating index pattern {pattern['title']}: {str(e)}")
    
    async def _create_index_templates(self) -> List[Dict[str, Any]]:
        """创建索引模板"""
        logger.info("Creating index templates")
        
        templates = [
            {
                "name": "lawsker-app-logs-template",
                "config": {
                    "index_patterns": ["lawsker-app-logs-*"],
                    "template": {
                        "settings": {
                            "number_of_shards": 1,
                            "number_of_replicas": 1,
                            "index.lifecycle.name": "lawsker-app-logs-policy",
                            "index.lifecycle.rollover_alias": "lawsker-app-logs"
                        },
                        "mappings": {
                            "properties": {
                                "@timestamp": {"type": "date"},
                                "level": {"type": "keyword"},
                                "logger": {"type": "keyword"},
                                "message": {"type": "text"},
                                "module": {"type": "keyword"},
                                "function": {"type": "keyword"},
                                "line": {"type": "integer"},
                                "thread": {"type": "keyword"},
                                "process": {"type": "keyword"},
                                "host": {"type": "keyword"},
                                "environment": {"type": "keyword"}
                            }
                        }
                    }
                }
            },
            {
                "name": "lawsker-access-logs-template",
                "config": {
                    "index_patterns": ["lawsker-access-logs-*"],
                    "template": {
                        "settings": {
                            "number_of_shards": 1,
                            "number_of_replicas": 1,
                            "index.lifecycle.name": "lawsker-access-logs-policy",
                            "index.lifecycle.rollover_alias": "lawsker-access-logs"
                        },
                        "mappings": {
                            "properties": {
                                "@timestamp": {"type": "date"},
                                "remote_addr": {"type": "ip"},
                                "remote_user": {"type": "keyword"},
                                "request": {"type": "text"},
                                "status": {"type": "integer"},
                                "body_bytes_sent": {"type": "long"},
                                "http_referer": {"type": "text"},
                                "http_user_agent": {"type": "text"},
                                "request_time": {"type": "float"},
                                "upstream_response_time": {"type": "float"},
                                "method": {"type": "keyword"},
                                "url": {"type": "keyword"},
                                "protocol": {"type": "keyword"},
                                "host": {"type": "keyword"}
                            }
                        }
                    }
                }
            }
        ]
        
        results = []
        
        for template in templates:
            try:
                response = requests.put(
                    f"{self.elasticsearch_url}/_index_template/{template['name']}",
                    json=template['config'],
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Index template {template['name']} created successfully")
                    results.append({
                        "name": template['name'],
                        "status": "created",
                        "message": "Template created successfully"
                    })
                else:
                    logger.error(f"Failed to create index template {template['name']}: {response.text}")
                    results.append({
                        "name": template['name'],
                        "status": "error",
                        "message": f"Failed to create: {response.text}"
                    })
                    
            except Exception as e:
                logger.error(f"Error creating index template {template['name']}: {str(e)}")
                results.append({
                    "name": template['name'],
                    "status": "error",
                    "message": str(e)
                })
        
        return results
    
    async def _create_kibana_dashboards(self) -> List[Dict[str, Any]]:
        """创建Kibana仪表盘"""
        logger.info("Creating Kibana dashboards")
        
        dashboards = [
            {
                "id": "lawsker-application-logs",
                "title": "Lawsker Application Logs",
                "config": self._get_application_logs_dashboard()
            },
            {
                "id": "lawsker-access-logs",
                "title": "Lawsker Access Logs",
                "config": self._get_access_logs_dashboard()
            },
            {
                "id": "lawsker-security-logs",
                "title": "Lawsker Security Logs",
                "config": self._get_security_logs_dashboard()
            }
        ]
        
        results = []
        
        for dashboard in dashboards:
            try:
                headers = {
                    'Content-Type': 'application/json',
                    'kbn-xsrf': 'true'
                }
                
                response = requests.post(
                    f"{self.kibana_url}/api/saved_objects/dashboard/{dashboard['id']}",
                    json={"attributes": dashboard['config']},
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code in [200, 201, 409]:
                    logger.info(f"Dashboard {dashboard['title']} created/exists")
                    results.append({
                        "title": dashboard['title'],
                        "status": "created",
                        "url": f"{self.kibana_url}/app/dashboards#/view/{dashboard['id']}"
                    })
                else:
                    logger.error(f"Failed to create dashboard {dashboard['title']}: {response.text}")
                    results.append({
                        "title": dashboard['title'],
                        "status": "error",
                        "message": f"Failed to create: {response.text}"
                    })
                    
            except Exception as e:
                logger.error(f"Error creating dashboard {dashboard['title']}: {str(e)}")
                results.append({
                    "title": dashboard['title'],
                    "status": "error",
                    "message": str(e)
                })
        
        return results
    
    def _get_application_logs_dashboard(self) -> Dict[str, Any]:
        """获取应用日志仪表盘配置"""
        return {
            "title": "Lawsker Application Logs",
            "type": "dashboard",
            "description": "Application logs monitoring dashboard",
            "panelsJSON": json.dumps([
                {
                    "version": "8.0.0",
                    "type": "visualization",
                    "gridData": {"x": 0, "y": 0, "w": 24, "h": 15},
                    "panelIndex": "1",
                    "embeddableConfig": {},
                    "panelRefName": "panel_1"
                }
            ]),
            "timeRestore": False,
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "query": {"match_all": {}},
                    "filter": []
                })
            }
        }
    
    def _get_access_logs_dashboard(self) -> Dict[str, Any]:
        """获取访问日志仪表盘配置"""
        return {
            "title": "Lawsker Access Logs",
            "type": "dashboard",
            "description": "Access logs monitoring dashboard",
            "panelsJSON": json.dumps([]),
            "timeRestore": False,
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "query": {"match_all": {}},
                    "filter": []
                })
            }
        }
    
    def _get_security_logs_dashboard(self) -> Dict[str, Any]:
        """获取安全日志仪表盘配置"""
        return {
            "title": "Lawsker Security Logs",
            "type": "dashboard",
            "description": "Security logs monitoring dashboard",
            "panelsJSON": json.dumps([]),
            "timeRestore": False,
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "query": {"match_all": {}},
                    "filter": []
                })
            }
        }
    
    async def get_elk_status(self) -> Dict[str, Any]:
        """获取ELK Stack状态"""
        status = {
            "elasticsearch": {"connected": False},
            "logstash": {"connected": False},
            "kibana": {"connected": False}
        }
        
        # 检查Elasticsearch
        try:
            response = requests.get(f"{self.elasticsearch_url}/_cluster/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                status["elasticsearch"] = {
                    "connected": True,
                    "cluster_name": health.get("cluster_name"),
                    "status": health.get("status"),
                    "number_of_nodes": health.get("number_of_nodes")
                }
        except Exception as e:
            status["elasticsearch"]["error"] = str(e)
        
        # 检查Logstash
        try:
            response = requests.get(f"{self.logstash_url}/_node/stats", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                status["logstash"] = {
                    "connected": True,
                    "version": stats.get("version"),
                    "uptime": stats.get("jvm", {}).get("uptime_in_millis")
                }
        except Exception as e:
            status["logstash"]["error"] = str(e)
        
        # 检查Kibana
        try:
            response = requests.get(f"{self.kibana_url}/api/status", timeout=5)
            if response.status_code == 200:
                kibana_status = response.json()
                status["kibana"] = {
                    "connected": True,
                    "version": kibana_status.get("version", {}).get("number"),
                    "status": kibana_status.get("status", {}).get("overall", {}).get("level")
                }
        except Exception as e:
            status["kibana"]["error"] = str(e)
        
        return status
    
    async def search_logs(self, index: str, query: Dict[str, Any], size: int = 100) -> Dict[str, Any]:
        """搜索日志"""
        try:
            response = requests.post(
                f"{self.elasticsearch_url}/{index}/_search",
                json={
                    "query": query,
                    "size": size,
                    "sort": [{"@timestamp": {"order": "desc"}}]
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Search failed: {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}


# 全局ELK服务实例
elk_service = ELKService()

# 便捷函数
async def setup_elk_logging() -> Dict[str, Any]:
    """设置ELK日志系统"""
    return await elk_service.setup_elk_stack()

async def get_elk_stack_status() -> Dict[str, Any]:
    """获取ELK Stack状态"""
    return await elk_service.get_elk_status()

async def search_application_logs(query: str, hours: int = 24) -> Dict[str, Any]:
    """搜索应用日志"""
    search_query = {
        "bool": {
            "must": [
                {"match": {"message": query}},
                {
                    "range": {
                        "@timestamp": {
                            "gte": f"now-{hours}h"
                        }
                    }
                }
            ]
        }
    }
    
    return await elk_service.search_logs("lawsker-app-logs-*", search_query)