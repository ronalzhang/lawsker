#!/usr/bin/env python3
"""
Simplified Security Validation
Validates core security requirements for the Lawsker system
"""

import os
import sys
import json
import time
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SecurityValidation:
    """Simplified security validation focusing on core requirements"""
    
    def __init__(self):
        self.project_root = Path(".")
        self.validation_results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'tests_passed': 0,
            'tests_failed': 0,
            'critical_issues': 0,
            'high_issues': 0,
            'security_score': 0,
            'details': {}
        }
    
    def validate_environment_security(self):
        """Validate environment variable security"""
        logger.info("Validating environment security...")
        
        try:
            env_files = ['.env.production', '.env.server']
            issues = []
            
            for env_file in env_files:
                env_path = self.project_root / env_file
                if env_path.exists():
                    with open(env_path, 'r') as f:
                        content = f.read()
                    
                    # Check for basic security variables
                    required_vars = ['SECRET_KEY', 'DATABASE_URL']
                    for var in required_vars:
                        if var not in content:
                            issues.append(f"Missing {var} in {env_file}")
                    
                    # Check for weak secrets (basic check)
                    if 'SECRET_KEY=test' in content or 'SECRET_KEY=dev' in content:
                        issues.append(f"Weak SECRET_KEY in {env_file}")
            
            if not issues:
                self.validation_results['tests_passed'] += 1
                self.validation_results['details']['environment'] = 'PASSED'
                logger.info("✅ Environment security validation passed")
                return True
            else:
                self.validation_results['tests_failed'] += 1
                self.validation_results['high_issues'] += len(issues)
                self.validation_results['details']['environment'] = f'FAILED: {issues}'
                logger.warning(f"⚠️ Environment security issues: {issues}")
                return False
        
        except Exception as e:
            logger.error(f"Error validating environment security: {e}")
            self.validation_results['tests_failed'] += 1
            return False
    
    def validate_authentication_implementation(self):
        """Validate authentication implementation"""
        logger.info("Validating authentication implementation...")
        
        try:
            auth_files = [
                'backend/app/core/security.py',
                'backend/app/services/unified_auth_service.py'
            ]
            
            auth_implemented = False
            secure_hashing = False
            
            for auth_file in auth_files:
                auth_path = self.project_root / auth_file
                if auth_path.exists():
                    with open(auth_path, 'r') as f:
                        content = f.read()
                    
                    if 'password' in content.lower() and 'hash' in content.lower():
                        auth_implemented = True
                    
                    if any(alg in content.lower() for alg in ['bcrypt', 'scrypt', 'argon2', 'pbkdf2']):
                        secure_hashing = True
            
            if auth_implemented and secure_hashing:
                self.validation_results['tests_passed'] += 1
                self.validation_results['details']['authentication'] = 'PASSED'
                logger.info("✅ Authentication implementation validated")
                return True
            else:
                self.validation_results['tests_failed'] += 1
                if not auth_implemented:
                    self.validation_results['high_issues'] += 1
                if not secure_hashing:
                    self.validation_results['high_issues'] += 1
                self.validation_results['details']['authentication'] = 'FAILED: Missing secure authentication'
                logger.warning("⚠️ Authentication implementation issues found")
                return False
        
        except Exception as e:
            logger.error(f"Error validating authentication: {e}")
            self.validation_results['tests_failed'] += 1
            return False
    
    def validate_input_validation(self):
        """Validate input validation implementation"""
        logger.info("Validating input validation...")
        
        try:
            api_files = list((self.project_root / 'backend/app/api').rglob('*.py'))
            validation_found = False
            
            for api_file in api_files:
                if api_file.name == '__init__.py':
                    continue
                
                try:
                    with open(api_file, 'r') as f:
                        content = f.read()
                    
                    # Check for validation patterns
                    if any(pattern in content.lower() for pattern in ['validate', 'schema', 'pydantic']):
                        validation_found = True
                        break
                except:
                    continue
            
            if validation_found:
                self.validation_results['tests_passed'] += 1
                self.validation_results['details']['input_validation'] = 'PASSED'
                logger.info("✅ Input validation found in API files")
                return True
            else:
                self.validation_results['tests_failed'] += 1
                self.validation_results['high_issues'] += 1
                self.validation_results['details']['input_validation'] = 'FAILED: No input validation found'
                logger.warning("⚠️ Input validation not found in API files")
                return False
        
        except Exception as e:
            logger.error(f"Error validating input validation: {e}")
            self.validation_results['tests_failed'] += 1
            return False
    
    def validate_https_configuration(self):
        """Validate HTTPS configuration"""
        logger.info("Validating HTTPS configuration...")
        
        try:
            nginx_configs = ['nginx/nginx.conf', 'nginx/lawsker.conf']
            https_configured = False
            security_headers = False
            
            for config_file in nginx_configs:
                config_path = self.project_root / config_file
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        content = f.read()
                    
                    if 'ssl_certificate' in content or 'listen 443' in content:
                        https_configured = True
                    
                    if 'X-Content-Type-Options' in content or 'X-Frame-Options' in content:
                        security_headers = True
            
            if https_configured and security_headers:
                self.validation_results['tests_passed'] += 1
                self.validation_results['details']['https'] = 'PASSED'
                logger.info("✅ HTTPS and security headers configured")
                return True
            else:
                self.validation_results['tests_failed'] += 1
                if not https_configured:
                    self.validation_results['high_issues'] += 1
                if not security_headers:
                    self.validation_results['high_issues'] += 1
                self.validation_results['details']['https'] = 'FAILED: HTTPS or security headers not configured'
                logger.warning("⚠️ HTTPS or security headers not properly configured")
                return False
        
        except Exception as e:
            logger.error(f"Error validating HTTPS configuration: {e}")
            self.validation_results['tests_failed'] += 1
            return False
    
    def validate_database_security(self):
        """Validate database security"""
        logger.info("Validating database security...")
        
        try:
            db_files = [
                'backend/app/core/database.py',
                'backend/config/database_config.py'
            ]
            
            parameterized_queries = False
            no_hardcoded_creds = True
            
            for db_file in db_files:
                db_path = self.project_root / db_file
                if db_path.exists():
                    with open(db_path, 'r') as f:
                        content = f.read()
                    
                    # Check for parameterized queries
                    if 'execute(' in content and ('%s' in content or '?' in content):
                        parameterized_queries = True
                    
                    # Check for hardcoded credentials
                    if any(pattern in content.lower() for pattern in ['password="', "password='", 'password=123']):
                        no_hardcoded_creds = False
            
            if parameterized_queries and no_hardcoded_creds:
                self.validation_results['tests_passed'] += 1
                self.validation_results['details']['database'] = 'PASSED'
                logger.info("✅ Database security validated")
                return True
            else:
                self.validation_results['tests_failed'] += 1
                if not parameterized_queries:
                    self.validation_results['high_issues'] += 1
                if not no_hardcoded_creds:
                    self.validation_results['critical_issues'] += 1
                self.validation_results['details']['database'] = 'FAILED: Database security issues'
                logger.warning("⚠️ Database security issues found")
                return False
        
        except Exception as e:
            logger.error(f"Error validating database security: {e}")
            self.validation_results['tests_failed'] += 1
            return False
    
    def validate_file_permissions(self):
        """Validate file permissions"""
        logger.info("Validating file permissions...")
        
        try:
            sensitive_files = [
                '.env.production',
                '.env.server',
                'backend/jwt_private_key.pem',
                'jwt_private_key.pem'
            ]
            
            permission_issues = []
            
            for file_path in sensitive_files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    try:
                        import stat
                        file_stat = full_path.stat()
                        
                        # Check if file is readable by others
                        if file_stat.st_mode & stat.S_IROTH:
                            permission_issues.append(f"{file_path} readable by others")
                        
                        # Check if file is writable by group or others
                        if file_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
                            permission_issues.append(f"{file_path} writable by group/others")
                    
                    except Exception as e:
                        logger.debug(f"Could not check permissions for {file_path}: {e}")
            
            if not permission_issues:
                self.validation_results['tests_passed'] += 1
                self.validation_results['details']['file_permissions'] = 'PASSED'
                logger.info("✅ File permissions validated")
                return True
            else:
                self.validation_results['tests_failed'] += 1
                self.validation_results['high_issues'] += len(permission_issues)
                self.validation_results['details']['file_permissions'] = f'FAILED: {permission_issues}'
                logger.warning(f"⚠️ File permission issues: {permission_issues}")
                return False
        
        except Exception as e:
            logger.error(f"Error validating file permissions: {e}")
            self.validation_results['tests_failed'] += 1
            return False
    
    def validate_security_middleware(self):
        """Validate security middleware implementation"""
        logger.info("Validating security middleware...")
        
        try:
            middleware_files = [
                'backend/app/middlewares/auth_middleware.py',
                'backend/app/middlewares/rate_limit_middleware.py',
                'backend/app/middlewares/enhanced_security_middleware.py'
            ]
            
            middleware_count = 0
            for middleware_file in middleware_files:
                middleware_path = self.project_root / middleware_file
                if middleware_path.exists():
                    middleware_count += 1
            
            if middleware_count >= 2:  # At least 2 security middleware files
                self.validation_results['tests_passed'] += 1
                self.validation_results['details']['middleware'] = 'PASSED'
                logger.info("✅ Security middleware validated")
                return True
            else:
                self.validation_results['tests_failed'] += 1
                self.validation_results['high_issues'] += 1
                self.validation_results['details']['middleware'] = 'FAILED: Insufficient security middleware'
                logger.warning("⚠️ Insufficient security middleware found")
                return False
        
        except Exception as e:
            logger.error(f"Error validating security middleware: {e}")
            self.validation_results['tests_failed'] += 1
            return False
    
    def validate_logging_security(self):
        """Validate security logging"""
        logger.info("Validating security logging...")
        
        try:
            logging_files = [
                'backend/app/core/logging.py',
                'backend/app/services/security_logger.py'
            ]
            
            security_logging = False
            for log_file in logging_files:
                log_path = self.project_root / log_file
                if log_path.exists():
                    with open(log_path, 'r') as f:
                        content = f.read()
                    
                    if any(event in content.lower() for event in ['security', 'auth', 'login']):
                        security_logging = True
                        break
            
            if security_logging:
                self.validation_results['tests_passed'] += 1
                self.validation_results['details']['logging'] = 'PASSED'
                logger.info("✅ Security logging validated")
                return True
            else:
                self.validation_results['tests_failed'] += 1
                self.validation_results['high_issues'] += 1
                self.validation_results['details']['logging'] = 'FAILED: No security logging found'
                logger.warning("⚠️ Security logging not found")
                return False
        
        except Exception as e:
            logger.error(f"Error validating security logging: {e}")
            self.validation_results['tests_failed'] += 1
            return False
    
    def run_all_validations(self):
        """Run all security validations"""
        logger.info("Starting security validation...")
        
        validations = [
            self.validate_environment_security,
            self.validate_authentication_implementation,
            self.validate_input_validation,
            self.validate_https_configuration,
            self.validate_database_security,
            self.validate_file_permissions,
            self.validate_security_middleware,
            self.validate_logging_security,
        ]
        
        for validation in validations:
            try:
                validation()
            except Exception as e:
                logger.error(f"Error in {validation.__name__}: {e}")
                self.validation_results['tests_failed'] += 1
        
        # Calculate security score
        total_tests = self.validation_results['tests_passed'] + self.validation_results['tests_failed']
        if total_tests > 0:
            base_score = (self.validation_results['tests_passed'] / total_tests) * 100
            
            # Penalize for critical and high issues
            penalty = (self.validation_results['critical_issues'] * 20) + (self.validation_results['high_issues'] * 5)
            self.validation_results['security_score'] = max(0, base_score - penalty)
        else:
            self.validation_results['security_score'] = 0
        
        logger.info("Security validation completed")
        return self.validation_results
    
    def generate_report(self):
        """Generate security validation report"""
        report = []
        report.append("=" * 80)
        report.append("SECURITY VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Validation Date: {self.validation_results['timestamp']}")
        report.append(f"Tests Passed: {self.validation_results['tests_passed']}")
        report.append(f"Tests Failed: {self.validation_results['tests_failed']}")
        report.append(f"Critical Issues: {self.validation_results['critical_issues']}")
        report.append(f"High Issues: {self.validation_results['high_issues']}")
        report.append(f"Security Score: {self.validation_results['security_score']:.1f}/100")
        report.append("")
        
        report.append("VALIDATION DETAILS:")
        report.append("-" * 40)
        for test_name, result in self.validation_results['details'].items():
            report.append(f"{test_name.upper()}: {result}")
        report.append("")
        
        # Determine overall status
        if self.validation_results['critical_issues'] == 0 and self.validation_results['high_issues'] == 0:
            if self.validation_results['security_score'] >= 80:
                status = "✅ PASSED"
                message = "Security validation passed - no high-risk vulnerabilities found."
            else:
                status = "⚠️ PARTIAL"
                message = "Security validation partially passed - some improvements needed."
        else:
            status = "❌ FAILED"
            message = "Security validation failed - critical or high-risk issues found."
        
        report.append("=" * 80)
        report.append(f"OVERALL STATUS: {status}")
        report.append(message)
        report.append("=" * 80)
        
        return "\n".join(report)

def main():
    """Main function"""
    validator = SecurityValidation()
    results = validator.run_all_validations()
    
    # Save results
    with open('security_validation_report.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print report
    report = validator.generate_report()
    print(report)
    
    # Exit with appropriate code
    if results['critical_issues'] == 0 and results['high_issues'] == 0:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()