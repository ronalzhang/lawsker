#!/usr/bin/env python3
"""
故障诊断工具
实现常见问题自动诊断、日志分析、错误定位、修复建议和故障报告功能
"""

import os
import re
import sys
import json
import time
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import psutil
import requests
from collections import defaultdict, Counter
import sqlite3

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DiagnosisResult:
    """诊断结果数据结构"""
    issue_id: str
    title: str
    severity: str  # 'critical', 'warning', 'info'
    category: str  # 'system', 'service', 'network', 'database', 'application'
    description: str
    symptoms: List[str]
    root_cause: Optional[str]
    recommendations: List[str]
    auto_fix_available: bool
    confidence: float  # 0.0 - 1.0
    timestamp: str

@dataclass
class LogAnalysisResult:
    """日志分析结果"""
    log_file: str
    error_count: int
    warning_count: int
    critical_patterns: List[Dict[str, Any]]
    frequent_errors: List[Dict[str, Any]]
    time_range: Tuple[str, str]
    analysis_summary: str

@dataclass
class KnowledgeBaseEntry:
    """知识库条目"""
    issue_pattern: str
    title: str
    category: str
    severity: str
    description: str
    symptoms: List[str]
    solutions: List[str]
    keywords: List[str]

class FaultDiagnosisEngine:
    """故障诊断引擎"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "diagnosis_config.json"
        self.config = self._load_config()
        self.knowledge_base = self._load_knowledge_base()
        self.diagnosis_history = []
        self.db_path = self.config.get("database_path", "diagnosis.db")
        self._init_database()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载诊断配置"""
        default_config = {
            "log_files": [
                "/var/log/syslog",
                "/var/log/nginx/error.log",
                "/var/log/postgresql/postgresql.log",
                "/var/log/redis/redis-server.log",
                "/var/log/lawsker/app.log"
            ],
            "service_configs": {
                "nginx": {
                    "config_file": "/etc/nginx/nginx.conf",
                    "error_log": "/var/log/nginx/error.log",
                    "access_log": "/var/log/nginx/access.log"
                },
                "postgresql": {
                    "config_file": "/etc/postgresql/*/main/postgresql.conf",
                    "log_file": "/var/log/postgresql/postgresql.log"
                },
                "redis": {
                    "config_file": "/etc/redis/redis.conf",
                    "log_file": "/var/log/redis/redis-server.log"
                }
            },
            "analysis_window_hours": 24,
            "max_log_lines": 10000,
            "database_path": "diagnosis.db",
            "auto_fix_enabled": True,
            "notification_webhook": None
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                return default_config
        else:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    
    def _load_knowledge_base(self) -> List[KnowledgeBaseEntry]:
        """加载知识库"""
        knowledge_base = [
            # 系统相关问题
            KnowledgeBaseEntry(
                issue_pattern=r"Out of memory|Cannot allocate memory|OOM",
                title="系统内存不足",
                category="system",
                severity="critical",
                description="系统可用内存不足，可能导致进程被杀死或系统不稳定",
                symptoms=["进程意外终止", "系统响应缓慢", "OOM Killer激活"],
                solutions=[
                    "增加系统内存",
                    "优化应用内存使用",
                    "配置swap空间",
                    "重启内存占用高的服务"
                ],
                keywords=["memory", "oom", "swap", "malloc"]
            ),
            
            KnowledgeBaseEntry(
                issue_pattern=r"No space left on device|Disk full",
                title="磁盘空间不足",
                category="system",
                severity="critical",
                description="磁盘空间已满，无法写入新文件",
                symptoms=["无法创建文件", "应用写入失败", "日志停止更新"],
                solutions=[
                    "清理临时文件和日志",
                    "删除不必要的文件",
                    "扩展磁盘空间",
                    "配置日志轮转"
                ],
                keywords=["disk", "space", "full", "storage"]
            ),
            
            # 网络相关问题
            KnowledgeBaseEntry(
                issue_pattern=r"Connection refused|Connection timeout|Network unreachable",
                title="网络连接问题",
                category="network",
                severity="warning",
                description="网络连接失败，可能是服务未启动或网络配置问题",
                symptoms=["连接超时", "服务不可达", "网络错误"],
                solutions=[
                    "检查服务状态",
                    "验证网络配置",
                    "检查防火墙规则",
                    "重启网络服务"
                ],
                keywords=["connection", "network", "timeout", "refused"]
            ),
            
            # 数据库相关问题
            KnowledgeBaseEntry(
                issue_pattern=r"too many connections|connection limit exceeded",
                title="数据库连接数过多",
                category="database",
                severity="warning",
                description="数据库连接数达到上限，新连接被拒绝",
                symptoms=["连接被拒绝", "应用数据库错误", "连接池耗尽"],
                solutions=[
                    "增加最大连接数配置",
                    "优化连接池配置",
                    "检查连接泄漏",
                    "重启数据库服务"
                ],
                keywords=["database", "connection", "pool", "limit"]
            ),
            
            # Web服务相关问题
            KnowledgeBaseEntry(
                issue_pattern=r"502 Bad Gateway|503 Service Unavailable|upstream",
                title="Web服务网关错误",
                category="service",
                severity="critical",
                description="Web服务网关错误，后端服务不可用",
                symptoms=["502/503错误", "页面无法访问", "服务不响应"],
                solutions=[
                    "检查后端服务状态",
                    "重启应用服务",
                    "检查Nginx配置",
                    "验证upstream配置"
                ],
                keywords=["nginx", "gateway", "upstream", "502", "503"]
            ),
            
            # SSL证书问题
            KnowledgeBaseEntry(
                issue_pattern=r"certificate|SSL|TLS|expired|invalid",
                title="SSL证书问题",
                category="security",
                severity="warning",
                description="SSL证书过期或配置错误",
                symptoms=["HTTPS访问失败", "证书警告", "SSL握手失败"],
                solutions=[
                    "更新SSL证书",
                    "检查证书配置",
                    "验证证书链",
                    "重新申请证书"
                ],
                keywords=["ssl", "certificate", "tls", "https"]
            ),
            
            # 应用相关问题
            KnowledgeBaseEntry(
                issue_pattern=r"ImportError|ModuleNotFoundError|No module named",
                title="Python模块缺失",
                category="application",
                severity="critical",
                description="Python应用缺少必要的模块依赖",
                symptoms=["导入错误", "应用启动失败", "功能异常"],
                solutions=[
                    "安装缺失的模块",
                    "检查虚拟环境",
                    "更新requirements.txt",
                    "重新安装依赖"
                ],
                keywords=["python", "import", "module", "dependency"]
            )
        ]
        
        # 尝试从文件加载额外的知识库条目
        kb_file = "knowledge_base.json"
        if os.path.exists(kb_file):
            try:
                with open(kb_file, 'r', encoding='utf-8') as f:
                    kb_data = json.load(f)
                    for entry_data in kb_data:
                        knowledge_base.append(KnowledgeBaseEntry(**entry_data))
            except Exception as e:
                logger.error(f"加载知识库文件失败: {e}")
        
        return knowledge_base
    
    def _init_database(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS diagnosis_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        issue_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        category TEXT NOT NULL,
                        description TEXT,
                        root_cause TEXT,
                        confidence REAL,
                        auto_fixed BOOLEAN DEFAULT FALSE,
                        resolved BOOLEAN DEFAULT FALSE
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS log_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        log_file TEXT NOT NULL,
                        error_count INTEGER,
                        warning_count INTEGER,
                        analysis_summary TEXT
                    )
                ''')
                
                conn.commit()
        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
    
    def analyze_logs(self, log_file: str, hours: int = 24) -> LogAnalysisResult:
        """分析日志文件"""
        try:
            if not os.path.exists(log_file):
                logger.warning(f"日志文件不存在: {log_file}")
                return LogAnalysisResult(
                    log_file=log_file,
                    error_count=0,
                    warning_count=0,
                    critical_patterns=[],
                    frequent_errors=[],
                    time_range=("", ""),
                    analysis_summary="日志文件不存在"
                )
            
            # 读取日志文件
            cutoff_time = datetime.now() - timedelta(hours=hours)
            max_lines = self.config.get("max_log_lines", 10000)
            
            error_patterns = []
            warning_patterns = []
            all_lines = []
            
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                # 只分析最近的行
                recent_lines = lines[-max_lines:] if len(lines) > max_lines else lines
                
                for line in recent_lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    all_lines.append(line)
                    
                    # 检测错误模式
                    if re.search(r'\b(ERROR|FATAL|CRITICAL)\b', line, re.IGNORECASE):
                        error_patterns.append(line)
                    elif re.search(r'\b(WARN|WARNING)\b', line, re.IGNORECASE):
                        warning_patterns.append(line)
            
            # 分析关键模式
            critical_patterns = self._find_critical_patterns(all_lines)
            frequent_errors = self._find_frequent_errors(error_patterns)
            
            # 时间范围
            time_range = self._extract_time_range(all_lines)
            
            # 生成分析摘要
            analysis_summary = self._generate_log_summary(
                len(error_patterns), len(warning_patterns), 
                critical_patterns, frequent_errors
            )
            
            result = LogAnalysisResult(
                log_file=log_file,
                error_count=len(error_patterns),
                warning_count=len(warning_patterns),
                critical_patterns=critical_patterns,
                frequent_errors=frequent_errors,
                time_range=time_range,
                analysis_summary=analysis_summary
            )
            
            # 保存分析结果到数据库
            self._save_log_analysis(result)
            
            return result
            
        except Exception as e:
            logger.error(f"分析日志文件失败 {log_file}: {e}")
            return LogAnalysisResult(
                log_file=log_file,
                error_count=0,
                warning_count=0,
                critical_patterns=[],
                frequent_errors=[],
                time_range=("", ""),
                analysis_summary=f"分析失败: {str(e)}"
            )
    
    def _find_critical_patterns(self, lines: List[str]) -> List[Dict[str, Any]]:
        """查找关键模式"""
        critical_patterns = []
        
        for entry in self.knowledge_base:
            pattern_matches = []
            for line in lines:
                if re.search(entry.issue_pattern, line, re.IGNORECASE):
                    pattern_matches.append(line)
            
            if pattern_matches:
                critical_patterns.append({
                    "pattern": entry.issue_pattern,
                    "title": entry.title,
                    "category": entry.category,
                    "severity": entry.severity,
                    "match_count": len(pattern_matches),
                    "sample_lines": pattern_matches[:3]  # 只保留前3个样本
                })
        
        # 按匹配数量排序
        critical_patterns.sort(key=lambda x: x["match_count"], reverse=True)
        return critical_patterns[:10]  # 只返回前10个
    
    def _find_frequent_errors(self, error_lines: List[str]) -> List[Dict[str, Any]]:
        """查找频繁错误"""
        # 提取错误消息的关键部分
        error_patterns = []
        for line in error_lines:
            # 移除时间戳和进程ID等变化部分
            cleaned = re.sub(r'\d{4}-\d{2}-\d{2}[\s\d:.-]*', '', line)
            cleaned = re.sub(r'\[\d+\]', '', cleaned)
            cleaned = re.sub(r'pid:\s*\d+', '', cleaned)
            cleaned = re.sub(r'\b\d+\.\d+\.\d+\.\d+\b', 'IP', cleaned)
            error_patterns.append(cleaned.strip())
        
        # 统计频率
        error_counter = Counter(error_patterns)
        frequent_errors = []
        
        for error, count in error_counter.most_common(10):
            if count > 1:  # 只包含出现多次的错误
                frequent_errors.append({
                    "error_pattern": error,
                    "count": count,
                    "sample_line": next((line for line in error_lines if error in line), "")
                })
        
        return frequent_errors
    
    def _extract_time_range(self, lines: List[str]) -> Tuple[str, str]:
        """提取时间范围"""
        timestamps = []
        
        for line in lines:
            # 尝试提取时间戳
            time_match = re.search(r'\d{4}-\d{2}-\d{2}[\s\d:.-]+', line)
            if time_match:
                timestamps.append(time_match.group())
        
        if timestamps:
            return (timestamps[0], timestamps[-1])
        else:
            return ("", "")
    
    def _generate_log_summary(self, error_count: int, warning_count: int, 
                            critical_patterns: List[Dict], frequent_errors: List[Dict]) -> str:
        """生成日志分析摘要"""
        summary_parts = []
        
        if error_count > 0:
            summary_parts.append(f"发现 {error_count} 个错误")
        
        if warning_count > 0:
            summary_parts.append(f"发现 {warning_count} 个警告")
        
        if critical_patterns:
            summary_parts.append(f"检测到 {len(critical_patterns)} 种关键问题模式")
        
        if frequent_errors:
            summary_parts.append(f"发现 {len(frequent_errors)} 种频繁错误")
        
        if not summary_parts:
            return "日志分析正常，未发现明显问题"
        
        return "；".join(summary_parts)
    
    def diagnose_system_issues(self) -> List[DiagnosisResult]:
        """诊断系统问题"""
        diagnosis_results = []
        
        try:
            # 系统资源检查
            diagnosis_results.extend(self._diagnose_system_resources())
            
            # 服务状态检查
            diagnosis_results.extend(self._diagnose_services())
            
            # 网络连接检查
            diagnosis_results.extend(self._diagnose_network())
            
            # 日志分析
            diagnosis_results.extend(self._diagnose_from_logs())
            
            # 配置文件检查
            diagnosis_results.extend(self._diagnose_configurations())
            
            # 保存诊断结果
            for result in diagnosis_results:
                self._save_diagnosis_result(result)
            
            return diagnosis_results
            
        except Exception as e:
            logger.error(f"系统诊断失败: {e}")
            return []
    
    def _diagnose_system_resources(self) -> List[DiagnosisResult]:
        """诊断系统资源问题"""
        results = []
        
        try:
            # CPU使用率检查
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                results.append(DiagnosisResult(
                    issue_id="high_cpu_usage",
                    title="CPU使用率过高",
                    severity="critical",
                    category="system",
                    description=f"当前CPU使用率为 {cpu_percent:.1f}%，超过90%阈值",
                    symptoms=["系统响应缓慢", "应用性能下降"],
                    root_cause="CPU资源不足或存在高负载进程",
                    recommendations=[
                        "检查高CPU使用率的进程",
                        "优化应用性能",
                        "考虑增加CPU资源"
                    ],
                    auto_fix_available=False,
                    confidence=0.9,
                    timestamp=datetime.now().isoformat()
                ))
            
            # 内存使用率检查
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                results.append(DiagnosisResult(
                    issue_id="high_memory_usage",
                    title="内存使用率过高",
                    severity="critical",
                    category="system",
                    description=f"当前内存使用率为 {memory.percent:.1f}%，可用内存仅 {memory.available // 1024 // 1024} MB",
                    symptoms=["系统响应缓慢", "应用可能被OOM Killer终止"],
                    root_cause="内存不足或存在内存泄漏",
                    recommendations=[
                        "检查高内存使用率的进程",
                        "重启内存占用高的服务",
                        "增加系统内存",
                        "配置swap空间"
                    ],
                    auto_fix_available=True,
                    confidence=0.9,
                    timestamp=datetime.now().isoformat()
                ))
            
            # 磁盘空间检查
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    usage_percent = (usage.used / usage.total) * 100
                    
                    if usage_percent > 95:
                        results.append(DiagnosisResult(
                            issue_id=f"disk_full_{partition.mountpoint.replace('/', '_')}",
                            title=f"磁盘空间严重不足 ({partition.mountpoint})",
                            severity="critical",
                            category="system",
                            description=f"分区 {partition.mountpoint} 使用率为 {usage_percent:.1f}%，剩余空间仅 {(usage.total - usage.used) // 1024 // 1024} MB",
                            symptoms=["无法写入文件", "应用错误", "日志停止更新"],
                            root_cause="磁盘空间不足",
                            recommendations=[
                                "清理临时文件和日志",
                                "删除不必要的文件",
                                "扩展磁盘空间",
                                "配置日志轮转"
                            ],
                            auto_fix_available=True,
                            confidence=1.0,
                            timestamp=datetime.now().isoformat()
                        ))
                except Exception:
                    continue
            
        except Exception as e:
            logger.error(f"诊断系统资源失败: {e}")
        
        return results
    
    def _diagnose_services(self) -> List[DiagnosisResult]:
        """诊断服务问题"""
        results = []
        
        # 关键服务列表
        critical_services = ["nginx", "postgresql", "redis-server"]
        
        for service_name in critical_services:
            try:
                # 检查服务是否运行
                service_running = False
                for proc in psutil.process_iter(['name', 'cmdline']):
                    try:
                        if service_name in proc.info['name'] or \
                           any(service_name in cmd for cmd in proc.info['cmdline'] if cmd):
                            service_running = True
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if not service_running:
                    results.append(DiagnosisResult(
                        issue_id=f"service_down_{service_name}",
                        title=f"关键服务未运行: {service_name}",
                        severity="critical",
                        category="service",
                        description=f"关键服务 {service_name} 未在运行",
                        symptoms=["服务不可用", "应用功能异常"],
                        root_cause=f"{service_name} 服务已停止",
                        recommendations=[
                            f"启动 {service_name} 服务",
                            "检查服务配置",
                            "查看服务日志",
                            "检查依赖服务"
                        ],
                        auto_fix_available=True,
                        confidence=1.0,
                        timestamp=datetime.now().isoformat()
                    ))
                
            except Exception as e:
                logger.error(f"检查服务 {service_name} 失败: {e}")
        
        return results
    
    def _diagnose_network(self) -> List[DiagnosisResult]:
        """诊断网络问题"""
        results = []
        
        try:
            # 检查关键端口
            critical_ports = [80, 443, 5432, 6379, 8000]
            
            for port in critical_ports:
                try:
                    import socket
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(1)
                        result = sock.connect_ex(('localhost', port))
                        
                        if result != 0:
                            service_name = {
                                80: "HTTP (Nginx)",
                                443: "HTTPS (Nginx)",
                                5432: "PostgreSQL",
                                6379: "Redis",
                                8000: "Lawsker Backend"
                            }.get(port, f"Port {port}")
                            
                            results.append(DiagnosisResult(
                                issue_id=f"port_not_listening_{port}",
                                title=f"端口未监听: {port} ({service_name})",
                                severity="warning",
                                category="network",
                                description=f"端口 {port} ({service_name}) 未在监听",
                                symptoms=["服务不可访问", "连接被拒绝"],
                                root_cause="服务未启动或配置错误",
                                recommendations=[
                                    f"检查 {service_name} 服务状态",
                                    "验证服务配置",
                                    "检查防火墙规则",
                                    "查看服务日志"
                                ],
                                auto_fix_available=False,
                                confidence=0.8,
                                timestamp=datetime.now().isoformat()
                            ))
                
                except Exception as e:
                    logger.warning(f"检查端口 {port} 失败: {e}")
        
        except Exception as e:
            logger.error(f"网络诊断失败: {e}")
        
        return results
    
    def _diagnose_from_logs(self) -> List[DiagnosisResult]:
        """从日志诊断问题"""
        results = []
        
        for log_file in self.config.get("log_files", []):
            try:
                if not os.path.exists(log_file):
                    continue
                
                log_analysis = self.analyze_logs(log_file, hours=1)  # 分析最近1小时
                
                # 基于关键模式生成诊断结果
                for pattern in log_analysis.critical_patterns:
                    if pattern["match_count"] > 5:  # 只处理频繁出现的问题
                        results.append(DiagnosisResult(
                            issue_id=f"log_pattern_{hash(pattern['pattern'])}",
                            title=pattern["title"],
                            severity=pattern["severity"],
                            category=pattern["category"],
                            description=f"在日志 {log_file} 中发现 {pattern['match_count']} 次匹配",
                            symptoms=[f"日志中出现: {line[:100]}..." for line in pattern["sample_lines"]],
                            root_cause="根据日志模式分析得出",
                            recommendations=self._get_recommendations_for_pattern(pattern["pattern"]),
                            auto_fix_available=False,
                            confidence=0.7,
                            timestamp=datetime.now().isoformat()
                        ))
                
            except Exception as e:
                logger.error(f"从日志诊断失败 {log_file}: {e}")
        
        return results
    
    def _diagnose_configurations(self) -> List[DiagnosisResult]:
        """诊断配置问题"""
        results = []
        
        # 检查Nginx配置
        nginx_config = "/etc/nginx/nginx.conf"
        if os.path.exists(nginx_config):
            try:
                # 测试Nginx配置语法
                result = subprocess.run(
                    ["nginx", "-t"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                
                if result.returncode != 0:
                    results.append(DiagnosisResult(
                        issue_id="nginx_config_error",
                        title="Nginx配置错误",
                        severity="critical",
                        category="service",
                        description="Nginx配置文件存在语法错误",
                        symptoms=["Nginx无法启动", "配置重载失败"],
                        root_cause="配置文件语法错误",
                        recommendations=[
                            "检查Nginx配置语法",
                            "修复配置错误",
                            "恢复备份配置",
                            "重新生成配置"
                        ],
                        auto_fix_available=False,
                        confidence=1.0,
                        timestamp=datetime.now().isoformat()
                    ))
                
            except Exception as e:
                logger.warning(f"检查Nginx配置失败: {e}")
        
        return results
    
    def _get_recommendations_for_pattern(self, pattern: str) -> List[str]:
        """根据模式获取建议"""
        for entry in self.knowledge_base:
            if entry.issue_pattern == pattern:
                return entry.solutions
        
        return ["查看相关日志", "检查服务状态", "联系技术支持"]
    
    def auto_fix_issue(self, issue_id: str) -> bool:
        """自动修复问题"""
        if not self.config.get("auto_fix_enabled", True):
            logger.info("自动修复功能已禁用")
            return False
        
        try:
            if issue_id.startswith("high_memory_usage"):
                return self._auto_fix_memory_issue()
            elif issue_id.startswith("disk_full_"):
                return self._auto_fix_disk_issue()
            elif issue_id.startswith("service_down_"):
                service_name = issue_id.replace("service_down_", "")
                return self._auto_fix_service_issue(service_name)
            else:
                logger.info(f"问题 {issue_id} 不支持自动修复")
                return False
                
        except Exception as e:
            logger.error(f"自动修复失败 {issue_id}: {e}")
            return False
    
    def _auto_fix_memory_issue(self) -> bool:
        """自动修复内存问题"""
        try:
            # 清理系统缓存
            subprocess.run(["sync"], check=True)
            subprocess.run(["echo", "3", ">", "/proc/sys/vm/drop_caches"], shell=True)
            
            # 重启高内存使用的非关键进程
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    if proc.info['memory_percent'] > 10 and \
                       proc.info['name'] not in ['nginx', 'postgres', 'redis-server']:
                        logger.info(f"重启高内存进程: {proc.info['name']} (PID: {proc.info['pid']})")
                        proc.terminate()
                        proc.wait(timeout=5)
                except Exception:
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"自动修复内存问题失败: {e}")
            return False
    
    def _auto_fix_disk_issue(self) -> bool:
        """自动修复磁盘问题"""
        try:
            # 清理临时文件
            temp_dirs = ["/tmp", "/var/tmp", "/var/log"]
            
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    # 删除7天前的临时文件
                    subprocess.run([
                        "find", temp_dir, "-type", "f", 
                        "-mtime", "+7", "-delete"
                    ], check=False)
            
            # 清理日志文件
            log_dirs = ["/var/log"]
            for log_dir in log_dirs:
                if os.path.exists(log_dir):
                    # 压缩大于100MB的日志文件
                    subprocess.run([
                        "find", log_dir, "-name", "*.log", 
                        "-size", "+100M", "-exec", "gzip", "{}", ";"
                    ], check=False)
            
            return True
            
        except Exception as e:
            logger.error(f"自动修复磁盘问题失败: {e}")
            return False
    
    def _auto_fix_service_issue(self, service_name: str) -> bool:
        """自动修复服务问题"""
        try:
            # 尝试启动服务
            if service_name == "nginx":
                subprocess.run(["systemctl", "start", "nginx"], check=True)
            elif service_name == "postgresql":
                subprocess.run(["systemctl", "start", "postgresql"], check=True)
            elif service_name == "redis-server":
                subprocess.run(["systemctl", "start", "redis"], check=True)
            else:
                logger.warning(f"不支持自动启动服务: {service_name}")
                return False
            
            # 等待服务启动
            time.sleep(3)
            
            # 验证服务状态
            result = subprocess.run(
                ["systemctl", "is-active", service_name], 
                capture_output=True, 
                text=True
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"自动修复服务问题失败 {service_name}: {e}")
            return False
    
    def _save_diagnosis_result(self, result: DiagnosisResult):
        """保存诊断结果到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO diagnosis_history 
                    (timestamp, issue_id, title, severity, category, description, 
                     root_cause, confidence, auto_fixed, resolved)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result.timestamp, result.issue_id, result.title,
                    result.severity, result.category, result.description,
                    result.root_cause, result.confidence, False, False
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存诊断结果失败: {e}")
    
    def _save_log_analysis(self, result: LogAnalysisResult):
        """保存日志分析结果到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO log_analysis 
                    (timestamp, log_file, error_count, warning_count, analysis_summary)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(), result.log_file,
                    result.error_count, result.warning_count,
                    result.analysis_summary
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存日志分析结果失败: {e}")
    
    def generate_diagnosis_report(self) -> Dict[str, Any]:
        """生成诊断报告"""
        try:
            # 执行完整诊断
            diagnosis_results = self.diagnose_system_issues()
            
            # 分析所有日志文件
            log_analyses = []
            for log_file in self.config.get("log_files", []):
                if os.path.exists(log_file):
                    analysis = self.analyze_logs(log_file)
                    log_analyses.append(asdict(analysis))
            
            # 统计信息
            severity_counts = Counter(result.severity for result in diagnosis_results)
            category_counts = Counter(result.category for result in diagnosis_results)
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_issues": len(diagnosis_results),
                    "critical_issues": severity_counts.get("critical", 0),
                    "warning_issues": severity_counts.get("warning", 0),
                    "info_issues": severity_counts.get("info", 0),
                    "auto_fixable_issues": len([r for r in diagnosis_results if r.auto_fix_available]),
                    "categories": dict(category_counts)
                },
                "diagnosis_results": [asdict(result) for result in diagnosis_results],
                "log_analyses": log_analyses,
                "recommendations": self._generate_overall_recommendations(diagnosis_results),
                "system_health_score": self._calculate_health_score(diagnosis_results)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"生成诊断报告失败: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def _generate_overall_recommendations(self, results: List[DiagnosisResult]) -> List[str]:
        """生成总体建议"""
        recommendations = set()
        
        critical_count = len([r for r in results if r.severity == "critical"])
        warning_count = len([r for r in results if r.severity == "warning"])
        
        if critical_count > 0:
            recommendations.add("立即处理关键问题以避免系统故障")
        
        if warning_count > 3:
            recommendations.add("关注警告问题，防止问题恶化")
        
        # 基于问题类别的建议
        categories = Counter(result.category for result in results)
        
        if categories.get("system", 0) > 2:
            recommendations.add("考虑系统资源扩容或优化")
        
        if categories.get("service", 0) > 1:
            recommendations.add("检查服务配置和依赖关系")
        
        if categories.get("network", 0) > 0:
            recommendations.add("验证网络配置和防火墙规则")
        
        return list(recommendations)
    
    def _calculate_health_score(self, results: List[DiagnosisResult]) -> int:
        """计算系统健康评分"""
        base_score = 100
        
        for result in results:
            if result.severity == "critical":
                base_score -= 20
            elif result.severity == "warning":
                base_score -= 10
            elif result.severity == "info":
                base_score -= 2
        
        return max(0, base_score)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="故障诊断工具")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--report", action="store_true", help="生成诊断报告")
    parser.add_argument("--analyze-logs", help="分析指定日志文件")
    parser.add_argument("--auto-fix", help="自动修复指定问题ID")
    parser.add_argument("--output", help="报告输出文件")
    
    args = parser.parse_args()
    
    try:
        engine = FaultDiagnosisEngine(args.config)
        
        if args.analyze_logs:
            # 分析日志
            result = engine.analyze_logs(args.analyze_logs)
            print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
        
        elif args.auto_fix:
            # 自动修复
            success = engine.auto_fix_issue(args.auto_fix)
            print(f"自动修复 {'成功' if success else '失败'}: {args.auto_fix}")
        
        elif args.report:
            # 生成报告
            report = engine.generate_diagnosis_report()
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                print(f"诊断报告已保存到: {args.output}")
            else:
                print(json.dumps(report, indent=2, ensure_ascii=False))
        
        else:
            # 默认执行诊断
            results = engine.diagnose_system_issues()
            for result in results:
                print(f"[{result.severity.upper()}] {result.title}")
                print(f"  描述: {result.description}")
                print(f"  建议: {'; '.join(result.recommendations)}")
                print()
    
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()