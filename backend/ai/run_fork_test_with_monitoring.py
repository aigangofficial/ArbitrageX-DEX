#!/usr/bin/env python3
"""
ArbitrageX Forked Mainnet Test with Monitoring

This script runs a test of the ArbitrageX bot on a forked mainnet with
enhanced monitoring and learning loop integration.
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fork_test_with_monitoring.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ForkTestWithMonitoring")

# Add the parent directory to the Python path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
from backend.ai.enhanced_monitoring import EnhancedMonitoring
from backend.ai.web3_connector import Web3Connector
from backend.ai.strategy_optimizer import StrategyOptimizer
from backend.ai.learning_loop import LearningLoop
from backend.ai.system_monitor import SystemMonitor

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Run ArbitrageX on a forked mainnet with monitoring")
    
    parser.add_argument("--duration", type=int, default=24,
                        help="Duration of the test in hours (default: 24)")
    
    parser.add_argument("--trades", type=int, default=10,
                        help="Number of trades to execute per hour (default: 10)")
    
    parser.add_argument("--fork-config", type=str, default="backend/ai/hardhat_fork_config.json",
                        help="Path to the fork configuration file")
    
    parser.add_argument("--metrics-dir", type=str, default="backend/ai/metrics/fork_test",
                        help="Directory to store metrics")
    
    parser.add_argument("--results-dir", type=str, default="backend/ai/results/fork_test",
                        help="Directory to store results")
    
    return parser.parse_args()

def test_fork_connection(fork_config_path):
    """
    Test the connection to the Hardhat fork.
    
    Args:
        fork_config_path: Path to the fork configuration file
        
    Returns:
        Web3Connector: The initialized Web3Connector
    """
    logger.info("Testing connection to Hardhat fork...")
    
    # Initialize the Web3Connector with the fork configuration
    connector = Web3Connector(fork_config_path)
    
    # Check if connected
    if connector.is_connected():
        logger.info(f"Successfully connected to Hardhat fork at block {connector.web3.eth.block_number}")
        return connector
    else:
        logger.error("Failed to connect to Hardhat fork")
        return None

def initialize_components(args):
    """
    Initialize all components for the test.
    
    Args:
        args: Command line arguments
        
    Returns:
        tuple: (Web3Connector, StrategyOptimizer, EnhancedMonitoring, LearningLoop)
    """
    logger.info("Initializing components...")
    
    # Create directories
    os.makedirs(args.metrics_dir, exist_ok=True)
    os.makedirs(args.results_dir, exist_ok=True)
    
    # Initialize Web3Connector
    connector = test_fork_connection(args.fork_config)
    if not connector:
        logger.error("Failed to initialize Web3Connector")
        return None, None, None, None
    
    # Initialize StrategyOptimizer
    optimizer = StrategyOptimizer(fork_config_path=args.fork_config)
    
    # Initialize EnhancedMonitoring
    monitoring = EnhancedMonitoring(
        metrics_dir=args.metrics_dir,
        save_interval_seconds=300,  # Save metrics every 5 minutes
        monitor_interval_seconds=60  # Monitor system every minute
    )
    
    # Initialize LearningLoop
    learning_loop = LearningLoop(
        results_dir=args.results_dir
    )
    
    logger.info("Components initialized successfully")
    return connector, optimizer, monitoring, learning_loop

def generate_trade_opportunity(fork_config):
    """
    Generate a realistic trade opportunity based on current market conditions.
    
    Args:
        fork_config: The fork configuration
        
    Returns:
        Dict: A trade opportunity
    """
    # Get available token pairs from the fork config
    networks = fork_config.get("networks", ["ethereum"])
    network = networks[0]  # Use the first network
    
    tokens = fork_config.get("tokens", {}).get(network, ["WETH", "USDC"])
    dexes = fork_config.get("dexes", {}).get(network, ["uniswap_v3"])
    
    # Create a sample trade opportunity
    opportunity = {
        "network": network,
        "token_in": "WETH",
        "token_out": "USDC",
        "amount_in": 1.0,  # 1 WETH
        "estimated_profit": 0.01 + (0.02 * (time.time() % 100) / 100),  # 1-3% profit
        "route": [
            {"dex": dexes[0], "token_in": "WETH", "token_out": "USDC"},
            {"dex": dexes[-1] if len(dexes) > 1 else dexes[0], "token_in": "USDC", "token_out": "WETH"}
        ],
        "gas_estimate": 200000 + int(100000 * (time.time() % 100) / 100),  # 200K-300K gas
        "execution_priority": "high",
        "slippage_tolerance": 0.005,
        "timestamp": int(time.time())
    }
    
    return opportunity

def execute_trade(optimizer, opportunity, monitoring, learning_loop):
    """
    Execute a trade using the StrategyOptimizer.
    
    Args:
        optimizer: The StrategyOptimizer
        opportunity: The trade opportunity to execute
        monitoring: The EnhancedMonitoring instance
        learning_loop: The LearningLoop instance
        
    Returns:
        Dict: The execution result
    """
    logger.info(f"Executing trade: {opportunity['token_in']} -> {opportunity['token_out']}")
    
    # Predict the opportunity
    prediction = optimizer.predict_opportunity(opportunity)
    
    # Execute the opportunity if it's profitable
    if prediction.get("is_profitable", False):
        result = optimizer.execute_opportunity(opportunity)
        
        # Log the trade
        monitoring.log_trade(result)
        
        # Add to learning loop
        learning_loop.add_execution_result(result)
        
        return result
    else:
        logger.info("Opportunity not profitable, skipping execution")
        return {"success": False, "reason": "Not profitable"}

def run_learning_loop_iteration(learning_loop, monitoring):
    """
    Run one iteration of the learning loop.
    
    Args:
        learning_loop: The LearningLoop instance
        monitoring: The EnhancedMonitoring instance
    """
    logger.info("Running learning loop iteration...")
    
    # Process execution results
    learning_loop._process_execution_results()
    
    # Check and update models
    learning_loop._check_and_update_models()
    
    # Check and adapt strategies
    learning_loop._check_and_adapt_strategies()
    
    # Get learning stats
    stats = learning_loop.get_learning_stats()
    logger.info(f"Learning stats: {json.dumps(stats, indent=2)}")
    
    # Log ML update
    monitoring.log_ml_update({
        "model_updates": stats.get("model_updates", 0),
        "strategy_adaptations": stats.get("strategy_adaptations", 0),
        "prediction_accuracy": stats.get("prediction_accuracy", 0.0)
    })

def run_test(args):
    """
    Run the forked mainnet test with monitoring.
    
    Args:
        args: Command line arguments
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Starting forked mainnet test for {args.duration} hours with {args.trades} trades per hour...")
    
    # Initialize components
    connector, optimizer, monitoring, learning_loop = initialize_components(args)
    if not connector or not optimizer or not monitoring or not learning_loop:
        logger.error("Failed to initialize components")
        return False
    
    # Load fork configuration
    with open(args.fork_config, 'r') as f:
        fork_config = json.load(f)
    
    # Start monitoring
    monitoring.start()
    
    # Start learning loop
    learning_loop.start()
    
    try:
        # Track metrics
        total_trades = 0
        successful_trades = 0
        total_profit = 0.0
        
        # Run for the specified duration
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=args.duration)
        
        logger.info(f"Test started at {start_time.isoformat()}")
        logger.info(f"Test will end at {end_time.isoformat()}")
        
        # Main test loop
        current_hour = 0
        while datetime.now() < end_time:
            logger.info(f"Hour {current_hour + 1}: Executing {args.trades} trades...")
            
            # Execute trades for this hour
            for i in range(args.trades):
                # Generate and execute trade
                opportunity = generate_trade_opportunity(fork_config)
                result = execute_trade(optimizer, opportunity, monitoring, learning_loop)
                
                # Update metrics
                total_trades += 1
                if result.get("success", False):
                    successful_trades += 1
                    total_profit += result.get("profit", 0.0)
                
                # Add some delay between trades
                time.sleep(1)
            
            # Run learning loop every 4 hours
            if current_hour % 4 == 0:
                run_learning_loop_iteration(learning_loop, monitoring)
            
            # Log system metrics
            system_metrics = SystemMonitor.get_system_metrics()
            monitoring.log_system_metrics(system_metrics)
            
            # Save metrics
            monitoring.metrics.save_metrics()
            
            # Update progress
            current_hour += 1
            elapsed = datetime.now() - start_time
            remaining = end_time - datetime.now()
            
            logger.info(f"Progress: {elapsed.total_seconds() / (args.duration * 3600) * 100:.2f}%")
            logger.info(f"Elapsed time: {elapsed}")
            logger.info(f"Remaining time: {remaining}")
            logger.info(f"Trades executed: {total_trades}")
            logger.info(f"Successful trades: {successful_trades}")
            logger.info(f"Total profit: ${total_profit:.2f}")
            
            # Add some delay between hours (but don't delay if we're behind schedule)
            time_per_hour = timedelta(hours=args.duration) / args.duration
            next_hour_time = start_time + (current_hour * time_per_hour)
            if datetime.now() < next_hour_time:
                time.sleep((next_hour_time - datetime.now()).total_seconds())
        
        # Generate final report
        metrics = monitoring.get_metrics_summary()
        
        # Save final report
        report_path = f"{args.results_dir}/test_report.json"
        with open(report_path, 'w') as f:
            json.dump({
                "duration_hours": args.duration,
                "trades_per_hour": args.trades,
                "total_trades": total_trades,
                "successful_trades": successful_trades,
                "success_rate": (successful_trades / total_trades * 100) if total_trades > 0 else 0,
                "total_profit": total_profit,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "metrics": metrics
            }, f, indent=2)
        
        logger.info(f"Test report saved to {report_path}")
        
        # Print summary
        logger.info("=== Test Summary ===")
        logger.info(f"Duration: {args.duration} hours")
        logger.info(f"Total Trades: {total_trades}")
        logger.info(f"Successful Trades: {successful_trades}")
        logger.info(f"Success Rate: {(successful_trades / total_trades * 100) if total_trades > 0 else 0:.2f}%")
        logger.info(f"Total Profit: ${total_profit:.2f}")
        
        return True
        
    except Exception as e:
        logger.exception(f"Error during test: {e}")
        return False
        
    finally:
        # Stop monitoring
        monitoring.stop()
        
        # Stop learning loop
        learning_loop.stop()
        
        logger.info("Test completed")

def main():
    """
    Main function to run the test.
    """
    # Parse arguments
    args = parse_arguments()
    
    # Run test
    success = run_test(args)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 