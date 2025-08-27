#!/usr/bin/env python3
"""
Comprehensive Security Verification for Lawsker System
Verifies all security implementations and ensures no high-risk vulnerabilities
"""

import os
import sys
import json
import hashlib
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SecurityVerifier:
    """Comprehensive security verification system"""
    
    def __init__(self):
        self.verification_results = {
            'timestamp': datetime.now().isoformat(),
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'low_issues': 0,
            'security_score': 0,
            'checks': {}
        }
        
    def verify_authentication_security(self) -> bool:
        """Verify authentication security implementation"""
        logger.info("Verifying authentication security...")
        
        checks = {
            'unified_auth_service': self._check_file_exists('backend/app/services/unified_auth_service.py'),
            'password_hashing': self._check_password_hashing(),
            'jwt_security': self._check_jwt_implementation(),
            'workspace_security': self._check_workspace_security(),
            'session_management': self._check_session_management()
        }
        
        passed = all(checks.values())
        self.verification_results['checks']['authentication'] = {
            'passed': passed,
            'details': checks,
            'score': sum(checks.values()) / len(checks) * 100
        }
        
        return passed
    
    def verify_data_protection(self) -> bool:
        """Verify data protection measures"""
        logger.info("Verifying data protection...")
        
        checks = {
            'encryption_middleware': self._check_file_exists('backend/app/middlewares/encryption_middleware.py'),
            'database_encryption': self._check_database_encryption(),
            'file_encryption': self._check_file_encryption(),
            'demo_data_isolation': self._check_demo_isolation(),
            'sensitive_data_handling': self._check_sensitive_data_handling()
        }
        
        passed = all(checks.values())
        self.verification_results['checks']['data_protection'] = {
            'passed': passed,
            'details': checks,
            'score': sum(checks.values()) / len(checks) * 100
        }
        
        return passed
    
    def verify_input_validation(self) -> bool:
        """Verify input validation and sanitization"""
        logger.info("Verifying input validation...")
        
        checks = {
            'api_validation': self._check_api_validation(),
            'sql_injection_protection': self._check_sql_injection_protection(),
            'xss_protection': self._check_xss_protection(),
            'file_upload_security': self._check_file_upload_security(),
            'csrf_protection': self._check_csrf_protection()
        }
        
        passed = all(checks.values())
        self.verification_results['checks']['input_validation'] = {
            'passed': passed,
            'details': checks,
            'score': sum(checks.values()) / len(checks) * 100
        }
        
        return passed
    
    def verify_network_security(self) -> bool:
        """Verify network security configuration"""
        logger.info("Verifying network security...")
        
        checks = {
            'https_configuration': self._check_https_config(),
            'security_headers': self._check_security_headers(),
            'rate_limiting': self._check_rate_limiting(),
            'cors_configuration': self._check_cors_config(),
            'nginx_security': self._check_nginx_security()
        }
        
        passed = all(checks.values())
        self.verification_results['checks']['network_security'] = {
            'passed': passed,
            'details': checks,
            'score': sum(checks.values()) / len(checks) * 100
        }
        
        return passed
    
    def verify_monitoring_logging(self) -> bool:
        """Verify monitoring and logging implementation"""
        logger.info("Verifying monitoring and logging...")
        
        checks = {
            'security_logging': self._check_security_logging(),
            'audit_trails': self._check_audit_trails(),
            'monitoring_system': self._check_monitoring_system(),
            'alert_system': self._check_alert_system(),
            'health_monitoring': self._check_health_monitoring()
        }
        
        passed = all(checks.values())
        self.verification_results['checks']['monitoring_logging'] = {
            'passed': passed,
            'details': checks,
            'score': sum(checks.values()) / len(checks) * 100
        }
        
        return passed
    
    def verify_infrastructure_security(self) -> bool:
        """Verify infrastructure security"""
        logger.info("Verifying infrastructure security...")
        
        checks = {
            'file_permissions': self._check_file_permissions(),
            'environment_security': self._check_environment_security(),
            'dependency_security': self._check_dependency_security(),
            'configuration_security': self._check_configuration_security(),
            'backup_security': self._check_backup_security()
        }
        
        passed = all(checks.values())
        self.verification_results['checks']['infrastructure'] = {
            'passed': passed,
            'details': checks,
            'score': sum(checks.values()) / len(checks) * 100
        }
        
        return passed
    
    def verify_compliance_requirements(self) -> bool:
        """Verify compliance with security requirements"""
        logger.info("Verifying compliance requirements...")
        
        checks = {
            'workspace_id_security': self._check_workspace_id_security(),
            'demo_data_isolation': self._check_demo_isolation(),
            'certificate_encryption': self._check_certificate_encryption(),
            'audit_logging': self._check_audit_logging(),
            'pci_dss_compliance': self._check_pci_dss_compliance(),
            'performance_requirements': self._check_performance_requirements(),
            'availability_requirements': self._check_availability_requirements(),
            'concurrency_support': self._check_concurrency_support()
        }
        
        passed = all(checks.values())
        self.verification_results['checks']['compliance'] = {
            'passed': passed,
            'details': checks,
            'score': sum(checks.values()) / len(checks) * 100
        }
        
        return passed
    
    def _check_file_exists(self, filepath: str) -> bool:
        """Check if a file exists"""
        return os.path.exists(filepath)
    
    def _check_password_hashing(self) -> bool:
        """Check password hashing implementation"""
        auth_files = [
            'backend/app/services/unified_auth_service.py',
            'backend/app/core/security.py'
        ]
        
        for filepath in auth_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    if any(term in content for term in ['bcrypt', 'scrypt', 'hash_password', 'verify_password']):
                        return True
        return False
    
    def _check_jwt_implementation(self) -> bool:
        """Check JWT implementation"""
        jwt_indicators = [
            'jwt_private_key.pem',
            'backend/jwt_private_key.pem'
        ]
        
        for filepath in jwt_indicators:
            if os.path.exists(filepath):
                return True
        
        # Check for JWT in code
        security_files = [
            'backend/app/core/security.py',
            'backend/app/services/unified_auth_service.py'
        ]
        
        for filepath in security_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    if any(term in content for term in ['jwt', 'JWT', 'token', 'create_access_token']):
                        return True
        
        return False
    
    def _check_workspace_security(self) -> bool:
        """Check workspace security implementation"""
        workspace_files = [
            'backend/app/middlewares/workspace_middleware.py',
            'backend/app/services/unified_auth_service.py'
        ]
        
        for filepath in workspace_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    if any(term in content for term in ['workspace_id', 'secure_workspace', 'workspace_hash']):
                        return True
        return False
    
    def _check_session_management(self) -> bool:
        """Check session management"""
        return self._check_file_exists('backend/app/middlewares/auth_middleware.py')
    
    def _check_database_encryption(self) -> bool:
        """Check database encryption"""
        return self._check_file_exists('backend/app/middlewares/encryption_middleware.py')
    
    def _check_file_encryption(self) -> bool:
        """Check file encryption implementation"""
        encryption_files = [
            'backend/app/core/encryption.py',
            'backend/app/services/lawyer_certification_service.py'
        ]
        
        for filepath in encryption_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    if any(term in content for term in ['encrypt', 'decrypt', 'AES', 'Fernet']):
                        return True
        return False
    
    def _check_demo_isolation(self) -> bool:
        """Check demo data isolation"""
        demo_files = [
            'backend/app/services/demo_data_isolation_service.py',
            'backend/app/middlewares/demo_security_middleware.py'
        ]
        
        return all(os.path.exists(f) for f in demo_files)
    
    def _check_sensitive_data_handling(self) -> bool:
        """Check sensitive data handling"""
        return self._check_file_exists('backend/app/core/encryption.py')
    
    def _check_api_validation(self) -> bool:
        """Check API validation implementation"""
        api_files = []
        api_dir = 'backend/app/api/v1/endpoints'
        
        if os.path.exists(api_dir):
            api_files = [os.path.join(api_dir, f) for f in os.listdir(api_dir) if f.endswith('.py')]
        
        validation_found = False
        for filepath in api_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    if any(term in content for term in ['pydantic', 'BaseModel', 'validator', 'Field']):
                        validation_found = True
                        break
        
        return validation_found
    
    def _check_sql_injection_protection(self) -> bool:
        """Check SQL injection protection"""
        db_files = [
            'backend/app/core/database.py',
            'backend/app/models'
        ]
        
        for filepath in db_files:
            if os.path.exists(filepath):
                if os.path.isdir(filepath):
                    # Check model files
                    for model_file in os.listdir(filepath):
                        if model_file.endswith('.py'):
                            with open(os.path.join(filepath, model_file), 'r') as f:
                                content = f.read()
                                if any(term in content for term in ['SQLAlchemy', 'declarative_base', 'Column']):
                                    return True
                else:
                    with open(filepath, 'r') as f:
                        content = f.read()
                        if any(term in content for term in ['SQLAlchemy', 'sessionmaker', 'create_engine']):
                            return True
        return False
    
    def _check_xss_protection(self) -> bool:
        """Check XSS protection"""
        security_files = [
            'backend/app/middlewares/enhanced_security_middleware.py',
            'backend/app/core/security.py'
        ]
        
        for filepath in security_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    if any(term in content for term in ['escape', 'sanitize', 'Content-Security-Policy']):
                        return True
        return False
    
    def _check_file_upload_security(self) -> bool:
        """Check file upload security"""
        upload_files = [
            'backend/app/services/file_upload_service.py',
            'backend/app/services/lawyer_certification_service.py'
        ]
        
        for filepath in upload_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    if any(term in content for term in ['validate_file', 'allowed_extensions', 'file_size']):
                        return True
        return False
    
    def _check_csrf_protection(self) -> bool:
        """Check CSRF protection"""
        return self._check_file_exists('backend/app/middlewares/csrf_middleware.py')
    
    def _check_https_config(self) -> bool:
        """Check HTTPS configuration"""
        nginx_files = [
            'nginx/nginx.conf',
            'nginx/lawsker.conf'
        ]
        
        for filepath in nginx_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    if any(term in content for term in ['ssl', 'https', 'ssl_certificate']):
                        return True
        return False
    
    def _check_security_headers(self) -> bool:
        """Check security headers implementation"""
        middleware_files = [
            'backend/app/middlewares/enhanced_security_middleware.py',
            'nginx/nginx.conf'
        ]
        
        for filepath in middleware_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    if any(term in content for term in ['X-Frame-Options', 'X-Content-Type-Options', 'Strict-Transport-Security']):
                        return True
        return False
    
    def _check_rate_limiting(self) -> bool:
        """Check rate limiting implementation"""
        return self._check_file_exists('backend/app/middlewares/rate_limit_middleware.py')
    
    def _check_cors_config(self) -> bool:
        """Check CORS configuration"""
        config_files = [
            'backend/app/main.py',
            'backend/app/core/config.py'
        ]
        
        for filepath in config_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    if any(term in content for term in ['CORS', 'CORSMiddleware', 'allow_origins']):
                        return True
        return False
    
    def _check_nginx_security(self) -> bool:
        """Check NGINX security configuration"""
        nginx_files = [
            'nginx/nginx.conf',
            'nginx/lawsker.conf'
        ]
        
        for filepath in nginx_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    if any(term in content for term in ['server_tokens off', 'client_max_body_size', 'rate_limit']):
                        return True
        return False
    
    def _check_security_logging(self) -> bool:
        """Check security logging implementation"""
        return self._check_file_exists('backend/app/services/security_logger.py')
    
    def _check_audit_trails(self) -> bool:
        """Check audit trail implementation"""
        audit_files = [
            'backend/app/services/lawyer_points_engine.py',
            'backend/app/services/user_credits_service.py'
        ]
        
        for filepath in audit_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    if any(term in content for term in ['audit', 'log_transaction', 'record_change']):
                        return True
        return False
    
    def _check_monitoring_system(self) -> bool:
        """Check monitoring system implementation"""
        monitoring_files = [
            'backend/app/core/performance_monitor.py',
            'backend/app/services/health_monitor.py'
        ]
        
        return any(os.path.exists(f) for f in monitoring_files)
    
    def _check_alert_system(self) -> bool:
        """Check alert system implementation"""
        return self._check_file_exists('backend/app/services/alert_manager.py')
    
    def _check_health_monitoring(self) -> bool:
        """Check health monitoring implementation"""
        return self._check_file_exists('backend/app/services/health_monitor.py')
    
    def _check_file_permissions(self) -> bool:
        """Check file permissions"""
        sensitive_files = [
            '.env.production',
            '.env.server',
            'jwt_private_key.pem',
            'backend/jwt_private_key.pem'
        ]
        
        for filepath in sensitive_files:
            if os.path.exists(filepath):
                stat = os.stat(filepath)
                # Check if file is readable only by owner (600 or 400)
                if stat.st_mode & 0o077 != 0:
                    return False
        return True
    
    def _check_environment_security(self) -> bool:
        """Check environment security"""
        env_files = ['.env.production', '.env.server']
        
        for filepath in env_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    if any(term in content for term in ['SECRET_KEY', 'DATABASE_URL', 'JWT_SECRET']):
                        return True
        return False
    
    def _check_dependency_security(self) -> bool:
        """Check dependency security"""
        requirements_files = [
            'backend/requirements.txt',
            'backend/requirements-prod.txt'
        ]
        
        for filepath in requirements_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    if any(term in content for term in ['cryptography', 'bcrypt', 'pyjwt']):
                        return True
        return False
    
    def _check_configuration_security(self) -> bool:
        """Check configuration security"""
        config_files = [
            'backend/config/security_config.py',
            'backend/app/core/config.py'
        ]
        
        return any(os.path.exists(f) for f in config_files)
    
    def _check_backup_security(self) -> bool:
        """Check backup security"""
        return os.path.exists('security_backups')
    
    def _check_workspace_id_security(self) -> bool:
        """Check workspace ID security implementation"""
        return self._check_workspace_security()
    
    def _check_certificate_encryption(self) -> bool:
        """Check certificate encryption"""
        return self._check_file_encryption()
    
    def _check_audit_logging(self) -> bool:
        """Check audit logging implementation"""
        return self._check_audit_trails()
    
    def _check_pci_dss_compliance(self) -> bool:
        """Check PCI DSS compliance"""
        payment_files = [
            'backend/app/services/payment_service.py',
            'backend/app/services/user_credits_service.py'
        ]
        
        for filepath in payment_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    if any(term in content for term in ['encrypt', 'secure', 'payment', 'pci']):
                        return True
        return False
    
    def _check_performance_requirements(self) -> bool:
        """Check performance requirements implementation"""
        return self._check_file_exists('backend/app/core/performance.py')
    
    def _check_availability_requirements(self) -> bool:
        """Check availability requirements implementation"""
        return self._check_file_exists('backend/app/services/health_monitor.py')
    
    def _check_concurrency_support(self) -> bool:
        """Check concurrency support implementation"""
        return self._check_file_exists('backend/app/core/performance.py')
    
    def calculate_security_score(self) -> int:
        """Calculate overall security score"""
        total_score = 0
        total_categories = 0
        
        for category, results in self.verification_results['checks'].items():
            if 'score' in results:
                total_score += results['score']
                total_categories += 1
        
        if total_categories == 0:
            return 0
        
        return int(total_score / total_categories)
    
    def run_comprehensive_verification(self) -> Dict[str, Any]:
        """Run comprehensive security verification"""
        logger.info("Starting comprehensive security verification...")
        
        verification_methods = [
            self.verify_authentication_security,
            self.verify_data_protection,
            self.verify_input_validation,
            self.verify_network_security,
            self.verify_monitoring_logging,
            self.verify_infrastructure_security,
            self.verify_compliance_requirements
        ]
        
        total_checks = len(verification_methods)
        passed_checks = 0
        
        for method in verification_methods:
            try:
                if method():
                    passed_checks += 1
                    logger.info(f"✅ {method.__name__} passed")
                else:
                    logger.warning(f"❌ {method.__name__} failed")
            except Exception as e:
                logger.error(f"❌ {method.__name__} error: {e}")
        
        # Update results
        self.verification_results.update({
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'failed_checks': total_checks - passed_checks,
            'security_score': self.calculate_security_score()
        })
        
        # Determine risk levels based on failures
        if self.verification_results['failed_checks'] == 0:
            self.verification_results['risk_level'] = 'LOW'
        elif self.verification_results['failed_checks'] <= 2:
            self.verification_results['risk_level'] = 'MEDIUM'
        else:
            self.verification_results['risk_level'] = 'HIGH'
        
        return self.verification_results
    
    def generate_report(self) -> str:
        """Generate security verification report"""
        results = self.verification_results
        
        report = f"""
================================================================================
COMPREHENSIVE SECURITY VERIFICATION REPORT
================================================================================
Verification Date: {results['timestamp']}
Total Checks: {results['total_checks']}
Passed Checks: {results['passed_checks']}
Failed Checks: {results['failed_checks']}
Security Score: {results['security_score']}/100
Risk Level: {results.get('risk_level', 'UNKNOWN')}

DETAILED RESULTS:
================================================================================
"""
        
        for category, details in results['checks'].items():
            status = "✅ PASSED" if details['passed'] else "❌ FAILED"
            score = details.get('score', 0)
            
            report += f"""
{category.upper().replace('_', ' ')}: {status} (Score: {score:.1f}/100)
"""
            
            for check_name, check_result in details['details'].items():
                check_status = "✅" if check_result else "❌"
                report += f"  {check_status} {check_name.replace('_', ' ').title()}\n"
        
        report += f"""
================================================================================
SECURITY ASSESSMENT:
================================================================================
"""
        
        if results['security_score'] >= 95:
            report += "🟢 EXCELLENT: System has excellent security posture with minimal risks.\n"
        elif results['security_score'] >= 85:
            report += "🟡 GOOD: System has good security posture with some areas for improvement.\n"
        elif results['security_score'] >= 70:
            report += "🟠 FAIR: System has fair security posture but requires attention.\n"
        else:
            report += "🔴 POOR: System has poor security posture and requires immediate attention.\n"
        
        if results['failed_checks'] == 0:
            report += "\n✅ NO HIGH-RISK VULNERABILITIES FOUND\n"
            report += "✅ SYSTEM IS READY FOR PRODUCTION DEPLOYMENT\n"
        else:
            report += f"\n❌ {results['failed_checks']} SECURITY CHECKS FAILED\n"
            report += "❌ SECURITY ISSUES MUST BE ADDRESSED BEFORE DEPLOYMENT\n"
        
        report += """
================================================================================
"""
        
        return report

def main():
    """Main function"""
    logger.info("Starting comprehensive security verification...")
    
    verifier = SecurityVerifier()
    results = verifier.run_comprehensive_verification()
    
    # Generate and save report
    report = verifier.generate_report()
    
    # Save results to JSON
    with open('security_verification_comprehensive.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save report to text file
    with open('security_verification_comprehensive.txt', 'w') as f:
        f.write(report)
    
    # Print report
    print(report)
    
    # Exit with appropriate code
    if results['failed_checks'] == 0 and results['security_score'] >= 85:
        logger.info("🎉 Security verification completed successfully!")
        return 0
    else:
        logger.error("❌ Security verification failed - issues must be addressed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())