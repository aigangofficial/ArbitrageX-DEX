"""
System Resource Monitor for ArbitrageX

This module provides system resource monitoring capabilities for the ArbitrageX system,
including CPU, memory, and disk usage tracking.
"""

import os
import time
import logging
import threading
import platform
from typing import Dict, Any, Optional, Callable
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("system_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SystemMonitor")

class SystemMonitor:
    """
    System resource monitor for ArbitrageX.
    """
    
    def __init__(self, 
                 monitor_interval_seconds: int = 60,
                 callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Initialize the system monitor.
        
        Args:
            monitor_interval_seconds: Interval in seconds to monitor system resources
            callback: Callback function to call with system metrics
        """
        self.monitor_interval_seconds = monitor_interval_seconds
        self.callback = callback
        
        # Initialize system metrics
        self.system_metrics = {
            "cpu_usage_percent": 0.0,
            "memory_usage_mb": 0.0,
            "memory_total_mb": 0.0,
            "memory_usage_percent": 0.0,
            "disk_usage_mb": 0.0,
            "disk_total_mb": 0.0,
            "disk_usage_percent": 0.0,
            "process_cpu_usage_percent": 0.0,
            "process_memory_usage_mb": 0.0,
            "process_uptime_seconds": 0.0,
            "system_uptime_seconds": 0.0,
            "timestamp": datetime.now().isoformat()
        }
        
        # Initialize stop event
        self.stop_event = threading.Event()
        
        # Initialize monitor thread
        self.monitor_thread = None
        
        # Initialize start time
        self.start_time = time.time()
        
        # Try to import psutil
        try:
            import psutil
            self.psutil_available = True
        except ImportError:
            logger.warning("psutil not available, system monitoring will be limited")
            self.psutil_available = False
    
    def start(self):
        """
        Start the system monitor.
        """
        logger.info("Starting system monitor")
        
        # Start monitor thread
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop(self):
        """
        Stop the system monitor.
        """
        logger.info("Stopping system monitor")
        
        # Stop monitor thread
        self.stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
    
    def _monitor_loop(self):
        """
        Loop to periodically monitor system resources.
        """
        while not self.stop_event.is_set():
            # Monitor system resources
            self._monitor_system_resources()
            
            # Call callback if provided
            if self.callback:
                self.callback(self.system_metrics)
            
            # Sleep for the monitor interval
            for _ in range(self.monitor_interval_seconds):
                if self.stop_event.is_set():
                    break
                time.sleep(1)
    
    def _monitor_system_resources(self):
        """
        Monitor system resources.
        """
        # Update timestamp
        self.system_metrics["timestamp"] = datetime.now().isoformat()
        
        # Update process uptime
        self.system_metrics["process_uptime_seconds"] = time.time() - self.start_time
        
        if self.psutil_available:
            try:
                import psutil
                
                # Get CPU usage
                self.system_metrics["cpu_usage_percent"] = psutil.cpu_percent(interval=1.0)
                
                # Get memory usage
                memory = psutil.virtual_memory()
                self.system_metrics["memory_usage_mb"] = memory.used / (1024 * 1024)
                self.system_metrics["memory_total_mb"] = memory.total / (1024 * 1024)
                self.system_metrics["memory_usage_percent"] = memory.percent
                
                # Get disk usage
                disk = psutil.disk_usage('/')
                self.system_metrics["disk_usage_mb"] = disk.used / (1024 * 1024)
                self.system_metrics["disk_total_mb"] = disk.total / (1024 * 1024)
                self.system_metrics["disk_usage_percent"] = disk.percent
                
                # Get process-specific metrics
                process = psutil.Process(os.getpid())
                self.system_metrics["process_cpu_usage_percent"] = process.cpu_percent(interval=1.0)
                self.system_metrics["process_memory_usage_mb"] = process.memory_info().rss / (1024 * 1024)
                
                # Get system uptime
                self.system_metrics["system_uptime_seconds"] = time.time() - psutil.boot_time()
                
                logger.debug(f"System metrics updated: CPU={self.system_metrics['cpu_usage_percent']:.1f}%, Memory={self.system_metrics['memory_usage_percent']:.1f}%, Disk={self.system_metrics['disk_usage_percent']:.1f}%")
            except Exception as e:
                logger.error(f"Error monitoring system resources: {e}")
        else:
            # Limited monitoring without psutil
            try:
                # Get memory usage (platform-specific)
                if platform.system() == "Linux":
                    with open('/proc/meminfo', 'r') as f:
                        meminfo = {}
                        for line in f:
                            if ':' in line:
                                key, value = line.split(':')
                                meminfo[key.strip()] = int(value.strip().split()[0])
                        
                        total_memory_kb = meminfo.get('MemTotal', 0)
                        free_memory_kb = meminfo.get('MemFree', 0)
                        available_memory_kb = meminfo.get('MemAvailable', free_memory_kb)
                        
                        used_memory_kb = total_memory_kb - available_memory_kb
                        
                        self.system_metrics["memory_usage_mb"] = used_memory_kb / 1024
                        self.system_metrics["memory_total_mb"] = total_memory_kb / 1024
                        self.system_metrics["memory_usage_percent"] = (used_memory_kb / total_memory_kb) * 100 if total_memory_kb > 0 else 0
                
                # Get disk usage
                if hasattr(os, 'statvfs'):
                    statvfs = os.statvfs('/')
                    total_disk_kb = statvfs.f_frsize * statvfs.f_blocks / 1024
                    free_disk_kb = statvfs.f_frsize * statvfs.f_bfree / 1024
                    used_disk_kb = total_disk_kb - free_disk_kb
                    
                    self.system_metrics["disk_usage_mb"] = used_disk_kb / 1024
                    self.system_metrics["disk_total_mb"] = total_disk_kb / 1024
                    self.system_metrics["disk_usage_percent"] = (used_disk_kb / total_disk_kb) * 100 if total_disk_kb > 0 else 0
                
                logger.debug("System metrics updated with limited information (psutil not available)")
            except Exception as e:
                logger.error(f"Error monitoring system resources: {e}")
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get system metrics.
        
        Returns:
            Dictionary containing system metrics
        """
        return self.system_metrics.copy()

def main():
    """
    Main function to run the system monitor as a standalone script.
    """
    def print_metrics(metrics):
        print(f"CPU: {metrics['cpu_usage_percent']:.1f}%, Memory: {metrics['memory_usage_percent']:.1f}%, Disk: {metrics['disk_usage_percent']:.1f}%")
    
    # Create system monitor
    monitor = SystemMonitor(monitor_interval_seconds=5, callback=print_metrics)
    
    try:
        # Start monitor
        monitor.start()
        
        # Run for 60 seconds
        print("Running system monitor for 60 seconds...")
        time.sleep(60)
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        # Stop monitor
        monitor.stop()
        print("System monitor stopped")

if __name__ == "__main__":
    main() 