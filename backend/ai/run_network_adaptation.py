#!/usr/bin/env python3
"""
Network Adaptation Runner for ArbitrageX

This script provides a command-line interface to run the network adaptation
demo with various options, including testnet mode.
"""

import argparse
import os
import sys
import logging
import json
from network_demo import NetworkAdaptation, demonstrate_network_adaptation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("NetworkAdaptationRunner")

def main():
    """Main entry point for the network adaptation runner."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="ArbitrageX Network Adaptation")
    parser.add_argument("--testnet", action="store_true", help="Run in testnet mode")
    parser.add_argument("--networks", type=str, default="ethereum,arbitrum,polygon,bsc", 
                        help="Comma-separated list of networks to include")
    parser.add_argument("--visualize", action="store_true", 
                        help="Visualize results")
    args = parser.parse_args()
    
    # Print mode
    if args.testnet:
        logger.info("Running in TESTNET mode")
        # Additional testnet-specific configuration could be set here
    else:
        logger.info("Running in MAINNET mode")
    
    # Parse networks
    networks = args.networks.split(",")
    logger.info(f"Analyzing networks: {', '.join(networks)}")
    
    # Run the network adaptation demonstration
    print("\n===== ARBITRAGEX NETWORK ADAPTATION DEMONSTRATION =====\n")
    print(f"Mode: {'TESTNET' if args.testnet else 'MAINNET'}")
    print(f"Networks: {', '.join(networks)}")
    print("\nThis demonstration shows how the AI model adapts to different networks")
    print("and time-based patterns to optimize arbitrage strategies.\n")
    
    # Run the demonstration
    demonstrate_network_adaptation()
    
    if args.testnet:
        print("\n⚠️ TESTNET MODE: No real transactions will be executed")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 