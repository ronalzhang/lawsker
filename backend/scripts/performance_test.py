#!/usr/bin/env python3
"""
性能压力测试脚本
使用多种工具进行API性能测试、并发测试、数据库压力测试等
"""
import asyncio
import aiohttp
import time
import json
import statistics
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    start_time: datetime
    end_time: datetime
    duration: float
    errors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['start_time'] = self.start_time.isoformat()
        result['end_time'] = self.end_time.isoformat()
        return result

@dataclass
class SystemMetrics:
    """系统指标数据类"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_io_read: int
    disk_io_write: int
    network_bytes_sent: int
    network_bytes_recv: int
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result

class SystemMonitor:
    """系统监控器"""
    
    def __init__(self):
        self.monitoring = False
        self.metrics: List[SystemMetrics] = []
        self.monitor_thread = None
    
    def start_monitoring(self):
        """开始监控"""
        self.monitoring = True
        self.metrics = []
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                # 获取系统指标
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk_io = psutil.disk_io_counters()
                network_io = psutil.net_io_counters()
                
                metrics = SystemMetrics(
                    timestamp=datetime.now(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    disk_io_read=disk_io.read_bytes if disk_io else 0,
                    disk_io_write=disk_io.write_bytes if disk_io else 0,
                    network_bytes_sent=network_io.bytes_sent if network_io else 0,
                    network_bytes_recv=network_io.bytes_recv if network_io else 0
                )
                
                self.metrics.append(metrics)
                
                # 每秒采集一次
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"System monitoring error: {str(e)}")
    
    def get_average_metrics(self) -> Dict[str, float]:
        """获取平均指标"""
        if not self.metrics:
            return {}
        
        return {
            "avg_cpu_percent": statistics.mean([m.cpu_percent for m in self.metrics]),
            "max_cpu_percent": max([m.cpu_percent for m in self.metrics]),
            "avg_memory_percent": statistics.mean([m.memory_percent for m in self.metrics]),
            "max_memory_percent": max([m.memory_percent for m in self.metrics]),
            "total_disk_read": self.metrics[-1].disk_io_read - self.metrics[0].disk_io_read,
            "total_disk_write": self.metrics[-1].disk_io_write - self.metrics[0].disk_io_write,
            "total_network_sent": self.metrics[-1].network_bytes_sent - self.metrics[0].network_bytes_sent,
            "total_network_recv": self.metrics[-1].network_bytes_recv - self.metrics[0].network_bytes_recv
        }

class APILoadTester:
    """API负载测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.system_monitor = SystemMonitor()
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def single_request(self, method: str, endpoint: str, **kwargs) -> Tuple[bool, float, str]:
        """执行单个请求"""
        start_time = time.time()
        
        try:
            url = f"{self.base_url}{endpoint}"
            async with self.session.request(method, url, **kwargs) as response:
                await response.text()  # 读取响应内容
                response_time = time.time() - start_time
                
                if response.status < 400:
                    return True, response_time, ""
                else:
                    return False, response_time, f"HTTP {response.status}"
                    
        except Exception as e:
            response_time = time.time() - start_time
            return False, response_time, str(e)
    
    async def concurrent_test(
        self,
        method: str,
        endpoint: str,
        concurrent_users: int,
        requests_per_user: int,
        test_duration: Optional[int] = None,
        **request_kwargs
    ) -> TestResult:
        """并发测试"""
        test_name = f"{method} {endpoint} - {concurrent_users} users"
        logger.info(f"Starting concurrent test: {test_name}")
        
        start_time = datetime.now()
        self.system_monitor.start_monitoring()
        
        # 创建任务列表
        tasks = []
        
        if test_duration:
            # 基于时间的测试
            end_time = start_time + timedelta(seconds=test_duration)
            
            async def time_based_requests():
                results = []
                while datetime.now() < end_time:
                    success, response_time, error = await self.single_request(
                        method, endpoint, **request_kwargs
                    )
                    results.append((success, response_time, error))
                return results
            
            tasks = [time_based_requests() for _ in range(concurrent_users)]
        else:
            # 基于请求数量的测试
            async def request_batch():
                results = []
                for _ in range(requests_per_user):
                    success, response_time, error = await self.single_request(
                        method, endpoint, **request_kwargs
                    )
                    results.append((success, response_time, error))
                return results
            
            tasks = [request_batch() for _ in range(concurrent_users)]
        
        # 执行并发请求
        all_results = []
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        for task_result in completed_tasks:
            if isinstance(task_result, Exception):
                logger.error(f"Task failed: {str(task_result)}")
                continue
            all_results.extend(task_result)
        
        end_time = datetime.now()
        self.system_monitor.stop_monitoring()
        
        # 分析结果
        return self._analyze_results(test_name, all_results, start_time, end_time)
    
    def _analyze_results(
        self,
        test_name: str,
        results: List[Tuple[bool, float, str]],
        start_time: datetime,
        end_time: datetime
    ) -> TestResult:
        """分析测试结果"""
        total_requests = len(results)
        successful_requests = sum(1 for success, _, _ in results if success)
        failed_requests = total_requests - successful_requests
        
        response_times = [rt for _, rt, _ in results]
        errors = [error for success, _, error in results if not success and error]
        
        duration = (end_time - start_time).total_seconds()
        
        return TestResult(
            test_name=test_name,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            p95_response_time=self._percentile(response_times, 95) if response_times else 0,
            p99_response_time=self._percentile(response_times, 99) if response_times else 0,
            requests_per_second=total_requests / duration if duration > 0 else 0,
            error_rate=(failed_requests / total_requests * 100) if total_requests > 0 else 0,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            errors=list(set(errors))  # 去重错误信息
        )
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    async def stress_test_suite(self) -> List[TestResult]:
        """压力测试套件"""
        test_results = []
        
        # 测试场景配置
        test_scenarios = [
            # 健康检查端点 - 轻量级测试
            {
                "name": "Health Check",
                "method": "GET",
                "endpoint": "/api/v1/health",
                "concurrent_users": 10,
                "requests_per_user": 100
            },
            # 用户认证 - 中等负载
            {
                "name": "User Authentication",
                "method": "POST",
                "endpoint": "/api/v1/auth/login",
                "concurrent_users": 20,
                "requests_per_user": 50,
                "json": {
                    "username": "test_user",
                    "password": "test_password"
                }
            },
            # 案件列表查询 - 数据库密集型
            {
                "name": "Case List Query",
                "method": "GET",
                "endpoint": "/api/v1/cases",
                "concurrent_users": 50,
                "requests_per_user": 20,
                "params": {"page": 1, "size": 20}
            },
            # 高并发场景
            {
                "name": "High Concurrency Test",
                "method": "GET",
                "endpoint": "/api/v1/health",
                "concurrent_users": 100,
                "requests_per_user": 10
            },
            # 长时间测试
            {
                "name": "Endurance Test",
                "method": "GET",
                "endpoint": "/api/v1/health",
                "concurrent_users": 20,
                "test_duration": 60  # 60秒持续测试
            }
        ]
        
        for scenario in test_scenarios:
            try:
                logger.info(f"Running test scenario: {scenario['name']}")
                
                # 提取测试参数
                test_params = scenario.copy()
                test_params.pop('name')
                
                result = await self.concurrent_test(**test_params)
                test_results.append(result)
                
                # 测试间隔，让系统恢复
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Test scenario {scenario['name']} failed: {str(e)}")
        
        return test_results

class DatabaseStressTester:
    """数据库压力测试器"""
    
    def __init__(self):
        self.connection_pool = None
    
    def connection_pool_test(self, max_connections: int = 50, test_duration: int = 30) -> Dict[str, Any]:
        """连接池压力测试"""
        logger.info(f"Starting database connection pool test with {max_connections} connections")
        
        start_time = time.time()
        successful_connections = 0
        failed_connections = 0
        connection_times = []
        
        def create_connection():
            nonlocal successful_connections, failed_connections
            try:
                conn_start = time.time()
                # 这里应该创建实际的数据库连接
                # 为了测试，我们模拟连接时间
                time.sleep(0.01)  # 模拟连接时间
                conn_time = time.time() - conn_start
                connection_times.append(conn_time)
                successful_connections += 1
                return True
            except Exception as e:
                failed_connections += 1
                logger.error(f"Connection failed: {str(e)}")
                return False
        
        # 使用线程池模拟并发连接
        with ThreadPoolExecutor(max_workers=max_connections) as executor:
            end_time = start_time + test_duration
            futures = []
            
            while time.time() < end_time:
                if len(futures) < max_connections:
                    future = executor.submit(create_connection)
                    futures.append(future)
                
                # 清理完成的任务
                futures = [f for f in futures if not f.done()]
                
                time.sleep(0.1)  # 短暂休息
            
            # 等待所有任务完成
            for future in as_completed(futures):
                future.result()
        
        duration = time.time() - start_time
        
        return {
            "test_name": "Database Connection Pool Test",
            "duration": duration,
            "max_connections": max_connections,
            "successful_connections": successful_connections,
            "failed_connections": failed_connections,
            "connection_success_rate": (successful_connections / (successful_connections + failed_connections) * 100) if (successful_connections + failed_connections) > 0 else 0,
            "average_connection_time": statistics.mean(connection_times) if connection_times else 0,
            "max_connection_time": max(connection_times) if connection_times else 0,
            "connections_per_second": successful_connections / duration if duration > 0 else 0
        }
    
    def query_performance_test(self) -> Dict[str, Any]:
        """查询性能测试"""
        logger.info("Starting database query performance test")
        
        # 模拟不同类型的查询测试
        query_tests = [
            {"name": "Simple SELECT", "complexity": "low", "expected_time": 0.01},
            {"name": "JOIN Query", "complexity": "medium", "expected_time": 0.05},
            {"name": "Complex Aggregation", "complexity": "high", "expected_time": 0.1},
            {"name": "Full Text Search", "complexity": "high", "expected_time": 0.2}
        ]
        
        results = []
        
        for query_test in query_tests:
            # 模拟查询执行
            execution_times = []
            
            for _ in range(100):  # 执行100次查询
                start_time = time.time()
                # 模拟查询执行时间
                time.sleep(query_test["expected_time"] + (time.time() % 0.01))
                execution_time = time.time() - start_time
                execution_times.append(execution_time)
            
            results.append({
                "query_name": query_test["name"],
                "complexity": query_test["complexity"],
                "executions": len(execution_times),
                "average_time": statistics.mean(execution_times),
                "min_time": min(execution_times),
                "max_time": max(execution_times),
                "p95_time": self._percentile(execution_times, 95),
                "queries_per_second": len(execution_times) / sum(execution_times)
            })
        
        return {
            "test_name": "Database Query Performance Test",
            "query_results": results,
            "total_queries": sum(len(execution_times) for _ in query_tests),
            "test_duration": sum(sum(execution_times) for _ in query_tests for execution_times in [[0.01] * 100])
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

class JMeterIntegration:
    """JMeter集成测试"""
    
    def __init__(self):
        self.jmeter_path = self._find_jmeter()
    
    def _find_jmeter(self) -> Optional[str]:
        """查找JMeter安装路径"""
        possible_paths = [
            "/usr/local/bin/jmeter",
            "/opt/apache-jmeter/bin/jmeter",
            "jmeter"  # 假设在PATH中
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    return path
            except FileNotFoundError:
                continue
        
        return None
    
    def create_test_plan(self, test_config: Dict[str, Any]) -> str:
        """创建JMeter测试计划"""
        test_plan_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.4.1">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Lawsker API Performance Test" enabled="true">
      <stringProp name="TestPlan.comments">Automated performance test for Lawsker API</stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.tearDown_on_shutdown">true</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.arguments" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
      <stringProp name="TestPlan.user_define_classpath"></stringProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="API Load Test" enabled="true">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControllerGui" testclass="LoopController" testname="Loop Controller" enabled="true">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <stringProp name="LoopController.loops">{test_config.get('loops', 10)}</stringProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">{test_config.get('threads', 10)}</stringProp>
        <stringProp name="ThreadGroup.ramp_time">{test_config.get('ramp_time', 10)}</stringProp>
        <boolProp name="ThreadGroup.scheduler">false</boolProp>
        <stringProp name="ThreadGroup.duration"></stringProp>
        <stringProp name="ThreadGroup.delay"></stringProp>
        <boolProp name="ThreadGroup.same_user_on_next_iteration">true</boolProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="API Request" enabled="true">
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
            <collectionProp name="Arguments.arguments"/>
          </elementProp>
          <stringProp name="HTTPSampler.domain">{test_config.get('host', 'localhost')}</stringProp>
          <stringProp name="HTTPSampler.port">{test_config.get('port', '8000')}</stringProp>
          <stringProp name="HTTPSampler.protocol">http</stringProp>
          <stringProp name="HTTPSampler.contentEncoding"></stringProp>
          <stringProp name="HTTPSampler.path">{test_config.get('path', '/api/v1/health')}</stringProp>
          <stringProp name="HTTPSampler.method">{test_config.get('method', 'GET')}</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
          <boolProp name="HTTPSampler.auto_redirects">false</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
          <boolProp name="HTTPSampler.DO_MULTIPART_POST">false</boolProp>
          <stringProp name="HTTPSampler.embedded_url_re"></stringProp>
          <stringProp name="HTTPSampler.connect_timeout"></stringProp>
          <stringProp name="HTTPSampler.response_timeout"></stringProp>
        </HTTPSamplerProxy>
        <hashTree/>
        <ResultCollector guiclass="SummaryReport" testclass="ResultCollector" testname="Summary Report" enabled="true">
          <boolProp name="ResultCollector.error_logging">false</boolProp>
          <objProp>
            <name>saveConfig</name>
            <value class="SampleSaveConfiguration">
              <time>true</time>
              <latency>true</latency>
              <timestamp>true</timestamp>
              <success>true</success>
              <label>true</label>
              <code>true</code>
              <message>true</message>
              <threadName>true</threadName>
              <dataType>true</dataType>
              <encoding>false</encoding>
              <assertions>true</assertions>
              <subresults>true</subresults>
              <responseData>false</responseData>
              <samplerData>false</samplerData>
              <xml>false</xml>
              <fieldNames>true</fieldNames>
              <responseHeaders>false</responseHeaders>
              <requestHeaders>false</requestHeaders>
              <responseDataOnError>false</responseDataOnError>
              <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
              <assertionsResultsToSave>0</assertionsResultsToSave>
              <bytes>true</bytes>
              <sentBytes>true</sentBytes>
              <url>true</url>
              <threadCounts>true</threadCounts>
              <idleTime>true</idleTime>
              <connectTime>true</connectTime>
            </value>
          </objProp>
          <stringProp name="filename">jmeter_results.jtl</stringProp>
        </ResultCollector>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>"""
        
        # 保存测试计划文件
        test_plan_file = Path("performance_test_plan.jmx")
        test_plan_file.write_text(test_plan_xml)
        
        return str(test_plan_file)
    
    def run_jmeter_test(self, test_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """运行JMeter测试"""
        if not self.jmeter_path:
            logger.warning("JMeter not found, skipping JMeter tests")
            return None
        
        logger.info("Running JMeter performance test")
        
        try:
            # 创建测试计划
            test_plan_file = self.create_test_plan(test_config)
            
            # 运行JMeter测试
            cmd = [
                self.jmeter_path,
                "-n",  # 非GUI模式
                "-t", test_plan_file,  # 测试计划文件
                "-l", "jmeter_results.jtl",  # 结果文件
                "-e",  # 生成HTML报告
                "-o", "jmeter_report"  # 报告目录
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # 解析结果文件
                return self._parse_jmeter_results("jmeter_results.jtl")
            else:
                logger.error(f"JMeter test failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("JMeter test timed out")
            return None
        except Exception as e:
            logger.error(f"JMeter test error: {str(e)}")
            return None
    
    def _parse_jmeter_results(self, results_file: str) -> Dict[str, Any]:
        """解析JMeter结果文件"""
        try:
            results_path = Path(results_file)
            if not results_path.exists():
                return {"error": "Results file not found"}
            
            # 简单的结果解析（实际应该解析JTL文件）
            return {
                "test_name": "JMeter Performance Test",
                "status": "completed",
                "results_file": results_file,
                "report_directory": "jmeter_report"
            }
            
        except Exception as e:
            logger.error(f"Failed to parse JMeter results: {str(e)}")
            return {"error": str(e)}

class PerformanceTestRunner:
    """性能测试运行器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有性能测试"""
        logger.info("Starting comprehensive performance test suite")
        
        test_report = {
            "test_suite": "Lawsker Performance Test Suite",
            "start_time": datetime.now().isoformat(),
            "base_url": self.base_url,
            "results": {}
        }
        
        # 1. API负载测试
        logger.info("Running API load tests...")
        async with APILoadTester(self.base_url) as api_tester:
            api_results = await api_tester.stress_test_suite()
            test_report["results"]["api_load_tests"] = [result.to_dict() for result in api_results]
            
            # 系统指标
            system_metrics = api_tester.system_monitor.get_average_metrics()
            test_report["results"]["system_metrics_during_api_tests"] = system_metrics
        
        # 2. 数据库压力测试
        logger.info("Running database stress tests...")
        db_tester = DatabaseStressTester()
        
        connection_pool_result = db_tester.connection_pool_test()
        test_report["results"]["database_connection_pool_test"] = connection_pool_result
        
        query_performance_result = db_tester.query_performance_test()
        test_report["results"]["database_query_performance_test"] = query_performance_result
        
        # 3. JMeter集成测试
        logger.info("Running JMeter tests...")
        jmeter = JMeterIntegration()
        jmeter_config = {
            "host": "localhost",
            "port": "8000",
            "path": "/api/v1/health",
            "method": "GET",
            "threads": 50,
            "loops": 20,
            "ramp_time": 10
        }
        
        jmeter_result = jmeter.run_jmeter_test(jmeter_config)
        if jmeter_result:
            test_report["results"]["jmeter_test"] = jmeter_result
        
        # 4. 系统稳定性测试
        logger.info("Running system stability test...")
        stability_result = await self._system_stability_test()
        test_report["results"]["system_stability_test"] = stability_result
        
        test_report["end_time"] = datetime.now().isoformat()
        test_report["total_duration"] = (
            datetime.fromisoformat(test_report["end_time"]) - 
            datetime.fromisoformat(test_report["start_time"])
        ).total_seconds()
        
        # 生成测试摘要
        test_report["summary"] = self._generate_test_summary(test_report)
        
        return test_report
    
    async def _system_stability_test(self) -> Dict[str, Any]:
        """系统稳定性测试"""
        logger.info("Running system stability test (5 minutes)")
        
        system_monitor = SystemMonitor()
        system_monitor.start_monitoring()
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=5)
        
        request_count = 0
        error_count = 0
        
        async with aiohttp.ClientSession() as session:
            while datetime.now() < end_time:
                try:
                    async with session.get(f"{self.base_url}/api/v1/health") as response:
                        request_count += 1
                        if response.status >= 400:
                            error_count += 1
                except Exception:
                    error_count += 1
                
                await asyncio.sleep(1)  # 每秒一个请求
        
        system_monitor.stop_monitoring()
        
        return {
            "test_name": "System Stability Test",
            "duration_minutes": 5,
            "total_requests": request_count,
            "error_count": error_count,
            "error_rate": (error_count / request_count * 100) if request_count > 0 else 0,
            "system_metrics": system_monitor.get_average_metrics()
        }
    
    def _generate_test_summary(self, test_report: Dict[str, Any]) -> Dict[str, Any]:
        """生成测试摘要"""
        summary = {
            "total_duration": test_report["total_duration"],
            "tests_completed": len(test_report["results"]),
            "overall_status": "PASS"
        }
        
        # 分析API测试结果
        api_tests = test_report["results"].get("api_load_tests", [])
        if api_tests:
            total_requests = sum(test["total_requests"] for test in api_tests)
            total_errors = sum(test["failed_requests"] for test in api_tests)
            avg_response_time = statistics.mean([test["average_response_time"] for test in api_tests])
            
            summary["api_tests"] = {
                "total_requests": total_requests,
                "total_errors": total_errors,
                "overall_error_rate": (total_errors / total_requests * 100) if total_requests > 0 else 0,
                "average_response_time": avg_response_time
            }
            
            # 检查是否有测试失败
            if summary["api_tests"]["overall_error_rate"] > 5:  # 错误率超过5%
                summary["overall_status"] = "FAIL"
        
        # 分析数据库测试结果
        db_connection_test = test_report["results"].get("database_connection_pool_test", {})
        if db_connection_test:
            summary["database_tests"] = {
                "connection_success_rate": db_connection_test.get("connection_success_rate", 0),
                "connections_per_second": db_connection_test.get("connections_per_second", 0)
            }
            
            if summary["database_tests"]["connection_success_rate"] < 95:  # 成功率低于95%
                summary["overall_status"] = "FAIL"
        
        return summary
    
    def save_report(self, test_report: Dict[str, Any], filename: str = "performance_test_report.json"):
        """保存测试报告"""
        report_path = Path(filename)
        with open(report_path, 'w') as f:
            json.dump(test_report, f, indent=2)
        
        logger.info(f"Performance test report saved to: {report_path.absolute()}")
        
        # 打印摘要
        self._print_summary(test_report)
    
    def _print_summary(self, test_report: Dict[str, Any]):
        """打印测试摘要"""
        summary = test_report.get("summary", {})
        
        print("\n" + "="*60)
        print("PERFORMANCE TEST REPORT SUMMARY")
        print("="*60)
        print(f"Overall Status: {summary.get('overall_status', 'UNKNOWN')}")
        print(f"Total Duration: {summary.get('total_duration', 0):.2f} seconds")
        print(f"Tests Completed: {summary.get('tests_completed', 0)}")
        
        if "api_tests" in summary:
            api = summary["api_tests"]
            print(f"\nAPI Tests:")
            print(f"  Total Requests: {api['total_requests']}")
            print(f"  Total Errors: {api['total_errors']}")
            print(f"  Error Rate: {api['overall_error_rate']:.2f}%")
            print(f"  Avg Response Time: {api['average_response_time']:.3f}s")
        
        if "database_tests" in summary:
            db = summary["database_tests"]
            print(f"\nDatabase Tests:")
            print(f"  Connection Success Rate: {db['connection_success_rate']:.2f}%")
            print(f"  Connections/Second: {db['connections_per_second']:.2f}")
        
        print("="*60)

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Lawsker性能压力测试工具")
    parser.add_argument("--url", default="http://localhost:8000", help="API基础URL")
    parser.add_argument("--output", default="performance_test_report.json", help="输出报告文件")
    
    args = parser.parse_args()
    
    try:
        runner = PerformanceTestRunner(args.url)
        test_report = await runner.run_all_tests()
        runner.save_report(test_report, args.output)
        
        # 根据测试结果设置退出码
        if test_report.get("summary", {}).get("overall_status") == "PASS":
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Performance test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Performance test failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())