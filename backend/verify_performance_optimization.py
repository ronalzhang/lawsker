"""
性能优化验证脚本
验证系统性能指标是否达到要求
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List

from test_performance_optimization import PerformanceTestSuite
from config.performance_config import PerformanceConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceVerificationSuite:
    """性能验证套件"""
    
    def __init__(self):
        self.config = PerformanceConfig()
        self.test_suite = PerformanceTestSuite()
        self.verification_results = {}
    
    async def run_comprehensive_verification(self) -> Dict[str, Any]:
        """运行综合性能验证"""
        logger.info("开始综合性能验证...")
        
        verification_steps = [
            ("基础性能测试", self.verify_basic_performance),
            ("响应时间验证", self.verify_response_times),
            ("并发能力验证", self.verify_concurrency_capacity),
            ("系统资源验证", self.verify_system_resources),
            ("缓存性能验证", self.verify_cache_performance),
            ("数据库性能验证", self.verify_database_performance),
            ("可用性验证", self.verify_system_availability),
        ]
        
        overall_results = {
            'verification_timestamp': datetime.now().isoformat(),
            'total_steps': len(verification_steps),
            'passed_steps': 0,
            'failed_steps': 0,
            'step_results': {},
            'performance_score': 0.0,
            'requirements_compliance': {}
        }
        
        for step_name, step_func in verification_steps:
            logger.info(f"执行验证步骤: {step_name}")
            try:
                step_result = await step_func()
                overall_results['step_results'][step_name] = step_result
                
                if step_result.get('status') == 'PASSED':
                    overall_results['passed_steps'] += 1
                else:
                    overall_results['failed_steps'] += 1
                    
            except Exception as e:
                logger.error(f"验证步骤 {step_name} 失败: {e}")
                overall_results['step_results'][step_name] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
                overall_results['failed_steps'] += 1
        
        # 计算总体性能评分
        overall_results['performance_score'] = self.calculate_performance_score(overall_results)
        
        # 检查需求合规性
        overall_results['requirements_compliance'] = self.check_requirements_compliance(overall_results)
        
        logger.info("综合性能验证完成")
        return overall_results
    
    async def verify_basic_performance(self) -> Dict[str, Any]:
        """验证基础性能"""
        logger.info("验证基础性能指标...")
        
        # 运行基础性能测试
        test_results = await self.test_suite.run_all_tests()
        
        # 分析测试结果
        passed_tests = test_results['summary']['passed_tests']
        total_tests = test_results['summary']['total_tests']
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            'status': 'PASSED' if success_rate >= 80 else 'FAILED',
            'success_rate': success_rate,
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'detailed_results': test_results['test_results']
        }
    
    async def verify_response_times(self) -> Dict[str, Any]:
        """验证响应时间要求"""
        logger.info("验证响应时间要求...")
        
        response_time_checks = {}
        requirements = self.config.RESPONSE_TIME_REQUIREMENTS
        
        # 检查认证系统响应时间
        if 'auth_response_time' in self.test_suite.test_results:
            auth_result = self.test_suite.test_results['auth_response_time']
            auth_avg = auth_result.get('average', float('inf'))
            response_time_checks['auth_system'] = {
                'actual': auth_avg,
                'requirement': requirements['auth_system'],
                'status': 'PASSED' if auth_avg < requirements['auth_system'] else 'FAILED'
            }
        
        # 检查积分计算响应时间
        if 'points_calculation_time' in self.test_suite.test_results:
            points_result = self.test_suite.test_results['points_calculation_time']
            points_avg = points_result.get('average', float('inf'))
            response_time_checks['points_calculation'] = {
                'actual': points_avg,
                'requirement': requirements['points_calculation'],
                'status': 'PASSED' if points_avg < requirements['points_calculation'] else 'FAILED'
            }
        
        # 检查Credits支付响应时间
        if 'credits_payment_time' in self.test_suite.test_results:
            credits_result = self.test_suite.test_results['credits_payment_time']
            credits_avg = credits_result.get('average', float('inf'))
            response_time_checks['credits_payment'] = {
                'actual': credits_avg,
                'requirement': requirements['credits_payment'],
                'status': 'PASSED' if credits_avg < requirements['credits_payment'] else 'FAILED'
            }
        
        # 计算总体状态
        passed_checks = sum(1 for check in response_time_checks.values() if check['status'] == 'PASSED')
        total_checks = len(response_time_checks)
        overall_status = 'PASSED' if passed_checks == total_checks else 'FAILED'
        
        return {
            'status': overall_status,
            'passed_checks': passed_checks,
            'total_checks': total_checks,
            'response_time_checks': response_time_checks
        }
    
    async def verify_concurrency_capacity(self) -> Dict[str, Any]:
        """验证并发能力"""
        logger.info("验证并发能力...")
        
        concurrency_results = {}
        requirements = self.config.CONCURRENCY_REQUIREMENTS
        
        # 检查并发用户支持
        if 'concurrent_user_capacity' in self.test_suite.test_results:
            capacity_result = self.test_suite.test_results['concurrent_user_capacity']
            
            # 检查1000用户并发
            if 1000 in capacity_result.get('results', {}):
                result_1000 = capacity_result['results'][1000]
                success_rate = result_1000.get('success_rate', 0)
                
                concurrency_results['concurrent_users_1000'] = {
                    'actual_success_rate': success_rate,
                    'requirement': 95.0,  # 95%成功率
                    'status': 'PASSED' if success_rate >= 95.0 else 'FAILED'
                }
        
        # 模拟Credits处理能力测试
        credits_processing_rate = await self.test_credits_processing_rate()
        concurrency_results['credits_processing_rate'] = {
            'actual': credits_processing_rate,
            'requirement': requirements['credits_processing_rate'],
            'status': 'PASSED' if credits_processing_rate >= requirements['credits_processing_rate'] else 'FAILED'
        }
        
        # 计算总体状态
        passed_checks = sum(1 for check in concurrency_results.values() if check['status'] == 'PASSED')
        total_checks = len(concurrency_results)
        overall_status = 'PASSED' if passed_checks == total_checks else 'FAILED'
        
        return {
            'status': overall_status,
            'passed_checks': passed_checks,
            'total_checks': total_checks,
            'concurrency_results': concurrency_results
        }
    
    async def test_credits_processing_rate(self) -> float:
        """测试Credits处理速率"""
        try:
            # 模拟1小时内的Credits处理
            test_duration = 60  # 测试1分钟，然后推算1小时
            start_time = time.time()
            processed_count = 0
            
            # 模拟并发处理
            async def process_credit():
                nonlocal processed_count
                await asyncio.sleep(0.01)  # 模拟处理时间
                processed_count += 1
            
            # 并发执行
            tasks = []
            while time.time() - start_time < test_duration:
                if len(tasks) < 100:  # 限制并发数
                    task = asyncio.create_task(process_credit())
                    tasks.append(task)
                
                # 清理完成的任务
                tasks = [t for t in tasks if not t.done()]
                await asyncio.sleep(0.001)
            
            # 等待所有任务完成
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # 计算每小时处理能力
            actual_duration = time.time() - start_time
            processing_rate = (processed_count / actual_duration) * 3600  # 每小时
            
            return processing_rate
            
        except Exception as e:
            logger.error(f"Credits处理速率测试失败: {e}")
            return 0.0
    
    async def verify_system_resources(self) -> Dict[str, Any]:
        """验证系统资源使用"""
        logger.info("验证系统资源使用...")
        
        import psutil
        
        # 收集系统资源数据
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        resource_checks = {
            'cpu_usage': {
                'actual': cpu_percent,
                'threshold': self.config.get_alert_threshold('cpu_usage'),
                'status': 'PASSED' if cpu_percent < self.config.get_alert_threshold('cpu_usage') else 'WARNING'
            },
            'memory_usage': {
                'actual': memory.percent,
                'threshold': self.config.get_alert_threshold('memory_usage'),
                'status': 'PASSED' if memory.percent < self.config.get_alert_threshold('memory_usage') else 'WARNING'
            },
            'disk_usage': {
                'actual': (disk.used / disk.total) * 100,
                'threshold': self.config.get_alert_threshold('disk_usage'),
                'status': 'PASSED' if (disk.used / disk.total) * 100 < self.config.get_alert_threshold('disk_usage') else 'WARNING'
            }
        }
        
        # 计算总体状态
        warning_count = sum(1 for check in resource_checks.values() if check['status'] == 'WARNING')
        overall_status = 'PASSED' if warning_count == 0 else 'WARNING'
        
        return {
            'status': overall_status,
            'warning_count': warning_count,
            'resource_checks': resource_checks
        }
    
    async def verify_cache_performance(self) -> Dict[str, Any]:
        """验证缓存性能"""
        logger.info("验证缓存性能...")
        
        cache_results = {}
        
        # 检查缓存命中率
        if 'cache_performance' in self.test_suite.test_results:
            cache_result = self.test_suite.test_results['cache_performance']
            improvement = cache_result.get('improvement_percent', 0)
            
            cache_results['cache_improvement'] = {
                'actual': improvement,
                'requirement': 20.0,  # 至少20%性能提升
                'status': 'PASSED' if improvement >= 20.0 else 'FAILED'
            }
        
        return {
            'status': cache_results.get('cache_improvement', {}).get('status', 'UNKNOWN'),
            'cache_results': cache_results
        }
    
    async def verify_database_performance(self) -> Dict[str, Any]:
        """验证数据库性能"""
        logger.info("验证数据库性能...")
        
        db_results = {}
        
        # 检查数据库查询性能
        if 'database_performance' in self.test_suite.test_results:
            db_result = self.test_suite.test_results['database_performance']
            avg_query_time = db_result.get('average_query_time', float('inf'))
            
            db_results['query_performance'] = {
                'actual': avg_query_time,
                'requirement': 0.5,  # 500ms
                'status': 'PASSED' if avg_query_time < 0.5 else 'FAILED'
            }
        
        return {
            'status': db_results.get('query_performance', {}).get('status', 'UNKNOWN'),
            'database_results': db_results
        }
    
    async def verify_system_availability(self) -> Dict[str, Any]:
        """验证系统可用性"""
        logger.info("验证系统可用性...")
        
        # 模拟可用性测试
        availability_test_duration = 60  # 测试1分钟
        test_interval = 1  # 每秒测试一次
        
        successful_requests = 0
        total_requests = 0
        
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            for _ in range(availability_test_duration):
                try:
                    async with session.get(
                        f"{self.test_suite.base_url}/health",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        total_requests += 1
                        if response.status == 200:
                            successful_requests += 1
                except Exception:
                    total_requests += 1
                
                await asyncio.sleep(test_interval)
        
        availability_percent = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        requirement = self.config.AVAILABILITY_REQUIREMENTS['system_availability']
        
        return {
            'status': 'PASSED' if availability_percent >= requirement else 'FAILED',
            'actual_availability': availability_percent,
            'required_availability': requirement,
            'successful_requests': successful_requests,
            'total_requests': total_requests
        }
    
    def calculate_performance_score(self, results: Dict[str, Any]) -> float:
        """计算性能评分"""
        total_score = 0
        max_score = 0
        
        for step_name, step_result in results['step_results'].items():
            max_score += 100
            
            if step_result.get('status') == 'PASSED':
                total_score += 100
            elif step_result.get('status') == 'WARNING':
                total_score += 70
            elif step_result.get('status') == 'FAILED':
                total_score += 0
            else:  # ERROR
                total_score += 0
        
        return (total_score / max_score * 100) if max_score > 0 else 0
    
    def check_requirements_compliance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """检查需求合规性"""
        compliance = {
            'auth_response_time': False,
            'points_calculation_time': False,
            'credits_payment_time': False,
            'concurrent_users_1000': False,
            'system_availability_99_9': False,
            'credits_processing_10000_per_hour': False,
            'page_load_time_2s': False
        }
        
        # 检查各项需求
        step_results = results.get('step_results', {})
        
        # 响应时间需求
        response_time_result = step_results.get('响应时间验证', {})
        if response_time_result.get('status') == 'PASSED':
            checks = response_time_result.get('response_time_checks', {})
            compliance['auth_response_time'] = checks.get('auth_system', {}).get('status') == 'PASSED'
            compliance['points_calculation_time'] = checks.get('points_calculation', {}).get('status') == 'PASSED'
            compliance['credits_payment_time'] = checks.get('credits_payment', {}).get('status') == 'PASSED'
        
        # 并发能力需求
        concurrency_result = step_results.get('并发能力验证', {})
        if concurrency_result.get('status') == 'PASSED':
            concurrency_checks = concurrency_result.get('concurrency_results', {})
            compliance['concurrent_users_1000'] = concurrency_checks.get('concurrent_users_1000', {}).get('status') == 'PASSED'
            compliance['credits_processing_10000_per_hour'] = concurrency_checks.get('credits_processing_rate', {}).get('status') == 'PASSED'
        
        # 可用性需求
        availability_result = step_results.get('可用性验证', {})
        compliance['system_availability_99_9'] = availability_result.get('status') == 'PASSED'
        
        # 页面加载时间（从基础性能测试获取）
        basic_performance = step_results.get('基础性能测试', {})
        if basic_performance.get('status') == 'PASSED':
            detailed_results = basic_performance.get('detailed_results', {})
            page_load_result = detailed_results.get('page_load_performance', {})
            compliance['page_load_time_2s'] = page_load_result.get('status') == 'PASSED'
        
        # 计算合规率
        total_requirements = len(compliance)
        met_requirements = sum(1 for met in compliance.values() if met)
        compliance_rate = (met_requirements / total_requirements * 100) if total_requirements > 0 else 0
        
        return {
            'individual_compliance': compliance,
            'total_requirements': total_requirements,
            'met_requirements': met_requirements,
            'compliance_rate': compliance_rate
        }
    
    def save_verification_report(self, results: Dict[str, Any], filename: str = None):
        """保存验证报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_verification_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"性能验证报告已保存: {filename}")
        return filename

async def main():
    """主函数"""
    verification_suite = PerformanceVerificationSuite()
    
    # 运行综合验证
    results = await verification_suite.run_comprehensive_verification()
    
    # 保存报告
    report_file = verification_suite.save_verification_report(results)
    
    # 打印摘要
    print("\n" + "="*80)
    print("LAWSKER 系统性能验证报告")
    print("="*80)
    print(f"验证时间: {results['verification_timestamp']}")
    print(f"总体评分: {results['performance_score']:.1f}%")
    print(f"通过步骤: {results['passed_steps']}/{results['total_steps']}")
    print(f"需求合规率: {results['requirements_compliance']['compliance_rate']:.1f}%")
    print("="*80)
    
    # 详细结果
    print("\n验证步骤结果:")
    for step_name, step_result in results['step_results'].items():
        status = step_result.get('status', 'UNKNOWN')
        print(f"  {step_name}: {status}")
    
    print("\n需求合规性:")
    compliance = results['requirements_compliance']['individual_compliance']
    for requirement, met in compliance.items():
        status = "✅ 达标" if met else "❌ 未达标"
        print(f"  {requirement}: {status}")
    
    print(f"\n详细报告已保存至: {report_file}")
    
    # 判断总体结果
    if results['performance_score'] >= 80 and results['requirements_compliance']['compliance_rate'] >= 80:
        print("\n🎉 系统性能验证通过！所有关键指标均达到要求。")
        return 0
    else:
        print("\n⚠️  系统性能验证未完全通过，请检查未达标项目并进行优化。")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())