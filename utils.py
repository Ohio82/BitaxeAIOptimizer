"""
Utility functions for Bitaxe Monitor
Data processing, validation, and helper functions
"""

import re
import json
import logging
import hashlib
import socket
import subprocess
import platform
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import ipaddress

def validate_ip_address(ip: str) -> bool:
    """Validate IP address format"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def validate_port(port: Union[int, str]) -> bool:
    """Validate port number"""
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except (ValueError, TypeError):
        return False

def validate_email(email: str) -> bool:
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_frequency(frequency: Union[int, str]) -> bool:
    """Validate ASIC frequency value"""
    try:
        freq = int(frequency)
        return 200 <= freq <= 800  # Reasonable range for Bitaxe
    except (ValueError, TypeError):
        return False

def validate_voltage(voltage: Union[float, str]) -> bool:
    """Validate ASIC voltage value"""
    try:
        volt = float(voltage)
        return 0.8 <= volt <= 1.6  # Reasonable range for Bitaxe
    except (ValueError, TypeError):
        return False

def format_hashrate(hashrate: float, precision: int = 1) -> str:
    """Format hashrate with appropriate units"""
    if hashrate >= 1000:
        return f"{hashrate / 1000:.{precision}f} TH/s"
    elif hashrate >= 1:
        return f"{hashrate:.{precision}f} GH/s"
    elif hashrate >= 0.001:
        return f"{hashrate * 1000:.{precision}f} MH/s"
    else:
        return f"{hashrate * 1000000:.{precision}f} KH/s"

def format_power(power: float, precision: int = 1) -> str:
    """Format power consumption with appropriate units"""
    if power >= 1000:
        return f"{power / 1000:.{precision}f} kW"
    else:
        return f"{power:.{precision}f} W"

def format_temperature(temp: float, unit: str = 'C', precision: int = 1) -> str:
    """Format temperature with unit"""
    if unit.upper() == 'F':
        temp = (temp * 9/5) + 32
        return f"{temp:.{precision}f}°F"
    else:
        return f"{temp:.{precision}f}°C"

def format_uptime(seconds: int) -> str:
    """Format uptime in human readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s"
    elif seconds < 86400:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{hours}h {remaining_minutes}m"
    else:
        days = seconds // 86400
        remaining_hours = (seconds % 86400) // 3600
        return f"{days}d {remaining_hours}h"

def format_difficulty(difficulty: float) -> str:
    """Format mining difficulty with appropriate units"""
    if difficulty >= 1e12:
        return f"{difficulty / 1e12:.2f}T"
    elif difficulty >= 1e9:
        return f"{difficulty / 1e9:.2f}G"
    elif difficulty >= 1e6:
        return f"{difficulty / 1e6:.2f}M"
    elif difficulty >= 1e3:
        return f"{difficulty / 1e3:.2f}K"
    else:
        return f"{difficulty:.0f}"

def calculate_efficiency(hashrate: float, power: float) -> float:
    """Calculate mining efficiency (GH/s per Watt)"""
    if power <= 0:
        return 0.0
    return hashrate / power

def calculate_profitability(hashrate_ghs: float, power_watts: float, 
                          electricity_cost: float = 0.10, 
                          btc_price: float = 50000,
                          network_hashrate_ehs: float = 500) -> Dict[str, float]:
    """Calculate mining profitability estimates"""
    try:
        # Convert units
        hashrate_hs = hashrate_ghs * 1e9  # Convert to H/s
        network_hashrate_hs = network_hashrate_ehs * 1e18  # Convert to H/s
        
        # Bitcoin mining calculations (simplified)
        blocks_per_day = 144  # Average blocks per day
        btc_per_block = 6.25  # Current block reward
        daily_btc_reward = blocks_per_day * btc_per_block
        
        # Calculate share of network hashrate
        hashrate_share = hashrate_hs / network_hashrate_hs
        
        # Daily earnings
        daily_btc_earned = daily_btc_reward * hashrate_share
        daily_revenue = daily_btc_earned * btc_price
        
        # Daily costs
        daily_power_kwh = (power_watts / 1000) * 24
        daily_electricity_cost = daily_power_kwh * electricity_cost
        
        # Profit calculations
        daily_profit = daily_revenue - daily_electricity_cost
        monthly_profit = daily_profit * 30
        yearly_profit = daily_profit * 365
        
        return {
            'daily_btc': daily_btc_earned,
            'daily_revenue': daily_revenue,
            'daily_cost': daily_electricity_cost,
            'daily_profit': daily_profit,
            'monthly_profit': monthly_profit,
            'yearly_profit': yearly_profit,
            'roi_days': abs(daily_profit) if daily_profit != 0 else 0,
            'breakeven_btc_price': daily_electricity_cost / daily_btc_earned if daily_btc_earned > 0 else 0
        }
    
    except (ZeroDivisionError, TypeError, ValueError):
        return {
            'daily_btc': 0,
            'daily_revenue': 0,
            'daily_cost': 0,
            'daily_profit': 0,
            'monthly_profit': 0,
            'yearly_profit': 0,
            'roi_days': 0,
            'breakeven_btc_price': 0
        }

def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """Calculate statistical measures for a list of values"""
    if not values:
        return {
            'count': 0,
            'min': 0,
            'max': 0,
            'mean': 0,
            'median': 0,
            'std_dev': 0,
            'variance': 0
        }
    
    count = len(values)
    min_val = min(values)
    max_val = max(values)
    mean = sum(values) / count
    
    # Calculate median
    sorted_values = sorted(values)
    if count % 2 == 0:
        median = (sorted_values[count // 2 - 1] + sorted_values[count // 2]) / 2
    else:
        median = sorted_values[count // 2]
    
    # Calculate standard deviation and variance
    if count > 1:
        variance = sum((x - mean) ** 2 for x in values) / (count - 1)
        std_dev = variance ** 0.5
    else:
        variance = 0
        std_dev = 0
    
    return {
        'count': count,
        'min': min_val,
        'max': max_val,
        'mean': mean,
        'median': median,
        'std_dev': std_dev,
        'variance': variance
    }

def detect_device_network(ip_range: str = "192.168.1") -> List[str]:
    """Scan network for Bitaxe devices"""
    devices = []
    
    try:
        for i in range(1, 255):
            ip = f"{ip_range}.{i}"
            
            # Quick port scan for typical Bitaxe ports
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            
            result = sock.connect_ex((ip, 80))
            if result == 0:
                # Check if it's actually a Bitaxe by trying to connect
                try:
                    import requests
                    response = requests.get(f"http://{ip}/api/system/info", timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        if 'ASICModel' in data or 'version' in data:
                            devices.append(ip)
                except:
                    pass
            
            sock.close()
    
    except Exception as e:
        logging.error(f"Error scanning network: {e}")
    
    return devices

def get_system_info() -> Dict[str, Any]:
    """Get system information"""
    try:
        return {
            'platform': platform.platform(),
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'hostname': socket.gethostname()
        }
    except Exception as e:
        logging.error(f"Error getting system info: {e}")
        return {}

def check_internet_connection(host: str = "8.8.8.8", port: int = 53, timeout: int = 3) -> bool:
    """Check if internet connection is available"""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

def backup_config(config_file: str, backup_dir: str = "backups") -> bool:
    """Create a backup of configuration file"""
    try:
        config_path = Path(config_file)
        if not config_path.exists():
            return False
        
        backup_path = Path(backup_dir)
        backup_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"config_backup_{timestamp}.json"
        
        with open(config_path, 'r') as src, open(backup_file, 'w') as dst:
            dst.write(src.read())
        
        logging.info(f"Config backed up to {backup_file}")
        return True
    
    except Exception as e:
        logging.error(f"Error backing up config: {e}")
        return False

def restore_config(backup_file: str, config_file: str = "config.json") -> bool:
    """Restore configuration from backup"""
    try:
        backup_path = Path(backup_file)
        config_path = Path(config_file)
        
        if not backup_path.exists():
            return False
        
        with open(backup_path, 'r') as src, open(config_path, 'w') as dst:
            dst.write(src.read())
        
        logging.info(f"Config restored from {backup_file}")
        return True
    
    except Exception as e:
        logging.error(f"Error restoring config: {e}")
        return False

def cleanup_logs(log_file: str = "bitaxe_monitor.log", max_size_mb: int = 10) -> bool:
    """Cleanup log file if it gets too large"""
    try:
        log_path = Path(log_file)
        if not log_path.exists():
            return False
        
        file_size_mb = log_path.stat().st_size / (1024 * 1024)
        
        if file_size_mb > max_size_mb:
            # Keep only the last 50% of the file
            with open(log_path, 'r') as f:
                lines = f.readlines()
            
            keep_lines = len(lines) // 2
            with open(log_path, 'w') as f:
                f.writelines(lines[-keep_lines:])
            
            logging.info(f"Log file cleaned up: reduced from {file_size_mb:.1f}MB")
            return True
        
        return False
    
    except Exception as e:
        logging.error(f"Error cleaning up logs: {e}")
        return False

def generate_device_id(ip_address: str) -> str:
    """Generate unique device ID based on IP address"""
    return hashlib.md5(ip_address.encode()).hexdigest()[:8]

def parse_pool_url(url: str) -> Dict[str, str]:
    """Parse mining pool URL into components"""
    try:
        # Basic URL parsing for stratum URLs
        if url.startswith('stratum+tcp://'):
            url = url[14:]  # Remove stratum+tcp://
        elif url.startswith('stratum://'):
            url = url[10:]  # Remove stratum://
        
        if ':' in url:
            host, port = url.split(':', 1)
            return {
                'protocol': 'stratum',
                'host': host,
                'port': port,
                'full_url': f"stratum+tcp://{host}:{port}"
            }
        else:
            return {
                'protocol': 'stratum',
                'host': url,
                'port': '4444',  # Default stratum port
                'full_url': f"stratum+tcp://{url}:4444"
            }
    
    except Exception as e:
        logging.error(f"Error parsing pool URL: {e}")
        return {
            'protocol': 'unknown',
            'host': '',
            'port': '',
            'full_url': url
        }

def format_bytes(bytes_val: int) -> str:
    """Format bytes in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"

def get_local_ip() -> str:
    """Get local IP address"""
    try:
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def ping_host(host: str, timeout: int = 3) -> bool:
    """Ping a host to check connectivity"""
    try:
        if platform.system().lower() == "windows":
            cmd = f"ping -n 1 -w {timeout * 1000} {host}"
        else:
            cmd = f"ping -c 1 -W {timeout} {host}"
        
        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True,
            timeout=timeout + 1
        )
        
        return result.returncode == 0
    
    except Exception as e:
        logging.error(f"Error pinging {host}: {e}")
        return False

def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to int"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def create_alert_sound():
    """Create a simple beep sound for alerts (Windows only)"""
    try:
        if platform.system().lower() == "windows":
            import winsound
            winsound.Beep(1000, 500)  # 1000 Hz for 500ms
    except ImportError:
        pass  # winsound not available on non-Windows systems

def export_data_csv(data: List[Dict[str, Any]], filename: str, fields: List[str] = None) -> bool:
    """Export data to CSV file"""
    try:
        import csv
        
        if not data:
            return False
        
        if fields is None:
            fields = list(data[0].keys())
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields)
            writer.writeheader()
            
            for row in data:
                # Filter row to only include specified fields
                filtered_row = {field: row.get(field, '') for field in fields}
                writer.writerow(filtered_row)
        
        logging.info(f"Data exported to {filename}")
        return True
    
    except Exception as e:
        logging.error(f"Error exporting data to CSV: {e}")
        return False

def import_data_csv(filename: str) -> List[Dict[str, Any]]:
    """Import data from CSV file"""
    try:
        import csv
        
        data = []
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(dict(row))
        
        logging.info(f"Data imported from {filename}: {len(data)} rows")
        return data
    
    except Exception as e:
        logging.error(f"Error importing data from CSV: {e}")
        return []

class PerformanceMonitor:
    """Monitor application performance"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.metrics = {
            'api_calls': 0,
            'api_errors': 0,
            'database_operations': 0,
            'database_errors': 0,
            'notifications_sent': 0,
            'optimization_runs': 0
        }
    
    def increment_metric(self, metric: str):
        """Increment a performance metric"""
        if metric in self.metrics:
            self.metrics[metric] += 1
    
    def get_uptime(self) -> timedelta:
        """Get application uptime"""
        return datetime.now() - self.start_time
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all performance metrics"""
        uptime = self.get_uptime()
        
        return {
            **self.metrics,
            'uptime_seconds': uptime.total_seconds(),
            'uptime_formatted': format_uptime(int(uptime.total_seconds())),
            'api_success_rate': (
                (self.metrics['api_calls'] - self.metrics['api_errors']) / 
                max(self.metrics['api_calls'], 1) * 100
            ),
            'database_success_rate': (
                (self.metrics['database_operations'] - self.metrics['database_errors']) / 
                max(self.metrics['database_operations'], 1) * 100
            )
        }
    
    def reset_metrics(self):
        """Reset all metrics"""
        for key in self.metrics:
            self.metrics[key] = 0
        self.start_time = datetime.now()

# Global performance monitor instance
performance_monitor = PerformanceMonitor()
