#!/usr/bin/env python3
"""
应用管理器 - ApplicationManager类
负责应用注册和发现、资源配额管理、应用生命周期管理和应用间依赖关系处理
"""

import os
import json
import logging
import asyncio
import psutil
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
from datetime import datetime
from enum import Enum
import yaml
import subprocess
import signal
import time
from contextlib import asynccontextmanager


class ApplicationStatus(Enum):
    """应用状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ResourceType(Enum):
    """资源类型枚举"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    PORT = "port"


@dataclass
class ResourceQuota:
    """资源配额配置"""
    cpu_limit: float = 1.0  # CPU核心数限制
    memory_limit: int = 1024  # 内存限制(MB)
    disk_limit: int = 10240  # 磁盘限制(MB)
    network_bandwidth: int = 100  # 网络带宽限制(Mbps)
    max_connections: int = 1000  # 最大连接数
    max_file_descriptors: int = 1024  # 最大文件描述符数


@dataclass
class ResourceUsage:
    """资源使用情况"""
    cpu_usage: float = 0.0  # CPU使用率(%)
    memory_usage: int = 0  # 内存使用量(MB)
    disk_usage: int = 0  # 磁盘使用量(MB)
    network_rx: int = 0  # 网络接收字节数
    network_tx: int = 0  # 网络发送字节数
    connections: int = 0  # 当前连接数
    file_descriptors: int = 0  # 当前文件描述符数
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ApplicationConfig:
    """应用配置"""
    name: str
    type: str  # web, api, worker, service等
    version: str = "1.0.0"
    description: str = ""
    
    # 运行配置
    command: str = ""
    args: List[str] = field(default_factory=list)
    working_directory: str = ""
    environment: Dict[str, str] = field(default_factory=dict)
    
    # 网络配置
    port: Optional[int] = None
    host: str = "localhost"
    domain: Optional[str] = None
    ssl_enabled: bool = False
    
    # 资源配置
    resource_quota: ResourceQuota = field(default_factory=ResourceQuota)
    
    # 依赖配置
    dependencies: List[str] = field(default_factory=list)
    reverse_dependencies: List[str] = field(default_factory=list)
    
    # 健康检查配置
    health_check_url: Optional[str] = None
    health_check_interval: int = 30  # 秒
    health_check_timeout: int = 10  # 秒
    health_check_retries: int = 3
    
    # 自动重启配置
    auto_restart: bool = True
    max_restarts: int = 5
    restart_delay: int = 5  # 秒
    
    # 日志配置
    log_file: Optional[str] = None
    log_level: str = "INFO"
    log_rotation: bool = True
    log_max_size: int = 100  # MB
    log_backup_count: int = 5


@dataclass
class ApplicationInstance:
    """应用实例"""
    config: ApplicationConfig
    status: ApplicationStatus = ApplicationStatus.STOPPED
    pid: Optional[int] = None
    start_time: Optional[datetime] = None
    restart_count: int = 0
    last_health_check: Optional[datetime] = None
    health_status: bool = True
    resource_usage: ResourceUsage = field(default_factory=ResourceUsage)
    error_message: Optional[str] = None


class ApplicationManager:
    """
    应用管理器
    
    负责：
    - 编写应用注册和发现机制
    - 实现资源配额和限制管理
    - 添加应用生命周期管理
    - 创建应用间依赖关系处理
    """
    
    def __init__(self, config_dir: str = "/etc/lawsker/applications"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = self._setup_logger()
        
        # 应用注册表
        self.applications: Dict[str, ApplicationInstance] = {}
        self.port_registry: Dict[int, str] = {}  # 端口占用注册表
        self.domain_registry: Dict[str, str] = {}  # 域名注册表
        
        # 资源监控
        self.resource_monitor_interval = 30  # 秒
        self.resource_monitor_task: Optional[asyncio.Task] = None
        
        # 健康检查
        self.health_check_tasks: Dict[str, asyncio.Task] = {}
        
        # 依赖图
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.reverse_dependency_graph: Dict[str, Set[str]] = {}
        
        # 加载已注册的应用
        self._load_applications()
    
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
            log_file = self.config_dir / "application_manager.log"
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _load_applications(self):
        """加载已注册的应用配置"""
        try:
            config_files = list(self.config_dir.glob("*.yaml")) + list(self.config_dir.glob("*.yml"))
            
            for config_file in config_files:
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f)
                    
                    app_config = ApplicationConfig(**config_data)
                    app_instance = ApplicationInstance(config=app_config)
                    
                    self.applications[app_config.name] = app_instance
                    self.logger.info(f"Loaded application config: {app_config.name}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to load config from {config_file}: {str(e)}")
            
            # 构建依赖图
            self._build_dependency_graph()
            
            self.logger.info(f"Loaded {len(self.applications)} applications")
            
        except Exception as e:
            self.logger.error(f"Failed to load applications: {str(e)}")
    
    def _build_dependency_graph(self):
        """构建应用依赖图"""
        self.dependency_graph.clear()
        self.reverse_dependency_graph.clear()
        
        for app_name, app_instance in self.applications.items():
            self.dependency_graph[app_name] = set(app_instance.config.dependencies)
            
            # 构建反向依赖图
            for dep in app_instance.config.dependencies:
                if dep not in self.reverse_dependency_graph:
                    self.reverse_dependency_graph[dep] = set()
                self.reverse_dependency_graph[dep].add(app_name)
    
    def register_application(self, config: ApplicationConfig) -> bool:
        """
        注册应用
        
        Args:
            config: 应用配置
            
        Returns:
            注册是否成功
        """
        try:
            # 检查应用名称冲突
            if config.name in self.applications:
                self.logger.error(f"Application {config.name} already registered")
                return False
            
            # 检查端口冲突
            if config.port and self._check_port_conflict(config.port, config.name):
                self.logger.error(f"Port {config.port} already in use")
                return False
            
            # 检查域名冲突
            if config.domain and self._check_domain_conflict(config.domain, config.name):
                self.logger.error(f"Domain {config.domain} already in use")
                return False
            
            # 验证依赖关系
            if not self._validate_dependencies(config):
                self.logger.error(f"Invalid dependencies for application {config.name}")
                return False
            
            # 创建应用实例
            app_instance = ApplicationInstance(config=config)
            self.applications[config.name] = app_instance
            
            # 注册端口和域名
            if config.port:
                self.port_registry[config.port] = config.name
            if config.domain:
                self.domain_registry[config.domain] = config.name
            
            # 保存配置文件
            self._save_application_config(config)
            
            # 重新构建依赖图
            self._build_dependency_graph()
            
            self.logger.info(f"Application {config.name} registered successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register application {config.name}: {str(e)}")
            return False
    
    def unregister_application(self, app_name: str) -> bool:
        """
        注销应用
        
        Args:
            app_name: 应用名称
            
        Returns:
            注销是否成功
        """
        try:
            if app_name not in self.applications:
                self.logger.error(f"Application {app_name} not found")
                return False
            
            app_instance = self.applications[app_name]
            
            # 检查是否有其他应用依赖此应用
            dependents = self.reverse_dependency_graph.get(app_name, set())
            if dependents:
                self.logger.error(f"Cannot unregister {app_name}, it has dependents: {dependents}")
                return False
            
            # 停止应用
            if app_instance.status == ApplicationStatus.RUNNING:
                self.stop_application(app_name)
            
            # 清理注册信息
            if app_instance.config.port:
                self.port_registry.pop(app_instance.config.port, None)
            if app_instance.config.domain:
                self.domain_registry.pop(app_instance.config.domain, None)
            
            # 删除配置文件
            config_file = self.config_dir / f"{app_name}.yaml"
            if config_file.exists():
                config_file.unlink()
            
            # 从注册表中移除
            del self.applications[app_name]
            
            # 重新构建依赖图
            self._build_dependency_graph()
            
            self.logger.info(f"Application {app_name} unregistered successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister application {app_name}: {str(e)}")
            return False
    
    def discover_applications(self) -> List[Dict[str, Any]]:
        """
        发现已注册的应用
        
        Returns:
            应用信息列表
        """
        applications = []
        
        for app_name, app_instance in self.applications.items():
            app_info = {
                "name": app_name,
                "type": app_instance.config.type,
                "version": app_instance.config.version,
                "status": app_instance.status.value,
                "port": app_instance.config.port,
                "domain": app_instance.config.domain,
                "dependencies": app_instance.config.dependencies,
                "resource_usage": asdict(app_instance.resource_usage),
                "health_status": app_instance.health_status,
                "restart_count": app_instance.restart_count
            }
            
            if app_instance.start_time:
                app_info["uptime"] = (datetime.now() - app_instance.start_time).total_seconds()
            
            applications.append(app_info)
        
        return applications
    
    def _check_port_conflict(self, port: int, exclude_app: str = None) -> bool:
        """检查端口冲突"""
        if port in self.port_registry:
            return self.port_registry[port] != exclude_app
        
        # 检查系统端口占用
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                result = s.connect_ex(('localhost', port))
                return result == 0  # 端口被占用
        except:
            return False
    
    def _check_domain_conflict(self, domain: str, exclude_app: str = None) -> bool:
        """检查域名冲突"""
        if domain in self.domain_registry:
            return self.domain_registry[domain] != exclude_app
        return False
    
    def _validate_dependencies(self, config: ApplicationConfig) -> bool:
        """验证应用依赖关系"""
        for dep in config.dependencies:
            if dep not in self.applications and dep != config.name:
                # 依赖的应用不存在
                self.logger.warning(f"Dependency {dep} not found for application {config.name}")
        
        # 检查循环依赖
        if self._has_circular_dependency(config.name, config.dependencies):
            return False
        
        return True
    
    def _has_circular_dependency(self, app_name: str, dependencies: List[str], visited: Set[str] = None) -> bool:
        """检查循环依赖"""
        if visited is None:
            visited = set()
        
        if app_name in visited:
            return True
        
        visited.add(app_name)
        
        for dep in dependencies:
            if dep in self.applications:
                dep_dependencies = self.applications[dep].config.dependencies
                if self._has_circular_dependency(dep, dep_dependencies, visited.copy()):
                    return True
        
        return False
    
    def _save_application_config(self, config: ApplicationConfig):
        """保存应用配置到文件"""
        config_file = self.config_dir / f"{config.name}.yaml"
        config_dict = asdict(config)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
    
    async def start_application(self, app_name: str) -> bool:
        """
        启动应用
        
        Args:
            app_name: 应用名称
            
        Returns:
            启动是否成功
        """
        try:
            if app_name not in self.applications:
                self.logger.error(f"Application {app_name} not found")
                return False
            
            app_instance = self.applications[app_name]
            
            if app_instance.status == ApplicationStatus.RUNNING:
                self.logger.info(f"Application {app_name} is already running")
                return True
            
            # 检查依赖应用是否运行
            for dep in app_instance.config.dependencies:
                if dep in self.applications:
                    dep_instance = self.applications[dep]
                    if dep_instance.status != ApplicationStatus.RUNNING:
                        self.logger.error(f"Dependency {dep} is not running")
                        return False
            
            # 检查资源可用性
            if not self._check_resource_availability(app_instance.config.resource_quota):
                self.logger.error(f"Insufficient resources to start {app_name}")
                return False
            
            # 启动应用进程
            app_instance.status = ApplicationStatus.STARTING
            
            success = await self._start_application_process(app_instance)
            
            if success:
                app_instance.status = ApplicationStatus.RUNNING
                app_instance.start_time = datetime.now()
                app_instance.restart_count = 0
                
                # 启动健康检查
                if app_instance.config.health_check_url:
                    self._start_health_check(app_name)
                
                self.logger.info(f"Application {app_name} started successfully")
                return True
            else:
                app_instance.status = ApplicationStatus.FAILED
                self.logger.error(f"Failed to start application {app_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start application {app_name}: {str(e)}")
            if app_name in self.applications:
                self.applications[app_name].status = ApplicationStatus.FAILED
                self.applications[app_name].error_message = str(e)
            return False
    
    async def stop_application(self, app_name: str, force: bool = False) -> bool:
        """
        停止应用
        
        Args:
            app_name: 应用名称
            force: 是否强制停止
            
        Returns:
            停止是否成功
        """
        try:
            if app_name not in self.applications:
                self.logger.error(f"Application {app_name} not found")
                return False
            
            app_instance = self.applications[app_name]
            
            if app_instance.status == ApplicationStatus.STOPPED:
                self.logger.info(f"Application {app_name} is already stopped")
                return True
            
            # 检查是否有其他应用依赖此应用
            if not force:
                dependents = self.reverse_dependency_graph.get(app_name, set())
                running_dependents = [
                    dep for dep in dependents
                    if dep in self.applications and 
                    self.applications[dep].status == ApplicationStatus.RUNNING
                ]
                
                if running_dependents:
                    self.logger.error(f"Cannot stop {app_name}, running dependents: {running_dependents}")
                    return False
            
            # 停止健康检查
            self._stop_health_check(app_name)
            
            # 停止应用进程
            app_instance.status = ApplicationStatus.STOPPING
            
            success = await self._stop_application_process(app_instance, force)
            
            if success:
                app_instance.status = ApplicationStatus.STOPPED
                app_instance.pid = None
                app_instance.start_time = None
                
                self.logger.info(f"Application {app_name} stopped successfully")
                return True
            else:
                self.logger.error(f"Failed to stop application {app_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to stop application {app_name}: {str(e)}")
            return False
    
    async def restart_application(self, app_name: str) -> bool:
        """
        重启应用
        
        Args:
            app_name: 应用名称
            
        Returns:
            重启是否成功
        """
        try:
            if app_name not in self.applications:
                self.logger.error(f"Application {app_name} not found")
                return False
            
            app_instance = self.applications[app_name]
            
            # 停止应用
            if app_instance.status == ApplicationStatus.RUNNING:
                if not await self.stop_application(app_name):
                    return False
            
            # 等待一段时间
            await asyncio.sleep(app_instance.config.restart_delay)
            
            # 启动应用
            success = await self.start_application(app_name)
            
            if success:
                app_instance.restart_count += 1
                self.logger.info(f"Application {app_name} restarted successfully")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to restart application {app_name}: {str(e)}")
            return False
    
    def get_application_status(self, app_name: str) -> Optional[Dict[str, Any]]:
        """
        获取应用状态
        
        Args:
            app_name: 应用名称
            
        Returns:
            应用状态信息
        """
        if app_name not in self.applications:
            return None
        
        app_instance = self.applications[app_name]
        
        status_info = {
            "name": app_name,
            "status": app_instance.status.value,
            "pid": app_instance.pid,
            "restart_count": app_instance.restart_count,
            "health_status": app_instance.health_status,
            "resource_usage": asdict(app_instance.resource_usage),
            "error_message": app_instance.error_message
        }
        
        if app_instance.start_time:
            status_info["start_time"] = app_instance.start_time.isoformat()
            status_info["uptime"] = (datetime.now() - app_instance.start_time).total_seconds()
        
        if app_instance.last_health_check:
            status_info["last_health_check"] = app_instance.last_health_check.isoformat()
        
        return status_info
    
    def _check_resource_availability(self, quota: ResourceQuota) -> bool:
        """检查资源可用性"""
        try:
            # 检查CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent + (quota.cpu_limit * 100) > 90:  # 预留10%
                return False
            
            # 检查内存
            memory = psutil.virtual_memory()
            if memory.available < quota.memory_limit * 1024 * 1024:  # 转换为字节
                return False
            
            # 检查磁盘空间
            disk = psutil.disk_usage('/')
            if disk.free < quota.disk_limit * 1024 * 1024:  # 转换为字节
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to check resource availability: {str(e)}")
            return False
    
    async def _start_application_process(self, app_instance: ApplicationInstance) -> bool:
        """启动应用进程"""
        try:
            config = app_instance.config
            
            # 构建命令
            cmd = [config.command] + config.args
            
            # 设置环境变量
            env = os.environ.copy()
            env.update(config.environment)
            
            # 设置工作目录
            cwd = config.working_directory or os.getcwd()
            
            # 启动进程
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            app_instance.pid = process.pid
            
            # 等待进程启动
            await asyncio.sleep(2)
            
            # 检查进程是否还在运行
            if process.returncode is None:
                return True
            else:
                stdout, stderr = await process.communicate()
                self.logger.error(f"Process exited with code {process.returncode}")
                self.logger.error(f"stdout: {stdout.decode()}")
                self.logger.error(f"stderr: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start process: {str(e)}")
            return False
    
    async def _stop_application_process(self, app_instance: ApplicationInstance, force: bool = False) -> bool:
        """停止应用进程"""
        try:
            if not app_instance.pid:
                return True
            
            try:
                process = psutil.Process(app_instance.pid)
                
                if not force:
                    # 优雅停止
                    process.terminate()
                    
                    # 等待进程结束
                    try:
                        process.wait(timeout=30)
                    except psutil.TimeoutExpired:
                        # 超时后强制杀死
                        process.kill()
                        process.wait(timeout=10)
                else:
                    # 强制停止
                    process.kill()
                    process.wait(timeout=10)
                
                return True
                
            except psutil.NoSuchProcess:
                # 进程已经不存在
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to stop process: {str(e)}")
            return False
    
    def _start_health_check(self, app_name: str):
        """启动健康检查任务"""
        if app_name in self.health_check_tasks:
            self.health_check_tasks[app_name].cancel()
        
        task = asyncio.create_task(self._health_check_loop(app_name))
        self.health_check_tasks[app_name] = task
    
    def _stop_health_check(self, app_name: str):
        """停止健康检查任务"""
        if app_name in self.health_check_tasks:
            self.health_check_tasks[app_name].cancel()
            del self.health_check_tasks[app_name]
    
    async def _health_check_loop(self, app_name: str):
        """健康检查循环"""
        try:
            app_instance = self.applications[app_name]
            config = app_instance.config
            
            while app_instance.status == ApplicationStatus.RUNNING:
                try:
                    # 执行健康检查
                    healthy = await self._perform_health_check(app_instance)
                    
                    app_instance.health_status = healthy
                    app_instance.last_health_check = datetime.now()
                    
                    if not healthy:
                        self.logger.warning(f"Health check failed for {app_name}")
                        
                        # 如果启用自动重启
                        if config.auto_restart and app_instance.restart_count < config.max_restarts:
                            self.logger.info(f"Auto-restarting {app_name}")
                            await self.restart_application(app_name)
                    
                    await asyncio.sleep(config.health_check_interval)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Health check error for {app_name}: {str(e)}")
                    await asyncio.sleep(config.health_check_interval)
                    
        except Exception as e:
            self.logger.error(f"Health check loop error for {app_name}: {str(e)}")
    
    async def _perform_health_check(self, app_instance: ApplicationInstance) -> bool:
        """执行健康检查"""
        try:
            import aiohttp
            
            config = app_instance.config
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.health_check_timeout)) as session:
                for attempt in range(config.health_check_retries):
                    try:
                        async with session.get(config.health_check_url) as response:
                            return response.status == 200
                    except:
                        if attempt < config.health_check_retries - 1:
                            await asyncio.sleep(1)
                        else:
                            return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False
    
    async def start_resource_monitoring(self):
        """启动资源监控"""
        if self.resource_monitor_task:
            return
        
        self.resource_monitor_task = asyncio.create_task(self._resource_monitor_loop())
        self.logger.info("Resource monitoring started")
    
    async def stop_resource_monitoring(self):
        """停止资源监控"""
        if self.resource_monitor_task:
            self.resource_monitor_task.cancel()
            self.resource_monitor_task = None
            self.logger.info("Resource monitoring stopped")
    
    async def _resource_monitor_loop(self):
        """资源监控循环"""
        try:
            while True:
                for app_name, app_instance in self.applications.items():
                    if app_instance.status == ApplicationStatus.RUNNING and app_instance.pid:
                        try:
                            usage = self._collect_resource_usage(app_instance.pid)
                            app_instance.resource_usage = usage
                            
                            # 检查资源限制
                            self._check_resource_limits(app_name, app_instance)
                            
                        except Exception as e:
                            self.logger.error(f"Failed to collect resource usage for {app_name}: {str(e)}")
                
                await asyncio.sleep(self.resource_monitor_interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Resource monitor loop error: {str(e)}")
    
    def _collect_resource_usage(self, pid: int) -> ResourceUsage:
        """收集进程资源使用情况"""
        try:
            process = psutil.Process(pid)
            
            # CPU使用率
            cpu_percent = process.cpu_percent()
            
            # 内存使用量
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # 网络IO
            try:
                net_io = process.net_io_counters()
                network_rx = net_io.bytes_recv
                network_tx = net_io.bytes_sent
            except:
                network_rx = network_tx = 0
            
            # 连接数
            try:
                connections = len(process.connections())
            except:
                connections = 0
            
            # 文件描述符数
            try:
                file_descriptors = process.num_fds()
            except:
                file_descriptors = 0
            
            return ResourceUsage(
                cpu_usage=cpu_percent,
                memory_usage=int(memory_mb),
                network_rx=network_rx,
                network_tx=network_tx,
                connections=connections,
                file_descriptors=file_descriptors,
                timestamp=datetime.now()
            )
            
        except psutil.NoSuchProcess:
            return ResourceUsage()
        except Exception as e:
            self.logger.error(f"Failed to collect resource usage: {str(e)}")
            return ResourceUsage()
    
    def _check_resource_limits(self, app_name: str, app_instance: ApplicationInstance):
        """检查资源限制"""
        quota = app_instance.config.resource_quota
        usage = app_instance.resource_usage
        
        # 检查CPU限制
        if usage.cpu_usage > quota.cpu_limit * 100:
            self.logger.warning(f"Application {app_name} exceeds CPU limit: {usage.cpu_usage}% > {quota.cpu_limit * 100}%")
        
        # 检查内存限制
        if usage.memory_usage > quota.memory_limit:
            self.logger.warning(f"Application {app_name} exceeds memory limit: {usage.memory_usage}MB > {quota.memory_limit}MB")
        
        # 检查连接数限制
        if usage.connections > quota.max_connections:
            self.logger.warning(f"Application {app_name} exceeds connection limit: {usage.connections} > {quota.max_connections}")
        
        # 检查文件描述符限制
        if usage.file_descriptors > quota.max_file_descriptors:
            self.logger.warning(f"Application {app_name} exceeds file descriptor limit: {usage.file_descriptors} > {quota.max_file_descriptors}")
    
    async def start_dependency_ordered_applications(self, app_names: List[str] = None) -> Dict[str, bool]:
        """
        按依赖顺序启动应用
        
        Args:
            app_names: 要启动的应用名称列表，None表示启动所有应用
            
        Returns:
            启动结果字典
        """
        if app_names is None:
            app_names = list(self.applications.keys())
        
        # 拓扑排序获取启动顺序
        start_order = self._topological_sort(app_names)
        
        results = {}
        
        for app_name in start_order:
            if app_name in self.applications:
                success = await self.start_application(app_name)
                results[app_name] = success
                
                if not success:
                    self.logger.error(f"Failed to start {app_name}, stopping dependency chain")
                    break
        
        return results
    
    async def stop_dependency_ordered_applications(self, app_names: List[str] = None) -> Dict[str, bool]:
        """
        按依赖顺序停止应用（反向顺序）
        
        Args:
            app_names: 要停止的应用名称列表，None表示停止所有应用
            
        Returns:
            停止结果字典
        """
        if app_names is None:
            app_names = list(self.applications.keys())
        
        # 拓扑排序获取启动顺序，然后反向
        start_order = self._topological_sort(app_names)
        stop_order = list(reversed(start_order))
        
        results = {}
        
        for app_name in stop_order:
            if app_name in self.applications:
                success = await self.stop_application(app_name)
                results[app_name] = success
        
        return results
    
    def _topological_sort(self, app_names: List[str]) -> List[str]:
        """拓扑排序获取应用启动顺序"""
        # 构建子图
        sub_graph = {}
        in_degree = {}
        
        for app_name in app_names:
            if app_name in self.applications:
                dependencies = [
                    dep for dep in self.applications[app_name].config.dependencies
                    if dep in app_names
                ]
                sub_graph[app_name] = dependencies
                in_degree[app_name] = len(dependencies)
        
        # 拓扑排序
        result = []
        queue = [app for app, degree in in_degree.items() if degree == 0]
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            # 更新依赖此应用的其他应用的入度
            for app_name, dependencies in sub_graph.items():
                if current in dependencies:
                    in_degree[app_name] -= 1
                    if in_degree[app_name] == 0:
                        queue.append(app_name)
        
        return result
    
    def get_dependency_graph(self) -> Dict[str, Any]:
        """获取依赖关系图"""
        return {
            "dependencies": {k: list(v) for k, v in self.dependency_graph.items()},
            "reverse_dependencies": {k: list(v) for k, v in self.reverse_dependency_graph.items()}
        }
    
    def validate_application_config(self, config: ApplicationConfig) -> List[str]:
        """
        验证应用配置
        
        Args:
            config: 应用配置
            
        Returns:
            验证错误列表
        """
        errors = []
        
        # 检查必填字段
        if not config.name:
            errors.append("Application name is required")
        
        if not config.command:
            errors.append("Application command is required")
        
        # 检查端口范围
        if config.port and (config.port < 1 or config.port > 65535):
            errors.append("Port must be between 1 and 65535")
        
        # 检查资源配额
        if config.resource_quota.cpu_limit <= 0:
            errors.append("CPU limit must be positive")
        
        if config.resource_quota.memory_limit <= 0:
            errors.append("Memory limit must be positive")
        
        # 检查健康检查配置
        if config.health_check_url and not config.health_check_url.startswith(('http://', 'https://')):
            errors.append("Health check URL must start with http:// or https://")
        
        return errors
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 停止所有健康检查任务
            for task in self.health_check_tasks.values():
                task.cancel()
            self.health_check_tasks.clear()
            
            # 停止资源监控
            await self.stop_resource_monitoring()
            
            self.logger.info("Application manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")


# 示例配置
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
            environment={
                "PYTHONPATH": "/opt/lawsker/backend",
                "ENV": "production"
            },
            port=8000,
            host="0.0.0.0",
            domain="api.lawsker.com",
            ssl_enabled=True,
            resource_quota=ResourceQuota(
                cpu_limit=2.0,
                memory_limit=2048,
                disk_limit=5120,
                max_connections=1000
            ),
            dependencies=[],
            health_check_url="http://localhost:8000/health",
            health_check_interval=30,
            auto_restart=True,
            max_restarts=3
        ),
        ApplicationConfig(
            name="lawsker-worker",
            type="worker",
            version="1.0.0",
            description="Lawsker后台任务处理器",
            command="python",
            args=["-m", "celery", "worker", "-A", "app.main:celery_app", "--loglevel=info"],
            working_directory="/opt/lawsker/backend",
            environment={
                "PYTHONPATH": "/opt/lawsker/backend",
                "ENV": "production"
            },
            resource_quota=ResourceQuota(
                cpu_limit=1.0,
                memory_limit=1024,
                disk_limit=2048,
                max_connections=100
            ),
            dependencies=["lawsker-api"],
            auto_restart=True,
            max_restarts=5
        )
    ]


if __name__ == "__main__":
    # 测试代码
    async def main():
        manager = ApplicationManager()
        
        # 创建示例应用
        sample_apps = create_sample_applications()
        
        for app_config in sample_apps:
            success = manager.register_application(app_config)
            print(f"Register {app_config.name}: {success}")
        
        # 发现应用
        apps = manager.discover_applications()
        print(f"Discovered {len(apps)} applications")
        
        # 启动资源监控
        await manager.start_resource_monitoring()
        
        # 按依赖顺序启动应用
        # start_results = await manager.start_dependency_ordered_applications()
        # print(f"Start results: {start_results}")
        
        # 等待一段时间
        await asyncio.sleep(5)
        
        # 清理
        await manager.cleanup()
    
    # asyncio.run(main())