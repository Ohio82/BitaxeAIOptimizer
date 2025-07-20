"""
Performance optimization module for Bitaxe Gamma 601
Automatically finds optimal frequency and voltage settings
"""

import time
import logging
import threading
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from bitaxe_api import BitaxeAPI
from config import Config
from database import Database

@dataclass
class OptimizationResult:
    """Data class for optimization results"""
    frequency: int
    voltage: float
    hashrate_before: float
    hashrate_after: float
    temperature_before: float
    temperature_after: float
    improvement_percent: float
    success: bool
    test_duration: int
    stability_score: float

class PerformanceOptimizer:
    def __init__(self, api: BitaxeAPI, config: Config, database: Database = None):
        self.api = api
        self.config = config
        self.database = database
        
        # Optimization parameters
        self.test_duration = 300  # 5 minutes per test
        self.stability_threshold = 0.95  # 95% stability required
        self.max_temperature = config.get('optimization.target_temperature', 75)
        self.min_improvement = config.get('optimization.min_hashrate_improvement', 5)
        
        # Safety limits
        self.min_frequency = 400
        self.max_frequency = 600
        self.min_voltage = 1.0
        self.max_voltage = 1.4
        
        # Test ranges
        self.frequency_steps = [400, 450, 500, 525, 550, 575, 600]
        self.voltage_steps = [1.0, 1.1, 1.15, 1.2, 1.25, 1.3, 1.35, 1.4]
        
        self.running = False
        self.current_test = None
        
    def optimize(self) -> Optional[OptimizationResult]:
        """Run complete optimization process"""
        if self.running:
            logging.warning("Optimization already running")
            return None
        
        self.running = True
        logging.info("Starting performance optimization")
        
        try:
            # Get baseline performance
            baseline = self._get_baseline_performance()
            if not baseline:
                logging.error("Failed to get baseline performance")
                return None
            
            logging.info(f"Baseline: {baseline['hashrate']:.1f} GH/s at {baseline['temperature']:.1f}°C")
            
            # Find optimal settings
            best_result = self._find_optimal_settings(baseline)
            
            if best_result and best_result.success:
                # Apply optimal settings
                self._apply_optimal_settings(best_result)
                
                # Send notification if enabled
                if self.config.get('notifications.email.alerts.optimal_settings_found', True):
                    try:
                        from notifications import NotificationManager
                        notif_manager = NotificationManager(self.config)
                        notif_manager.send_optimization_alert(best_result.__dict__)
                    except Exception as e:
                        logging.error(f"Failed to send optimization notification: {e}")
                
                # Store result in database
                if self.database:
                    self._store_optimization_result(best_result)
                
                logging.info(f"Optimization complete: {best_result.improvement_percent:.1f}% improvement")
                return best_result
            else:
                logging.info("No better settings found")
                return OptimizationResult(
                    frequency=baseline['frequency'],
                    voltage=baseline['voltage'],
                    hashrate_before=baseline['hashrate'],
                    hashrate_after=baseline['hashrate'],
                    temperature_before=baseline['temperature'],
                    temperature_after=baseline['temperature'],
                    improvement_percent=0,
                    success=False,
                    test_duration=0,
                    stability_score=1.0
                )
        
        except Exception as e:
            logging.error(f"Optimization failed: {e}")
            return None
        
        finally:
            self.running = False
    
    def _get_baseline_performance(self) -> Optional[Dict[str, Any]]:
        """Get current performance baseline"""
        try:
            # Collect data for baseline measurement
            samples = []
            sample_count = 12  # 1 minute of samples at 5s intervals
            
            for i in range(sample_count):
                status = self.api.get_mining_status()
                if status:
                    samples.append(status)
                    time.sleep(5)
                else:
                    logging.warning(f"Failed to get status for baseline sample {i+1}")
            
            if len(samples) < sample_count // 2:
                logging.error("Insufficient samples for baseline")
                return None
            
            # Calculate averages
            avg_hashrate = sum(s['hashrate'] for s in samples) / len(samples)
            avg_temperature = sum(s['temperature'] for s in samples) / len(samples)
            
            # Get current settings
            current_freq = samples[-1]['frequency']
            current_voltage = samples[-1]['voltage']
            
            return {
                'hashrate': avg_hashrate,
                'temperature': avg_temperature,
                'frequency': current_freq,
                'voltage': current_voltage,
                'samples': len(samples),
                'stability': self._calculate_stability(samples)
            }
        
        except Exception as e:
            logging.error(f"Error getting baseline performance: {e}")
            return None
    
    def _find_optimal_settings(self, baseline: Dict[str, Any]) -> Optional[OptimizationResult]:
        """Find optimal frequency and voltage combination"""
        best_result = None
        best_score = 0
        
        # Generate test combinations
        test_combinations = self._generate_test_combinations()
        
        logging.info(f"Testing {len(test_combinations)} frequency/voltage combinations")
        
        for i, (freq, voltage) in enumerate(test_combinations):
            if not self.running:
                break
            
            logging.info(f"Testing combination {i+1}/{len(test_combinations)}: {freq}MHz, {voltage:.2f}V")
            
            # Test this combination
            result = self._test_settings(freq, voltage, baseline)
            
            if result and result.success:
                # Calculate overall score (hashrate improvement weighted by temperature)
                temp_penalty = max(0, (result.temperature_after - self.max_temperature) * 0.1)
                score = result.improvement_percent - temp_penalty
                
                if score > best_score and score >= self.min_improvement:
                    best_score = score
                    best_result = result
                    logging.info(f"New best result: {score:.1f} score, {result.improvement_percent:.1f}% improvement")
        
        # Restore baseline settings if no improvement found
        if not best_result:
            self.api.set_frequency(baseline['frequency'])
            self.api.set_voltage(baseline['voltage'])
            time.sleep(10)  # Allow settings to settle
        
        return best_result
    
    def _generate_test_combinations(self) -> List[Tuple[int, float]]:
        """Generate smart test combinations based on expected performance"""
        combinations = []
        
        # Start with conservative settings and gradually increase
        for freq in self.frequency_steps:
            for voltage in self.voltage_steps:
                # Skip unsafe combinations
                if self._is_safe_combination(freq, voltage):
                    combinations.append((freq, voltage))
        
        # Sort by expected performance (higher frequency first, then higher voltage)
        combinations.sort(key=lambda x: (x[0], x[1]), reverse=True)
        
        return combinations
    
    def _is_safe_combination(self, frequency: int, voltage: float) -> bool:
        """Check if frequency/voltage combination is safe"""
        # Basic safety checks
        if frequency < self.min_frequency or frequency > self.max_frequency:
            return False
        
        if voltage < self.min_voltage or voltage > self.max_voltage:
            return False
        
        # Conservative voltage limits for high frequencies
        if frequency >= 575 and voltage > 1.3:
            return False
        
        if frequency >= 550 and voltage > 1.35:
            return False
        
        return True
    
    def _test_settings(self, frequency: int, voltage: float, baseline: Dict[str, Any]) -> Optional[OptimizationResult]:
        """Test specific frequency and voltage settings"""
        try:
            self.current_test = f"{frequency}MHz, {voltage:.2f}V"
            
            # Apply settings
            if not self.api.set_frequency(frequency):
                logging.error(f"Failed to set frequency to {frequency}")
                return None
            
            time.sleep(2)
            
            if not self.api.set_voltage(voltage):
                logging.error(f"Failed to set voltage to {voltage}")
                return None
            
            # Wait for settings to stabilize
            time.sleep(30)
            
            # Collect performance data
            samples = []
            sample_interval = 10  # 10 seconds between samples
            total_samples = self.test_duration // sample_interval
            
            for i in range(total_samples):
                if not self.running:
                    break
                
                status = self.api.get_mining_status()
                if status:
                    samples.append(status)
                    
                    # Safety check - abort if temperature too high
                    if status['temperature'] > self.max_temperature + 10:
                        logging.warning(f"Temperature too high ({status['temperature']:.1f}°C), aborting test")
                        return None
                
                time.sleep(sample_interval)
            
            if len(samples) < total_samples // 2:
                logging.warning("Insufficient samples for test")
                return None
            
            # Calculate results
            avg_hashrate = sum(s['hashrate'] for s in samples) / len(samples)
            avg_temperature = sum(s['temperature'] for s in samples) / len(samples)
            stability = self._calculate_stability(samples)
            
            # Check if results are valid
            if stability < self.stability_threshold:
                logging.warning(f"Low stability ({stability:.2f}), rejecting result")
                return None
            
            if avg_temperature > self.max_temperature:
                logging.warning(f"Temperature too high ({avg_temperature:.1f}°C), rejecting result")
                return None
            
            # Calculate improvement
            improvement_percent = ((avg_hashrate - baseline['hashrate']) / baseline['hashrate']) * 100
            
            result = OptimizationResult(
                frequency=frequency,
                voltage=voltage,
                hashrate_before=baseline['hashrate'],
                hashrate_after=avg_hashrate,
                temperature_before=baseline['temperature'],
                temperature_after=avg_temperature,
                improvement_percent=improvement_percent,
                success=improvement_percent >= self.min_improvement,
                test_duration=len(samples) * sample_interval,
                stability_score=stability
            )
            
            logging.info(f"Test result: {improvement_percent:.1f}% improvement, {avg_temperature:.1f}°C, {stability:.2f} stability")
            
            return result
        
        except Exception as e:
            logging.error(f"Error testing settings {frequency}MHz, {voltage:.2f}V: {e}")
            return None
        
        finally:
            self.current_test = None
    
    def _calculate_stability(self, samples: List[Dict[str, Any]]) -> float:
        """Calculate stability score based on hashrate variance"""
        if len(samples) < 2:
            return 0.0
        
        hashrates = [s['hashrate'] for s in samples]
        avg_hashrate = sum(hashrates) / len(hashrates)
        
        if avg_hashrate == 0:
            return 0.0
        
        # Calculate coefficient of variation (lower is more stable)
        variance = sum((h - avg_hashrate) ** 2 for h in hashrates) / len(hashrates)
        std_dev = variance ** 0.5
        cv = std_dev / avg_hashrate
        
        # Convert to stability score (0-1, higher is more stable)
        stability = max(0, 1 - cv * 10)  # Scale coefficient of variation
        
        return min(1.0, stability)
    
    def _apply_optimal_settings(self, result: OptimizationResult):
        """Apply the optimal settings found"""
        try:
            logging.info(f"Applying optimal settings: {result.frequency}MHz, {result.voltage:.2f}V")
            
            self.api.set_frequency(result.frequency)
            time.sleep(2)
            self.api.set_voltage(result.voltage)
            
            # Wait for settings to stabilize
            time.sleep(30)
            
            # Verify settings applied correctly
            status = self.api.get_mining_status()
            if status:
                actual_freq = status.get('frequency', 0)
                actual_voltage = status.get('voltage', 0)
                
                if abs(actual_freq - result.frequency) > 5 or abs(actual_voltage - result.voltage) > 0.05:
                    logging.warning(f"Settings verification failed: expected {result.frequency}MHz/{result.voltage:.2f}V, got {actual_freq}MHz/{actual_voltage:.2f}V")
                else:
                    logging.info("Optimal settings applied and verified successfully")
        
        except Exception as e:
            logging.error(f"Error applying optimal settings: {e}")
    
    def _store_optimization_result(self, result: OptimizationResult):
        """Store optimization result in database"""
        try:
            if self.database:
                self.database.database.insert_optimization_history({
                    'frequency': result.frequency,
                    'voltage': result.voltage,
                    'hashrate_before': result.hashrate_before,
                    'hashrate_after': result.hashrate_after,
                    'temperature_before': result.temperature_before,
                    'temperature_after': result.temperature_after,
                    'improvement_percent': result.improvement_percent,
                    'success': result.success
                })
        except Exception as e:
            logging.error(f"Error storing optimization result: {e}")
    
    def stop_optimization(self):
        """Stop the optimization process"""
        self.running = False
        logging.info("Optimization stop requested")
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status"""
        return {
            'running': self.running,
            'current_test': self.current_test,
            'test_duration': self.test_duration,
            'max_temperature': self.max_temperature,
            'min_improvement': self.min_improvement
        }
    
    def quick_tune(self, target_hashrate: float = None) -> Optional[OptimizationResult]:
        """Quick optimization focusing on specific target"""
        if self.running:
            return None
        
        self.running = True
        
        try:
            baseline = self._get_baseline_performance()
            if not baseline:
                return None
            
            # If no target specified, aim for 10% improvement
            if target_hashrate is None:
                target_hashrate = baseline['hashrate'] * 1.1
            
            # Test a few promising combinations
            quick_combinations = [
                (525, 1.2), (550, 1.25), (500, 1.15), (575, 1.3)
            ]
            
            best_result = None
            best_distance = float('inf')
            
            for freq, voltage in quick_combinations:
                if not self._is_safe_combination(freq, voltage):
                    continue
                
                result = self._test_settings(freq, voltage, baseline)
                if result and result.success:
                    distance = abs(result.hashrate_after - target_hashrate)
                    if distance < best_distance:
                        best_distance = distance
                        best_result = result
            
            if best_result:
                self._apply_optimal_settings(best_result)
                return best_result
            
            return None
        
        finally:
            self.running = False

class AutoOptimizer:
    """Automatic optimization scheduler"""
    
    def __init__(self, optimizer: PerformanceOptimizer, config: Config):
        self.optimizer = optimizer
        self.config = config
        self.running = False
        self.thread = None
        
        # Auto optimization settings
        self.check_interval = 3600  # Check every hour
        self.min_runtime_hours = 24  # Minimum runtime before optimization
        self.performance_threshold = 5  # % drop threshold for re-optimization
        
    def start(self):
        """Start automatic optimization"""
        if self.running:
            return
        
        if not self.config.get('optimization.auto_optimize', False):
            logging.info("Auto optimization disabled in config")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._auto_optimize_loop, daemon=True)
        self.thread.start()
        
        logging.info("Auto optimization started")
    
    def stop(self):
        """Stop automatic optimization"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        logging.info("Auto optimization stopped")
    
    def _auto_optimize_loop(self):
        """Main auto optimization loop"""
        last_optimization = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Check if it's time to consider optimization
                if current_time - last_optimization > self.min_runtime_hours * 3600:
                    
                    # Check if optimization is needed
                    if self._should_optimize():
                        logging.info("Auto optimization triggered")
                        
                        result = self.optimizer.optimize()
                        if result and result.success:
                            logging.info(f"Auto optimization successful: {result.improvement_percent:.1f}% improvement")
                            last_optimization = current_time
                        else:
                            logging.info("Auto optimization found no improvements")
                            last_optimization = current_time
                
                # Sleep until next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logging.error(f"Error in auto optimization loop: {e}")
                time.sleep(self.check_interval)
    
    def _should_optimize(self) -> bool:
        """Determine if optimization should be run"""
        try:
            # Get recent performance data
            if hasattr(self.optimizer, 'database') and self.optimizer.database:
                recent_data = self.optimizer.database.get_recent_data(hours=6)
                
                if len(recent_data) < 10:
                    return False  # Not enough data
                
                # Calculate average recent performance
                recent_hashrate = sum(d['hashrate'] for d in recent_data) / len(recent_data)
                recent_temperature = sum(d['temperature'] for d in recent_data) / len(recent_data)
                
                # Get historical average for comparison
                historical_data = self.optimizer.database.get_recent_data(hours=168)  # 1 week
                
                if len(historical_data) > 100:
                    historical_hashrate = sum(d['hashrate'] for d in historical_data) / len(historical_data)
                    
                    # Check for performance degradation
                    performance_drop = ((historical_hashrate - recent_hashrate) / historical_hashrate) * 100
                    
                    if performance_drop > self.performance_threshold:
                        logging.info(f"Performance drop detected: {performance_drop:.1f}%")
                        return True
                
                # Check for high temperature issues
                if recent_temperature > self.config.get('optimization.target_temperature', 75) + 5:
                    logging.info(f"High temperature detected: {recent_temperature:.1f}°C")
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking if optimization needed: {e}")
            return False
