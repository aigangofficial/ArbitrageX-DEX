#!/usr/bin/env python3
"""
Test AI Model Runner for ArbitrageX

This script provides a command-line interface to run the test AI model
with various options, including testnet mode.
"""

import argparse
import os
import sys
import logging
import json
from test_ai_model import test_multiple_scenarios

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestAIModelRunner")

def main():
    """Main entry point for the test AI model runner."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="ArbitrageX Test AI Model")
    parser.add_argument("--testnet", action="store_true", help="Run in testnet mode")
    parser.add_argument("--visualize", action="store_true", 
                        help="Visualize results")
    args = parser.parse_args()
    
    # Print mode
    if args.testnet:
        logger.info("Running in TESTNET mode")
        # Additional testnet-specific configuration could be set here
    else:
        logger.info("Running in MAINNET mode")
    
    # Run the test AI model
    print("\n===== ARBITRAGEX TEST AI MODEL =====\n")
    print(f"Mode: {'TESTNET' if args.testnet else 'MAINNET'}")
    print("\nThis demonstration tests the AI model across multiple scenarios\n")
    
    # Run the test
    test_multiple_scenarios()
    
    if args.testnet:
        print("\n⚠️ TESTNET MODE: No real transactions will be executed")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 