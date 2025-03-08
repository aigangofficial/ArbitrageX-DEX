"""
Run Enhanced Monitoring System for ArbitrageX

This script runs the enhanced monitoring system for the ArbitrageX system.
"""

import os
import sys
import time
import logging
import argparse
import signal
from typing import Dict, Any

# Add the parent directory to the Python path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("enhanced_monitoring.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RunEnhancedMonitoring")

# Import the enhanced monitoring system
from backend.ai.enhanced_monitoring import EnhancedMonitoring

def signal_handler(sig, frame):
    """
    Signal handler for graceful shutdown.
    """
    logger.info("Received shutdown signal, stopping...")
    global monitoring_system
    if monitoring_system:
        monitoring_system.stop()
    sys.exit(0)

def main():
    """
    Main function to run the enhanced monitoring system.
    """
    parser = argparse.ArgumentParser(description='Run Enhanced Monitoring System for ArbitrageX')
    parser.add_argument('--metrics-dir', type=str, default='backend/ai/metrics', help='Directory to store metrics')
    parser.add_argument('--alert-config', type=str, default='backend/ai/config/alert_config.json', help='Path to alert configuration file')
    parser.add_argument('--save-interval', type=int, default=300, help='Interval in seconds to save metrics')
    parser.add_argument('--monitor-interval', type=int, default=60, help='Interval in seconds to monitor system resources')
    
    args = parser.parse_args()
    
    # Create metrics directory if it doesn't exist
    os.makedirs(args.metrics_dir, exist_ok=True)
    
    # Create alert config directory if it doesn't exist
    os.makedirs(os.path.dirname(args.alert_config), exist_ok=True)
    
    # Create enhanced monitoring system
    global monitoring_system
    monitoring_system = EnhancedMonitoring(
        metrics_dir=args.metrics_dir,
        alert_config_path=args.alert_config,
        save_interval_seconds=args.save_interval,
        monitor_interval_seconds=args.monitor_interval
    )
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start monitoring system
        monitoring_system.start()
        logger.info(f"Enhanced monitoring system started (save interval: {args.save_interval}s, monitor interval: {args.monitor_interval}s)")
        
        # Log sample trade for testing
        sample_trade = {
            "trade_id": "test_trade_001",
            "success": True,
            "profit_usd": 10.0,
            "gas_cost_usd": 2.0,
            "net_profit_usd": 8.0,
            "execution_time_ms": 150.0,
            "network": "ethereum",
            "token_in": "WETH",
            "token_out": "USDC",
            "dex": "uniswap_v3",
            "timestamp": int(time.time())
        }
        monitoring_system.log_trade(sample_trade)
        logger.info("Logged sample trade for testing")
        
        # Log sample ML update for testing
        sample_ml_update = {
            "model_updates": 1,
            "strategy_adaptations": 1,
            "prediction_accuracy": 0.85
        }
        monitoring_system.log_ml_update(sample_ml_update)
        logger.info("Logged sample ML update for testing")
        
        # Run indefinitely
        logger.info("Monitoring system running, press Ctrl+C to stop")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        # Stop monitoring system
        monitoring_system.stop()
        logger.info("Enhanced monitoring system stopped")

if __name__ == "__main__":
    # Initialize global monitoring system
    monitoring_system = None
    
    # Run main function
    main() 