#!/usr/bin/env python3
"""
ArbitrageX Mainnet Fork Test Wrapper

This script is a wrapper for run_mainnet_fork_test.py that handles argument parsing
and configuration for the mainnet fork test.
"""

import os
import sys
import json
import logging
import argparse
import subprocess
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fork_test_wrapper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ForkTestWrapper")

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Run ArbitrageX on a mainnet fork")
    
    parser.add_argument("--networks", type=str, default="arbitrum,polygon",
                        help="Comma-separated list of networks to test (default: arbitrum,polygon)")
    
    parser.add_argument("--tokens", type=str, default="WETH,USDC,DAI,WBTC",
                        help="Comma-separated list of tokens to test")
    
    parser.add_argument("--dexes", type=str, default="uniswap_v3,sushiswap,curve,balancer",
                        help="Comma-separated list of DEXes to test")
    
    parser.add_argument("--fork-block", type=int, default=0,
                        help="Block number to fork from (default: 0 = latest)")
    
    parser.add_argument("--run-time", type=int, default=300,
                        help="How long to run the test in seconds (default: 300)")
    
    parser.add_argument("--batch-size", type=int, default=10,
                        help="Number of trades to process in each batch (default: 10)")
    
    parser.add_argument("--gas-strategy", type=str, default="dynamic",
                        choices=["static", "dynamic", "aggressive"],
                        help="Gas price strategy (default: dynamic)")
    
    parser.add_argument("--modules", type=str, default="all",
                        help="Comma-separated list of modules to run (default: all)")
    
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    
    return parser.parse_args()

def create_fork_config(args):
    """
    Create a fork configuration from the parsed arguments.
    
    Args:
        args: Parsed command line arguments
    
    Returns:
        Fork configuration dictionary
    """
    networks = [n.strip() for n in args.networks.split(",")]
    tokens = [t.strip() for t in args.tokens.split(",")]
    dexes = [d.strip() for d in args.dexes.split(",")]
    
    config = {
        "networks": networks,
        "tokens": tokens,
        "dexes": dexes,
        "fork_block": args.fork_block,
        "run_time": args.run_time,
        "batch_size": args.batch_size,
        "gas_strategy": args.gas_strategy,
        "modules": args.modules.split(",") if args.modules != "all" else "all",
        "debug": args.debug
    }
    
    # Save the configuration to a file
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fork_config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Fork configuration saved to {config_path}")
    
    return config, config_path

def main():
    """
    Main function.
    """
    logger.info("Starting ArbitrageX mainnet fork test wrapper")
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create fork configuration
    config, config_path = create_fork_config(args)
    
    # Initialize the StrategyOptimizer with the fork configuration
    logger.info("Initializing StrategyOptimizer with fork configuration")
    cmd = f"python3 -c \"import sys; sys.path.append('.'); from strategy_optimizer import StrategyOptimizer; optimizer = StrategyOptimizer(fork_config_path='{config_path}'); print('StrategyOptimizer initialized successfully')\""
    
    logger.info(f"Running command: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"StrategyOptimizer initialization failed: {result.stderr}")
        sys.exit(1)
    
    logger.info(result.stdout.strip())
    
    # Run the mainnet fork test
    logger.info("Running mainnet fork test with configuration:")
    logger.info(f"  Networks: {', '.join(config['networks'])}")
    logger.info(f"  Tokens: {', '.join(config['tokens'])}")
    logger.info(f"  DEXes: {', '.join(config['dexes'])}")
    logger.info(f"  Fork block: {config['fork_block']}")
    logger.info(f"  Run time: {config['run_time']}")
    logger.info(f"  Batch size: {config['batch_size']}")
    logger.info(f"  Gas strategy: {config['gas_strategy']}")
    logger.info(f"  Modules: {config['modules']}")
    logger.info(f"  Debug: {config['debug']}")
    
    # Run the mainnet fork test script
    cmd = f"python3 -c \"import sys; sys.path.append('.'); sys.argv = ['run_mainnet_fork_test.py']; import run_mainnet_fork_test; from argparse import Namespace; args = Namespace(networks='{args.networks}', tokens='{args.tokens}', dexes='{args.dexes}', fork_block={args.fork_block}, run_time={args.run_time}, batch_size={args.batch_size}, gas_strategy='{args.gas_strategy}', modules='{args.modules}', debug={args.debug}, fork_config_path='{config_path}'); run_mainnet_fork_test.run_mainnet_fork_test(args=args)\""
    
    logger.info(f"Running command: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"Mainnet fork test failed: {result.stderr}")
        sys.exit(1)
    
    logger.info(result.stdout.strip())
    logger.info("ArbitrageX mainnet fork test wrapper completed")

if __name__ == "__main__":
    main() 