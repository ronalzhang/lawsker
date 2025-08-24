#!/usr/bin/env python3
"""
部署编排器 - DeploymentOrchestrator类
负责整合所有部署组件，管理部署流程，监控部署进度和处理部署失败回滚
"""

import os
import sys
import json
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
from enum import Enum
import concurrent.futures
from contextlib import asynccontextmanager

# 导入部署组件
from .dependency_manager import DependencyManager, DependencyInfo
from .database_configurator import DatabaseConfigurator, DatabaseConfig, DatabaseStatus
from .frontend_builder import FrontendBuilder, FrontendProject
from .ssl_configurator import SSLConfigurator, SSLConfig
from .monitoring_configurator import MonitoringConfigurator, MonitoringConfig


class DeploymentStatus(Enum):
    """部署状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLBACK = "rollback"
    CANCELLED = "cancelled"


class ComponentType(Enum):
    """组件类型枚举"""
    DEPENDENCIES = "dependencies"
    DATABASE = "database"
    FRONTEND = "frontend"
    SSL = "ssl"
    MONITORING = "monitoring"


@dataclass
class DeploymentComponent:
    """部署组件配置"""
    name: str
    type: ComponentType
    enabled: bool = True
    priority: int = 1  # 优先级，数字越小优先级越高
    dependencies: List[str] = None  # 依赖的组件名称
    parallel_safe: bool = False  # 是否可以并行执行
    timeout: int = 1800  # 超时时间（秒）
    retry_count: int = 3  # 重试次数
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class DeploymentResult:
    """部署结果"""
    component: str
    status: DeploymentStatus
    message: str
    timestamp: datetime
    duration: float = 0.0
    details: Optional[Dict] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['status'] = self.status.value
        return result


@dataclass
class DeploymentConfig:
    """部署配置"""
    project_root: str
    server_ip: str = "localhost"
    server_user: str = "root"
    deploy_path: str = "/opt/lawsker"
    domains: List[str] = None
    ssl_enabled: bool = True
    monitoring_enabled: bool = True
    backup_enabled: bool = True
    parallel_execution: bool = True
    max_workers: int = 3
    
    def __post_init__(self):
        if self.domains is None:
            self.domains = ["lawsker.com"]


class DeploymentOrchestrator:
    """
    部署编排器
    
    负责：
    - 编写部署流程编排逻辑
    - 实现组件间依赖关系管理
    - 添加并行部署和优化功能
    - 创建部署状态跟踪和报告
    """
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.logger = self._setup_logger()
        self.project_root = Path(config.project_root).resolve()
        
        # 部署状态跟踪
        self.deployment_id = self._generate_deployment_id()
        self.deployment_status = DeploymentStatus.PENDING
        self.component_results: Dict[str, DeploymentResult] = {}
        self.deployment_start_time: Optional[datetime] = None
        self.deployment_end_time: Optional[datetime] = None
        
        # 组件管理器
        self.component_managers = {}
        self.deployment_components = self._initialize_components()
        
        # 并发控制
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=config.max_workers
        )
        
        # 备份和回滚
        self.backup_dir = self.project_root / "backend" / "deployment" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
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
            log_file = self.project_root / "backend" / "deployment" / "deployment.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(deployment_id)s] - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
        return logger
    
    def _generate_deployment_id(self) -> str:
        """生成部署ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"deploy_{timestamp}"
    
    def _initialize_components(self) -> List[DeploymentComponent]:
        """初始化部署组件"""
        components = [
            DeploymentComponent(
                name="dependencies",
                type=ComponentType.DEPENDENCIES,
                priority=1,
                dependencies=[],
                parallel_safe=False,
                timeout=1800,
                retry_count=3
            ),
            DeploymentComponent(
                name="database",
                type=ComponentType.DATABASE,
                priority=2,
                dependencies=["dependencies"],
                parallel_safe=False,
                timeout=900,
                retry_count=2
            ),
            DeploymentComponent(
                name="frontend",
                type=ComponentType.FRONTEND,
                priority=3,
                dependencies=["dependencies"],
                parallel_safe=True,
                timeout=1200,
                retry_count=2
            ),
            DeploymentComponent(
                name="ssl",
                type=ComponentType.SSL,
                priority=4,
                dependencies=["database", "frontend"],
                parallel_safe=True,
                timeout=600,
                retry_count=3,
                enabled=self.config.ssl_enabled
            ),
            DeploymentComponent(
                name="monitoring",
                type=ComponentType.MONITORING,
                priority=5,
                dependencies=["database"],
                parallel_safe=True,
                timeout=900,
                retry_count=2,
                enabled=self.config.monitoring_enabled
            )
        ]
        
        return [comp for comp in components if comp.enabled]
    
    def _initialize_component_managers(self):
        """初始化组件管理器"""
        try:
            # 依赖管理器
            requirements_file = self.project_root / "backend" / "requirements-prod.txt"
            venv_path = self.project_root / "backend" / "venv"
            self.component_managers["dependencies"] = DependencyManager(
                str(requirements_file),
                str(venv_path),
                str(self.project_root)
            )
            
            # 数据库配置器
            db_config = DatabaseConfig(
                host="localhost",
                port=5432,
                name="lawsker_prod",
                user="lawsker_user",
                password=os.getenv("DB_PASSWORD", "lawsker_secure_password"),
                admin_user="postgres",
                admin_password=os.getenv("POSTGRES_PASSWORD", "postgres")
            )
            self.component_managers["database"] = DatabaseConfigurator(
                db_config,
                str(self.project_root)
            )
            
            # 前端构建器
            frontend_projects = [
                FrontendProject(
                    name="lawsker-frontend",
                    path="frontend",
                    build_command="echo 'Static files, no build needed'",
                    output_dir=".",
                    nginx_root="/var/www/lawsker/frontend",
                    domain="lawsker.com"
                ),
                FrontendProject(
                    name="lawsker-admin",
                    path="frontend/admin",
                    build_command="npm run build",
                    output_dir="dist",
                    nginx_root="/var/www/lawsker/admin",
                    domain="admin.lawsker.com"
                )
            ]
            self.component_managers["frontend"] = FrontendBuilder(
                frontend_projects,
                str(self.project_root)
            )
            
            # SSL配置器
            if self.config.ssl_enabled:
                ssl_config = SSLConfig(
                    domains=self.config.domains,
                    email=os.getenv("SSL_EMAIL", "admin@lawsker.com"),
                    staging=os.getenv("SSL_STAGING", "false").lower() == "true"
                )
                self.component_managers["ssl"] = SSLConfigurator(ssl_config)
            
            # 监控配置器
            if self.config.monitoring_enabled:
                monitoring_config = MonitoringConfig(
                    prometheus_port=9090,
                    grafana_port=3000,
                    retention_days=30,
                    grafana_admin_password=os.getenv("GRAFANA_PASSWORD", "admin")
                )
                self.component_managers["monitoring"] = MonitoringConfigurator(monitoring_config)
            
            self.logger.info("Component managers initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize component managers: {str(e)}")
            raise
    
    async def deploy(self) -> Dict[str, Any]:
        """
        执行完整部署流程
        
        Returns:
            部署结果报告
        """
        self.logger.info(f"Starting deployment {self.deployment_id}")
        self.deployment_start_time = datetime.now()
        self.deployment_status = DeploymentStatus.IN_PROGRESS
        
        try:
            # 初始化组件管理器
            self._initialize_component_managers()
            
            # 创建部署快照
            if self.config.backup_enabled:
                await self._create_deployment_snapshot()
            
            # 执行部署计划
            deployment_plan = self._create_deployment_plan()
            self.logger.info(f"Deployment plan created with {len(deployment_plan)} stages")
            
            # 按阶段执行部署
            for stage_num, stage_components in enumerate(deployment_plan, 1):
                self.logger.info(f"Executing deployment stage {stage_num}/{len(deployment_plan)}")
                
                stage_results = await self._execute_deployment_stage(
                    stage_components, 
                    stage_num
                )
                
                # 检查阶段结果
                failed_components = [
                    comp for comp, result in stage_results.items()
                    if result.status == DeploymentStatus.FAILED
                ]
                
                if failed_components:
                    self.logger.error(f"Stage {stage_num} failed. Failed components: {failed_components}")
                    self.deployment_status = DeploymentStatus.FAILED
                    
                    # 执行回滚
                    if self.config.backup_enabled:
                        await self._execute_rollback()
                    
                    break
                
                self.logger.info(f"Stage {stage_num} completed successfully")
            
            # 检查整体部署状态
            if self.deployment_status == DeploymentStatus.IN_PROGRESS:
                self.deployment_status = DeploymentStatus.SUCCESS
                self.logger.info("Deployment completed successfully")
            
        except Exception as e:
            self.logger.error(f"Deployment failed with exception: {str(e)}")
            self.deployment_status = DeploymentStatus.FAILED
            
            if self.config.backup_enabled:
                await self._execute_rollback()
        
        finally:
            self.deployment_end_time = datetime.now()
            
            # 生成部署报告
            deployment_report = await self._generate_deployment_report()
            
            # 保存部署报告
            await self._save_deployment_report(deployment_report)
            
            return deployment_report
    
    def _create_deployment_plan(self) -> List[List[DeploymentComponent]]:
        """
        创建部署计划，按依赖关系和优先级分组
        
        Returns:
            按阶段分组的部署组件列表
        """
        # 按优先级排序组件
        sorted_components = sorted(
            self.deployment_components,
            key=lambda x: (x.priority, x.name)
        )
        
        deployment_plan = []
        remaining_components = sorted_components.copy()
        completed_components = set()
        
        while remaining_components:
            current_stage = []
            
            # 找到当前可以执行的组件
            for component in remaining_components.copy():
                # 检查依赖是否已完成
                dependencies_met = all(
                    dep in completed_components 
                    for dep in component.dependencies
                )
                
                if dependencies_met:
                    current_stage.append(component)
                    remaining_components.remove(component)
            
            if not current_stage:
                # 如果没有可执行的组件，说明存在循环依赖
                self.logger.error("Circular dependency detected in deployment components")
                raise ValueError("Circular dependency detected")
            
            # 根据并行安全性分组
            if self.config.parallel_execution:
                # 将并行安全的组件分组
                parallel_components = [c for c in current_stage if c.parallel_safe]
                sequential_components = [c for c in current_stage if not c.parallel_safe]
                
                # 先执行顺序组件
                for comp in sequential_components:
                    deployment_plan.append([comp])
                    completed_components.add(comp.name)
                
                # 然后执行并行组件
                if parallel_components:
                    deployment_plan.append(parallel_components)
                    completed_components.update(comp.name for comp in parallel_components)
            else:
                # 顺序执行所有组件
                for comp in current_stage:
                    deployment_plan.append([comp])
                    completed_components.add(comp.name)
        
        return deployment_plan
    
    async def _execute_deployment_stage(
        self, 
        components: List[DeploymentComponent], 
        stage_num: int
    ) -> Dict[str, DeploymentResult]:
        """
        执行部署阶段
        
        Args:
            components: 要执行的组件列表
            stage_num: 阶段编号
            
        Returns:
            组件执行结果字典
        """
        self.logger.info(f"Executing stage {stage_num} with components: {[c.name for c in components]}")
        
        stage_results = {}
        
        if len(components) == 1 or not self.config.parallel_execution:
            # 顺序执行
            for component in components:
                result = await self._execute_component(component)
                stage_results[component.name] = result
                self.component_results[component.name] = result
                
                # 如果组件失败，停止执行
                if result.status == DeploymentStatus.FAILED:
                    break
        else:
            # 并行执行
            tasks = []
            for component in components:
                task = asyncio.create_task(
                    self._execute_component(component),
                    name=f"deploy_{component.name}"
                )
                tasks.append((component.name, task))
            
            # 等待所有任务完成
            for component_name, task in tasks:
                try:
                    result = await task
                    stage_results[component_name] = result
                    self.component_results[component_name] = result
                except Exception as e:
                    result = DeploymentResult(
                        component=component_name,
                        status=DeploymentStatus.FAILED,
                        message=f"Component execution failed: {str(e)}",
                        timestamp=datetime.now(),
                        error=str(e)
                    )
                    stage_results[component_name] = result
                    self.component_results[component_name] = result
        
        return stage_results
    
    async def _execute_component(self, component: DeploymentComponent) -> DeploymentResult:
        """
        执行单个组件部署
        
        Args:
            component: 要执行的组件
            
        Returns:
            组件执行结果
        """
        self.logger.info(f"Executing component: {component.name}")
        start_time = datetime.now()
        
        for attempt in range(component.retry_count):
            try:
                if attempt > 0:
                    self.logger.info(f"Retrying component {component.name}, attempt {attempt + 1}")
                
                # 执行组件部署
                result = await asyncio.wait_for(
                    self._deploy_component(component),
                    timeout=component.timeout
                )
                
                if result["success"]:
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    
                    return DeploymentResult(
                        component=component.name,
                        status=DeploymentStatus.SUCCESS,
                        message=result.get("message", "Component deployed successfully"),
                        timestamp=end_time,
                        duration=duration,
                        details=result.get("details")
                    )
                else:
                    if attempt == component.retry_count - 1:
                        # 最后一次尝试失败
                        end_time = datetime.now()
                        duration = (end_time - start_time).total_seconds()
                        
                        return DeploymentResult(
                            component=component.name,
                            status=DeploymentStatus.FAILED,
                            message=result.get("message", "Component deployment failed"),
                            timestamp=end_time,
                            duration=duration,
                            error=result.get("error")
                        )
                    else:
                        # 等待重试
                        await asyncio.sleep(5 * (attempt + 1))
                        
            except asyncio.TimeoutError:
                self.logger.error(f"Component {component.name} timed out")
                if attempt == component.retry_count - 1:
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    
                    return DeploymentResult(
                        component=component.name,
                        status=DeploymentStatus.FAILED,
                        message=f"Component deployment timed out after {component.timeout} seconds",
                        timestamp=end_time,
                        duration=duration,
                        error="Timeout"
                    )
                    
            except Exception as e:
                self.logger.error(f"Component {component.name} failed with exception: {str(e)}")
                if attempt == component.retry_count - 1:
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    
                    return DeploymentResult(
                        component=component.name,
                        status=DeploymentStatus.FAILED,
                        message=f"Component deployment failed: {str(e)}",
                        timestamp=end_time,
                        duration=duration,
                        error=str(e)
                    )
        
        # 不应该到达这里
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return DeploymentResult(
            component=component.name,
            status=DeploymentStatus.FAILED,
            message="Component deployment failed after all retries",
            timestamp=end_time,
            duration=duration,
            error="Max retries exceeded"
        )
    
    async def _deploy_component(self, component: DeploymentComponent) -> Dict[str, Any]:
        """
        部署具体组件
        
        Args:
            component: 要部署的组件
            
        Returns:
            部署结果字典
        """
        manager = self.component_managers.get(component.name)
        if not manager:
            return {
                "success": False,
                "message": f"No manager found for component {component.name}",
                "error": "Manager not found"
            }
        
        try:
            if component.type == ComponentType.DEPENDENCIES:
                # 部署依赖
                return await self._deploy_dependencies(manager)
                
            elif component.type == ComponentType.DATABASE:
                # 部署数据库
                return await self._deploy_database(manager)
                
            elif component.type == ComponentType.FRONTEND:
                # 部署前端
                return await self._deploy_frontend(manager)
                
            elif component.type == ComponentType.SSL:
                # 部署SSL
                return await self._deploy_ssl(manager)
                
            elif component.type == ComponentType.MONITORING:
                # 部署监控
                return await self._deploy_monitoring(manager)
                
            else:
                return {
                    "success": False,
                    "message": f"Unknown component type: {component.type}",
                    "error": "Unknown component type"
                }
                
        except Exception as e:
            self.logger.error(f"Component {component.name} deployment failed: {str(e)}")
            return {
                "success": False,
                "message": f"Component deployment failed: {str(e)}",
                "error": str(e)
            }
    
    async def _deploy_dependencies(self, manager: DependencyManager) -> Dict[str, Any]:
        """部署依赖组件"""
        self.logger.info("Deploying dependencies...")
        
        try:
            # 创建虚拟环境
            if not manager.create_virtual_environment():
                return {
                    "success": False,
                    "message": "Failed to create virtual environment",
                    "error": "Virtual environment creation failed"
                }
            
            # 安装依赖
            if not manager.install_dependencies():
                return {
                    "success": False,
                    "message": "Failed to install dependencies",
                    "error": "Dependency installation failed"
                }
            
            # 验证依赖
            verification_results = manager.verify_dependencies()
            failed_deps = [k for k, v in verification_results.items() if not v]
            
            if failed_deps:
                return {
                    "success": False,
                    "message": f"Dependency verification failed for: {failed_deps}",
                    "error": "Dependency verification failed",
                    "details": {"failed_dependencies": failed_deps}
                }
            
            return {
                "success": True,
                "message": "Dependencies deployed successfully",
                "details": {
                    "verification_results": verification_results,
                    "venv_info": manager.get_virtual_environment_info()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Dependencies deployment failed: {str(e)}",
                "error": str(e)
            }
    
    async def _deploy_database(self, manager: DatabaseConfigurator) -> Dict[str, Any]:
        """部署数据库组件"""
        self.logger.info("Deploying database...")
        
        try:
            # 检查PostgreSQL服务
            if not manager.check_postgresql_service():
                return {
                    "success": False,
                    "message": "PostgreSQL service is not running",
                    "error": "PostgreSQL service check failed"
                }
            
            # 创建数据库和用户
            if not manager.create_database_and_user():
                return {
                    "success": False,
                    "message": "Failed to create database and user",
                    "error": "Database creation failed"
                }
            
            # 验证连接
            if not manager.verify_connection():
                return {
                    "success": False,
                    "message": "Database connection verification failed",
                    "error": "Connection verification failed"
                }
            
            # 优化连接池
            pool_config = manager.optimize_connection_pool()
            
            return {
                "success": True,
                "message": "Database deployed successfully",
                "details": {
                    "database_info": manager.get_database_info(),
                    "pool_config": pool_config
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Database deployment failed: {str(e)}",
                "error": str(e)
            }
    
    async def _deploy_frontend(self, manager: FrontendBuilder) -> Dict[str, Any]:
        """部署前端组件"""
        self.logger.info("Deploying frontend...")
        
        try:
            # 检查Node.js环境
            if not manager.check_node_environment():
                return {
                    "success": False,
                    "message": "Node.js environment check failed",
                    "error": "Node.js environment not ready"
                }
            
            # 构建所有项目
            build_results = manager.build_all_projects()
            
            # 检查构建结果
            failed_projects = [
                name for name, result in build_results.items()
                if result.get("status") not in ["success", "recovered"]
            ]
            
            if failed_projects:
                return {
                    "success": False,
                    "message": f"Frontend build failed for projects: {failed_projects}",
                    "error": "Frontend build failed",
                    "details": {"build_results": build_results}
                }
            
            return {
                "success": True,
                "message": "Frontend deployed successfully",
                "details": {"build_results": build_results}
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Frontend deployment failed: {str(e)}",
                "error": str(e)
            }
    
    async def _deploy_ssl(self, manager: SSLConfigurator) -> Dict[str, Any]:
        """部署SSL组件"""
        self.logger.info("Deploying SSL...")
        
        try:
            # 检查域名解析
            resolution_results = manager.check_domain_resolution()
            failed_domains = [
                domain for domain, resolved in resolution_results.items()
                if not resolved
            ]
            
            if failed_domains:
                return {
                    "success": False,
                    "message": f"Domain resolution failed for: {failed_domains}",
                    "error": "Domain resolution failed",
                    "details": {"resolution_results": resolution_results}
                }
            
            # 获取SSL证书
            if not manager.obtain_letsencrypt_certificate():
                return {
                    "success": False,
                    "message": "Failed to obtain SSL certificates",
                    "error": "SSL certificate acquisition failed"
                }
            
            # 验证证书
            cert_results = manager.verify_certificates()
            invalid_certs = [
                domain for domain, info in cert_results.items()
                if not info.valid
            ]
            
            if invalid_certs:
                return {
                    "success": False,
                    "message": f"SSL certificate validation failed for: {invalid_certs}",
                    "error": "SSL certificate validation failed",
                    "details": {"cert_results": cert_results}
                }
            
            return {
                "success": True,
                "message": "SSL deployed successfully",
                "details": {
                    "resolution_results": resolution_results,
                    "cert_results": cert_results
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"SSL deployment failed: {str(e)}",
                "error": str(e)
            }
    
    async def _deploy_monitoring(self, manager: MonitoringConfigurator) -> Dict[str, Any]:
        """部署监控组件"""
        self.logger.info("Deploying monitoring...")
        
        try:
            # 设置监控堆栈
            setup_results = await manager.setup_monitoring_stack()
            
            if setup_results.get("status") != "success":
                return {
                    "success": False,
                    "message": "Monitoring stack setup failed",
                    "error": "Monitoring setup failed",
                    "details": setup_results
                }
            
            return {
                "success": True,
                "message": "Monitoring deployed successfully",
                "details": setup_results
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Monitoring deployment failed: {str(e)}",
                "error": str(e)
            }
    
    async def _create_deployment_snapshot(self):
        """创建部署快照"""
        self.logger.info("Creating deployment snapshot...")
        
        try:
            snapshot_dir = self.backup_dir / f"snapshot_{self.deployment_id}"
            snapshot_dir.mkdir(exist_ok=True)
            
            # 备份关键配置文件
            config_files = [
                self.project_root / ".env.production",
                self.project_root / "docker-compose.yml",
                self.project_root / "nginx" / "nginx.conf",
                self.project_root / "backend" / "requirements-prod.txt"
            ]
            
            for config_file in config_files:
                if config_file.exists():
                    backup_file = snapshot_dir / config_file.name
                    backup_file.write_bytes(config_file.read_bytes())
            
            # 保存快照信息
            snapshot_info = {
                "deployment_id": self.deployment_id,
                "timestamp": datetime.now().isoformat(),
                "config_files": [str(f) for f in config_files if f.exists()],
                "project_root": str(self.project_root)
            }
            
            snapshot_info_file = snapshot_dir / "snapshot_info.json"
            with open(snapshot_info_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot_info, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Deployment snapshot created: {snapshot_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to create deployment snapshot: {str(e)}")
    
    async def _execute_rollback(self):
        """执行部署回滚"""
        self.logger.info("Executing deployment rollback...")
        
        try:
            self.deployment_status = DeploymentStatus.ROLLBACK
            
            # 查找最新的快照
            snapshot_dirs = list(self.backup_dir.glob("snapshot_*"))
            if not snapshot_dirs:
                self.logger.error("No snapshots found for rollback")
                return
            
            latest_snapshot = max(snapshot_dirs, key=lambda x: x.stat().st_mtime)
            self.logger.info(f"Rolling back to snapshot: {latest_snapshot}")
            
            # 恢复配置文件
            snapshot_info_file = latest_snapshot / "snapshot_info.json"
            if snapshot_info_file.exists():
                with open(snapshot_info_file, 'r', encoding='utf-8') as f:
                    snapshot_info = json.load(f)
                
                for config_file_path in snapshot_info.get("config_files", []):
                    config_file = Path(config_file_path)
                    backup_file = latest_snapshot / config_file.name
                    
                    if backup_file.exists():
                        config_file.write_bytes(backup_file.read_bytes())
                        self.logger.info(f"Restored config file: {config_file}")
            
            self.logger.info("Deployment rollback completed")
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {str(e)}")
    
    async def _generate_deployment_report(self) -> Dict[str, Any]:
        """生成部署报告"""
        total_duration = 0.0
        if self.deployment_start_time and self.deployment_end_time:
            total_duration = (self.deployment_end_time - self.deployment_start_time).total_seconds()
        
        successful_components = [
            name for name, result in self.component_results.items()
            if result.status == DeploymentStatus.SUCCESS
        ]
        
        failed_components = [
            name for name, result in self.component_results.items()
            if result.status == DeploymentStatus.FAILED
        ]
        
        report = {
            "deployment_id": self.deployment_id,
            "status": self.deployment_status.value,
            "start_time": self.deployment_start_time.isoformat() if self.deployment_start_time else None,
            "end_time": self.deployment_end_time.isoformat() if self.deployment_end_time else None,
            "total_duration": total_duration,
            "config": asdict(self.config),
            "summary": {
                "total_components": len(self.deployment_components),
                "successful_components": len(successful_components),
                "failed_components": len(failed_components),
                "success_rate": len(successful_components) / len(self.deployment_components) * 100 if self.deployment_components else 0
            },
            "component_results": {
                name: result.to_dict() 
                for name, result in self.component_results.items()
            },
            "successful_components": successful_components,
            "failed_components": failed_components
        }
        
        return report
    
    async def _save_deployment_report(self, report: Dict[str, Any]):
        """保存部署报告"""
        try:
            report_file = self.backup_dir / f"deployment_report_{self.deployment_id}.json"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Deployment report saved: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save deployment report: {str(e)}")
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """获取当前部署状态"""
        return {
            "deployment_id": self.deployment_id,
            "status": self.deployment_status.value,
            "start_time": self.deployment_start_time.isoformat() if self.deployment_start_time else None,
            "component_results": {
                name: result.to_dict() 
                for name, result in self.component_results.items()
            }
        }
    
    def cancel_deployment(self):
        """取消部署"""
        self.logger.info("Cancelling deployment...")
        self.deployment_status = DeploymentStatus.CANCELLED
        
        # 取消所有正在运行的任务
        for task in asyncio.all_tasks():
            if task.get_name().startswith("deploy_"):
                task.cancel()


# 工厂函数
def create_deployment_orchestrator(
    project_root: str,
    domains: List[str] = None,
    ssl_enabled: bool = True,
    monitoring_enabled: bool = True,
    parallel_execution: bool = True
) -> DeploymentOrchestrator:
    """
    创建部署编排器实例
    
    Args:
        project_root: 项目根目录
        domains: 域名列表
        ssl_enabled: 是否启用SSL
        monitoring_enabled: 是否启用监控
        parallel_execution: 是否启用并行执行
        
    Returns:
        DeploymentOrchestrator实例
    """
    config = DeploymentConfig(
        project_root=project_root,
        domains=domains or ["lawsker.com"],
        ssl_enabled=ssl_enabled,
        monitoring_enabled=monitoring_enabled,
        parallel_execution=parallel_execution
    )
    
    return DeploymentOrchestrator(config)


# 主函数用于测试
async def main():
    """主函数用于测试部署编排器"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deployment Orchestrator')
    parser.add_argument('--project-root', default='.', help='Project root directory')
    parser.add_argument('--domains', nargs='+', default=['lawsker.com'], help='Domains to deploy')
    parser.add_argument('--no-ssl', action='store_true', help='Disable SSL')
    parser.add_argument('--no-monitoring', action='store_true', help='Disable monitoring')
    parser.add_argument('--no-parallel', action='store_true', help='Disable parallel execution')
    
    args = parser.parse_args()
    
    # 创建部署编排器
    orchestrator = create_deployment_orchestrator(
        project_root=args.project_root,
        domains=args.domains,
        ssl_enabled=not args.no_ssl,
        monitoring_enabled=not args.no_monitoring,
        parallel_execution=not args.no_parallel
    )
    
    try:
        # 执行部署
        report = await orchestrator.deploy()
        
        # 打印报告
        print(json.dumps(report, indent=2, ensure_ascii=False))
        
        # 根据部署状态设置退出码
        if report["status"] == "success":
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("Deployment cancelled by user")
        orchestrator.cancel_deployment()
        sys.exit(130)
    except Exception as e:
        print(f"Deployment failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())