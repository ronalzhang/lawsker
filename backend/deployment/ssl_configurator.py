#!/usr/bin/env python3
"""
SSL Certificate Configuration System
Handles domain resolution checking, Let's Encrypt certificate management,
and SSL certificate monitoring for the Lawsker deployment system.
"""

import os
import sys
import json
import logging
import subprocess
import socket
import ssl
import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import dns.resolver
import requests
from cryptography import x509
from cryptography.hazmat.backends import default_backend


@dataclass
class SSLConfig:
    """SSL configuration parameters"""
    domains: List[str]
    cert_path: str = "/etc/letsencrypt/live"
    email: str = ""
    staging: bool = False
    key_size: int = 2048
    renewal_days: int = 30


@dataclass
class CertificateInfo:
    """Certificate information structure"""
    domain: str
    valid: bool
    expires_at: Optional[datetime.datetime] = None
    days_until_expiry: Optional[int] = None
    issuer: Optional[str] = None
    error: Optional[str] = None


class SSLConfigurator:
    """
    SSL Certificate Configuration and Management System
    
    Handles:
    - Domain DNS resolution checking
    - Let's Encrypt certificate acquisition via Certbot
    - Certificate file management and permissions
    - Certificate validity monitoring and expiry tracking
    """
    
    def __init__(self, config: SSLConfig):
        self.config = config
        self.logger = self._setup_logger()
        self.certbot_path = self._find_certbot()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
        
    def _find_certbot(self) -> str:
        """Find certbot executable path"""
        for path in ['/usr/bin/certbot', '/usr/local/bin/certbot', 'certbot']:
            if subprocess.run(['which', path], capture_output=True).returncode == 0:
                return path
        raise RuntimeError("Certbot not found. Please install certbot first.")
    
    def check_domain_resolution(self) -> Dict[str, bool]:
        """
        Check DNS resolution status for all configured domains
        
        Returns:
            Dict mapping domain names to their resolution status
        """
        self.logger.info("Checking domain resolution for domains: %s", self.config.domains)
        results = {}
        
        for domain in self.config.domains:
            try:
                # Check A record resolution
                resolver = dns.resolver.Resolver()
                resolver.timeout = 10
                resolver.lifetime = 10
                
                answers = resolver.resolve(domain, 'A')
                if answers:
                    ip_addresses = [str(answer) for answer in answers]
                    self.logger.info("Domain %s resolves to: %s", domain, ip_addresses)
                    
                    # Verify the domain actually points to this server
                    server_ip = self._get_server_public_ip()
                    if server_ip and server_ip in ip_addresses:
                        results[domain] = True
                        self.logger.info("Domain %s correctly points to server IP %s", domain, server_ip)
                    else:
                        results[domain] = False
                        self.logger.warning("Domain %s does not point to server IP %s", domain, server_ip)
                else:
                    results[domain] = False
                    self.logger.error("No A records found for domain %s", domain)
                    
            except dns.resolver.NXDOMAIN:
                results[domain] = False
                self.logger.error("Domain %s does not exist", domain)
            except dns.resolver.Timeout:
                results[domain] = False
                self.logger.error("DNS timeout for domain %s", domain)
            except Exception as e:
                results[domain] = False
                self.logger.error("DNS resolution error for domain %s: %s", domain, str(e))
        
        return results
    
    def _get_server_public_ip(self) -> Optional[str]:
        """Get server's public IP address"""
        try:
            # Try multiple services to get public IP
            services = [
                'https://api.ipify.org',
                'https://checkip.amazonaws.com',
                'https://icanhazip.com'
            ]
            
            for service in services:
                try:
                    response = requests.get(service, timeout=10)
                    if response.status_code == 200:
                        return response.text.strip()
                except:
                    continue
                    
            return None
        except Exception as e:
            self.logger.error("Failed to get server public IP: %s", str(e))
            return None
    
    def obtain_letsencrypt_certificate(self) -> bool:
        """
        Obtain Let's Encrypt certificates using Certbot
        
        Returns:
            True if certificate acquisition was successful
        """
        self.logger.info("Starting Let's Encrypt certificate acquisition")
        
        # Check domain resolution first
        resolution_results = self.check_domain_resolution()
        failed_domains = [domain for domain, resolved in resolution_results.items() if not resolved]
        
        if failed_domains:
            self.logger.error("Cannot proceed with certificate acquisition. Failed domains: %s", failed_domains)
            return False
        
        try:
            # Prepare certbot command
            cmd = [
                self.certbot_path,
                'certonly',
                '--nginx',  # Use nginx plugin
                '--non-interactive',
                '--agree-tos',
            ]
            
            if self.config.email:
                cmd.extend(['--email', self.config.email])
            else:
                cmd.append('--register-unsafely-without-email')
            
            if self.config.staging:
                cmd.append('--staging')
                self.logger.info("Using Let's Encrypt staging environment")
            
            # Add domains
            for domain in self.config.domains:
                cmd.extend(['-d', domain])
            
            # Add key size
            cmd.extend(['--rsa-key-size', str(self.config.key_size)])
            
            self.logger.info("Running certbot command: %s", ' '.join(cmd))
            
            # Execute certbot
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.logger.info("Certificate acquisition successful")
                self.logger.info("Certbot output: %s", result.stdout)
                
                # Set proper permissions on certificate files
                self._set_certificate_permissions()
                
                return True
            else:
                self.logger.error("Certificate acquisition failed")
                self.logger.error("Certbot error: %s", result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Certbot command timed out")
            return False
        except Exception as e:
            self.logger.error("Error during certificate acquisition: %s", str(e))
            return False
    
    def _set_certificate_permissions(self) -> None:
        """Set proper permissions on certificate files"""
        try:
            for domain in self.config.domains:
                cert_dir = Path(self.config.cert_path) / domain
                if cert_dir.exists():
                    # Set directory permissions
                    os.chmod(cert_dir, 0o755)
                    
                    # Set file permissions
                    for cert_file in ['cert.pem', 'chain.pem', 'fullchain.pem']:
                        cert_path = cert_dir / cert_file
                        if cert_path.exists():
                            os.chmod(cert_path, 0o644)
                    
                    # Private key should be more restrictive
                    privkey_path = cert_dir / 'privkey.pem'
                    if privkey_path.exists():
                        os.chmod(privkey_path, 0o600)
                    
                    self.logger.info("Set permissions for certificate files in %s", cert_dir)
                    
        except Exception as e:
            self.logger.error("Error setting certificate permissions: %s", str(e))
    
    def verify_certificates(self) -> Dict[str, CertificateInfo]:
        """
        Verify SSL certificates for all domains
        
        Returns:
            Dict mapping domain names to their certificate information
        """
        self.logger.info("Verifying SSL certificates for domains: %s", self.config.domains)
        results = {}
        
        for domain in self.config.domains:
            cert_info = self._get_certificate_info(domain)
            results[domain] = cert_info
            
            if cert_info.valid:
                self.logger.info(
                    "Certificate for %s is valid, expires in %d days",
                    domain, cert_info.days_until_expiry or 0
                )
            else:
                self.logger.error(
                    "Certificate for %s is invalid: %s",
                    domain, cert_info.error
                )
        
        return results
    
    def _get_certificate_info(self, domain: str) -> CertificateInfo:
        """Get certificate information for a specific domain"""
        try:
            # First try to get certificate from file system
            cert_path = Path(self.config.cert_path) / domain / 'cert.pem'
            if cert_path.exists():
                return self._parse_certificate_file(domain, cert_path)
            
            # If file doesn't exist, try to get from server
            return self._get_certificate_from_server(domain)
            
        except Exception as e:
            return CertificateInfo(
                domain=domain,
                valid=False,
                error=f"Error getting certificate info: {str(e)}"
            )
    
    def _parse_certificate_file(self, domain: str, cert_path: Path) -> CertificateInfo:
        """Parse certificate file and extract information"""
        try:
            with open(cert_path, 'rb') as f:
                cert_data = f.read()
            
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            
            # Extract certificate information
            expires_at = cert.not_valid_after
            now = datetime.datetime.now()
            days_until_expiry = (expires_at - now).days
            
            # Get issuer information
            issuer = cert.issuer.rfc4514_string()
            
            return CertificateInfo(
                domain=domain,
                valid=days_until_expiry > 0,
                expires_at=expires_at,
                days_until_expiry=days_until_expiry,
                issuer=issuer
            )
            
        except Exception as e:
            return CertificateInfo(
                domain=domain,
                valid=False,
                error=f"Error parsing certificate file: {str(e)}"
            )
    
    def _get_certificate_from_server(self, domain: str, port: int = 443) -> CertificateInfo:
        """Get certificate information from server"""
        try:
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect to server and get certificate
            with socket.create_connection((domain, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert_der = ssock.getpeercert_chain()[0]
                    cert = x509.load_der_x509_certificate(cert_der, default_backend())
                    
                    # Extract certificate information
                    expires_at = cert.not_valid_after
                    now = datetime.datetime.now()
                    days_until_expiry = (expires_at - now).days
                    
                    # Get issuer information
                    issuer = cert.issuer.rfc4514_string()
                    
                    return CertificateInfo(
                        domain=domain,
                        valid=days_until_expiry > 0,
                        expires_at=expires_at,
                        days_until_expiry=days_until_expiry,
                        issuer=issuer
                    )
                    
        except Exception as e:
            return CertificateInfo(
                domain=domain,
                valid=False,
                error=f"Error connecting to server: {str(e)}"
            )
    
    def monitor_certificate_expiry(self) -> Dict[str, Any]:
        """
        Monitor certificate expiry and return status report
        
        Returns:
            Dict containing monitoring results and recommendations
        """
        self.logger.info("Monitoring certificate expiry for all domains")
        
        cert_info = self.verify_certificates()
        
        report = {
            'timestamp': datetime.datetime.now().isoformat(),
            'domains': {},
            'alerts': [],
            'recommendations': []
        }
        
        for domain, info in cert_info.items():
            domain_status = {
                'valid': info.valid,
                'expires_at': info.expires_at.isoformat() if info.expires_at else None,
                'days_until_expiry': info.days_until_expiry,
                'issuer': info.issuer,
                'error': info.error
            }
            
            report['domains'][domain] = domain_status
            
            # Generate alerts and recommendations
            if not info.valid:
                report['alerts'].append({
                    'level': 'critical',
                    'domain': domain,
                    'message': f"Certificate for {domain} is invalid: {info.error}"
                })
                report['recommendations'].append(f"Renew certificate for {domain} immediately")
                
            elif info.days_until_expiry is not None:
                if info.days_until_expiry <= 7:
                    report['alerts'].append({
                        'level': 'critical',
                        'domain': domain,
                        'message': f"Certificate for {domain} expires in {info.days_until_expiry} days"
                    })
                    report['recommendations'].append(f"Renew certificate for {domain} immediately")
                    
                elif info.days_until_expiry <= self.config.renewal_days:
                    report['alerts'].append({
                        'level': 'warning',
                        'domain': domain,
                        'message': f"Certificate for {domain} expires in {info.days_until_expiry} days"
                    })
                    report['recommendations'].append(f"Schedule renewal for {domain}")
        
        # Log summary
        total_domains = len(cert_info)
        valid_domains = sum(1 for info in cert_info.values() if info.valid)
        
        self.logger.info(
            "Certificate monitoring complete: %d/%d domains have valid certificates",
            valid_domains, total_domains
        )
        
        if report['alerts']:
            self.logger.warning("Found %d certificate alerts", len(report['alerts']))
        
        return report
    
    def renew_certificates(self) -> bool:
        """
        Renew certificates using certbot
        
        Returns:
            True if renewal was successful
        """
        self.logger.info("Starting certificate renewal")
        
        try:
            cmd = [
                self.certbot_path,
                'renew',
                '--non-interactive',
                '--quiet'
            ]
            
            if self.config.staging:
                cmd.append('--staging')
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.logger.info("Certificate renewal successful")
                self.logger.info("Renewal output: %s", result.stdout)
                
                # Set proper permissions after renewal
                self._set_certificate_permissions()
                
                return True
            else:
                self.logger.error("Certificate renewal failed")
                self.logger.error("Renewal error: %s", result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Certificate renewal timed out")
            return False
        except Exception as e:
            self.logger.error("Error during certificate renewal: %s", str(e))
            return False
    
    def backup_certificates(self, backup_path: str) -> bool:
        """
        Create backup of certificate files
        
        Args:
            backup_path: Path to store certificate backups
            
        Returns:
            True if backup was successful
        """
        self.logger.info("Creating certificate backup to %s", backup_path)
        
        try:
            backup_dir = Path(backup_path)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create timestamped backup directory
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_subdir = backup_dir / f"certificates_{timestamp}"
            backup_subdir.mkdir(exist_ok=True)
            
            # Copy certificate files for each domain
            for domain in self.config.domains:
                domain_cert_dir = Path(self.config.cert_path) / domain
                if domain_cert_dir.exists():
                    domain_backup_dir = backup_subdir / domain
                    domain_backup_dir.mkdir(exist_ok=True)
                    
                    # Copy all certificate files
                    for cert_file in domain_cert_dir.glob('*.pem'):
                        backup_file = domain_backup_dir / cert_file.name
                        backup_file.write_bytes(cert_file.read_bytes())
                    
                    self.logger.info("Backed up certificates for domain %s", domain)
            
            self.logger.info("Certificate backup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error("Error creating certificate backup: %s", str(e))
            return False


def main():
    """Main function for testing SSL configurator"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SSL Certificate Configurator')
    parser.add_argument('--domains', nargs='+', required=True, help='Domains to configure')
    parser.add_argument('--email', help='Email for Let\'s Encrypt registration')
    parser.add_argument('--staging', action='store_true', help='Use staging environment')
    parser.add_argument('--cert-path', default='/etc/letsencrypt/live', help='Certificate path')
    parser.add_argument('--action', choices=['check', 'obtain', 'verify', 'monitor', 'renew'], 
                       default='check', help='Action to perform')
    
    args = parser.parse_args()
    
    # Create SSL configuration
    config = SSLConfig(
        domains=args.domains,
        email=args.email or '',
        staging=args.staging,
        cert_path=args.cert_path
    )
    
    # Create SSL configurator
    configurator = SSLConfigurator(config)
    
    try:
        if args.action == 'check':
            results = configurator.check_domain_resolution()
            print(json.dumps(results, indent=2))
            
        elif args.action == 'obtain':
            success = configurator.obtain_letsencrypt_certificate()
            print(f"Certificate acquisition: {'SUCCESS' if success else 'FAILED'}")
            
        elif args.action == 'verify':
            results = configurator.verify_certificates()
            for domain, info in results.items():
                print(f"{domain}: {'VALID' if info.valid else 'INVALID'}")
                if info.days_until_expiry:
                    print(f"  Expires in {info.days_until_expiry} days")
                if info.error:
                    print(f"  Error: {info.error}")
                    
        elif args.action == 'monitor':
            report = configurator.monitor_certificate_expiry()
            print(json.dumps(report, indent=2))
            
        elif args.action == 'renew':
            success = configurator.renew_certificates()
            print(f"Certificate renewal: {'SUCCESS' if success else 'FAILED'}")
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()