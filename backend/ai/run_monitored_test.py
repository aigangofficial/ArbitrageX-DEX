"""
Run Monitored Comprehensive Test for ArbitrageX

This script runs a comprehensive test for the ArbitrageX system with enhanced monitoring.
"""

import os
import sys
import time
import logging
import argparse
import threading
import signal
from typing import Dict, Any

# Add the parent directory to the Python path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("monitored_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MonitoredTest")

# Import required modules
from backend.ai.run_comprehensive_test import ComprehensiveTest
from backend.ai.enhanced_monitoring import EnhancedMonitoring

def signal_handler(sig, frame):
    """
    Signal handler for graceful shutdown.
    """
    logger.info("Received shutdown signal, stopping...")
    global test_instance, monitoring_system
    if test_instance:
        test_instance.stop_event.set()
    if monitoring_system:
        monitoring_system.stop()
    sys.exit(0)

def main():
    """
    Main function to run the monitored comprehensive test.
    """
    # Create a new argument parser
    parser = argparse.ArgumentParser(description='Run Monitored Comprehensive Test for ArbitrageX')
    parser.add_argument('--duration', type=int, default=3600, help='Test duration in seconds')
    parser.add_argument('--networks', type=str, default='ethereum', help='Comma-separated list of networks to test')
    parser.add_argument('--token-pairs', type=str, default='WETH-USDC', help='Comma-separated list of token pairs to test')
    parser.add_argument('--dexes', type=str, default='uniswap_v3,sushiswap', help='Comma-separated list of DEXes to test')
    parser.add_argument('--fork-config', type=str, default='backend/ai/hardhat_fork_config.json', help='Path to fork configuration file')
    parser.add_argument('--results-dir', type=str, default='backend/ai/results/comprehensive_test', help='Directory to store test results')
    parser.add_argument('--metrics-dir', type=str, default='backend/ai/metrics', help='Directory to store metrics')
    parser.add_argument('--alert-config', type=str, default='backend/ai/config/alert_config.json', help='Path to alert configuration file')
    parser.add_argument('--save-interval', type=int, default=300, help='Interval in seconds to save metrics')
    parser.add_argument('--monitor-interval', type=int, default=60, help='Interval in seconds to monitor system resources')
    
    args = parser.parse_args()
    
    # Parse arguments
    networks = args.networks.split(',')
    token_pairs = args.token_pairs.split(',')
    dexes = args.dexes.split(',')
    
    # Create directories if they don't exist
    os.makedirs(args.results_dir, exist_ok=True)
    os.makedirs(args.metrics_dir, exist_ok=True)
    os.makedirs(os.path.dirname(args.alert_config), exist_ok=True)
    
    # Create enhanced monitoring system
    global monitoring_system
    monitoring_system = EnhancedMonitoring(
        metrics_dir=args.metrics_dir,
        alert_config_path=args.alert_config,
        save_interval_seconds=args.save_interval,
        monitor_interval_seconds=args.monitor_interval
    )
    
    # Create comprehensive test
    global test_instance
    test_instance = ComprehensiveTest(
        duration_seconds=args.duration,
        networks=networks,
        token_pairs=token_pairs,
        dexes=dexes,
        fork_config_path=args.fork_config,
        results_dir=args.results_dir
    )
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start monitoring system
        monitoring_system.start()
        logger.info(f"Enhanced monitoring system started (save interval: {args.save_interval}s, monitor interval: {args.monitor_interval}s)")
        
        # Create and start test thread
        test_thread = threading.Thread(target=test_instance.run_test)
        test_thread.daemon = True
        test_thread.start()
        
        # Wait for test to complete
        test_thread.join()
        
        # Log test completion
        logger.info("Comprehensive test completed")
        
        # Wait for a moment to ensure all metrics are saved
        time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        # Stop monitoring system
        monitoring_system.stop()
        logger.info("Enhanced monitoring system stopped")

if __name__ == "__main__":
    # Initialize global variables
    test_instance = None
    monitoring_system = None
    
    # Run main function
    main() 