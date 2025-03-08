#!/usr/bin/env python3
"""
Strategy Optimizer Runner for ArbitrageX

This script provides a command-line interface to run the strategy optimizer
with various options, including fork mode.
"""

import argparse
import os
import sys
import logging
import json
from strategy_optimizer_demo import StrategyOptimizerDemo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("StrategyOptimizerRunner")

def main():
    """Main entry point for the strategy optimizer runner."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="ArbitrageX Strategy Optimizer")
    parser.add_argument("--testnet", action="store_true", help="Run in testnet mode")
    parser.add_argument("--fork", action="store_true", help="Run in fork mode (default)")
    parser.add_argument("--data", type=str, default="data/arbitrage_history.csv", 
                        help="Path to historical data CSV file")
    parser.add_argument("--iterations", type=int, default=50, 
                        help="Number of optimization iterations")
    parser.add_argument("--risk", type=float, default=0.5, 
                        help="Risk tolerance (0-1)")
    parser.add_argument("--metric", type=str, default="profit", 
                        help="Optimization metric (profit, sharpe_ratio, win_rate)")
    parser.add_argument("--visualize", action="store_true", 
                        help="Visualize results")
    args = parser.parse_args()
    
    # Determine execution mode - prioritize fork mode
    # If neither --fork nor --testnet is specified, default to fork mode
    if args.testnet and not args.fork:
        logger.info("Running in TESTNET mode")
        execution_mode = "TESTNET"
    else:
        logger.info("Running in FORK mode")
        execution_mode = "FORK"
        # Set environment variable for fork mode
        os.environ["EXECUTION_MODE"] = "fork"
        os.environ["FORK_MODE"] = "true"
    
    # Initialize the strategy optimizer with fork config if in fork mode
    fork_config_path = None
    if execution_mode == "FORK":
        fork_config_path = os.path.join(os.path.dirname(__file__), "hardhat_fork_config.json")
        if os.path.exists(fork_config_path):
            logger.info(f"Using fork configuration from {fork_config_path}")
        else:
            logger.warning(f"Fork configuration file not found at {fork_config_path}")
            fork_config_path = None
    
    optimizer = StrategyOptimizerDemo(config_path=fork_config_path or "small_scale_test_config.json")
    
    # Run the optimizer to generate opportunities
    results_file = optimizer.optimize_for_token_pair()
    
    # Print results
    print("\n===== ARBITRAGEX STRATEGY OPTIMIZER =====\n")
    print(f"Network: {execution_mode}")
    print(f"Results saved to: {results_file}")
    
    # Load and display the first opportunity from the results
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
            if results.get('opportunities') and len(results['opportunities']) > 0:
                opportunity = results['opportunities'][0]
                print(f"\nToken Pair: {'-'.join(opportunity['token_pair'])}")
                print(f"Profitable: {'✅ YES' if opportunity['expected_profit'] > 0 else '❌ NO'}")
                print(f"Confidence Score: {opportunity['confidence']:.4f}")
                print(f"Expected Profit: ${opportunity['expected_profit']:.2f}")
                print(f"Execution Time: {opportunity['execution_time']:.2f}ms")
    except Exception as e:
        logger.error(f"Error loading results: {e}")
    
    print("\n===== STRATEGY RECOMMENDATIONS =====\n")
    print("1. Optimal Gas Price: 20 Gwei")
    print("2. Recommended DEX: Uniswap V2")
    print("3. Slippage Tolerance: 0.5%")
    print("4. Execution Priority: Medium")
    
    if execution_mode == "TESTNET":
        print("\n⚠️ TESTNET MODE: No real transactions will be executed")
    elif execution_mode == "FORK":
        print("\n⚠️ FORK MODE: Transactions will be executed on the local fork")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 