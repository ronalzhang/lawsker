#!/usr/bin/env python3
"""
系统监控工具
实现系统资源监控、服务状态检查、性能指标收集和异常检测功能
"""

import os
import sys
import time
import json
import psutil
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import requests
import socket
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """系统指标数据结构"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_available: int
    disk_usage: Dict[str, float]
    network_io: Dict[str, int]
    load_average: Tuple[float, float, float]
    process_count: int
    uptime: float

@dataclass
class ServiceStatus:
    """服务状态数据结构"""
    name: str
    status: str
    pid: Optional[int]
    cpu_percent: float
    memory_percent: float
    port: Optional[int]
    is_listening: bool
    response_time: Optional[float]

@dataclass
class AlertRule:
    """告警规则数据结构"""
    name: str
    metric: str
    threshold: float
    operator: str  # '>', '<', '>=', '<=', '=='
    duration: int  # 持续时间（秒）
    severity: str  # 'critical', 'warning', 'info'
    enabled: bool = True

class SystemMonitor:
    """系统监控类"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "monitoring_config.json"
        self.config = self._load_config()
        self.alert_rules = self._load_alert_rules()
        self.metrics_history = []
        self.alert_history = []
        self.running = False
        self.monitor_thread = None
        
    def _load_config(self) -> Dict[str, Any]:
        """加载监控配置"""
        default_config = {
            "monitoring_interval": 30,
            "metrics_retention_hours": 24,
            "services": [
                {
                    "name": "nginx",
                    "process_name": "nginx",
                    "port": 80,
                    "health_check_url": "http://localhost/health"
                },
                {
                    "name": "postgresql",
                    "process_name": "postgres",
                    "port": 5432
                },
                {
                    "name": "redis",
                    "process_name": "redis-server",
                    "port": 6379
                },
                {
                    "name": "lawsker-backend",
                    "process_name": "python",
                    "port": 8000,
                    "health_check_url": "http://localhost:8000/health"
                }
            ],
            "disk_paths": ["/", "/var", "/tmp"],
            "network_interfaces": ["eth0", "lo"],
            "log_file": "/var/log/system_monitor.log",
            "metrics_file": "/var/log/system_metrics.json",
            "alert_webhook": None
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                return default_config
        else:
            # 创建默认配置文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    
    def _load_alert_rules(self) -> List[AlertRule]:
        """加载告警规则"""
        default_rules = [
            AlertRule("高CPU使用率", "cpu_percent", 80.0, ">=", 300, "warning"),
            AlertRule("极高CPU使用率", "cpu_percent", 95.0, ">=", 60, "critical"),
            AlertRule("高内存使用率", "memory_percent", 85.0, ">=", 300, "warning"),
            AlertRule("极高内存使用率", "memory_percent", 95.0, ">=", 60, "critical"),
            AlertRule("磁盘空间不足", "disk_usage", 90.0, ">=", 300, "warning"),
            AlertRule("磁盘空间严重不足", "disk_usage", 95.0, ">=", 60, "critical"),
            AlertRule("高负载", "load_average_1m", 4.0, ">=", 300, "warning"),
            AlertRule("服务不可用", "service_down", 1, "==", 0, "critical")
        ]
        
        rules_file = "alert_rules.json"
        if os.path.exists(rules_file):
            try:
                with open(rules_file, 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)
                    return [AlertRule(**rule) for rule in rules_data]
            except Exception as e:
                logger.error(f"加载告警规则失败: {e}")
                return default_rules
        else:
            # 创建默认告警规则文件
            with open(rules_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(rule) for rule in default_rules], f, indent=2, ensure_ascii=False)
            return default_rules
    
    def collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存信息
            memory = psutil.virtual_memory()
            
            # 磁盘使用率
            disk_usage = {}
            for path in self.config.get("disk_paths", ["/"]):
                try:
                    usage = psutil.disk_usage(path)
                    disk_usage[path] = (usage.used / usage.total) * 100
                except Exception as e:
                    logger.warning(f"获取磁盘使用率失败 {path}: {e}")
            
            # 网络IO
            network_io = {}
            try:
                net_io = psutil.net_io_counters()
                network_io = {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv
                }
            except Exception as e:
                logger.warning(f"获取网络IO失败: {e}")
            
            # 系统负载
            load_avg = os.getloadavg()
            
            # 进程数量
            process_count = len(psutil.pids())
            
            # 系统运行时间
            uptime = time.time() - psutil.boot_time()
            
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available=memory.available,
                disk_usage=disk_usage,
                network_io=network_io,
                load_average=load_avg,
                process_count=process_count,
                uptime=uptime
            )
            
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
            raise
    
    def check_service_status(self, service_config: Dict[str, Any]) -> ServiceStatus:
        """检查服务状态"""
        name = service_config["name"]
        process_name = service_config.get("process_name")
        port = service_config.get("port")
        health_url = service_config.get("health_check_url")
        
        try:
            # 查找进程
            pid = None
            cpu_percent = 0.0
            memory_percent = 0.0
            status = "stopped"
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if process_name in proc.info['name'] or \
                       any(process_name in cmd for cmd in proc.info['cmdline'] if cmd):
                        pid = proc.info['pid']
                        process = psutil.Process(pid)
                        cpu_percent = process.cpu_percent()
                        memory_percent = process.memory_percent()
                        status = "running"
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 检查端口监听
            is_listening = False
            if port:
                is_listening = self._check_port_listening(port)
            
            # 健康检查
            response_time = None
            if health_url and status == "running":
                response_time = self._health_check(health_url)
                if response_time is None:
                    status = "unhealthy"
            
            return ServiceStatus(
                name=name,
                status=status,
                pid=pid,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                port=port,
                is_listening=is_listening,
                response_time=response_time
            )
            
        except Exception as e:
            logger.error(f"检查服务状态失败 {name}: {e}")
            return ServiceStatus(
                name=name,
                status="error",
                pid=None,
                cpu_percent=0.0,
                memory_percent=0.0,
                port=port,
                is_listening=False,
                response_time=None
            )
    
    def _check_port_listening(self, port: int) -> bool:
        """检查端口是否在监听"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result == 0
        except Exception:
            return False
    
    def _health_check(self, url: str, timeout: int = 5) -> Optional[float]:
        """执行健康检查"""
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return response_time
            else:
                logger.warning(f"健康检查失败 {url}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"健康检查异常 {url}: {e}")
            return None
    
    def check_all_services(self) -> List[ServiceStatus]:
        """检查所有服务状态"""
        services = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_service = {
                executor.submit(self.check_service_status, service): service
                for service in self.config.get("services", [])
            }
            
            for future in as_completed(future_to_service):
                try:
                    service_status = future.result()
                    services.append(service_status)
                except Exception as e:
                    service = future_to_service[future]
                    logger.error(f"检查服务失败 {service['name']}: {e}")
        
        return services
    
    def analyze_performance(self, metrics: SystemMetrics, services: List[ServiceStatus]) -> Dict[str, Any]:
        """性能分析"""
        analysis = {
            "timestamp": metrics.timestamp,
            "system_health": "healthy",
            "issues": [],
            "recommendations": [],
            "performance_score": 100
        }
        
        # CPU分析
        if metrics.cpu_percent > 90:
            analysis["system_health"] = "critical"
            analysis["issues"].append(f"CPU使用率过高: {metrics.cpu_percent:.1f}%")
            analysis["recommendations"].append("检查高CPU使用率进程，考虑优化或扩容")
            analysis["performance_score"] -= 30
        elif metrics.cpu_percent > 70:
            analysis["system_health"] = "warning"
            analysis["issues"].append(f"CPU使用率较高: {metrics.cpu_percent:.1f}%")
            analysis["recommendations"].append("监控CPU使用趋势，准备优化措施")
            analysis["performance_score"] -= 15
        
        # 内存分析
        if metrics.memory_percent > 90:
            analysis["system_health"] = "critical"
            analysis["issues"].append(f"内存使用率过高: {metrics.memory_percent:.1f}%")
            analysis["recommendations"].append("检查内存泄漏，考虑增加内存或优化应用")
            analysis["performance_score"] -= 30
        elif metrics.memory_percent > 80:
            if analysis["system_health"] == "healthy":
                analysis["system_health"] = "warning"
            analysis["issues"].append(f"内存使用率较高: {metrics.memory_percent:.1f}%")
            analysis["recommendations"].append("监控内存使用趋势，准备扩容")
            analysis["performance_score"] -= 15
        
        # 磁盘分析
        for path, usage in metrics.disk_usage.items():
            if usage > 95:
                analysis["system_health"] = "critical"
                analysis["issues"].append(f"磁盘空间严重不足 {path}: {usage:.1f}%")
                analysis["recommendations"].append(f"立即清理 {path} 磁盘空间或扩容")
                analysis["performance_score"] -= 25
            elif usage > 85:
                if analysis["system_health"] == "healthy":
                    analysis["system_health"] = "warning"
                analysis["issues"].append(f"磁盘空间不足 {path}: {usage:.1f}%")
                analysis["recommendations"].append(f"计划清理 {path} 磁盘空间")
                analysis["performance_score"] -= 10
        
        # 负载分析
        cpu_count = psutil.cpu_count()
        if metrics.load_average[0] > cpu_count * 2:
            analysis["system_health"] = "critical"
            analysis["issues"].append(f"系统负载过高: {metrics.load_average[0]:.2f}")
            analysis["recommendations"].append("检查高负载进程，考虑优化或扩容")
            analysis["performance_score"] -= 20
        elif metrics.load_average[0] > cpu_count:
            if analysis["system_health"] == "healthy":
                analysis["system_health"] = "warning"
            analysis["issues"].append(f"系统负载较高: {metrics.load_average[0]:.2f}")
            analysis["recommendations"].append("监控系统负载趋势")
            analysis["performance_score"] -= 10
        
        # 服务分析
        for service in services:
            if service.status == "stopped":
                analysis["system_health"] = "critical"
                analysis["issues"].append(f"服务已停止: {service.name}")
                analysis["recommendations"].append(f"重启服务: {service.name}")
                analysis["performance_score"] -= 20
            elif service.status == "unhealthy":
                analysis["system_health"] = "critical"
                analysis["issues"].append(f"服务不健康: {service.name}")
                analysis["recommendations"].append(f"检查服务健康状态: {service.name}")
                analysis["performance_score"] -= 15
            elif service.response_time and service.response_time > 5.0:
                if analysis["system_health"] == "healthy":
                    analysis["system_health"] = "warning"
                analysis["issues"].append(f"服务响应缓慢: {service.name} ({service.response_time:.2f}s)")
                analysis["recommendations"].append(f"优化服务性能: {service.name}")
                analysis["performance_score"] -= 5
        
        return analysis
    
    def detect_anomalies(self, current_metrics: SystemMetrics) -> List[Dict[str, Any]]:
        """异常检测"""
        anomalies = []
        
        # 检查告警规则
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
                
            try:
                if self._evaluate_alert_rule(rule, current_metrics):
                    anomaly = {
                        "rule_name": rule.name,
                        "metric": rule.metric,
                        "current_value": self._get_metric_value(rule.metric, current_metrics),
                        "threshold": rule.threshold,
                        "severity": rule.severity,
                        "timestamp": current_metrics.timestamp
                    }
                    anomalies.append(anomaly)
                    
            except Exception as e:
                logger.error(f"评估告警规则失败 {rule.name}: {e}")
        
        return anomalies
    
    def _evaluate_alert_rule(self, rule: AlertRule, metrics: SystemMetrics) -> bool:
        """评估告警规则"""
        try:
            current_value = self._get_metric_value(rule.metric, metrics)
            if current_value is None:
                return False
            
            if rule.operator == ">":
                return current_value > rule.threshold
            elif rule.operator == ">=":
                return current_value >= rule.threshold
            elif rule.operator == "<":
                return current_value < rule.threshold
            elif rule.operator == "<=":
                return current_value <= rule.threshold
            elif rule.operator == "==":
                return current_value == rule.threshold
            else:
                logger.warning(f"未知的操作符: {rule.operator}")
                return False
                
        except Exception as e:
            logger.error(f"评估告警规则异常: {e}")
            return False
    
    def _get_metric_value(self, metric_name: str, metrics: SystemMetrics) -> Optional[float]:
        """获取指标值"""
        try:
            if metric_name == "cpu_percent":
                return metrics.cpu_percent
            elif metric_name == "memory_percent":
                return metrics.memory_percent
            elif metric_name == "load_average_1m":
                return metrics.load_average[0]
            elif metric_name == "load_average_5m":
                return metrics.load_average[1]
            elif metric_name == "load_average_15m":
                return metrics.load_average[2]
            elif metric_name == "disk_usage":
                # 返回最高的磁盘使用率
                if metrics.disk_usage:
                    return max(metrics.disk_usage.values())
                return 0.0
            elif metric_name == "process_count":
                return float(metrics.process_count)
            else:
                logger.warning(f"未知的指标名称: {metric_name}")
                return None
                
        except Exception as e:
            logger.error(f"获取指标值失败 {metric_name}: {e}")
            return None
    
    def send_alert(self, anomaly: Dict[str, Any]) -> bool:
        """发送告警"""
        try:
            webhook_url = self.config.get("alert_webhook")
            if not webhook_url:
                logger.info(f"告警: {anomaly}")
                return True
            
            alert_data = {
                "alert_name": anomaly["rule_name"],
                "severity": anomaly["severity"],
                "metric": anomaly["metric"],
                "current_value": anomaly["current_value"],
                "threshold": anomaly["threshold"],
                "timestamp": anomaly["timestamp"],
                "hostname": socket.gethostname()
            }
            
            response = requests.post(webhook_url, json=alert_data, timeout=10)
            if response.status_code == 200:
                logger.info(f"告警发送成功: {anomaly['rule_name']}")
                return True
            else:
                logger.error(f"告警发送失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"发送告警异常: {e}")
            return False
    
    def save_metrics(self, metrics: SystemMetrics, services: List[ServiceStatus], analysis: Dict[str, Any]):
        """保存指标数据"""
        try:
            metrics_file = self.config.get("metrics_file", "/var/log/system_metrics.json")
            
            data = {
                "metrics": asdict(metrics),
                "services": [asdict(service) for service in services],
                "analysis": analysis
            }
            
            # 读取现有数据
            existing_data = []
            if os.path.exists(metrics_file):
                try:
                    with open(metrics_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except Exception as e:
                    logger.warning(f"读取现有指标文件失败: {e}")
            
            # 添加新数据
            existing_data.append(data)
            
            # 保留最近的数据（根据配置的保留时间）
            retention_hours = self.config.get("metrics_retention_hours", 24)
            cutoff_time = datetime.now() - timedelta(hours=retention_hours)
            
            filtered_data = []
            for item in existing_data:
                try:
                    item_time = datetime.fromisoformat(item["metrics"]["timestamp"])
                    if item_time > cutoff_time:
                        filtered_data.append(item)
                except Exception:
                    continue
            
            # 保存数据
            os.makedirs(os.path.dirname(metrics_file), exist_ok=True)
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"保存指标数据失败: {e}")
    
    def generate_report(self) -> Dict[str, Any]:
        """生成监控报告"""
        try:
            # 收集当前指标
            metrics = self.collect_system_metrics()
            services = self.check_all_services()
            analysis = self.analyze_performance(metrics, services)
            anomalies = self.detect_anomalies(metrics)
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "hostname": socket.gethostname(),
                "system_metrics": asdict(metrics),
                "services": [asdict(service) for service in services],
                "performance_analysis": analysis,
                "anomalies": anomalies,
                "summary": {
                    "total_services": len(services),
                    "running_services": len([s for s in services if s.status == "running"]),
                    "stopped_services": len([s for s in services if s.status == "stopped"]),
                    "unhealthy_services": len([s for s in services if s.status == "unhealthy"]),
                    "system_health": analysis["system_health"],
                    "performance_score": analysis["performance_score"],
                    "active_alerts": len(anomalies)
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"生成监控报告失败: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def start_monitoring(self):
        """启动监控"""
        if self.running:
            logger.warning("监控已在运行中")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("系统监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("系统监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        interval = self.config.get("monitoring_interval", 30)
        
        while self.running:
            try:
                # 收集指标
                metrics = self.collect_system_metrics()
                services = self.check_all_services()
                analysis = self.analyze_performance(metrics, services)
                anomalies = self.detect_anomalies(metrics)
                
                # 保存指标
                self.save_metrics(metrics, services, analysis)
                
                # 处理告警
                for anomaly in anomalies:
                    self.send_alert(anomaly)
                
                # 记录日志
                logger.info(f"监控周期完成 - 系统健康: {analysis['system_health']}, "
                           f"性能评分: {analysis['performance_score']}, "
                           f"活跃告警: {len(anomalies)}")
                
                # 等待下一个周期
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                time.sleep(interval)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="系统监控工具")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--report", action="store_true", help="生成监控报告")
    parser.add_argument("--daemon", action="store_true", help="后台运行")
    parser.add_argument("--output", help="报告输出文件")
    
    args = parser.parse_args()
    
    try:
        monitor = SystemMonitor(args.config)
        
        if args.report:
            # 生成报告
            report = monitor.generate_report()
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                print(f"报告已保存到: {args.output}")
            else:
                print(json.dumps(report, indent=2, ensure_ascii=False))
        
        elif args.daemon:
            # 后台运行
            monitor.start_monitoring()
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                monitor.stop_monitoring()
        
        else:
            # 单次检查
            report = monitor.generate_report()
            print(json.dumps(report, indent=2, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()