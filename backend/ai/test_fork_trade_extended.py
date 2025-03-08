"""
Extended Test Fork Trade Script

This script runs an extended test of the ArbitrageX bot on a forked mainnet,
with enhanced monitoring and learning loop integration.
"""

import os
import sys
import json
import logging
import time
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add the parent directory to the Python path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_fork_trade_extended.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TestForkTradeExtended")

# Import the required modules
from backend.ai.web3_connector import Web3Connector
from backend.ai.strategy_optimizer import StrategyOptimizer
from backend.ai.enhanced_monitoring import EnhancedMonitoring
from backend.ai.learning_loop import LearningLoop
from backend.ai.system_monitor import SystemMonitor

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run an extended test of ArbitrageX on a forked mainnet")
    
    parser.add_argument("--trades", type=int, default=10,
                        help="Number of trades to execute (default: 10)")
    
    parser.add_argument("--interval", type=int, default=5,
                        help="Interval between trades in seconds (default: 5)")
    
    parser.add_argument("--fork-config", type=str, default="backend/ai/hardhat_fork_config.json",
                        help="Path to the fork configuration file")
    
    parser.add_argument("--metrics-dir", type=str, default="backend/ai/metrics",
                        help="Directory to store metrics")
    
    parser.add_argument("--results-dir", type=str, default="backend/ai/results",
                        help="Directory to store results")
    
    # Add these arguments to avoid conflicts with existing code
    parser.add_argument("--market-data", type=str, help=argparse.SUPPRESS)
    parser.add_argument("--mainnet-fork", type=str, help=argparse.SUPPRESS)
    parser.add_argument("--testnet", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--version", action="store_true", help=argparse.SUPPRESS)
    
    return parser.parse_args()

def test_fork_connection(fork_config_path):
    """Test the connection to the Hardhat fork."""
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
    """Initialize all components for the test."""
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
        save_interval_seconds=60,  # Save metrics every minute
        monitor_interval_seconds=30  # Monitor system every 30 seconds
    )
    
    # Initialize LearningLoop
    learning_loop = LearningLoop(
        results_dir=args.results_dir
    )
    
    logger.info("Components initialized successfully")
    return connector, optimizer, monitoring, learning_loop

def generate_trade_opportunity(fork_config):
    """Generate a realistic trade opportunity based on current market conditions."""
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
    """Execute a trade using the StrategyOptimizer."""
    logger.info(f"Executing trade: {opportunity['token_in']} -> {opportunity['token_out']}")
    
    # Predict the opportunity
    prediction = optimizer.predict_opportunity(opportunity)
    logger.info(f"Opportunity prediction: {json.dumps(prediction, indent=2)}")
    
    # Execute the opportunity if it's profitable
    if prediction.get("is_profitable", False):
        logger.info("Executing the opportunity...")
        result = optimizer.execute_opportunity(opportunity)
        logger.info(f"Execution result: {json.dumps(result, indent=2)}")
        
        # Log the trade
        monitoring.log_trade(result)
        
        # Add to learning loop
        learning_loop.add_execution_result(result)
        
        return result
    else:
        logger.info("Opportunity not profitable, skipping execution")
        
        # Create a failed trade result for monitoring
        result = {
            "success": False,
            "reason": "Not profitable",
            "profit": 0.0,
            "gas_used": 0,
            "execution_time_ms": prediction.get("execution_time_ms", 0),
            "timestamp": int(time.time())
        }
        
        # Log the failed trade
        monitoring.log_trade(result)
        
        return result

def run_learning_loop_iteration(learning_loop, monitoring):
    """Run one iteration of the learning loop."""
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

def main():
    """Main function to run the extended test."""
    logger.info("Starting extended fork trade test...")
    
    # Parse arguments
    args = parse_arguments()
    
    # Initialize components
    connector, optimizer, monitoring, learning_loop = initialize_components(args)
    if not connector or not optimizer or not monitoring or not learning_loop:
        logger.error("Failed to initialize components")
        return
    
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
        
        # Run for the specified number of trades
        for i in range(args.trades):
            logger.info(f"Trade {i+1}/{args.trades}")
            
            # Generate and execute trade
            opportunity = generate_trade_opportunity(fork_config)
            result = execute_trade(optimizer, opportunity, monitoring, learning_loop)
            
            # Update metrics
            total_trades += 1
            if result.get("success", False):
                successful_trades += 1
                total_profit += result.get("profit", 0.0)
            
            # Run learning loop every 5 trades
            if (i + 1) % 5 == 0:
                run_learning_loop_iteration(learning_loop, monitoring)
            
            # Log system metrics
            system_metrics = SystemMonitor.get_system_metrics()
            monitoring.log_system_metrics(system_metrics)
            
            # Save metrics
            monitoring.metrics.save_metrics()
            
            # Add some delay between trades
            if i < args.trades - 1:  # Don't delay after the last trade
                logger.info(f"Waiting {args.interval} seconds before next trade...")
                time.sleep(args.interval)
        
        # Run final learning loop iteration
        run_learning_loop_iteration(learning_loop, monitoring)
        
        # Generate final report
        metrics = monitoring.get_metrics_summary()
        
        # Save final report
        report_path = f"{args.results_dir}/test_report.json"
        with open(report_path, 'w') as f:
            json.dump({
                "total_trades": total_trades,
                "successful_trades": successful_trades,
                "success_rate": (successful_trades / total_trades * 100) if total_trades > 0 else 0,
                "total_profit": total_profit,
                "start_time": datetime.now().isoformat(),
                "metrics": metrics
            }, f, indent=2)
        
        logger.info(f"Test report saved to {report_path}")
        
        # Print summary
        logger.info("=== Test Summary ===")
        logger.info(f"Total Trades: {total_trades}")
        logger.info(f"Successful Trades: {successful_trades}")
        logger.info(f"Success Rate: {(successful_trades / total_trades * 100) if total_trades > 0 else 0:.2f}%")
        logger.info(f"Total Profit: ${total_profit:.2f}")
        
    except Exception as e:
        logger.exception(f"Error during test: {e}")
        
    finally:
        # Stop monitoring
        monitoring.stop()
        
        # Stop learning loop
        learning_loop.stop()
        
        logger.info("Extended fork trade test completed")

if __name__ == "__main__":
    main() 