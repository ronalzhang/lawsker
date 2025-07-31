#!/usr/bin/env python3
"""
自动化运维功能测试脚本
测试健康监控、告警自动化、部署等功能
"""
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.health_monitor import health_monitor, HealthStatus
from app.services.alert_automation import alert_automation, AutomationRule, ActionType
from app.scripts.auto_deploy import DeploymentManager, DatabaseBackupManager
from app.core.logging import get_logger

logger = get_logger(__name__)

class AutomationTester:
    """自动化功能测试器"""
    
    def __init__(self):
        self.test_results = []
    
    def log_test_result(self, test_name: str, success: bool, message: str = "", details: dict = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {message}")
    
    async def test_health_monitoring(self):
        """测试健康监控功能"""
        logger.info("Testing health monitoring...")
        
        try:
            # 测试健康检查
            health_data = await health_monitor.get_health_status()
            
            # 验证返回数据结构
            required_fields = ["overall_status", "timestamp", "components", "summary"]
            for field in required_fields:
                if field not in health_data:
                    self.log_test_result(
                        "health_check_structure",
                        False,
                        f"Missing field: {field}"
                    )
                    return
            
            self.log_test_result(
                "health_check_structure",
                True,
                "Health check data structure is valid",
                {"components_count": len(health_data["components"])}
            )
            
            # 测试各组件健康检查
            for component_name, component_data in health_data["components"].items():
                if "status" in component_data and "metrics" in component_data:
                    self.log_test_result(
                        f"health_check_{component_name}",
                        True,
                        f"Component {component_name} health check successful",
                        {"status": component_data["status"]}
                    )
                else:
                    self.log_test_result(
                        f"health_check_{component_name}",
                        False,
                        f"Component {component_name} health check failed"
                    )
            
            # 测试监控服务启动/停止
            if not health_monitor.is_running:
                await health_monitor.start_monitoring()
                await asyncio.sleep(2)  # 等待服务启动
                
                if health_monitor.is_running:
                    self.log_test_result(
                        "health_monitor_start",
                        True,
                        "Health monitoring service started successfully"
                    )
                else:
                    self.log_test_result(
                        "health_monitor_start",
                        False,
                        "Failed to start health monitoring service"
                    )
                
                await health_monitor.stop_monitoring()
                await asyncio.sleep(1)  # 等待服务停止
                
                if not health_monitor.is_running:
                    self.log_test_result(
                        "health_monitor_stop",
                        True,
                        "Health monitoring service stopped successfully"
                    )
                else:
                    self.log_test_result(
                        "health_monitor_stop",
                        False,
                        "Failed to stop health monitoring service"
                    )
            
        except Exception as e:
            self.log_test_result(
                "health_monitoring",
                False,
                f"Health monitoring test failed: {str(e)}"
            )
    
    async def test_alert_automation(self):
        """测试告警自动化功能"""
        logger.info("Testing alert automation...")
        
        try:
            # 测试规则管理
            test_rule = AutomationRule(
                id="test_rule",
                name="Test Rule",
                description="Test automation rule",
                enabled=True,
                conditions={"component": "test", "status": "warning"},
                actions=[
                    {
                        "type": ActionType.SEND_NOTIFICATION.value,
                        "config": {
                            "channel": "test",
                            "message": "Test notification",
                            "priority": "low"
                        }
                    }
                ],
                cooldown_minutes=1,
                max_executions_per_hour=10,
                priority=1
            )
            
            # 添加测试规则
            alert_automation.add_rule(test_rule)
            
            # 验证规则是否添加成功
            retrieved_rule = alert_automation.get_rule("test_rule")
            if retrieved_rule and retrieved_rule.name == "Test Rule":
                self.log_test_result(
                    "automation_rule_add",
                    True,
                    "Automation rule added successfully"
                )
            else:
                self.log_test_result(
                    "automation_rule_add",
                    False,
                    "Failed to add automation rule"
                )
            
            # 测试规则匹配
            test_alert = {
                "component": "test",
                "status": "warning",
                "message": "Test alert"
            }
            
            if test_rule.matches_alert(test_alert):
                self.log_test_result(
                    "automation_rule_matching",
                    True,
                    "Rule matching works correctly"
                )
            else:
                self.log_test_result(
                    "automation_rule_matching",
                    False,
                    "Rule matching failed"
                )
            
            # 测试统计信息
            stats = alert_automation.get_statistics()
            if isinstance(stats, dict) and "total_rules" in stats:
                self.log_test_result(
                    "automation_statistics",
                    True,
                    "Statistics retrieval successful",
                    {"total_rules": stats["total_rules"]}
                )
            else:
                self.log_test_result(
                    "automation_statistics",
                    False,
                    "Failed to get statistics"
                )
            
            # 清理测试规则
            alert_automation.remove_rule("test_rule")
            
        except Exception as e:
            self.log_test_result(
                "alert_automation",
                False,
                f"Alert automation test failed: {str(e)}"
            )
    
    async def test_deployment_management(self):
        """测试部署管理功能"""
        logger.info("Testing deployment management...")
        
        try:
            deployment_manager = DeploymentManager()
            
            # 测试配置加载
            if deployment_manager.config and "environments" in deployment_manager.config:
                self.log_test_result(
                    "deployment_config_load",
                    True,
                    "Deployment configuration loaded successfully",
                    {"environments": list(deployment_manager.config["environments"].keys())}
                )
            else:
                self.log_test_result(
                    "deployment_config_load",
                    False,
                    "Failed to load deployment configuration"
                )
            
            # 测试部署状态获取
            status = deployment_manager.get_deployment_status()
            if isinstance(status, dict):
                self.log_test_result(
                    "deployment_status",
                    True,
                    "Deployment status retrieval successful",
                    {"config_loaded": "config" in status}
                )
            else:
                self.log_test_result(
                    "deployment_status",
                    False,
                    "Failed to get deployment status"
                )
            
        except Exception as e:
            self.log_test_result(
                "deployment_management",
                False,
                f"Deployment management test failed: {str(e)}"
            )
    
    async def test_backup_management(self):
        """测试备份管理功能"""
        logger.info("Testing backup management...")
        
        try:
            # 使用测试数据库URL
            test_db_url = "postgresql://test:test@localhost:5432/test_db"
            backup_manager = DatabaseBackupManager(test_db_url)
            
            # 测试备份目录创建
            if backup_manager.backup_dir.exists():
                self.log_test_result(
                    "backup_directory",
                    True,
                    "Backup directory exists",
                    {"path": str(backup_manager.backup_dir)}
                )
            else:
                self.log_test_result(
                    "backup_directory",
                    False,
                    "Backup directory does not exist"
                )
            
            # 测试备份配置方法
            should_compress = backup_manager._should_compress()
            should_encrypt = backup_manager._should_encrypt()
            
            self.log_test_result(
                "backup_configuration",
                True,
                "Backup configuration methods work",
                {
                    "compression": should_compress,
                    "encryption": should_encrypt
                }
            )
            
        except Exception as e:
            self.log_test_result(
                "backup_management",
                False,
                f"Backup management test failed: {str(e)}"
            )
    
    async def test_configuration_validation(self):
        """测试配置验证功能"""
        logger.info("Testing configuration validation...")
        
        try:
            from backend.config.automation_config import validate_config, get_automation_config
            
            # 测试配置验证
            errors = validate_config()
            
            self.log_test_result(
                "config_validation",
                len(errors) == 0,
                f"Configuration validation completed with {len(errors)} errors",
                {"errors": errors}
            )
            
            # 测试配置获取
            config = get_automation_config()
            
            required_sections = ["settings", "health_check", "alert_automation", "deployment"]
            missing_sections = [section for section in required_sections if section not in config]
            
            self.log_test_result(
                "config_structure",
                len(missing_sections) == 0,
                f"Configuration structure validation",
                {"missing_sections": missing_sections}
            )
            
        except Exception as e:
            self.log_test_result(
                "configuration_validation",
                False,
                f"Configuration validation test failed: {str(e)}"
            )
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("Starting automation tests...")
        
        test_methods = [
            self.test_health_monitoring,
            self.test_alert_automation,
            self.test_deployment_management,
            self.test_backup_management,
            self.test_configuration_validation
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                logger.error(f"Test method {test_method.__name__} failed: {str(e)}")
        
        # 生成测试报告
        self.generate_test_report()
    
    def generate_test_report(self):
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": round(success_rate, 2)
            },
            "test_results": self.test_results,
            "generated_at": datetime.now().isoformat()
        }
        
        # 保存测试报告
        report_file = Path("automation_test_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # 打印测试摘要
        print("\n" + "="*60)
        print("AUTOMATION TEST REPORT")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Report saved to: {report_file.absolute()}")
        print("="*60)
        
        # 打印失败的测试
        if failed_tests > 0:
            print("\nFAILED TESTS:")
            print("-"*40)
            for result in self.test_results:
                if not result["success"]:
                    print(f"❌ {result['test_name']}: {result['message']}")
        
        print()

async def main():
    """主函数"""
    tester = AutomationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        sys.exit(1)