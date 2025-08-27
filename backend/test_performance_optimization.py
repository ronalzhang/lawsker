"""
性能优化测试脚本
测试系统性能指标是否达标
"""

import asyncio
import time
import logging
import statistics
from typing import List, Dict, Any
import aiohttp
import psutil
from datetime import datetime
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceTestSuite:
    """性能测试套件"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = {}
        self.performance_requirements = {
            'auth_response_time': 1.0,  # 认证系统响应时间 < 1秒
            'points_calculation_time': 0.5,  # 积分计算延迟 < 500ms
            'credits_payment_time': 2.0,  # Credits支付处理时间 < 2秒
            'concurrent_users': 1000,  # 支持1000+并发用户
            'page_load_time': 2.0,  # 前端页面加载时间 < 2秒
            'system_availability': 99.9,  # 系统可用性 > 99.9%
            'credits_processing_rate': 10000  # Credits处理能力 > 10000次/小时
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有性能测试"""
        logger.info("Starting comprehensive performance tests...")
        
        test_methods = [
            self.test_auth_response_time,
            self.test_points_calculation_performance,
            self.test_credits_payment_performance,
            self.test_concurrent_user_capacity,
            self.test_page_load_performance,
            self.test_system_resource_usage,
            self.test_database_performance,
            self.test_cache_performance
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                logger.error(f"Test {test_method.__name__} failed: {e}")
                self.test_results[test_method.__name__] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
        
        # 生成测试报告
        report = self.generate_performance_report()
        logger.info("Performance tests completed")
        
        return report
    
    async def test_auth_response_time(self):
        """测试认证系统响应时间"""
        logger.info("Testing authentication response time...")
        
        response_times = []
        test_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        
        async with aiohttp.ClientSession() as session:
            for i in range(50):  # 测试50次
                start_time = time.time()
                try:
                    async with session.post(
                        f"{self.base_url}/api/v1/auth/login",
                        json=test_data,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        await response.text()
                        response_time = time.time() - start_time
                        response_times.append(response_time)
                except Exception as e:
                    logger.warning(f"Auth test request {i} failed: {e}")
                
                await asyncio.sleep(0.1)  # 避免过于频繁的请求
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            
            self.test_results['auth_response_time'] = {
                'status': 'PASSED' if avg_response_time < self.performance_requirements['auth_response_time'] else 'FAILED',
                'average': avg_response_time,
                'maximum': max_response_time,
                'p95': p95_response_time,
                'requirement': self.performance_requirements['auth_response_time'],
                'sample_size': len(response_times)
            }
            
            logger.info(f"Auth response time - Avg: {avg_response_time:.3f}s, Max: {max_response_time:.3f}s, P95: {p95_response_time:.3f}s")
        else:
            self.test_results['auth_response_time'] = {
                'status': 'FAILED',
                'error': 'No successful requests'
            }
    
    async def test_points_calculation_performance(self):
        """测试积分计算性能"""
        logger.info("Testing points calculation performance...")
        
        calculation_times = []
        
        async with aiohttp.ClientSession() as session:
            for i in range(100):  # 测试100次积分计算
                start_time = time.time()
                try:
                    test_data = {
                        'lawyer_id': f'test_lawyer_{i}',
                        'action': 'case_complete_success',
                        'context': {'case_value': 1000}
                    }
                    
                    async with session.post(
                        f"{self.base_url}/api/v1/points/calculate",
                        json=test_data,
                        timeout=aiohttp.ClientTimeout(total=2)
                    ) as response:
                        await response.text()
                        calculation_time = time.time() - start_time
                        calculation_times.append(calculation_time)
                        
                except Exception as e:
                    logger.warning(f"Points calculation test {i} failed: {e}")
                
                await asyncio.sleep(0.05)
        
        if calculation_times:
            avg_calculation_time = statistics.mean(calculation_times)
            max_calculation_time = max(calculation_times)
            
            self.test_results['points_calculation_time'] = {
                'status': 'PASSED' if avg_calculation_time < self.performance_requirements['points_calculation_time'] else 'FAILED',
                'average': avg_calculation_time,
                'maximum': max_calculation_time,
                'requirement': self.performance_requirements['points_calculation_time'],
                'sample_size': len(calculation_times)
            }
            
            logger.info(f"Points calculation time - Avg: {avg_calculation_time:.3f}s, Max: {max_calculation_time:.3f}s")
        else:
            self.test_results['points_calculation_time'] = {
                'status': 'FAILED',
                'error': 'No successful calculations'
            }
    
    async def test_credits_payment_performance(self):
        """测试Credits支付性能"""
        logger.info("Testing credits payment performance...")
        
        payment_times = []
        
        async with aiohttp.ClientSession() as session:
            for i in range(30):  # 测试30次支付
                start_time = time.time()
                try:
                    test_data = {
                        'user_id': f'test_user_{i}',
                        'credits_count': 1,
                        'payment_method': 'test'
                    }
                    
                    async with session.post(
                        f"{self.base_url}/api/v1/credits/purchase",
                        json=test_data,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        await response.text()
                        payment_time = time.time() - start_time
                        payment_times.append(payment_time)
                        
                except Exception as e:
                    logger.warning(f"Credits payment test {i} failed: {e}")
                
                await asyncio.sleep(0.2)
        
        if payment_times:
            avg_payment_time = statistics.mean(payment_times)
            max_payment_time = max(payment_times)
            
            self.test_results['credits_payment_time'] = {
                'status': 'PASSED' if avg_payment_time < self.performance_requirements['credits_payment_time'] else 'FAILED',
                'average': avg_payment_time,
                'maximum': max_payment_time,
                'requirement': self.performance_requirements['credits_payment_time'],
                'sample_size': len(payment_times)
            }
            
            logger.info(f"Credits payment time - Avg: {avg_payment_time:.3f}s, Max: {max_payment_time:.3f}s")
        else:
            self.test_results['credits_payment_time'] = {
                'status': 'FAILED',
                'error': 'No successful payments'
            }
    
    async def test_concurrent_user_capacity(self):
        """测试并发用户容量"""
        logger.info("Testing concurrent user capacity...")
        
        concurrent_levels = [100, 500, 1000, 1500]  # 测试不同并发级别
        results = {}
        
        for concurrent_users in concurrent_levels:
            logger.info(f"Testing {concurrent_users} concurrent users...")
            
            async def make_request(session, user_id):
                try:
                    start_time = time.time()
                    async with session.get(
                        f"{self.base_url}/api/v1/health",
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        response_time = time.time() - start_time
                        return {
                            'user_id': user_id,
                            'status_code': response.status,
                            'response_time': response_time,
                            'success': response.status == 200
                        }
                except Exception as e:
                    return {
                        'user_id': user_id,
                        'error': str(e),
                        'success': False
                    }
            
            async with aiohttp.ClientSession() as session:
                tasks = [make_request(session, i) for i in range(concurrent_users)]
                start_time = time.time()
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                total_time = time.time() - start_time
                
                successful_requests = [r for r in responses if isinstance(r, dict) and r.get('success', False)]
                success_rate = len(successful_requests) / len(responses) * 100
                
                if successful_requests:
                    avg_response_time = statistics.mean([r['response_time'] for r in successful_requests])
                else:
                    avg_response_time = 0
                
                results[concurrent_users] = {
                    'total_requests': len(responses),
                    'successful_requests': len(successful_requests),
                    'success_rate': success_rate,
                    'average_response_time': avg_response_time,
                    'total_time': total_time,
                    'requests_per_second': len(responses) / total_time
                }
                
                logger.info(f"{concurrent_users} users - Success rate: {success_rate:.1f}%, "
                          f"Avg response: {avg_response_time:.3f}s, RPS: {results[concurrent_users]['requests_per_second']:.1f}")
        
        # 判断是否支持1000+并发用户
        if 1000 in results:
            success_rate_1000 = results[1000]['success_rate']
            status = 'PASSED' if success_rate_1000 >= 95 else 'FAILED'  # 95%成功率阈值
        else:
            status = 'FAILED'
        
        self.test_results['concurrent_user_capacity'] = {
            'status': status,
            'results': results,
            'requirement': self.performance_requirements['concurrent_users']
        }
    
    async def test_page_load_performance(self):
        """测试页面加载性能"""
        logger.info("Testing page load performance...")
        
        pages_to_test = [
            '/',
            '/login',
            '/dashboard',
            '/lawyer-workspace',
            '/user-workspace'
        ]
        
        page_load_times = {}
        
        async with aiohttp.ClientSession() as session:
            for page in pages_to_test:
                load_times = []
                
                for i in range(10):  # 每个页面测试10次
                    start_time = time.time()
                    try:
                        async with session.get(
                            f"{self.base_url}{page}",
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            await response.text()
                            load_time = time.time() - start_time
                            load_times.append(load_time)
                    except Exception as e:
                        logger.warning(f"Page load test for {page} failed: {e}")
                    
                    await asyncio.sleep(0.1)
                
                if load_times:
                    avg_load_time = statistics.mean(load_times)
                    page_load_times[page] = {
                        'average': avg_load_time,
                        'maximum': max(load_times),
                        'minimum': min(load_times),
                        'sample_size': len(load_times)
                    }
                    
                    logger.info(f"Page {page} - Avg load time: {avg_load_time:.3f}s")
        
        # 计算整体页面加载性能
        if page_load_times:
            all_avg_times = [times['average'] for times in page_load_times.values()]
            overall_avg = statistics.mean(all_avg_times)
            status = 'PASSED' if overall_avg < self.performance_requirements['page_load_time'] else 'FAILED'
        else:
            overall_avg = 0
            status = 'FAILED'
        
        self.test_results['page_load_performance'] = {
            'status': status,
            'overall_average': overall_avg,
            'page_details': page_load_times,
            'requirement': self.performance_requirements['page_load_time']
        }
    
    async def test_system_resource_usage(self):
        """测试系统资源使用情况"""
        logger.info("Testing system resource usage...")
        
        # 监控系统资源使用情况
        cpu_samples = []
        memory_samples = []
        
        for i in range(30):  # 监控30秒
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            cpu_samples.append(cpu_percent)
            memory_samples.append(memory_percent)
        
        avg_cpu = statistics.mean(cpu_samples)
        max_cpu = max(cpu_samples)
        avg_memory = statistics.mean(memory_samples)
        max_memory = max(memory_samples)
        
        # 获取磁盘使用情况
        disk_usage = psutil.disk_usage('/')
        disk_percent = (disk_usage.used / disk_usage.total) * 100
        
        self.test_results['system_resource_usage'] = {
            'status': 'PASSED' if max_cpu < 80 and max_memory < 85 else 'WARNING',
            'cpu': {
                'average': avg_cpu,
                'maximum': max_cpu,
                'samples': len(cpu_samples)
            },
            'memory': {
                'average': avg_memory,
                'maximum': max_memory,
                'samples': len(memory_samples)
            },
            'disk': {
                'usage_percent': disk_percent,
                'free_gb': disk_usage.free / (1024**3),
                'total_gb': disk_usage.total / (1024**3)
            }
        }
        
        logger.info(f"System resources - CPU: {avg_cpu:.1f}% avg, {max_cpu:.1f}% max; "
                   f"Memory: {avg_memory:.1f}% avg, {max_memory:.1f}% max; "
                   f"Disk: {disk_percent:.1f}% used")
    
    async def test_database_performance(self):
        """测试数据库性能"""
        logger.info("Testing database performance...")
        
        # 测试数据库连接和查询性能
        query_times = []
        
        async with aiohttp.ClientSession() as session:
            for i in range(20):
                start_time = time.time()
                try:
                    async with session.get(
                        f"{self.base_url}/api/v1/health/db",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        await response.text()
                        query_time = time.time() - start_time
                        query_times.append(query_time)
                except Exception as e:
                    logger.warning(f"Database test {i} failed: {e}")
                
                await asyncio.sleep(0.1)
        
        if query_times:
            avg_query_time = statistics.mean(query_times)
            max_query_time = max(query_times)
            
            self.test_results['database_performance'] = {
                'status': 'PASSED' if avg_query_time < 0.5 else 'WARNING',
                'average_query_time': avg_query_time,
                'maximum_query_time': max_query_time,
                'sample_size': len(query_times)
            }
            
            logger.info(f"Database performance - Avg query time: {avg_query_time:.3f}s")
        else:
            self.test_results['database_performance'] = {
                'status': 'FAILED',
                'error': 'No successful database queries'
            }
    
    async def test_cache_performance(self):
        """测试缓存性能"""
        logger.info("Testing cache performance...")
        
        # 测试缓存命中率和响应时间
        cache_tests = []
        
        async with aiohttp.ClientSession() as session:
            # 第一次请求（缓存未命中）
            for i in range(10):
                start_time = time.time()
                try:
                    async with session.get(
                        f"{self.base_url}/api/v1/config/system",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        await response.text()
                        response_time = time.time() - start_time
                        cache_tests.append({
                            'request_type': 'first',
                            'response_time': response_time
                        })
                except Exception as e:
                    logger.warning(f"Cache test (first) {i} failed: {e}")
                
                await asyncio.sleep(0.1)
            
            # 第二次请求（应该缓存命中）
            for i in range(10):
                start_time = time.time()
                try:
                    async with session.get(
                        f"{self.base_url}/api/v1/config/system",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        await response.text()
                        response_time = time.time() - start_time
                        cache_tests.append({
                            'request_type': 'cached',
                            'response_time': response_time
                        })
                except Exception as e:
                    logger.warning(f"Cache test (cached) {i} failed: {e}")
                
                await asyncio.sleep(0.1)
        
        if cache_tests:
            first_requests = [t for t in cache_tests if t['request_type'] == 'first']
            cached_requests = [t for t in cache_tests if t['request_type'] == 'cached']
            
            if first_requests and cached_requests:
                avg_first_time = statistics.mean([r['response_time'] for r in first_requests])
                avg_cached_time = statistics.mean([r['response_time'] for r in cached_requests])
                
                # 缓存应该显著提高响应速度
                cache_improvement = (avg_first_time - avg_cached_time) / avg_first_time * 100
                
                self.test_results['cache_performance'] = {
                    'status': 'PASSED' if cache_improvement > 20 else 'WARNING',  # 至少20%的性能提升
                    'first_request_avg': avg_first_time,
                    'cached_request_avg': avg_cached_time,
                    'improvement_percent': cache_improvement,
                    'sample_size': len(cache_tests)
                }
                
                logger.info(f"Cache performance - First: {avg_first_time:.3f}s, "
                          f"Cached: {avg_cached_time:.3f}s, "
                          f"Improvement: {cache_improvement:.1f}%")
            else:
                self.test_results['cache_performance'] = {
                    'status': 'FAILED',
                    'error': 'Insufficient test data'
                }
        else:
            self.test_results['cache_performance'] = {
                'status': 'FAILED',
                'error': 'No successful cache tests'
            }
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """生成性能测试报告"""
        report = {
            'test_timestamp': datetime.now().isoformat(),
            'performance_requirements': self.performance_requirements,
            'test_results': self.test_results,
            'summary': {
                'total_tests': len(self.test_results),
                'passed_tests': len([r for r in self.test_results.values() if r.get('status') == 'PASSED']),
                'failed_tests': len([r for r in self.test_results.values() if r.get('status') == 'FAILED']),
                'warning_tests': len([r for r in self.test_results.values() if r.get('status') == 'WARNING'])
            }
        }
        
        # 计算总体性能评分
        total_score = 0
        max_score = 0
        
        for test_name, result in self.test_results.items():
            max_score += 100
            if result.get('status') == 'PASSED':
                total_score += 100
            elif result.get('status') == 'WARNING':
                total_score += 70
            # FAILED tests get 0 points
        
        report['summary']['overall_score'] = (total_score / max_score * 100) if max_score > 0 else 0
        
        # 性能要求达标情况
        requirements_met = []
        for test_name, result in self.test_results.items():
            if result.get('status') == 'PASSED':
                requirements_met.append(test_name)
        
        report['summary']['requirements_met'] = requirements_met
        report['summary']['requirements_met_percentage'] = len(requirements_met) / len(self.performance_requirements) * 100
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """保存测试报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_test_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Performance test report saved to: {filename}")

async def main():
    """主函数"""
    # 创建性能测试套件
    test_suite = PerformanceTestSuite()
    
    # 运行所有测试
    report = await test_suite.run_all_tests()
    
    # 保存报告
    test_suite.save_report(report)
    
    # 打印摘要
    summary = report['summary']
    print("\n" + "="*60)
    print("PERFORMANCE TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Warnings: {summary['warning_tests']}")
    print(f"Overall Score: {summary['overall_score']:.1f}%")
    print(f"Requirements Met: {summary['requirements_met_percentage']:.1f}%")
    print("="*60)
    
    # 详细结果
    for test_name, result in report['test_results'].items():
        status = result.get('status', 'UNKNOWN')
        print(f"{test_name}: {status}")
        if 'error' in result:
            print(f"  Error: {result['error']}")
    
    print("\nPerformance optimization test completed!")

if __name__ == "__main__":
    asyncio.run(main())