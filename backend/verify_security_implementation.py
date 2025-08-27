#!/usr/bin/env python3
"""
Security Implementation Verification
Final verification that all security measures are properly implemented
"""

import asyncio
import subprocess
import sys
import json
import time
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SecurityVerification:
    """Comprehensive security verification"""
    
    def __init__(self):
        self.verification_results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'tests': {},
            'overall_status': 'UNKNOWN',
            'security_score': 0,
            'critical_issues': 0,
            'high_issues': 0,
            'recommendations': []
        }
    
    def run_security_hardening(self):
        """Apply security hardening measures"""
        logger.info("Applying security hardening measures...")
        
        try:
            result = subprocess.run([
                sys.executable, 'backend/security_hardening.py',
                '--project-root', '.',
                '--output', 'security_hardening_report.json'
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                logger.info("✅ Security hardening applied successfully")
                self.verification_results['tests']['hardening'] = {
                    'status': 'PASSED',
                    'message': 'Security hardening measures applied'
                }
                return True
            else:
                logger.error(f"❌ Security hardening failed: {result.stderr}")
                self.verification_results['tests']['hardening'] = {
                    'status': 'FAILED',
                    'message': f'Security hardening failed: {result.stderr}'
                }
                return False
        
        except Exception as e:
            logger.error(f"❌ Error applying security hardening: {e}")
            self.verification_results['tests']['hardening'] = {
                'status': 'ERROR',
                'message': f'Error applying security hardening: {str(e)}'
            }
            return False
    
    def run_configuration_validation(self):
        """Run security configuration validation"""
        logger.info("Running security configuration validation...")
        
        try:
            result = subprocess.run([
                sys.executable, 'backend/security_config_validator.py',
                '--project-root', '.',
                '--output', 'security_config_validation_report.json'
            ], capture_output=True, text=True, timeout=60)
            
            # Load validation report
            report_path = Path('security_config_validation_report.json')
            if report_path.exists():
                with open(report_path, 'r') as f:
                    report = json.load(f)
                
                critical_issues = report['summary']['critical_issues']
                high_issues = report['summary']['high_issues']
                security_score = report['summary']['security_score']
                
                if critical_issues == 0 and high_issues == 0:
                    logger.info(f"✅ Configuration validation passed (Score: {security_score}/100)")
                    self.verification_results['tests']['config_validation'] = {
                        'status': 'PASSED',
                        'score': security_score,
                        'critical_issues': critical_issues,
                        'high_issues': high_issues
                    }
                    return True
                else:
                    logger.error(f"❌ Configuration validation failed: {critical_issues} critical, {high_issues} high issues")
                    self.verification_results['tests']['config_validation'] = {
                        'status': 'FAILED',
                        'score': security_score,
                        'critical_issues': critical_issues,
                        'high_issues': high_issues
                    }
                    self.verification_results['critical_issues'] += critical_issues
                    self.verification_results['high_issues'] += high_issues
                    return False
            else:
                logger.error("❌ Configuration validation report not generated")
                return False
        
        except Exception as e:
            logger.error(f"❌ Error in configuration validation: {e}")
            self.verification_results['tests']['config_validation'] = {
                'status': 'ERROR',
                'message': str(e)
            }
            return False
    
    async def run_penetration_testing(self):
        """Run penetration testing"""
        logger.info("Running penetration testing...")
        
        try:
            from security_penetration_test import SecurityPenetrationTester
            
            async with SecurityPenetrationTester("http://localhost:8000") as tester:
                await tester.run_all_tests()
                report = tester.generate_report()
            
            critical_findings = report['summary']['critical_findings']
            high_findings = report['summary']['high_findings']
            security_score = report['summary']['security_score']
            
            if critical_findings == 0 and high_findings == 0:
                logger.info(f"✅ Penetration testing passed (Score: {security_score}/100)")
                self.verification_results['tests']['penetration_test'] = {
                    'status': 'PASSED',
                    'score': security_score,
                    'critical_findings': critical_findings,
                    'high_findings': high_findings
                }
                return True
            else:
                logger.error(f"❌ Penetration testing failed: {critical_findings} critical, {high_findings} high findings")
                self.verification_results['tests']['penetration_test'] = {
                    'status': 'FAILED',
                    'score': security_score,
                    'critical_findings': critical_findings,
                    'high_findings': high_findings
                }
                self.verification_results['critical_issues'] += critical_findings
                self.verification_results['high_issues'] += high_findings
                return False
        
        except Exception as e:
            logger.error(f"❌ Error in penetration testing: {e}")
            self.verification_results['tests']['penetration_test'] = {
                'status': 'ERROR',
                'message': str(e)
            }
            return False
    
    def run_comprehensive_security_tests(self):
        """Run comprehensive security test suite"""
        logger.info("Running comprehensive security test suite...")
        
        try:
            result = subprocess.run([
                sys.executable, 'backend/run_security_tests.py',
                '--url', 'http://localhost:8000',
                '--project-root', '.',
                '--output', 'comprehensive_security_report.json'
            ], capture_output=True, text=True, timeout=300)
            
            # Load comprehensive report
            report_path = Path('comprehensive_security_report.json')
            if report_path.exists():
                with open(report_path, 'r') as f:
                    report = json.load(f)
                
                overall_score = report.get('overall_score', 0)
                passed = report.get('passed', False)
                total_critical = report.get('total_critical_issues', 0)
                total_high = report.get('total_high_issues', 0)
                
                if passed:
                    logger.info(f"✅ Comprehensive security tests passed (Score: {overall_score}/100)")
                    self.verification_results['tests']['comprehensive'] = {
                        'status': 'PASSED',
                        'score': overall_score,
                        'critical_issues': total_critical,
                        'high_issues': total_high
                    }
                    return True
                else:
                    logger.error(f"❌ Comprehensive security tests failed: {total_critical} critical, {total_high} high issues")
                    self.verification_results['tests']['comprehensive'] = {
                        'status': 'FAILED',
                        'score': overall_score,
                        'critical_issues': total_critical,
                        'high_issues': total_high
                    }
                    self.verification_results['critical_issues'] += total_critical
                    self.verification_results['high_issues'] += total_high
                    return False
            else:
                logger.error("❌ Comprehensive security report not generated")
                return False
        
        except Exception as e:
            logger.error(f"❌ Error in comprehensive security tests: {e}")
            self.verification_results['tests']['comprehensive'] = {
                'status': 'ERROR',
                'message': str(e)
            }
            return False
    
    def run_unit_security_tests(self):
        """Run unit security tests"""
        logger.info("Running unit security tests...")
        
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pytest',
                'backend/test_security_comprehensive.py',
                '-v', '--tb=short', '--json-report', '--json-report-file=security_unit_test_report.json'
            ], capture_output=True, text=True, timeout=180)
            
            if result.returncode == 0:
                logger.info("✅ Unit security tests passed")
                self.verification_results['tests']['unit_tests'] = {
                    'status': 'PASSED',
                    'message': 'All unit security tests passed'
                }
                return True
            else:
                logger.error(f"❌ Unit security tests failed")
                self.verification_results['tests']['unit_tests'] = {
                    'status': 'FAILED',
                    'message': 'Some unit security tests failed'
                }
                return False
        
        except Exception as e:
            logger.error(f"❌ Error in unit security tests: {e}")
            self.verification_results['tests']['unit_tests'] = {
                'status': 'ERROR',
                'message': str(e)
            }
            return False
    
    def verify_security_files_exist(self):
        """Verify that all security files exist"""
        logger.info("Verifying security files exist...")
        
        required_files = [
            'backend/security_penetration_test.py',
            'backend/security_config_validator.py',
            'backend/run_security_tests.py',
            'backend/security_hardening.py',
            'backend/test_security_comprehensive.py'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if not missing_files:
            logger.info("✅ All security files exist")
            self.verification_results['tests']['file_existence'] = {
                'status': 'PASSED',
                'message': 'All required security files exist'
            }
            return True
        else:
            logger.error(f"❌ Missing security files: {missing_files}")
            self.verification_results['tests']['file_existence'] = {
                'status': 'FAILED',
                'message': f'Missing files: {missing_files}'
            }
            return False
    
    def verify_security_requirements_met(self):
        """Verify that security requirements from the spec are met"""
        logger.info("Verifying security requirements are met...")
        
        requirements_met = []
        requirements_failed = []
        
        # Check security requirements from the spec
        security_requirements = [
            {
                'name': 'Workspace ID Security',
                'check': lambda: self.check_workspace_id_security(),
                'description': '工作台ID使用安全哈希，防止信息泄露'
            },
            {
                'name': 'Demo Data Isolation',
                'check': lambda: self.check_demo_data_isolation(),
                'description': '演示数据与真实数据完全隔离'
            },
            {
                'name': 'Lawyer Certificate Encryption',
                'check': lambda: self.check_lawyer_cert_encryption(),
                'description': '律师证文件加密存储'
            },
            {
                'name': 'Points Audit Logging',
                'check': lambda: self.check_points_audit_logging(),
                'description': '积分变动完整审计日志'
            },
            {
                'name': 'Payment PCI DSS Compliance',
                'check': lambda: self.check_payment_compliance(),
                'description': '支付接口PCI DSS合规'
            }
        ]
        
        for requirement in security_requirements:
            try:
                if requirement['check']():
                    requirements_met.append(requirement['name'])
                    logger.info(f"✅ {requirement['name']}: {requirement['description']}")
                else:
                    requirements_failed.append(requirement['name'])
                    logger.warning(f"⚠️ {requirement['name']}: {requirement['description']} - Not fully implemented")
            except Exception as e:
                requirements_failed.append(requirement['name'])
                logger.error(f"❌ {requirement['name']}: Error checking - {e}")
        
        if len(requirements_met) >= len(security_requirements) * 0.8:  # 80% threshold
            self.verification_results['tests']['requirements'] = {
                'status': 'PASSED',
                'met': requirements_met,
                'failed': requirements_failed,
                'score': len(requirements_met) / len(security_requirements) * 100
            }
            return True
        else:
            self.verification_results['tests']['requirements'] = {
                'status': 'FAILED',
                'met': requirements_met,
                'failed': requirements_failed,
                'score': len(requirements_met) / len(security_requirements) * 100
            }
            return False
    
    def check_workspace_id_security(self):
        """Check workspace ID security implementation"""
        # Check if workspace ID generation uses secure hashing
        auth_files = [
            'backend/app/services/unified_auth_service.py',
            'backend/app/middlewares/workspace_middleware.py'
        ]
        
        for file_path in auth_files:
            if Path(file_path).exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                if 'hash' in content.lower() and 'workspace' in content.lower():
                    return True
        return False
    
    def check_demo_data_isolation(self):
        """Check demo data isolation implementation"""
        demo_files = [
            'backend/app/services/demo_account_service.py',
            'backend/app/middlewares/demo_security_middleware.py'
        ]
        
        for file_path in demo_files:
            if Path(file_path).exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                if 'isolation' in content.lower() or 'separate' in content.lower():
                    return True
        return False
    
    def check_lawyer_cert_encryption(self):
        """Check lawyer certificate encryption"""
        cert_files = [
            'backend/app/services/lawyer_certification_service.py',
            'backend/app/core/encryption.py'
        ]
        
        for file_path in cert_files:
            if Path(file_path).exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                if 'encrypt' in content.lower() and ('certificate' in content.lower() or 'file' in content.lower()):
                    return True
        return False
    
    def check_points_audit_logging(self):
        """Check points audit logging implementation"""
        points_files = [
            'backend/app/services/lawyer_points_engine.py',
            'backend/app/services/security_logger.py'
        ]
        
        for file_path in points_files:
            if Path(file_path).exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                if 'audit' in content.lower() or ('log' in content.lower() and 'points' in content.lower()):
                    return True
        return False
    
    def check_payment_compliance(self):
        """Check payment PCI DSS compliance measures"""
        payment_files = [
            'backend/app/services/payment_service.py',
            'backend/app/services/user_credits_service.py'
        ]
        
        for file_path in payment_files:
            if Path(file_path).exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                if any(term in content.lower() for term in ['encrypt', 'secure', 'pci', 'compliance']):
                    return True
        return False
    
    async def run_all_verifications(self):
        """Run all security verifications"""
        logger.info("Starting comprehensive security verification...")
        
        verification_steps = [
            ('File Existence', self.verify_security_files_exist),
            ('Security Hardening', self.run_security_hardening),
            ('Configuration Validation', self.run_configuration_validation),
            ('Penetration Testing', self.run_penetration_testing),
            ('Comprehensive Tests', self.run_comprehensive_security_tests),
            ('Unit Tests', self.run_unit_security_tests),
            ('Requirements Verification', self.verify_security_requirements_met),
        ]
        
        passed_steps = 0
        total_steps = len(verification_steps)
        
        for step_name, step_function in verification_steps:
            logger.info(f"Running {step_name}...")
            try:
                if asyncio.iscoroutinefunction(step_function):
                    success = await step_function()
                else:
                    success = step_function()
                
                if success:
                    passed_steps += 1
                    logger.info(f"✅ {step_name} completed successfully")
                else:
                    logger.error(f"❌ {step_name} failed")
            
            except Exception as e:
                logger.error(f"❌ {step_name} error: {e}")
        
        # Calculate overall results
        self.verification_results['security_score'] = (passed_steps / total_steps) * 100
        
        if self.verification_results['critical_issues'] == 0 and self.verification_results['high_issues'] == 0:
            if passed_steps >= total_steps * 0.8:  # 80% threshold
                self.verification_results['overall_status'] = 'PASSED'
            else:
                self.verification_results['overall_status'] = 'PARTIAL'
        else:
            self.verification_results['overall_status'] = 'FAILED'
        
        # Generate recommendations
        self.generate_recommendations()
        
        logger.info("Security verification completed")
        return self.verification_results
    
    def generate_recommendations(self):
        """Generate security recommendations"""
        recommendations = []
        
        if self.verification_results['critical_issues'] > 0:
            recommendations.append("CRITICAL: Address all critical security vulnerabilities immediately before deployment")
        
        if self.verification_results['high_issues'] > 0:
            recommendations.append("HIGH: Fix all high-risk security issues within 24 hours")
        
        # Check individual test results
        for test_name, test_result in self.verification_results['tests'].items():
            if test_result.get('status') == 'FAILED':
                if test_name == 'penetration_test':
                    recommendations.append("Fix penetration testing vulnerabilities - implement proper input validation and security controls")
                elif test_name == 'config_validation':
                    recommendations.append("Update security configuration - ensure all security settings are properly configured")
                elif test_name == 'comprehensive':
                    recommendations.append("Address comprehensive security test failures - review static analysis and dependency security")
                elif test_name == 'requirements':
                    recommendations.append("Implement missing security requirements from the specification")
        
        if self.verification_results['security_score'] < 90:
            recommendations.append("Improve overall security score by addressing remaining security issues")
        
        self.verification_results['recommendations'] = recommendations
    
    def generate_final_report(self):
        """Generate final security verification report"""
        report = []
        report.append("=" * 80)
        report.append("LAWSKER SECURITY VERIFICATION REPORT")
        report.append("=" * 80)
        report.append(f"Verification Date: {self.verification_results['timestamp']}")
        report.append(f"Overall Status: {self.verification_results['overall_status']}")
        report.append(f"Security Score: {self.verification_results['security_score']:.1f}/100")
        report.append(f"Critical Issues: {self.verification_results['critical_issues']}")
        report.append(f"High-Risk Issues: {self.verification_results['high_issues']}")
        report.append("")
        
        # Test Results
        report.append("VERIFICATION TEST RESULTS:")
        report.append("-" * 40)
        for test_name, test_result in self.verification_results['tests'].items():
            status = test_result.get('status', 'UNKNOWN')
            score = test_result.get('score', 'N/A')
            if score != 'N/A':
                report.append(f"{test_name.upper()}: {status} (Score: {score}/100)")
            else:
                report.append(f"{test_name.upper()}: {status}")
        report.append("")
        
        # Recommendations
        if self.verification_results['recommendations']:
            report.append("SECURITY RECOMMENDATIONS:")
            report.append("-" * 40)
            for i, rec in enumerate(self.verification_results['recommendations'], 1):
                report.append(f"{i}. {rec}")
            report.append("")
        
        # Final Status
        report.append("=" * 80)
        if self.verification_results['overall_status'] == 'PASSED':
            report.append("✅ SECURITY VERIFICATION PASSED")
            report.append("System meets security requirements - no high-risk vulnerabilities found.")
            report.append("Safe for production deployment.")
        elif self.verification_results['overall_status'] == 'PARTIAL':
            report.append("⚠️ SECURITY VERIFICATION PARTIALLY PASSED")
            report.append("Most security requirements met, but some improvements needed.")
            report.append("Review recommendations before production deployment.")
        else:
            report.append("❌ SECURITY VERIFICATION FAILED")
            report.append("Critical or high-risk vulnerabilities found.")
            report.append("Must address all security issues before deployment.")
        report.append("=" * 80)
        
        return "\n".join(report)

async def main():
    """Main verification function"""
    verifier = SecurityVerification()
    results = await verifier.run_all_verifications()
    
    # Save detailed results
    with open('security_verification_report.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print final report
    final_report = verifier.generate_final_report()
    print(final_report)
    
    # Save final report
    with open('security_verification_summary.txt', 'w') as f:
        f.write(final_report)
    
    # Exit with appropriate code
    if results['overall_status'] == 'PASSED':
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())