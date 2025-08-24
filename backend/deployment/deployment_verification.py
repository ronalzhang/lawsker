#!/usr/bin/env python3
"""
部署验证测试套件
实现健康检查端点测试、功能性端到端测试、性能基准测试和安全配置验证测试
"""

import os
import sys
import json
import time
import asyncio
import logging
import requests
import psutil
import ssl
import socket
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import subprocess
import concurrent.futures
from urllib.parse import urljoin
import psycopg2
import redis
from cryptography import x509
from cryptography.hazmat.backends import default_backend


@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    category: str
    status: str  # "pass", "fail", "skip", "error"
    message: str
    duration: float = 0.0
    details: Optional[Dict] = None
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class VerificationConfig:
    """验证配置"""
    base_url: str = "http://localhost:8000"
    ssl_base_url: str = "https://lawsker.com"
    domains: List[str] = None
    database_url: str = "postgresql://lawsker_user:password@localhost:5432/lawsker_prod"
    redis_url: str = "redis://localhost:6379/0"
    prometheus_url: str = "http://localhost:9090"
    grafana_url: str = "http://localhost:3000"
    timeout: int = 30
    performance_thresholds: Dict[str, float] = None
    
    def __post_init__(self):
        if self.domains is None:
            self.domains = ["lawsker.com", "admin.lawsker.com"]
        if self.performance_thresholds is None:
            self.performance_thresholds = {
                "response_time_ms": 1000,
                "database_query_ms": 100,
                "memory_usage_percent": 80,
                "cpu_usage_percent": 80,
                "disk_usage_percent": 90
            }


class DeploymentVerificationSuite:
    """
    部署验证测试套件
    
    实现：
    - 健康检查端点测试
    - 功能性端到端测试
    - 性能基准测试
    - 安全配置验证测试
    """
    
    def __init__(self, config: VerificationConfig):
        self.config = config
        self.logger = self._setup_logger()
        self.test_results: List[TestResult] = []
        self.session = requests.Session()
        self.session.timeout = config.timeout
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """
        运行所有验证测试
        
        Returns:
            完整的测试报告
        """
        self.logger.info("Starting deployment verification tests")
        start_time = datetime.now()
        
        # 清空之前的测试结果
        self.test_results = []
        
        try:
            # 1. 健康检查测试
            await self._run_health_check_tests()
            
            # 2. 功能性端到端测试
            await self._run_functional_tests()
            
            # 3. 性能基准测试
            await self._run_performance_tests()
            
            # 4. 安全配置验证测试
            await self._run_security_tests()
            
        except Exception as e:
            self.logger.error(f"Test suite execution failed: {str(e)}")
            self.test_results.append(TestResult(
                test_name="test_suite_execution",
                category="system",
                status="error",
                message=f"Test suite execution failed: {str(e)}",
                error=str(e)
            ))
        
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        # 生成测试报告
        report = self._generate_test_report(total_duration)
        
        self.logger.info(f"Verification tests completed in {total_duration:.2f} seconds")
        return report
    
    async def _run_health_check_tests(self):
        """运行健康检查端点测试"""
        self.logger.info("Running health check tests")
        
        # 后端健康检查
        await self._test_backend_health()
        
        # 数据库健康检查
        await self._test_database_health()
        
        # Redis健康检查
        await self._test_redis_health()
        
        # 前端可访问性检查
        await self._test_frontend_accessibility()
        
        # 监控服务健康检查
        await self._test_monitoring_health()
    
    async def _test_backend_health(self):
        """测试后端健康检查端点"""
        test_name = "backend_health_check"
        start_time = time.time()
        
        try:
            health_url = urljoin(self.config.base_url, "/api/v1/health")
            response = self.session.get(health_url)
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                health_data = response.json()
                
                # 检查健康状态
                if health_data.get("status") == "healthy":
                    self.test_results.append(TestResult(
                        test_name=test_name,
                        category="health_check",
                        status="pass",
                        message="Backend health check passed",
                        duration=duration,
                        details=health_data
                    ))
                else:
                    self.test_results.append(TestResult(
                        test_name=test_name,
                        category="health_check",
                        status="fail",
                        message=f"Backend health check failed: {health_data.get('message', 'Unknown error')}",
                        duration=duration,
                        details=health_data
                    ))
            else:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="health_check",
                    status="fail",
                    message=f"Backend health check returned status {response.status_code}",
                    duration=duration,
                    error=response.text
                ))
                
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name=test_name,
                category="health_check",
                status="error",
                message=f"Backend health check failed: {str(e)}",
                duration=duration,
                error=str(e)
            ))
    
    async def _test_database_health(self):
        """测试数据库健康检查"""
        test_name = "database_health_check"
        start_time = time.time()
        
        try:
            conn = psycopg2.connect(self.config.database_url)
            cursor = conn.cursor()
            
            # 执行简单查询
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            
            # 检查连接数
            cursor.execute("SELECT count(*) FROM pg_stat_activity")
            connection_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=test_name,
                category="health_check",
                status="pass",
                message="Database health check passed",
                duration=duration,
                details={
                    "version": version,
                    "connection_count": connection_count
                }
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name=test_name,
                category="health_check",
                status="error",
                message=f"Database health check failed: {str(e)}",
                duration=duration,
                error=str(e)
            ))
    
    async def _test_redis_health(self):
        """测试Redis健康检查"""
        test_name = "redis_health_check"
        start_time = time.time()
        
        try:
            r = redis.from_url(self.config.redis_url)
            
            # 测试连接
            info = r.info()
            
            # 测试读写
            test_key = "health_check_test"
            r.set(test_key, "test_value", ex=60)
            value = r.get(test_key)
            r.delete(test_key)
            
            duration = time.time() - start_time
            
            if value == b"test_value":
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="health_check",
                    status="pass",
                    message="Redis health check passed",
                    duration=duration,
                    details={
                        "version": info.get("redis_version"),
                        "connected_clients": info.get("connected_clients"),
                        "used_memory": info.get("used_memory_human")
                    }
                ))
            else:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="health_check",
                    status="fail",
                    message="Redis read/write test failed",
                    duration=duration
                ))
                
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name=test_name,
                category="health_check",
                status="error",
                message=f"Redis health check failed: {str(e)}",
                duration=duration,
                error=str(e)
            ))
    
    async def _test_frontend_accessibility(self):
        """测试前端可访问性"""
        test_name = "frontend_accessibility"
        start_time = time.time()
        
        try:
            # 测试主页
            response = self.session.get(self.config.base_url.replace(":8000", ""))
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                # 检查基本HTML结构
                content = response.text.lower()
                has_html = "<html" in content
                has_title = "<title" in content
                has_body = "<body" in content
                
                if has_html and has_title and has_body:
                    self.test_results.append(TestResult(
                        test_name=test_name,
                        category="health_check",
                        status="pass",
                        message="Frontend accessibility check passed",
                        duration=duration,
                        details={
                            "status_code": response.status_code,
                            "content_length": len(response.text),
                            "has_basic_structure": True
                        }
                    ))
                else:
                    self.test_results.append(TestResult(
                        test_name=test_name,
                        category="health_check",
                        status="fail",
                        message="Frontend HTML structure incomplete",
                        duration=duration,
                        details={
                            "has_html": has_html,
                            "has_title": has_title,
                            "has_body": has_body
                        }
                    ))
            else:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="health_check",
                    status="fail",
                    message=f"Frontend returned status {response.status_code}",
                    duration=duration,
                    error=response.text[:500]
                ))
                
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name=test_name,
                category="health_check",
                status="error",
                message=f"Frontend accessibility check failed: {str(e)}",
                duration=duration,
                error=str(e)
            ))
    
    async def _test_monitoring_health(self):
        """测试监控服务健康检查"""
        # Prometheus健康检查
        await self._test_prometheus_health()
        
        # Grafana健康检查
        await self._test_grafana_health()
    
    async def _test_prometheus_health(self):
        """测试Prometheus健康检查"""
        test_name = "prometheus_health_check"
        start_time = time.time()
        
        try:
            # 测试Prometheus API
            targets_url = urljoin(self.config.prometheus_url, "/api/v1/targets")
            response = self.session.get(targets_url)
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    targets = data.get("data", {}).get("activeTargets", [])
                    healthy_targets = [t for t in targets if t.get("health") == "up"]
                    
                    self.test_results.append(TestResult(
                        test_name=test_name,
                        category="health_check",
                        status="pass",
                        message="Prometheus health check passed",
                        duration=duration,
                        details={
                            "total_targets": len(targets),
                            "healthy_targets": len(healthy_targets),
                            "targets": targets
                        }
                    ))
                else:
                    self.test_results.append(TestResult(
                        test_name=test_name,
                        category="health_check",
                        status="fail",
                        message="Prometheus API returned error status",
                        duration=duration,
                        details=data
                    ))
            else:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="health_check",
                    status="fail",
                    message=f"Prometheus returned status {response.status_code}",
                    duration=duration,
                    error=response.text
                ))
                
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name=test_name,
                category="health_check",
                status="error",
                message=f"Prometheus health check failed: {str(e)}",
                duration=duration,
                error=str(e)
            ))
    
    async def _test_grafana_health(self):
        """测试Grafana健康检查"""
        test_name = "grafana_health_check"
        start_time = time.time()
        
        try:
            # 测试Grafana健康端点
            health_url = urljoin(self.config.grafana_url, "/api/health")
            response = self.session.get(health_url)
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                health_data = response.json()
                
                if health_data.get("database") == "ok":
                    self.test_results.append(TestResult(
                        test_name=test_name,
                        category="health_check",
                        status="pass",
                        message="Grafana health check passed",
                        duration=duration,
                        details=health_data
                    ))
                else:
                    self.test_results.append(TestResult(
                        test_name=test_name,
                        category="health_check",
                        status="fail",
                        message="Grafana database check failed",
                        duration=duration,
                        details=health_data
                    ))
            else:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="health_check",
                    status="fail",
                    message=f"Grafana returned status {response.status_code}",
                    duration=duration,
                    error=response.text
                ))
                
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name=test_name,
                category="health_check",
                status="error",
                message=f"Grafana health check failed: {str(e)}",
                duration=duration,
                error=str(e)
            ))
    
    async def _run_functional_tests(self):
        """运行功能性端到端测试"""
        self.logger.info("Running functional tests")
        
        # API端点测试
        await self._test_api_endpoints()
        
        # 用户认证流程测试
        await self._test_authentication_flow()
        
        # 数据库操作测试
        await self._test_database_operations()
        
        # 文件上传测试
        await self._test_file_upload()
    
    async def _test_api_endpoints(self):
        """测试API端点"""
        endpoints = [
            ("/api/v1/health", "GET"),
            ("/api/v1/users/me", "GET"),
            ("/api/v1/cases", "GET"),
            ("/api/v1/statistics", "GET")
        ]
        
        for endpoint, method in endpoints:
            test_name = f"api_endpoint_{endpoint.replace('/', '_').replace('-', '_')}"
            start_time = time.time()
            
            try:
                url = urljoin(self.config.base_url, endpoint)
                
                if method == "GET":
                    response = self.session.get(url)
                elif method == "POST":
                    response = self.session.post(url, json={})
                else:
                    continue
                
                duration = time.time() - start_time
                
                # 检查响应状态
                if response.status_code in [200, 401, 403]:  # 401/403 for protected endpoints
                    self.test_results.append(TestResult(
                        test_name=test_name,
                        category="functional",
                        status="pass",
                        message=f"API endpoint {endpoint} responded correctly",
                        duration=duration,
                        details={
                            "status_code": response.status_code,
                            "response_time_ms": duration * 1000
                        }
                    ))
                else:
                    self.test_results.append(TestResult(
                        test_name=test_name,
                        category="functional",
                        status="fail",
                        message=f"API endpoint {endpoint} returned unexpected status {response.status_code}",
                        duration=duration,
                        error=response.text[:500]
                    ))
                    
            except Exception as e:
                duration = time.time() - start_time
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="functional",
                    status="error",
                    message=f"API endpoint {endpoint} test failed: {str(e)}",
                    duration=duration,
                    error=str(e)
                ))
    
    async def _test_authentication_flow(self):
        """测试用户认证流程"""
        test_name = "authentication_flow"
        start_time = time.time()
        
        try:
            # 测试登录端点
            login_url = urljoin(self.config.base_url, "/api/v1/auth/login")
            
            # 尝试无效登录
            invalid_response = self.session.post(login_url, json={
                "username": "invalid_user",
                "password": "invalid_password"
            })
            
            duration = time.time() - start_time
            
            # 应该返回401或400
            if invalid_response.status_code in [400, 401, 422]:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="functional",
                    status="pass",
                    message="Authentication flow test passed - invalid login rejected",
                    duration=duration,
                    details={
                        "invalid_login_status": invalid_response.status_code
                    }
                ))
            else:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="functional",
                    status="fail",
                    message=f"Authentication flow test failed - invalid login returned {invalid_response.status_code}",
                    duration=duration,
                    error=invalid_response.text
                ))
                
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name=test_name,
                category="functional",
                status="error",
                message=f"Authentication flow test failed: {str(e)}",
                duration=duration,
                error=str(e)
            ))
    
    async def _test_database_operations(self):
        """测试数据库操作"""
        test_name = "database_operations"
        start_time = time.time()
        
        try:
            conn = psycopg2.connect(self.config.database_url)
            cursor = conn.cursor()
            
            # 测试基本查询
            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
            table_count = cursor.fetchone()[0]
            
            # 测试事务
            cursor.execute("BEGIN")
            cursor.execute("SELECT 1")
            cursor.execute("ROLLBACK")
            
            cursor.close()
            conn.close()
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=test_name,
                category="functional",
                status="pass",
                message="Database operations test passed",
                duration=duration,
                details={
                    "table_count": table_count,
                    "transaction_test": "passed"
                }
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name=test_name,
                category="functional",
                status="error",
                message=f"Database operations test failed: {str(e)}",
                duration=duration,
                error=str(e)
            ))
    
    async def _test_file_upload(self):
        """测试文件上传功能"""
        test_name = "file_upload"
        start_time = time.time()
        
        try:
            upload_url = urljoin(self.config.base_url, "/api/v1/upload")
            
            # 创建测试文件
            test_content = b"This is a test file for upload verification"
            files = {"file": ("test.txt", test_content, "text/plain")}
            
            response = self.session.post(upload_url, files=files)
            
            duration = time.time() - start_time
            
            # 检查响应（可能需要认证，所以401也是正常的）
            if response.status_code in [200, 201, 401, 403]:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="functional",
                    status="pass",
                    message="File upload endpoint responded correctly",
                    duration=duration,
                    details={
                        "status_code": response.status_code
                    }
                ))
            else:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="functional",
                    status="fail",
                    message=f"File upload endpoint returned unexpected status {response.status_code}",
                    duration=duration,
                    error=response.text[:500]
                ))
                
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name=test_name,
                category="functional",
                status="error",
                message=f"File upload test failed: {str(e)}",
                duration=duration,
                error=str(e)
            ))
    
    async def _run_performance_tests(self):
        """运行性能基准测试"""
        self.logger.info("Running performance tests")
        
        # 响应时间测试
        await self._test_response_times()
        
        # 系统资源使用测试
        await self._test_system_resources()
        
        # 数据库性能测试
        await self._test_database_performance()
        
        # 并发负载测试
        await self._test_concurrent_load()
    
    async def _test_response_times(self):
        """测试响应时间"""
        test_name = "response_times"
        start_time = time.time()
        
        try:
            endpoints = [
                "/api/v1/health",
                "/",
                "/api/v1/statistics"
            ]
            
            response_times = []
            
            for endpoint in endpoints:
                url = urljoin(self.config.base_url, endpoint)
                
                # 测试多次请求
                for _ in range(5):
                    req_start = time.time()
                    response = self.session.get(url)
                    req_duration = (time.time() - req_start) * 1000  # 转换为毫秒
                    
                    if response.status_code < 500:  # 忽略服务器错误
                        response_times.append(req_duration)
            
            duration = time.time() - start_time
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                
                threshold = self.config.performance_thresholds["response_time_ms"]
                
                if avg_response_time <= threshold:
                    self.test_results.append(TestResult(
                        test_name=test_name,
                        category="performance",
                        status="pass",
                        message=f"Response times within threshold ({avg_response_time:.2f}ms avg)",
                        duration=duration,
                        details={
                            "avg_response_time_ms": avg_response_time,
                            "max_response_time_ms": max_response_time,
                            "threshold_ms": threshold,
                            "sample_count": len(response_times)
                        }
                    ))
                else:
                    self.test_results.append(TestResult(
                        test_name=test_name,
                        category="performance",
                        status="fail",
                        message=f"Response times exceed threshold ({avg_response_time:.2f}ms avg > {threshold}ms)",
                        duration=duration,
                        details={
                            "avg_response_time_ms": avg_response_time,
                            "max_response_time_ms": max_response_time,
                            "threshold_ms": threshold
                        }
                    ))
            else:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="performance",
                    status="fail",
                    message="No valid response times collected",
                    duration=duration
                ))
                
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name=test_name,
                category="performance",
                status="error",
                message=f"Response time test failed: {str(e)}",
                duration=duration,
                error=str(e)
            ))
    
    async def _test_system_resources(self):
        """测试系统资源使用"""
        test_name = "system_resources"
        start_time = time.time()
        
        try:
            # 获取系统资源使用情况
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            duration = time.time() - start_time
            
            # 检查阈值
            cpu_threshold = self.config.performance_thresholds["cpu_usage_percent"]
            memory_threshold = self.config.performance_thresholds["memory_usage_percent"]
            disk_threshold = self.config.performance_thresholds["disk_usage_percent"]
            
            issues = []
            if cpu_percent > cpu_threshold:
                issues.append(f"CPU usage {cpu_percent:.1f}% > {cpu_threshold}%")
            if memory.percent > memory_threshold:
                issues.append(f"Memory usage {memory.percent:.1f}% > {memory_threshold}%")
            if disk.percent > disk_threshold:
                issues.append(f"Disk usage {disk.percent:.1f}% > {disk_threshold}%")
            
            if not issues:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="performance",
                    status="pass",
                    message="System resource usage within thresholds",
                    duration=duration,
                    details={
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "disk_percent": disk.percent,
                        "memory_available_gb": memory.available / (1024**3),
                        "disk_free_gb": disk.free / (1024**3)
                    }
                ))
            else:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="performance",
                    status="fail",
                    message=f"System resource usage exceeds thresholds: {', '.join(issues)}",
                    duration=duration,
                    details={
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "disk_percent": disk.percent,
                        "issues": issues
                    }
                ))
                
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name=test_name,
                category="performance",
                status="error",
                message=f"System resources test failed: {str(e)}",
                duration=duration,
                error=str(e)
            ))
    
    async def _test_database_performance(self):
        """测试数据库性能"""
        test_name = "database_performance"
        start_time = time.time()
        
        try:
            conn = psycopg2.connect(self.config.database_url)
            cursor = conn.cursor()
            
            # 测试查询性能
            query_times = []
            
            queries = [
                "SELECT 1",
                "SELECT COUNT(*) FROM information_schema.tables",
                "SELECT version()",
                "SELECT current_timestamp"
            ]
            
            for query in queries:
                query_start = time.time()
                cursor.execute(query)
                cursor.fetchall()
                query_duration = (time.time() - query_start) * 1000  # 转换为毫秒
                query_times.append(query_duration)
            
            cursor.close()
            conn.close()
            
            duration = time.time() - start_time
            
            avg_query_time = sum(query_times) / len(query_times)
            max_query_time = max(query_times)
            
            threshold = self.config.performance_thresholds["database_query_ms"]
            
            if avg_query_time <= threshold:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="performance",
                    status="pass",
                    message=f"Database performance within threshold ({avg_query_time:.2f}ms avg)",
                    duration=duration,
                    details={
                        "avg_query_time_ms": avg_query_time,
                        "max_query_time_ms": max_query_time,
                        "threshold_ms": threshold,
                        "query_count": len(query_times)
                    }
                ))
            else:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="performance",
                    status="fail",
                    message=f"Database performance exceeds threshold ({avg_query_time:.2f}ms avg > {threshold}ms)",
                    duration=duration,
                    details={
                        "avg_query_time_ms": avg_query_time,
                        "max_query_time_ms": max_query_time,
                        "threshold_ms": threshold
                    }
                ))
                
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name=test_name,
                category="performance",
                status="error",
                message=f"Database performance test failed: {str(e)}",
                duration=duration,
                error=str(e)
            ))
    
    async def _test_concurrent_load(self):
        """测试并发负载"""
        test_name = "concurrent_load"
        start_time = time.time()
        
        try:
            # 并发请求测试
            concurrent_requests = 10
            url = urljoin(self.config.base_url, "/api/v1/health")
            
            async def make_request():
                try:
                    req_start = time.time()
                    response = self.session.get(url)
                    req_duration = time.time() - req_start
                    return {
                        "status_code": response.status_code,
                        "duration": req_duration,
                        "success": response.status_code < 500
                    }
                except Exception as e:
                    return {
                        "status_code": 0,
                        "duration": 0,
                        "success": False,
                        "error": str(e)
                    }
            
            # 使用线程池执行并发请求
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
                futures = [executor.submit(asyncio.run, make_request()) for _ in range(concurrent_requests)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            duration = time.time() - start_time
            
            successful_requests = sum(1 for r in results if r["success"])
            avg_response_time = sum(r["duration"] for r in results if r["success"]) / max(successful_requests, 1)
            
            success_rate = successful_requests / concurrent_requests * 100
            
            if success_rate >= 90:  # 90%成功率阈值
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="performance",
                    status="pass",
                    message=f"Concurrent load test passed ({success_rate:.1f}% success rate)",
                    duration=duration,
                    details={
                        "concurrent_requests": concurrent_requests,
                        "successful_requests": successful_requests,
                        "success_rate_percent": success_rate,
                        "avg_response_time": avg_response_time
                    }
                ))
            else:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="performance",
                    status="fail",
                    message=f"Concurrent load test failed ({success_rate:.1f}% success rate < 90%)",
                    duration=duration,
                    details={
                        "concurrent_requests": concurrent_requests,
                        "successful_requests": successful_requests,
                        "success_rate_percent": success_rate,
                        "results": results
                    }
                ))
                
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name=test_name,
                category="performance",
                status="error",
                message=f"Concurrent load test failed: {str(e)}",
                duration=duration,
                error=str(e)
            ))
    
    async def _run_security_tests(self):
        """运行安全配置验证测试"""
        self.logger.info("Running security tests")
        
        # SSL证书验证
        await self._test_ssl_certificates()
        
        # 安全头检查
        await self._test_security_headers()
        
        # 端口安全检查
        await self._test_port_security()
        
        # 文件权限检查
        await self._test_file_permissions()
    
    async def _test_ssl_certificates(self):
        """测试SSL证书"""
        for domain in self.config.domains:
            test_name = f"ssl_certificate_{domain.replace('.', '_')}"
            start_time = time.time()
            
            try:
                # 连接到域名并获取证书
                context = ssl.create_default_context()
                
                with socket.create_connection((domain, 443), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=domain) as ssock:
                        cert_der = ssock.getpeercert_chain()[0]
                        cert = x509.load_der_x509_certificate(cert_der, default_backend())
                        
                        # 检查证书有效期
                        now = datetime.now()
                        expires_at = cert.not_valid_after
                        days_until_expiry = (expires_at - now).days
                        
                        duration = time.time() - start_time
                        
                        if days_until_expiry > 7:  # 至少7天有效期
                            self.test_results.append(TestResult(
                                test_name=test_name,
                                category="security",
                                status="pass",
                                message=f"SSL certificate for {domain} is valid",
                                duration=duration,
                                details={
                                    "domain": domain,
                                    "expires_at": expires_at.isoformat(),
                                    "days_until_expiry": days_until_expiry,
                                    "issuer": cert.issuer.rfc4514_string()
                                }
                            ))
                        else:
                            self.test_results.append(TestResult(
                                test_name=test_name,
                                category="security",
                                status="fail",
                                message=f"SSL certificate for {domain} expires soon ({days_until_expiry} days)",
                                duration=duration,
                                details={
                                    "domain": domain,
                                    "days_until_expiry": days_until_expiry
                                }
                            ))
                            
            except Exception as e:
                duration = time.time() - start_time
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="security",
                    status="error",
                    message=f"SSL certificate test for {domain} failed: {str(e)}",
                    duration=duration,
                    error=str(e)
                ))
    
    async def _test_security_headers(self):
        """测试安全头"""
        test_name = "security_headers"
        start_time = time.time()
        
        try:
            response = self.session.get(self.config.base_url)
            
            duration = time.time() - start_time
            
            # 检查重要的安全头
            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": None,  # 任何值都可以
                "Content-Security-Policy": None
            }
            
            missing_headers = []
            present_headers = {}
            
            for header, expected_value in security_headers.items():
                actual_value = response.headers.get(header)
                present_headers[header] = actual_value
                
                if actual_value is None:
                    missing_headers.append(header)
                elif expected_value and isinstance(expected_value, list):
                    if actual_value not in expected_value:
                        missing_headers.append(f"{header} (invalid value)")
                elif expected_value and actual_value != expected_value:
                    missing_headers.append(f"{header} (invalid value)")
            
            if not missing_headers:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="security",
                    status="pass",
                    message="All security headers are present",
                    duration=duration,
                    details={"headers": present_headers}
                ))
            else:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="security",
                    status="fail",
                    message=f"Missing or invalid security headers: {', '.join(missing_headers)}",
                    duration=duration,
                    details={
                        "headers": present_headers,
                        "missing_headers": missing_headers
                    }
                ))
                
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name=test_name,
                category="security",
                status="error",
                message=f"Security headers test failed: {str(e)}",
                duration=duration,
                error=str(e)
            ))
    
    async def _test_port_security(self):
        """测试端口安全"""
        test_name = "port_security"
        start_time = time.time()
        
        try:
            # 检查开放的端口
            connections = psutil.net_connections(kind='inet')
            listening_ports = set()
            
            for conn in connections:
                if conn.status == 'LISTEN':
                    listening_ports.add(conn.laddr.port)
            
            duration = time.time() - start_time
            
            # 定义允许的端口
            allowed_ports = {22, 80, 443, 5432, 6379, 8000, 9090, 3000}  # SSH, HTTP, HTTPS, PostgreSQL, Redis, App, Prometheus, Grafana
            
            # 检查是否有不应该开放的端口
            unexpected_ports = listening_ports - allowed_ports
            
            # 过滤掉高端口（通常是临时端口）
            unexpected_ports = {port for port in unexpected_ports if port < 10000}
            
            if not unexpected_ports:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="security",
                    status="pass",
                    message="Port security check passed",
                    duration=duration,
                    details={
                        "listening_ports": sorted(list(listening_ports)),
                        "allowed_ports": sorted(list(allowed_ports))
                    }
                ))
            else:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="security",
                    status="fail",
                    message=f"Unexpected ports are listening: {sorted(list(unexpected_ports))}",
                    duration=duration,
                    details={
                        "listening_ports": sorted(list(listening_ports)),
                        "unexpected_ports": sorted(list(unexpected_ports))
                    }
                ))
                
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name=test_name,
                category="security",
                status="error",
                message=f"Port security test failed: {str(e)}",
                duration=duration,
                error=str(e)
            ))
    
    async def _test_file_permissions(self):
        """测试文件权限"""
        test_name = "file_permissions"
        start_time = time.time()
        
        try:
            # 检查关键文件的权限
            critical_files = [
                ("/etc/passwd", 0o644),
                ("/etc/shadow", 0o640),
                ("/etc/ssh/sshd_config", 0o644),
            ]
            
            permission_issues = []
            
            for file_path, expected_mode in critical_files:
                try:
                    if os.path.exists(file_path):
                        actual_mode = os.stat(file_path).st_mode & 0o777
                        if actual_mode != expected_mode:
                            permission_issues.append(f"{file_path}: {oct(actual_mode)} (expected {oct(expected_mode)})")
                except PermissionError:
                    # 无法访问文件，可能是权限限制，这是好事
                    pass
            
            duration = time.time() - start_time
            
            if not permission_issues:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="security",
                    status="pass",
                    message="File permissions check passed",
                    duration=duration,
                    details={"checked_files": [f[0] for f in critical_files]}
                ))
            else:
                self.test_results.append(TestResult(
                    test_name=test_name,
                    category="security",
                    status="fail",
                    message=f"File permission issues: {', '.join(permission_issues)}",
                    duration=duration,
                    details={"permission_issues": permission_issues}
                ))
                
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name=test_name,
                category="security",
                status="error",
                message=f"File permissions test failed: {str(e)}",
                duration=duration,
                error=str(e)
            ))
    
    def _generate_test_report(self, total_duration: float) -> Dict[str, Any]:
        """生成测试报告"""
        # 按类别统计结果
        categories = {}
        for result in self.test_results:
            category = result.category
            if category not in categories:
                categories[category] = {"pass": 0, "fail": 0, "error": 0, "skip": 0}
            categories[category][result.status] += 1
        
        # 总体统计
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.status == "pass")
        failed_tests = sum(1 for r in self.test_results if r.status == "fail")
        error_tests = sum(1 for r in self.test_results if r.status == "error")
        skipped_tests = sum(1 for r in self.test_results if r.status == "skip")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # 生成报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_duration": total_duration,
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "skipped": skipped_tests,
                "success_rate": success_rate
            },
            "categories": categories,
            "test_results": [result.to_dict() for result in self.test_results],
            "config": asdict(self.config)
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_path: str = None):
        """保存测试报告"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"deployment_verification_report_{timestamp}.json"
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Test report saved to: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save test report: {str(e)}")


# 工厂函数
def create_verification_suite(
    base_url: str = "http://localhost:8000",
    domains: List[str] = None,
    database_url: str = None,
    **kwargs
) -> DeploymentVerificationSuite:
    """
    创建部署验证测试套件
    
    Args:
        base_url: 应用基础URL
        domains: 要测试的域名列表
        database_url: 数据库连接URL
        **kwargs: 其他配置参数
        
    Returns:
        DeploymentVerificationSuite实例
    """
    config = VerificationConfig(
        base_url=base_url,
        domains=domains or ["lawsker.com"],
        database_url=database_url or "postgresql://lawsker_user:password@localhost:5432/lawsker_prod",
        **kwargs
    )
    
    return DeploymentVerificationSuite(config)


# 主函数用于测试
async def main():
    """主函数用于测试验证套件"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deployment Verification Suite')
    parser.add_argument('--base-url', default='http://localhost:8000', help='Base URL for testing')
    parser.add_argument('--domains', nargs='+', default=['lawsker.com'], help='Domains to test')
    parser.add_argument('--database-url', help='Database URL for testing')
    parser.add_argument('--output', help='Output file for test report')
    
    args = parser.parse_args()
    
    # 创建验证套件
    suite = create_verification_suite(
        base_url=args.base_url,
        domains=args.domains,
        database_url=args.database_url
    )
    
    try:
        # 运行所有测试
        report = await suite.run_all_tests()
        
        # 保存报告
        suite.save_report(report, args.output)
        
        # 打印摘要
        summary = report["summary"]
        print(f"\nTest Results Summary:")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Errors: {summary['errors']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        
        # 根据测试结果设置退出码
        if summary['failed'] == 0 and summary['errors'] == 0:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"Verification suite failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())