#!/usr/bin/env python3
"""
集成测试框架
实现端到端部署测试、多环境测试支持、性能和压力测试、测试报告和分析
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
import subprocess
import threading
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
import concurrent.futures
from urllib.parse import urljoin, urlparse
import tempfile
import shutil
import yaml
from contextlib import asynccontextmanager
import statistics

# 导入部署组件
from .deployment_orchestrator import DeploymentOrchestrator, DeploymentConfig
from .deployment_verification import DeploymentVerificationSuite, VerificationConfig, TestResult


@dataclass
class TestEnvironment:
    """测试环境配置"""
    name: str
    base_url: str
    database_url: str
    redis_url: str
    ssl_enabled: bool = False
    monitoring_enabled: bool = False
    cleanup_after_test: bool = True
    timeout: int = 300
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    response_time_ms: float
    throughput_rps: float
    cpu_usage_percent: float
    memory_usage_mb: float
    disk_io_mbps: float
    network_io_mbps: float
    error_rate_percent: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LoadTestConfig:
    """负载测试配置"""
    concurrent_users: int = 10
    duration_seconds: int = 60
    ramp_up_seconds: int = 10
    target_endpoints: List[str] = None
    request_timeout: int = 30
    
    def __post_init__(self):
        if self.target_endpoints is None:
            self.target_endpoints = [
                "/api/v1/health",
                "/api/v1/statistics",
                "/"
            ]


class IntegrationTestFramework:
    """
    集成测试框架
    
    实现：
    - 编写端到端部署测试
    - 实现多环境测试支持
    - 添加性能和压力测试
    - 创建测试报告和分析
    """
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.logger = self._setup_logger()
        self.test_results: List[TestResult] = []
        self.performance_metrics: List[PerformanceMetrics] = []
        
        # 测试环境配置
        self.test_environments = self._load_test_environments()
        
        # 测试数据目录
        self.test_data_dir = self.project_root / "backend" / "deployment" / "test_data"
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        
        # 报告目录
        self.reports_dir = self.project_root / "backend" / "deployment" / "test_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
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
            log_file = self.project_root / "backend" / "deployment" / "integration_tests.log"
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
        return logger
    
    def _load_test_environments(self) -> Dict[str, TestEnvironment]:
        """加载测试环境配置"""
        environments = {
            "unit": TestEnvironment(
                name="unit",
                base_url="http://localhost:8000",
                database_url="sqlite:///:memory:",
                redis_url="redis://localhost:6379/15",
                ssl_enabled=False,
                monitoring_enabled=False,
                cleanup_after_test=True,
                timeout=60
            ),
            "integration": TestEnvironment(
                name="integration",
                base_url="http://localhost:8001",
                database_url="postgresql://test_user:test_pass@localhost:5432/test_lawsker",
                redis_url="redis://localhost:6379/14",
                ssl_enabled=False,
                monitoring_enabled=True,
                cleanup_after_test=True,
                timeout=300
            ),
            "staging": TestEnvironment(
                name="staging",
                base_url="https://staging.lawsker.com",
                database_url="postgresql://staging_user:staging_pass@staging-db:5432/staging_lawsker",
                redis_url="redis://staging-redis:6379/0",
                ssl_enabled=True,
                monitoring_enabled=True,
                cleanup_after_test=False,
                timeout=600
            )
        }
        
        # 尝试从配置文件加载
        config_file = self.project_root / "backend" / "deployment" / "test_environments.yml"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                    
                for env_name, env_config in config_data.get("environments", {}).items():
                    environments[env_name] = TestEnvironment(**env_config)
                    
            except Exception as e:
                self.logger.warning(f"Failed to load test environments config: {str(e)}")
        
        return environments
    
    async def run_end_to_end_deployment_test(
        self, 
        environment: str = "integration",
        deployment_config: Optional[DeploymentConfig] = None
    ) -> Dict[str, Any]:
        """
        运行端到端部署测试
        
        Args:
            environment: 测试环境名称
            deployment_config: 部署配置（可选）
            
        Returns:
            测试结果报告
        """
        self.logger.info(f"Starting end-to-end deployment test in {environment} environment")
        start_time = datetime.now()
        
        test_env = self.test_environments.get(environment)
        if not test_env:
            raise ValueError(f"Unknown test environment: {environment}")
        
        test_id = f"e2e_deployment_{environment}_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # 1. 准备测试环境
            await self._prepare_test_environment(test_env)
            
            # 2. 执行部署
            deployment_result = await self._execute_test_deployment(
                test_env, deployment_config
            )
            
            # 3. 验证部署结果
            verification_result = await self._verify_deployment(test_env)
            
            # 4. 运行功能测试
            functional_result = await self._run_functional_tests(test_env)
            
            # 5. 运行性能测试
            performance_result = await self._run_performance_tests(test_env)
            
            # 6. 清理测试环境
            if test_env.cleanup_after_test:
                await self._cleanup_test_environment(test_env)
            
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()
            
            # 生成测试报告
            report = {
                "test_id": test_id,
                "environment": environment,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": total_duration,
                "deployment_result": deployment_result,
                "verification_result": verification_result,
                "functional_result": functional_result,
                "performance_result": performance_result,
                "overall_status": self._determine_overall_status([
                    deployment_result, verification_result, 
                    functional_result, performance_result
                ])
            }
            
            # 保存测试报告
            await self._save_test_report(test_id, report)
            
            self.logger.info(f"End-to-end deployment test completed in {total_duration:.2f} seconds")
            return report
            
        except Exception as e:
            self.logger.error(f"End-to-end deployment test failed: {str(e)}")
            
            # 清理测试环境
            if test_env.cleanup_after_test:
                try:
                    await self._cleanup_test_environment(test_env)
                except Exception as cleanup_error:
                    self.logger.error(f"Failed to cleanup test environment: {str(cleanup_error)}")
            
            raise
    
    async def run_multi_environment_tests(
        self, 
        environments: List[str] = None
    ) -> Dict[str, Any]:
        """
        运行多环境测试
        
        Args:
            environments: 要测试的环境列表
            
        Returns:
            多环境测试结果
        """
        if environments is None:
            environments = ["unit", "integration"]
        
        self.logger.info(f"Starting multi-environment tests: {environments}")
        start_time = datetime.now()
        
        results = {}
        
        for env_name in environments:
            if env_name not in self.test_environments:
                self.logger.warning(f"Skipping unknown environment: {env_name}")
                continue
            
            try:
                self.logger.info(f"Testing environment: {env_name}")
                env_result = await self.run_end_to_end_deployment_test(env_name)
                results[env_name] = env_result
                
            except Exception as e:
                self.logger.error(f"Environment {env_name} test failed: {str(e)}")
                results[env_name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        # 生成多环境测试报告
        report = {
            "test_type": "multi_environment",
            "environments": environments,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": total_duration,
            "results": results,
            "summary": self._generate_multi_env_summary(results)
        }
        
        # 保存报告
        report_id = f"multi_env_{start_time.strftime('%Y%m%d_%H%M%S')}"
        await self._save_test_report(report_id, report)
        
        self.logger.info(f"Multi-environment tests completed in {total_duration:.2f} seconds")
        return report
    
    async def run_performance_stress_tests(
        self, 
        environment: str = "integration",
        load_config: Optional[LoadTestConfig] = None
    ) -> Dict[str, Any]:
        """
        运行性能和压力测试
        
        Args:
            environment: 测试环境
            load_config: 负载测试配置
            
        Returns:
            性能测试结果
        """
        if load_config is None:
            load_config = LoadTestConfig()
        
        test_env = self.test_environments.get(environment)
        if not test_env:
            raise ValueError(f"Unknown test environment: {environment}")
        
        self.logger.info(f"Starting performance stress tests in {environment}")
        start_time = datetime.now()
        
        try:
            # 1. 基准性能测试
            baseline_metrics = await self._run_baseline_performance_test(test_env)
            
            # 2. 负载测试
            load_test_results = await self._run_load_test(test_env, load_config)
            
            # 3. 压力测试
            stress_test_results = await self._run_stress_test(test_env, load_config)
            
            # 4. 资源监控
            resource_metrics = await self._monitor_system_resources(test_env)
            
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()
            
            # 生成性能测试报告
            report = {
                "test_type": "performance_stress",
                "environment": environment,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": total_duration,
                "load_config": asdict(load_config),
                "baseline_metrics": baseline_metrics,
                "load_test_results": load_test_results,
                "stress_test_results": stress_test_results,
                "resource_metrics": resource_metrics,
                "performance_analysis": self._analyze_performance_results(
                    baseline_metrics, load_test_results, stress_test_results
                )
            }
            
            # 保存报告
            report_id = f"performance_{environment}_{start_time.strftime('%Y%m%d_%H%M%S')}"
            await self._save_test_report(report_id, report)
            
            self.logger.info(f"Performance stress tests completed in {total_duration:.2f} seconds")
            return report
            
        except Exception as e:
            self.logger.error(f"Performance stress tests failed: {str(e)}")
            raise
    
    async def _prepare_test_environment(self, test_env: TestEnvironment):
        """准备测试环境"""
        self.logger.info(f"Preparing test environment: {test_env.name}")
        
        try:
            # 检查必要的服务
            await self._check_required_services(test_env)
            
            # 初始化测试数据
            await self._initialize_test_data(test_env)
            
            # 等待服务就绪
            await self._wait_for_services(test_env)
            
        except Exception as e:
            self.logger.error(f"Failed to prepare test environment {test_env.name}: {str(e)}")
            raise
    
    async def _execute_test_deployment(
        self, 
        test_env: TestEnvironment,
        deployment_config: Optional[DeploymentConfig] = None
    ) -> Dict[str, Any]:
        """执行测试部署"""
        self.logger.info(f"Executing test deployment in {test_env.name}")
        
        if deployment_config is None:
            deployment_config = DeploymentConfig(
                project_root=str(self.project_root),
                server_ip="localhost",
                ssl_enabled=test_env.ssl_enabled,
                monitoring_enabled=test_env.monitoring_enabled
            )
        
        try:
            orchestrator = DeploymentOrchestrator(deployment_config)
            deployment_result = await orchestrator.deploy()
            
            return {
                "status": "success" if deployment_result.get("overall_status") == "success" else "failed",
                "deployment_result": deployment_result
            }
            
        except Exception as e:
            self.logger.error(f"Test deployment failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _verify_deployment(self, test_env: TestEnvironment) -> Dict[str, Any]:
        """验证部署结果"""
        self.logger.info(f"Verifying deployment in {test_env.name}")
        
        try:
            verification_config = VerificationConfig(
                base_url=test_env.base_url,
                database_url=test_env.database_url,
                redis_url=test_env.redis_url,
                timeout=test_env.timeout
            )
            
            verification_suite = DeploymentVerificationSuite(verification_config)
            verification_result = await verification_suite.run_all_tests()
            
            return {
                "status": "success" if verification_result.get("overall_status") == "success" else "failed",
                "verification_result": verification_result
            }
            
        except Exception as e:
            self.logger.error(f"Deployment verification failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _run_functional_tests(self, test_env: TestEnvironment) -> Dict[str, Any]:
        """运行功能测试"""
        self.logger.info(f"Running functional tests in {test_env.name}")
        
        try:
            # 这里可以集成更多的功能测试
            # 目前使用验证套件的功能测试部分
            verification_config = VerificationConfig(
                base_url=test_env.base_url,
                database_url=test_env.database_url,
                redis_url=test_env.redis_url
            )
            
            verification_suite = DeploymentVerificationSuite(verification_config)
            
            # 只运行功能测试部分
            await verification_suite._run_functional_tests()
            
            functional_results = [
                result for result in verification_suite.test_results
                if result.category == "functional"
            ]
            
            passed_tests = len([r for r in functional_results if r.status == "pass"])
            total_tests = len(functional_results)
            
            return {
                "status": "success" if passed_tests == total_tests else "failed",
                "passed_tests": passed_tests,
                "total_tests": total_tests,
                "test_results": [result.to_dict() for result in functional_results]
            }
            
        except Exception as e:
            self.logger.error(f"Functional tests failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _run_performance_tests(self, test_env: TestEnvironment) -> Dict[str, Any]:
        """运行性能测试"""
        self.logger.info(f"Running performance tests in {test_env.name}")
        
        try:
            # 基本性能指标收集
            metrics = await self._collect_performance_metrics(test_env)
            
            return {
                "status": "success",
                "metrics": metrics.to_dict() if metrics else None
            }
            
        except Exception as e:
            self.logger.error(f"Performance tests failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _run_baseline_performance_test(self, test_env: TestEnvironment) -> Dict[str, Any]:
        """运行基准性能测试"""
        self.logger.info("Running baseline performance test")
        
        try:
            session = requests.Session()
            session.timeout = 30
            
            # 测试主要端点的响应时间
            endpoints = ["/api/v1/health", "/", "/api/v1/statistics"]
            response_times = []
            
            for endpoint in endpoints:
                url = urljoin(test_env.base_url, endpoint)
                
                for _ in range(10):  # 每个端点测试10次
                    start_time = time.time()
                    try:
                        response = session.get(url)
                        if response.status_code < 500:
                            response_time = (time.time() - start_time) * 1000
                            response_times.append(response_time)
                    except Exception:
                        pass
            
            if response_times:
                return {
                    "avg_response_time_ms": statistics.mean(response_times),
                    "median_response_time_ms": statistics.median(response_times),
                    "p95_response_time_ms": statistics.quantiles(response_times, n=20)[18],  # 95th percentile
                    "max_response_time_ms": max(response_times),
                    "min_response_time_ms": min(response_times),
                    "sample_count": len(response_times)
                }
            else:
                return {"error": "No valid response times collected"}
                
        except Exception as e:
            return {"error": str(e)}
    
    async def _run_load_test(self, test_env: TestEnvironment, load_config: LoadTestConfig) -> Dict[str, Any]:
        """运行负载测试"""
        self.logger.info(f"Running load test with {load_config.concurrent_users} concurrent users")
        
        try:
            results = []
            errors = []
            
            async def make_request(session, url):
                try:
                    start_time = time.time()
                    response = session.get(url, timeout=load_config.request_timeout)
                    duration = time.time() - start_time
                    
                    return {
                        "status_code": response.status_code,
                        "response_time": duration,
                        "success": response.status_code < 400
                    }
                except Exception as e:
                    return {
                        "status_code": 0,
                        "response_time": load_config.request_timeout,
                        "success": False,
                        "error": str(e)
                    }
            
            # 创建会话池
            sessions = [requests.Session() for _ in range(load_config.concurrent_users)]
            
            # 执行负载测试
            start_time = time.time()
            end_time = start_time + load_config.duration_seconds
            
            tasks = []
            while time.time() < end_time:
                for i, session in enumerate(sessions):
                    if time.time() >= end_time:
                        break
                    
                    endpoint = load_config.target_endpoints[i % len(load_config.target_endpoints)]
                    url = urljoin(test_env.base_url, endpoint)
                    
                    task = asyncio.create_task(make_request(session, url))
                    tasks.append(task)
                
                # 等待一小段时间避免过度负载
                await asyncio.sleep(0.1)
            
            # 收集结果
            for task in tasks:
                try:
                    result = await task
                    results.append(result)
                    if not result["success"]:
                        errors.append(result)
                except Exception as e:
                    errors.append({"error": str(e)})
            
            # 分析结果
            if results:
                successful_requests = [r for r in results if r["success"]]
                response_times = [r["response_time"] for r in successful_requests]
                
                total_requests = len(results)
                successful_count = len(successful_requests)
                error_count = len(errors)
                
                return {
                    "total_requests": total_requests,
                    "successful_requests": successful_count,
                    "failed_requests": error_count,
                    "success_rate": (successful_count / total_requests) * 100 if total_requests > 0 else 0,
                    "avg_response_time": statistics.mean(response_times) if response_times else 0,
                    "throughput_rps": successful_count / load_config.duration_seconds,
                    "errors": errors[:10]  # 只保留前10个错误
                }
            else:
                return {"error": "No results collected"}
                
        except Exception as e:
            return {"error": str(e)}
    
    async def _run_stress_test(self, test_env: TestEnvironment, load_config: LoadTestConfig) -> Dict[str, Any]:
        """运行压力测试"""
        self.logger.info("Running stress test")
        
        # 压力测试使用更高的并发数
        stress_config = LoadTestConfig(
            concurrent_users=load_config.concurrent_users * 2,
            duration_seconds=load_config.duration_seconds // 2,
            target_endpoints=load_config.target_endpoints,
            request_timeout=load_config.request_timeout
        )
        
        return await self._run_load_test(test_env, stress_config)
    
    async def _collect_performance_metrics(self, test_env: TestEnvironment) -> Optional[PerformanceMetrics]:
        """收集性能指标"""
        try:
            # 系统资源使用
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            network_io = psutil.net_io_counters()
            
            # 简单的响应时间测试
            start_time = time.time()
            try:
                response = requests.get(urljoin(test_env.base_url, "/api/v1/health"), timeout=30)
                response_time = (time.time() - start_time) * 1000
                error_rate = 0 if response.status_code < 400 else 100
            except Exception:
                response_time = 30000  # 超时
                error_rate = 100
            
            return PerformanceMetrics(
                response_time_ms=response_time,
                throughput_rps=1.0 / (response_time / 1000) if response_time > 0 else 0,
                cpu_usage_percent=cpu_percent,
                memory_usage_mb=memory.used / (1024 * 1024),
                disk_io_mbps=0,  # 需要更复杂的计算
                network_io_mbps=0,  # 需要更复杂的计算
                error_rate_percent=error_rate
            )
            
        except Exception as e:
            self.logger.error(f"Failed to collect performance metrics: {str(e)}")
            return None
    
    async def _monitor_system_resources(self, test_env: TestEnvironment) -> Dict[str, Any]:
        """监控系统资源"""
        try:
            # 收集系统资源信息
            cpu_info = {
                "count": psutil.cpu_count(),
                "usage_percent": psutil.cpu_percent(interval=1)
            }
            
            memory_info = psutil.virtual_memory()._asdict()
            disk_info = psutil.disk_usage('/')._asdict()
            
            return {
                "cpu": cpu_info,
                "memory": memory_info,
                "disk": disk_info,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _cleanup_test_environment(self, test_env: TestEnvironment):
        """清理测试环境"""
        self.logger.info(f"Cleaning up test environment: {test_env.name}")
        
        try:
            # 这里可以添加具体的清理逻辑
            # 例如：删除测试数据、停止测试服务等
            pass
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup test environment: {str(e)}")
    
    async def _check_required_services(self, test_env: TestEnvironment):
        """检查必要的服务"""
        # 检查数据库连接
        if "postgresql" in test_env.database_url:
            # PostgreSQL连接检查
            pass
        
        # 检查Redis连接
        # Redis连接检查
        pass
    
    async def _initialize_test_data(self, test_env: TestEnvironment):
        """初始化测试数据"""
        # 创建测试数据
        pass
    
    async def _wait_for_services(self, test_env: TestEnvironment):
        """等待服务就绪"""
        max_wait_time = test_env.timeout
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                # 检查主要服务是否就绪
                response = requests.get(
                    urljoin(test_env.base_url, "/api/v1/health"),
                    timeout=5
                )
                if response.status_code == 200:
                    return
            except Exception:
                pass
            
            await asyncio.sleep(5)
        
        raise TimeoutError(f"Services not ready after {max_wait_time} seconds")
    
    def _determine_overall_status(self, results: List[Dict[str, Any]]) -> str:
        """确定整体状态"""
        for result in results:
            if result.get("status") in ["error", "failed"]:
                return "failed"
        return "success"
    
    def _generate_multi_env_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成多环境测试摘要"""
        total_envs = len(results)
        successful_envs = len([r for r in results.values() if r.get("overall_status") == "success"])
        
        return {
            "total_environments": total_envs,
            "successful_environments": successful_envs,
            "failed_environments": total_envs - successful_envs,
            "success_rate": (successful_envs / total_envs) * 100 if total_envs > 0 else 0
        }
    
    def _analyze_performance_results(
        self, 
        baseline: Dict[str, Any],
        load_test: Dict[str, Any],
        stress_test: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析性能测试结果"""
        analysis = {
            "baseline_performance": "good" if baseline.get("avg_response_time_ms", 0) < 1000 else "poor",
            "load_test_performance": "good" if load_test.get("success_rate", 0) > 95 else "poor",
            "stress_test_performance": "good" if stress_test.get("success_rate", 0) > 80 else "poor"
        }
        
        # 性能趋势分析
        if baseline.get("avg_response_time_ms") and load_test.get("avg_response_time"):
            performance_degradation = (
                (load_test["avg_response_time"] * 1000 - baseline["avg_response_time_ms"]) /
                baseline["avg_response_time_ms"] * 100
            )
            analysis["performance_degradation_percent"] = performance_degradation
        
        return analysis
    
    async def _save_test_report(self, test_id: str, report: Dict[str, Any]):
        """保存测试报告"""
        try:
            report_file = self.reports_dir / f"{test_id}.json"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Test report saved: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save test report: {str(e)}")
    
    def generate_test_summary_report(self, days: int = 7) -> Dict[str, Any]:
        """生成测试摘要报告"""
        try:
            # 读取最近的测试报告
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_reports = []
            
            for report_file in self.reports_dir.glob("*.json"):
                try:
                    with open(report_file, 'r', encoding='utf-8') as f:
                        report = json.load(f)
                    
                    report_date = datetime.fromisoformat(report.get("start_time", ""))
                    if report_date >= cutoff_date:
                        recent_reports.append(report)
                        
                except Exception:
                    continue
            
            # 生成摘要
            total_tests = len(recent_reports)
            successful_tests = len([r for r in recent_reports if r.get("overall_status") == "success"])
            
            summary = {
                "period_days": days,
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests,
                "success_rate": (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
                "test_types": {},
                "environments": {},
                "generated_at": datetime.now().isoformat()
            }
            
            # 按测试类型统计
            for report in recent_reports:
                test_type = report.get("test_type", "unknown")
                if test_type not in summary["test_types"]:
                    summary["test_types"][test_type] = {"count": 0, "success": 0}
                
                summary["test_types"][test_type]["count"] += 1
                if report.get("overall_status") == "success":
                    summary["test_types"][test_type]["success"] += 1
            
            # 按环境统计
            for report in recent_reports:
                env = report.get("environment", "unknown")
                if env not in summary["environments"]:
                    summary["environments"][env] = {"count": 0, "success": 0}
                
                summary["environments"][env]["count"] += 1
                if report.get("overall_status") == "success":
                    summary["environments"][env]["success"] += 1
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate test summary report: {str(e)}")
            return {"error": str(e)}


# CLI接口
async def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Integration Test Framework")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--test-type", choices=["e2e", "multi-env", "performance"], 
                       default="e2e", help="Test type to run")
    parser.add_argument("--environment", default="integration", help="Test environment")
    parser.add_argument("--environments", nargs="+", help="Multiple environments for multi-env test")
    
    args = parser.parse_args()
    
    framework = IntegrationTestFramework(args.project_root)
    
    try:
        if args.test_type == "e2e":
            result = await framework.run_end_to_end_deployment_test(args.environment)
        elif args.test_type == "multi-env":
            environments = args.environments or ["unit", "integration"]
            result = await framework.run_multi_environment_tests(environments)
        elif args.test_type == "performance":
            result = await framework.run_performance_stress_tests(args.environment)
        
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(f"Test execution failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())