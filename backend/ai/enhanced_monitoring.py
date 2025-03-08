"""
Enhanced Monitoring System for ArbitrageX

This module provides enhanced monitoring capabilities for the ArbitrageX system,
including structured logging, performance metrics tracking, and alerting.
"""

import os
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("enhanced_monitoring.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("EnhancedMonitoring")

# Import system monitor
from .system_monitor import SystemMonitor

class PerformanceMetrics:
    """
    Class to track performance metrics for the ArbitrageX system.
    """
    
    def __init__(self, metrics_dir: str = "backend/ai/metrics"):
        """
        Initialize performance metrics.
        
        Args:
            metrics_dir: Directory to store metrics
        """
        self.metrics_dir = metrics_dir
        os.makedirs(self.metrics_dir, exist_ok=True)
        
        # Initialize metrics
        self.metrics = {
            "trades": {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0
            },
            "profit": {
                "total_usd": 0.0,
                "gas_cost_usd": 0.0,
                "net_profit_usd": 0.0,
                "avg_profit_per_trade_usd": 0.0
            },
            "performance": {
                "avg_execution_time_ms": 0.0,
                "max_execution_time_ms": 0.0,
                "min_execution_time_ms": float('inf')
            },
            "ml": {
                "model_updates": 0,
                "strategy_adaptations": 0,
                "prediction_accuracy": 0.0
            },
            "system": {
                "cpu_usage_percent": 0.0,
                "memory_usage_mb": 0.0,
                "disk_usage_mb": 0.0
            },
            "networks": {},
            "token_pairs": {},
            "dexes": {}
        }
        
        # Initialize timestamp
        self.last_update = datetime.now()
        
        # Initialize lock for thread safety
        self.lock = threading.Lock()
    
    def update_trade_metrics(self, trade_result: Dict[str, Any]):
        """
        Update metrics based on a trade result.
        
        Args:
            trade_result: Dictionary containing trade result information
        """
        with self.lock:
            # Update trade counts
            self.metrics["trades"]["total"] += 1
            
            if trade_result.get("success", False):
                self.metrics["trades"]["successful"] += 1
            else:
                self.metrics["trades"]["failed"] += 1
            
            # Update success rate
            if self.metrics["trades"]["total"] > 0:
                self.metrics["trades"]["success_rate"] = self.metrics["trades"]["successful"] / self.metrics["trades"]["total"]
            
            # Update profit metrics
            profit_usd = trade_result.get("profit_usd", 0.0)
            gas_cost_usd = trade_result.get("gas_cost_usd", 0.0)
            net_profit_usd = trade_result.get("net_profit_usd", 0.0)
            
            self.metrics["profit"]["total_usd"] += profit_usd
            self.metrics["profit"]["gas_cost_usd"] += gas_cost_usd
            self.metrics["profit"]["net_profit_usd"] += net_profit_usd
            
            if self.metrics["trades"]["successful"] > 0:
                self.metrics["profit"]["avg_profit_per_trade_usd"] = self.metrics["profit"]["net_profit_usd"] / self.metrics["trades"]["successful"]
            
            # Update performance metrics
            execution_time_ms = trade_result.get("execution_time_ms", 0.0)
            
            if execution_time_ms > 0:
                # Update average execution time
                current_total = self.metrics["performance"]["avg_execution_time_ms"] * (self.metrics["trades"]["total"] - 1)
                new_avg = (current_total + execution_time_ms) / self.metrics["trades"]["total"]
                self.metrics["performance"]["avg_execution_time_ms"] = new_avg
                
                # Update max execution time
                if execution_time_ms > self.metrics["performance"]["max_execution_time_ms"]:
                    self.metrics["performance"]["max_execution_time_ms"] = execution_time_ms
                
                # Update min execution time
                if execution_time_ms < self.metrics["performance"]["min_execution_time_ms"]:
                    self.metrics["performance"]["min_execution_time_ms"] = execution_time_ms
            
            # Update network metrics
            network = trade_result.get("network", "unknown")
            if network not in self.metrics["networks"]:
                self.metrics["networks"][network] = {
                    "trades": 0,
                    "successful_trades": 0,
                    "net_profit_usd": 0.0
                }
            
            self.metrics["networks"][network]["trades"] += 1
            if trade_result.get("success", False):
                self.metrics["networks"][network]["successful_trades"] += 1
            self.metrics["networks"][network]["net_profit_usd"] += net_profit_usd
            
            # Update token pair metrics
            token_pair = f"{trade_result.get('token_in', 'unknown')}-{trade_result.get('token_out', 'unknown')}"
            if token_pair not in self.metrics["token_pairs"]:
                self.metrics["token_pairs"][token_pair] = {
                    "trades": 0,
                    "successful_trades": 0,
                    "net_profit_usd": 0.0
                }
            
            self.metrics["token_pairs"][token_pair]["trades"] += 1
            if trade_result.get("success", False):
                self.metrics["token_pairs"][token_pair]["successful_trades"] += 1
            self.metrics["token_pairs"][token_pair]["net_profit_usd"] += net_profit_usd
            
            # Update DEX metrics
            dex = trade_result.get("dex", "unknown")
            if dex not in self.metrics["dexes"]:
                self.metrics["dexes"][dex] = {
                    "trades": 0,
                    "successful_trades": 0,
                    "net_profit_usd": 0.0
                }
            
            self.metrics["dexes"][dex]["trades"] += 1
            if trade_result.get("success", False):
                self.metrics["dexes"][dex]["successful_trades"] += 1
            self.metrics["dexes"][dex]["net_profit_usd"] += net_profit_usd
            
            # Update timestamp
            self.last_update = datetime.now()
    
    def update_ml_metrics(self, ml_metrics: Dict[str, Any]):
        """
        Update machine learning metrics.
        
        Args:
            ml_metrics: Dictionary containing ML metrics
        """
        with self.lock:
            # Update model updates
            self.metrics["ml"]["model_updates"] = ml_metrics.get("model_updates", self.metrics["ml"]["model_updates"])
            
            # Update strategy adaptations
            self.metrics["ml"]["strategy_adaptations"] = ml_metrics.get("strategy_adaptations", self.metrics["ml"]["strategy_adaptations"])
            
            # Update prediction accuracy
            self.metrics["ml"]["prediction_accuracy"] = ml_metrics.get("prediction_accuracy", self.metrics["ml"]["prediction_accuracy"])
            
            # Update timestamp
            self.last_update = datetime.now()
    
    def update_system_metrics(self, system_metrics: Dict[str, Any]):
        """
        Update system metrics.
        
        Args:
            system_metrics: Dictionary containing system metrics
        """
        with self.lock:
            # Update CPU usage
            self.metrics["system"]["cpu_usage_percent"] = system_metrics.get("cpu_usage_percent", self.metrics["system"]["cpu_usage_percent"])
            
            # Update memory usage
            self.metrics["system"]["memory_usage_mb"] = system_metrics.get("memory_usage_mb", self.metrics["system"]["memory_usage_mb"])
            
            # Update disk usage
            self.metrics["system"]["disk_usage_mb"] = system_metrics.get("disk_usage_mb", self.metrics["system"]["disk_usage_mb"])
            
            # Update timestamp
            self.last_update = datetime.now()
    
    def save_metrics(self):
        """
        Save metrics to a JSON file.
        """
        with self.lock:
            # Create timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create metrics file path
            metrics_file = os.path.join(self.metrics_dir, f"metrics_{timestamp}.json")
            
            # Save metrics to file
            with open(metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
            
            logger.info(f"Metrics saved to {metrics_file}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the metrics.
        
        Returns:
            Dictionary containing metrics summary
        """
        with self.lock:
            return {
                "trades": {
                    "total": self.metrics["trades"]["total"],
                    "successful": self.metrics["trades"]["successful"],
                    "success_rate": self.metrics["trades"]["success_rate"]
                },
                "profit": {
                    "net_profit_usd": self.metrics["profit"]["net_profit_usd"],
                    "avg_profit_per_trade_usd": self.metrics["profit"]["avg_profit_per_trade_usd"]
                },
                "performance": {
                    "avg_execution_time_ms": self.metrics["performance"]["avg_execution_time_ms"]
                },
                "last_update": self.last_update.isoformat()
            }

class AlertSystem:
    """
    Alert system for ArbitrageX.
    """
    
    def __init__(self, alert_config_path: str = "backend/ai/config/alert_config.json"):
        """
        Initialize the alert system.
        
        Args:
            alert_config_path: Path to the alert configuration file
        """
        self.alert_config_path = alert_config_path
        self.alert_config = self._load_alert_config()
        
        # Initialize alert history
        self.alert_history = []
        
        # Initialize lock for thread safety
        self.lock = threading.Lock()
    
    def _load_alert_config(self) -> Dict[str, Any]:
        """
        Load alert configuration from a JSON file.
        
        Returns:
            Alert configuration dictionary
        """
        default_config = {
            "enabled": True,
            "log_alerts": True,
            "email_alerts": False,
            "email_config": {
                "smtp_server": "smtp.example.com",
                "smtp_port": 587,
                "smtp_username": "alerts@example.com",
                "smtp_password": "password",
                "from_email": "alerts@example.com",
                "to_email": "admin@example.com"
            },
            "thresholds": {
                "consecutive_failed_trades": 3,
                "low_success_rate": 0.5,
                "negative_profit_threshold": -10.0,
                "high_gas_cost_percent": 50.0,
                "execution_time_threshold_ms": 5000.0,
                "cpu_usage_threshold_percent": 80.0,
                "memory_usage_threshold_mb": 1000.0,
                "disk_usage_threshold_mb": 10000.0
            }
        }
        
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(self.alert_config_path), exist_ok=True)
        
        # Load config if it exists, otherwise create default config
        if os.path.exists(self.alert_config_path):
            try:
                with open(self.alert_config_path, 'r') as f:
                    config = json.load(f)
                    # Update default config with loaded config
                    for key, value in config.items():
                        if key in default_config and isinstance(value, dict) and isinstance(default_config[key], dict):
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
                logger.info(f"Alert configuration loaded from {self.alert_config_path}")
            except Exception as e:
                logger.error(f"Error loading alert configuration: {e}")
        else:
            # Save default config
            with open(self.alert_config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Default alert configuration saved to {self.alert_config_path}")
        
        return default_config
    
    def check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check for alert conditions based on metrics.
        
        Args:
            metrics: Dictionary containing metrics
            
        Returns:
            List of alert dictionaries
        """
        if not self.alert_config.get("enabled", True):
            return []
        
        alerts = []
        
        with self.lock:
            # Check for consecutive failed trades
            consecutive_failed_trades = 0
            for result in metrics.get("recent_trades", [])[::-1]:
                if not result.get("success", False):
                    consecutive_failed_trades += 1
                else:
                    break
            
            if consecutive_failed_trades >= self.alert_config["thresholds"]["consecutive_failed_trades"]:
                alerts.append({
                    "type": "consecutive_failed_trades",
                    "severity": "high",
                    "message": f"Detected {consecutive_failed_trades} consecutive failed trades",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Check for low success rate
            success_rate = metrics["trades"]["success_rate"]
            if success_rate < self.alert_config["thresholds"]["low_success_rate"] and metrics["trades"]["total"] >= 10:
                alerts.append({
                    "type": "low_success_rate",
                    "severity": "medium",
                    "message": f"Low success rate: {success_rate:.2f}",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Check for negative profit
            net_profit_usd = metrics["profit"]["net_profit_usd"]
            if net_profit_usd < self.alert_config["thresholds"]["negative_profit_threshold"]:
                alerts.append({
                    "type": "negative_profit",
                    "severity": "high",
                    "message": f"Negative profit: {net_profit_usd:.2f} USD",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Check for high gas cost
            if metrics["profit"]["total_usd"] > 0:
                gas_cost_percent = (metrics["profit"]["gas_cost_usd"] / metrics["profit"]["total_usd"]) * 100
                if gas_cost_percent > self.alert_config["thresholds"]["high_gas_cost_percent"]:
                    alerts.append({
                        "type": "high_gas_cost",
                        "severity": "medium",
                        "message": f"High gas cost: {gas_cost_percent:.2f}% of profit",
                        "timestamp": datetime.now().isoformat()
                    })
            
            # Check for high execution time
            avg_execution_time_ms = metrics["performance"]["avg_execution_time_ms"]
            if avg_execution_time_ms > self.alert_config["thresholds"]["execution_time_threshold_ms"]:
                alerts.append({
                    "type": "high_execution_time",
                    "severity": "low",
                    "message": f"High average execution time: {avg_execution_time_ms:.2f} ms",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Check for high CPU usage
            cpu_usage_percent = metrics["system"]["cpu_usage_percent"]
            if cpu_usage_percent > self.alert_config["thresholds"]["cpu_usage_threshold_percent"]:
                alerts.append({
                    "type": "high_cpu_usage",
                    "severity": "medium",
                    "message": f"High CPU usage: {cpu_usage_percent:.2f}%",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Check for high memory usage
            memory_usage_mb = metrics["system"]["memory_usage_mb"]
            if memory_usage_mb > self.alert_config["thresholds"]["memory_usage_threshold_mb"]:
                alerts.append({
                    "type": "high_memory_usage",
                    "severity": "medium",
                    "message": f"High memory usage: {memory_usage_mb:.2f} MB",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Check for high disk usage
            disk_usage_mb = metrics["system"]["disk_usage_mb"]
            if disk_usage_mb > self.alert_config["thresholds"]["disk_usage_threshold_mb"]:
                alerts.append({
                    "type": "high_disk_usage",
                    "severity": "medium",
                    "message": f"High disk usage: {disk_usage_mb:.2f} MB",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Add alerts to history
            self.alert_history.extend(alerts)
            
            # Log alerts
            if self.alert_config.get("log_alerts", True):
                for alert in alerts:
                    severity = alert["severity"]
                    if severity == "high":
                        logger.error(f"ALERT: {alert['message']}")
                    elif severity == "medium":
                        logger.warning(f"ALERT: {alert['message']}")
                    else:
                        logger.info(f"ALERT: {alert['message']}")
            
            # Send email alerts
            if self.alert_config.get("email_alerts", False) and alerts:
                self._send_email_alerts(alerts)
            
            return alerts
    
    def _send_email_alerts(self, alerts: List[Dict[str, Any]]):
        """
        Send email alerts.
        
        Args:
            alerts: List of alert dictionaries
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Get email config
            email_config = self.alert_config.get("email_config", {})
            smtp_server = email_config.get("smtp_server", "")
            smtp_port = email_config.get("smtp_port", 587)
            smtp_username = email_config.get("smtp_username", "")
            smtp_password = email_config.get("smtp_password", "")
            from_email = email_config.get("from_email", "")
            to_email = email_config.get("to_email", "")
            
            if not all([smtp_server, smtp_username, smtp_password, from_email, to_email]):
                logger.error("Email configuration incomplete, cannot send email alerts")
                return
            
            # Create message
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = to_email
            msg["Subject"] = f"ArbitrageX Alerts: {len(alerts)} new alerts"
            
            # Create message body
            body = "The following alerts have been triggered:\n\n"
            for alert in alerts:
                body += f"- {alert['severity'].upper()}: {alert['message']} ({alert['timestamp']})\n"
            
            msg.attach(MIMEText(body, "plain"))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent to {to_email}")
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    def get_alert_history(self) -> List[Dict[str, Any]]:
        """
        Get alert history.
        
        Returns:
            List of alert dictionaries
        """
        with self.lock:
            return self.alert_history.copy()

class EnhancedMonitoring:
    """
    Enhanced monitoring system for ArbitrageX.
    """
    
    def __init__(self, 
                 metrics_dir: str = "backend/ai/metrics",
                 alert_config_path: str = "backend/ai/config/alert_config.json",
                 save_interval_seconds: int = 300,
                 monitor_interval_seconds: int = 60):
        """
        Initialize the enhanced monitoring system.
        
        Args:
            metrics_dir: Directory to store metrics
            alert_config_path: Path to the alert configuration file
            save_interval_seconds: Interval in seconds to save metrics
            monitor_interval_seconds: Interval in seconds to monitor system resources
        """
        self.metrics = PerformanceMetrics(metrics_dir=metrics_dir)
        self.alert_system = AlertSystem(alert_config_path=alert_config_path)
        self.save_interval_seconds = save_interval_seconds
        
        # Initialize system monitor
        self.system_monitor = SystemMonitor(
            monitor_interval_seconds=monitor_interval_seconds,
            callback=self.log_system_metrics
        )
        
        # Initialize stop event
        self.stop_event = threading.Event()
        
        # Initialize save thread
        self.save_thread = None
    
    def start(self):
        """
        Start the enhanced monitoring system.
        """
        logger.info("Starting enhanced monitoring system")
        
        # Start system monitor
        self.system_monitor.start()
        
        # Start save thread
        self.stop_event.clear()
        self.save_thread = threading.Thread(target=self._save_metrics_loop)
        self.save_thread.daemon = True
        self.save_thread.start()
    
    def stop(self):
        """
        Stop the enhanced monitoring system.
        """
        logger.info("Stopping enhanced monitoring system")
        
        # Stop system monitor
        self.system_monitor.stop()
        
        # Stop save thread
        self.stop_event.set()
        if self.save_thread:
            self.save_thread.join(timeout=5.0)
        
        # Save metrics one last time
        self.metrics.save_metrics()
    
    def _save_metrics_loop(self):
        """
        Loop to periodically save metrics.
        """
        while not self.stop_event.is_set():
            # Sleep for the save interval
            for _ in range(self.save_interval_seconds):
                if self.stop_event.is_set():
                    break
                time.sleep(1)
            
            # Save metrics
            if not self.stop_event.is_set():
                self.metrics.save_metrics()
                
                # Check for alerts
                self.alert_system.check_alerts(self.metrics.metrics)
    
    def log_trade(self, trade_result: Dict[str, Any]):
        """
        Log a trade result.
        
        Args:
            trade_result: Dictionary containing trade result information
        """
        # Update metrics
        self.metrics.update_trade_metrics(trade_result)
        
        # Log structured information
        logger.info("Trade executed", extra={
            "trade_id": trade_result.get("trade_id", "unknown"),
            "success": trade_result.get("success", False),
            "profit_usd": trade_result.get("profit_usd", 0.0),
            "gas_cost_usd": trade_result.get("gas_cost_usd", 0.0),
            "net_profit_usd": trade_result.get("net_profit_usd", 0.0),
            "execution_time_ms": trade_result.get("execution_time_ms", 0.0),
            "network": trade_result.get("network", "unknown"),
            "token_pair": f"{trade_result.get('token_in', 'unknown')}-{trade_result.get('token_out', 'unknown')}",
            "dex": trade_result.get("dex", "unknown")
        })
    
    def log_ml_update(self, ml_metrics: Dict[str, Any]):
        """
        Log a machine learning update.
        
        Args:
            ml_metrics: Dictionary containing ML metrics
        """
        # Update metrics
        self.metrics.update_ml_metrics(ml_metrics)
        
        # Log structured information
        logger.info("ML model updated", extra={
            "model_updates": ml_metrics.get("model_updates", 0),
            "strategy_adaptations": ml_metrics.get("strategy_adaptations", 0),
            "prediction_accuracy": ml_metrics.get("prediction_accuracy", 0.0)
        })
    
    def log_system_metrics(self, system_metrics: Dict[str, Any]):
        """
        Log system metrics.
        
        Args:
            system_metrics: Dictionary containing system metrics
        """
        # Update metrics
        self.metrics.update_system_metrics(system_metrics)
        
        # Log structured information
        logger.info("System metrics updated", extra={
            "cpu_usage_percent": system_metrics.get("cpu_usage_percent", 0.0),
            "memory_usage_mb": system_metrics.get("memory_usage_mb", 0.0),
            "disk_usage_mb": system_metrics.get("disk_usage_mb", 0.0)
        })
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the metrics.
        
        Returns:
            Dictionary containing metrics summary
        """
        return self.metrics.get_metrics_summary()
    
    def get_alert_history(self) -> List[Dict[str, Any]]:
        """
        Get alert history.
        
        Returns:
            List of alert dictionaries
        """
        return self.alert_system.get_alert_history() 