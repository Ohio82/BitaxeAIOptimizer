"""
Configuration management for Bitaxe Monitor
"""

import os
import json
import logging
from typing import Dict, Any

class Config:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.settings = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        default_config = {
            "bitaxe": {
                "ip_address": "192.168.1.100",
                "port": 80,
                "poll_interval": 5,
                "timeout": 10
            },
            "database": {
                "file": "bitaxe_data.db",
                "retention_days": 30
            },
            "notifications": {
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "sender_email": "",
                    "sender_password": "",
                    "recipient_email": "",
                    "alerts": {
                        "temperature_threshold": 85,
                        "hashrate_drop_percent": 20,
                        "optimal_settings_found": True
                    }
                }
            },
            "optimization": {
                "auto_optimize": False,
                "target_temperature": 75,
                "min_hashrate_improvement": 5
            },
            "gui": {
                "theme": "light",
                "chart_update_interval": 2,
                "data_points_display": 100
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults to ensure all keys exist
                return self._merge_configs(default_config, loaded_config)
            except Exception as e:
                logging.error(f"Error loading config: {e}")
                return default_config
        else:
            self.save_config(default_config)
            return default_config
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Recursively merge loaded config with defaults"""
        for key, value in loaded.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                default[key] = self._merge_configs(default[key], value)
            else:
                default[key] = value
        return default
    
    def save_config(self, config=None):
        """Save configuration to file"""
        try:
            config_to_save = config if config else self.settings
            with open(self.config_file, 'w') as f:
                json.dump(config_to_save, f, indent=4)
            logging.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logging.error(f"Error saving config: {e}")
    
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'bitaxe.ip_address')"""
        keys = key_path.split('.')
        value = self.settings
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value):
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self.settings
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
        self.save_config()
    
    def get_email_config(self):
        """Get email configuration with environment variable fallbacks"""
        email_config = self.get('notifications.email', {})
        
        # Override with environment variables if available
        email_config['sender_email'] = os.getenv('BITAXE_EMAIL', email_config.get('sender_email', ''))
        email_config['sender_password'] = os.getenv('BITAXE_EMAIL_PASSWORD', email_config.get('sender_password', ''))
        email_config['recipient_email'] = os.getenv('BITAXE_RECIPIENT_EMAIL', email_config.get('recipient_email', ''))
        
        return email_config
