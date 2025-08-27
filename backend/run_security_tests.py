#!/usr/bin/env python3
"""
Comprehensive Security Test Runner
Runs all security tests including penetration testing and configuration validation
"""

import asyncio
import subprocess
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SecurityTestRunner:
    """Comprehensive security test runner"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.results = {
            'penetration_test': None,
            'config_validation': None,
            'overall_score': 0,
            'test_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'passed': False
        }
    
    async def run_penetration_tests(self, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
        """Run penetration tests"""
        logger.info("Running security penetration tests...")
        
        try:
            # Import and run penetration tests
            from security_penetration_test import SecurityPenetrationTester
            
            async with SecurityPenetrationTester(base_url) as tester:
                await tester.run_all_tests()
                report = tester.generate_report()
                
                logger.info(f"Penetration test completed. Score: {report['summary']['security_score']}/100")
                return report
        
        except Exception as e:
            logger.error(f"Error running penetration tests: {e}")
            return {
                'summary': {
                    'security_score': 0,
                    'total_findings': 1,
                    'critical_findings': 1,
                    'high_findings': 0,
                    'medium_findings': 0,
                    'low_findings': 0
                },
                'findings': {
                    'critical': [{
                        'title': 'Penetration Test Failed',
                        'description': f'Failed to run penetration tests: {str(e)}',
                        'recommendation': 'Fix test environment and retry'
                    }]
                },
                'error': str(e)
            }
    
    def run_config_validation(self) -> Dict[str, Any]:
        """Run configuration validation"""
        logger.info("Running security configuration validation...")
        
        try:
            from security_config_validator import SecurityConfigValidator
            
            validator = SecurityConfigValidator(str(self.project_root))
            validator.run_all_validations()
            report = validator.generate_report()
            
            logger.info(f"Configuration validation completed. Score: {report['summary']['security_score']}/100")
            return report
        
        except Exception as e:
            logger.error(f"Error running configuration validation: {e}")
            return {
                'summary': {
                    'security_score': 0,
                    'total_issues': 1,
                    'critical_issues': 1,
                    'high_issues': 0,
                    'medium_issues': 0,
                    'low_issues': 0
                },
                'issues': {
                    'critical': [{
                        'component': 'Configuration Validator',
                        'issue': f'Failed to run configuration validation: {str(e)}',
                        'recommendation': 'Fix validation environment and retry'
                    }]
                },
                'error': str(e)
            }
    
    def run_static_analysis(self) -> Dict[str, Any]:
        """Run static security analysis"""
        logger.info("Running static security analysis...")
        
        findings = []
        
        try:
            # Check for common security issues in Python files
            python_files = list(self.project_root.rglob('*.py'))
            
            for py_file in python_files:
                if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                    continue
                
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for potential security issues
                    line_number = 0
                    for line in content.split('\n'):
                        line_number += 1
                        line_lower = line.lower().strip()
                        
                        # Check for hardcoded secrets
                        if any(pattern in line_lower for pattern in ['password=', 'secret=', 'key=', 'token=']):
                            if not line_lower.startswith('#') and '=' in line:
                                value = line.split('=', 1)[1].strip().strip('"\'')
                                if value and not value.startswith('$') and not value.startswith('os.'):
                                    findings.append({
                                        'file': str(py_file.relative_to(self.project_root)),
                                        'line': line_number,
                                        'issue': 'Potential hardcoded secret',
                                        'severity': 'HIGH',
                                        'content': line.strip()
                                    })
                        
                        # Check for SQL injection risks
                        if 'execute(' in line and '%' in line and 'format' in line:
                            findings.append({
                                'file': str(py_file.relative_to(self.project_root)),
                                'line': line_number,
                                'issue': 'Potential SQL injection risk',
                                'severity': 'HIGH',
                                'content': line.strip()
                            })
                        
                        # Check for eval/exec usage
                        if any(func in line_lower for func in ['eval(', 'exec(']):
                            findings.append({
                                'file': str(py_file.relative_to(self.project_root)),
                                'line': line_number,
                                'issue': 'Dangerous function usage (eval/exec)',
                                'severity': 'CRITICAL',
                                'content': line.strip()
                            })
                        
                        # Check for shell injection risks
                        if 'subprocess' in line and 'shell=True' in line:
                            findings.append({
                                'file': str(py_file.relative_to(self.project_root)),
                                'line': line_number,
                                'issue': 'Shell injection risk',
                                'severity': 'HIGH',
                                'content': line.strip()
                            })
                
                except Exception as e:
                    logger.debug(f"Error analyzing {py_file}: {e}")
        
        except Exception as e:
            logger.error(f"Error in static analysis: {e}")
        
        # Calculate score
        critical_count = len([f for f in findings if f['severity'] == 'CRITICAL'])
        high_count = len([f for f in findings if f['severity'] == 'HIGH'])
        medium_count = len([f for f in findings if f['severity'] == 'MEDIUM'])
        
        total_penalty = critical_count * 25 + high_count * 10 + medium_count * 5
        max_penalty = len(findings) * 25 if findings else 100
        score = max(0, 100 - (total_penalty * 100 // max_penalty)) if max_penalty > 0 else 100
        
        return {
            'summary': {
                'total_files_analyzed': len(list(self.project_root.rglob('*.py'))),
                'total_findings': len(findings),
                'critical_findings': critical_count,
                'high_findings': high_count,
                'medium_findings': medium_count,
                'security_score': score
            },
            'findings': findings
        }
    
    def check_dependencies_security(self) -> Dict[str, Any]:
        """Check for known vulnerabilities in dependencies"""
        logger.info("Checking dependencies for known vulnerabilities...")
        
        findings = []
        
        try:
            # Check Python dependencies with safety (if available)
            requirements_files = [
                'backend/requirements.txt',
                'backend/requirements-prod.txt'
            ]
            
            for req_file in requirements_files:
                req_path = self.project_root / req_file
                if req_path.exists():
                    try:
                        # Try to run safety check
                        result = subprocess.run([
                            sys.executable, '-m', 'pip', 'install', 'safety'
                        ], capture_output=True, text=True, timeout=60)
                        
                        if result.returncode == 0:
                            # Run safety check
                            safety_result = subprocess.run([
                                sys.executable, '-m', 'safety', 'check', '-r', str(req_path), '--json'
                            ], capture_output=True, text=True, timeout=60)
                            
                            if safety_result.returncode != 0 and safety_result.stdout:
                                try:
                                    safety_data = json.loads(safety_result.stdout)
                                    for vuln in safety_data:
                                        findings.append({
                                            'package': vuln.get('package', 'unknown'),
                                            'version': vuln.get('installed_version', 'unknown'),
                                            'vulnerability': vuln.get('vulnerability', 'unknown'),
                                            'severity': 'HIGH',
                                            'file': req_file
                                        })
                                except json.JSONDecodeError:
                                    pass
                    
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        logger.debug(f"Could not run safety check for {req_file}")
            
            # Check Node.js dependencies (if package.json exists)
            package_json = self.project_root / 'frontend/package.json'
            if package_json.exists():
                try:
                    # Try to run npm audit
                    audit_result = subprocess.run([
                        'npm', 'audit', '--json'
                    ], cwd=self.project_root / 'frontend', capture_output=True, text=True, timeout=60)
                    
                    if audit_result.stdout:
                        try:
                            audit_data = json.loads(audit_result.stdout)
                            if 'vulnerabilities' in audit_data:
                                for vuln_name, vuln_data in audit_data['vulnerabilities'].items():
                                    severity = vuln_data.get('severity', 'unknown').upper()
                                    if severity in ['CRITICAL', 'HIGH', 'MODERATE']:
                                        findings.append({
                                            'package': vuln_name,
                                            'severity': 'HIGH' if severity == 'MODERATE' else severity,
                                            'vulnerability': vuln_data.get('title', 'Unknown vulnerability'),
                                            'file': 'frontend/package.json'
                                        })
                        except json.JSONDecodeError:
                            pass
                
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    logger.debug("Could not run npm audit")
        
        except Exception as e:
            logger.error(f"Error checking dependencies: {e}")
        
        # Calculate score
        critical_count = len([f for f in findings if f['severity'] == 'CRITICAL'])
        high_count = len([f for f in findings if f['severity'] == 'HIGH'])
        
        score = 100
        if findings:
            total_penalty = critical_count * 30 + high_count * 15
            score = max(0, 100 - total_penalty)
        
        return {
            'summary': {
                'total_vulnerabilities': len(findings),
                'critical_vulnerabilities': critical_count,
                'high_vulnerabilities': high_count,
                'security_score': score
            },
            'vulnerabilities': findings
        }
    
    async def run_all_tests(self, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
        """Run all security tests"""
        logger.info("Starting comprehensive security testing...")
        
        # Run penetration tests
        self.results['penetration_test'] = await self.run_penetration_tests(base_url)
        
        # Run configuration validation
        self.results['config_validation'] = self.run_config_validation()
        
        # Run static analysis
        self.results['static_analysis'] = self.run_static_analysis()
        
        # Check dependencies
        self.results['dependency_check'] = self.check_dependencies_security()
        
        # Calculate overall score
        scores = []
        if self.results['penetration_test']:
            scores.append(self.results['penetration_test']['summary']['security_score'])
        if self.results['config_validation']:
            scores.append(self.results['config_validation']['summary']['security_score'])
        if self.results['static_analysis']:
            scores.append(self.results['static_analysis']['summary']['security_score'])
        if self.results['dependency_check']:
            scores.append(self.results['dependency_check']['summary']['security_score'])
        
        self.results['overall_score'] = sum(scores) // len(scores) if scores else 0
        
        # Determine if tests passed
        critical_issues = 0
        high_issues = 0
        
        if self.results['penetration_test']:
            critical_issues += self.results['penetration_test']['summary'].get('critical_findings', 0)
            high_issues += self.results['penetration_test']['summary'].get('high_findings', 0)
        
        if self.results['config_validation']:
            critical_issues += self.results['config_validation']['summary'].get('critical_issues', 0)
            high_issues += self.results['config_validation']['summary'].get('high_issues', 0)
        
        if self.results['static_analysis']:
            critical_issues += self.results['static_analysis']['summary'].get('critical_findings', 0)
            high_issues += self.results['static_analysis']['summary'].get('high_findings', 0)
        
        if self.results['dependency_check']:
            critical_issues += self.results['dependency_check']['summary'].get('critical_vulnerabilities', 0)
            high_issues += self.results['dependency_check']['summary'].get('high_vulnerabilities', 0)
        
        self.results['passed'] = critical_issues == 0 and high_issues == 0
        self.results['total_critical_issues'] = critical_issues
        self.results['total_high_issues'] = high_issues
        
        logger.info("Comprehensive security testing completed")
        return self.results
    
    def generate_summary_report(self) -> str:
        """Generate a summary report"""
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE SECURITY TEST REPORT")
        report.append("=" * 80)
        report.append(f"Test Timestamp: {self.results['test_timestamp']}")
        report.append(f"Overall Security Score: {self.results['overall_score']}/100")
        report.append(f"Test Result: {'✅ PASSED' if self.results['passed'] else '❌ FAILED'}")
        report.append("")
        
        # Penetration Test Results
        if self.results['penetration_test']:
            pt = self.results['penetration_test']['summary']
            report.append("PENETRATION TEST RESULTS:")
            report.append(f"  Score: {pt['security_score']}/100")
            report.append(f"  Total Findings: {pt['total_findings']}")
            report.append(f"  Critical: {pt['critical_findings']}, High: {pt['high_findings']}")
            report.append("")
        
        # Configuration Validation Results
        if self.results['config_validation']:
            cv = self.results['config_validation']['summary']
            report.append("CONFIGURATION VALIDATION RESULTS:")
            report.append(f"  Score: {cv['security_score']}/100")
            report.append(f"  Total Issues: {cv['total_issues']}")
            report.append(f"  Critical: {cv['critical_issues']}, High: {cv['high_issues']}")
            report.append("")
        
        # Static Analysis Results
        if self.results['static_analysis']:
            sa = self.results['static_analysis']['summary']
            report.append("STATIC ANALYSIS RESULTS:")
            report.append(f"  Score: {sa['security_score']}/100")
            report.append(f"  Total Findings: {sa['total_findings']}")
            report.append(f"  Critical: {sa['critical_findings']}, High: {sa['high_findings']}")
            report.append("")
        
        # Dependency Check Results
        if self.results['dependency_check']:
            dc = self.results['dependency_check']['summary']
            report.append("DEPENDENCY SECURITY RESULTS:")
            report.append(f"  Score: {dc['security_score']}/100")
            report.append(f"  Total Vulnerabilities: {dc['total_vulnerabilities']}")
            report.append(f"  Critical: {dc['critical_vulnerabilities']}, High: {dc['high_vulnerabilities']}")
            report.append("")
        
        report.append("=" * 80)
        
        if not self.results['passed']:
            report.append("❌ SECURITY TESTS FAILED - CRITICAL OR HIGH RISK VULNERABILITIES FOUND!")
            report.append("Please address all critical and high-risk issues before deployment.")
        else:
            report.append("✅ SECURITY TESTS PASSED - NO HIGH-RISK VULNERABILITIES FOUND!")
            report.append("System meets security requirements for deployment.")
        
        report.append("=" * 80)
        
        return "\n".join(report)

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive Security Test Runner')
    parser.add_argument('--url', default='http://localhost:8000', help='Base URL for penetration testing')
    parser.add_argument('--project-root', default='.', help='Project root directory')
    parser.add_argument('--output', default='comprehensive_security_report.json', help='Output report file')
    parser.add_argument('--summary', action='store_true', help='Print summary report')
    
    args = parser.parse_args()
    
    runner = SecurityTestRunner(args.project_root)
    results = await runner.run_all_tests(args.url)
    
    # Save detailed report
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    summary = runner.generate_summary_report()
    print(summary)
    
    if args.summary:
        print(f"\nDetailed report saved to: {args.output}")
    
    # Exit with appropriate code
    sys.exit(0 if results['passed'] else 1)

if __name__ == "__main__":
    asyncio.run(main())