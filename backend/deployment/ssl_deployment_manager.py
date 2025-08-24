#!/usr/bin/env python3
"""
SSL Deployment Manager
Integrates all SSL certificate configuration components into a unified system
for complete SSL certificate management and deployment.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

from ssl_configurator import SSLConfigurator, SSLConfig
from nginx_ssl_generator import NginxSSLGenerator, NginxSSLConfig, ApplicationConfig, SSLSecurityConfig
from ssl_renewal_system import SSLRenewalSystem, RenewalConfig, NotificationConfig


@dataclass
class SSLDeploymentConfig:
    """Complete SSL deployment configuration"""
    # Domain and certificate settings
    domains: List[str]
    email: str
    staging: bool = False
    cert_path: str = "/etc/letsencrypt/live"
    
    # Application configurations
    applications: List[ApplicationConfig] = field(default_factory=list)
    
    # Nginx settings
    nginx_path: str = "/etc/nginx"
    sites_available: str = "/etc/nginx/sites-available"
    sites_enabled: str = "/etc/nginx/sites-enabled"
    
    # SSL security settings
    ssl_protocols: List[str] = field(default_factory=lambda: ['TLSv1.2', 'TLSv1.3'])
    ssl_ciphers: str = 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384'
    
    # Renewal settings
    renewal_threshold_days: int = 30
    critical_threshold_days: int = 7
    check_interval_hours: int = 24
    backup_enabled: bool = True
    backup_path: str = "/var/backups/ssl-certificates"
    
    # Notification settings
    email_notifications: bool = False
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    notification_emails: List[str] = field(default_factory=list)
    webhook_url: Optional[str] = None
    slack_webhook: Optional[str] = None


class SSLDeploymentManager:
    """
    Complete SSL Certificate Deployment and Management System
    
    Integrates:
    - Domain resolution checking and certificate acquisition
    - Nginx SSL configuration generation and deployment
    - Automatic certificate renewal and monitoring
    - Notification and alerting system
    """
    
    def __init__(self, config: SSLDeploymentConfig):
        self.config = config
        self.logger = self._setup_logger()
        
        # Initialize component configurations
        self.ssl_config = self._create_ssl_config()
        self.nginx_config = self._create_nginx_config()
        self.renewal_config = self._create_renewal_config()
        self.notification_config = self._create_notification_config()
        
        # Initialize components
        self.ssl_configurator = SSLConfigurator(self.ssl_config)
        self.nginx_generator = NginxSSLGenerator(self.nginx_config)
        self.renewal_system = SSLRenewalSystem(
            self.ssl_config, 
            self.renewal_config, 
            self.notification_config
        )
        
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
    
    def _create_ssl_config(self) -> SSLConfig:
        """Create SSL configurator configuration"""
        return SSLConfig(
            domains=self.config.domains,
            cert_path=self.config.cert_path,
            email=self.config.email,
            staging=self.config.staging
        )
    
    def _create_nginx_config(self) -> NginxSSLConfig:
        """Create Nginx SSL generator configuration"""
        ssl_security = SSLSecurityConfig(
            protocols=self.config.ssl_protocols,
            ciphers=self.config.ssl_ciphers
        )
        
        return NginxSSLConfig(
            cert_path=self.config.cert_path,
            nginx_path=self.config.nginx_path,
            sites_available=self.config.sites_available,
            sites_enabled=self.config.sites_enabled,
            ssl_config=ssl_security,
            applications=self.config.applications
        )
    
    def _create_renewal_config(self) -> RenewalConfig:
        """Create renewal system configuration"""
        return RenewalConfig(
            check_interval_hours=self.config.check_interval_hours,
            renewal_threshold_days=self.config.renewal_threshold_days,
            critical_threshold_days=self.config.critical_threshold_days,
            backup_enabled=self.config.backup_enabled,
            backup_path=self.config.backup_path
        )
    
    def _create_notification_config(self) -> NotificationConfig:
        """Create notification configuration"""
        return NotificationConfig(
            email_enabled=self.config.email_notifications,
            smtp_server=self.config.smtp_server,
            smtp_port=self.config.smtp_port,
            smtp_username=self.config.smtp_username,
            smtp_password=self.config.smtp_password,
            from_email=self.config.smtp_username,
            to_emails=self.config.notification_emails,
            webhook_url=self.config.webhook_url,
            slack_webhook=self.config.slack_webhook
        )
    
    def deploy_complete_ssl_system(self) -> Dict[str, Any]:
        """
        Deploy complete SSL certificate system
        
        Returns:
            Dict containing deployment results and status
        """
        self.logger.info("Starting complete SSL system deployment")
        
        results = {
            'timestamp': self._get_timestamp(),
            'domain_resolution': {},
            'certificate_acquisition': False,
            'nginx_configuration': {},
            'nginx_deployment': False,
            'renewal_system': False,
            'overall_success': False,
            'errors': []
        }
        
        try:
            # Step 1: Check domain resolution
            self.logger.info("Step 1: Checking domain resolution")
            resolution_results = self.ssl_configurator.check_domain_resolution()
            results['domain_resolution'] = resolution_results
            
            failed_domains = [domain for domain, resolved in resolution_results.items() if not resolved]
            if failed_domains:
                error_msg = f"Domain resolution failed for: {failed_domains}"
                results['errors'].append(error_msg)
                self.logger.error(error_msg)
                return results
            
            self.logger.info("Domain resolution successful for all domains")
            
            # Step 2: Acquire SSL certificates
            self.logger.info("Step 2: Acquiring SSL certificates")
            cert_success = self.ssl_configurator.obtain_letsencrypt_certificate()
            results['certificate_acquisition'] = cert_success
            
            if not cert_success:
                error_msg = "SSL certificate acquisition failed"
                results['errors'].append(error_msg)
                self.logger.error(error_msg)
                return results
            
            self.logger.info("SSL certificate acquisition successful")
            
            # Step 3: Generate Nginx configurations
            self.logger.info("Step 3: Generating Nginx SSL configurations")
            config_results = self.nginx_generator.write_configuration_files()
            results['nginx_configuration'] = config_results
            
            failed_configs = [path for path, success in config_results.items() if not success]
            if failed_configs:
                error_msg = f"Nginx configuration generation failed for: {failed_configs}"
                results['errors'].append(error_msg)
                self.logger.error(error_msg)
                return results
            
            self.logger.info("Nginx configuration generation successful")
            
            # Step 4: Deploy Nginx configurations
            self.logger.info("Step 4: Deploying Nginx configurations")
            nginx_success = self.nginx_generator.reload_nginx()
            results['nginx_deployment'] = nginx_success
            
            if not nginx_success:
                error_msg = "Nginx configuration deployment failed"
                results['errors'].append(error_msg)
                self.logger.error(error_msg)
                return results
            
            self.logger.info("Nginx configuration deployment successful")
            
            # Step 5: Start renewal system
            self.logger.info("Step 5: Starting SSL renewal system")
            try:
                self.renewal_system.start_scheduler()
                results['renewal_system'] = True
                self.logger.info("SSL renewal system started successfully")
            except Exception as e:
                error_msg = f"SSL renewal system startup failed: {str(e)}"
                results['errors'].append(error_msg)
                self.logger.error(error_msg)
                # Don't return here as the main deployment is still successful
            
            # Step 6: Verify complete deployment
            self.logger.info("Step 6: Verifying SSL deployment")
            verification_results = self.verify_ssl_deployment()
            results['verification'] = verification_results
            
            # Determine overall success
            results['overall_success'] = (
                cert_success and 
                nginx_success and 
                all(config_results.values()) and
                verification_results.get('ssl_accessible', False)
            )
            
            if results['overall_success']:
                self.logger.info("Complete SSL system deployment successful")
            else:
                self.logger.warning("SSL system deployment completed with issues")
            
            return results
            
        except Exception as e:
            error_msg = f"Unexpected error during SSL deployment: {str(e)}"
            results['errors'].append(error_msg)
            self.logger.error(error_msg)
            return results
    
    def verify_ssl_deployment(self) -> Dict[str, Any]:
        """
        Verify SSL deployment is working correctly
        
        Returns:
            Dict containing verification results
        """
        self.logger.info("Verifying SSL deployment")
        
        verification = {
            'timestamp': self._get_timestamp(),
            'certificate_validity': {},
            'nginx_status': False,
            'ssl_accessible': False,
            'renewal_system_status': False
        }
        
        try:
            # Check certificate validity
            cert_info = self.ssl_configurator.verify_certificates()
            verification['certificate_validity'] = {
                domain: {
                    'valid': info.valid,
                    'days_until_expiry': info.days_until_expiry,
                    'error': info.error
                }
                for domain, info in cert_info.items()
            }
            
            # Check Nginx status
            nginx_valid = self.nginx_generator.validate_configuration()
            verification['nginx_status'] = nginx_valid
            
            # Check if SSL is accessible (basic check)
            all_certs_valid = all(info.valid for info in cert_info.values())
            verification['ssl_accessible'] = nginx_valid and all_certs_valid
            
            # Check renewal system status
            renewal_status = self.renewal_system.get_renewal_status()
            verification['renewal_system_status'] = renewal_status['scheduler_running']
            verification['renewal_details'] = renewal_status
            
            return verification
            
        except Exception as e:
            self.logger.error("Error during SSL deployment verification: %s", str(e))
            verification['error'] = str(e)
            return verification
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get complete SSL system status
        
        Returns:
            Dict containing comprehensive system status
        """
        self.logger.info("Getting SSL system status")
        
        try:
            # Get renewal system status (includes certificate info)
            renewal_status = self.renewal_system.get_renewal_status()
            
            # Get Nginx status
            nginx_valid = self.nginx_generator.validate_configuration()
            
            # Combine all status information
            status = {
                'timestamp': self._get_timestamp(),
                'system_health': {
                    'certificates_valid': renewal_status['renewal_summary']['valid_certificates'],
                    'total_certificates': renewal_status['renewal_summary']['total_domains'],
                    'nginx_configuration_valid': nginx_valid,
                    'renewal_system_running': renewal_status['scheduler_running'],
                    'renewals_needed': renewal_status['renewal_summary']['renewal_needed'],
                    'critical_renewals': renewal_status['renewal_summary']['critical_renewal']
                },
                'certificate_details': renewal_status['domains'],
                'renewal_configuration': renewal_status['configuration'],
                'recent_renewal_history': renewal_status['recent_history'],
                'configuration': {
                    'domains': self.config.domains,
                    'applications': len(self.config.applications),
                    'staging_mode': self.config.staging,
                    'backup_enabled': self.config.backup_enabled,
                    'notifications_enabled': self.config.email_notifications
                }
            }
            
            return status
            
        except Exception as e:
            self.logger.error("Error getting SSL system status: %s", str(e))
            return {
                'timestamp': self._get_timestamp(),
                'error': str(e),
                'system_health': {
                    'status': 'error'
                }
            }
    
    def stop_renewal_system(self) -> bool:
        """
        Stop the SSL renewal system
        
        Returns:
            True if stopped successfully
        """
        try:
            self.renewal_system.stop_scheduler()
            self.logger.info("SSL renewal system stopped")
            return True
        except Exception as e:
            self.logger.error("Error stopping SSL renewal system: %s", str(e))
            return False
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    @classmethod
    def from_config_file(cls, config_file: str) -> 'SSLDeploymentManager':
        """
        Create SSL deployment manager from configuration file
        
        Args:
            config_file: Path to YAML configuration file
            
        Returns:
            SSLDeploymentManager instance
        """
        import yaml
        
        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)
        
        # Parse applications
        applications = []
        for app_data in data.get('applications', []):
            app = ApplicationConfig(**app_data)
            applications.append(app)
        
        # Create deployment config
        config_data = data.copy()
        config_data.pop('applications', None)
        config_data['applications'] = applications
        
        config = SSLDeploymentConfig(**config_data)
        
        return cls(config)


def create_sample_config() -> str:
    """Create a sample configuration file"""
    sample_config = """
# SSL Deployment Configuration
domains:
  - lawsker.com
  - api.lawsker.com
  - admin.lawsker.com

email: admin@lawsker.com
staging: false
cert_path: /etc/letsencrypt/live

applications:
  - name: lawsker-main
    domain: lawsker.com
    upstream_port: 8000
    root_path: /var/www/lawsker
    client_max_body_size: 10M
    
  - name: lawsker-api
    domain: api.lawsker.com
    upstream_port: 8001
    client_max_body_size: 50M
    
  - name: lawsker-admin
    domain: admin.lawsker.com
    upstream_port: 8002
    root_path: /var/www/lawsker-admin
    auth_required: true

# SSL Security Settings
ssl_protocols:
  - TLSv1.2
  - TLSv1.3

# Renewal Settings
renewal_threshold_days: 30
critical_threshold_days: 7
check_interval_hours: 24
backup_enabled: true
backup_path: /var/backups/ssl-certificates

# Notification Settings
email_notifications: true
smtp_server: smtp.gmail.com
smtp_port: 587
smtp_username: notifications@lawsker.com
smtp_password: your-app-password
notification_emails:
  - admin@lawsker.com
  - devops@lawsker.com

# Optional webhook for alerts
# webhook_url: https://your-webhook-url.com/ssl-alerts
# slack_webhook: https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
"""
    
    config_path = "ssl_deployment_config.yaml"
    with open(config_path, 'w') as f:
        f.write(sample_config.strip())
    
    return config_path


def main():
    """Main function for SSL deployment manager"""
    parser = argparse.ArgumentParser(description='SSL Deployment Manager')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--create-sample-config', action='store_true', 
                       help='Create sample configuration file')
    parser.add_argument('--action', choices=['deploy', 'status', 'verify', 'stop'], 
                       default='deploy', help='Action to perform')
    parser.add_argument('--domains', nargs='+', help='Domains (if not using config file)')
    parser.add_argument('--email', help='Email for Let\'s Encrypt')
    parser.add_argument('--staging', action='store_true', help='Use staging environment')
    
    args = parser.parse_args()
    
    try:
        if args.create_sample_config:
            config_path = create_sample_config()
            print(f"Sample configuration created: {config_path}")
            print("Please edit the configuration file and run with --config option")
            return
        
        # Create deployment manager
        if args.config:
            manager = SSLDeploymentManager.from_config_file(args.config)
        else:
            if not args.domains or not args.email:
                print("Error: --domains and --email are required when not using --config")
                sys.exit(1)
            
            # Create simple configuration
            config = SSLDeploymentConfig(
                domains=args.domains,
                email=args.email,
                staging=args.staging
            )
            manager = SSLDeploymentManager(config)
        
        # Execute action
        if args.action == 'deploy':
            print("Starting SSL system deployment...")
            results = manager.deploy_complete_ssl_system()
            print(json.dumps(results, indent=2))
            
            if results['overall_success']:
                print("\n✅ SSL system deployment completed successfully!")
            else:
                print("\n❌ SSL system deployment completed with errors:")
                for error in results['errors']:
                    print(f"  - {error}")
                    
        elif args.action == 'status':
            status = manager.get_system_status()
            print(json.dumps(status, indent=2))
            
        elif args.action == 'verify':
            verification = manager.verify_ssl_deployment()
            print(json.dumps(verification, indent=2))
            
        elif args.action == 'stop':
            success = manager.stop_renewal_system()
            print(f"Renewal system stop: {'SUCCESS' if success else 'FAILED'}")
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()