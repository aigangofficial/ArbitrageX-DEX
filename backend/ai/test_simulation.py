#!/usr/bin/env python3
"""
Simple Test Simulation for ArbitrageX
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_simulation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TestSimulation")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test simulation for ArbitrageX")
    
    parser.add_argument("--start-date", type=str, default="2025-03-06",
                        help="Start date for the simulation in YYYY-MM-DD format")
    
    parser.add_argument("--end-date", type=str, default="2025-03-07",
                        help="End date for the simulation in YYYY-MM-DD format")
    
    parser.add_argument("--trades-per-day", type=int, default=10,
                        help="Number of trades to simulate per day")
    
    parser.add_argument("--learning-interval", type=int, default=6,
                        help="How often to run the learning loop in hours")
    
    parser.add_argument("--metrics-dir", type=str, default="backend/ai/metrics/test",
                        help="Directory to store metrics")
    
    parser.add_argument("--results-dir", type=str, default="backend/ai/results/test",
                        help="Directory to store results")
    
    parser.add_argument("--synthetic-data", action="store_true",
                        help="Force the use of synthetic data")
    
    return parser.parse_args()

def run_simulation(args):
    """Run a simplified simulation."""
    print(f"Running simulation from {args.start_date} to {args.end_date}")
    print(f"Trades per day: {args.trades_per_day}")
    print(f"Learning interval: {args.learning_interval} hours")
    print(f"Metrics directory: {args.metrics_dir}")
    print(f"Results directory: {args.results_dir}")
    print(f"Using synthetic data: {args.synthetic_data}")
    
    # Create directories
    os.makedirs(args.metrics_dir, exist_ok=True)
    os.makedirs(args.results_dir, exist_ok=True)
    
    # Parse dates
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    
    # Calculate number of days
    num_days = (end_date - start_date).days + 1
    print(f"Total days: {num_days}")
    
    # Simulate trades for each day
    current_date = start_date
    total_trades = 0
    successful_trades = 0
    total_profit = 0.0
    
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        print(f"Simulating trades for {date_str}")
        
        # Simulate trades for this day
        for i in range(args.trades_per_day):
            # Simulate a trade
            success = (i % 3 == 0)  # 33% success rate
            profit = 10.0 if success else 0.0
            
            total_trades += 1
            if success:
                successful_trades += 1
                total_profit += profit
            
            # Simulate trade processing time
            time.sleep(0.1)
        
        # Run learning loop if needed
        if current_date.hour % args.learning_interval == 0:
            print(f"Running learning loop for {date_str}")
            time.sleep(0.5)
        
        # Move to next day
        current_date += timedelta(days=1)
    
    # Generate report
    success_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0
    avg_profit = total_profit / num_days if num_days > 0 else 0
    
    report = {
        "total_trades": total_trades,
        "successful_trades": successful_trades,
        "success_rate": success_rate,
        "total_profit_usd": total_profit,
        "avg_profit_per_day_usd": avg_profit
    }
    
    # Save report
    report_path = os.path.join(args.results_dir, "simulation_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Simulation completed. Report saved to {report_path}")
    print(f"Total trades: {total_trades}")
    print(f"Successful trades: {successful_trades}")
    print(f"Success rate: {success_rate:.2f}%")
    print(f"Total profit: ${total_profit:.2f}")
    print(f"Average profit per day: ${avg_profit:.2f}")
    
    return report

def main():
    """Main function to run the test."""
    args = parse_arguments()
    report = run_simulation(args)
    return 0 if report else 1

if __name__ == "__main__":
    sys.exit(main()) 