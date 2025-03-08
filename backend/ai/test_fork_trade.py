"""
Test Fork Trade Script

This script tests the execution of a trade on the Hardhat forked mainnet
using the Web3Connector and StrategyOptimizer.
"""

import os
import sys
import json
import logging
import time
from typing import Dict, Any

# Add the parent directory to the Python path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_fork_trade.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TestForkTrade")

# Import the Web3Connector and StrategyOptimizer
from backend.ai.web3_connector import Web3Connector
from backend.ai.strategy_optimizer import StrategyOptimizer

def test_fork_connection():
    """Test the connection to the Hardhat fork."""
    logger.info("Testing connection to Hardhat fork...")
    
    # Initialize the Web3Connector with the fork configuration
    connector = Web3Connector('backend/ai/hardhat_fork_config.json')
    
    # Check if connected
    if connector.is_connected():
        logger.info(f"Successfully connected to Hardhat fork at block {connector.web3.eth.block_number}")
        return connector
    else:
        logger.error("Failed to connect to Hardhat fork")
        return None

def simulate_trade(connector: Web3Connector):
    """Simulate a trade on the forked mainnet."""
    logger.info("Simulating a trade on the forked mainnet...")
    
    # Create a sample trade opportunity
    opportunity = {
        "network": "ethereum",
        "token_in": "WETH",
        "token_out": "USDC",
        "amount_in": 1.0,  # 1 WETH
        "estimated_profit": 0.02,  # 2% profit
        "route": [
            {"dex": "uniswap_v3", "token_in": "WETH", "token_out": "USDC"},
            {"dex": "sushiswap", "token_in": "USDC", "token_out": "WETH"}
        ],
        "gas_estimate": 250000,
        "execution_priority": "high",
        "slippage_tolerance": 0.005,
        "timestamp": int(time.time())
    }
    
    # Initialize the StrategyOptimizer
    optimizer = StrategyOptimizer(fork_config_path='backend/ai/hardhat_fork_config.json')
    
    # Predict the opportunity
    prediction = optimizer.predict_opportunity(opportunity)
    logger.info(f"Opportunity prediction: {json.dumps(prediction, indent=2)}")
    
    # Execute the opportunity if it's profitable
    if prediction.get("is_profitable", False):
        logger.info("Executing the opportunity...")
        result = optimizer.execute_opportunity(opportunity)
        logger.info(f"Execution result: {json.dumps(result, indent=2)}")
        return result
    else:
        logger.info("Opportunity not profitable, skipping execution")
        return None

def main():
    """Main function to run the test."""
    logger.info("Starting fork trade test...")
    
    # Test the fork connection
    connector = test_fork_connection()
    if not connector:
        logger.error("Fork connection test failed, exiting")
        return
    
    # Simulate a trade
    result = simulate_trade(connector)
    
    if result:
        logger.info("Trade simulation completed successfully")
        logger.info(f"Profit: {result.get('profit', 'N/A')}")
        logger.info(f"Gas used: {result.get('gas_used', 'N/A')}")
        logger.info(f"Transaction hash: {result.get('tx_hash', 'N/A')}")
    else:
        logger.info("Trade simulation did not execute")
    
    logger.info("Fork trade test completed")

if __name__ == "__main__":
    main() 