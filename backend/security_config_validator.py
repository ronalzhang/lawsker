#!/usr/bin/env python3
"""
Security Configuration Validator
Validates that all security configurations are properly set up
"""

import os
import json
import yaml
import re
import subprocess
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SecurityConfigValidator:
    """Validates security configurations across the application"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.issues = []
        self.passed_checks = 0
        self.failed_checks = 0
    
    def add_issue(self, severity: str, component: str, issue: str, recommendation: str):
        """Add a security configuration issue"""
        self.issues.append({
            'severity': severity,
            'component': component,
            'issue': issue,
            'recommendation': recommendation
        })
        self.failed_checks += 1
    
    def validate_environment_variables(self):
        """Validate environment variable security"""
        logger.info("Validating environment variables...")
        
        env_files = [
            '.env',
            '.env.production',
            '.env.server',
            'backend/.env'
        ]
        
        required_secure_vars = [
            'JWT_SECRET_KEY',
            'DATABASE_PASSWORD',
            'REDIS_PASSWORD',
            'SECRET_KEY',
            'ENCRYPTION_KEY'
        ]
        
        for env_file in env_files:
            env_path = self.project_root / env_file
            if env_path.exists():
                try:
                    with open(env_path, 'r') as f:
                        content = f.read()
                    
                    # Check for weak secrets
                    if 'password=123456' in content.lower() or 'secret=test' in content.lower():
                        self.add_issue(
                            'CRITICAL',
                            f'Environment ({env_file})',
                            'Weak default passwords or secrets detected',
                            'Use strong, randomly generated secrets'
                        )
                    
                    # Check for missing required variables
                    for var in required_secure_vars:
                        if var not in content:
                            self.add_issue(
                                'HIGH',
                                f'Environment ({env_file})',
                                f'Missing required security variable: {var}',
                                f'Add {var} with a secure value'
                            )
                    
                    # Check for exposed secrets in comments
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if line.strip().startswith('#') and any(word in line.lower() for word in ['password', 'secret', 'key']):
                            if '=' in line:
                                self.add_issue(
                                    'MEDIUM',
                                    f'Environment ({env_file})',
                                    f'Potential secret exposed in comment at line {i}',
                                    'Remove secrets from comments'
                                )
                
                except Exception as e:
                    logger.error(f"Error reading {env_file}: {e}")
        
        self.passed_checks += 1
    
    def validate_database_security(self):
        """Validate database security configuration"""
        logger.info("Validating database security...")
        
        # Check database configuration files
        db_config_files = [
            'backend/app/core/database.py',
            'backend/config/database_config.py',
            'database/init/01-init-database.sql'
        ]
        
        for config_file in db_config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        content = f.read()
                    
                    # Check for hardcoded credentials
                    if re.search(r'password\s*=\s*["\'](?!.*\$)[^"\']{1,20}["\']', content, re.IGNORECASE):
                        self.add_issue(
                            'CRITICAL',
                            f'Database Config ({config_file})',
                            'Hardcoded database password detected',
                            'Use environment variables for database credentials'
                        )
                    
                    # Check for SQL injection prevention
                    if config_file.endswith('.py'):
                        if 'parameterized' not in content.lower() and 'prepared' not in content.lower():
                            if 'execute(' in content and '%s' not in content:
                                self.add_issue(
                                    'HIGH',
                                    f'Database Config ({config_file})',
                                    'Potential SQL injection vulnerability - not using parameterized queries',
                                    'Use parameterized queries for all database operations'
                                )
                
                except Exception as e:
                    logger.error(f"Error reading {config_file}: {e}")
        
        self.passed_checks += 1
    
    def validate_authentication_security(self):
        """Validate authentication security configuration"""
        logger.info("Validating authentication security...")
        
        auth_files = [
            'backend/app/core/security.py',
            'backend/app/services/unified_auth_service.py',
            'backend/app/middlewares/auth_middleware.py'
        ]
        
        for auth_file in auth_files:
            auth_path = self.project_root / auth_file
            if auth_path.exists():
                try:
                    with open(auth_path, 'r') as f:
                        content = f.read()
                    
                    # Check for secure password hashing
                    if 'bcrypt' not in content.lower() and 'scrypt' not in content.lower() and 'argon2' not in content.lower():
                        if 'hash' in content.lower() and 'password' in content.lower():
                            self.add_issue(
                                'HIGH',
                                f'Authentication ({auth_file})',
                                'Weak password hashing algorithm detected',
                                'Use bcrypt, scrypt, or Argon2 for password hashing'
                            )
                    
                    # Check for JWT security
                    if 'jwt' in content.lower():
                        if 'HS256' in content and 'RS256' not in content:
                            self.add_issue(
                                'MEDIUM',
                                f'Authentication ({auth_file})',
                                'Using symmetric JWT algorithm (HS256) instead of asymmetric',
                                'Consider using RS256 for better security'
                            )
                        
                        if 'exp' not in content.lower():
                            self.add_issue(
                                'MEDIUM',
                                f'Authentication ({auth_file})',
                                'JWT tokens may not have expiration',
                                'Ensure all JWT tokens have expiration times'
                            )
                    
                    # Check for session security
                    if 'session' in content.lower():
                        if 'httponly' not in content.lower():
                            self.add_issue(
                                'MEDIUM',
                                f'Authentication ({auth_file})',
                                'Session cookies may not be HttpOnly',
                                'Set HttpOnly flag on session cookies'
                            )
                        
                        if 'secure' not in content.lower():
                            self.add_issue(
                                'MEDIUM',
                                f'Authentication ({auth_file})',
                                'Session cookies may not be Secure',
                                'Set Secure flag on session cookies for HTTPS'
                            )
                
                except Exception as e:
                    logger.error(f"Error reading {auth_file}: {e}")
        
        self.passed_checks += 1
    
    def validate_input_validation(self):
        """Validate input validation and sanitization"""
        logger.info("Validating input validation...")
        
        api_files = list((self.project_root / 'backend/app/api').rglob('*.py'))
        
        for api_file in api_files:
            try:
                with open(api_file, 'r') as f:
                    content = f.read()
                
                # Check for input validation
                if 'request' in content and 'json' in content:
                    if 'validate' not in content.lower() and 'schema' not in content.lower():
                        self.add_issue(
                            'MEDIUM',
                            f'API Endpoint ({api_file.name})',
                            'Missing input validation',
                            'Implement input validation for all API endpoints'
                        )
                
                # Check for SQL injection prevention
                if 'execute(' in content:
                    if '%s' not in content and '?' not in content:
                        self.add_issue(
                            'HIGH',
                            f'API Endpoint ({api_file.name})',
                            'Potential SQL injection vulnerability',
                            'Use parameterized queries'
                        )
                
                # Check for XSS prevention
                if 'html' in content.lower() or 'render' in content.lower():
                    if 'escape' not in content.lower() and 'sanitize' not in content.lower():
                        self.add_issue(
                            'MEDIUM',
                            f'API Endpoint ({api_file.name})',
                            'Potential XSS vulnerability - missing output encoding',
                            'Implement proper output encoding/escaping'
                        )
            
            except Exception as e:
                logger.debug(f"Error reading {api_file}: {e}")
        
        self.passed_checks += 1
    
    def validate_https_configuration(self):
        """Validate HTTPS and SSL/TLS configuration"""
        logger.info("Validating HTTPS configuration...")
        
        nginx_configs = [
            'nginx/nginx.conf',
            'nginx/lawsker.conf'
        ]
        
        for config_file in nginx_configs:
            config_path = self.project_root / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        content = f.read()
                    
                    # Check for HTTPS redirect
                    if 'listen 80' in content and 'return 301 https' not in content:
                        self.add_issue(
                            'HIGH',
                            f'NGINX Config ({config_file})',
                            'HTTP traffic not redirected to HTTPS',
                            'Configure HTTP to HTTPS redirect'
                        )
                    
                    # Check for SSL configuration
                    if 'ssl_certificate' not in content:
                        self.add_issue(
                            'HIGH',
                            f'NGINX Config ({config_file})',
                            'SSL certificate not configured',
                            'Configure SSL certificates'
                        )
                    
                    # Check for security headers
                    security_headers = [
                        'X-Content-Type-Options',
                        'X-Frame-Options',
                        'X-XSS-Protection',
                        'Strict-Transport-Security'
                    ]
                    
                    for header in security_headers:
                        if header not in content:
                            self.add_issue(
                                'MEDIUM',
                                f'NGINX Config ({config_file})',
                                f'Missing security header: {header}',
                                f'Add {header} header to NGINX configuration'
                            )
                
                except Exception as e:
                    logger.error(f"Error reading {config_file}: {e}")
        
        self.passed_checks += 1
    
    def validate_rate_limiting(self):
        """Validate rate limiting configuration"""
        logger.info("Validating rate limiting...")
        
        rate_limit_files = [
            'backend/app/middlewares/rate_limit_middleware.py',
            'backend/config/rate_limit_config.py',
            'nginx/nginx.conf'
        ]
        
        rate_limit_configured = False
        
        for config_file in rate_limit_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        content = f.read()
                    
                    if 'rate_limit' in content.lower() or 'limit_req' in content:
                        rate_limit_configured = True
                        break
                
                except Exception as e:
                    logger.error(f"Error reading {config_file}: {e}")
        
        if not rate_limit_configured:
            self.add_issue(
                'MEDIUM',
                'Rate Limiting',
                'Rate limiting not configured',
                'Implement rate limiting to prevent abuse'
            )
        
        self.passed_checks += 1
    
    def validate_logging_security(self):
        """Validate security logging configuration"""
        logger.info("Validating security logging...")
        
        logging_files = [
            'backend/app/core/logging.py',
            'backend/app/services/security_logger.py'
        ]
        
        security_logging_configured = False
        
        for log_file in logging_files:
            log_path = self.project_root / log_file
            if log_path.exists():
                try:
                    with open(log_path, 'r') as f:
                        content = f.read()
                    
                    # Check for security event logging
                    security_events = ['login', 'authentication', 'authorization', 'access']
                    if any(event in content.lower() for event in security_events):
                        security_logging_configured = True
                    
                    # Check for sensitive data in logs
                    if 'password' in content.lower() and 'log' in content.lower():
                        if 'mask' not in content.lower() and 'redact' not in content.lower():
                            self.add_issue(
                                'HIGH',
                                f'Logging ({log_file})',
                                'Potential sensitive data logging',
                                'Ensure passwords and sensitive data are not logged'
                            )
                
                except Exception as e:
                    logger.error(f"Error reading {log_file}: {e}")
        
        if not security_logging_configured:
            self.add_issue(
                'MEDIUM',
                'Security Logging',
                'Security event logging not configured',
                'Implement comprehensive security event logging'
            )
        
        self.passed_checks += 1
    
    def validate_dependency_security(self):
        """Validate dependency security"""
        logger.info("Validating dependency security...")
        
        requirements_files = [
            'backend/requirements.txt',
            'backend/requirements-prod.txt',
            'frontend/package.json'
        ]
        
        for req_file in requirements_files:
            req_path = self.project_root / req_file
            if req_path.exists():
                try:
                    # Check for known vulnerable packages (simplified check)
                    with open(req_path, 'r') as f:
                        content = f.read()
                    
                    # Known vulnerable patterns (this is a simplified check)
                    vulnerable_patterns = [
                        'django==1.',  # Old Django versions
                        'flask==0.',   # Old Flask versions
                        'requests==2.0',  # Old requests versions
                        'pillow==2.',  # Old Pillow versions
                    ]
                    
                    for pattern in vulnerable_patterns:
                        if pattern in content.lower():
                            self.add_issue(
                                'HIGH',
                                f'Dependencies ({req_file})',
                                f'Potentially vulnerable dependency: {pattern}',
                                'Update to latest secure version'
                            )
                
                except Exception as e:
                    logger.error(f"Error reading {req_file}: {e}")
        
        self.passed_checks += 1
    
    def validate_file_permissions(self):
        """Validate file permissions"""
        logger.info("Validating file permissions...")
        
        sensitive_files = [
            '.env',
            '.env.production',
            'backend/jwt_private_key.pem',
            'jwt_private_key.pem'
        ]
        
        for file_path in sensitive_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    # Check file permissions (Unix-like systems)
                    import stat
                    file_stat = full_path.stat()
                    permissions = stat.filemode(file_stat.st_mode)
                    
                    # Check if file is readable by others
                    if file_stat.st_mode & stat.S_IROTH:
                        self.add_issue(
                            'HIGH',
                            f'File Permissions ({file_path})',
                            'Sensitive file readable by others',
                            'Restrict file permissions (chmod 600)'
                        )
                    
                    # Check if file is writable by group or others
                    if file_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
                        self.add_issue(
                            'HIGH',
                            f'File Permissions ({file_path})',
                            'Sensitive file writable by group or others',
                            'Restrict file permissions (chmod 600)'
                        )
                
                except Exception as e:
                    logger.debug(f"Error checking permissions for {file_path}: {e}")
        
        self.passed_checks += 1
    
    def run_all_validations(self):
        """Run all security configuration validations"""
        logger.info("Starting security configuration validation...")
        
        validation_methods = [
            self.validate_environment_variables,
            self.validate_database_security,
            self.validate_authentication_security,
            self.validate_input_validation,
            self.validate_https_configuration,
            self.validate_rate_limiting,
            self.validate_logging_security,
            self.validate_dependency_security,
            self.validate_file_permissions,
        ]
        
        for method in validation_methods:
            try:
                method()
            except Exception as e:
                logger.error(f"Error in {method.__name__}: {e}")
                self.failed_checks += 1
        
        logger.info("Security configuration validation completed")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate security configuration report"""
        critical_issues = [i for i in self.issues if i['severity'] == 'CRITICAL']
        high_issues = [i for i in self.issues if i['severity'] == 'HIGH']
        medium_issues = [i for i in self.issues if i['severity'] == 'MEDIUM']
        low_issues = [i for i in self.issues if i['severity'] == 'LOW']
        
        return {
            'summary': {
                'total_checks': self.passed_checks + self.failed_checks,
                'passed_checks': self.passed_checks,
                'failed_checks': self.failed_checks,
                'total_issues': len(self.issues),
                'critical_issues': len(critical_issues),
                'high_issues': len(high_issues),
                'medium_issues': len(medium_issues),
                'low_issues': len(low_issues),
                'security_score': self.calculate_security_score()
            },
            'issues': {
                'critical': critical_issues,
                'high': high_issues,
                'medium': medium_issues,
                'low': low_issues
            }
        }
    
    def calculate_security_score(self) -> int:
        """Calculate security configuration score"""
        if self.passed_checks + self.failed_checks == 0:
            return 0
        
        # Weight issues by severity
        critical_weight = 20
        high_weight = 10
        medium_weight = 5
        low_weight = 1
        
        total_penalty = sum(
            critical_weight if i['severity'] == 'CRITICAL' else
            high_weight if i['severity'] == 'HIGH' else
            medium_weight if i['severity'] == 'MEDIUM' else
            low_weight
            for i in self.issues
        )
        
        max_penalty = (self.passed_checks + self.failed_checks) * critical_weight
        
        if max_penalty == 0:
            return 100
        
        score = max(0, 100 - (total_penalty * 100 // max_penalty))
        return score

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Security Configuration Validator')
    parser.add_argument('--project-root', default='.', help='Project root directory')
    parser.add_argument('--output', default='security_config_report.json', help='Output report file')
    
    args = parser.parse_args()
    
    validator = SecurityConfigValidator(args.project_root)
    validator.run_all_validations()
    
    report = validator.generate_report()
    
    # Save report
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("SECURITY CONFIGURATION VALIDATION REPORT")
    print("="*60)
    print(f"Total Checks: {report['summary']['total_checks']}")
    print(f"Passed: {report['summary']['passed_checks']}")
    print(f"Failed: {report['summary']['failed_checks']}")
    print(f"Total Issues: {report['summary']['total_issues']}")
    print(f"Critical: {report['summary']['critical_issues']}")
    print(f"High: {report['summary']['high_issues']}")
    print(f"Medium: {report['summary']['medium_issues']}")
    print(f"Low: {report['summary']['low_issues']}")
    print(f"Security Score: {report['summary']['security_score']}/100")
    print("="*60)
    
    # Print critical and high issues
    if report['issues']['critical']:
        print("\nCRITICAL ISSUES:")
        for issue in report['issues']['critical']:
            print(f"- {issue['component']}: {issue['issue']}")
            print(f"  Recommendation: {issue['recommendation']}")
    
    if report['issues']['high']:
        print("\nHIGH ISSUES:")
        for issue in report['issues']['high']:
            print(f"- {issue['component']}: {issue['issue']}")
            print(f"  Recommendation: {issue['recommendation']}")
    
    print(f"\nDetailed report saved to: {args.output}")
    
    # Exit with error code if critical or high issues found
    if report['summary']['critical_issues'] > 0 or report['summary']['high_issues'] > 0:
        print("\n❌ SECURITY CONFIGURATION VALIDATION FAILED!")
        sys.exit(1)
    else:
        print("\n✅ SECURITY CONFIGURATION VALIDATION PASSED!")
        sys.exit(0)

if __name__ == "__main__":
    main()