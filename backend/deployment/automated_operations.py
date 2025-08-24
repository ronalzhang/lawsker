#!/usr/bin/env python3
"""
自动化运维脚本
集成系统监控和故障诊断功能，提供自动化运维能力
"""

import os
import sys
import json
import time
import logging
import schedule
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

# 导入自定义模块
from system_monitor import SystemMonitor
from fault_diagnosis import FaultDiagnosisEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class OperationTask:
    """运维任务数据结构"""
    task_id: str
    name: str
    description: str
    schedule: str  # cron格式或简单描述
    enabled: bool
    last_run: Optional[str]
    next_run: Optional[str]
    success_count: int
    failure_count: int

@dataclass
class MaintenanceWindow:
    """维护窗口数据结构"""
    name: str
    start_time: str  # HH:MM格式
    end_time: str    # HH:MM格式
    days: List[str]  # ['monday', 'tuesday', ...]
    timezone: str
    enabled: bool

class AutomatedOperations:
    """自动化运维管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "operations_config.json"
        self.config = self._load_config()
        self.monitor = SystemMonitor()
        self.diagnosis_engine = FaultDiagnosisEngine()
        self.running = False
        self.scheduler_thread = None
        self.tasks = self._load_tasks()
        self.maintenance_windows = self._load_maintenance_windows()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载运维配置"""
        default_config = {
            "monitoring": {
                "enabled": True,
                "interval_minutes": 5,
                "alert_threshold": {
                    "cpu_percent": 80,
                    "memory_percent": 85,
                    "disk_percent": 90
                }
            },
            "diagnosis": {
                "enabled": True,
                "auto_fix": True,
                "schedule": "0 */6 * * *"  # 每6小时执行一次
            },
            "maintenance": {
                "auto_cleanup": True,
                "log_retention_days": 30,
                "backup_retention_days": 7,
                "cleanup_schedule": "0 2 * * 0"  # 每周日凌晨2点
            },
            "notifications": {
                "email": {
                    "enabled": False,
                    "smtp_server": "localhost",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "from_address": "ops@lawsker.com",
                    "to_addresses": ["admin@lawsker.com"]
                },
                "webhook": {
                    "enabled": False,
                    "url": "",
                    "timeout": 10
                }
            },
            "auto_recovery": {
                "enabled": True,
                "max_attempts": 3,
                "retry_interval_minutes": 5,
                "services": ["nginx", "postgresql", "redis"]
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                        elif isinstance(value, dict) and isinstance(config[key], dict):
                            for sub_key, sub_value in value.items():
                                if sub_key not in config[key]:
                                    config[key][sub_key] = sub_value
                    return config
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                return default_config
        else:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    
    def _load_tasks(self) -> List[OperationTask]:
        """加载运维任务"""
        default_tasks = [
            OperationTask(
                task_id="system_monitoring",
                name="系统监控",
                description="定期收集系统指标和服务状态",
                schedule="*/5 * * * *",  # 每5分钟
                enabled=True,
                last_run=None,
                next_run=None,
                success_count=0,
                failure_count=0
            ),
            OperationTask(
                task_id="fault_diagnosis",
                name="故障诊断",
                description="定期执行系统故障诊断",
                schedule="0 */6 * * *",  # 每6小时
                enabled=True,
                last_run=None,
                next_run=None,
                success_count=0,
                failure_count=0
            ),
            OperationTask(
                task_id="log_cleanup",
                name="日志清理",
                description="清理过期日志文件",
                schedule="0 2 * * 0",  # 每周日凌晨2点
                enabled=True,
                last_run=None,
                next_run=None,
                success_count=0,
                failure_count=0
            ),
            OperationTask(
                task_id="backup_cleanup",
                name="备份清理",
                description="清理过期备份文件",
                schedule="0 3 * * 0",  # 每周日凌晨3点
                enabled=True,
                last_run=None,
                next_run=None,
                success_count=0,
                failure_count=0
            ),
            OperationTask(
                task_id="health_check",
                name="健康检查",
                description="执行系统健康检查",
                schedule="*/10 * * * *",  # 每10分钟
                enabled=True,
                last_run=None,
                next_run=None,
                success_count=0,
                failure_count=0
            )
        ]
        
        tasks_file = "operation_tasks.json"
        if os.path.exists(tasks_file):
            try:
                with open(tasks_file, 'r', encoding='utf-8') as f:
                    tasks_data = json.load(f)
                    return [OperationTask(**task) for task in tasks_data]
            except Exception as e:
                logger.error(f"加载任务文件失败: {e}")
                return default_tasks
        else:
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(task) for task in default_tasks], f, indent=2, ensure_ascii=False)
            return default_tasks
    
    def _load_maintenance_windows(self) -> List[MaintenanceWindow]:
        """加载维护窗口"""
        default_windows = [
            MaintenanceWindow(
                name="周末维护窗口",
                start_time="02:00",
                end_time="06:00",
                days=["saturday", "sunday"],
                timezone="Asia/Shanghai",
                enabled=True
            ),
            MaintenanceWindow(
                name="工作日深夜维护",
                start_time="03:00",
                end_time="05:00",
                days=["monday", "tuesday", "wednesday", "thursday", "friday"],
                timezone="Asia/Shanghai",
                enabled=False
            )
        ]
        
        windows_file = "maintenance_windows.json"
        if os.path.exists(windows_file):
            try:
                with open(windows_file, 'r', encoding='utf-8') as f:
                    windows_data = json.load(f)
                    return [MaintenanceWindow(**window) for window in windows_data]
            except Exception as e:
                logger.error(f"加载维护窗口失败: {e}")
                return default_windows
        else:
            with open(windows_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(window) for window in default_windows], f, indent=2, ensure_ascii=False)
            return default_windows
    
    def is_maintenance_window(self) -> bool:
        """检查当前是否在维护窗口内"""
        now = datetime.now()
        current_day = now.strftime("%A").lower()
        current_time = now.strftime("%H:%M")
        
        for window in self.maintenance_windows:
            if not window.enabled:
                continue
                
            if current_day in [day.lower() for day in window.days]:
                if window.start_time <= current_time <= window.end_time:
                    return True
        
        return False
    
    def execute_monitoring_task(self) -> bool:
        """执行监控任务"""
        try:
            logger.info("开始执行系统监控任务")
            
            # 生成监控报告
            report = self.monitor.generate_report()
            
            # 检查告警条件
            alerts = []
            metrics = report.get("system_metrics", {})
            
            # CPU告警
            cpu_threshold = self.config["monitoring"]["alert_threshold"]["cpu_percent"]
            if metrics.get("cpu_percent", 0) > cpu_threshold:
                alerts.append(f"CPU使用率过高: {metrics['cpu_percent']:.1f}%")
            
            # 内存告警
            memory_threshold = self.config["monitoring"]["alert_threshold"]["memory_percent"]
            if metrics.get("memory_percent", 0) > memory_threshold:
                alerts.append(f"内存使用率过高: {metrics['memory_percent']:.1f}%")
            
            # 磁盘告警
            disk_threshold = self.config["monitoring"]["alert_threshold"]["disk_percent"]
            disk_usage = metrics.get("disk_usage", {})
            for path, usage in disk_usage.items():
                if usage > disk_threshold:
                    alerts.append(f"磁盘使用率过高 {path}: {usage:.1f}%")
            
            # 服务状态告警
            services = report.get("services", [])
            for service in services:
                if service.get("status") != "running":
                    alerts.append(f"服务异常: {service.get('name')} - {service.get('status')}")
            
            # 发送告警
            if alerts:
                self._send_alerts(alerts, "系统监控告警")
            
            # 保存监控报告
            self._save_monitoring_report(report)
            
            logger.info(f"系统监控任务完成，发现 {len(alerts)} 个告警")
            return True
            
        except Exception as e:
            logger.error(f"执行监控任务失败: {e}")
            return False
    
    def execute_diagnosis_task(self) -> bool:
        """执行诊断任务"""
        try:
            logger.info("开始执行故障诊断任务")
            
            # 生成诊断报告
            report = self.diagnosis_engine.generate_diagnosis_report()
            
            # 处理诊断结果
            diagnosis_results = report.get("diagnosis_results", [])
            critical_issues = [r for r in diagnosis_results if r.get("severity") == "critical"]
            
            # 自动修复（如果启用）
            fixed_issues = []
            if self.config["diagnosis"]["auto_fix"]:
                for issue in critical_issues:
                    if issue.get("auto_fix_available"):
                        issue_id = issue.get("issue_id")
                        if self.diagnosis_engine.auto_fix_issue(issue_id):
                            fixed_issues.append(issue)
                            logger.info(f"自动修复成功: {issue.get('title')}")
            
            # 发送诊断报告
            if critical_issues:
                alert_message = f"发现 {len(critical_issues)} 个关键问题"
                if fixed_issues:
                    alert_message += f"，已自动修复 {len(fixed_issues)} 个"
                self._send_alerts([alert_message], "故障诊断报告")
            
            # 保存诊断报告
            self._save_diagnosis_report(report)
            
            logger.info(f"故障诊断任务完成，发现 {len(critical_issues)} 个关键问题，修复 {len(fixed_issues)} 个")
            return True
            
        except Exception as e:
            logger.error(f"执行诊断任务失败: {e}")
            return False
    
    def execute_cleanup_task(self, task_type: str) -> bool:
        """执行清理任务"""
        try:
            logger.info(f"开始执行清理任务: {task_type}")
            
            if task_type == "log_cleanup":
                return self._cleanup_logs()
            elif task_type == "backup_cleanup":
                return self._cleanup_backups()
            else:
                logger.warning(f"未知的清理任务类型: {task_type}")
                return False
                
        except Exception as e:
            logger.error(f"执行清理任务失败 {task_type}: {e}")
            return False
    
    def _cleanup_logs(self) -> bool:
        """清理日志文件"""
        try:
            retention_days = self.config["maintenance"]["log_retention_days"]
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            log_dirs = ["/var/log", "/var/log/nginx", "/var/log/postgresql"]
            cleaned_files = 0
            
            for log_dir in log_dirs:
                if not os.path.exists(log_dir):
                    continue
                
                for root, dirs, files in os.walk(log_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            # 检查文件修改时间
                            mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                            if mtime < cutoff_date and file.endswith(('.log', '.log.gz')):
                                os.remove(file_path)
                                cleaned_files += 1
                                logger.debug(f"删除过期日志: {file_path}")
                        except Exception as e:
                            logger.warning(f"删除日志文件失败 {file_path}: {e}")
            
            logger.info(f"日志清理完成，删除 {cleaned_files} 个文件")
            return True
            
        except Exception as e:
            logger.error(f"日志清理失败: {e}")
            return False
    
    def _cleanup_backups(self) -> bool:
        """清理备份文件"""
        try:
            retention_days = self.config["maintenance"]["backup_retention_days"]
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            backup_dirs = ["/var/backups", "/opt/lawsker/backups"]
            cleaned_files = 0
            
            for backup_dir in backup_dirs:
                if not os.path.exists(backup_dir):
                    continue
                
                for root, dirs, files in os.walk(backup_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            # 检查文件修改时间
                            mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                            if mtime < cutoff_date:
                                os.remove(file_path)
                                cleaned_files += 1
                                logger.debug(f"删除过期备份: {file_path}")
                        except Exception as e:
                            logger.warning(f"删除备份文件失败 {file_path}: {e}")
            
            logger.info(f"备份清理完成，删除 {cleaned_files} 个文件")
            return True
            
        except Exception as e:
            logger.error(f"备份清理失败: {e}")
            return False
    
    def execute_health_check(self) -> bool:
        """执行健康检查"""
        try:
            logger.info("开始执行健康检查")
            
            # 检查关键服务
            services = self.config["auto_recovery"]["services"]
            unhealthy_services = []
            
            for service in services:
                if not self._check_service_health(service):
                    unhealthy_services.append(service)
            
            # 自动恢复（如果启用）
            recovered_services = []
            if self.config["auto_recovery"]["enabled"] and unhealthy_services:
                for service in unhealthy_services:
                    if self._recover_service(service):
                        recovered_services.append(service)
            
            # 记录结果
            if unhealthy_services:
                message = f"发现 {len(unhealthy_services)} 个不健康服务"
                if recovered_services:
                    message += f"，已恢复 {len(recovered_services)} 个"
                logger.warning(message)
                
                # 发送告警
                if len(unhealthy_services) > len(recovered_services):
                    self._send_alerts([message], "服务健康检查")
            
            logger.info(f"健康检查完成，检查 {len(services)} 个服务，发现 {len(unhealthy_services)} 个问题，恢复 {len(recovered_services)} 个")
            return True
            
        except Exception as e:
            logger.error(f"执行健康检查失败: {e}")
            return False
    
    def _check_service_health(self, service_name: str) -> bool:
        """检查服务健康状态"""
        try:
            import subprocess
            
            # 检查systemd服务状态
            result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.returncode == 0 and result.stdout.strip() == "active"
            
        except Exception as e:
            logger.warning(f"检查服务健康状态失败 {service_name}: {e}")
            return False
    
    def _recover_service(self, service_name: str) -> bool:
        """恢复服务"""
        try:
            import subprocess
            
            max_attempts = self.config["auto_recovery"]["max_attempts"]
            retry_interval = self.config["auto_recovery"]["retry_interval_minutes"] * 60
            
            for attempt in range(max_attempts):
                logger.info(f"尝试恢复服务 {service_name} (第 {attempt + 1} 次)")
                
                # 重启服务
                result = subprocess.run(
                    ["systemctl", "restart", service_name],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    # 等待服务启动
                    time.sleep(10)
                    
                    # 检查服务状态
                    if self._check_service_health(service_name):
                        logger.info(f"服务恢复成功: {service_name}")
                        return True
                
                if attempt < max_attempts - 1:
                    time.sleep(retry_interval)
            
            logger.error(f"服务恢复失败: {service_name}")
            return False
            
        except Exception as e:
            logger.error(f"恢复服务失败 {service_name}: {e}")
            return False
    
    def _send_alerts(self, alerts: List[str], subject: str):
        """发送告警"""
        try:
            # 邮件告警
            if self.config["notifications"]["email"]["enabled"]:
                self._send_email_alert(alerts, subject)
            
            # Webhook告警
            if self.config["notifications"]["webhook"]["enabled"]:
                self._send_webhook_alert(alerts, subject)
            
        except Exception as e:
            logger.error(f"发送告警失败: {e}")
    
    def _send_email_alert(self, alerts: List[str], subject: str):
        """发送邮件告警"""
        try:
            email_config = self.config["notifications"]["email"]
            
            msg = MimeMultipart()
            msg['From'] = email_config["from_address"]
            msg['To'] = ", ".join(email_config["to_addresses"])
            msg['Subject'] = f"[Lawsker运维] {subject}"
            
            body = f"""
系统时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

告警信息:
{chr(10).join(f"- {alert}" for alert in alerts)}

请及时处理相关问题。

---
Lawsker自动化运维系统
            """.strip()
            
            msg.attach(MimeText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
            if email_config.get("username") and email_config.get("password"):
                server.starttls()
                server.login(email_config["username"], email_config["password"])
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"邮件告警发送成功: {subject}")
            
        except Exception as e:
            logger.error(f"发送邮件告警失败: {e}")
    
    def _send_webhook_alert(self, alerts: List[str], subject: str):
        """发送Webhook告警"""
        try:
            import requests
            
            webhook_config = self.config["notifications"]["webhook"]
            
            payload = {
                "timestamp": datetime.now().isoformat(),
                "subject": subject,
                "alerts": alerts,
                "hostname": os.uname().nodename,
                "source": "lawsker-ops"
            }
            
            response = requests.post(
                webhook_config["url"],
                json=payload,
                timeout=webhook_config.get("timeout", 10)
            )
            
            if response.status_code == 200:
                logger.info(f"Webhook告警发送成功: {subject}")
            else:
                logger.error(f"Webhook告警发送失败: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"发送Webhook告警失败: {e}")
    
    def _save_monitoring_report(self, report: Dict[str, Any]):
        """保存监控报告"""
        try:
            reports_dir = "monitoring_reports"
            os.makedirs(reports_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join(reports_dir, f"monitoring_{timestamp}.json")
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"保存监控报告失败: {e}")
    
    def _save_diagnosis_report(self, report: Dict[str, Any]):
        """保存诊断报告"""
        try:
            reports_dir = "diagnosis_reports"
            os.makedirs(reports_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join(reports_dir, f"diagnosis_{timestamp}.json")
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"保存诊断报告失败: {e}")
    
    def execute_task(self, task_id: str) -> bool:
        """执行指定任务"""
        try:
            task = next((t for t in self.tasks if t.task_id == task_id), None)
            if not task:
                logger.error(f"任务不存在: {task_id}")
                return False
            
            if not task.enabled:
                logger.info(f"任务已禁用: {task_id}")
                return False
            
            logger.info(f"开始执行任务: {task.name}")
            start_time = datetime.now()
            
            # 执行任务
            success = False
            if task_id == "system_monitoring":
                success = self.execute_monitoring_task()
            elif task_id == "fault_diagnosis":
                success = self.execute_diagnosis_task()
            elif task_id == "log_cleanup":
                success = self.execute_cleanup_task("log_cleanup")
            elif task_id == "backup_cleanup":
                success = self.execute_cleanup_task("backup_cleanup")
            elif task_id == "health_check":
                success = self.execute_health_check()
            else:
                logger.error(f"未知的任务类型: {task_id}")
                return False
            
            # 更新任务状态
            task.last_run = start_time.isoformat()
            if success:
                task.success_count += 1
            else:
                task.failure_count += 1
            
            # 保存任务状态
            self._save_tasks()
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"任务执行完成: {task.name} ({'成功' if success else '失败'}) - 耗时 {duration:.2f}s")
            
            return success
            
        except Exception as e:
            logger.error(f"执行任务失败 {task_id}: {e}")
            return False
    
    def _save_tasks(self):
        """保存任务状态"""
        try:
            tasks_file = "operation_tasks.json"
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(task) for task in self.tasks], f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存任务状态失败: {e}")
    
    def setup_scheduler(self):
        """设置任务调度器"""
        try:
            # 清除现有调度
            schedule.clear()
            
            # 设置任务调度
            for task in self.tasks:
                if not task.enabled:
                    continue
                
                # 简化的调度设置（实际应该解析cron表达式）
                if task.task_id == "system_monitoring":
                    schedule.every(5).minutes.do(self.execute_task, task.task_id)
                elif task.task_id == "fault_diagnosis":
                    schedule.every(6).hours.do(self.execute_task, task.task_id)
                elif task.task_id == "log_cleanup":
                    schedule.every().sunday.at("02:00").do(self.execute_task, task.task_id)
                elif task.task_id == "backup_cleanup":
                    schedule.every().sunday.at("03:00").do(self.execute_task, task.task_id)
                elif task.task_id == "health_check":
                    schedule.every(10).minutes.do(self.execute_task, task.task_id)
            
            logger.info(f"任务调度器设置完成，共 {len([t for t in self.tasks if t.enabled])} 个任务")
            
        except Exception as e:
            logger.error(f"设置任务调度器失败: {e}")
    
    def start_scheduler(self):
        """启动调度器"""
        if self.running:
            logger.warning("调度器已在运行中")
            return
        
        self.running = True
        self.setup_scheduler()
        
        def scheduler_loop():
            while self.running:
                try:
                    schedule.run_pending()
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"调度器循环异常: {e}")
                    time.sleep(5)
        
        self.scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("自动化运维调度器已启动")
    
    def stop_scheduler(self):
        """停止调度器"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("自动化运维调度器已停止")
    
    def get_status(self) -> Dict[str, Any]:
        """获取运维状态"""
        try:
            return {
                "timestamp": datetime.now().isoformat(),
                "scheduler_running": self.running,
                "maintenance_window": self.is_maintenance_window(),
                "tasks": [asdict(task) for task in self.tasks],
                "maintenance_windows": [asdict(window) for window in self.maintenance_windows],
                "config": self.config
            }
        except Exception as e:
            logger.error(f"获取运维状态失败: {e}")
            return {"error": str(e)}


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="自动化运维工具")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--daemon", action="store_true", help="后台运行")
    parser.add_argument("--task", help="执行指定任务")
    parser.add_argument("--status", action="store_true", help="显示运维状态")
    parser.add_argument("--output", help="输出文件")
    
    args = parser.parse_args()
    
    try:
        ops = AutomatedOperations(args.config)
        
        if args.status:
            # 显示状态
            status = ops.get_status()
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(status, f, indent=2, ensure_ascii=False)
                print(f"状态信息已保存到: {args.output}")
            else:
                print(json.dumps(status, indent=2, ensure_ascii=False))
        
        elif args.task:
            # 执行指定任务
            success = ops.execute_task(args.task)
            print(f"任务执行 {'成功' if success else '失败'}: {args.task}")
        
        elif args.daemon:
            # 后台运行
            ops.start_scheduler()
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                ops.stop_scheduler()
        
        else:
            # 显示帮助
            parser.print_help()
    
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()