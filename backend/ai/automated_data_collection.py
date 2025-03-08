#!/usr/bin/env python3
"""
Automated Data Collection Script

This script automates the process of collecting data for the ArbitrageX learning loop.
It can generate simulated trades, fetch real trading data from the forked mainnet,
and ensure the learning loop has a continuous stream of data to learn from.
"""

import os
import sys
import time
import json
import random
import logging
import argparse
import schedule
from datetime import datetime, timedelta
import requests

# Add the parent directory to the path so we can import the learning_loop module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.learning_loop import LearningLoop
from ai.simulate_trades import generate_random_trade

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_collection.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DataCollection")

class DataCollector:
    """Class for collecting data for the learning loop."""
    
    def __init__(self, config=None):
        """Initialize the data collector."""
        self.config = config or {}
        self.learning_loop = LearningLoop()
        self.api_base_url = self.config.get('api_base_url', 'http://localhost:3002')
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        logger.info("Data collector initialized")
    
    def collect_simulated_trades(self, count=10, variation='normal'):
        """
        Generate and collect simulated trades.
        
        Args:
            count: Number of trades to generate
            variation: Variation level ('low', 'normal', 'high')
        """
        logger.info(f"Generating {count} simulated trades with {variation} variation")
        
        for i in range(count):
            # Generate a random trade
            trade = generate_random_trade()
            
            # Apply variation
            if variation == 'high':
                # High variation: more extreme values
                trade['expected_profit'] *= random.uniform(0.5, 2.0)
                trade['actual_profit'] *= random.uniform(0.5, 2.0)
                trade['gas_price'] *= random.uniform(0.5, 2.0)
                trade['gas_used'] *= random.uniform(0.8, 1.2)
            elif variation == 'low':
                # Low variation: more consistent values
                trade['expected_profit'] *= random.uniform(0.9, 1.1)
                trade['actual_profit'] *= random.uniform(0.9, 1.1)
                trade['gas_price'] *= random.uniform(0.9, 1.1)
                trade['gas_used'] *= random.uniform(0.95, 1.05)
            
            # Add the trade to the learning loop
            self.learning_loop.add_execution_result(trade)
            
            logger.debug(f"Added simulated trade {i+1}/{count} to learning loop: {trade['opportunity_id']}")
            
            # Sleep for a random time to simulate real-world timing
            time.sleep(random.uniform(0.1, 0.5))
        
        logger.info(f"Completed generation of {count} simulated trades")
    
    def collect_real_trades(self, limit=10):
        """
        Collect real trades from the API.
        
        Args:
            limit: Maximum number of trades to collect
        """
        logger.info(f"Collecting up to {limit} real trades from API")
        
        try:
            # Fetch trades from the API
            response = requests.get(f"{self.api_base_url}/api/v1/trades?limit={limit}")
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch trades from API: {response.status_code}")
                return
            
            trades = response.json().get('trades', [])
            logger.info(f"Fetched {len(trades)} trades from API")
            
            for trade in trades:
                # Convert the trade to the format expected by the learning loop
                execution_result = {
                    'opportunity_id': trade.get('_id', f"api_{int(time.time())}_{random.randint(1000, 9999)}"),
                    'network': 'ethereum',  # Assuming all trades are on Ethereum
                    'token_pair': [trade.get('tokenIn', 'unknown'), trade.get('tokenOut', 'unknown')],
                    'dex': trade.get('router', 'unknown'),
                    'amount_in': float(trade.get('amountIn', 0)),
                    'amount_out': float(trade.get('amountOut', 0)),
                    'expected_profit': float(trade.get('profit', 0)),
                    'actual_profit': float(trade.get('profit', 0)),
                    'gas_price': float(trade.get('gasPrice', 0)),
                    'gas_used': float(trade.get('gasUsed', 0)),
                    'gas_cost': float(trade.get('gasPrice', 0)) * float(trade.get('gasUsed', 0)) * 1e-18,
                    'status': trade.get('status', 'unknown'),
                    'execution_time': 500,  # Placeholder value
                    'timestamp': trade.get('timestamp', datetime.now().isoformat())
                }
                
                # Add the trade to the learning loop
                self.learning_loop.add_execution_result(execution_result)
                
                logger.debug(f"Added real trade to learning loop: {execution_result['opportunity_id']}")
            
            logger.info(f"Added {len(trades)} real trades to learning loop")
        except Exception as e:
            logger.error(f"Error collecting real trades: {e}")
    
    def save_collected_data(self, filename=None):
        """
        Save the collected data to a file.
        
        Args:
            filename: Name of the file to save the data to
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"collected_data_{timestamp}.json"
        
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            # Get the historical execution results from the learning loop
            historical_results = self.learning_loop.historical_execution_results
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(historical_results, f, indent=2)
            
            logger.info(f"Saved {len(historical_results)} collected data points to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving collected data: {e}")
            return None
    
    def load_collected_data(self, filepath):
        """
        Load collected data from a file and add it to the learning loop.
        
        Args:
            filepath: Path to the file containing the data
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            logger.info(f"Loaded {len(data)} data points from {filepath}")
            
            for item in data:
                self.learning_loop.add_execution_result(item)
            
            logger.info(f"Added {len(data)} data points to learning loop")
            return len(data)
        except Exception as e:
            logger.error(f"Error loading collected data: {e}")
            return 0
    
    def run_scheduled_collection(self, schedule_config=None):
        """
        Run data collection on a schedule.
        
        Args:
            schedule_config: Configuration for the schedule
        """
        if not schedule_config:
            schedule_config = {
                'simulated_trades': {
                    'interval': 'hour',
                    'count': 20,
                    'variation': 'normal'
                },
                'real_trades': {
                    'interval': 'hour',
                    'limit': 10
                },
                'save_data': {
                    'interval': 'day'
                }
            }
        
        logger.info(f"Setting up scheduled data collection: {schedule_config}")
        
        # Schedule simulated trades collection
        sim_config = schedule_config.get('simulated_trades', {})
        sim_interval = sim_config.get('interval', 'hour')
        sim_count = sim_config.get('count', 20)
        sim_variation = sim_config.get('variation', 'normal')
        
        if sim_interval == 'minute':
            schedule.every().minute.do(self.collect_simulated_trades, count=sim_count, variation=sim_variation)
        elif sim_interval == 'hour':
            schedule.every().hour.do(self.collect_simulated_trades, count=sim_count, variation=sim_variation)
        elif sim_interval == 'day':
            schedule.every().day.at("00:00").do(self.collect_simulated_trades, count=sim_count, variation=sim_variation)
        
        # Schedule real trades collection
        real_config = schedule_config.get('real_trades', {})
        real_interval = real_config.get('interval', 'hour')
        real_limit = real_config.get('limit', 10)
        
        if real_interval == 'minute':
            schedule.every().minute.do(self.collect_real_trades, limit=real_limit)
        elif real_interval == 'hour':
            schedule.every().hour.do(self.collect_real_trades, limit=real_limit)
        elif real_interval == 'day':
            schedule.every().day.at("00:00").do(self.collect_real_trades, limit=real_limit)
        
        # Schedule data saving
        save_config = schedule_config.get('save_data', {})
        save_interval = save_config.get('interval', 'day')
        
        if save_interval == 'hour':
            schedule.every().hour.do(self.save_collected_data)
        elif save_interval == 'day':
            schedule.every().day.at("00:00").do(self.save_collected_data)
        
        logger.info("Scheduled data collection started")
        
        # Run the schedule
        while True:
            schedule.run_pending()
            time.sleep(1)

def main():
    """Main function to run the data collector."""
    parser = argparse.ArgumentParser(description="Collect data for the ArbitrageX learning loop")
    parser.add_argument("--simulated", type=int, help="Generate and collect simulated trades")
    parser.add_argument("--variation", choices=['low', 'normal', 'high'], default='normal', help="Variation level for simulated trades")
    parser.add_argument("--real", type=int, help="Collect real trades from the API")
    parser.add_argument("--save", action="store_true", help="Save collected data to a file")
    parser.add_argument("--load", type=str, help="Load collected data from a file")
    parser.add_argument("--schedule", action="store_true", help="Run data collection on a schedule")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    args = parser.parse_args()
    
    # Load configuration if provided
    config = None
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Error loading configuration file: {e}")
    
    # Create data collector
    collector = DataCollector(config)
    
    # Process command line arguments
    if args.simulated:
        collector.collect_simulated_trades(count=args.simulated, variation=args.variation)
    
    if args.real:
        collector.collect_real_trades(limit=args.real)
    
    if args.load:
        collector.load_collected_data(args.load)
    
    if args.save:
        collector.save_collected_data()
    
    if args.schedule:
        collector.run_scheduled_collection()
    
    # If no specific action is requested, print help
    if not (args.simulated or args.real or args.load or args.save or args.schedule):
        parser.print_help()

if __name__ == "__main__":
    main() 