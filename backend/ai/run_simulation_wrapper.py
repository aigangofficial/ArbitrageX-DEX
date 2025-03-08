#!/usr/bin/env python3
"""
Wrapper script for running the real-world simulation.
"""

import os
import sys
import subprocess
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SimulationWrapper")

def parse_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="Run a real-world simulation for ArbitrageX")
    
    parser.add_argument("--initial-capital", type=float, default=50.0,
                        help="Initial capital in USD (default: 50.0)")
    
    parser.add_argument("--networks", type=str, default="ethereum,arbitrum,polygon",
                        help="Comma-separated list of networks to test (default: ethereum,arbitrum,polygon)")
    
    parser.add_argument("--token-pairs", type=str, default="WETH-USDC,WBTC-USDT,ETH-DAI",
                        help="Comma-separated list of token pairs to test (default: WETH-USDC,WBTC-USDT,ETH-DAI)")
    
    parser.add_argument("--dexes", type=str, default="uniswap_v3,sushiswap,curve",
                        help="Comma-separated list of DEXes to test (default: uniswap_v3,sushiswap,curve)")
    
    parser.add_argument("--min-trades", type=int, default=50,
                        help="Minimum number of trades to execute (default: 50)")
    
    parser.add_argument("--max-trades", type=int, default=200,
                        help="Maximum number of trades to execute (default: 200)")
    
    parser.add_argument("--simulation-time", type=int, default=3600,
                        help="Simulation time in seconds (default: 3600)")
    
    parser.add_argument("--fork-block", type=int, default=0,
                        help="Block number to fork from (0 for latest)")
    
    parser.add_argument("--output-dir", type=str, default="results/real_world_simulation",
                        help="Directory to save results (default: results/real_world_simulation)")
    
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    
    parser.add_argument("--use-historical-data", action="store_true", default=True,
                        help="Use historical data from MongoDB (default: True)")
    
    parser.add_argument("--enable-learning", action="store_true", default=True,
                        help="Enable AI learning loop (default: True)")
    
    parser.add_argument("--flash-loan-enabled", action="store_true", default=True,
                        help="Enable flash loan usage (default: True)")
    
    return parser.parse_args()

def main():
    """
    Main function to run the simulation.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create market data JSON
    market_data = {
        "initial_capital_usd": args.initial_capital,
        "networks": args.networks.split(","),
        "token_pairs": [pair.split("-") for pair in args.token_pairs.split(",")],
        "dexes": args.dexes.split(","),
        "min_trades": args.min_trades,
        "max_trades": args.max_trades,
        "simulation_time": args.simulation_time,
        "use_historical_data": args.use_historical_data,
        "enable_learning": args.enable_learning,
        "flash_loan_enabled": args.flash_loan_enabled
    }
    
    # Convert market data to JSON string
    import json
    market_data_json = json.dumps(market_data)
    
    # Build the command
    cmd = [
        sys.executable,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_real_world_simulation.py"),
        "--market-data", market_data_json,
        "--mainnet-fork", "http://localhost:8546"
    ]
    
    # Run the simulation
    logger.info("Running simulation with the following parameters:")
    logger.info(f"Initial capital: ${args.initial_capital}")
    logger.info(f"Networks: {args.networks}")
    logger.info(f"Token pairs: {args.token_pairs}")
    logger.info(f"DEXes: {args.dexes}")
    logger.info(f"Min trades: {args.min_trades}")
    logger.info(f"Max trades: {args.max_trades}")
    logger.info(f"Simulation time: {args.simulation_time} seconds")
    
    logger.info("Running command: %s", " ".join(cmd))
    
    try:
        result = subprocess.run(cmd, check=True)
        logger.info("Simulation completed successfully.")
        return 0
    except subprocess.CalledProcessError as e:
        logger.error("Simulation failed with error code %d", e.returncode)
        return e.returncode

if __name__ == "__main__":
    sys.exit(main()) 