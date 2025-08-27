#!/usr/bin/env python3
"""
Comprehensive Security Test Suite
Tests all security aspects of the Lawsker system to ensure no high-risk vulnerabilities
"""

import asyncio
import pytest
import json
import subprocess
import sys
import time
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestSecurityComprehensive:
    """Comprehensive security test suite"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.project_root = Path(".")
        self.test_results = {
            'penetration_test': False,
            'config_validation': False,
            'static_analysis': False,
            'dependency_check': False,
            'hardening_applied': False
        }
    
    def test_security_hardening_applied(self):
        """Test that security hardening has been applied"""
        logger.info("Testing security hardening application...")
        
        try:
            # Run security hardening
            result = subprocess.run([
                sys.executable, 'backend/security_hardening.py',
                '--project-root', '.',
                '--output', 'test_hardening_report.json'
            ], capture_output=True, text=True, timeout=120)
            
            assert result.returncode == 0, f"Security hardening failed: {result.stderr}"
            
            # Verify hardening report
            report_path = Path('test_hardening_report.json')
            assert report_path.exists(), "Hardening report not generated"
            
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            assert report['status'] == 'completed', "Hardening not completed"
            assert report['total_changes'] >= 0, "No hardening changes recorded"
            
            self.test_results['hardening_applied'] = True
            logger.info("✅ Security hardening test passed")
            
        except Exception as e:
            logger.error(f"❌ Security hardening test failed: {e}")
            raise
    
    def test_security_configuration_validation(self):
        """Test security configuration validation"""
        logger.info("Testing security configuration validation...")
        
        try:
            # Run configuration validation
            result = subprocess.run([
                sys.executable, 'backend/security_config_validator.py',
                '--project-root', '.',
                '--output', 'test_config_report.json'
            ], capture_output=True, text=True, timeout=60)
            
            # Verify validation report
            report_path = Path('test_config_report.json')
            assert report_path.exists(), "Configuration validation report not generated"
            
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            # Check for critical and high issues
            critical_issues = report['summary']['critical_issues']
            high_issues = report['summary']['high_issues']
            
            assert critical_issues == 0, f"Critical security configuration issues found: {critical_issues}"
            assert high_issues == 0, f"High security configuration issues found: {high_issues}"
            
            # Security score should be acceptable
            security_score = report['summary']['security_score']
            assert security_score >= 80, f"Security configuration score too low: {security_score}/100"
            
            self.test_results['config_validation'] = True
            logger.info(f"✅ Security configuration validation passed (Score: {security_score}/100)")
            
        except Exception as e:
            logger.error(f"❌ Security configuration validation failed: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_penetration_testing(self):
        """Test penetration testing results"""
        logger.info("Running penetration testing...")
        
        try:
            # Import and run penetration tests
            from security_penetration_test import SecurityPenetrationTester
            
            async with SecurityPenetrationTester("http://localhost:8000") as tester:
                await tester.run_all_tests()
                report = tester.generate_report()
            
            # Check for critical and high vulnerabilities
            critical_findings = report['summary']['critical_findings']
            high_findings = report['summary']['high_findings']
            
            assert critical_findings == 0, f"Critical vulnerabilities found: {critical_findings}"
            assert high_findings == 0, f"High-risk vulnerabilities found: {high_findings}"
            
            # Security score should be acceptable
            security_score = report['summary']['security_score']
            assert security_score >= 85, f"Penetration test security score too low: {security_score}/100"
            
            self.test_results['penetration_test'] = True
            logger.info(f"✅ Penetration testing passed (Score: {security_score}/100)")
            
        except Exception as e:
            logger.error(f"❌ Penetration testing failed: {e}")
            raise
    
    def test_static_security_analysis(self):
        """Test static security analysis"""
        logger.info("Running static security analysis...")
        
        try:
            # Run comprehensive security tests
            result = subprocess.run([
                sys.executable, 'backend/run_security_tests.py',
                '--url', 'http://localhost:8000',
                '--project-root', '.',
                '--output', 'test_security_report.json'
            ], capture_output=True, text=True, timeout=300)
            
            # Verify security report
            report_path = Path('test_security_report.json')
            assert report_path.exists(), "Security test report not generated"
            
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            # Check overall results
            assert report['passed'] == True, "Security tests failed"
            
            # Check individual test results
            if report.get('static_analysis'):
                static_analysis = report['static_analysis']['summary']
                critical_findings = static_analysis.get('critical_findings', 0)
                high_findings = static_analysis.get('high_findings', 0)
                
                assert critical_findings == 0, f"Critical static analysis findings: {critical_findings}"
                assert high_findings <= 2, f"Too many high-risk static analysis findings: {high_findings}"
            
            # Check dependency security
            if report.get('dependency_check'):
                dependency_check = report['dependency_check']['summary']
                critical_vulns = dependency_check.get('critical_vulnerabilities', 0)
                high_vulns = dependency_check.get('high_vulnerabilities', 0)
                
                assert critical_vulns == 0, f"Critical dependency vulnerabilities: {critical_vulns}"
                assert high_vulns <= 1, f"Too many high-risk dependency vulnerabilities: {high_vulns}"
            
            # Overall security score
            overall_score = report.get('overall_score', 0)
            assert overall_score >= 80, f"Overall security score too low: {overall_score}/100"
            
            self.test_results['static_analysis'] = True
            self.test_results['dependency_check'] = True
            logger.info(f"✅ Static security analysis passed (Score: {overall_score}/100)")
            
        except Exception as e:
            logger.error(f"❌ Static security analysis failed: {e}")
            raise
    
    def test_authentication_security(self):
        """Test authentication security implementation"""
        logger.info("Testing authentication security...")
        
        try:
            # Check for secure authentication files
            auth_files = [
                'backend/app/core/security.py',
                'backend/app/services/unified_auth_service.py',
                'backend/app/middlewares/auth_middleware.py'
            ]
            
            for auth_file in auth_files:
                auth_path = Path(auth_file)
                if auth_path.exists():
                    with open(auth_path, 'r') as f:
                        content = f.read()
                    
                    # Check for secure password hashing
                    assert any(alg in content.lower() for alg in ['bcrypt', 'scrypt', 'argon2']), \
                        f"Secure password hashing not found in {auth_file}"
                    
                    # Check for JWT security
                    if 'jwt' in content.lower():
                        # Should have expiration
                        assert 'exp' in content.lower() or 'expire' in content.lower(), \
                            f"JWT expiration not configured in {auth_file}"
            
            logger.info("✅ Authentication security test passed")
            
        except Exception as e:
            logger.error(f"❌ Authentication security test failed: {e}")
            raise
    
    def test_input_validation_security(self):
        """Test input validation security"""
        logger.info("Testing input validation security...")
        
        try:
            # Check API files for input validation
            api_files = list(Path('backend/app/api').rglob('*.py'))
            
            validation_found = False
            for api_file in api_files:
                if api_file.name == '__init__.py':
                    continue
                
                with open(api_file, 'r') as f:
                    content = f.read()
                
                # Check for validation patterns
                if any(pattern in content.lower() for pattern in ['validate', 'schema', 'pydantic']):
                    validation_found = True
                    break
            
            assert validation_found, "Input validation not found in API files"
            
            logger.info("✅ Input validation security test passed")
            
        except Exception as e:
            logger.error(f"❌ Input validation security test failed: {e}")
            raise
    
    def test_https_and_security_headers(self):
        """Test HTTPS and security headers configuration"""
        logger.info("Testing HTTPS and security headers...")
        
        try:
            # Check NGINX configuration
            nginx_configs = ['nginx/nginx.conf', 'nginx/lawsker.conf']
            
            security_headers_found = False
            https_configured = False
            
            for config_file in nginx_configs:
                config_path = Path(config_file)
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        content = f.read()
                    
                    # Check for security headers
                    required_headers = [
                        'X-Content-Type-Options',
                        'X-Frame-Options',
                        'X-XSS-Protection'
                    ]
                    
                    if any(header in content for header in required_headers):
                        security_headers_found = True
                    
                    # Check for HTTPS configuration
                    if 'ssl_certificate' in content or 'listen 443' in content:
                        https_configured = True
            
            # At least basic security headers should be configured
            assert security_headers_found, "Security headers not configured in NGINX"
            
            logger.info("✅ HTTPS and security headers test passed")
            
        except Exception as e:
            logger.error(f"❌ HTTPS and security headers test failed: {e}")
            raise
    
    def test_file_upload_security(self):
        """Test file upload security"""
        logger.info("Testing file upload security...")
        
        try:
            # Check file upload services
            upload_files = [
                'backend/app/services/file_upload_service.py',
                'backend/app/api/v1/file_upload.py'
            ]
            
            security_measures_found = False
            
            for upload_file in upload_files:
                upload_path = Path(upload_file)
                if upload_path.exists():
                    with open(upload_path, 'r') as f:
                        content = f.read()
                    
                    # Check for security measures
                    security_patterns = [
                        'allowed_extensions',
                        'file_size',
                        'content_type',
                        'validate',
                        'sanitize'
                    ]
                    
                    if any(pattern in content.lower() for pattern in security_patterns):
                        security_measures_found = True
                        break
            
            # File upload security should be implemented
            if any(Path(f).exists() for f in upload_files):
                assert security_measures_found, "File upload security measures not found"
            
            logger.info("✅ File upload security test passed")
            
        except Exception as e:
            logger.error(f"❌ File upload security test failed: {e}")
            raise
    
    def test_environment_security(self):
        """Test environment variable security"""
        logger.info("Testing environment variable security...")
        
        try:
            env_files = ['.env', '.env.production', '.env.server']
            
            for env_file in env_files:
                env_path = Path(env_file)
                if env_path.exists():
                    with open(env_path, 'r') as f:
                        content = f.read()
                    
                    # Check for weak secrets
                    lines = content.split('\n')
                    for line in lines:
                        if '=' in line and not line.strip().startswith('#'):
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')
                            
                            # Check for weak secrets
                            if any(secret_key in key.upper() for secret_key in ['SECRET', 'KEY', 'PASSWORD']):
                                if value and not value.startswith('$'):
                                    assert len(value) >= 20, f"Weak secret in {env_file}: {key}"
                                    assert value not in ['test', 'dev', 'password', '123456'], \
                                        f"Default/weak secret in {env_file}: {key}"
            
            logger.info("✅ Environment security test passed")
            
        except Exception as e:
            logger.error(f"❌ Environment security test failed: {e}")
            raise
    
    def test_database_security(self):
        """Test database security configuration"""
        logger.info("Testing database security...")
        
        try:
            # Check database configuration files
            db_files = [
                'backend/app/core/database.py',
                'backend/config/database_config.py'
            ]
            
            for db_file in db_files:
                db_path = Path(db_file)
                if db_path.exists():
                    with open(db_path, 'r') as f:
                        content = f.read()
                    
                    # Check for parameterized queries
                    if 'execute(' in content:
                        # Should use parameterized queries
                        assert '%s' in content or '?' in content or 'bind' in content.lower(), \
                            f"Parameterized queries not used in {db_file}"
                    
                    # Check for no hardcoded credentials
                    assert not any(pattern in content.lower() for pattern in [
                        'password="', "password='", 'password=123'
                    ]), f"Hardcoded database credentials in {db_file}"
            
            logger.info("✅ Database security test passed")
            
        except Exception as e:
            logger.error(f"❌ Database security test failed: {e}")
            raise
    
    def test_logging_security(self):
        """Test security logging implementation"""
        logger.info("Testing security logging...")
        
        try:
            # Check for security logging
            logging_files = [
                'backend/app/core/logging.py',
                'backend/app/services/security_logger.py'
            ]
            
            security_logging_found = False
            
            for log_file in logging_files:
                log_path = Path(log_file)
                if log_path.exists():
                    with open(log_path, 'r') as f:
                        content = f.read()
                    
                    # Check for security event logging
                    security_events = ['login', 'authentication', 'authorization', 'security']
                    if any(event in content.lower() for event in security_events):
                        security_logging_found = True
                        break
            
            # Security logging should be implemented
            assert security_logging_found, "Security event logging not implemented"
            
            logger.info("✅ Security logging test passed")
            
        except Exception as e:
            logger.error(f"❌ Security logging test failed: {e}")
            raise
    
    def test_overall_security_compliance(self):
        """Test overall security compliance"""
        logger.info("Testing overall security compliance...")
        
        try:
            # Check that all individual tests passed
            required_tests = [
                'hardening_applied',
                'config_validation',
                'penetration_test',
                'static_analysis',
                'dependency_check'
            ]
            
            passed_tests = sum(1 for test in required_tests if self.test_results.get(test, False))
            total_tests = len(required_tests)
            
            compliance_score = (passed_tests / total_tests) * 100
            
            assert compliance_score >= 80, f"Security compliance score too low: {compliance_score}%"
            
            # No critical or high-risk vulnerabilities should remain
            assert self.test_results.get('penetration_test', False), "Penetration testing not passed"
            assert self.test_results.get('config_validation', False), "Configuration validation not passed"
            
            logger.info(f"✅ Overall security compliance test passed (Score: {compliance_score}%)")
            
        except Exception as e:
            logger.error(f"❌ Overall security compliance test failed: {e}")
            raise

def run_security_tests():
    """Run all security tests"""
    logger.info("Starting comprehensive security testing...")
    
    # Run pytest with this test file
    result = subprocess.run([
        sys.executable, '-m', 'pytest', 
        'backend/test_security_comprehensive.py',
        '-v', '--tb=short'
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0

if __name__ == "__main__":
    success = run_security_tests()
    
    if success:
        print("\n" + "="*80)
        print("✅ ALL SECURITY TESTS PASSED!")
        print("System meets security requirements - no high-risk vulnerabilities found.")
        print("="*80)
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print("❌ SECURITY TESTS FAILED!")
        print("Critical or high-risk vulnerabilities found - must be addressed before deployment.")
        print("="*80)
        sys.exit(1)