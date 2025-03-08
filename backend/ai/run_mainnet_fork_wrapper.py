#!/usr/bin/env python3
"""
ArbitrageX Mainnet Fork Test Wrapper

This script is a wrapper for run_mainnet_fork_test.py that handles argument parsing
and passes the arguments to the main function of run_mainnet_fork_test.py.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, Any

# Import the main function from run_mainnet_fork_test.py
from run_mainnet_fork_test import main as run_mainnet_fork_test_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mainnet_fork_wrapper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MainnetForkWrapper")

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Run ArbitrageX on a mainnet fork")
    
    parser.add_argument("--networks", type=str, default="ethereum,arbitrum",
                        help="Comma-separated list of networks to test (default: ethereum,arbitrum)")
    
    parser.add_argument("--tokens", type=str, default="WETH,USDC,DAI,WBTC",
                        help="Comma-separated list of tokens to test")
    
    parser.add_argument("--dexes", type=str, default="uniswap_v3,sushiswap,curve,balancer",
                        help="Comma-separated list of DEXes to test")
    
    parser.add_argument("--fork-block", type=int, default=0,
                        help="Block number to fork from (0 for latest)")
    
    parser.add_argument("--run-time", type=int, default=300,
                        help="How long to run the test in seconds")
    
    parser.add_argument("--batch-size", type=int, default=10,
                        help="Number of trades to process in each batch")
    
    parser.add_argument("--gas-strategy", type=str, default="dynamic",
                        choices=["static", "dynamic", "aggressive"],
                        help="Gas price strategy")
    
    parser.add_argument("--modules", type=str, default="all",
                        help="Comma-separated list of modules to run")
    
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    
    return parser.parse_args()

def main():
    """
    Main function.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting ArbitrageX mainnet fork test wrapper")
    
    # Run the test
    run_mainnet_fork_test_main(args=args)
    
    logger.info("ArbitrageX mainnet fork test wrapper completed")

if __name__ == "__main__":
    main() 