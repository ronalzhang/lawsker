#!/usr/bin/env python3
"""
SSL Certificate Auto-Renewal System
Handles automatic certificate expiry checking, renewal scheduling,
failure alerting, and certificate backup/recovery operations.
"""

import os
import sys
import json
import logging
import subprocess
import datetime
import smtplib
import shutil
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import schedule
import time
import threading
from ssl_configurator import SSLConfigurator, SSLConfig, CertificateInfo


@dataclass
class NotificationConfig:
    """Notification configuration for alerts"""
    email_enabled: bool = False
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    from_email: str = ""
    to_emails: List[str] = field(default_factory=list)
    webhook_url: Optional[str] = None
    slack_webhook: Optional[str] = None


@dataclass
class RenewalConfig:
    """Certificate renewal configuration"""
    check_interval_hours: int = 24
    renewal_threshold_days: int = 30
    critical_threshold_days: int = 7
    max_retry_attempts: int = 3
    retry_delay_hours: int = 6
    backup_enabled: bool = True
    backup_path: str = "/var/backups/ssl-certificates"
    backup_retention_days: int = 90
    post_renewal_commands: List[str] = field(default_factory=lambda: ['systemctl reload nginx'])


@dataclass
class RenewalAttempt:
    """Record of a renewal attempt"""
    domain: str
    timestamp: datetime.datetime
    success: bool
    error_message: Optional[str] = None
    attempt_number: int = 1


class SSLRenewalSystem:
    """
    SSL Certificate Auto-Renewal System
    
    Features:
    - Automatic certificate expiry monitoring
    - Scheduled renewal attempts with retry logic
    - Multiple notification channels for alerts
    - Certificate backup and recovery
    - Post-renewal command execution
    """
    
    def __init__(self, ssl_config: SSLConfig, renewal_config: RenewalConfig, 
                 notification_config: NotificationConfig):
        self.ssl_config = ssl_config
        self.renewal_config = renewal_config
        self.notification_config = notification_config
        self.logger = self._setup_logger()
        self.ssl_configurator = SSLConfigurator(ssl_config)
        self.renewal_history: List[RenewalAttempt] = []
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # File handler
            log_dir = Path('/var/log/ssl-renewal')
            log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_dir / 'ssl-renewal.log')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            logger.setLevel(logging.INFO)
        return logger
    
    def check_certificate_expiry(self) -> Dict[str, CertificateInfo]:
        """
        Check certificate expiry for all domains
        
        Returns:
            Dict mapping domain names to certificate information
        """
        self.logger.info("Checking certificate expiry for all domains")
        return self.ssl_configurator.verify_certificates()
    
    def identify_renewal_candidates(self) -> Tuple[List[str], List[str]]:
        """
        Identify certificates that need renewal
        
        Returns:
            Tuple of (renewal_needed, critical_renewal) domain lists
        """
        cert_info = self.check_certificate_expiry()
        renewal_needed = []
        critical_renewal = []
        
        for domain, info in cert_info.items():
            if not info.valid:
                critical_renewal.append(domain)
                self.logger.warning("Certificate for %s is invalid", domain)
            elif info.days_until_expiry is not None:
                if info.days_until_expiry <= self.renewal_config.critical_threshold_days:
                    critical_renewal.append(domain)
                    self.logger.warning(
                        "Certificate for %s expires in %d days (critical)",
                        domain, info.days_until_expiry
                    )
                elif info.days_until_expiry <= self.renewal_config.renewal_threshold_days:
                    renewal_needed.append(domain)
                    self.logger.info(
                        "Certificate for %s expires in %d days (renewal needed)",
                        domain, info.days_until_expiry
                    )
        
        return renewal_needed, critical_renewal
    
    def backup_certificates(self) -> bool:
        """
        Create backup of all certificates
        
        Returns:
            True if backup was successful
        """
        if not self.renewal_config.backup_enabled:
            return True
            
        self.logger.info("Creating certificate backup")
        
        try:
            backup_path = self.renewal_config.backup_path
            success = self.ssl_configurator.backup_certificates(backup_path)
            
            if success:
                # Clean up old backups
                self._cleanup_old_backups()
                
            return success
            
        except Exception as e:
            self.logger.error("Error creating certificate backup: %s", str(e))
            return False
    
    def _cleanup_old_backups(self) -> None:
        """Clean up old certificate backups"""
        try:
            backup_dir = Path(self.renewal_config.backup_path)
            if not backup_dir.exists():
                return
            
            cutoff_date = datetime.datetime.now() - datetime.timedelta(
                days=self.renewal_config.backup_retention_days
            )
            
            for backup_subdir in backup_dir.iterdir():
                if backup_subdir.is_dir() and backup_subdir.name.startswith('certificates_'):
                    try:
                        # Extract timestamp from directory name
                        timestamp_str = backup_subdir.name.replace('certificates_', '')
                        backup_date = datetime.datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                        
                        if backup_date < cutoff_date:
                            shutil.rmtree(backup_subdir)
                            self.logger.info("Removed old backup: %s", backup_subdir.name)
                            
                    except (ValueError, OSError) as e:
                        self.logger.warning("Error processing backup directory %s: %s", 
                                          backup_subdir.name, str(e))
                        
        except Exception as e:
            self.logger.error("Error cleaning up old backups: %s", str(e))
    
    def renew_certificate(self, domain: str, attempt_number: int = 1) -> bool:
        """
        Renew certificate for a specific domain
        
        Args:
            domain: Domain to renew certificate for
            attempt_number: Current attempt number
            
        Returns:
            True if renewal was successful
        """
        self.logger.info("Attempting to renew certificate for %s (attempt %d)", 
                        domain, attempt_number)
        
        # Create backup before renewal
        if self.renewal_config.backup_enabled:
            self.backup_certificates()
        
        try:
            # Create domain-specific SSL config for renewal
            domain_config = SSLConfig(
                domains=[domain],
                email=self.ssl_config.email,
                staging=self.ssl_config.staging,
                cert_path=self.ssl_config.cert_path
            )
            
            domain_configurator = SSLConfigurator(domain_config)
            success = domain_configurator.renew_certificates()
            
            # Record renewal attempt
            attempt = RenewalAttempt(
                domain=domain,
                timestamp=datetime.datetime.now(),
                success=success,
                attempt_number=attempt_number
            )
            
            if success:
                self.logger.info("Certificate renewal successful for %s", domain)
                
                # Execute post-renewal commands
                self._execute_post_renewal_commands()
                
                # Send success notification
                self._send_notification(
                    subject=f"SSL Certificate Renewed Successfully - {domain}",
                    message=f"Certificate for {domain} has been renewed successfully.",
                    level="info"
                )
                
            else:
                attempt.error_message = "Renewal command failed"
                self.logger.error("Certificate renewal failed for %s", domain)
                
            self.renewal_history.append(attempt)
            return success
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error("Error renewing certificate for %s: %s", domain, error_msg)
            
            # Record failed attempt
            attempt = RenewalAttempt(
                domain=domain,
                timestamp=datetime.datetime.now(),
                success=False,
                error_message=error_msg,
                attempt_number=attempt_number
            )
            self.renewal_history.append(attempt)
            
            return False
    
    def _execute_post_renewal_commands(self) -> None:
        """Execute post-renewal commands"""
        for command in self.renewal_config.post_renewal_commands:
            try:
                self.logger.info("Executing post-renewal command: %s", command)
                result = subprocess.run(
                    command.split(),
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    self.logger.info("Post-renewal command successful: %s", command)
                else:
                    self.logger.error("Post-renewal command failed: %s - %s", 
                                    command, result.stderr)
                    
            except Exception as e:
                self.logger.error("Error executing post-renewal command %s: %s", 
                                command, str(e))
    
    def process_renewals(self) -> Dict[str, bool]:
        """
        Process all pending certificate renewals
        
        Returns:
            Dict mapping domain names to renewal success status
        """
        self.logger.info("Processing certificate renewals")
        
        renewal_needed, critical_renewal = self.identify_renewal_candidates()
        all_domains = list(set(renewal_needed + critical_renewal))
        
        if not all_domains:
            self.logger.info("No certificates need renewal")
            return {}
        
        results = {}
        
        for domain in all_domains:
            is_critical = domain in critical_renewal
            max_attempts = self.renewal_config.max_retry_attempts if not is_critical else 1
            
            success = False
            for attempt in range(1, max_attempts + 1):
                success = self.renew_certificate(domain, attempt)
                
                if success:
                    break
                    
                if attempt < max_attempts:
                    self.logger.info("Renewal failed for %s, retrying in %d hours", 
                                   domain, self.renewal_config.retry_delay_hours)
                    # In a real implementation, you might want to schedule the retry
                    # For now, we'll just log it
                    
            results[domain] = success
            
            # Send failure notification if all attempts failed
            if not success:
                level = "critical" if is_critical else "warning"
                self._send_notification(
                    subject=f"SSL Certificate Renewal Failed - {domain}",
                    message=f"Failed to renew certificate for {domain} after {max_attempts} attempts.",
                    level=level
                )
        
        return results
    
    def _send_notification(self, subject: str, message: str, level: str = "info") -> None:
        """
        Send notification via configured channels
        
        Args:
            subject: Notification subject
            message: Notification message
            level: Notification level (info, warning, critical)
        """
        self.logger.info("Sending %s notification: %s", level, subject)
        
        # Email notification
        if self.notification_config.email_enabled:
            self._send_email_notification(subject, message, level)
        
        # Webhook notification
        if self.notification_config.webhook_url:
            self._send_webhook_notification(subject, message, level)
        
        # Slack notification
        if self.notification_config.slack_webhook:
            self._send_slack_notification(subject, message, level)
    
    def _send_email_notification(self, subject: str, message: str, level: str) -> None:
        """Send email notification"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.notification_config.from_email
            msg['To'] = ', '.join(self.notification_config.to_emails)
            msg['Subject'] = f"[{level.upper()}] {subject}"
            
            # Create detailed message
            detailed_message = f"""
SSL Certificate Renewal System Notification

Level: {level.upper()}
Subject: {subject}
Message: {message}
Timestamp: {datetime.datetime.now().isoformat()}

System Information:
- Domains monitored: {', '.join(self.ssl_config.domains)}
- Renewal threshold: {self.renewal_config.renewal_threshold_days} days
- Critical threshold: {self.renewal_config.critical_threshold_days} days

This is an automated message from the SSL Certificate Renewal System.
"""
            
            msg.attach(MimeText(detailed_message, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.notification_config.smtp_server, 
                            self.notification_config.smtp_port) as server:
                server.starttls()
                server.login(self.notification_config.smtp_username, 
                           self.notification_config.smtp_password)
                server.send_message(msg)
            
            self.logger.info("Email notification sent successfully")
            
        except Exception as e:
            self.logger.error("Error sending email notification: %s", str(e))
    
    def _send_webhook_notification(self, subject: str, message: str, level: str) -> None:
        """Send webhook notification"""
        try:
            import requests
            
            payload = {
                'subject': subject,
                'message': message,
                'level': level,
                'timestamp': datetime.datetime.now().isoformat(),
                'domains': self.ssl_config.domains
            }
            
            response = requests.post(
                self.notification_config.webhook_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info("Webhook notification sent successfully")
            else:
                self.logger.error("Webhook notification failed: %s", response.status_code)
                
        except Exception as e:
            self.logger.error("Error sending webhook notification: %s", str(e))
    
    def _send_slack_notification(self, subject: str, message: str, level: str) -> None:
        """Send Slack notification"""
        try:
            import requests
            
            # Choose emoji based on level
            emoji_map = {
                'info': ':information_source:',
                'warning': ':warning:',
                'critical': ':rotating_light:'
            }
            
            emoji = emoji_map.get(level, ':information_source:')
            
            payload = {
                'text': f"{emoji} SSL Certificate Alert",
                'attachments': [
                    {
                        'color': 'good' if level == 'info' else 'warning' if level == 'warning' else 'danger',
                        'fields': [
                            {
                                'title': 'Subject',
                                'value': subject,
                                'short': False
                            },
                            {
                                'title': 'Message',
                                'value': message,
                                'short': False
                            },
                            {
                                'title': 'Level',
                                'value': level.upper(),
                                'short': True
                            },
                            {
                                'title': 'Domains',
                                'value': ', '.join(self.ssl_config.domains),
                                'short': True
                            }
                        ],
                        'footer': 'SSL Renewal System',
                        'ts': int(datetime.datetime.now().timestamp())
                    }
                ]
            }
            
            response = requests.post(
                self.notification_config.slack_webhook,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info("Slack notification sent successfully")
            else:
                self.logger.error("Slack notification failed: %s", response.status_code)
                
        except Exception as e:
            self.logger.error("Error sending Slack notification: %s", str(e))
    
    def start_scheduler(self) -> None:
        """Start the renewal scheduler"""
        self.logger.info("Starting SSL renewal scheduler")
        
        # Schedule regular certificate checks
        schedule.every(self.renewal_config.check_interval_hours).hours.do(
            self._scheduled_check
        )
        
        # Schedule daily backup (if enabled)
        if self.renewal_config.backup_enabled:
            schedule.every().day.at("02:00").do(self.backup_certificates)
        
        self.running = True
        
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("SSL renewal scheduler started")
    
    def stop_scheduler(self) -> None:
        """Stop the renewal scheduler"""
        self.logger.info("Stopping SSL renewal scheduler")
        self.running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        self.logger.info("SSL renewal scheduler stopped")
    
    def _scheduled_check(self) -> None:
        """Scheduled certificate check and renewal"""
        self.logger.info("Running scheduled certificate check")
        
        try:
            results = self.process_renewals()
            
            if results:
                success_count = sum(1 for success in results.values() if success)
                total_count = len(results)
                
                self.logger.info(
                    "Scheduled renewal completed: %d/%d successful",
                    success_count, total_count
                )
            else:
                self.logger.info("No renewals needed during scheduled check")
                
        except Exception as e:
            self.logger.error("Error during scheduled certificate check: %s", str(e))
            self._send_notification(
                subject="SSL Renewal System Error",
                message=f"Error during scheduled certificate check: {str(e)}",
                level="critical"
            )
    
    def get_renewal_status(self) -> Dict[str, Any]:
        """
        Get current renewal system status
        
        Returns:
            Dict containing system status information
        """
        cert_info = self.check_certificate_expiry()
        renewal_needed, critical_renewal = self.identify_renewal_candidates()
        
        # Get recent renewal history
        recent_history = [
            {
                'domain': attempt.domain,
                'timestamp': attempt.timestamp.isoformat(),
                'success': attempt.success,
                'error_message': attempt.error_message,
                'attempt_number': attempt.attempt_number
            }
            for attempt in self.renewal_history[-10:]  # Last 10 attempts
        ]
        
        status = {
            'timestamp': datetime.datetime.now().isoformat(),
            'scheduler_running': self.running,
            'domains': {
                domain: {
                    'valid': info.valid,
                    'expires_at': info.expires_at.isoformat() if info.expires_at else None,
                    'days_until_expiry': info.days_until_expiry,
                    'needs_renewal': domain in renewal_needed,
                    'critical': domain in critical_renewal,
                    'error': info.error
                }
                for domain, info in cert_info.items()
            },
            'renewal_summary': {
                'total_domains': len(cert_info),
                'valid_certificates': sum(1 for info in cert_info.values() if info.valid),
                'renewal_needed': len(renewal_needed),
                'critical_renewal': len(critical_renewal)
            },
            'configuration': {
                'check_interval_hours': self.renewal_config.check_interval_hours,
                'renewal_threshold_days': self.renewal_config.renewal_threshold_days,
                'critical_threshold_days': self.renewal_config.critical_threshold_days,
                'backup_enabled': self.renewal_config.backup_enabled
            },
            'recent_history': recent_history
        }
        
        return status


def main():
    """Main function for testing SSL renewal system"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SSL Certificate Renewal System')
    parser.add_argument('--domains', nargs='+', required=True, help='Domains to monitor')
    parser.add_argument('--email', help='Email for Let\'s Encrypt registration')
    parser.add_argument('--cert-path', default='/etc/letsencrypt/live', help='Certificate path')
    parser.add_argument('--action', choices=['check', 'renew', 'status', 'start-scheduler'], 
                       default='check', help='Action to perform')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    
    args = parser.parse_args()
    
    # Create configurations
    ssl_config = SSLConfig(
        domains=args.domains,
        email=args.email or '',
        cert_path=args.cert_path
    )
    
    renewal_config = RenewalConfig()
    notification_config = NotificationConfig()
    
    # Create renewal system
    renewal_system = SSLRenewalSystem(ssl_config, renewal_config, notification_config)
    
    try:
        if args.action == 'check':
            renewal_needed, critical_renewal = renewal_system.identify_renewal_candidates()
            print(f"Renewal needed: {renewal_needed}")
            print(f"Critical renewal: {critical_renewal}")
            
        elif args.action == 'renew':
            results = renewal_system.process_renewals()
            for domain, success in results.items():
                print(f"{domain}: {'SUCCESS' if success else 'FAILED'}")
                
        elif args.action == 'status':
            status = renewal_system.get_renewal_status()
            print(json.dumps(status, indent=2))
            
        elif args.action == 'start-scheduler':
            renewal_system.start_scheduler()
            
            if args.daemon:
                print("SSL renewal scheduler started as daemon")
                try:
                    while True:
                        time.sleep(60)
                except KeyboardInterrupt:
                    print("Stopping scheduler...")
                    renewal_system.stop_scheduler()
            else:
                print("SSL renewal scheduler started (press Ctrl+C to stop)")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("Stopping scheduler...")
                    renewal_system.stop_scheduler()
                    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()