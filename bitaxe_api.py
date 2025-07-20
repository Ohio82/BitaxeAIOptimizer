"""
Bitaxe Gamma 601 API communication module
Handles HTTP requests to the device's REST API
"""

import requests
import json
import logging
import time
from typing import Dict, Any, Optional, Tuple, List
import threading

class BitaxeAPI:
    def __init__(self, ip_address: str, port: int = 80, timeout: int = 10):
        self.ip_address = ip_address
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{ip_address}:{port}"
        self.session = requests.Session()
        self.last_share_count = 0
        self.lock = threading.Lock()
        
        # Set session timeout
        self.session.timeout = timeout
        
    def _make_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Tuple[bool, Any]:
        """Make HTTP request to Bitaxe device"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == "GET":
                response = self.session.get(url, timeout=self.timeout)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Try to parse JSON response
            try:
                return True, response.json()
            except json.JSONDecodeError:
                return True, response.text
                
        except requests.exceptions.Timeout:
            logging.error(f"Timeout connecting to Bitaxe at {self.ip_address}")
            return False, "Connection timeout"
        except requests.exceptions.ConnectionError:
            logging.error(f"Failed to connect to Bitaxe at {self.ip_address}")
            return False, "Connection failed"
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP error from Bitaxe: {e}")
            return False, f"HTTP error: {e}"
        except Exception as e:
            logging.error(f"Unexpected error communicating with Bitaxe: {e}")
            return False, f"Unexpected error: {e}"
    
    def test_connection(self) -> bool:
        """Test connection to Bitaxe device"""
        success, _ = self._make_request("/api/system/info")
        return success
    
    def get_system_info(self) -> Optional[Dict[str, Any]]:
        """Get system information from Bitaxe"""
        success, data = self._make_request("/api/system/info")
        if success and isinstance(data, dict):
            return data
        return None
    
    def get_mining_status(self) -> Optional[Dict[str, Any]]:
        """Get current mining status and statistics"""
        success, data = self._make_request("/api/system/status")
        if success and isinstance(data, dict):
            # Standardize the response format
            standardized = {
                'hashrate': data.get('hashRate', 0) / 1000000000,  # Convert to GH/s
                'temperature': data.get('temp', 0),
                'chip_temperature': data.get('chipTemp', 0),
                'power': data.get('power', 0),
                'voltage': data.get('voltage', 0),
                'frequency': data.get('frequency', 0),
                'shares_accepted': data.get('sharesAccepted', 0),
                'shares_rejected': data.get('sharesRejected', 0),
                'uptime': data.get('uptimeSeconds', 0),
                'difficulty': data.get('difficulty', 0),
                'pool_url': data.get('stratumURL', ''),
                'worker_name': data.get('stratumUser', ''),
                'fan_speed': data.get('fanSpeed', 0),
                'asic_count': data.get('asicCount', 0),
                'efficiency': data.get('efficiency', 0),
                'best_diff': data.get('bestDiff', 0),
                'session_diff': data.get('sessionDiff', 0)
            }
            
            # Check for new shares
            with self.lock:
                current_shares = standardized['shares_accepted']
                if current_shares > self.last_share_count:
                    standardized['new_share'] = True
                    self.last_share_count = current_shares
                else:
                    standardized['new_share'] = False
            
            return standardized
        return None
    
    def get_pool_info(self) -> Optional[Dict[str, Any]]:
        """Get mining pool information"""
        success, data = self._make_request("/api/system/pool")
        if success and isinstance(data, dict):
            return data
        return None
    
    def set_frequency(self, frequency: int) -> bool:
        """Set ASIC frequency in MHz"""
        data = {"frequency": frequency}
        success, response = self._make_request("/api/system/frequency", "POST", data)
        if success:
            logging.info(f"Frequency set to {frequency} MHz")
            return True
        else:
            logging.error(f"Failed to set frequency: {response}")
            return False
    
    def set_voltage(self, voltage: float) -> bool:
        """Set ASIC voltage in volts"""
        data = {"voltage": voltage}
        success, response = self._make_request("/api/system/voltage", "POST", data)
        if success:
            logging.info(f"Voltage set to {voltage}V")
            return True
        else:
            logging.error(f"Failed to set voltage: {response}")
            return False
    
    def set_pool_config(self, pool_url: str, worker_name: str, password: str = "x") -> bool:
        """Set mining pool configuration"""
        data = {
            "stratumURL": pool_url,
            "stratumUser": worker_name,
            "stratumPassword": password
        }
        success, response = self._make_request("/api/system/pool", "POST", data)
        if success:
            logging.info(f"Pool configuration updated: {pool_url}")
            return True
        else:
            logging.error(f"Failed to set pool config: {response}")
            return False
    
    def restart_device(self) -> bool:
        """Restart the Bitaxe device"""
        success, response = self._make_request("/api/system/restart", "POST")
        if success:
            logging.info("Device restart initiated")
            return True
        else:
            logging.error(f"Failed to restart device: {response}")
            return False
    
    def get_wifi_info(self) -> Optional[Dict[str, Any]]:
        """Get WiFi connection information"""
        success, data = self._make_request("/api/system/wifi")
        if success and isinstance(data, dict):
            return data
        return None
    
    def scan_wifi_networks(self) -> Optional[List[Dict[str, Any]]]:
        """Scan for available WiFi networks"""
        success, data = self._make_request("/api/system/wifi/scan")
        if success and isinstance(data, list):
            return data
        return None
    
    def get_logs(self) -> Optional[str]:
        """Get device logs"""
        success, data = self._make_request("/api/system/logs")
        if success:
            return data
        return None
    
    def get_settings(self) -> Optional[Dict[str, Any]]:
        """Get current device settings"""
        success, data = self._make_request("/api/system/settings")
        if success and isinstance(data, dict):
            return data
        return None
    
    def apply_settings(self, settings: Dict[str, Any]) -> bool:
        """Apply new settings to device"""
        success, response = self._make_request("/api/system/settings", "POST", settings)
        if success:
            logging.info("Settings applied successfully")
            return True
        else:
            logging.error(f"Failed to apply settings: {response}")
            return False
    
    def get_performance_metrics(self) -> Optional[Dict[str, Any]]:
        """Get detailed performance metrics"""
        status = self.get_mining_status()
        if not status:
            return None
        
        # Calculate additional metrics
        metrics = status.copy()
        
        # Calculate efficiency (GH/s per Watt)
        if status['power'] > 0:
            metrics['efficiency'] = status['hashrate'] / status['power']
        else:
            metrics['efficiency'] = 0
        
        # Calculate reject rate
        total_shares = status['shares_accepted'] + status['shares_rejected']
        if total_shares > 0:
            metrics['reject_rate'] = (status['shares_rejected'] / total_shares) * 100
        else:
            metrics['reject_rate'] = 0
        
        # Calculate uptime in human readable format
        uptime_seconds = status['uptime']
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        metrics['uptime_formatted'] = f"{hours}h {minutes}m"
        
        return metrics
    
    def update_ip_address(self, new_ip: str):
        """Update the IP address for API communication"""
        self.ip_address = new_ip
        self.base_url = f"http://{new_ip}:{self.port}"
        logging.info(f"Updated Bitaxe IP address to {new_ip}")
