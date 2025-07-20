"""
Notification system for sending email alerts
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any
from config import Config

class NotificationManager:
    def __init__(self, config: Config):
        self.config = config
        self.email_config = config.get_email_config()
        
    def is_email_enabled(self) -> bool:
        """Check if email notifications are enabled and configured"""
        if not self.config.get('notifications.email.enabled', False):
            return False
        
        required_fields = ['sender_email', 'sender_password', 'recipient_email']
        for field in required_fields:
            if not self.email_config.get(field):
                logging.warning(f"Email notification disabled: missing {field}")
                return False
        
        return True
    
    def send_email(self, subject: str, body: str, is_html: bool = False) -> bool:
        """Send email notification"""
        if not self.is_email_enabled():
            logging.info("Email notifications disabled, skipping email")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.email_config['recipient_email']
            msg['Subject'] = subject
            
            # Add body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            smtp_server = self.email_config.get('smtp_server', 'smtp.gmail.com')
            smtp_port = self.email_config.get('smtp_port', 587)
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(
                self.email_config['sender_email'],
                self.email_config['sender_password']
            )
            
            # Send email
            text = msg.as_string()
            server.sendmail(
                self.email_config['sender_email'],
                self.email_config['recipient_email'],
                text
            )
            server.quit()
            
            logging.info(f"Email sent successfully: {subject}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send email: {e}")
            return False
    
    def send_test_email(self) -> bool:
        """Send a test email to verify configuration"""
        subject = "Bitaxe Monitor - Test Email"
        body = f"""
        This is a test email from your Bitaxe Gamma 601 Monitor.
        
        If you received this email, your notification system is working correctly!
        
        Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Best regards,
        Bitaxe Monitor
        """
        
        return self.send_email(subject, body)
    
    def send_temperature_alert(self, temperature: float) -> bool:
        """Send temperature alert email"""
        threshold = self.config.get('notifications.email.alerts.temperature_threshold', 85)
        
        subject = f"🔥 Bitaxe Temperature Alert - {temperature:.1f}°C"
        body = f"""
        TEMPERATURE ALERT
        
        Your Bitaxe Gamma 601 has exceeded the temperature threshold.
        
        Current Temperature: {temperature:.1f}°C
        Threshold: {threshold}°C
        
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Recommended Actions:
        1. Check ambient temperature and ventilation
        2. Verify fan operation
        3. Consider reducing frequency/voltage if temperature persists
        4. Clean device if dusty
        
        Monitor your device to prevent overheating damage.
        
        Bitaxe Monitor
        """
        
        return self.send_email(subject, body)
    
    def send_hashrate_alert(self, current_hashrate: float, expected_hashrate: float) -> bool:
        """Send hashrate drop alert email"""
        drop_percent = ((expected_hashrate - current_hashrate) / expected_hashrate) * 100
        
        subject = f"📉 Bitaxe Hashrate Drop Alert - {current_hashrate:.1f} GH/s"
        body = f"""
        HASHRATE DROP ALERT
        
        Your Bitaxe Gamma 601 hashrate has dropped significantly.
        
        Current Hashrate: {current_hashrate:.1f} GH/s
        Expected Hashrate: {expected_hashrate:.1f} GH/s
        Drop: {drop_percent:.1f}%
        
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Possible Causes:
        1. Network connectivity issues
        2. Pool problems
        3. Device overheating
        4. Hardware issues
        5. Suboptimal settings
        
        Check your device and network connection.
        
        Bitaxe Monitor
        """
        
        return self.send_email(subject, body)
    
    def send_connection_alert(self, connected: bool) -> bool:
        """Send connection status alert email"""
        if connected:
            subject = "✅ Bitaxe Connection Restored"
            body = f"""
            CONNECTION RESTORED
            
            Your Bitaxe Gamma 601 connection has been restored.
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            The device is now responding normally.
            
            Bitaxe Monitor
            """
        else:
            subject = "🔌 Bitaxe Connection Lost"
            body = f"""
            CONNECTION LOST
            
            Your Bitaxe Gamma 601 is not responding.
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Possible Causes:
            1. Network connectivity issues
            2. Device powered off
            3. IP address changed
            4. Hardware failure
            
            Please check your device and network connection.
            
            Bitaxe Monitor
            """
        
        return self.send_email(subject, body)
    
    def send_optimization_alert(self, results: Dict[str, Any]) -> bool:
        """Send optimization results email"""
        if not self.config.get('notifications.email.alerts.optimal_settings_found', True):
            return False
        
        success = results.get('success', False)
        
        if success:
            subject = "🎯 Bitaxe Optimization Complete - Improved Performance"
            body = f"""
            OPTIMIZATION SUCCESSFUL
            
            Your Bitaxe Gamma 601 has been optimized with improved settings.
            
            Results:
            - Previous Hashrate: {results.get('hashrate_before', 0):.1f} GH/s
            - New Hashrate: {results.get('hashrate_after', 0):.1f} GH/s
            - Improvement: {results.get('improvement_percent', 0):.1f}%
            
            - Previous Temperature: {results.get('temperature_before', 0):.1f}°C
            - New Temperature: {results.get('temperature_after', 0):.1f}°C
            
            Settings Applied:
            - Frequency: {results.get('frequency', 0)} MHz
            - Voltage: {results.get('voltage', 0):.2f} V
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Your device is now running with optimized settings.
            
            Bitaxe Monitor
            """
        else:
            subject = "⚠️ Bitaxe Optimization Failed"
            body = f"""
            OPTIMIZATION FAILED
            
            The optimization process for your Bitaxe Gamma 601 did not find better settings.
            
            Current Performance:
            - Hashrate: {results.get('hashrate_before', 0):.1f} GH/s
            - Temperature: {results.get('temperature_before', 0):.1f}°C
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Your device settings remain unchanged. You may want to:
            1. Monitor for longer to collect more data
            2. Check device temperature and cooling
            3. Manually adjust settings if needed
            
            Bitaxe Monitor
            """
        
        return self.send_email(subject, body)
    
    def send_daily_report(self, stats: Dict[str, Any]) -> bool:
        """Send daily performance report email"""
        subject = f"📊 Daily Bitaxe Report - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Calculate 24h averages
        avg_hashrate = stats.get('avg_hashrate', 0)
        avg_temperature = stats.get('avg_temperature', 0)
        avg_power = stats.get('avg_power', 0)
        efficiency = avg_hashrate / avg_power if avg_power > 0 else 0
        
        total_shares = stats.get('total_shares', 0)
        accepted_shares = stats.get('accepted_shares', 0)
        rejected_shares = stats.get('rejected_shares', 0)
        accept_rate = (accepted_shares / total_shares * 100) if total_shares > 0 else 0
        
        body = f"""
        DAILY PERFORMANCE REPORT
        
        24-Hour Summary for {datetime.now().strftime('%Y-%m-%d')}
        
        Performance Metrics:
        - Average Hashrate: {avg_hashrate:.1f} GH/s
        - Average Temperature: {avg_temperature:.1f}°C
        - Average Power: {avg_power:.1f} W
        - Efficiency: {efficiency:.2f} GH/W
        
        Share Statistics:
        - Total Shares: {total_shares}
        - Accepted: {accepted_shares}
        - Rejected: {rejected_shares}
        - Accept Rate: {accept_rate:.1f}%
        
        Device Status:
        - Max Temperature: {stats.get('max_temperature', 0):.1f}°C
        - Min Hashrate: {stats.get('min_hashrate', 0):.1f} GH/s
        - Max Hashrate: {stats.get('max_hashrate', 0):.1f} GH/s
        - Uptime: {stats.get('uptime_hours', 0):.1f} hours
        
        Your Bitaxe Gamma 601 continues to operate efficiently.
        
        Bitaxe Monitor
        """
        
        return self.send_email(subject, body)
