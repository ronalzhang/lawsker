#!/usr/bin/env python3
"""
主部署脚本 - 整合所有部署组件
使用DeploymentOrchestrator、DeploymentVerificationSuite和DeploymentRollbackSystem
"""

import os
import sys
import json
import asyncio
import argparse
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

# 导入部署组件
from .deployment_orchestrator import (
    DeploymentOrchestrator, 
    DeploymentConfig, 
    create_deployment_orchestrator
)
from .deployment_verification import (
    DeploymentVerificationSuite,
    VerificationConfig,
    create_verification_suite
)
from .deployment_rollback import (
    DeploymentRollbackSystem,
    RollbackTrigger,
    create_rollback_system
)


class MainDeploymentScript:
    """
    主部署脚本类
    
    整合部署编排、验证测试和回滚系统
    """
    
    def __init__(self, project_root: str, config: Dict[str, Any] = None):
        self.project_root = Path(project_root).resolve()
        self.config = config or {}
        self.logger = self._setup_logger()
        
        # 初始化子系统
        self.orchestrator: Optional[DeploymentOrchestrator] = None
        self.verification_suite: Optional[DeploymentVerificationSuite] = None
        self.rollback_system: Optional[DeploymentRollbackSystem] = None
        
        # 部署结果
        self.deployment_report: Optional[Dict[str, Any]] = None
        self.verification_report: Optional[Dict[str, Any]] = None
        self.rollback_result: Optional[Dict[str, Any]] = None
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # 文件处理器
            log_dir = self.project_root / "backend" / "deployment" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / f"deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
        return logger
    
    def _initialize_systems(self):
        """初始化部署系统"""
        try:
            # 获取配置
            domains = self.config.get("domains", ["lawsker.com"])
            ssl_enabled = self.config.get("ssl_enabled", True)
            monitoring_enabled = self.config.get("monitoring_enabled", True)
            parallel_execution = self.config.get("parallel_execution", True)
            
            # 初始化部署编排器
            self.orchestrator = create_deployment_orchestrator(
                project_root=str(self.project_root),
                domains=domains,
                ssl_enabled=ssl_enabled,
                monitoring_enabled=monitoring_enabled,
                parallel_execution=parallel_execution
            )
            
            # 初始化验证测试套件
            base_url = self.config.get("base_url", "http://localhost:8000")
            database_url = self.config.get("database_url", 
                "postgresql://lawsker_user:password@localhost:5432/lawsker_prod")
            
            self.verification_suite = create_verification_suite(
                base_url=base_url,
                domains=domains,
                database_url=database_url
            )
            
            # 初始化回滚系统
            retention_days = self.config.get("backup_retention_days", 30)
            self.rollback_system = create_rollback_system(
                project_root=str(self.project_root),
                retention_days=retention_days
            )
            
            self.logger.info("All deployment systems initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize deployment systems: {str(e)}")
            raise
    
    async def run_full_deployment(self) -> Dict[str, Any]:
        """
        运行完整部署流程
        
        Returns:
            完整的部署报告
        """
        self.logger.info("Starting full deployment process")
        start_time = datetime.now()
        
        overall_result = {
            "start_time": start_time.isoformat(),
            "status": "in_progress",
            "phases": {
                "initialization": {"status": "pending"},
                "pre_deployment_snapshot": {"status": "pending"},
                "deployment": {"status": "pending"},
                "verification": {"status": "pending"},
                "post_deployment_snapshot": {"status": "pending"}
            },
            "reports": {},
            "errors": []
        }
        
        try:
            # 阶段1: 初始化系统
            self.logger.info("Phase 1: Initializing deployment systems")
            overall_result["phases"]["initialization"]["status"] = "in_progress"
            
            self._initialize_systems()
            
            overall_result["phases"]["initialization"]["status"] = "completed"
            overall_result["phases"]["initialization"]["message"] = "Systems initialized successfully"
            
            # 阶段2: 创建部署前快照
            self.logger.info("Phase 2: Creating pre-deployment snapshot")
            overall_result["phases"]["pre_deployment_snapshot"]["status"] = "in_progress"
            
            pre_snapshot = await self.rollback_system.create_deployment_snapshot(
                deployment_id=f"pre_deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                description="Pre-deployment snapshot for rollback safety"
            )
            
            if pre_snapshot:
                overall_result["phases"]["pre_deployment_snapshot"]["status"] = "completed"
                overall_result["phases"]["pre_deployment_snapshot"]["snapshot_id"] = pre_snapshot.snapshot_id
                overall_result["phases"]["pre_deployment_snapshot"]["message"] = "Pre-deployment snapshot created"
            else:
                overall_result["phases"]["pre_deployment_snapshot"]["status"] = "failed"
                overall_result["phases"]["pre_deployment_snapshot"]["message"] = "Failed to create pre-deployment snapshot"
                overall_result["errors"].append("Pre-deployment snapshot creation failed")
            
            # 阶段3: 执行部署
            self.logger.info("Phase 3: Executing deployment")
            overall_result["phases"]["deployment"]["status"] = "in_progress"
            
            self.deployment_report = await self.orchestrator.deploy()
            overall_result["reports"]["deployment"] = self.deployment_report
            
            if self.deployment_report["status"] == "success":
                overall_result["phases"]["deployment"]["status"] = "completed"
                overall_result["phases"]["deployment"]["message"] = "Deployment completed successfully"
            else:
                overall_result["phases"]["deployment"]["status"] = "failed"
                overall_result["phases"]["deployment"]["message"] = "Deployment failed"
                overall_result["errors"].append("Deployment execution failed")
                
                # 如果部署失败，执行回滚
                if pre_snapshot:
                    await self._handle_deployment_failure(pre_snapshot.snapshot_id, overall_result)
                
                return overall_result
            
            # 阶段4: 执行验证测试
            self.logger.info("Phase 4: Running verification tests")
            overall_result["phases"]["verification"]["status"] = "in_progress"
            
            # 等待服务启动
            await asyncio.sleep(30)
            
            self.verification_report = await self.verification_suite.run_all_tests()
            overall_result["reports"]["verification"] = self.verification_report
            
            verification_success_rate = self.verification_report["summary"]["success_rate"]
            
            if verification_success_rate >= 80:  # 80%成功率阈值
                overall_result["phases"]["verification"]["status"] = "completed"
                overall_result["phases"]["verification"]["message"] = f"Verification passed ({verification_success_rate:.1f}% success rate)"
            else:
                overall_result["phases"]["verification"]["status"] = "failed"
                overall_result["phases"]["verification"]["message"] = f"Verification failed ({verification_success_rate:.1f}% success rate)"
                overall_result["errors"].append("Verification tests failed")
                
                # 如果验证失败，执行回滚
                if pre_snapshot:
                    await self._handle_verification_failure(pre_snapshot.snapshot_id, overall_result)
                
                return overall_result
            
            # 阶段5: 创建部署后快照
            self.logger.info("Phase 5: Creating post-deployment snapshot")
            overall_result["phases"]["post_deployment_snapshot"]["status"] = "in_progress"
            
            post_snapshot = await self.rollback_system.create_deployment_snapshot(
                deployment_id=self.deployment_report["deployment_id"],
                description="Post-deployment snapshot - successful deployment"
            )
            
            if post_snapshot:
                overall_result["phases"]["post_deployment_snapshot"]["status"] = "completed"
                overall_result["phases"]["post_deployment_snapshot"]["snapshot_id"] = post_snapshot.snapshot_id
                overall_result["phases"]["post_deployment_snapshot"]["message"] = "Post-deployment snapshot created"
            else:
                overall_result["phases"]["post_deployment_snapshot"]["status"] = "failed"
                overall_result["phases"]["post_deployment_snapshot"]["message"] = "Failed to create post-deployment snapshot"
                overall_result["errors"].append("Post-deployment snapshot creation failed")
            
            # 部署成功
            overall_result["status"] = "success"
            self.logger.info("Full deployment process completed successfully")
            
        except Exception as e:
            self.logger.error(f"Deployment process failed: {str(e)}")
            overall_result["status"] = "error"
            overall_result["error_message"] = str(e)
            overall_result["errors"].append(f"Deployment process error: {str(e)}")
        
        finally:
            end_time = datetime.now()
            overall_result["end_time"] = end_time.isoformat()
            overall_result["total_duration"] = (end_time - start_time).total_seconds()
            
            # 保存完整报告
            await self._save_deployment_report(overall_result)
        
        return overall_result
    
    async def _handle_deployment_failure(self, pre_snapshot_id: str, overall_result: Dict[str, Any]):
        """处理部署失败，执行回滚"""
        self.logger.warning("Deployment failed, initiating rollback")
        
        try:
            # 创建回滚计划
            rollback_plan = self.rollback_system.create_rollback_plan(
                target_snapshot_id=pre_snapshot_id,
                trigger=RollbackTrigger.DEPLOYMENT_FAILURE
            )
            
            if rollback_plan:
                # 执行回滚
                rollback_result = await self.rollback_system.execute_rollback(rollback_plan)
                
                overall_result["rollback"] = {
                    "triggered": True,
                    "reason": "deployment_failure",
                    "result": rollback_result.to_dict()
                }
                
                if rollback_result.status.value == "success":
                    self.logger.info("Rollback completed successfully")
                else:
                    self.logger.error("Rollback failed")
            else:
                overall_result["rollback"] = {
                    "triggered": False,
                    "reason": "failed_to_create_rollback_plan"
                }
                
        except Exception as e:
            self.logger.error(f"Rollback failed: {str(e)}")
            overall_result["rollback"] = {
                "triggered": False,
                "reason": f"rollback_error: {str(e)}"
            }
    
    async def _handle_verification_failure(self, pre_snapshot_id: str, overall_result: Dict[str, Any]):
        """处理验证失败，执行回滚"""
        self.logger.warning("Verification failed, initiating rollback")
        
        try:
            # 创建回滚计划
            rollback_plan = self.rollback_system.create_rollback_plan(
                target_snapshot_id=pre_snapshot_id,
                trigger=RollbackTrigger.HEALTH_CHECK_FAILURE
            )
            
            if rollback_plan:
                # 执行回滚
                rollback_result = await self.rollback_system.execute_rollback(rollback_plan)
                
                overall_result["rollback"] = {
                    "triggered": True,
                    "reason": "verification_failure",
                    "result": rollback_result.to_dict()
                }
                
                if rollback_result.status.value == "success":
                    self.logger.info("Rollback completed successfully")
                else:
                    self.logger.error("Rollback failed")
            else:
                overall_result["rollback"] = {
                    "triggered": False,
                    "reason": "failed_to_create_rollback_plan"
                }
                
        except Exception as e:
            self.logger.error(f"Rollback failed: {str(e)}")
            overall_result["rollback"] = {
                "triggered": False,
                "reason": f"rollback_error: {str(e)}"
            }
    
    async def _save_deployment_report(self, report: Dict[str, Any]):
        """保存部署报告"""
        try:
            reports_dir = self.project_root / "backend" / "deployment" / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = reports_dir / f"full_deployment_report_{timestamp}.json"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Deployment report saved: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save deployment report: {str(e)}")
    
    async def run_verification_only(self) -> Dict[str, Any]:
        """仅运行验证测试"""
        self.logger.info("Running verification tests only")
        
        try:
            self._initialize_systems()
            
            verification_report = await self.verification_suite.run_all_tests()
            
            # 保存验证报告
            self.verification_suite.save_report(verification_report)
            
            return verification_report
            
        except Exception as e:
            self.logger.error(f"Verification failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_rollback(self, snapshot_id: str, components: List[str] = None) -> Dict[str, Any]:
        """执行手动回滚"""
        self.logger.info(f"Running manual rollback to snapshot: {snapshot_id}")
        
        try:
            self._initialize_systems()
            
            # 创建回滚计划
            rollback_plan = self.rollback_system.create_rollback_plan(
                target_snapshot_id=snapshot_id,
                trigger=RollbackTrigger.MANUAL,
                components=components
            )
            
            if not rollback_plan:
                return {
                    "status": "error",
                    "error": "Failed to create rollback plan",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 执行回滚
            rollback_result = await self.rollback_system.execute_rollback(rollback_plan)
            
            return rollback_result.to_dict()
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def list_snapshots(self) -> List[Dict[str, Any]]:
        """列出所有快照"""
        try:
            if not self.rollback_system:
                self._initialize_systems()
            
            snapshots = self.rollback_system.list_snapshots()
            return [snapshot.to_dict() for snapshot in snapshots]
            
        except Exception as e:
            self.logger.error(f"Failed to list snapshots: {str(e)}")
            return []
    
    async def create_snapshot(self, deployment_id: str, description: str = "", components: List[str] = None) -> Optional[Dict[str, Any]]:
        """创建快照"""
        try:
            if not self.rollback_system:
                self._initialize_systems()
            
            snapshot_info = await self.rollback_system.create_deployment_snapshot(
                deployment_id=deployment_id,
                description=description,
                components=components
            )
            
            return snapshot_info.to_dict() if snapshot_info else None
            
        except Exception as e:
            self.logger.error(f"Failed to create snapshot: {str(e)}")
            return None


def load_config_file(config_path: str) -> Dict[str, Any]:
    """加载配置文件"""
    try:
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.suffix.lower() == '.json':
                    return json.load(f)
                else:
                    # 简单的键值对配置
                    config = {}
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
                    return config
        return {}
    except Exception as e:
        print(f"Failed to load config file {config_path}: {str(e)}")
        return {}


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Lawsker Deployment Script')
    
    # 基本参数
    parser.add_argument('--project-root', default='.', help='Project root directory')
    parser.add_argument('--config', help='Configuration file path')
    
    # 操作选择
    parser.add_argument('--action', choices=[
        'deploy', 'verify', 'rollback', 'list-snapshots', 'create-snapshot'
    ], default='deploy', help='Action to perform')
    
    # 部署参数
    parser.add_argument('--domains', nargs='+', default=['lawsker.com'], help='Domains to deploy')
    parser.add_argument('--no-ssl', action='store_true', help='Disable SSL')
    parser.add_argument('--no-monitoring', action='store_true', help='Disable monitoring')
    parser.add_argument('--no-parallel', action='store_true', help='Disable parallel execution')
    
    # 验证参数
    parser.add_argument('--base-url', default='http://localhost:8000', help='Base URL for verification')
    parser.add_argument('--database-url', help='Database URL for verification')
    
    # 回滚参数
    parser.add_argument('--snapshot-id', help='Snapshot ID for rollback')
    parser.add_argument('--components', nargs='+', help='Components to rollback')
    
    # 快照参数
    parser.add_argument('--deployment-id', help='Deployment ID for snapshot')
    parser.add_argument('--description', help='Snapshot description')
    
    # 输出参数
    parser.add_argument('--output', help='Output file for reports')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 加载配置
    config = {}
    if args.config:
        config = load_config_file(args.config)
    
    # 从命令行参数更新配置
    config.update({
        "domains": args.domains,
        "ssl_enabled": not args.no_ssl,
        "monitoring_enabled": not args.no_monitoring,
        "parallel_execution": not args.no_parallel,
        "base_url": args.base_url,
        "database_url": args.database_url
    })
    
    # 创建部署脚本实例
    deployment_script = MainDeploymentScript(args.project_root, config)
    
    try:
        if args.action == 'deploy':
            print("Starting full deployment process...")
            result = await deployment_script.run_full_deployment()
            
            # 输出结果
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 设置退出码
            if result["status"] == "success":
                print("\n✅ Deployment completed successfully!")
                sys.exit(0)
            else:
                print(f"\n❌ Deployment failed: {result.get('error_message', 'Unknown error')}")
                sys.exit(1)
                
        elif args.action == 'verify':
            print("Running verification tests...")
            result = await deployment_script.run_verification_only()
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
            
            # 输出摘要
            if "summary" in result:
                summary = result["summary"]
                print(f"\nVerification Results:")
                print(f"Total Tests: {summary['total_tests']}")
                print(f"Passed: {summary['passed']}")
                print(f"Failed: {summary['failed']}")
                print(f"Errors: {summary['errors']}")
                print(f"Success Rate: {summary['success_rate']:.1f}%")
                
                if summary['failed'] == 0 and summary['errors'] == 0:
                    print("\n✅ All verification tests passed!")
                    sys.exit(0)
                else:
                    print("\n❌ Some verification tests failed!")
                    sys.exit(1)
            else:
                print(f"\n❌ Verification failed: {result.get('error', 'Unknown error')}")
                sys.exit(1)
                
        elif args.action == 'rollback':
            if not args.snapshot_id:
                print("Snapshot ID is required for rollback")
                sys.exit(1)
            
            print(f"Rolling back to snapshot: {args.snapshot_id}")
            result = await deployment_script.run_rollback(args.snapshot_id, args.components)
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if result.get("status") == "success":
                print("\n✅ Rollback completed successfully!")
                sys.exit(0)
            else:
                print(f"\n❌ Rollback failed: {result.get('error_message', 'Unknown error')}")
                sys.exit(1)
                
        elif args.action == 'list-snapshots':
            snapshots = deployment_script.list_snapshots()
            
            if snapshots:
                print(f"Found {len(snapshots)} snapshots:")
                for snapshot in snapshots:
                    print(f"- {snapshot['snapshot_id']}: {snapshot['description']}")
                    print(f"  Created: {snapshot['timestamp']}")
                    print(f"  Components: {', '.join(snapshot['components'])}")
                    print(f"  Size: {snapshot['size_bytes']} bytes")
                    print()
            else:
                print("No snapshots found")
                
        elif args.action == 'create-snapshot':
            if not args.deployment_id:
                print("Deployment ID is required for creating snapshot")
                sys.exit(1)
            
            print(f"Creating snapshot for deployment: {args.deployment_id}")
            result = await deployment_script.create_snapshot(
                deployment_id=args.deployment_id,
                description=args.description or "",
                components=args.components
            )
            
            if result:
                print(f"✅ Snapshot created: {result['snapshot_id']}")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print("❌ Failed to create snapshot")
                sys.exit(1)
                
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"Operation failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())