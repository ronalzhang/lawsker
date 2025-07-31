"""
监控告警自动处理系统
自动响应和处理各种监控告警
"""
import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import re
from app.core.logging import get_logger
from app.services.alert_manager import AlertManager
from app.services.notification_channels import NotificationManager
from app.services.health_monitor import health_monitor

logger = get_logger(__name__)

class ActionType(Enum):
    """自动处理动作类型"""
    RESTART_SERVICE = "restart_service"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    CLEAR_CACHE = "clear_cache"
    CLEANUP_DISK = "cleanup_disk"
    KILL_PROCESS = "kill_process"
    SEND_NOTIFICATION = "send_notification"
    CREATE_TICKET = "create_ticket"
    CUSTOM_SCRIPT = "custom_script"

class ActionStatus(Enum):
    """动作执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class AutomationRule:
    """自动化规则"""
    id: str
    name: str
    description: str
    enabled: bool
    conditions: Dict[str, Any]  # 触发条件
    actions: List[Dict[str, Any]]  # 执行动作
    cooldown_minutes: int = 30  # 冷却时间（分钟）
    max_executions_per_hour: int = 5  # 每小时最大执行次数
    priority: int = 1  # 优先级（1-10，数字越大优先级越高）
    
    def matches_alert(self, alert_data: Dict[str, Any]) -> bool:
        """检查告警是否匹配规则条件"""
        try:
            for condition_key, condition_value in self.conditions.items():
                if condition_key not in alert_data:
                    return False
                
                alert_value = alert_data[condition_key]
                
                # 支持不同类型的条件匹配
                if isinstance(condition_value, dict):
                    # 复杂条件匹配
                    if not self._match_complex_condition(alert_value, condition_value):
                        return False
                elif isinstance(condition_value, str):
                    # 字符串匹配（支持正则表达式）
                    if not self._match_string_condition(str(alert_value), condition_value):
                        return False
                else:
                    # 直接匹配
                    if alert_value != condition_value:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error matching rule {self.id}: {str(e)}")
            return False
    
    def _match_complex_condition(self, alert_value: Any, condition: Dict[str, Any]) -> bool:
        """匹配复杂条件"""
        operator = condition.get("operator", "eq")
        value = condition.get("value")
        
        try:
            if operator == "eq":
                return alert_value == value
            elif operator == "ne":
                return alert_value != value
            elif operator == "gt":
                return float(alert_value) > float(value)
            elif operator == "gte":
                return float(alert_value) >= float(value)
            elif operator == "lt":
                return float(alert_value) < float(value)
            elif operator == "lte":
                return float(alert_value) <= float(value)
            elif operator == "contains":
                return str(value) in str(alert_value)
            elif operator == "regex":
                return bool(re.search(str(value), str(alert_value)))
            elif operator == "in":
                return alert_value in value
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False
                
        except (ValueError, TypeError) as e:
            logger.error(f"Error in complex condition matching: {str(e)}")
            return False
    
    def _match_string_condition(self, alert_value: str, condition: str) -> bool:
        """匹配字符串条件"""
        # 如果条件以regex:开头，使用正则表达式匹配
        if condition.startswith("regex:"):
            pattern = condition[6:]  # 移除"regex:"前缀
            return bool(re.search(pattern, alert_value))
        
        # 如果条件包含通配符，转换为正则表达式
        if "*" in condition or "?" in condition:
            pattern = condition.replace("*", ".*").replace("?", ".")
            return bool(re.match(pattern, alert_value))
        
        # 直接字符串匹配
        return alert_value == condition

@dataclass
class ActionExecution:
    """动作执行记录"""
    id: str
    rule_id: str
    action_type: ActionType
    action_config: Dict[str, Any]
    status: ActionStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['action_type'] = self.action_type.value
        result['status'] = self.status.value
        result['start_time'] = self.start_time.isoformat()
        if self.end_time:
            result['end_time'] = self.end_time.isoformat()
        return result

class AlertAutomationEngine:
    """告警自动化引擎"""
    
    def __init__(self):
        self.rules: Dict[str, AutomationRule] = {}
        self.execution_history: List[ActionExecution] = []
        self.rule_execution_count: Dict[str, List[datetime]] = {}
        self.last_execution_time: Dict[str, datetime] = {}
        self.notification_manager = NotificationManager()
        self.is_running = False
        self.processing_task = None
        
        # 初始化默认规则
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """初始化默认自动化规则"""
        default_rules = [
            # 数据库连接池告警自动处理
            AutomationRule(
                id="db_pool_high_usage",
                name="数据库连接池使用率过高",
                description="当数据库连接池使用率超过80%时自动重启连接池",
                enabled=True,
                conditions={
                    "component": "database",
                    "metrics.checked_out": {"operator": "gte", "value": 16},  # 假设池大小为20
                    "status": "warning"
                },
                actions=[
                    {
                        "type": ActionType.RESTART_SERVICE.value,
                        "config": {"service": "database_pool"}
                    },
                    {
                        "type": ActionType.SEND_NOTIFICATION.value,
                        "config": {
                            "channel": "ops",
                            "message": "数据库连接池已自动重启",
                            "priority": "medium"
                        }
                    }
                ],
                cooldown_minutes=15,
                max_executions_per_hour=3,
                priority=8
            ),
            
            # 内存使用率过高自动处理
            AutomationRule(
                id="high_memory_usage",
                name="内存使用率过高",
                description="当内存使用率超过90%时自动清理缓存",
                enabled=True,
                conditions={
                    "component": "system_resources",
                    "metrics.memory_percent": {"operator": "gt", "value": 90},
                    "status": "warning"
                },
                actions=[
                    {
                        "type": ActionType.CLEAR_CACHE.value,
                        "config": {"cache_types": ["redis", "application"]}
                    },
                    {
                        "type": ActionType.CUSTOM_SCRIPT.value,
                        "config": {
                            "script": "python -c \"import gc; gc.collect()\"",
                            "description": "强制垃圾回收"
                        }
                    },
                    {
                        "type": ActionType.SEND_NOTIFICATION.value,
                        "config": {
                            "channel": "ops",
                            "message": "系统内存使用率过高，已执行自动清理",
                            "priority": "high"
                        }
                    }
                ],
                cooldown_minutes=10,
                max_executions_per_hour=6,
                priority=9
            ),
            
            # 磁盘空间不足自动处理
            AutomationRule(
                id="disk_space_low",
                name="磁盘空间不足",
                description="当磁盘使用率超过85%时自动清理临时文件",
                enabled=True,
                conditions={
                    "component": "system_resources",
                    "metrics.disk_percent": {"operator": "gt", "value": 85},
                    "status": "warning"
                },
                actions=[
                    {
                        "type": ActionType.CLEANUP_DISK.value,
                        "config": {
                            "paths": ["/tmp", "/var/log", "/var/cache"],
                            "max_age_days": 7
                        }
                    },
                    {
                        "type": ActionType.SEND_NOTIFICATION.value,
                        "config": {
                            "channel": "ops",
                            "message": "磁盘空间不足，已执行自动清理",
                            "priority": "high"
                        }
                    }
                ],
                cooldown_minutes=30,
                max_executions_per_hour=2,
                priority=7
            ),
            
            # Redis连接数过多自动处理
            AutomationRule(
                id="redis_high_connections",
                name="Redis连接数过多",
                description="当Redis连接数超过100时发送告警",
                enabled=True,
                conditions={
                    "component": "redis",
                    "metrics.connected_clients": {"operator": "gt", "value": 100},
                    "status": "warning"
                },
                actions=[
                    {
                        "type": ActionType.SEND_NOTIFICATION.value,
                        "config": {
                            "channel": "ops",
                            "message": "Redis连接数异常，当前连接数: {metrics.connected_clients}",
                            "priority": "medium"
                        }
                    },
                    {
                        "type": ActionType.CREATE_TICKET.value,
                        "config": {
                            "title": "Redis连接数异常",
                            "description": "需要检查Redis连接泄漏问题",
                            "priority": "medium"
                        }
                    }
                ],
                cooldown_minutes=60,
                max_executions_per_hour=1,
                priority=5
            ),
            
            # 应用程序响应时间过长自动处理
            AutomationRule(
                id="app_slow_response",
                name="应用程序响应缓慢",
                description="当应用程序响应时间超过3秒时重启应用",
                enabled=True,
                conditions={
                    "component": "application",
                    "metrics.response_time": {"operator": "gt", "value": 3000},  # 毫秒
                    "status": "warning"
                },
                actions=[
                    {
                        "type": ActionType.RESTART_SERVICE.value,
                        "config": {"service": "application"}
                    },
                    {
                        "type": ActionType.SEND_NOTIFICATION.value,
                        "config": {
                            "channel": "ops",
                            "message": "应用程序响应缓慢，已自动重启",
                            "priority": "high"
                        }
                    }
                ],
                cooldown_minutes=20,
                max_executions_per_hour=3,
                priority=8
            )
        ]
        
        for rule in default_rules:
            self.rules[rule.id] = rule
    
    async def start_processing(self):
        """开始处理告警"""
        if self.is_running:
            logger.warning("Alert automation is already running")
            return
        
        self.is_running = True
        self.processing_task = asyncio.create_task(self._processing_loop())
        logger.info("Alert automation engine started")
    
    async def stop_processing(self):
        """停止处理告警"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Alert automation engine stopped")
    
    async def _processing_loop(self):
        """处理循环"""
        alert_manager = AlertManager()
        
        while self.is_running:
            try:
                # 获取未处理的告警
                alerts = await alert_manager.get_unprocessed_alerts()
                
                for alert in alerts:
                    await self._process_alert(alert)
                
                # 等待下次处理
                await asyncio.sleep(10)  # 10秒检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Alert processing loop error: {str(e)}")
                await asyncio.sleep(30)  # 出错时等待更长时间
    
    async def _process_alert(self, alert_data: Dict[str, Any]):
        """处理单个告警"""
        try:
            # 查找匹配的规则
            matching_rules = []
            
            for rule in self.rules.values():
                if not rule.enabled:
                    continue
                
                if rule.matches_alert(alert_data):
                    matching_rules.append(rule)
            
            if not matching_rules:
                logger.debug(f"No matching rules for alert: {alert_data.get('id', 'unknown')}")
                return
            
            # 按优先级排序
            matching_rules.sort(key=lambda r: r.priority, reverse=True)
            
            # 执行匹配的规则
            for rule in matching_rules:
                if await self._can_execute_rule(rule):
                    await self._execute_rule(rule, alert_data)
                else:
                    logger.info(f"Rule {rule.id} skipped due to cooldown or rate limit")
        
        except Exception as e:
            logger.error(f"Error processing alert: {str(e)}")
    
    async def _can_execute_rule(self, rule: AutomationRule) -> bool:
        """检查规则是否可以执行"""
        now = datetime.now()
        
        # 检查冷却时间
        if rule.id in self.last_execution_time:
            last_time = self.last_execution_time[rule.id]
            cooldown_end = last_time + timedelta(minutes=rule.cooldown_minutes)
            
            if now < cooldown_end:
                return False
        
        # 检查每小时执行次数限制
        if rule.id in self.rule_execution_count:
            hour_ago = now - timedelta(hours=1)
            recent_executions = [
                exec_time for exec_time in self.rule_execution_count[rule.id]
                if exec_time > hour_ago
            ]
            
            if len(recent_executions) >= rule.max_executions_per_hour:
                return False
        
        return True
    
    async def _execute_rule(self, rule: AutomationRule, alert_data: Dict[str, Any]):
        """执行规则"""
        logger.info(f"Executing rule: {rule.name}")
        
        # 记录执行时间
        now = datetime.now()
        self.last_execution_time[rule.id] = now
        
        if rule.id not in self.rule_execution_count:
            self.rule_execution_count[rule.id] = []
        self.rule_execution_count[rule.id].append(now)
        
        # 执行所有动作
        for action_config in rule.actions:
            await self._execute_action(rule.id, action_config, alert_data)
    
    async def _execute_action(self, rule_id: str, action_config: Dict[str, Any], alert_data: Dict[str, Any]):
        """执行单个动作"""
        action_type = ActionType(action_config["type"])
        config = action_config.get("config", {})
        
        execution = ActionExecution(
            id=f"exec_{int(time.time() * 1000)}",
            rule_id=rule_id,
            action_type=action_type,
            action_config=config,
            status=ActionStatus.PENDING,
            start_time=datetime.now()
        )
        
        try:
            execution.status = ActionStatus.RUNNING
            logger.info(f"Executing action: {action_type.value}")
            
            # 根据动作类型执行相应操作
            if action_type == ActionType.RESTART_SERVICE:
                result = await self._restart_service(config, alert_data)
            elif action_type == ActionType.CLEAR_CACHE:
                result = await self._clear_cache(config, alert_data)
            elif action_type == ActionType.CLEANUP_DISK:
                result = await self._cleanup_disk(config, alert_data)
            elif action_type == ActionType.SEND_NOTIFICATION:
                result = await self._send_notification(config, alert_data)
            elif action_type == ActionType.CREATE_TICKET:
                result = await self._create_ticket(config, alert_data)
            elif action_type == ActionType.CUSTOM_SCRIPT:
                result = await self._execute_custom_script(config, alert_data)
            else:
                raise ValueError(f"Unsupported action type: {action_type}")
            
            execution.status = ActionStatus.SUCCESS
            execution.result = result
            logger.info(f"Action {action_type.value} completed successfully")
            
        except Exception as e:
            execution.status = ActionStatus.FAILED
            execution.error = str(e)
            logger.error(f"Action {action_type.value} failed: {str(e)}")
        
        finally:
            execution.end_time = datetime.now()
            self.execution_history.append(execution)
            
            # 保持历史记录在合理范围内
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-500:]
    
    # 动作执行方法
    async def _restart_service(self, config: Dict[str, Any], alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """重启服务"""
        service = config.get("service")
        
        if service == "database_pool":
            # 重启数据库连接池
            from app.core.database import engine
            engine.dispose()
            return {"message": "Database connection pool restarted"}
        
        elif service == "application":
            # 重启应用程序（这里只是示例，实际需要根据部署方式实现）
            import subprocess
            result = subprocess.run(["systemctl", "restart", "lawsker-backend"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                return {"message": "Application service restarted"}
            else:
                raise Exception(f"Failed to restart service: {result.stderr}")
        
        else:
            raise ValueError(f"Unknown service: {service}")
    
    async def _clear_cache(self, config: Dict[str, Any], alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """清理缓存"""
        cache_types = config.get("cache_types", ["redis"])
        cleared = []
        
        for cache_type in cache_types:
            if cache_type == "redis":
                # 清理Redis缓存
                import redis
                redis_client = redis.from_url("redis://localhost:6379/0")
                redis_client.flushdb()
                cleared.append("redis")
            
            elif cache_type == "application":
                # 清理应用程序缓存
                from app.core.performance import api_cache
                await api_cache.clear()
                cleared.append("application")
        
        return {"message": f"Cleared caches: {', '.join(cleared)}"}
    
    async def _cleanup_disk(self, config: Dict[str, Any], alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """清理磁盘空间"""
        paths = config.get("paths", ["/tmp"])
        max_age_days = config.get("max_age_days", 7)
        
        import os
        import time
        
        cleaned_files = 0
        freed_space = 0
        
        for path in paths:
            if not os.path.exists(path):
                continue
            
            cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
            
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if os.path.getmtime(file_path) < cutoff_time:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            cleaned_files += 1
                            freed_space += file_size
                    except (OSError, IOError):
                        continue
        
        return {
            "message": f"Cleaned {cleaned_files} files, freed {freed_space} bytes",
            "cleaned_files": cleaned_files,
            "freed_space": freed_space
        }
    
    async def _send_notification(self, config: Dict[str, Any], alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """发送通知"""
        channel = config.get("channel", "ops")
        message_template = config.get("message", "Alert: {alert_message}")
        priority = config.get("priority", "medium")
        
        # 格式化消息（支持模板变量）
        message = message_template.format(
            alert_message=alert_data.get("message", "Unknown alert"),
            component=alert_data.get("component", "unknown"),
            **alert_data.get("metrics", {})
        )
        
        await self.notification_manager.send_notification(
            channel=channel,
            message=message,
            priority=priority
        )
        
        return {"message": f"Notification sent to {channel}"}
    
    async def _create_ticket(self, config: Dict[str, Any], alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建工单"""
        title = config.get("title", "Alert Ticket")
        description = config.get("description", "Automated ticket from alert")
        priority = config.get("priority", "medium")
        
        # 这里应该集成实际的工单系统
        # 例如Jira、ServiceNow等
        
        ticket_data = {
            "title": title,
            "description": description,
            "priority": priority,
            "alert_data": alert_data,
            "created_at": datetime.now().isoformat()
        }
        
        # 模拟创建工单
        logger.info(f"Created ticket: {title}")
        
        return {"message": f"Ticket created: {title}", "ticket_data": ticket_data}
    
    async def _execute_custom_script(self, config: Dict[str, Any], alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行自定义脚本"""
        script = config.get("script")
        description = config.get("description", "Custom script")
        
        if not script:
            raise ValueError("Script not specified")
        
        import subprocess
        
        result = subprocess.run(
            script,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60  # 60秒超时
        )
        
        if result.returncode == 0:
            return {
                "message": f"Script executed successfully: {description}",
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        else:
            raise Exception(f"Script failed: {result.stderr}")
    
    def add_rule(self, rule: AutomationRule):
        """添加自动化规则"""
        self.rules[rule.id] = rule
        logger.info(f"Added automation rule: {rule.name}")
    
    def remove_rule(self, rule_id: str):
        """移除自动化规则"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed automation rule: {rule_id}")
    
    def get_rule(self, rule_id: str) -> Optional[AutomationRule]:
        """获取规则"""
        return self.rules.get(rule_id)
    
    def list_rules(self) -> List[AutomationRule]:
        """列出所有规则"""
        return list(self.rules.values())
    
    def get_execution_history(self, rule_id: str = None, limit: int = 100) -> List[ActionExecution]:
        """获取执行历史"""
        history = self.execution_history
        
        if rule_id:
            history = [exec for exec in history if exec.rule_id == rule_id]
        
        return history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_executions = len(self.execution_history)
        successful_executions = len([exec for exec in self.execution_history if exec.status == ActionStatus.SUCCESS])
        failed_executions = len([exec for exec in self.execution_history if exec.status == ActionStatus.FAILED])
        
        # 按规则统计
        rule_stats = {}
        for execution in self.execution_history:
            rule_id = execution.rule_id
            if rule_id not in rule_stats:
                rule_stats[rule_id] = {"total": 0, "success": 0, "failed": 0}
            
            rule_stats[rule_id]["total"] += 1
            if execution.status == ActionStatus.SUCCESS:
                rule_stats[rule_id]["success"] += 1
            elif execution.status == ActionStatus.FAILED:
                rule_stats[rule_id]["failed"] += 1
        
        # 按动作类型统计
        action_stats = {}
        for execution in self.execution_history:
            action_type = execution.action_type.value
            if action_type not in action_stats:
                action_stats[action_type] = {"total": 0, "success": 0, "failed": 0}
            
            action_stats[action_type]["total"] += 1
            if execution.status == ActionStatus.SUCCESS:
                action_stats[action_type]["success"] += 1
            elif execution.status == ActionStatus.FAILED:
                action_stats[action_type]["failed"] += 1
        
        return {
            "total_rules": len(self.rules),
            "enabled_rules": len([rule for rule in self.rules.values() if rule.enabled]),
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate": (successful_executions / total_executions * 100) if total_executions > 0 else 0,
            "rule_statistics": rule_stats,
            "action_statistics": action_stats,
            "is_running": self.is_running
        }

# 全局告警自动化引擎实例
alert_automation = AlertAutomationEngine()