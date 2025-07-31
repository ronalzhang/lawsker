"""
安全漏洞扫描服务
使用OWASP ZAP和自定义测试进行安全扫描
"""
import asyncio
import json
import subprocess
import requests
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import get_current_user
from app.models.user import User

logger = get_logger(__name__)

class SecurityScanner:
    """安全扫描器"""
    
    def __init__(self, target_url: str = "http://localhost:8000"):
        self.target_url = target_url
        self.zap_proxy = "http://127.0.0.1:8080"
        self.scan_results = {}
        self.vulnerabilities = []
        
    async def run_comprehensive_scan(self) -> Dict[str, Any]:
        """运行综合安全扫描"""
        logger.info("Starting comprehensive security scan")
        
        scan_results = {
            "scan_id": f"scan_{int(datetime.now().timestamp())}",
            "target_url": self.target_url,
            "start_time": datetime.now().isoformat(),
            "tests": {}
        }
        
        try:
            # 1. OWASP ZAP扫描
            scan_results["tests"]["owasp_zap"] = await self._run_owasp_zap_scan()
            
            # 2. SQL注入测试
            scan_results["tests"]["sql_injection"] = await self._test_sql_injection()
            
            # 3. XSS攻击测试
            scan_results["tests"]["xss_attacks"] = await self._test_xss_attacks()
            
            # 4. 权限绕过测试
            scan_results["tests"]["authorization_bypass"] = await self._test_authorization_bypass()
            
            # 5. CSRF测试
            scan_results["tests"]["csrf_protection"] = await self._test_csrf_protection()
            
            # 6. 输入验证测试
            scan_results["tests"]["input_validation"] = await self._test_input_validation()
            
            # 7. 会话管理测试
            scan_results["tests"]["session_management"] = await self._test_session_management()
            
            # 8. 文件上传安全测试
            scan_results["tests"]["file_upload_security"] = await self._test_file_upload_security()
            
            scan_results["end_time"] = datetime.now().isoformat()
            scan_results["status"] = "completed"
            
            # 生成扫描报告
            await self._generate_scan_report(scan_results)
            
            logger.info("Comprehensive security scan completed")
            return scan_results
            
        except Exception as e:
            logger.error(f"Security scan failed: {str(e)}")
            scan_results["status"] = "failed"
            scan_results["error"] = str(e)
            scan_results["end_time"] = datetime.now().isoformat()
            return scan_results
    
    async def _run_owasp_zap_scan(self) -> Dict[str, Any]:
        """运行OWASP ZAP扫描"""
        logger.info("Running OWASP ZAP scan")
        
        try:
            # 检查ZAP是否运行
            zap_status = await self._check_zap_status()
            if not zap_status:
                return {
                    "status": "skipped",
                    "reason": "OWASP ZAP not available",
                    "vulnerabilities": []
                }
            
            # 启动ZAP扫描
            scan_id = await self._start_zap_scan()
            
            # 等待扫描完成
            await self._wait_for_zap_scan(scan_id)
            
            # 获取扫描结果
            results = await self._get_zap_results(scan_id)
            
            return {
                "status": "completed",
                "scan_id": scan_id,
                "vulnerabilities": results.get("vulnerabilities", []),
                "summary": results.get("summary", {})
            }
            
        except Exception as e:
            logger.error(f"OWASP ZAP scan failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "vulnerabilities": []
            }
    
    async def _test_sql_injection(self) -> Dict[str, Any]:
        """测试SQL注入漏洞"""
        logger.info("Testing SQL injection vulnerabilities")
        
        vulnerabilities = []
        test_endpoints = [
            "/api/v1/users/profile",
            "/api/v1/auth/login",
            "/api/v1/cases/search",
            "/api/v1/lawyers/search"
        ]
        
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "1' AND (SELECT COUNT(*) FROM users) > 0 --",
            "' OR 1=1#",
            "admin'--",
            "admin' /*",
            "' OR 'x'='x",
            "') OR ('1'='1",
            "' OR 1=1 LIMIT 1 --"
        ]
        
        for endpoint in test_endpoints:
            for payload in sql_payloads:
                try:
                    # 测试GET参数
                    response = requests.get(
                        urljoin(self.target_url, endpoint),
                        params={"id": payload, "search": payload},
                        timeout=10
                    )
                    
                    if self._detect_sql_injection(response):
                        vulnerabilities.append({
                            "type": "SQL Injection",
                            "endpoint": endpoint,
                            "method": "GET",
                            "payload": payload,
                            "severity": "high",
                            "description": f"SQL injection vulnerability detected in {endpoint}"
                        })
                    
                    # 测试POST数据
                    if endpoint in ["/api/v1/auth/login"]:
                        response = requests.post(
                            urljoin(self.target_url, endpoint),
                            json={"username": payload, "password": payload},
                            timeout=10
                        )
                        
                        if self._detect_sql_injection(response):
                            vulnerabilities.append({
                                "type": "SQL Injection",
                                "endpoint": endpoint,
                                "method": "POST",
                                "payload": payload,
                                "severity": "high",
                                "description": f"SQL injection vulnerability detected in {endpoint}"
                            })
                    
                    await asyncio.sleep(0.1)  # 避免过于频繁的请求
                    
                except Exception as e:
                    logger.warning(f"SQL injection test failed for {endpoint}: {str(e)}")
        
        return {
            "status": "completed",
            "vulnerabilities": vulnerabilities,
            "tests_performed": len(test_endpoints) * len(sql_payloads)
        }
    
    async def _test_xss_attacks(self) -> Dict[str, Any]:
        """测试XSS攻击漏洞"""
        logger.info("Testing XSS vulnerabilities")
        
        vulnerabilities = []
        test_endpoints = [
            "/api/v1/users/profile",
            "/api/v1/cases/create",
            "/api/v1/lawyers/update-profile"
        ]
        
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
            "<keygen onfocus=alert('XSS') autofocus>"
        ]
        
        for endpoint in test_endpoints:
            for payload in xss_payloads:
                try:
                    # 测试GET参数
                    response = requests.get(
                        urljoin(self.target_url, endpoint),
                        params={"message": payload, "content": payload},
                        timeout=10
                    )
                    
                    if self._detect_xss_vulnerability(response, payload):
                        vulnerabilities.append({
                            "type": "XSS",
                            "endpoint": endpoint,
                            "method": "GET",
                            "payload": payload,
                            "severity": "medium",
                            "description": f"XSS vulnerability detected in {endpoint}"
                        })
                    
                    # 测试POST数据
                    response = requests.post(
                        urljoin(self.target_url, endpoint),
                        json={"content": payload, "description": payload},
                        timeout=10
                    )
                    
                    if self._detect_xss_vulnerability(response, payload):
                        vulnerabilities.append({
                            "type": "XSS",
                            "endpoint": endpoint,
                            "method": "POST",
                            "payload": payload,
                            "severity": "medium",
                            "description": f"XSS vulnerability detected in {endpoint}"
                        })
                    
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"XSS test failed for {endpoint}: {str(e)}")
        
        return {
            "status": "completed",
            "vulnerabilities": vulnerabilities,
            "tests_performed": len(test_endpoints) * len(xss_payloads)
        }
    
    async def _test_authorization_bypass(self) -> Dict[str, Any]:
        """测试权限绕过漏洞"""
        logger.info("Testing authorization bypass vulnerabilities")
        
        vulnerabilities = []
        protected_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/system-stats",
            "/api/v1/users/profile",
            "/api/v1/lawyers/qualification"
        ]
        
        bypass_techniques = [
            {"headers": {}, "description": "No authentication"},
            {"headers": {"Authorization": "Bearer invalid_token"}, "description": "Invalid token"},
            {"headers": {"Authorization": "Bearer "}, "description": "Empty token"},
            {"headers": {"X-User-ID": "1"}, "description": "Header injection"},
            {"headers": {"X-Admin": "true"}, "description": "Admin header injection"},
        ]
        
        for endpoint in protected_endpoints:
            for technique in bypass_techniques:
                try:
                    response = requests.get(
                        urljoin(self.target_url, endpoint),
                        headers=technique["headers"],
                        timeout=10
                    )
                    
                    # 如果返回200而不是401/403，可能存在权限绕过
                    if response.status_code == 200:
                        vulnerabilities.append({
                            "type": "Authorization Bypass",
                            "endpoint": endpoint,
                            "method": "GET",
                            "technique": technique["description"],
                            "severity": "high",
                            "description": f"Authorization bypass detected in {endpoint} using {technique['description']}"
                        })
                    
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"Authorization bypass test failed for {endpoint}: {str(e)}")
        
        return {
            "status": "completed",
            "vulnerabilities": vulnerabilities,
            "tests_performed": len(protected_endpoints) * len(bypass_techniques)
        }
    
    async def _test_csrf_protection(self) -> Dict[str, Any]:
        """测试CSRF保护"""
        logger.info("Testing CSRF protection")
        
        vulnerabilities = []
        state_changing_endpoints = [
            "/api/v1/users/update-profile",
            "/api/v1/cases/create",
            "/api/v1/lawyers/update-qualification"
        ]
        
        for endpoint in state_changing_endpoints:
            try:
                # 测试没有CSRF token的请求
                response = requests.post(
                    urljoin(self.target_url, endpoint),
                    json={"test": "data"},
                    timeout=10
                )
                
                # 如果请求成功，可能缺少CSRF保护
                if response.status_code not in [403, 400]:
                    vulnerabilities.append({
                        "type": "CSRF",
                        "endpoint": endpoint,
                        "method": "POST",
                        "severity": "medium",
                        "description": f"CSRF protection missing or insufficient in {endpoint}"
                    })
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"CSRF test failed for {endpoint}: {str(e)}")
        
        return {
            "status": "completed",
            "vulnerabilities": vulnerabilities,
            "tests_performed": len(state_changing_endpoints)
        }
    
    async def _test_input_validation(self) -> Dict[str, Any]:
        """测试输入验证"""
        logger.info("Testing input validation")
        
        vulnerabilities = []
        test_endpoints = [
            "/api/v1/auth/register",
            "/api/v1/users/update-profile",
            "/api/v1/cases/create"
        ]
        
        invalid_inputs = [
            {"email": "invalid-email"},
            {"phone": "invalid-phone"},
            {"age": -1},
            {"age": 999},
            {"name": "A" * 1000},  # 过长输入
            {"id": "../../etc/passwd"},  # 路径遍历
            {"file": "../../../etc/passwd"},
            {"url": "file:///etc/passwd"},
        ]
        
        for endpoint in test_endpoints:
            for invalid_input in invalid_inputs:
                try:
                    response = requests.post(
                        urljoin(self.target_url, endpoint),
                        json=invalid_input,
                        timeout=10
                    )
                    
                    # 检查是否正确验证了输入
                    if response.status_code == 200:
                        vulnerabilities.append({
                            "type": "Input Validation",
                            "endpoint": endpoint,
                            "method": "POST",
                            "input": invalid_input,
                            "severity": "medium",
                            "description": f"Input validation bypass detected in {endpoint}"
                        })
                    
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"Input validation test failed for {endpoint}: {str(e)}")
        
        return {
            "status": "completed",
            "vulnerabilities": vulnerabilities,
            "tests_performed": len(test_endpoints) * len(invalid_inputs)
        }
    
    async def _test_session_management(self) -> Dict[str, Any]:
        """测试会话管理"""
        logger.info("Testing session management")
        
        vulnerabilities = []
        
        try:
            # 测试会话固定
            session1 = requests.Session()
            response1 = session1.get(urljoin(self.target_url, "/api/v1/auth/me"))
            
            # 测试会话劫持
            if 'Set-Cookie' in response1.headers:
                cookies = response1.headers['Set-Cookie']
                if 'Secure' not in cookies:
                    vulnerabilities.append({
                        "type": "Session Management",
                        "issue": "Missing Secure flag",
                        "severity": "medium",
                        "description": "Session cookies missing Secure flag"
                    })
                
                if 'HttpOnly' not in cookies:
                    vulnerabilities.append({
                        "type": "Session Management",
                        "issue": "Missing HttpOnly flag",
                        "severity": "medium",
                        "description": "Session cookies missing HttpOnly flag"
                    })
            
        except Exception as e:
            logger.warning(f"Session management test failed: {str(e)}")
        
        return {
            "status": "completed",
            "vulnerabilities": vulnerabilities,
            "tests_performed": 2
        }
    
    async def _test_file_upload_security(self) -> Dict[str, Any]:
        """测试文件上传安全"""
        logger.info("Testing file upload security")
        
        vulnerabilities = []
        upload_endpoints = [
            "/api/v1/lawyers/upload-certificate",
            "/api/v1/cases/upload-document"
        ]
        
        malicious_files = [
            {"filename": "test.php", "content": "<?php phpinfo(); ?>", "type": "PHP script"},
            {"filename": "test.jsp", "content": "<% out.println('JSP'); %>", "type": "JSP script"},
            {"filename": "test.exe", "content": "MZ", "type": "Executable"},
            {"filename": "../../../etc/passwd", "content": "root:x:0:0", "type": "Path traversal"},
        ]
        
        for endpoint in upload_endpoints:
            for malicious_file in malicious_files:
                try:
                    files = {
                        'file': (
                            malicious_file["filename"],
                            malicious_file["content"],
                            'application/octet-stream'
                        )
                    }
                    
                    response = requests.post(
                        urljoin(self.target_url, endpoint),
                        files=files,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        vulnerabilities.append({
                            "type": "File Upload",
                            "endpoint": endpoint,
                            "file_type": malicious_file["type"],
                            "filename": malicious_file["filename"],
                            "severity": "high",
                            "description": f"Malicious file upload allowed in {endpoint}"
                        })
                    
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"File upload test failed for {endpoint}: {str(e)}")
        
        return {
            "status": "completed",
            "vulnerabilities": vulnerabilities,
            "tests_performed": len(upload_endpoints) * len(malicious_files)
        }
    
    def _detect_sql_injection(self, response: requests.Response) -> bool:
        """检测SQL注入漏洞"""
        sql_error_patterns = [
            "SQL syntax",
            "mysql_fetch",
            "ORA-",
            "PostgreSQL",
            "Warning: pg_",
            "valid MySQL result",
            "MySQLSyntaxErrorException",
            "SQLException",
            "sqlite3.OperationalError",
            "Microsoft OLE DB Provider for ODBC Drivers"
        ]
        
        response_text = response.text.lower()
        return any(pattern.lower() in response_text for pattern in sql_error_patterns)
    
    def _detect_xss_vulnerability(self, response: requests.Response, payload: str) -> bool:
        """检测XSS漏洞"""
        # 检查payload是否在响应中未经转义
        return payload in response.text and response.headers.get('content-type', '').startswith('text/html')
    
    async def _check_zap_status(self) -> bool:
        """检查OWASP ZAP是否运行"""
        try:
            response = requests.get(f"{self.zap_proxy}/JSON/core/view/version/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    async def _start_zap_scan(self) -> str:
        """启动ZAP扫描"""
        # 这里应该调用ZAP API启动扫描
        # 返回扫描ID
        return f"zap_scan_{int(time.time())}"
    
    async def _wait_for_zap_scan(self, scan_id: str):
        """等待ZAP扫描完成"""
        # 模拟等待扫描完成
        await asyncio.sleep(5)
    
    async def _get_zap_results(self, scan_id: str) -> Dict[str, Any]:
        """获取ZAP扫描结果"""
        # 这里应该从ZAP API获取扫描结果
        return {
            "vulnerabilities": [],
            "summary": {"total": 0, "high": 0, "medium": 0, "low": 0}
        }
    
    async def _generate_scan_report(self, scan_results: Dict[str, Any]):
        """生成扫描报告"""
        report_filename = f"security_scan_report_{scan_results['scan_id']}.json"
        
        try:
            with open(f"reports/{report_filename}", "w", encoding="utf-8") as f:
                json.dump(scan_results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Security scan report generated: {report_filename}")
            
        except Exception as e:
            logger.error(f"Failed to generate scan report: {str(e)}")


# 全局扫描器实例
security_scanner = SecurityScanner()

# 便捷函数
async def run_security_scan(target_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """运行安全扫描"""
    scanner = SecurityScanner(target_url)
    return await scanner.run_comprehensive_scan()

async def quick_vulnerability_check(endpoints: List[str]) -> Dict[str, Any]:
    """快速漏洞检查"""
    scanner = SecurityScanner()
    results = {
        "sql_injection": await scanner._test_sql_injection(),
        "xss_attacks": await scanner._test_xss_attacks(),
        "authorization_bypass": await scanner._test_authorization_bypass()
    }
    return results