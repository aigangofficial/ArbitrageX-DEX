#!/usr/bin/env python3
"""
Strategy Optimizer Runner for ArbitrageX

This script provides a command-line interface to run the strategy optimizer
with various options, including testnet mode.
"""

import argparse
import os
import sys
import logging
import json
from strategy_optimizer_demo import StrategyOptimizer

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
    
    # Print mode
    if args.testnet:
        logger.info("Running in TESTNET mode")
        # Additional testnet-specific configuration could be set here
    else:
        logger.info("Running in MAINNET mode")
    
    # Initialize the strategy optimizer
    optimizer = StrategyOptimizer()
    
    # Example opportunity for demonstration
    opportunity = {
        "token_in": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
        "token_out": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        "amount": 1000000000000000000,  # 1 ETH in wei
        "router": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"  # Uniswap
    }
    
    # Get prediction
    result = optimizer.predict_opportunity(opportunity)
    
    # Print results
    print("\n===== ARBITRAGEX STRATEGY OPTIMIZER =====\n")
    print(f"Network: {'TESTNET' if args.testnet else 'MAINNET'}")
    print(f"Token Pair: {result['token_pair']}")
    print(f"Profitable: {'✅ YES' if result['is_profitable'] else '❌ NO'}")
    print(f"Confidence Score: {result['confidence']:.4f}")
    print(f"Estimated Profit: ${result['estimated_profit_usd']:.2f}")
    print(f"Gas Cost: ${result['gas_cost_usd']:.2f}")
    print(f"Net Profit: ${result['net_profit_usd']:.2f}")
    print(f"Execution Time: {result['execution_time_ms']:.2f}ms")
    
    print("\n===== STRATEGY RECOMMENDATIONS =====\n")
    print("1. Optimal Gas Price: 20 Gwei")
    print("2. Recommended DEX: Uniswap V2")
    print("3. Slippage Tolerance: 0.5%")
    print("4. Execution Priority: Medium")
    
    if args.testnet:
        print("\n⚠️ TESTNET MODE: No real transactions will be executed")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 