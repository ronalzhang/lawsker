#!/usr/bin/env python3
"""
模拟性能测试脚本
验证性能测试框架和生成测试报告
"""
import asyncio
import time
import json
import statistics
import random
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

class MockPerformanceTester:
    """模拟性能测试器"""
    
    def __init__(self):
        self.results = []
    
    async def simulate_request(self, endpoint: str, expected_response_time: float = 0.1) -> Dict[str, Any]:
        """模拟单个请求"""
        # 模拟网络延迟
        response_time = expected_response_time + random.uniform(-0.05, 0.05)
        await asyncio.sleep(response_time)
        
        # 模拟成功/失败概率
        success = random.random() > 0.05  # 95%成功率
        
        return {
            "success": success,
            "response_time": response_time,
            "status_code": 200 if success else random.choice([404, 500, 503]),
            "error": None if success else "Simulated error"
        }
    
    async def simulate_concurrent_test(self, test_name: str, concurrent_users: int, requests_per_user: int, expected_response_time: float = 0.1) -> Dict[str, Any]:
        """模拟并发测试"""
        print(f"Running {test_name}: {concurrent_users} users, {requests_per_user} requests each")
        
        start_time = time.time()
        
        # 创建并发任务
        async def user_requests():
            results = []
            for _ in range(requests_per_user):
                result = await self.simulate_request("/api/test", expected_response_time)
                results.append(result)
            return results
        
        # 执行并发用户
        tasks = [user_requests() for _ in range(concurrent_users)]
        user_results = await asyncio.gather(*tasks)
        
        # 合并所有结果
        all_results = []
        for user_result in user_results:
            all_results.extend(user_result)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 分析结果
        total_requests = len(all_results)
        successful_requests = sum(1 for r in all_results if r["success"])
        failed_requests = total_requests - successful_requests
        
        response_times = [r["response_time"] for r in all_results]
        
        return {
            "test_name": test_name,
            "concurrent_users": concurrent_users,
            "requests_per_user": requests_per_user,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            "duration": duration,
            "requests_per_second": total_requests / duration if duration > 0 else 0,
            "average_response_time": statistics.mean(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "p95_response_time": self.percentile(response_times, 95),
            "p99_response_time": self.percentile(response_times, 99)
        }
    
    def percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def simulate_system_metrics(self) -> Dict[str, Any]:
        """模拟系统指标"""
        return {
            "cpu_percent": random.uniform(10, 80),
            "memory_percent": random.uniform(40, 90),
            "memory_available_gb": random.uniform(1, 8),
            "disk_percent": random.uniform(20, 70),
            "disk_free_gb": random.uniform(10, 100),
            "network_io_mb": random.uniform(1, 50)
        }
    
    async def simulate_database_test(self) -> Dict[str, Any]:
        """模拟数据库压力测试"""
        print("Running database connection pool test...")
        
        # 模拟连接池测试
        max_connections = 50
        test_duration = 5  # 5秒测试
        
        start_time = time.time()
        successful_connections = 0
        failed_connections = 0
        connection_times = []
        
        while time.time() - start_time < test_duration:
            # 模拟连接尝试
            connection_time = random.uniform(0.01, 0.1)
            connection_times.append(connection_time)
            
            if random.random() > 0.02:  # 98%成功率
                successful_connections += 1
            else:
                failed_connections += 1
            
            await asyncio.sleep(0.01)  # 模拟连接间隔
        
        return {
            "test_name": "Database Connection Pool Test",
            "max_connections": max_connections,
            "test_duration": test_duration,
            "successful_connections": successful_connections,
            "failed_connections": failed_connections,
            "connection_success_rate": (successful_connections / (successful_connections + failed_connections) * 100) if (successful_connections + failed_connections) > 0 else 0,
            "average_connection_time": statistics.mean(connection_times),
            "max_connection_time": max(connection_times),
            "connections_per_second": successful_connections / test_duration
        }
    
    async def run_performance_test_suite(self) -> Dict[str, Any]:
        """运行完整的性能测试套件"""
        print("Starting mock performance test suite...")
        
        test_report = {
            "test_suite": "Mock Performance Test Suite",
            "start_time": datetime.now().isoformat(),
            "system_metrics_before": self.simulate_system_metrics(),
            "test_results": {}
        }
        
        # 1. API负载测试
        print("\n=== API Load Tests ===")
        api_tests = []
        
        test_scenarios = [
            ("Light Load Test", 5, 20, 0.05),
            ("Medium Load Test", 20, 25, 0.1),
            ("Heavy Load Test", 50, 10, 0.15),
            ("Stress Test", 100, 5, 0.2)
        ]
        
        for test_name, users, requests, response_time in test_scenarios:
            result = await self.simulate_concurrent_test(test_name, users, requests, response_time)
            api_tests.append(result)
            await asyncio.sleep(1)  # 测试间隔
        
        test_report["test_results"]["api_load_tests"] = api_tests
        
        # 2. 数据库压力测试
        print("\n=== Database Stress Tests ===")
        db_test = await self.simulate_database_test()
        test_report["test_results"]["database_test"] = db_test
        
        # 3. 系统稳定性测试
        print("\n=== System Stability Test ===")
        stability_test = await self.simulate_stability_test()
        test_report["test_results"]["stability_test"] = stability_test
        
        test_report["system_metrics_after"] = self.simulate_system_metrics()
        test_report["end_time"] = datetime.now().isoformat()
        
        # 生成测试摘要
        test_report["summary"] = self.generate_summary(test_report)
        
        return test_report
    
    async def simulate_stability_test(self) -> Dict[str, Any]:
        """模拟系统稳定性测试"""
        print("Running 30-second stability test...")
        
        start_time = time.time()
        test_duration = 30  # 30秒测试
        
        request_count = 0
        error_count = 0
        response_times = []
        
        while time.time() - start_time < test_duration:
            # 模拟请求
            response_time = random.uniform(0.05, 0.3)
            response_times.append(response_time)
            request_count += 1
            
            # 模拟错误
            if random.random() < 0.02:  # 2%错误率
                error_count += 1
            
            await asyncio.sleep(1)  # 每秒一个请求
        
        return {
            "test_name": "System Stability Test",
            "duration": test_duration,
            "total_requests": request_count,
            "error_count": error_count,
            "error_rate": (error_count / request_count * 100) if request_count > 0 else 0,
            "average_response_time": statistics.mean(response_times),
            "max_response_time": max(response_times),
            "requests_per_second": request_count / test_duration
        }
    
    def generate_summary(self, test_report: Dict[str, Any]) -> Dict[str, Any]:
        """生成测试摘要"""
        api_tests = test_report["test_results"]["api_load_tests"]
        db_test = test_report["test_results"]["database_test"]
        stability_test = test_report["test_results"]["stability_test"]
        
        # API测试统计
        total_api_requests = sum(test["total_requests"] for test in api_tests)
        total_api_errors = sum(test["failed_requests"] for test in api_tests)
        avg_api_response_time = statistics.mean([test["average_response_time"] for test in api_tests])
        avg_api_success_rate = statistics.mean([test["success_rate"] for test in api_tests])
        
        # 整体状态判断
        overall_status = "PASS"
        
        if avg_api_success_rate < 95:
            overall_status = "FAIL"
        elif db_test["connection_success_rate"] < 95:
            overall_status = "FAIL"
        elif stability_test["error_rate"] > 5:
            overall_status = "FAIL"
        elif avg_api_response_time > 0.5:
            overall_status = "WARNING"
        
        return {
            "overall_status": overall_status,
            "total_api_requests": total_api_requests,
            "total_api_errors": total_api_errors,
            "api_success_rate": round(avg_api_success_rate, 2),
            "api_average_response_time": round(avg_api_response_time, 3),
            "database_connection_success_rate": round(db_test["connection_success_rate"], 2),
            "stability_error_rate": round(stability_test["error_rate"], 2),
            "max_concurrent_users": max(test["concurrent_users"] for test in api_tests),
            "peak_requests_per_second": max(test["requests_per_second"] for test in api_tests)
        }
    
    def save_report(self, test_report: Dict[str, Any], filename: str = "mock_performance_report.json"):
        """保存测试报告"""
        report_path = Path(filename)
        with open(report_path, 'w') as f:
            json.dump(test_report, f, indent=2)
        
        print(f"\nPerformance test report saved to: {report_path.absolute()}")
        self.print_summary(test_report)
    
    def print_summary(self, test_report: Dict[str, Any]):
        """打印测试摘要"""
        summary = test_report.get("summary", {})
        
        print("\n" + "="*70)
        print("PERFORMANCE TEST REPORT SUMMARY")
        print("="*70)
        print(f"Overall Status: {summary.get('overall_status', 'UNKNOWN')}")
        print(f"Test Duration: {(datetime.fromisoformat(test_report['end_time']) - datetime.fromisoformat(test_report['start_time'])).total_seconds():.1f} seconds")
        
        print(f"\nAPI Load Tests:")
        print(f"  Total Requests: {summary.get('total_api_requests', 0)}")
        print(f"  Total Errors: {summary.get('total_api_errors', 0)}")
        print(f"  Success Rate: {summary.get('api_success_rate', 0)}%")
        print(f"  Average Response Time: {summary.get('api_average_response_time', 0)}s")
        print(f"  Max Concurrent Users: {summary.get('max_concurrent_users', 0)}")
        print(f"  Peak Requests/Second: {summary.get('peak_requests_per_second', 0):.2f}")
        
        print(f"\nDatabase Tests:")
        print(f"  Connection Success Rate: {summary.get('database_connection_success_rate', 0)}%")
        
        print(f"\nStability Tests:")
        print(f"  Error Rate: {summary.get('stability_error_rate', 0)}%")
        
        # 系统指标
        metrics_before = test_report.get("system_metrics_before", {})
        metrics_after = test_report.get("system_metrics_after", {})
        
        print(f"\nSystem Resource Usage:")
        print(f"  CPU: {metrics_before.get('cpu_percent', 0):.1f}% → {metrics_after.get('cpu_percent', 0):.1f}%")
        print(f"  Memory: {metrics_before.get('memory_percent', 0):.1f}% → {metrics_after.get('memory_percent', 0):.1f}%")
        
        # 详细测试结果
        print(f"\nDetailed Test Results:")
        print("-" * 50)
        
        for test in test_report["test_results"]["api_load_tests"]:
            status_icon = "✅" if test["success_rate"] >= 95 else "⚠️" if test["success_rate"] >= 90 else "❌"
            print(f"{status_icon} {test['test_name']}: {test['success_rate']:.1f}% success, {test['average_response_time']:.3f}s avg, {test['requests_per_second']:.1f} req/s")
        
        db_test = test_report["test_results"]["database_test"]
        db_status = "✅" if db_test["connection_success_rate"] >= 95 else "❌"
        print(f"{db_status} {db_test['test_name']}: {db_test['connection_success_rate']:.1f}% success, {db_test['connections_per_second']:.1f} conn/s")
        
        stability_test = test_report["test_results"]["stability_test"]
        stability_status = "✅" if stability_test["error_rate"] <= 5 else "❌"
        print(f"{stability_status} {stability_test['test_name']}: {stability_test['error_rate']:.1f}% error rate")
        
        print("="*70)

async def main():
    """主函数"""
    try:
        tester = MockPerformanceTester()
        test_report = await tester.run_performance_test_suite()
        tester.save_report(test_report, "mock_performance_report.json")
        
        # 根据测试结果设置退出码
        if test_report.get("summary", {}).get("overall_status") == "PASS":
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        print("\nPerformance test interrupted by user")
        return 1
    except Exception as e:
        print(f"Performance test failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)