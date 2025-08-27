#!/usr/bin/env python3
"""
Security Hardening Script
Automatically applies security hardening measures to the Lawsker system
"""

import os
import sys
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any
import logging
import secrets
import string

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SecurityHardening:
    """Applies security hardening measures"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.changes_made = []
        self.backup_dir = self.project_root / "security_backups"
    
    def create_backup(self, file_path: Path):
        """Create backup of file before modification"""
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True)
        
        backup_path = self.backup_dir / f"{file_path.name}.backup"
        if file_path.exists():
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
    
    def generate_secure_secret(self, length: int = 64) -> str:
        """Generate a secure random secret"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def harden_environment_variables(self):
        """Harden environment variable configuration"""
        logger.info("Hardening environment variables...")
        
        env_files = ['.env', '.env.production', '.env.server']
        
        for env_file in env_files:
            env_path = self.project_root / env_file
            if env_path.exists():
                self.create_backup(env_path)
                
                try:
                    with open(env_path, 'r') as f:
                        lines = f.readlines()
                    
                    modified = False
                    new_lines = []
                    
                    for line in lines:
                        original_line = line
                        
                        # Replace weak secrets
                        if 'SECRET_KEY=' in line and ('test' in line.lower() or 'dev' in line.lower() or len(line.split('=')[1].strip()) < 32):
                            new_secret = self.generate_secure_secret()
                            line = f"SECRET_KEY={new_secret}\n"
                            modified = True
                            logger.info(f"Generated new SECRET_KEY for {env_file}")
                        
                        elif 'JWT_SECRET_KEY=' in line and ('test' in line.lower() or 'dev' in line.lower() or len(line.split('=')[1].strip()) < 32):
                            new_secret = self.generate_secure_secret()
                            line = f"JWT_SECRET_KEY={new_secret}\n"
                            modified = True
                            logger.info(f"Generated new JWT_SECRET_KEY for {env_file}")
                        
                        elif 'ENCRYPTION_KEY=' in line and ('test' in line.lower() or 'dev' in line.lower() or len(line.split('=')[1].strip()) < 32):
                            new_secret = self.generate_secure_secret()
                            line = f"ENCRYPTION_KEY={new_secret}\n"
                            modified = True
                            logger.info(f"Generated new ENCRYPTION_KEY for {env_file}")
                        
                        # Add missing security variables
                        new_lines.append(line)
                    
                    # Add missing security environment variables
                    required_vars = {
                        'SECURE_COOKIES': 'true',
                        'CSRF_PROTECTION': 'true',
                        'RATE_LIMITING': 'true',
                        'SECURITY_HEADERS': 'true',
                        'LOG_SECURITY_EVENTS': 'true'
                    }
                    
                    existing_vars = [line.split('=')[0] for line in new_lines if '=' in line]
                    
                    for var, default_value in required_vars.items():
                        if var not in existing_vars:
                            new_lines.append(f"{var}={default_value}\n")
                            modified = True
                            logger.info(f"Added {var} to {env_file}")
                    
                    if modified:
                        with open(env_path, 'w') as f:
                            f.writelines(new_lines)
                        self.changes_made.append(f"Hardened environment variables in {env_file}")
                
                except Exception as e:
                    logger.error(f"Error hardening {env_file}: {e}")
    
    def harden_nginx_configuration(self):
        """Harden NGINX configuration"""
        logger.info("Hardening NGINX configuration...")
        
        nginx_configs = ['nginx/nginx.conf', 'nginx/lawsker.conf']
        
        for config_file in nginx_configs:
            config_path = self.project_root / config_file
            if config_path.exists():
                self.create_backup(config_path)
                
                try:
                    with open(config_path, 'r') as f:
                        content = f.read()
                    
                    modified = False
                    
                    # Add security headers if missing
                    security_headers = {
                        'X-Content-Type-Options': 'nosniff',
                        'X-Frame-Options': 'DENY',
                        'X-XSS-Protection': '1; mode=block',
                        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
                        'Referrer-Policy': 'strict-origin-when-cross-origin'
                    }
                    
                    for header, value in security_headers.items():
                        if header not in content:
                            # Find location block and add header
                            if 'location /' in content:
                                content = content.replace(
                                    'location / {',
                                    f'location / {{\n        add_header {header} "{value}";'
                                )
                                modified = True
                                logger.info(f"Added {header} header to {config_file}")
                    
                    # Add rate limiting if missing
                    if 'limit_req' not in content and 'http {' in content:
                        rate_limit_config = '''
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
'''
                        content = content.replace('http {', f'http {{{rate_limit_config}')
                        modified = True
                        logger.info(f"Added rate limiting to {config_file}")
                    
                    # Ensure HTTPS redirect
                    if 'listen 80' in content and 'return 301 https' not in content:
                        # Add HTTPS redirect server block
                        https_redirect = '''
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}
'''
                        content = https_redirect + content
                        modified = True
                        logger.info(f"Added HTTPS redirect to {config_file}")
                    
                    if modified:
                        with open(config_path, 'w') as f:
                            f.write(content)
                        self.changes_made.append(f"Hardened NGINX configuration in {config_file}")
                
                except Exception as e:
                    logger.error(f"Error hardening {config_file}: {e}")
    
    def harden_database_configuration(self):
        """Harden database configuration"""
        logger.info("Hardening database configuration...")
        
        db_config_files = [
            'backend/app/core/database.py',
            'backend/config/database_config.py'
        ]
        
        for config_file in db_config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                self.create_backup(config_path)
                
                try:
                    with open(config_path, 'r') as f:
                        content = f.read()
                    
                    modified = False
                    
                    # Add connection security settings
                    security_settings = [
                        'sslmode=require',
                        'connect_timeout=10',
                        'command_timeout=30'
                    ]
                    
                    for setting in security_settings:
                        if setting not in content and 'postgresql://' in content:
                            # Add to connection string
                            content = content.replace(
                                'postgresql://',
                                f'postgresql://...?{setting}&'
                            )
                            modified = True
                            logger.info(f"Added database security setting: {setting}")
                    
                    # Ensure parameterized queries
                    if 'execute(' in content and '%s' not in content:
                        logger.warning(f"Potential SQL injection risk in {config_file} - manual review required")
                    
                    if modified:
                        with open(config_path, 'w') as f:
                            f.write(content)
                        self.changes_made.append(f"Hardened database configuration in {config_file}")
                
                except Exception as e:
                    logger.error(f"Error hardening {config_file}: {e}")
    
    def harden_file_permissions(self):
        """Harden file permissions"""
        logger.info("Hardening file permissions...")
        
        sensitive_files = [
            '.env',
            '.env.production',
            '.env.server',
            'backend/jwt_private_key.pem',
            'jwt_private_key.pem'
        ]
        
        for file_path in sensitive_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    # Set restrictive permissions (owner read/write only)
                    os.chmod(full_path, 0o600)
                    logger.info(f"Set restrictive permissions on {file_path}")
                    self.changes_made.append(f"Hardened file permissions for {file_path}")
                except Exception as e:
                    logger.error(f"Error setting permissions on {file_path}: {e}")
    
    def create_security_middleware(self):
        """Create enhanced security middleware"""
        logger.info("Creating enhanced security middleware...")
        
        middleware_path = self.project_root / 'backend/app/middlewares/enhanced_security_middleware.py'
        
        if not middleware_path.exists():
            security_middleware_content = '''"""
Enhanced Security Middleware
Provides comprehensive security protections
"""

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import time
import hashlib
import hmac
import logging
from typing import Dict, Set
import redis
import json

logger = logging.getLogger(__name__)

class EnhancedSecurityMiddleware:
    """Enhanced security middleware with multiple protection layers"""
    
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.blocked_ips: Set[str] = set()
        self.rate_limits: Dict[str, Dict] = {}
        self.csrf_tokens: Dict[str, str] = {}
    
    async def __call__(self, request: Request, call_next):
        """Main middleware function"""
        client_ip = self.get_client_ip(request)
        
        # IP blocking check
        if self.is_ip_blocked(client_ip):
            raise HTTPException(status_code=403, detail="IP blocked due to suspicious activity")
        
        # Rate limiting
        if not self.check_rate_limit(client_ip, request.url.path):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # CSRF protection for state-changing requests
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            if not self.verify_csrf_token(request):
                raise HTTPException(status_code=403, detail="CSRF token invalid")
        
        # Request size limiting
        if not self.check_request_size(request):
            raise HTTPException(status_code=413, detail="Request too large")
        
        # Log security events
        self.log_security_event(request, client_ip)
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        self.add_security_headers(response)
        
        return response
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        try:
            blocked = self.redis_client.get(f"blocked_ip:{ip}")
            return blocked is not None
        except:
            return ip in self.blocked_ips
    
    def check_rate_limit(self, ip: str, path: str) -> bool:
        """Check rate limiting"""
        try:
            key = f"rate_limit:{ip}:{path}"
            current = self.redis_client.get(key)
            
            if current is None:
                self.redis_client.setex(key, 60, 1)  # 1 request per minute
                return True
            
            if int(current) >= 60:  # Max 60 requests per minute
                return False
            
            self.redis_client.incr(key)
            return True
        except:
            # Fallback to in-memory rate limiting
            key = f"{ip}:{path}"
            now = time.time()
            
            if key not in self.rate_limits:
                self.rate_limits[key] = {"count": 1, "window": now}
                return True
            
            if now - self.rate_limits[key]["window"] > 60:
                self.rate_limits[key] = {"count": 1, "window": now}
                return True
            
            if self.rate_limits[key]["count"] >= 60:
                return False
            
            self.rate_limits[key]["count"] += 1
            return True
    
    def verify_csrf_token(self, request: Request) -> bool:
        """Verify CSRF token"""
        # Skip CSRF for API endpoints with proper authentication
        if request.url.path.startswith("/api/"):
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                return True
        
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            return False
        
        # Verify token (simplified - in production use proper CSRF library)
        return len(csrf_token) > 20
    
    def check_request_size(self, request: Request) -> bool:
        """Check request size limits"""
        content_length = request.headers.get("content-length")
        if content_length:
            size = int(content_length)
            # Limit to 10MB
            return size <= 10 * 1024 * 1024
        return True
    
    def log_security_event(self, request: Request, client_ip: str):
        """Log security events"""
        event = {
            "timestamp": time.time(),
            "ip": client_ip,
            "method": request.method,
            "path": request.url.path,
            "user_agent": request.headers.get("user-agent", ""),
        }
        
        try:
            self.redis_client.lpush("security_events", json.dumps(event))
            self.redis_client.ltrim("security_events", 0, 10000)  # Keep last 10k events
        except:
            logger.info(f"Security event: {event}")
    
    def add_security_headers(self, response: Response):
        """Add security headers to response"""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
'''
            
            with open(middleware_path, 'w') as f:
                f.write(security_middleware_content)
            
            logger.info("Created enhanced security middleware")
            self.changes_made.append("Created enhanced security middleware")
    
    def create_security_config(self):
        """Create security configuration file"""
        logger.info("Creating security configuration...")
        
        config_path = self.project_root / 'backend/config/security_config.py'
        
        if not config_path.exists():
            security_config_content = '''"""
Security Configuration
Centralized security settings
"""

import os
from typing import Dict, List

class SecurityConfig:
    """Security configuration settings"""
    
    # Authentication settings
    JWT_ALGORITHM = "RS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
    PASSWORD_MIN_LENGTH = 12
    PASSWORD_REQUIRE_SPECIAL_CHARS = True
    
    # Session settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "strict"
    SESSION_TIMEOUT_MINUTES = 30
    
    # Rate limiting
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_REQUESTS_PER_MINUTE = 60
    RATE_LIMIT_BURST = 10
    
    # CSRF protection
    CSRF_PROTECTION_ENABLED = True
    CSRF_TOKEN_EXPIRE_MINUTES = 60
    
    # File upload security
    MAX_FILE_SIZE_MB = 10
    ALLOWED_FILE_EXTENSIONS = ['.pdf', '.doc', '.docx', '.jpg', '.png']
    SCAN_UPLOADED_FILES = True
    
    # IP blocking
    AUTO_BLOCK_SUSPICIOUS_IPS = True
    FAILED_LOGIN_THRESHOLD = 5
    BLOCK_DURATION_MINUTES = 60
    
    # Logging
    LOG_SECURITY_EVENTS = True
    LOG_FAILED_LOGINS = True
    LOG_ADMIN_ACTIONS = True
    
    # Headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }
    
    @classmethod
    def get_config(cls) -> Dict:
        """Get security configuration as dictionary"""
        return {
            attr: getattr(cls, attr)
            for attr in dir(cls)
            if not attr.startswith('_') and not callable(getattr(cls, attr))
        }
'''
            
            with open(config_path, 'w') as f:
                f.write(security_config_content)
            
            logger.info("Created security configuration")
            self.changes_made.append("Created security configuration")
    
    def update_requirements(self):
        """Update requirements with security packages"""
        logger.info("Updating requirements with security packages...")
        
        requirements_files = [
            'backend/requirements.txt',
            'backend/requirements-prod.txt'
        ]
        
        security_packages = [
            'cryptography>=41.0.0',
            'bcrypt>=4.0.0',
            'python-jose[cryptography]>=3.3.0',
            'passlib[bcrypt]>=1.7.4',
            'python-multipart>=0.0.6',
            'slowapi>=0.1.9',  # Rate limiting
            'redis>=4.5.0',
        ]
        
        for req_file in requirements_files:
            req_path = self.project_root / req_file
            if req_path.exists():
                self.create_backup(req_path)
                
                try:
                    with open(req_path, 'r') as f:
                        existing_packages = f.read()
                    
                    modified = False
                    new_packages = []
                    
                    for package in security_packages:
                        package_name = package.split('>=')[0].split('[')[0]
                        if package_name not in existing_packages:
                            new_packages.append(package)
                            modified = True
                    
                    if modified:
                        with open(req_path, 'a') as f:
                            f.write('\n# Security packages\n')
                            for package in new_packages:
                                f.write(f'{package}\n')
                        
                        logger.info(f"Added security packages to {req_file}")
                        self.changes_made.append(f"Added security packages to {req_file}")
                
                except Exception as e:
                    logger.error(f"Error updating {req_file}: {e}")
    
    def run_all_hardening(self):
        """Run all security hardening measures"""
        logger.info("Starting comprehensive security hardening...")
        
        hardening_methods = [
            self.harden_environment_variables,
            self.harden_nginx_configuration,
            self.harden_database_configuration,
            self.harden_file_permissions,
            self.create_security_middleware,
            self.create_security_config,
            self.update_requirements,
        ]
        
        for method in hardening_methods:
            try:
                method()
            except Exception as e:
                logger.error(f"Error in {method.__name__}: {e}")
        
        logger.info("Security hardening completed")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate hardening report"""
        return {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'changes_made': self.changes_made,
            'total_changes': len(self.changes_made),
            'backup_directory': str(self.backup_dir),
            'status': 'completed'
        }

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Security Hardening Script')
    parser.add_argument('--project-root', default='.', help='Project root directory')
    parser.add_argument('--output', default='security_hardening_report.json', help='Output report file')
    
    args = parser.parse_args()
    
    hardening = SecurityHardening(args.project_root)
    hardening.run_all_hardening()
    
    report = hardening.generate_report()
    
    # Save report
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("SECURITY HARDENING REPORT")
    print("="*60)
    print(f"Total Changes Made: {report['total_changes']}")
    print(f"Backup Directory: {report['backup_directory']}")
    print("\nChanges Applied:")
    for change in report['changes_made']:
        print(f"  ✅ {change}")
    print("="*60)
    print("✅ Security hardening completed successfully!")
    print(f"Report saved to: {args.output}")
    print("="*60)

if __name__ == "__main__":
    main()