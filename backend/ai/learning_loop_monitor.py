#!/usr/bin/env python3
"""
Learning Loop Monitor

This script provides detailed monitoring and diagnostics for the ArbitrageX learning loop.
It can be used to check the status of the learning loop, view detailed statistics,
and diagnose issues with the learning process.
"""

import os
import sys
import json
import time
import argparse
import logging
import psutil
from datetime import datetime, timedelta
from tabulate import tabulate

# Add the parent directory to the path so we can import the learning_loop module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.learning_loop import LearningLoop

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("learning_loop_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LearningLoopMonitor")

def check_learning_loop_status():
    """Check if the learning loop is running and get its status."""
    status_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "learning_loop_status.json")
    
    if not os.path.exists(status_file):
        logger.error("Learning loop status file not found. Is the learning loop running?")
        return None
    
    try:
        with open(status_file, 'r') as f:
            status_data = json.load(f)
        
        # Check if the process is still running
        pid = status_data.get("pid")
        if pid and not psutil.pid_exists(pid):
            logger.error(f"Learning loop process (PID {pid}) is not running, but status file exists.")
            return {**status_data, "process_running": False}
        
        return {**status_data, "process_running": True}
    except Exception as e:
        logger.error(f"Error reading learning loop status file: {e}")
        return None

def get_learning_loop_stats():
    """Get detailed statistics from the learning loop."""
    try:
        # Try to create a learning loop instance to get stats
        learning_loop = LearningLoop()
        stats = learning_loop.get_learning_stats()
        
        # Get model performance metrics
        performance = learning_loop.get_model_performance()
        
        # Get validation stats if available
        validation_stats = {}
        if hasattr(learning_loop, 'get_validation_stats'):
            validation_stats = learning_loop.get_validation_stats()
        
        return {
            "stats": stats,
            "performance": performance,
            "validation": validation_stats
        }
    except Exception as e:
        logger.error(f"Error getting learning loop stats: {e}")
        return None

def check_historical_results():
    """Check the historical execution results file."""
    try:
        # Try to find the historical results file
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        results_file = os.path.join(data_dir, "historical_execution_results.json")
        
        if not os.path.exists(results_file):
            logger.warning(f"Historical results file not found at {results_file}")
            return None
        
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        # Analyze the results
        total_results = len(results)
        
        # Count results by status
        status_counts = {}
        for result in results:
            status = result.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count results by network
        network_counts = {}
        for result in results:
            network = result.get("network", "unknown")
            network_counts[network] = network_counts.get(network, 0) + 1
        
        # Calculate average profit
        total_profit = 0
        profit_count = 0
        for result in results:
            if "actual_profit" in result:
                total_profit += result["actual_profit"]
                profit_count += 1
        
        avg_profit = total_profit / profit_count if profit_count > 0 else 0
        
        return {
            "total_results": total_results,
            "status_counts": status_counts,
            "network_counts": network_counts,
            "avg_profit": avg_profit,
            "file_size": os.path.getsize(results_file),
            "last_modified": datetime.fromtimestamp(os.path.getmtime(results_file)).isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking historical results: {e}")
        return None

def check_model_files():
    """Check the model files in the models directory."""
    try:
        models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
        
        if not os.path.exists(models_dir):
            logger.warning(f"Models directory not found at {models_dir}")
            return None
        
        model_files = []
        for root, dirs, files in os.walk(models_dir):
            for file in files:
                if file.endswith(".pkl") or file.endswith(".h5") or file.endswith(".joblib"):
                    file_path = os.path.join(root, file)
                    model_files.append({
                        "name": file,
                        "path": file_path,
                        "size": os.path.getsize(file_path),
                        "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })
        
        return model_files
    except Exception as e:
        logger.error(f"Error checking model files: {e}")
        return None

def display_status(status_data):
    """Display the learning loop status in a formatted way."""
    if not status_data:
        print("No status data available.")
        return
    
    print("\n=== Learning Loop Status ===")
    print(f"Status: {status_data.get('status', 'unknown')}")
    print(f"Process Running: {'Yes' if status_data.get('process_running', False) else 'No'}")
    print(f"PID: {status_data.get('pid', 'unknown')}")
    print(f"Started At: {status_data.get('started_at', 'unknown')}")
    print(f"Last Updated: {status_data.get('last_updated', 'unknown')}")
    
    stats = status_data.get('stats', {})
    if stats:
        print("\n=== Learning Statistics ===")
        print(f"Running: {'Yes' if stats.get('is_running', False) else 'No'}")
        print(f"Queue Size: {stats.get('queue_size', 0)}")
        print(f"Model Update Queue Size: {stats.get('model_update_queue_size', 0)}")
        print(f"Historical Results Count: {stats.get('historical_results_count', 0)}")
        print(f"Successful Model Updates: {stats.get('successful_model_updates', 0)}")
        print(f"Failed Model Updates: {stats.get('failed_model_updates', 0)}")
        print(f"Strategy Adaptations: {stats.get('strategy_adaptations', 0)}")
        
        if 'next_model_update' in stats:
            next_update = datetime.fromisoformat(stats['next_model_update'])
            now = datetime.now()
            time_until_update = next_update - now
            print(f"Next Model Update: {stats['next_model_update']} ({time_until_update.total_seconds():.0f} seconds)")
        
        if 'next_strategy_adaptation' in stats:
            next_adaptation = datetime.fromisoformat(stats['next_strategy_adaptation'])
            now = datetime.now()
            time_until_adaptation = next_adaptation - now
            print(f"Next Strategy Adaptation: {stats['next_strategy_adaptation']} ({time_until_adaptation.total_seconds():.0f} seconds)")

def display_detailed_stats(stats_data):
    """Display detailed learning loop statistics."""
    if not stats_data:
        print("No detailed statistics available.")
        return
    
    stats = stats_data.get('stats', {})
    performance = stats_data.get('performance', {})
    validation = stats_data.get('validation', {})
    
    print("\n=== Detailed Learning Statistics ===")
    print(f"Queue Size: {stats.get('queue_size', 0)}")
    print(f"Model Update Queue Size: {stats.get('model_update_queue_size', 0)}")
    print(f"Historical Results Count: {stats.get('historical_results_count', 0)}")
    print(f"Successful Model Updates: {stats.get('successful_model_updates', 0)}")
    print(f"Failed Model Updates: {stats.get('failed_model_updates', 0)}")
    print(f"Strategy Adaptations: {stats.get('strategy_adaptations', 0)}")
    
    if performance:
        print("\n=== Model Performance ===")
        for model_name, metrics in performance.items():
            print(f"\nModel: {model_name}")
            
            for metric_name, values in metrics.items():
                if values and len(values) > 0:
                    latest_value = values[-1]['value']
                    print(f"  {metric_name.upper()}: {latest_value:.4f}")
    
    if validation:
        print("\n=== Validation Statistics ===")
        for key, value in validation.items():
            if isinstance(value, dict):
                print(f"\n{key.replace('_', ' ').title()}:")
                for subkey, subvalue in value.items():
                    print(f"  {subkey.replace('_', ' ').title()}: {subvalue}")
            else:
                print(f"{key.replace('_', ' ').title()}: {value}")

def display_historical_results(results_data):
    """Display information about historical execution results."""
    if not results_data:
        print("No historical results data available.")
        return
    
    print("\n=== Historical Execution Results ===")
    print(f"Total Results: {results_data.get('total_results', 0)}")
    print(f"File Size: {results_data.get('file_size', 0) / 1024:.2f} KB")
    print(f"Last Modified: {results_data.get('last_modified', 'unknown')}")
    
    status_counts = results_data.get('status_counts', {})
    if status_counts:
        print("\nStatus Counts:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
    
    network_counts = results_data.get('network_counts', {})
    if network_counts:
        print("\nNetwork Counts:")
        for network, count in network_counts.items():
            print(f"  {network}: {count}")
    
    print(f"\nAverage Profit: {results_data.get('avg_profit', 0):.6f}")

def display_model_files(model_files):
    """Display information about model files."""
    if not model_files:
        print("No model files found.")
        return
    
    print("\n=== Model Files ===")
    table_data = []
    for model in model_files:
        table_data.append([
            model['name'],
            f"{model['size'] / 1024:.2f} KB",
            model['last_modified']
        ])
    
    print(tabulate(table_data, headers=["Name", "Size", "Last Modified"], tablefmt="grid"))

def main():
    """Main function to run the learning loop monitor."""
    parser = argparse.ArgumentParser(description="Monitor the ArbitrageX Learning Loop")
    parser.add_argument("--status", action="store_true", help="Check the learning loop status")
    parser.add_argument("--stats", action="store_true", help="Get detailed learning loop statistics")
    parser.add_argument("--historical", action="store_true", help="Check historical execution results")
    parser.add_argument("--models", action="store_true", help="Check model files")
    parser.add_argument("--all", action="store_true", help="Show all information")
    parser.add_argument("--watch", action="store_true", help="Watch the learning loop status in real-time")
    parser.add_argument("--interval", type=int, default=5, help="Update interval for watch mode (seconds)")
    args = parser.parse_args()
    
    # If no specific options are provided, show status by default
    if not (args.status or args.stats or args.historical or args.models or args.all or args.watch):
        args.status = True
    
    # Watch mode
    if args.watch:
        try:
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')
                print(f"=== Learning Loop Monitor (Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
                
                status_data = check_learning_loop_status()
                display_status(status_data)
                
                if args.all or args.stats:
                    stats_data = get_learning_loop_stats()
                    display_detailed_stats(stats_data)
                
                if args.all or args.historical:
                    results_data = check_historical_results()
                    display_historical_results(results_data)
                
                if args.all or args.models:
                    model_files = check_model_files()
                    display_model_files(model_files)
                
                print(f"\nPress Ctrl+C to exit. Updating every {args.interval} seconds...")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nMonitor stopped.")
    else:
        # One-time display
        if args.all or args.status:
            status_data = check_learning_loop_status()
            display_status(status_data)
        
        if args.all or args.stats:
            stats_data = get_learning_loop_stats()
            display_detailed_stats(stats_data)
        
        if args.all or args.historical:
            results_data = check_historical_results()
            display_historical_results(results_data)
        
        if args.all or args.models:
            model_files = check_model_files()
            display_model_files(model_files)

if __name__ == "__main__":
    main() 