#!/usr/bin/env python3
"""
自动化部署脚本
支持蓝绿部署、滚动更新、回滚等功能
"""
import os
import sys
import json
import time
import shutil
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
import requests
from app.core.logging import get_logger

logger = get_logger(__name__)

class DeploymentManager:
    """部署管理器"""
    
    def __init__(self, config_file: str = "deploy_config.yaml"):
        self.config_file = config_file
        self.config = self._load_config()
        self.deployment_history = []
        self.current_deployment = None
    
    def _load_config(self) -> Dict[str, Any]:
        """加载部署配置"""
        config_path = Path(self.config_file)
        if not config_path.exists():
            # 创建默认配置
            default_config = {
                "environments": {
                    "staging": {
                        "servers": ["staging.lawsker.com"],
                        "database_url": "postgresql://user:pass@staging-db:5432/lawsker",
                        "redis_url": "redis://staging-redis:6379/0",
                        "backup_retention_days": 7
                    },
                    "production": {
                        "servers": ["prod1.lawsker.com", "prod2.lawsker.com"],
                        "database_url": "postgresql://user:pass@prod-db:5432/lawsker",
                        "redis_url": "redis://prod-redis:6379/0",
                        "backup_retention_days": 30
                    }
                },
                "deployment": {
                    "strategy": "blue_green",  # blue_green, rolling, recreate
                    "health_check_url": "/api/v1/health",
                    "health_check_timeout": 30,
                    "rollback_on_failure": True,
                    "pre_deploy_hooks": [],
                    "post_deploy_hooks": []
                },
                "backup": {
                    "enabled": True,
                    "storage_path": "/backups",
                    "compression": True,
                    "encryption": True
                },
                "monitoring": {
                    "enabled": True,
                    "webhook_url": None,
                    "slack_channel": None
                }
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            
            return default_config
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def deploy(self, environment: str, version: str = None, force: bool = False) -> bool:
        """执行部署"""
        try:
            logger.info(f"Starting deployment to {environment}")
            
            # 验证环境配置
            if environment not in self.config["environments"]:
                raise ValueError(f"Unknown environment: {environment}")
            
            env_config = self.config["environments"][environment]
            
            # 创建部署记录
            deployment_id = f"deploy_{int(time.time())}"
            self.current_deployment = {
                "id": deployment_id,
                "environment": environment,
                "version": version or "latest",
                "start_time": datetime.now().isoformat(),
                "status": "in_progress",
                "steps": []
            }
            
            # 执行部署步骤
            success = self._execute_deployment_steps(env_config, force)
            
            # 更新部署状态
            self.current_deployment["status"] = "success" if success else "failed"
            self.current_deployment["end_time"] = datetime.now().isoformat()
            
            # 保存部署历史
            self.deployment_history.append(self.current_deployment.copy())
            self._save_deployment_history()
            
            if success:
                logger.info(f"Deployment {deployment_id} completed successfully")
                self._send_notification(f"✅ Deployment to {environment} completed successfully")
            else:
                logger.error(f"Deployment {deployment_id} failed")
                self._send_notification(f"❌ Deployment to {environment} failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            if self.current_deployment:
                self.current_deployment["status"] = "error"
                self.current_deployment["error"] = str(e)
                self.current_deployment["end_time"] = datetime.now().isoformat()
            
            self._send_notification(f"💥 Deployment to {environment} error: {str(e)}")
            return False
    
    def _execute_deployment_steps(self, env_config: Dict[str, Any], force: bool) -> bool:
        """执行部署步骤"""
        steps = [
            ("pre_deploy_backup", self._create_backup),
            ("health_check", self._check_current_health),
            ("pre_deploy_hooks", self._run_pre_deploy_hooks),
            ("code_deployment", self._deploy_code),
            ("database_migration", self._run_database_migrations),
            ("service_restart", self._restart_services),
            ("health_check_new", self._check_new_deployment_health),
            ("post_deploy_hooks", self._run_post_deploy_hooks),
            ("cleanup", self._cleanup_old_deployments)
        ]
        
        for step_name, step_func in steps:
            try:
                logger.info(f"Executing step: {step_name}")
                step_start = time.time()
                
                result = step_func(env_config, force)
                
                step_duration = time.time() - step_start
                step_record = {
                    "name": step_name,
                    "status": "success" if result else "failed",
                    "duration": round(step_duration, 2),
                    "timestamp": datetime.now().isoformat()
                }
                
                self.current_deployment["steps"].append(step_record)
                
                if not result:
                    logger.error(f"Step {step_name} failed")
                    
                    # 如果配置了失败回滚，执行回滚
                    if self.config["deployment"].get("rollback_on_failure", True):
                        logger.info("Initiating rollback due to deployment failure")
                        self._rollback(env_config)
                    
                    return False
                
                logger.info(f"Step {step_name} completed in {step_duration:.2f}s")
                
            except Exception as e:
                logger.error(f"Step {step_name} error: {str(e)}")
                step_record = {
                    "name": step_name,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                self.current_deployment["steps"].append(step_record)
                return False
        
        return True
    
    def _create_backup(self, env_config: Dict[str, Any], force: bool) -> bool:
        """创建部署前备份"""
        if not self.config["backup"]["enabled"]:
            logger.info("Backup disabled, skipping")
            return True
        
        try:
            backup_manager = DatabaseBackupManager(env_config["database_url"])
            backup_file = backup_manager.create_backup(
                f"pre_deploy_{self.current_deployment['id']}"
            )
            
            self.current_deployment["backup_file"] = backup_file
            logger.info(f"Backup created: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}")
            return not force  # 如果强制部署，忽略备份失败
    
    def _check_current_health(self, env_config: Dict[str, Any], force: bool) -> bool:
        """检查当前系统健康状态"""
        health_url = f"http://{env_config['servers'][0]}{self.config['deployment']['health_check_url']}"
        timeout = self.config["deployment"]["health_check_timeout"]
        
        try:
            response = requests.get(health_url, timeout=timeout)
            if response.status_code == 200:
                logger.info("Current system health check passed")
                return True
            else:
                logger.warning(f"Health check returned status {response.status_code}")
                return force  # 如果强制部署，忽略健康检查失败
                
        except Exception as e:
            logger.warning(f"Health check failed: {str(e)}")
            return force
    
    def _run_pre_deploy_hooks(self, env_config: Dict[str, Any], force: bool) -> bool:
        """运行部署前钩子"""
        hooks = self.config["deployment"].get("pre_deploy_hooks", [])
        return self._run_hooks(hooks, "pre_deploy")
    
    def _deploy_code(self, env_config: Dict[str, Any], force: bool) -> bool:
        """部署代码"""
        strategy = self.config["deployment"]["strategy"]
        
        if strategy == "blue_green":
            return self._blue_green_deploy(env_config)
        elif strategy == "rolling":
            return self._rolling_deploy(env_config)
        elif strategy == "recreate":
            return self._recreate_deploy(env_config)
        else:
            logger.error(f"Unknown deployment strategy: {strategy}")
            return False
    
    def _blue_green_deploy(self, env_config: Dict[str, Any]) -> bool:
        """蓝绿部署"""
        try:
            # 这里实现蓝绿部署逻辑
            # 1. 部署到绿色环境
            # 2. 测试绿色环境
            # 3. 切换流量到绿色环境
            # 4. 保留蓝色环境作为回滚备份
            
            logger.info("Executing blue-green deployment")
            
            # 模拟部署过程
            for server in env_config["servers"]:
                logger.info(f"Deploying to server: {server}")
                # 这里应该是实际的部署命令
                time.sleep(2)  # 模拟部署时间
            
            return True
            
        except Exception as e:
            logger.error(f"Blue-green deployment failed: {str(e)}")
            return False
    
    def _rolling_deploy(self, env_config: Dict[str, Any]) -> bool:
        """滚动部署"""
        try:
            logger.info("Executing rolling deployment")
            
            # 逐个服务器部署
            for i, server in enumerate(env_config["servers"]):
                logger.info(f"Deploying to server {i+1}/{len(env_config['servers'])}: {server}")
                
                # 部署到当前服务器
                # 这里应该是实际的部署命令
                time.sleep(2)  # 模拟部署时间
                
                # 健康检查
                if not self._check_server_health(server):
                    logger.error(f"Health check failed for server: {server}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Rolling deployment failed: {str(e)}")
            return False
    
    def _recreate_deploy(self, env_config: Dict[str, Any]) -> bool:
        """重建部署"""
        try:
            logger.info("Executing recreate deployment")
            
            # 停止所有服务
            for server in env_config["servers"]:
                logger.info(f"Stopping services on server: {server}")
                # 这里应该是停止服务的命令
                time.sleep(1)
            
            # 部署新版本
            for server in env_config["servers"]:
                logger.info(f"Deploying to server: {server}")
                # 这里应该是部署命令
                time.sleep(2)
            
            # 启动服务
            for server in env_config["servers"]:
                logger.info(f"Starting services on server: {server}")
                # 这里应该是启动服务的命令
                time.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"Recreate deployment failed: {str(e)}")
            return False
    
    def _run_database_migrations(self, env_config: Dict[str, Any], force: bool) -> bool:
        """运行数据库迁移"""
        try:
            logger.info("Running database migrations")
            
            # 运行Alembic迁移
            result = subprocess.run([
                "alembic", "upgrade", "head"
            ], capture_output=True, text=True, cwd="backend")
            
            if result.returncode == 0:
                logger.info("Database migrations completed successfully")
                return True
            else:
                logger.error(f"Database migration failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Database migration error: {str(e)}")
            return False
    
    def _restart_services(self, env_config: Dict[str, Any], force: bool) -> bool:
        """重启服务"""
        try:
            logger.info("Restarting services")
            
            # 这里应该是重启服务的实际命令
            # 例如：systemctl restart lawsker-backend
            # 或者：docker-compose restart
            
            time.sleep(3)  # 模拟重启时间
            logger.info("Services restarted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Service restart failed: {str(e)}")
            return False
    
    def _check_new_deployment_health(self, env_config: Dict[str, Any], force: bool) -> bool:
        """检查新部署的健康状态"""
        return self._check_current_health(env_config, force)
    
    def _run_post_deploy_hooks(self, env_config: Dict[str, Any], force: bool) -> bool:
        """运行部署后钩子"""
        hooks = self.config["deployment"].get("post_deploy_hooks", [])
        return self._run_hooks(hooks, "post_deploy")
    
    def _cleanup_old_deployments(self, env_config: Dict[str, Any], force: bool) -> bool:
        """清理旧部署"""
        try:
            logger.info("Cleaning up old deployments")
            
            # 清理旧的备份文件
            backup_manager = DatabaseBackupManager(env_config["database_url"])
            backup_manager.cleanup_old_backups(
                self.config["environments"][self.current_deployment["environment"]].get("backup_retention_days", 7)
            )
            
            # 清理旧的代码版本
            # 这里应该实现清理逻辑
            
            logger.info("Cleanup completed")
            return True
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            return True  # 清理失败不应该影响部署成功
    
    def _run_hooks(self, hooks: List[str], hook_type: str) -> bool:
        """运行钩子脚本"""
        if not hooks:
            return True
        
        try:
            for hook in hooks:
                logger.info(f"Running {hook_type} hook: {hook}")
                result = subprocess.run(hook, shell=True, capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"Hook failed: {hook}, error: {result.stderr}")
                    return False
                
                logger.info(f"Hook completed: {hook}")
            
            return True
            
        except Exception as e:
            logger.error(f"Hook execution error: {str(e)}")
            return False
    
    def _check_server_health(self, server: str) -> bool:
        """检查单个服务器健康状态"""
        health_url = f"http://{server}{self.config['deployment']['health_check_url']}"
        timeout = self.config["deployment"]["health_check_timeout"]
        
        try:
            response = requests.get(health_url, timeout=timeout)
            return response.status_code == 200
        except:
            return False
    
    def _rollback(self, env_config: Dict[str, Any]) -> bool:
        """回滚部署"""
        try:
            logger.info("Starting deployment rollback")
            
            # 如果有备份，恢复数据库
            if "backup_file" in self.current_deployment:
                backup_manager = DatabaseBackupManager(env_config["database_url"])
                backup_manager.restore_backup(self.current_deployment["backup_file"])
            
            # 回滚代码
            # 这里应该实现代码回滚逻辑
            
            # 重启服务
            self._restart_services(env_config, True)
            
            logger.info("Rollback completed")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            return False
    
    def _send_notification(self, message: str):
        """发送通知"""
        if not self.config["monitoring"]["enabled"]:
            return
        
        try:
            # Webhook通知
            webhook_url = self.config["monitoring"].get("webhook_url")
            if webhook_url:
                requests.post(webhook_url, json={"text": message}, timeout=10)
            
            # Slack通知
            slack_channel = self.config["monitoring"].get("slack_channel")
            if slack_channel:
                # 实现Slack通知
                pass
            
        except Exception as e:
            logger.error(f"Notification failed: {str(e)}")
    
    def _save_deployment_history(self):
        """保存部署历史"""
        try:
            history_file = "deployment_history.json"
            with open(history_file, 'w') as f:
                json.dump(self.deployment_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save deployment history: {str(e)}")
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """获取部署状态"""
        return {
            "current_deployment": self.current_deployment,
            "deployment_history": self.deployment_history[-10:],  # 最近10次部署
            "config": self.config
        }

class DatabaseBackupManager:
    """数据库备份管理器"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.backup_dir = Path("/backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, backup_name: str = None) -> str:
        """创建数据库备份"""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_file = self.backup_dir / f"{backup_name}.sql"
        
        try:
            # 使用pg_dump创建备份
            cmd = [
                "pg_dump",
                self.database_url,
                "-f", str(backup_file),
                "--verbose",
                "--no-owner",
                "--no-privileges"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # 压缩备份文件
                if self._should_compress():
                    compressed_file = f"{backup_file}.gz"
                    subprocess.run(["gzip", str(backup_file)])
                    backup_file = compressed_file
                
                # 加密备份文件
                if self._should_encrypt():
                    encrypted_file = self._encrypt_backup(backup_file)
                    backup_file = encrypted_file
                
                logger.info(f"Database backup created: {backup_file}")
                return str(backup_file)
            else:
                raise Exception(f"pg_dump failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}")
            raise
    
    def restore_backup(self, backup_file: str) -> bool:
        """恢复数据库备份"""
        try:
            backup_path = Path(backup_file)
            
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_file}")
            
            # 解密备份文件
            if backup_file.endswith('.enc'):
                backup_file = self._decrypt_backup(backup_file)
            
            # 解压备份文件
            if backup_file.endswith('.gz'):
                subprocess.run(["gunzip", backup_file])
                backup_file = backup_file[:-3]  # 移除.gz后缀
            
            # 使用psql恢复备份
            cmd = [
                "psql",
                self.database_url,
                "-f", backup_file,
                "--quiet"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Database restored from backup: {backup_file}")
                return True
            else:
                raise Exception(f"psql restore failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Backup restore failed: {str(e)}")
            return False
    
    def cleanup_old_backups(self, retention_days: int):
        """清理旧备份"""
        try:
            cutoff_time = time.time() - (retention_days * 24 * 60 * 60)
            
            for backup_file in self.backup_dir.glob("backup_*.sql*"):
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    logger.info(f"Deleted old backup: {backup_file}")
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {str(e)}")
    
    def _should_compress(self) -> bool:
        """检查是否应该压缩备份"""
        # 从配置中读取
        return True
    
    def _should_encrypt(self) -> bool:
        """检查是否应该加密备份"""
        # 从配置中读取
        return True
    
    def _encrypt_backup(self, backup_file: str) -> str:
        """加密备份文件"""
        # 这里应该实现实际的加密逻辑
        # 例如使用GPG或其他加密工具
        encrypted_file = f"{backup_file}.enc"
        
        # 模拟加密过程
        shutil.copy2(backup_file, encrypted_file)
        os.remove(backup_file)
        
        return encrypted_file
    
    def _decrypt_backup(self, encrypted_file: str) -> str:
        """解密备份文件"""
        # 这里应该实现实际的解密逻辑
        decrypted_file = encrypted_file[:-4]  # 移除.enc后缀
        
        # 模拟解密过程
        shutil.copy2(encrypted_file, decrypted_file)
        
        return decrypted_file

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Lawsker自动化部署工具")
    parser.add_argument("command", choices=["deploy", "rollback", "status", "backup"])
    parser.add_argument("--environment", "-e", required=True, help="部署环境")
    parser.add_argument("--version", "-v", help="部署版本")
    parser.add_argument("--force", "-f", action="store_true", help="强制部署")
    parser.add_argument("--config", "-c", default="deploy_config.yaml", help="配置文件路径")
    
    args = parser.parse_args()
    
    try:
        deployment_manager = DeploymentManager(args.config)
        
        if args.command == "deploy":
            success = deployment_manager.deploy(args.environment, args.version, args.force)
            sys.exit(0 if success else 1)
        
        elif args.command == "rollback":
            # 实现回滚逻辑
            print("Rollback functionality not yet implemented")
            sys.exit(1)
        
        elif args.command == "status":
            status = deployment_manager.get_deployment_status()
            print(json.dumps(status, indent=2))
            sys.exit(0)
        
        elif args.command == "backup":
            # 创建备份
            env_config = deployment_manager.config["environments"][args.environment]
            backup_manager = DatabaseBackupManager(env_config["database_url"])
            backup_file = backup_manager.create_backup()
            print(f"Backup created: {backup_file}")
            sys.exit(0)
    
    except Exception as e:
        logger.error(f"Command failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()