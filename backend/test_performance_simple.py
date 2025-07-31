#!/usr/bin/env python3
"""
简化的性能测试脚本
快速验证系统性能和稳定性
"""
import asyncio
import aiohttp
import time
import json
import statistics
import psutil
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

class SimplePerformanceTester:
    """简化的性能测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
    
    async def single_request_test(self, endpoint: str, method: str = "GET") -> Dict[str, Any]:
        """单个请求测试"""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}{endpoint}"
                async with session.request(method, url) as response:
                    await response.text()
                    response_time = time.time() - start_time
                    
                    return {
                        "success": response.status < 400,
                        "status_code": response.status,
                        "response_time": response_time,
                        "error": None
                    }
        except Exception as e:
            return {
                "success": False,
                "status_code": 0,
                "response_time": time.time() - start_time,
                "error": str(e)
            }
    
    async def concurrent_requests_test(self, endpoint: str, concurrent_count: int = 10, total_requests: int = 100) -> Dict[str, Any]:
        """并发请求测试"""
        print(f"Testing {endpoint} with {concurrent_count} concurrent users, {total_requests} total requests")
        
        start_time = time.time()
        semaphore = asyncio.Semaphore(concurrent_count)
        
        async def make_request():
            async with semaphore:
                return await self.single_request_test(endpoint)
        
        # 创建任务
        tasks = [make_request() for _ in range(total_requests)]
        
        # 执行并发请求
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 分析结果
        successful_requests = 0
        failed_requests = 0
        response_times = []
        errors = []
        
        for result in results:
            if isinstance(result, Exception):
                failed_requests += 1
                errors.append(str(result))
            elif result["success"]:
                successful_requests += 1
                response_times.append(result["response_time"])
            else:
                failed_requests += 1
                if result["error"]:
                    errors.append(result["error"])
        
        return {
            "endpoint": endpoint,
            "concurrent_users": concurrent_count,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            "duration": duration,
            "requests_per_second": total_requests / duration if duration > 0 else 0,
            "average_response_time": statistics.mean(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "errors": list(set(errors))[:5]  # 最多显示5个不同的错误
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": (disk.used / disk.total) * 100,
                "disk_free_gb": disk.free / (1024**3)
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def run_performance_tests(self) -> Dict[str, Any]:
        """运行性能测试套件"""
        print("Starting performance test suite...")
        
        test_report = {
            "test_suite": "Simple Performance Test",
            "start_time": datetime.now().isoformat(),
            "base_url": self.base_url,
            "system_metrics_before": self.get_system_metrics(),
            "test_results": []
        }
        
        # 测试场景
        test_scenarios = [
            {
                "name": "Health Check - Light Load",
                "endpoint": "/api/v1/health",
                "concurrent_users": 5,
                "total_requests": 50
            },
            {
                "name": "Health Check - Medium Load", 
                "endpoint": "/api/v1/health",
                "concurrent_users": 20,
                "total_requests": 100
            },
            {
                "name": "Health Check - High Load",
                "endpoint": "/api/v1/health", 
                "concurrent_users": 50,
                "total_requests": 200
            }
        ]
        
        # 运行测试
        for scenario in test_scenarios:
            try:
                print(f"\nRunning: {scenario['name']}")
                result = await self.concurrent_requests_test(
                    scenario["endpoint"],
                    scenario["concurrent_users"],
                    scenario["total_requests"]
                )
                result["test_name"] = scenario["name"]
                test_report["test_results"].append(result)
                
                # 测试间隔
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"Test {scenario['name']} failed: {str(e)}")
                test_report["test_results"].append({
                    "test_name": scenario["name"],
                    "error": str(e),
                    "success": False
                })
        
        test_report["system_metrics_after"] = self.get_system_metrics()
        test_report["end_time"] = datetime.now().isoformat()
        
        # 计算总体统计
        test_report["summary"] = self.calculate_summary(test_report)
        
        return test_report
    
    def calculate_summary(self, test_report: Dict[str, Any]) -> Dict[str, Any]:
        """计算测试摘要"""
        successful_tests = 0
        total_requests = 0
        total_successful_requests = 0
        total_failed_requests = 0
        avg_response_times = []
        
        for result in test_report["test_results"]:
            if "error" not in result:
                successful_tests += 1
                total_requests += result.get("total_requests", 0)
                total_successful_requests += result.get("successful_requests", 0)
                total_failed_requests += result.get("failed_requests", 0)
                
                if result.get("average_response_time", 0) > 0:
                    avg_response_times.append(result["average_response_time"])
        
        overall_success_rate = (total_successful_requests / total_requests * 100) if total_requests > 0 else 0
        overall_avg_response_time = statistics.mean(avg_response_times) if avg_response_times else 0
        
        # 判断整体状态
        status = "PASS"
        if successful_tests < len(test_report["test_results"]):
            status = "FAIL"
        elif overall_success_rate < 95:
            status = "FAIL"
        elif overall_avg_response_time > 1.0:  # 平均响应时间超过1秒
            status = "WARNING"
        
        return {
            "overall_status": status,
            "successful_tests": successful_tests,
            "total_tests": len(test_report["test_results"]),
            "total_requests": total_requests,
            "total_successful_requests": total_successful_requests,
            "total_failed_requests": total_failed_requests,
            "overall_success_rate": round(overall_success_rate, 2),
            "overall_avg_response_time": round(overall_avg_response_time, 3)
        }
    
    def save_report(self, test_report: Dict[str, Any], filename: str = "simple_performance_report.json"):
        """保存测试报告"""
        report_path = Path(filename)
        with open(report_path, 'w') as f:
            json.dump(test_report, f, indent=2)
        
        print(f"\nReport saved to: {report_path.absolute()}")
        self.print_summary(test_report)
    
    def print_summary(self, test_report: Dict[str, Any]):
        """打印测试摘要"""
        summary = test_report.get("summary", {})
        
        print("\n" + "="*60)
        print("PERFORMANCE TEST SUMMARY")
        print("="*60)
        print(f"Overall Status: {summary.get('overall_status', 'UNKNOWN')}")
        print(f"Tests Passed: {summary.get('successful_tests', 0)}/{summary.get('total_tests', 0)}")
        print(f"Total Requests: {summary.get('total_requests', 0)}")
        print(f"Successful Requests: {summary.get('total_successful_requests', 0)}")
        print(f"Failed Requests: {summary.get('total_failed_requests', 0)}")
        print(f"Overall Success Rate: {summary.get('overall_success_rate', 0)}%")
        print(f"Average Response Time: {summary.get('overall_avg_response_time', 0)}s")
        
        # 系统指标对比
        metrics_before = test_report.get("system_metrics_before", {})
        metrics_after = test_report.get("system_metrics_after", {})
        
        if metrics_before and metrics_after:
            print(f"\nSystem Metrics:")
            print(f"CPU Usage: {metrics_before.get('cpu_percent', 0):.1f}% → {metrics_after.get('cpu_percent', 0):.1f}%")
            print(f"Memory Usage: {metrics_before.get('memory_percent', 0):.1f}% → {metrics_after.get('memory_percent', 0):.1f}%")
        
        print("\nDetailed Results:")
        print("-" * 40)
        for result in test_report["test_results"]:
            if "error" in result:
                print(f"❌ {result['test_name']}: {result['error']}")
            else:
                status = "✅" if result["success_rate"] >= 95 else "⚠️"
                print(f"{status} {result['test_name']}: {result['success_rate']:.1f}% success, {result['average_response_time']:.3f}s avg")
        
        print("="*60)

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="简化性能测试工具")
    parser.add_argument("--url", default="http://localhost:8000", help="API基础URL")
    parser.add_argument("--output", default="simple_performance_report.json", help="输出报告文件")
    
    args = parser.parse_args()
    
    try:
        tester = SimplePerformanceTester(args.url)
        test_report = await tester.run_performance_tests()
        tester.save_report(test_report, args.output)
        
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