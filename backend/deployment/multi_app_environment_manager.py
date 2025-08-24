#!/usr/bin/env python3
"""
多应用环境管理器 - MultiAppEnvironmentManager类
整合ApplicationManager和NginxConfigManager，提供完整的多应用环境支持
"""

import os
import sys
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import yaml

# 导入应用管理器和Nginx配置管理器
from .application_manager import (
    ApplicationManager, ApplicationConfig, ApplicationInstance, 
    ResourceQuota, ApplicationStatus
)
from .nginx_config_manager import (
    NginxConfigManager, VirtualHostConfig, LocationConfig, 
    SSLCertificateConfig, LoadBalancerConfig, UpstreamServer,
    NginxConfigType, LoadBalanceMethod, SecurityConfig
)


@dataclass
class EnvironmentConfig:
    """环境配置"""
    name: str
    description: str = ""
    base_domain: str = "lawsker.com"
    ssl_enabled: bool = True
    monitoring_enabled: bool = True
    backup_enabled: bool = True
    
    # 目录配置
    app_config_dir: str = "/etc/lawsker/applications"
    nginx_config_dir: str = "/etc/nginx"
    ssl_cert_dir: str = "/etc/letsencrypt/live"
    
    # 默认资源配额
    default_resource_quota: ResourceQuota = None
    
    # 安全配置
    default_security_config: SecurityConfig = None
    
    def __post_init__(self):
        if self.default_resource_quota is None:
            self.default_resource_quota = ResourceQuota()
        if self.default_security_config is None:
            self.default_security_config = SecurityConfig()


class MultiAppEnvironmentManager:
    """
    多应用环境管理器
    
    整合应用管理和Nginx配置管理，提供：
    - 应用隔离和资源分配
    - Nginx虚拟主机管理
    - 端口和域名冲突检测
    - 应用间通信配置
    """
    
    def __init__(self, config: EnvironmentConfig):
        self.config = config
        self.logger = self._setup_logger()
        
        # 初始化子管理器
        self.app_manager = ApplicationManager(config.app_config_dir)
        self.nginx_manager = NginxConfigManager(
            nginx_path=config.nginx_config_dir,
            application_manager=self.app_manager
        )
        
        # 环境状态
        self.environment_status = "stopped"
        self.deployed_applications: Set[str] = set()
        self.active_virtual_hosts: Set[str] = set()
        
        # 冲突检测缓存
        self._port_conflicts: Dict[int, List[str]] = {}
        self._domain_conflicts: Dict[str, List[str]] = {}
    
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
            log_file = Path(self.config.app_config_dir) / "multi_app_environment.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    async def initialize_environment(self) -> bool:
        """
        初始化多应用环境
        
        Returns:
            初始化是否成功
        """
        try:
            self.logger.info(f"Initializing multi-app environment: {self.config.name}")
            
            # 启动应用管理器的资源监控
            await self.app_manager.start_resource_monitoring()
            
            # 同步应用管理器和Nginx配置管理器
            self.nginx_manager.sync_with_application_manager()
            
            # 检测现有冲突
            await self._detect_conflicts()
            
            self.environment_status = "initialized"
            self.logger.info("Multi-app environment initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize environment: {str(e)}")
            return False
    
    async def deploy_application(self, app_config: ApplicationConfig, 
                                auto_create_vhost: bool = True) -> bool:
        """
        部署应用到环境
        
        Args:
            app_config: 应用配置
            auto_create_vhost: 是否自动创建虚拟主机
            
        Returns:
            部署是否成功
        """
        try:
            self.logger.info(f"Deploying application: {app_config.name}")
            
            # 检查冲突
            conflicts = await self._check_application_conflicts(app_config)
            if conflicts:
                self.logger.error(f"Application conflicts detected: {conflicts}")
                return False
            
            # 应用默认资源配额
            if not app_config.resource_quota or app_config.resource_quota == ResourceQuota():
                app_config.resource_quota = self.config.default_resource_quota
            
            # 注册应用
            if not self.app_manager.register_application(app_config):
                self.logger.error(f"Failed to register application: {app_config.name}")
                return False
            
            # 自动创建虚拟主机配置
            if auto_create_vhost and app_config.domain:
                vhost_config = self._create_vhost_from_app_config(app_config)
                if vhost_config:
                    if not self.nginx_manager.create_virtual_host(vhost_config):
                        self.logger.error(f"Failed to create virtual host for: {app_config.name}")
                        # 回滚应用注册
                        self.app_manager.unregister_application(app_config.name)
                        return False
                    
                    # 部署虚拟主机配置
                    if not self.nginx_manager.deploy_virtual_host(app_config.name):
                        self.logger.error(f"Failed to deploy virtual host for: {app_config.name}")
                        # 回滚
                        self.nginx_manager.delete_virtual_host(app_config.name)
                        self.app_manager.unregister_application(app_config.name)
                        return False
                    
                    self.active_virtual_hosts.add(app_config.name)
            
            # 启动应用
            if await self.app_manager.start_application(app_config.name):
                self.deployed_applications.add(app_config.name)
                self.logger.info(f"Application {app_config.name} deployed successfully")
                return True
            else:
                self.logger.error(f"Failed to start application: {app_config.name}")
                # 回滚
                if app_config.name in self.active_virtual_hosts:
                    self.nginx_manager.delete_virtual_host(app_config.name)
                    self.active_virtual_hosts.discard(app_config.name)
                self.app_manager.unregister_application(app_config.name)
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to deploy application {app_config.name}: {str(e)}")
            return False
    
    async def undeploy_application(self, app_name: str) -> bool:
        """
        从环境中移除应用
        
        Args:
            app_name: 应用名称
            
        Returns:
            移除是否成功
        """
        try:
            self.logger.info(f"Undeploying application: {app_name}")
            
            # 停止应用
            if app_name in self.deployed_applications:
                await self.app_manager.stop_application(app_name)
                self.deployed_applications.discard(app_name)
            
            # 删除虚拟主机配置
            if app_name in self.active_virtual_hosts:
                self.nginx_manager.disable_virtual_host(app_name)
                self.nginx_manager.delete_virtual_host(app_name)
                self.nginx_manager.reload_nginx()
                self.active_virtual_hosts.discard(app_name)
            
            # 注销应用
            self.app_manager.unregister_application(app_name)
            
            self.logger.info(f"Application {app_name} undeployed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to undeploy application {app_name}: {str(e)}")
            return False
    
    async def scale_application(self, app_name: str, instances: int) -> bool:
        """
        扩缩容应用
        
        Args:
            app_name: 应用名称
            instances: 实例数量
            
        Returns:
            扩缩容是否成功
        """
        try:
            self.logger.info(f"Scaling application {app_name} to {instances} instances")
            
            if app_name not in self.deployed_applications:
                self.logger.error(f"Application {app_name} is not deployed")
                return False
            
            # 获取应用配置
            app_status = self.app_manager.get_application_status(app_name)
            if not app_status:
                self.logger.error(f"Application {app_name} not found")
                return False
            
            # 创建负载均衡器配置
            if instances > 1:
                # 创建多个上游服务器
                base_port = app_status.get("port", 8000)
                servers = []
                
                for i in range(instances):
                    server = UpstreamServer(
                        host="127.0.0.1",
                        port=base_port + i,
                        weight=1
                    )
                    servers.append(server)
                
                lb_config = LoadBalancerConfig(
                    name=f"{app_name}_backend",
                    method=LoadBalanceMethod.ROUND_ROBIN,
                    servers=servers
                )
                
                # 更新虚拟主机配置
                if app_name in self.active_virtual_hosts:
                    vhost = self.nginx_manager.virtual_hosts.get(app_name)
                    if vhost:
                        vhost.load_balancer = lb_config
                        # 更新Location配置为使用负载均衡器
                        for location in vhost.locations:
                            if location.config_type == NginxConfigType.PROXY:
                                location.proxy_pass = None  # 使用负载均衡器
                        
                        # 重新部署配置
                        self.nginx_manager.deploy_virtual_host(app_name)
            
            self.logger.info(f"Application {app_name} scaled to {instances} instances")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to scale application {app_name}: {str(e)}")
            return False
    
    def _create_vhost_from_app_config(self, app_config: ApplicationConfig) -> Optional[VirtualHostConfig]:
        """从应用配置创建虚拟主机配置"""
        try:
            if not app_config.domain:
                return None
            
            # 创建虚拟主机配置
            vhost_config = VirtualHostConfig(
                name=app_config.name,
                domain=app_config.domain,
                ssl_enabled=self.config.ssl_enabled and app_config.ssl_enabled,
                security=self.config.default_security_config
            )
            
            # 配置SSL证书
            if vhost_config.ssl_enabled:
                vhost_config.ssl_certificate = SSLCertificateConfig(
                    domain=app_config.domain,
                    cert_path=self.config.ssl_cert_dir
                )
            
            # 创建主要Location配置
            if app_config.port:
                main_location = LocationConfig(
                    path="/",
                    config_type=NginxConfigType.PROXY,
                    proxy_pass=f"http://{app_config.host}:{app_config.port}"
                )
                vhost_config.locations.append(main_location)
            
            # 添加健康检查Location
            health_location = LocationConfig(
                path="/health",
                config_type=NginxConfigType.PROXY,
                proxy_pass=f"http://{app_config.host}:{app_config.port}/health" if app_config.port else None
            )
            vhost_config.locations.append(health_location)
            
            return vhost_config
            
        except Exception as e:
            self.logger.error(f"Failed to create vhost from app config: {str(e)}")
            return None
    
    async def _check_application_conflicts(self, app_config: ApplicationConfig) -> List[str]:
        """检查应用配置冲突"""
        conflicts = []
        
        try:
            # 检查端口冲突
            if app_config.port:
                if app_config.port in self._port_conflicts:
                    conflicts.append(f"Port {app_config.port} already in use by: {self._port_conflicts[app_config.port]}")
                
                # 检查系统端口占用
                import socket
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        result = s.connect_ex((app_config.host, app_config.port))
                        if result == 0:
                            conflicts.append(f"Port {app_config.port} is already in use by system")
                except:
                    pass
            
            # 检查域名冲突
            if app_config.domain:
                if app_config.domain in self._domain_conflicts:
                    conflicts.append(f"Domain {app_config.domain} already in use by: {self._domain_conflicts[app_config.domain]}")
            
            # 检查应用名称冲突
            if app_config.name in self.app_manager.applications:
                conflicts.append(f"Application name {app_config.name} already exists")
            
            return conflicts
            
        except Exception as e:
            self.logger.error(f"Failed to check application conflicts: {str(e)}")
            return [f"Error checking conflicts: {str(e)}"]
    
    async def _detect_conflicts(self):
        """检测现有的端口和域名冲突"""
        try:
            self._port_conflicts.clear()
            self._domain_conflicts.clear()
            
            # 检测应用管理器中的冲突
            applications = self.app_manager.discover_applications()
            for app in applications:
                app_name = app["name"]
                port = app.get("port")
                domain = app.get("domain")
                
                if port:
                    if port not in self._port_conflicts:
                        self._port_conflicts[port] = []
                    self._port_conflicts[port].append(app_name)
                
                if domain:
                    if domain not in self._domain_conflicts:
                        self._domain_conflicts[domain] = []
                    self._domain_conflicts[domain].append(app_name)
            
            # 检测Nginx配置管理器中的冲突
            for vhost_name, vhost in self.nginx_manager.virtual_hosts.items():
                if vhost.port not in self._port_conflicts:
                    self._port_conflicts[vhost.port] = []
                self._port_conflicts[vhost.port].append(f"nginx:{vhost_name}")
                
                if vhost.ssl_enabled:
                    if vhost.ssl_port not in self._port_conflicts:
                        self._port_conflicts[vhost.ssl_port] = []
                    self._port_conflicts[vhost.ssl_port].append(f"nginx:{vhost_name}")
                
                if vhost.domain not in self._domain_conflicts:
                    self._domain_conflicts[vhost.domain] = []
                self._domain_conflicts[vhost.domain].append(f"nginx:{vhost_name}")
            
            # 记录冲突
            for port, apps in self._port_conflicts.items():
                if len(apps) > 1:
                    self.logger.warning(f"Port conflict detected on {port}: {apps}")
            
            for domain, apps in self._domain_conflicts.items():
                if len(apps) > 1:
                    self.logger.warning(f"Domain conflict detected on {domain}: {apps}")
                    
        except Exception as e:
            self.logger.error(f"Failed to detect conflicts: {str(e)}")
    
    async def start_environment(self) -> bool:
        """
        启动整个环境
        
        Returns:
            启动是否成功
        """
        try:
            self.logger.info("Starting multi-app environment")
            
            # 按依赖顺序启动所有应用
            start_results = await self.app_manager.start_dependency_ordered_applications()
            
            # 检查启动结果
            failed_apps = [app for app, success in start_results.items() if not success]
            if failed_apps:
                self.logger.error(f"Failed to start applications: {failed_apps}")
                return False
            
            # 部署所有虚拟主机配置
            deploy_results = self.nginx_manager.deploy_all_virtual_hosts()
            failed_vhosts = [vhost for vhost, success in deploy_results.items() if not success]
            if failed_vhosts:
                self.logger.error(f"Failed to deploy virtual hosts: {failed_vhosts}")
                return False
            
            self.environment_status = "running"
            self.deployed_applications.update(start_results.keys())
            self.active_virtual_hosts.update(deploy_results.keys())
            
            self.logger.info("Multi-app environment started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start environment: {str(e)}")
            return False
    
    async def stop_environment(self) -> bool:
        """
        停止整个环境
        
        Returns:
            停止是否成功
        """
        try:
            self.logger.info("Stopping multi-app environment")
            
            # 按依赖顺序停止所有应用
            stop_results = await self.app_manager.stop_dependency_ordered_applications()
            
            # 禁用所有虚拟主机
            for vhost_name in self.active_virtual_hosts:
                self.nginx_manager.disable_virtual_host(vhost_name)
            
            # 重载Nginx配置
            self.nginx_manager.reload_nginx()
            
            self.environment_status = "stopped"
            self.deployed_applications.clear()
            self.active_virtual_hosts.clear()
            
            self.logger.info("Multi-app environment stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop environment: {str(e)}")
            return False
    
    async def restart_environment(self) -> bool:
        """
        重启整个环境
        
        Returns:
            重启是否成功
        """
        try:
            self.logger.info("Restarting multi-app environment")
            
            # 停止环境
            if not await self.stop_environment():
                return False
            
            # 等待一段时间
            await asyncio.sleep(5)
            
            # 启动环境
            return await self.start_environment()
            
        except Exception as e:
            self.logger.error(f"Failed to restart environment: {str(e)}")
            return False
    
    def get_environment_status(self) -> Dict[str, Any]:
        """
        获取环境状态
        
        Returns:
            环境状态信息
        """
        try:
            # 获取应用状态
            applications = self.app_manager.discover_applications()
            
            # 获取虚拟主机状态
            virtual_hosts = self.nginx_manager.list_virtual_hosts()
            
            # 获取冲突信息
            port_conflicts = {
                port: apps for port, apps in self._port_conflicts.items()
                if len(apps) > 1
            }
            domain_conflicts = {
                domain: apps for domain, apps in self._domain_conflicts.items()
                if len(apps) > 1
            }
            
            status = {
                "environment": {
                    "name": self.config.name,
                    "status": self.environment_status,
                    "base_domain": self.config.base_domain,
                    "ssl_enabled": self.config.ssl_enabled
                },
                "applications": {
                    "total": len(applications),
                    "running": len([app for app in applications if app["status"] == "running"]),
                    "deployed": len(self.deployed_applications),
                    "details": applications
                },
                "virtual_hosts": {
                    "total": len(virtual_hosts),
                    "active": len(self.active_virtual_hosts),
                    "details": virtual_hosts
                },
                "conflicts": {
                    "ports": port_conflicts,
                    "domains": domain_conflicts
                },
                "resources": {
                    "monitoring_enabled": self.config.monitoring_enabled,
                    "backup_enabled": self.config.backup_enabled
                }
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get environment status: {str(e)}")
            return {"error": str(e)}
    
    async def backup_environment(self, backup_dir: str) -> bool:
        """
        备份整个环境配置
        
        Args:
            backup_dir: 备份目录
            
        Returns:
            备份是否成功
        """
        try:
            self.logger.info("Backing up multi-app environment")
            
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            env_backup_dir = backup_path / f"environment_backup_{timestamp}"
            env_backup_dir.mkdir()
            
            # 备份应用配置
            app_backup_dir = env_backup_dir / "applications"
            app_backup_dir.mkdir()
            
            # 复制应用配置文件
            import shutil
            if Path(self.config.app_config_dir).exists():
                shutil.copytree(self.config.app_config_dir, app_backup_dir / "configs")
            
            # 备份Nginx配置
            nginx_success = self.nginx_manager.backup_configurations(str(env_backup_dir / "nginx"))
            
            # 保存环境状态
            env_status = self.get_environment_status()
            status_file = env_backup_dir / "environment_status.json"
            status_file.write_text(json.dumps(env_status, indent=2, default=str))
            
            # 保存环境配置
            env_config_dict = asdict(self.config)
            config_file = env_backup_dir / "environment_config.json"
            config_file.write_text(json.dumps(env_config_dict, indent=2, default=str))
            
            self.logger.info(f"Environment backed up to {env_backup_dir}")
            return nginx_success
            
        except Exception as e:
            self.logger.error(f"Failed to backup environment: {str(e)}")
            return False
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 停止应用管理器
            await self.app_manager.cleanup()
            
            self.logger.info("Multi-app environment manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")


# 示例配置和使用
def create_sample_environment() -> EnvironmentConfig:
    """创建示例环境配置"""
    return EnvironmentConfig(
        name="lawsker-production",
        description="Lawsker生产环境",
        base_domain="lawsker.com",
        ssl_enabled=True,
        monitoring_enabled=True,
        backup_enabled=True,
        default_resource_quota=ResourceQuota(
            cpu_limit=2.0,
            memory_limit=2048,
            disk_limit=10240,
            max_connections=1000
        )
    )


def create_sample_applications() -> List[ApplicationConfig]:
    """创建示例应用配置"""
    return [
        ApplicationConfig(
            name="lawsker-api",
            type="api",
            version="1.0.0",
            description="Lawsker API服务",
            command="python",
            args=["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            working_directory="/opt/lawsker/backend",
            environment={"PYTHONPATH": "/opt/lawsker/backend", "ENV": "production"},
            port=8000,
            host="0.0.0.0",
            domain="api.lawsker.com",
            ssl_enabled=True,
            health_check_url="http://localhost:8000/health",
            auto_restart=True,
            max_restarts=3
        ),
        ApplicationConfig(
            name="lawsker-frontend",
            type="web",
            version="1.0.0",
            description="Lawsker前端服务",
            command="python",
            args=["-m", "http.server", "6060"],
            working_directory="/opt/lawsker/frontend",
            port=6060,
            host="0.0.0.0",
            domain="lawsker.com",
            ssl_enabled=True,
            auto_restart=True,
            max_restarts=3
        ),
        ApplicationConfig(
            name="lawsker-admin",
            type="web",
            version="1.0.0",
            description="Lawsker管理后台",
            command="python",
            args=["-m", "http.server", "6061"],
            working_directory="/opt/lawsker/frontend/admin",
            port=6061,
            host="0.0.0.0",
            domain="admin.lawsker.com",
            ssl_enabled=True,
            dependencies=["lawsker-api"],
            auto_restart=True,
            max_restarts=3
        )
    ]


if __name__ == "__main__":
    # 测试代码
    async def main():
        # 创建环境配置
        env_config = create_sample_environment()
        
        # 创建环境管理器
        env_manager = MultiAppEnvironmentManager(env_config)
        
        # 初始化环境
        await env_manager.initialize_environment()
        
        # 部署示例应用
        sample_apps = create_sample_applications()
        
        for app_config in sample_apps:
            success = await env_manager.deploy_application(app_config)
            print(f"Deploy {app_config.name}: {success}")
        
        # 获取环境状态
        status = env_manager.get_environment_status()
        print(f"\nEnvironment Status:")
        print(f"- Applications: {status['applications']['total']} total, {status['applications']['running']} running")
        print(f"- Virtual Hosts: {status['virtual_hosts']['total']} total, {status['virtual_hosts']['active']} active")
        
        if status['conflicts']['ports'] or status['conflicts']['domains']:
            print(f"- Conflicts detected: {status['conflicts']}")
        
        # 清理
        await env_manager.cleanup()
    
    asyncio.run(main())