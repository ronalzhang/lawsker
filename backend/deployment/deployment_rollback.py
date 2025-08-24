#!/usr/bin/env python3
"""
部署回滚系统
创建部署快照和备份机制、实现自动回滚触发条件、添加手动回滚操作接口、创建回滚后验证和报告
"""

import os
import sys
import json
import shutil
import asyncio
import logging
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
import tarfile
import hashlib
import psycopg2
import redis


class RollbackTrigger(Enum):
    """回滚触发条件"""
    MANUAL = "manual"
    HEALTH_CHECK_FAILURE = "health_check_failure"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    ERROR_RATE_THRESHOLD = "error_rate_threshold"
    DEPLOYMENT_FAILURE = "deployment_failure"
    SECURITY_BREACH = "security_breach"


class RollbackStatus(Enum):
    """回滚状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SnapshotInfo:
    """快照信息"""
    snapshot_id: str
    deployment_id: str
    timestamp: datetime
    description: str
    components: List[str]
    size_bytes: int
    checksum: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class RollbackPlan:
    """回滚计划"""
    rollback_id: str
    target_snapshot_id: str
    trigger: RollbackTrigger
    components_to_rollback: List[str]
    estimated_duration: int  # 秒
    risk_level: str  # "low", "medium", "high"
    rollback_steps: List[Dict[str, Any]]
    verification_steps: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['trigger'] = self.trigger.value
        return result


@dataclass
class RollbackResult:
    """回滚结果"""
    rollback_id: str
    status: RollbackStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    components_rolled_back: List[str] = None
    verification_results: Dict[str, bool] = None
    error_message: Optional[str] = None
    details: Optional[Dict] = None
    
    def __post_init__(self):
        if self.components_rolled_back is None:
            self.components_rolled_back = []
        if self.verification_results is None:
            self.verification_results = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['status'] = self.status.value
        result['start_time'] = self.start_time.isoformat()
        if self.end_time:
            result['end_time'] = self.end_time.isoformat()
        return result


class DeploymentRollbackSystem:
    """
    部署回滚系统
    
    实现：
    - 创建部署快照和备份机制
    - 实现自动回滚触发条件
    - 添加手动回滚操作接口
    - 创建回滚后验证和报告
    """
    
    def __init__(self, project_root: str, backup_retention_days: int = 30):
        self.project_root = Path(project_root).resolve()
        self.backup_retention_days = backup_retention_days
        self.logger = self._setup_logger()
        
        # 目录设置
        self.backup_dir = self.project_root / "backend" / "deployment" / "backups"
        self.snapshots_dir = self.backup_dir / "snapshots"
        self.rollback_logs_dir = self.backup_dir / "rollback_logs"
        
        # 创建必要目录
        for directory in [self.backup_dir, self.snapshots_dir, self.rollback_logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # 快照和回滚记录
        self.snapshots: Dict[str, SnapshotInfo] = {}
        self.rollback_history: List[RollbackResult] = []
        
        # 加载现有快照信息
        self._load_snapshots()
        
        # 自动回滚配置
        self.auto_rollback_enabled = True
        self.health_check_threshold = 3  # 连续失败次数
        self.error_rate_threshold = 0.1  # 10%错误率
        self.performance_degradation_threshold = 2.0  # 响应时间增加2倍
    
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
            log_file = self.rollback_logs_dir / "rollback.log"
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
        return logger
    
    def _generate_snapshot_id(self) -> str:
        """生成快照ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"snapshot_{timestamp}"
    
    def _generate_rollback_id(self) -> str:
        """生成回滚ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"rollback_{timestamp}"
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """计算文件校验和"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _load_snapshots(self):
        """加载现有快照信息"""
        try:
            snapshots_index_file = self.snapshots_dir / "snapshots_index.json"
            if snapshots_index_file.exists():
                with open(snapshots_index_file, 'r', encoding='utf-8') as f:
                    snapshots_data = json.load(f)
                
                for snapshot_id, snapshot_info in snapshots_data.items():
                    # 转换时间戳
                    snapshot_info['timestamp'] = datetime.fromisoformat(snapshot_info['timestamp'])
                    self.snapshots[snapshot_id] = SnapshotInfo(**snapshot_info)
                
                self.logger.info(f"Loaded {len(self.snapshots)} existing snapshots")
        except Exception as e:
            self.logger.error(f"Failed to load snapshots: {str(e)}")
    
    def _save_snapshots_index(self):
        """保存快照索引"""
        try:
            snapshots_index_file = self.snapshots_dir / "snapshots_index.json"
            snapshots_data = {
                snapshot_id: snapshot_info.to_dict()
                for snapshot_id, snapshot_info in self.snapshots.items()
            }
            
            with open(snapshots_index_file, 'w', encoding='utf-8') as f:
                json.dump(snapshots_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to save snapshots index: {str(e)}")
    
    async def create_deployment_snapshot(
        self, 
        deployment_id: str, 
        description: str = "",
        components: List[str] = None
    ) -> Optional[SnapshotInfo]:
        """
        创建部署快照
        
        Args:
            deployment_id: 部署ID
            description: 快照描述
            components: 要备份的组件列表
            
        Returns:
            快照信息，失败时返回None
        """
        snapshot_id = self._generate_snapshot_id()
        self.logger.info(f"Creating deployment snapshot: {snapshot_id}")
        
        try:
            snapshot_dir = self.snapshots_dir / snapshot_id
            snapshot_dir.mkdir(exist_ok=True)
            
            if components is None:
                components = ["config", "database", "frontend", "ssl", "monitoring"]
            
            backed_up_components = []
            total_size = 0
            
            # 备份配置文件
            if "config" in components:
                config_backup_size = await self._backup_configuration(snapshot_dir)
                if config_backup_size > 0:
                    backed_up_components.append("config")
                    total_size += config_backup_size
            
            # 备份数据库
            if "database" in components:
                db_backup_size = await self._backup_database(snapshot_dir)
                if db_backup_size > 0:
                    backed_up_components.append("database")
                    total_size += db_backup_size
            
            # 备份前端文件
            if "frontend" in components:
                frontend_backup_size = await self._backup_frontend(snapshot_dir)
                if frontend_backup_size > 0:
                    backed_up_components.append("frontend")
                    total_size += frontend_backup_size
            
            # 备份SSL证书
            if "ssl" in components:
                ssl_backup_size = await self._backup_ssl_certificates(snapshot_dir)
                if ssl_backup_size > 0:
                    backed_up_components.append("ssl")
                    total_size += ssl_backup_size
            
            # 备份监控配置
            if "monitoring" in components:
                monitoring_backup_size = await self._backup_monitoring_config(snapshot_dir)
                if monitoring_backup_size > 0:
                    backed_up_components.append("monitoring")
                    total_size += monitoring_backup_size
            
            # 创建快照元数据
            metadata = {
                "deployment_id": deployment_id,
                "project_root": str(self.project_root),
                "backup_time": datetime.now().isoformat(),
                "system_info": {
                    "hostname": os.uname().nodename,
                    "platform": os.uname().system,
                    "python_version": sys.version
                }
            }
            
            metadata_file = snapshot_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 创建快照压缩包
            snapshot_archive = self.snapshots_dir / f"{snapshot_id}.tar.gz"
            with tarfile.open(snapshot_archive, "w:gz") as tar:
                tar.add(snapshot_dir, arcname=snapshot_id)
            
            # 删除临时目录
            shutil.rmtree(snapshot_dir)
            
            # 计算校验和
            checksum = self._calculate_checksum(snapshot_archive)
            archive_size = snapshot_archive.stat().st_size
            
            # 创建快照信息
            snapshot_info = SnapshotInfo(
                snapshot_id=snapshot_id,
                deployment_id=deployment_id,
                timestamp=datetime.now(),
                description=description or f"Snapshot for deployment {deployment_id}",
                components=backed_up_components,
                size_bytes=archive_size,
                checksum=checksum,
                metadata=metadata
            )
            
            # 保存快照信息
            self.snapshots[snapshot_id] = snapshot_info
            self._save_snapshots_index()
            
            self.logger.info(f"Snapshot created successfully: {snapshot_id} ({archive_size} bytes)")
            return snapshot_info
            
        except Exception as e:
            self.logger.error(f"Failed to create snapshot {snapshot_id}: {str(e)}")
            
            # 清理失败的快照
            try:
                snapshot_dir = self.snapshots_dir / snapshot_id
                if snapshot_dir.exists():
                    shutil.rmtree(snapshot_dir)
                
                snapshot_archive = self.snapshots_dir / f"{snapshot_id}.tar.gz"
                if snapshot_archive.exists():
                    snapshot_archive.unlink()
            except:
                pass
            
            return None
    
    async def _backup_configuration(self, snapshot_dir: Path) -> int:
        """备份配置文件"""
        try:
            config_dir = snapshot_dir / "config"
            config_dir.mkdir(exist_ok=True)
            
            config_files = [
                self.project_root / ".env.production",
                self.project_root / "docker-compose.yml",
                self.project_root / "docker-compose.prod.yml",
                self.project_root / "nginx" / "nginx.conf",
                self.project_root / "nginx" / "lawsker.conf",
                self.project_root / "backend" / "requirements-prod.txt",
                self.project_root / "backend" / "alembic.ini"
            ]
            
            total_size = 0
            
            for config_file in config_files:
                if config_file.exists():
                    backup_file = config_dir / config_file.name
                    shutil.copy2(config_file, backup_file)
                    total_size += backup_file.stat().st_size
            
            return total_size
            
        except Exception as e:
            self.logger.error(f"Failed to backup configuration: {str(e)}")
            return 0
    
    async def _backup_database(self, snapshot_dir: Path) -> int:
        """备份数据库"""
        try:
            db_dir = snapshot_dir / "database"
            db_dir.mkdir(exist_ok=True)
            
            # 使用pg_dump备份数据库
            db_url = os.getenv("DATABASE_URL", "postgresql://lawsker_user:password@localhost:5432/lawsker_prod")
            backup_file = db_dir / "database_backup.sql"
            
            # 执行pg_dump
            cmd = [
                "pg_dump",
                db_url,
                "--no-password",
                "--verbose",
                "--clean",
                "--no-acl",
                "--no-owner",
                "-f", str(backup_file)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30分钟超时
            )
            
            if result.returncode == 0 and backup_file.exists():
                return backup_file.stat().st_size
            else:
                self.logger.error(f"Database backup failed: {result.stderr}")
                return 0
                
        except Exception as e:
            self.logger.error(f"Failed to backup database: {str(e)}")
            return 0
    
    async def _backup_frontend(self, snapshot_dir: Path) -> int:
        """备份前端文件"""
        try:
            frontend_dir = snapshot_dir / "frontend"
            frontend_dir.mkdir(exist_ok=True)
            
            # 备份前端源文件和构建产物
            frontend_paths = [
                self.project_root / "frontend",
                Path("/var/www/lawsker") if Path("/var/www/lawsker").exists() else None
            ]
            
            total_size = 0
            
            for frontend_path in frontend_paths:
                if frontend_path and frontend_path.exists():
                    backup_path = frontend_dir / frontend_path.name
                    
                    # 使用tar压缩备份
                    tar_file = frontend_dir / f"{frontend_path.name}.tar.gz"
                    
                    with tarfile.open(tar_file, "w:gz") as tar:
                        tar.add(frontend_path, arcname=frontend_path.name)
                    
                    total_size += tar_file.stat().st_size
            
            return total_size
            
        except Exception as e:
            self.logger.error(f"Failed to backup frontend: {str(e)}")
            return 0
    
    async def _backup_ssl_certificates(self, snapshot_dir: Path) -> int:
        """备份SSL证书"""
        try:
            ssl_dir = snapshot_dir / "ssl"
            ssl_dir.mkdir(exist_ok=True)
            
            # 备份Let's Encrypt证书
            letsencrypt_dir = Path("/etc/letsencrypt")
            if letsencrypt_dir.exists():
                backup_tar = ssl_dir / "letsencrypt_backup.tar.gz"
                
                with tarfile.open(backup_tar, "w:gz") as tar:
                    tar.add(letsencrypt_dir, arcname="letsencrypt")
                
                return backup_tar.stat().st_size
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to backup SSL certificates: {str(e)}")
            return 0
    
    async def _backup_monitoring_config(self, snapshot_dir: Path) -> int:
        """备份监控配置"""
        try:
            monitoring_dir = snapshot_dir / "monitoring"
            monitoring_dir.mkdir(exist_ok=True)
            
            # 备份监控配置文件
            monitoring_paths = [
                self.project_root / "monitoring",
                Path("/opt/monitoring") if Path("/opt/monitoring").exists() else None
            ]
            
            total_size = 0
            
            for monitoring_path in monitoring_paths:
                if monitoring_path and monitoring_path.exists():
                    tar_file = monitoring_dir / f"{monitoring_path.name}.tar.gz"
                    
                    with tarfile.open(tar_file, "w:gz") as tar:
                        tar.add(monitoring_path, arcname=monitoring_path.name)
                    
                    total_size += tar_file.stat().st_size
            
            return total_size
            
        except Exception as e:
            self.logger.error(f"Failed to backup monitoring config: {str(e)}")
            return 0
    
    def create_rollback_plan(
        self, 
        target_snapshot_id: str, 
        trigger: RollbackTrigger,
        components: List[str] = None
    ) -> Optional[RollbackPlan]:
        """
        创建回滚计划
        
        Args:
            target_snapshot_id: 目标快照ID
            trigger: 回滚触发条件
            components: 要回滚的组件列表
            
        Returns:
            回滚计划，失败时返回None
        """
        try:
            if target_snapshot_id not in self.snapshots:
                self.logger.error(f"Snapshot not found: {target_snapshot_id}")
                return None
            
            snapshot_info = self.snapshots[target_snapshot_id]
            
            if components is None:
                components = snapshot_info.components
            
            # 验证组件是否在快照中
            invalid_components = [c for c in components if c not in snapshot_info.components]
            if invalid_components:
                self.logger.error(f"Components not in snapshot: {invalid_components}")
                return None
            
            rollback_id = self._generate_rollback_id()
            
            # 创建回滚步骤
            rollback_steps = []
            verification_steps = []
            
            # 根据组件创建回滚步骤
            if "config" in components:
                rollback_steps.append({
                    "step": "restore_configuration",
                    "description": "Restore configuration files",
                    "estimated_duration": 30
                })
                verification_steps.append({
                    "step": "verify_configuration",
                    "description": "Verify configuration files"
                })
            
            if "database" in components:
                rollback_steps.append({
                    "step": "restore_database",
                    "description": "Restore database from backup",
                    "estimated_duration": 300
                })
                verification_steps.append({
                    "step": "verify_database",
                    "description": "Verify database connectivity and data"
                })
            
            if "frontend" in components:
                rollback_steps.append({
                    "step": "restore_frontend",
                    "description": "Restore frontend files",
                    "estimated_duration": 120
                })
                verification_steps.append({
                    "step": "verify_frontend",
                    "description": "Verify frontend accessibility"
                })
            
            if "ssl" in components:
                rollback_steps.append({
                    "step": "restore_ssl",
                    "description": "Restore SSL certificates",
                    "estimated_duration": 60
                })
                verification_steps.append({
                    "step": "verify_ssl",
                    "description": "Verify SSL certificates"
                })
            
            if "monitoring" in components:
                rollback_steps.append({
                    "step": "restore_monitoring",
                    "description": "Restore monitoring configuration",
                    "estimated_duration": 90
                })
                verification_steps.append({
                    "step": "verify_monitoring",
                    "description": "Verify monitoring services"
                })
            
            # 计算总预估时间
            estimated_duration = sum(step.get("estimated_duration", 0) for step in rollback_steps)
            
            # 评估风险级别
            risk_level = self._assess_rollback_risk(components, snapshot_info)
            
            rollback_plan = RollbackPlan(
                rollback_id=rollback_id,
                target_snapshot_id=target_snapshot_id,
                trigger=trigger,
                components_to_rollback=components,
                estimated_duration=estimated_duration,
                risk_level=risk_level,
                rollback_steps=rollback_steps,
                verification_steps=verification_steps
            )
            
            self.logger.info(f"Rollback plan created: {rollback_id}")
            return rollback_plan
            
        except Exception as e:
            self.logger.error(f"Failed to create rollback plan: {str(e)}")
            return None
    
    def _assess_rollback_risk(self, components: List[str], snapshot_info: SnapshotInfo) -> str:
        """评估回滚风险级别"""
        risk_score = 0
        
        # 数据库回滚风险最高
        if "database" in components:
            risk_score += 3
        
        # 配置文件回滚中等风险
        if "config" in components:
            risk_score += 2
        
        # SSL证书回滚中等风险
        if "ssl" in components:
            risk_score += 2
        
        # 前端和监控回滚风险较低
        if "frontend" in components:
            risk_score += 1
        if "monitoring" in components:
            risk_score += 1
        
        # 快照年龄影响风险
        snapshot_age = datetime.now() - snapshot_info.timestamp
        if snapshot_age > timedelta(days=7):
            risk_score += 2
        elif snapshot_age > timedelta(days=1):
            risk_score += 1
        
        # 评估风险级别
        if risk_score >= 6:
            return "high"
        elif risk_score >= 3:
            return "medium"
        else:
            return "low"
    
    async def execute_rollback(self, rollback_plan: RollbackPlan) -> RollbackResult:
        """
        执行回滚操作
        
        Args:
            rollback_plan: 回滚计划
            
        Returns:
            回滚结果
        """
        self.logger.info(f"Starting rollback execution: {rollback_plan.rollback_id}")
        
        rollback_result = RollbackResult(
            rollback_id=rollback_plan.rollback_id,
            status=RollbackStatus.IN_PROGRESS,
            start_time=datetime.now()
        )
        
        try:
            # 提取快照
            snapshot_dir = await self._extract_snapshot(rollback_plan.target_snapshot_id)
            if not snapshot_dir:
                rollback_result.status = RollbackStatus.FAILED
                rollback_result.error_message = "Failed to extract snapshot"
                return rollback_result
            
            # 执行回滚步骤
            for step in rollback_plan.rollback_steps:
                step_name = step["step"]
                self.logger.info(f"Executing rollback step: {step_name}")
                
                try:
                    success = await self._execute_rollback_step(step_name, snapshot_dir, rollback_plan)
                    if success:
                        rollback_result.components_rolled_back.append(step_name)
                    else:
                        raise Exception(f"Rollback step {step_name} failed")
                        
                except Exception as e:
                    self.logger.error(f"Rollback step {step_name} failed: {str(e)}")
                    rollback_result.status = RollbackStatus.FAILED
                    rollback_result.error_message = f"Step {step_name} failed: {str(e)}"
                    return rollback_result
            
            # 执行验证步骤
            verification_results = {}
            for step in rollback_plan.verification_steps:
                step_name = step["step"]
                self.logger.info(f"Executing verification step: {step_name}")
                
                try:
                    success = await self._execute_verification_step(step_name)
                    verification_results[step_name] = success
                    
                    if not success:
                        self.logger.warning(f"Verification step {step_name} failed")
                        
                except Exception as e:
                    self.logger.error(f"Verification step {step_name} error: {str(e)}")
                    verification_results[step_name] = False
            
            rollback_result.verification_results = verification_results
            
            # 检查验证结果
            failed_verifications = [k for k, v in verification_results.items() if not v]
            if failed_verifications:
                rollback_result.status = RollbackStatus.FAILED
                rollback_result.error_message = f"Verification failed: {failed_verifications}"
            else:
                rollback_result.status = RollbackStatus.SUCCESS
                self.logger.info(f"Rollback completed successfully: {rollback_plan.rollback_id}")
            
            # 清理临时文件
            if snapshot_dir.exists():
                shutil.rmtree(snapshot_dir)
            
        except Exception as e:
            self.logger.error(f"Rollback execution failed: {str(e)}")
            rollback_result.status = RollbackStatus.FAILED
            rollback_result.error_message = str(e)
        
        finally:
            rollback_result.end_time = datetime.now()
            rollback_result.duration = (rollback_result.end_time - rollback_result.start_time).total_seconds()
            
            # 保存回滚记录
            self.rollback_history.append(rollback_result)
            await self._save_rollback_result(rollback_result)
        
        return rollback_result
    
    async def _extract_snapshot(self, snapshot_id: str) -> Optional[Path]:
        """提取快照文件"""
        try:
            snapshot_archive = self.snapshots_dir / f"{snapshot_id}.tar.gz"
            if not snapshot_archive.exists():
                self.logger.error(f"Snapshot archive not found: {snapshot_archive}")
                return None
            
            # 验证校验和
            snapshot_info = self.snapshots[snapshot_id]
            actual_checksum = self._calculate_checksum(snapshot_archive)
            if actual_checksum != snapshot_info.checksum:
                self.logger.error(f"Snapshot checksum mismatch: {snapshot_id}")
                return None
            
            # 提取到临时目录
            extract_dir = self.snapshots_dir / f"temp_{snapshot_id}"
            extract_dir.mkdir(exist_ok=True)
            
            with tarfile.open(snapshot_archive, "r:gz") as tar:
                tar.extractall(extract_dir)
            
            snapshot_dir = extract_dir / snapshot_id
            if snapshot_dir.exists():
                return snapshot_dir
            else:
                self.logger.error(f"Extracted snapshot directory not found: {snapshot_dir}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to extract snapshot {snapshot_id}: {str(e)}")
            return None
    
    async def _execute_rollback_step(self, step_name: str, snapshot_dir: Path, rollback_plan: RollbackPlan) -> bool:
        """执行回滚步骤"""
        try:
            if step_name == "restore_configuration":
                return await self._restore_configuration(snapshot_dir)
            elif step_name == "restore_database":
                return await self._restore_database(snapshot_dir)
            elif step_name == "restore_frontend":
                return await self._restore_frontend(snapshot_dir)
            elif step_name == "restore_ssl":
                return await self._restore_ssl_certificates(snapshot_dir)
            elif step_name == "restore_monitoring":
                return await self._restore_monitoring_config(snapshot_dir)
            else:
                self.logger.error(f"Unknown rollback step: {step_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Rollback step {step_name} failed: {str(e)}")
            return False
    
    async def _restore_configuration(self, snapshot_dir: Path) -> bool:
        """恢复配置文件"""
        try:
            config_dir = snapshot_dir / "config"
            if not config_dir.exists():
                return False
            
            # 恢复配置文件
            for config_file in config_dir.iterdir():
                if config_file.is_file():
                    target_file = self.project_root / config_file.name
                    
                    # 备份当前文件
                    if target_file.exists():
                        backup_file = target_file.with_suffix(f"{target_file.suffix}.rollback_backup")
                        shutil.copy2(target_file, backup_file)
                    
                    # 恢复文件
                    shutil.copy2(config_file, target_file)
                    self.logger.info(f"Restored config file: {target_file}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore configuration: {str(e)}")
            return False
    
    async def _restore_database(self, snapshot_dir: Path) -> bool:
        """恢复数据库"""
        try:
            db_dir = snapshot_dir / "database"
            backup_file = db_dir / "database_backup.sql"
            
            if not backup_file.exists():
                return False
            
            # 使用psql恢复数据库
            db_url = os.getenv("DATABASE_URL", "postgresql://lawsker_user:password@localhost:5432/lawsker_prod")
            
            cmd = [
                "psql",
                db_url,
                "--no-password",
                "--quiet",
                "-f", str(backup_file)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30分钟超时
            )
            
            if result.returncode == 0:
                self.logger.info("Database restored successfully")
                return True
            else:
                self.logger.error(f"Database restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to restore database: {str(e)}")
            return False
    
    async def _restore_frontend(self, snapshot_dir: Path) -> bool:
        """恢复前端文件"""
        try:
            frontend_dir = snapshot_dir / "frontend"
            if not frontend_dir.exists():
                return False
            
            # 恢复前端文件
            for tar_file in frontend_dir.glob("*.tar.gz"):
                # 确定目标目录
                if "frontend" in tar_file.name:
                    target_dir = self.project_root / "frontend"
                elif "lawsker" in tar_file.name:
                    target_dir = Path("/var/www/lawsker")
                else:
                    continue
                
                # 备份当前目录
                if target_dir.exists():
                    backup_dir = target_dir.with_suffix(".rollback_backup")
                    if backup_dir.exists():
                        shutil.rmtree(backup_dir)
                    shutil.move(target_dir, backup_dir)
                
                # 提取文件
                target_dir.parent.mkdir(parents=True, exist_ok=True)
                
                with tarfile.open(tar_file, "r:gz") as tar:
                    tar.extractall(target_dir.parent)
                
                self.logger.info(f"Restored frontend files to: {target_dir}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore frontend: {str(e)}")
            return False
    
    async def _restore_ssl_certificates(self, snapshot_dir: Path) -> bool:
        """恢复SSL证书"""
        try:
            ssl_dir = snapshot_dir / "ssl"
            backup_tar = ssl_dir / "letsencrypt_backup.tar.gz"
            
            if not backup_tar.exists():
                return False
            
            # 备份当前证书
            letsencrypt_dir = Path("/etc/letsencrypt")
            if letsencrypt_dir.exists():
                backup_dir = Path("/etc/letsencrypt.rollback_backup")
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)
                shutil.move(letsencrypt_dir, backup_dir)
            
            # 恢复证书
            with tarfile.open(backup_tar, "r:gz") as tar:
                tar.extractall("/etc")
            
            self.logger.info("SSL certificates restored successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore SSL certificates: {str(e)}")
            return False
    
    async def _restore_monitoring_config(self, snapshot_dir: Path) -> bool:
        """恢复监控配置"""
        try:
            monitoring_dir = snapshot_dir / "monitoring"
            if not monitoring_dir.exists():
                return False
            
            # 恢复监控配置
            for tar_file in monitoring_dir.glob("*.tar.gz"):
                if "monitoring" in tar_file.name:
                    target_dir = self.project_root / "monitoring"
                elif "opt" in tar_file.name:
                    target_dir = Path("/opt/monitoring")
                else:
                    continue
                
                # 备份当前配置
                if target_dir.exists():
                    backup_dir = target_dir.with_suffix(".rollback_backup")
                    if backup_dir.exists():
                        shutil.rmtree(backup_dir)
                    shutil.move(target_dir, backup_dir)
                
                # 恢复配置
                target_dir.parent.mkdir(parents=True, exist_ok=True)
                
                with tarfile.open(tar_file, "r:gz") as tar:
                    tar.extractall(target_dir.parent)
                
                self.logger.info(f"Restored monitoring config to: {target_dir}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore monitoring config: {str(e)}")
            return False
    
    async def _execute_verification_step(self, step_name: str) -> bool:
        """执行验证步骤"""
        try:
            if step_name == "verify_configuration":
                return await self._verify_configuration()
            elif step_name == "verify_database":
                return await self._verify_database()
            elif step_name == "verify_frontend":
                return await self._verify_frontend()
            elif step_name == "verify_ssl":
                return await self._verify_ssl_certificates()
            elif step_name == "verify_monitoring":
                return await self._verify_monitoring_services()
            else:
                self.logger.error(f"Unknown verification step: {step_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Verification step {step_name} failed: {str(e)}")
            return False
    
    async def _verify_configuration(self) -> bool:
        """验证配置文件"""
        try:
            # 检查关键配置文件是否存在
            config_files = [
                self.project_root / ".env.production",
                self.project_root / "nginx" / "nginx.conf"
            ]
            
            for config_file in config_files:
                if not config_file.exists():
                    self.logger.error(f"Configuration file missing: {config_file}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration verification failed: {str(e)}")
            return False
    
    async def _verify_database(self) -> bool:
        """验证数据库"""
        try:
            db_url = os.getenv("DATABASE_URL", "postgresql://lawsker_user:password@localhost:5432/lawsker_prod")
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            # 执行简单查询
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Database verification failed: {str(e)}")
            return False
    
    async def _verify_frontend(self) -> bool:
        """验证前端"""
        try:
            # 检查前端文件是否存在
            frontend_dir = self.project_root / "frontend"
            if not frontend_dir.exists():
                return False
            
            # 检查关键文件
            key_files = ["index.html", "dashboard.html"]
            for key_file in key_files:
                if not (frontend_dir / key_file).exists():
                    self.logger.error(f"Frontend file missing: {key_file}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Frontend verification failed: {str(e)}")
            return False
    
    async def _verify_ssl_certificates(self) -> bool:
        """验证SSL证书"""
        try:
            letsencrypt_dir = Path("/etc/letsencrypt")
            return letsencrypt_dir.exists()
            
        except Exception as e:
            self.logger.error(f"SSL verification failed: {str(e)}")
            return False
    
    async def _verify_monitoring_services(self) -> bool:
        """验证监控服务"""
        try:
            monitoring_dir = self.project_root / "monitoring"
            return monitoring_dir.exists()
            
        except Exception as e:
            self.logger.error(f"Monitoring verification failed: {str(e)}")
            return False
    
    async def _save_rollback_result(self, rollback_result: RollbackResult):
        """保存回滚结果"""
        try:
            result_file = self.rollback_logs_dir / f"{rollback_result.rollback_id}.json"
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(rollback_result.to_dict(), f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to save rollback result: {str(e)}")
    
    def list_snapshots(self) -> List[SnapshotInfo]:
        """列出所有快照"""
        return list(self.snapshots.values())
    
    def get_snapshot(self, snapshot_id: str) -> Optional[SnapshotInfo]:
        """获取快照信息"""
        return self.snapshots.get(snapshot_id)
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        try:
            if snapshot_id not in self.snapshots:
                return False
            
            # 删除快照文件
            snapshot_archive = self.snapshots_dir / f"{snapshot_id}.tar.gz"
            if snapshot_archive.exists():
                snapshot_archive.unlink()
            
            # 从索引中删除
            del self.snapshots[snapshot_id]
            self._save_snapshots_index()
            
            self.logger.info(f"Snapshot deleted: {snapshot_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete snapshot {snapshot_id}: {str(e)}")
            return False
    
    def cleanup_old_snapshots(self):
        """清理过期快照"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.backup_retention_days)
            
            snapshots_to_delete = [
                snapshot_id for snapshot_id, snapshot_info in self.snapshots.items()
                if snapshot_info.timestamp < cutoff_date
            ]
            
            for snapshot_id in snapshots_to_delete:
                self.delete_snapshot(snapshot_id)
            
            if snapshots_to_delete:
                self.logger.info(f"Cleaned up {len(snapshots_to_delete)} old snapshots")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old snapshots: {str(e)}")
    
    def get_rollback_history(self) -> List[RollbackResult]:
        """获取回滚历史"""
        return self.rollback_history.copy()


# 工厂函数
def create_rollback_system(project_root: str, retention_days: int = 30) -> DeploymentRollbackSystem:
    """
    创建部署回滚系统
    
    Args:
        project_root: 项目根目录
        retention_days: 快照保留天数
        
    Returns:
        DeploymentRollbackSystem实例
    """
    return DeploymentRollbackSystem(project_root, retention_days)


# 主函数用于测试
async def main():
    """主函数用于测试回滚系统"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deployment Rollback System')
    parser.add_argument('--project-root', default='.', help='Project root directory')
    parser.add_argument('--action', choices=['create-snapshot', 'list-snapshots', 'rollback'], 
                       required=True, help='Action to perform')
    parser.add_argument('--deployment-id', help='Deployment ID for snapshot')
    parser.add_argument('--snapshot-id', help='Snapshot ID for rollback')
    parser.add_argument('--components', nargs='+', help='Components to backup/rollback')
    parser.add_argument('--description', help='Snapshot description')
    
    args = parser.parse_args()
    
    # 创建回滚系统
    rollback_system = create_rollback_system(args.project_root)
    
    try:
        if args.action == 'create-snapshot':
            if not args.deployment_id:
                print("Deployment ID is required for creating snapshot")
                sys.exit(1)
            
            snapshot_info = await rollback_system.create_deployment_snapshot(
                deployment_id=args.deployment_id,
                description=args.description or "",
                components=args.components
            )
            
            if snapshot_info:
                print(f"Snapshot created: {snapshot_info.snapshot_id}")
                print(json.dumps(snapshot_info.to_dict(), indent=2, ensure_ascii=False))
            else:
                print("Failed to create snapshot")
                sys.exit(1)
                
        elif args.action == 'list-snapshots':
            snapshots = rollback_system.list_snapshots()
            
            if snapshots:
                print(f"Found {len(snapshots)} snapshots:")
                for snapshot in snapshots:
                    print(f"- {snapshot.snapshot_id}: {snapshot.description} ({snapshot.timestamp})")
            else:
                print("No snapshots found")
                
        elif args.action == 'rollback':
            if not args.snapshot_id:
                print("Snapshot ID is required for rollback")
                sys.exit(1)
            
            # 创建回滚计划
            rollback_plan = rollback_system.create_rollback_plan(
                target_snapshot_id=args.snapshot_id,
                trigger=RollbackTrigger.MANUAL,
                components=args.components
            )
            
            if not rollback_plan:
                print("Failed to create rollback plan")
                sys.exit(1)
            
            print(f"Rollback plan created: {rollback_plan.rollback_id}")
            print(f"Risk level: {rollback_plan.risk_level}")
            print(f"Estimated duration: {rollback_plan.estimated_duration} seconds")
            
            # 执行回滚
            rollback_result = await rollback_system.execute_rollback(rollback_plan)
            
            print(f"Rollback result: {rollback_result.status.value}")
            if rollback_result.error_message:
                print(f"Error: {rollback_result.error_message}")
            
            print(json.dumps(rollback_result.to_dict(), indent=2, ensure_ascii=False))
            
            if rollback_result.status == RollbackStatus.SUCCESS:
                sys.exit(0)
            else:
                sys.exit(1)
                
    except Exception as e:
        print(f"Operation failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())