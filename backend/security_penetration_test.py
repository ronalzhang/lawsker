#!/usr/bin/env python3
"""
Lawsker Security Penetration Testing Suite
Comprehensive security testing to identify and prevent high-risk vulnerabilities
"""

import asyncio
import aiohttp
import json
import hashlib
import hmac
import time
import random
import string
import subprocess
import sys
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VulnerabilityLevel(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

@dataclass
class SecurityFinding:
    """Security vulnerability finding"""
    title: str
    level: VulnerabilityLevel
    description: str
    endpoint: str
    payload: Optional[str] = None
    recommendation: str = ""
    cve_reference: Optional[str] = None

class SecurityPenetrationTester:
    """Comprehensive security penetration testing suite"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.findings: List[SecurityFinding] = []
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'critical_findings': 0,
            'high_findings': 0,
            'medium_findings': 0,
            'low_findings': 0
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(ssl=False)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def add_finding(self, finding: SecurityFinding):
        """Add a security finding"""
        self.findings.append(finding)
        if finding.level == VulnerabilityLevel.CRITICAL:
            self.test_results['critical_findings'] += 1
        elif finding.level == VulnerabilityLevel.HIGH:
            self.test_results['high_findings'] += 1
        elif finding.level == VulnerabilityLevel.MEDIUM:
            self.test_results['medium_findings'] += 1
        elif finding.level == VulnerabilityLevel.LOW:
            self.test_results['low_findings'] += 1
    
    async def test_sql_injection(self):
        """Test for SQL injection vulnerabilities"""
        logger.info("Testing SQL injection vulnerabilities...")
        
        # Common SQL injection payloads
        sql_payloads = [
            "' OR '1'='1",
            "' OR 1=1--",
            "' UNION SELECT NULL--",
            "'; DROP TABLE users;--",
            "' OR 'x'='x",
            "1' AND 1=1--",
            "1' AND 1=2--",
            "admin'--",
            "' OR 1=1#",
            "' OR 'a'='a",
            "') OR ('1'='1",
            "1' OR '1'='1' /*",
        ]
        
        # Test endpoints that might be vulnerable
        test_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/users/search",
            "/api/v1/lawyers/search",
            "/api/v1/cases/search",
            "/api/v1/admin/users",
        ]
        
        for endpoint in test_endpoints:
            for payload in sql_payloads:
                try:
                    # Test GET parameters
                    url = urljoin(self.base_url, endpoint)
                    params = {'q': payload, 'search': payload, 'id': payload}
                    
                    async with self.session.get(url, params=params) as response:
                        response_text = await response.text()
                        
                        # Check for SQL error messages
                        sql_errors = [
                            'sql syntax',
                            'mysql_fetch',
                            'postgresql',
                            'ora-',
                            'microsoft ole db',
                            'sqlite_',
                            'sqlstate',
                            'column count doesn\'t match',
                            'table doesn\'t exist'
                        ]
                        
                        for error in sql_errors:
                            if error.lower() in response_text.lower():
                                self.add_finding(SecurityFinding(
                                    title="SQL Injection Vulnerability",
                                    level=VulnerabilityLevel.CRITICAL,
                                    description=f"SQL injection detected in {endpoint} with payload: {payload}",
                                    endpoint=endpoint,
                                    payload=payload,
                                    recommendation="Use parameterized queries and input validation",
                                    cve_reference="CWE-89"
                                ))
                                break
                    
                    # Test POST data
                    if endpoint in ["/api/v1/auth/login"]:
                        data = {'email': payload, 'password': payload}
                        async with self.session.post(url, json=data) as response:
                            response_text = await response.text()
                            
                            for error in sql_errors:
                                if error.lower() in response_text.lower():
                                    self.add_finding(SecurityFinding(
                                        title="SQL Injection in POST Data",
                                        level=VulnerabilityLevel.CRITICAL,
                                        description=f"SQL injection detected in POST data for {endpoint}",
                                        endpoint=endpoint,
                                        payload=str(data),
                                        recommendation="Use parameterized queries and input validation"
                                    ))
                                    break
                
                except Exception as e:
                    logger.debug(f"Error testing SQL injection on {endpoint}: {e}")
        
        self.test_results['total_tests'] += len(test_endpoints) * len(sql_payloads)
    
    async def test_xss_vulnerabilities(self):
        """Test for Cross-Site Scripting (XSS) vulnerabilities"""
        logger.info("Testing XSS vulnerabilities...")
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src=javascript:alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>",
            "<textarea onfocus=alert('XSS') autofocus>",
            "<keygen onfocus=alert('XSS') autofocus>",
            "<video><source onerror=alert('XSS')>",
            "<audio src=x onerror=alert('XSS')>",
        ]
        
        test_endpoints = [
            "/api/v1/cases/create",
            "/api/v1/users/profile",
            "/api/v1/lawyers/profile",
            "/api/v1/feedback/create",
        ]
        
        for endpoint in test_endpoints:
            for payload in xss_payloads:
                try:
                    url = urljoin(self.base_url, endpoint)
                    
                    # Test in various fields
                    test_data = {
                        'title': payload,
                        'description': payload,
                        'content': payload,
                        'name': payload,
                        'comment': payload
                    }
                    
                    async with self.session.post(url, json=test_data) as response:
                        response_text = await response.text()
                        
                        # Check if payload is reflected without encoding
                        if payload in response_text and '<script>' in response_text:
                            self.add_finding(SecurityFinding(
                                title="Cross-Site Scripting (XSS) Vulnerability",
                                level=VulnerabilityLevel.HIGH,
                                description=f"XSS vulnerability detected in {endpoint}",
                                endpoint=endpoint,
                                payload=payload,
                                recommendation="Implement proper input validation and output encoding",
                                cve_reference="CWE-79"
                            ))
                
                except Exception as e:
                    logger.debug(f"Error testing XSS on {endpoint}: {e}")
        
        self.test_results['total_tests'] += len(test_endpoints) * len(xss_payloads)
    
    async def test_authentication_bypass(self):
        """Test for authentication bypass vulnerabilities"""
        logger.info("Testing authentication bypass...")
        
        # Test endpoints that should require authentication
        protected_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/dashboard",
            "/api/v1/lawyers/profile",
            "/api/v1/users/profile",
            "/api/v1/cases/my-cases",
        ]
        
        for endpoint in protected_endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                
                # Test without authentication
                async with self.session.get(url) as response:
                    if response.status == 200:
                        self.add_finding(SecurityFinding(
                            title="Authentication Bypass",
                            level=VulnerabilityLevel.CRITICAL,
                            description=f"Protected endpoint {endpoint} accessible without authentication",
                            endpoint=endpoint,
                            recommendation="Implement proper authentication checks",
                            cve_reference="CWE-287"
                        ))
                
                # Test with invalid token
                headers = {'Authorization': 'Bearer invalid_token_12345'}
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        self.add_finding(SecurityFinding(
                            title="Invalid Token Accepted",
                            level=VulnerabilityLevel.HIGH,
                            description=f"Endpoint {endpoint} accepts invalid authentication token",
                            endpoint=endpoint,
                            recommendation="Implement proper token validation"
                        ))
            
            except Exception as e:
                logger.debug(f"Error testing auth bypass on {endpoint}: {e}")
        
        self.test_results['total_tests'] += len(protected_endpoints) * 2
    
    async def test_csrf_protection(self):
        """Test for CSRF protection"""
        logger.info("Testing CSRF protection...")
        
        # Test state-changing endpoints
        csrf_endpoints = [
            ("/api/v1/users/profile", "PUT"),
            ("/api/v1/cases/create", "POST"),
            ("/api/v1/lawyers/certification", "POST"),
            ("/api/v1/admin/users", "DELETE"),
        ]
        
        for endpoint, method in csrf_endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                
                # Test without CSRF token
                test_data = {'test': 'data'}
                
                if method == "POST":
                    async with self.session.post(url, json=test_data) as response:
                        if response.status not in [403, 400]:
                            self.add_finding(SecurityFinding(
                                title="Missing CSRF Protection",
                                level=VulnerabilityLevel.MEDIUM,
                                description=f"Endpoint {endpoint} lacks CSRF protection",
                                endpoint=endpoint,
                                recommendation="Implement CSRF tokens for state-changing operations",
                                cve_reference="CWE-352"
                            ))
                
                elif method == "PUT":
                    async with self.session.put(url, json=test_data) as response:
                        if response.status not in [403, 400]:
                            self.add_finding(SecurityFinding(
                                title="Missing CSRF Protection",
                                level=VulnerabilityLevel.MEDIUM,
                                description=f"Endpoint {endpoint} lacks CSRF protection",
                                endpoint=endpoint,
                                recommendation="Implement CSRF tokens for state-changing operations"
                            ))
            
            except Exception as e:
                logger.debug(f"Error testing CSRF on {endpoint}: {e}")
        
        self.test_results['total_tests'] += len(csrf_endpoints)
    
    async def test_rate_limiting(self):
        """Test rate limiting implementation"""
        logger.info("Testing rate limiting...")
        
        test_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/cases/create",
        ]
        
        for endpoint in test_endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                
                # Send multiple requests rapidly
                tasks = []
                for i in range(50):  # Send 50 requests
                    if endpoint == "/api/v1/auth/login":
                        data = {'email': f'test{i}@example.com', 'password': 'password'}
                    else:
                        data = {'test': f'data_{i}'}
                    
                    task = self.session.post(url, json=data)
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check if any rate limiting occurred
                rate_limited = False
                for response in responses:
                    if not isinstance(response, Exception) and response.status == 429:
                        rate_limited = True
                        break
                
                if not rate_limited:
                    self.add_finding(SecurityFinding(
                        title="Missing Rate Limiting",
                        level=VulnerabilityLevel.MEDIUM,
                        description=f"Endpoint {endpoint} lacks rate limiting protection",
                        endpoint=endpoint,
                        recommendation="Implement rate limiting to prevent abuse",
                        cve_reference="CWE-770"
                    ))
            
            except Exception as e:
                logger.debug(f"Error testing rate limiting on {endpoint}: {e}")
        
        self.test_results['total_tests'] += len(test_endpoints)
    
    async def test_information_disclosure(self):
        """Test for information disclosure vulnerabilities"""
        logger.info("Testing information disclosure...")
        
        # Test for sensitive information in responses
        test_endpoints = [
            "/api/v1/health",
            "/api/v1/version",
            "/api/v1/debug",
            "/api/v1/config",
            "/.env",
            "/config.json",
            "/api/v1/users",
            "/api/v1/admin/logs",
        ]
        
        sensitive_patterns = [
            r'password',
            r'secret',
            r'key',
            r'token',
            r'database',
            r'connection',
            r'api_key',
            r'private',
            r'confidential',
        ]
        
        for endpoint in test_endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        response_text = await response.text()
                        
                        for pattern in sensitive_patterns:
                            if pattern in response_text.lower():
                                self.add_finding(SecurityFinding(
                                    title="Information Disclosure",
                                    level=VulnerabilityLevel.MEDIUM,
                                    description=f"Sensitive information exposed in {endpoint}",
                                    endpoint=endpoint,
                                    recommendation="Remove sensitive information from public endpoints",
                                    cve_reference="CWE-200"
                                ))
                                break
            
            except Exception as e:
                logger.debug(f"Error testing info disclosure on {endpoint}: {e}")
        
        self.test_results['total_tests'] += len(test_endpoints)
    
    async def test_file_upload_vulnerabilities(self):
        """Test file upload security"""
        logger.info("Testing file upload vulnerabilities...")
        
        upload_endpoints = [
            "/api/v1/files/upload",
            "/api/v1/lawyers/certificate",
            "/api/v1/cases/documents",
        ]
        
        # Test malicious file uploads
        malicious_files = [
            ('shell.php', b'<?php system($_GET["cmd"]); ?>', 'application/x-php'),
            ('script.js', b'alert("XSS")', 'application/javascript'),
            ('test.exe', b'MZ\x90\x00', 'application/x-executable'),
            ('large.txt', b'A' * (10 * 1024 * 1024), 'text/plain'),  # 10MB file
        ]
        
        for endpoint in upload_endpoints:
            for filename, content, content_type in malicious_files:
                try:
                    url = urljoin(self.base_url, endpoint)
                    
                    data = aiohttp.FormData()
                    data.add_field('file', content, filename=filename, content_type=content_type)
                    
                    async with self.session.post(url, data=data) as response:
                        if response.status == 200:
                            response_data = await response.json()
                            
                            if filename.endswith('.php') or filename.endswith('.exe'):
                                self.add_finding(SecurityFinding(
                                    title="Malicious File Upload",
                                    level=VulnerabilityLevel.CRITICAL,
                                    description=f"Malicious file {filename} uploaded to {endpoint}",
                                    endpoint=endpoint,
                                    recommendation="Implement file type validation and scanning",
                                    cve_reference="CWE-434"
                                ))
                            
                            elif len(content) > 5 * 1024 * 1024:  # 5MB
                                self.add_finding(SecurityFinding(
                                    title="Large File Upload Allowed",
                                    level=VulnerabilityLevel.MEDIUM,
                                    description=f"Large file upload allowed on {endpoint}",
                                    endpoint=endpoint,
                                    recommendation="Implement file size limits"
                                ))
                
                except Exception as e:
                    logger.debug(f"Error testing file upload on {endpoint}: {e}")
        
        self.test_results['total_tests'] += len(upload_endpoints) * len(malicious_files)
    
    async def test_security_headers(self):
        """Test security headers"""
        logger.info("Testing security headers...")
        
        required_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=',
            'Content-Security-Policy': 'default-src',
        }
        
        try:
            async with self.session.get(self.base_url) as response:
                headers = response.headers
                
                for header_name, expected_value in required_headers.items():
                    if header_name not in headers:
                        self.add_finding(SecurityFinding(
                            title=f"Missing Security Header: {header_name}",
                            level=VulnerabilityLevel.MEDIUM,
                            description=f"Security header {header_name} is missing",
                            endpoint="/",
                            recommendation=f"Add {header_name} header to all responses"
                        ))
                    elif isinstance(expected_value, list):
                        if not any(val in headers[header_name] for val in expected_value):
                            self.add_finding(SecurityFinding(
                                title=f"Incorrect Security Header: {header_name}",
                                level=VulnerabilityLevel.MEDIUM,
                                description=f"Security header {header_name} has incorrect value",
                                endpoint="/",
                                recommendation=f"Set {header_name} to appropriate value"
                            ))
                    elif expected_value not in headers.get(header_name, ''):
                        self.add_finding(SecurityFinding(
                            title=f"Incorrect Security Header: {header_name}",
                            level=VulnerabilityLevel.MEDIUM,
                            description=f"Security header {header_name} has incorrect value",
                            endpoint="/",
                            recommendation=f"Set {header_name} to include '{expected_value}'"
                        ))
        
        except Exception as e:
            logger.debug(f"Error testing security headers: {e}")
        
        self.test_results['total_tests'] += len(required_headers)
    
    async def test_ssl_configuration(self):
        """Test SSL/TLS configuration"""
        logger.info("Testing SSL/TLS configuration...")
        
        if not self.base_url.startswith('https://'):
            self.add_finding(SecurityFinding(
                title="HTTP Used Instead of HTTPS",
                level=VulnerabilityLevel.HIGH,
                description="Application is not using HTTPS",
                endpoint="/",
                recommendation="Enable HTTPS with proper SSL/TLS configuration",
                cve_reference="CWE-319"
            ))
        
        self.test_results['total_tests'] += 1
    
    async def run_all_tests(self):
        """Run all security tests"""
        logger.info("Starting comprehensive security penetration testing...")
        
        test_methods = [
            self.test_sql_injection,
            self.test_xss_vulnerabilities,
            self.test_authentication_bypass,
            self.test_csrf_protection,
            self.test_rate_limiting,
            self.test_information_disclosure,
            self.test_file_upload_vulnerabilities,
            self.test_security_headers,
            self.test_ssl_configuration,
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
                self.test_results['passed_tests'] += 1
            except Exception as e:
                logger.error(f"Error in {test_method.__name__}: {e}")
                self.test_results['failed_tests'] += 1
        
        logger.info("Security penetration testing completed")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate security test report"""
        # Sort findings by severity
        critical_findings = [f for f in self.findings if f.level == VulnerabilityLevel.CRITICAL]
        high_findings = [f for f in self.findings if f.level == VulnerabilityLevel.HIGH]
        medium_findings = [f for f in self.findings if f.level == VulnerabilityLevel.MEDIUM]
        low_findings = [f for f in self.findings if f.level == VulnerabilityLevel.LOW]
        
        report = {
            'summary': {
                'total_tests': self.test_results['total_tests'],
                'total_findings': len(self.findings),
                'critical_findings': len(critical_findings),
                'high_findings': len(high_findings),
                'medium_findings': len(medium_findings),
                'low_findings': len(low_findings),
                'security_score': self.calculate_security_score(),
                'test_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'findings': {
                'critical': [self.finding_to_dict(f) for f in critical_findings],
                'high': [self.finding_to_dict(f) for f in high_findings],
                'medium': [self.finding_to_dict(f) for f in medium_findings],
                'low': [self.finding_to_dict(f) for f in low_findings]
            },
            'recommendations': self.generate_recommendations()
        }
        
        return report
    
    def finding_to_dict(self, finding: SecurityFinding) -> Dict[str, Any]:
        """Convert finding to dictionary"""
        return {
            'title': finding.title,
            'level': finding.level.value,
            'description': finding.description,
            'endpoint': finding.endpoint,
            'payload': finding.payload,
            'recommendation': finding.recommendation,
            'cve_reference': finding.cve_reference
        }
    
    def calculate_security_score(self) -> int:
        """Calculate security score (0-100)"""
        if not self.findings:
            return 100
        
        # Weighted scoring
        critical_weight = 25
        high_weight = 10
        medium_weight = 5
        low_weight = 1
        
        total_penalty = (
            self.test_results['critical_findings'] * critical_weight +
            self.test_results['high_findings'] * high_weight +
            self.test_results['medium_findings'] * medium_weight +
            self.test_results['low_findings'] * low_weight
        )
        
        # Maximum possible penalty (assuming all tests find critical issues)
        max_penalty = self.test_results['total_tests'] * critical_weight
        
        if max_penalty == 0:
            return 100
        
        score = max(0, 100 - (total_penalty * 100 // max_penalty))
        return score
    
    def generate_recommendations(self) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        if self.test_results['critical_findings'] > 0:
            recommendations.append("CRITICAL: Address all critical vulnerabilities immediately")
        
        if self.test_results['high_findings'] > 0:
            recommendations.append("HIGH: Fix high-severity vulnerabilities within 24 hours")
        
        # Specific recommendations based on findings
        finding_types = [f.title for f in self.findings]
        
        if any('SQL Injection' in title for title in finding_types):
            recommendations.append("Implement parameterized queries and input validation")
        
        if any('XSS' in title for title in finding_types):
            recommendations.append("Implement proper output encoding and Content Security Policy")
        
        if any('Authentication' in title for title in finding_types):
            recommendations.append("Strengthen authentication and authorization mechanisms")
        
        if any('CSRF' in title for title in finding_types):
            recommendations.append("Implement CSRF protection for all state-changing operations")
        
        if any('Rate Limiting' in title for title in finding_types):
            recommendations.append("Implement rate limiting to prevent abuse")
        
        if any('Security Header' in title for title in finding_types):
            recommendations.append("Configure all required security headers")
        
        if any('HTTPS' in title for title in finding_types):
            recommendations.append("Enable HTTPS with proper SSL/TLS configuration")
        
        return recommendations

async def main():
    """Main function to run security tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Lawsker Security Penetration Testing')
    parser.add_argument('--url', default='http://localhost:8000', help='Base URL to test')
    parser.add_argument('--output', default='security_report.json', help='Output report file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    async with SecurityPenetrationTester(args.url) as tester:
        await tester.run_all_tests()
        
        report = tester.generate_report()
        
        # Save report
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("SECURITY PENETRATION TEST REPORT")
        print("="*60)
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Total Findings: {report['summary']['total_findings']}")
        print(f"Critical: {report['summary']['critical_findings']}")
        print(f"High: {report['summary']['high_findings']}")
        print(f"Medium: {report['summary']['medium_findings']}")
        print(f"Low: {report['summary']['low_findings']}")
        print(f"Security Score: {report['summary']['security_score']}/100")
        print("="*60)
        
        # Print critical and high findings
        if report['findings']['critical']:
            print("\nCRITICAL FINDINGS:")
            for finding in report['findings']['critical']:
                print(f"- {finding['title']}: {finding['description']}")
        
        if report['findings']['high']:
            print("\nHIGH FINDINGS:")
            for finding in report['findings']['high']:
                print(f"- {finding['title']}: {finding['description']}")
        
        # Print recommendations
        if report['recommendations']:
            print("\nRECOMMENDATIONS:")
            for rec in report['recommendations']:
                print(f"- {rec}")
        
        print(f"\nDetailed report saved to: {args.output}")
        
        # Exit with error code if critical or high vulnerabilities found
        if report['summary']['critical_findings'] > 0 or report['summary']['high_findings'] > 0:
            print("\n❌ SECURITY TEST FAILED: Critical or high-risk vulnerabilities found!")
            sys.exit(1)
        else:
            print("\n✅ SECURITY TEST PASSED: No high-risk vulnerabilities found!")
            sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())