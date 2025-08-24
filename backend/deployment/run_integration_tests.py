#!/usr/bin/env python3
"""
集成测试运行器
提供命令行接口来运行各种集成测试
"""

import os
import sys
import asyncio
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.deployment.integration_test_framework import (
    IntegrationTestFramework,
    LoadTestConfig
)


class TestRunner:
    """测试运行器"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.framework = IntegrationTestFramework(project_root)
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def run_end_to_end_test(self, environment: str = "integration") -> Dict[str, Any]:
        """运行端到端测试"""
        self.logger.info(f"Starting end-to-end test in {environment} environment")
        
        try:
            result = await self.framework.run_end_to_end_deployment_test(environment)
            
            # 打印测试结果摘要
            self._print_test_summary("End-to-End Test", result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"End-to-end test failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def run_multi_environment_test(self, environments: List[str] = None) -> Dict[str, Any]:
        """运行多环境测试"""
        if environments is None:
            environments = ["unit", "integration"]
        
        self.logger.info(f"Starting multi-environment test: {environments}")
        
        try:
            result = await self.framework.run_multi_environment_tests(environments)
            
            # 打印测试结果摘要
            self._print_multi_env_summary(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Multi-environment test failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def run_performance_test(
        self, 
        environment: str = "integration",
        load_level: str = "medium"
    ) -> Dict[str, Any]:
        """运行性能测试"""
        self.logger.info(f"Starting performance test in {environment} environment")
        
        # 配置负载测试参数
        load_configs = {
            "light": LoadTestConfig(
                concurrent_users=5,
                duration_seconds=30,
                ramp_up_seconds=5
            ),
            "medium": LoadTestConfig(
                concurrent_users=20,
                duration_seconds=120,
                ramp_up_seconds=20
            ),
            "heavy": LoadTestConfig(
                concurrent_users=50,
                duration_seconds=300,
                ramp_up_seconds=60
            )
        }
        
        load_config = load_configs.get(load_level, load_configs["medium"])
        
        try:
            result = await self.framework.run_performance_stress_tests(
                environment, load_config
            )
            
            # 打印性能测试结果摘要
            self._print_performance_summary(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Performance test failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def generate_summary_report(self, days: int = 7) -> Dict[str, Any]:
        """生成测试摘要报告"""
        self.logger.info(f"Generating test summary report for last {days} days")
        
        try:
            summary = self.framework.generate_test_summary_report(days)
            
            # 打印摘要报告
            self._print_summary_report(summary)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate summary report: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def _print_test_summary(self, test_name: str, result: Dict[str, Any]):
        """打印测试结果摘要"""
        print(f"\n{'='*60}")
        print(f"{test_name} Results")
        print(f"{'='*60}")
        
        status = result.get("overall_status", "unknown")
        print(f"Overall Status: {status.upper()}")
        
        if "duration_seconds" in result:
            print(f"Duration: {result['duration_seconds']:.2f} seconds")
        
        # 部署结果
        if "deployment_result" in result:
            deployment = result["deployment_result"]
            if isinstance(deployment, dict) and "deployment_result" in deployment:
                deploy_status = deployment["deployment_result"].get("overall_status", "unknown")
                print(f"Deployment Status: {deploy_status.upper()}")
        
        # 验证结果
        if "verification_result" in result:
            verification = result["verification_result"]
            if isinstance(verification, dict) and "verification_result" in verification:
                verify_data = verification["verification_result"]
                if "test_summary" in verify_data:
                    summary = verify_data["test_summary"]
                    print(f"Verification Tests: {summary.get('passed', 0)}/{summary.get('total', 0)} passed")
        
        print(f"{'='*60}\n")
    
    def _print_multi_env_summary(self, result: Dict[str, Any]):
        """打印多环境测试摘要"""
        print(f"\n{'='*60}")
        print("Multi-Environment Test Results")
        print(f"{'='*60}")
        
        summary = result.get("summary", {})
        print(f"Total Environments: {summary.get('total_environments', 0)}")
        print(f"Successful: {summary.get('successful_environments', 0)}")
        print(f"Failed: {summary.get('failed_environments', 0)}")
        print(f"Success Rate: {summary.get('success_rate', 0):.1f}%")
        
        print(f"\nEnvironment Details:")
        print(f"{'-'*40}")
        
        for env_name, env_result in result.get("results", {}).items():
            status = env_result.get("overall_status", env_result.get("status", "unknown"))
            print(f"{env_name:15}: {status.upper()}")
        
        print(f"{'='*60}\n")
    
    def _print_performance_summary(self, result: Dict[str, Any]):
        """打印性能测试摘要"""
        print(f"\n{'='*60}")
        print("Performance Test Results")
        print(f"{'='*60}")
        
        # 基准性能
        baseline = result.get("baseline_metrics", {})
        if baseline and "avg_response_time_ms" in baseline:
            print(f"Baseline Response Time: {baseline['avg_response_time_ms']:.2f}ms")
        
        # 负载测试结果
        load_test = result.get("load_test_results", {})
        if load_test:
            print(f"Load Test Success Rate: {load_test.get('success_rate', 0):.1f}%")
            print(f"Load Test Throughput: {load_test.get('throughput_rps', 0):.2f} RPS")
        
        # 压力测试结果
        stress_test = result.get("stress_test_results", {})
        if stress_test:
            print(f"Stress Test Success Rate: {stress_test.get('success_rate', 0):.1f}%")
            print(f"Stress Test Throughput: {stress_test.get('throughput_rps', 0):.2f} RPS")
        
        # 性能分析
        analysis = result.get("performance_analysis", {})
        if analysis:
            print(f"\nPerformance Analysis:")
            print(f"Baseline: {analysis.get('baseline_performance', 'unknown')}")
            print(f"Load Test: {analysis.get('load_test_performance', 'unknown')}")
            print(f"Stress Test: {analysis.get('stress_test_performance', 'unknown')}")
        
        print(f"{'='*60}\n")
    
    def _print_summary_report(self, summary: Dict[str, Any]):
        """打印摘要报告"""
        print(f"\n{'='*60}")
        print(f"Test Summary Report ({summary.get('period_days', 0)} days)")
        print(f"{'='*60}")
        
        print(f"Total Tests: {summary.get('total_tests', 0)}")
        print(f"Successful: {summary.get('successful_tests', 0)}")
        print(f"Failed: {summary.get('failed_tests', 0)}")
        print(f"Success Rate: {summary.get('success_rate', 0):.1f}%")
        
        # 按测试类型统计
        test_types = summary.get("test_types", {})
        if test_types:
            print(f"\nBy Test Type:")
            print(f"{'-'*30}")
            for test_type, stats in test_types.items():
                success_rate = (stats["success"] / stats["count"]) * 100 if stats["count"] > 0 else 0
                print(f"{test_type:15}: {stats['success']}/{stats['count']} ({success_rate:.1f}%)")
        
        # 按环境统计
        environments = summary.get("environments", {})
        if environments:
            print(f"\nBy Environment:")
            print(f"{'-'*30}")
            for env_name, stats in environments.items():
                success_rate = (stats["success"] / stats["count"]) * 100 if stats["count"] > 0 else 0
                print(f"{env_name:15}: {stats['success']}/{stats['count']} ({success_rate:.1f}%)")
        
        print(f"{'='*60}\n")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Integration Test Runner for Lawsker Deployment System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run end-to-end test in integration environment
  python run_integration_tests.py e2e --environment integration

  # Run multi-environment tests
  python run_integration_tests.py multi-env --environments unit integration

  # Run performance test with heavy load
  python run_integration_tests.py performance --load-level heavy

  # Generate summary report for last 30 days
  python run_integration_tests.py summary --days 30
        """
    )
    
    parser.add_argument(
        "test_type",
        choices=["e2e", "multi-env", "performance", "summary"],
        help="Type of test to run"
    )
    
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root directory (default: current directory)"
    )
    
    parser.add_argument(
        "--environment",
        default="integration",
        help="Test environment for single environment tests (default: integration)"
    )
    
    parser.add_argument(
        "--environments",
        nargs="+",
        default=["unit", "integration"],
        help="List of environments for multi-environment tests"
    )
    
    parser.add_argument(
        "--load-level",
        choices=["light", "medium", "heavy"],
        default="medium",
        help="Load level for performance tests (default: medium)"
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days for summary report (default: 7)"
    )
    
    parser.add_argument(
        "--output",
        help="Output file for test results (JSON format)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建测试运行器
    runner = TestRunner(args.project_root)
    
    try:
        # 根据测试类型运行相应的测试
        if args.test_type == "e2e":
            result = await runner.run_end_to_end_test(args.environment)
        elif args.test_type == "multi-env":
            result = await runner.run_multi_environment_test(args.environments)
        elif args.test_type == "performance":
            result = await runner.run_performance_test(args.environment, args.load_level)
        elif args.test_type == "summary":
            result = runner.generate_summary_report(args.days)
        else:
            print(f"Unknown test type: {args.test_type}")
            sys.exit(1)
        
        # 保存结果到文件
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"Results saved to: {output_path}")
        
        # 检查测试结果并设置退出码
        if result.get("status") == "error" or result.get("overall_status") == "failed":
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Test execution failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())