"""
Test ML Learning Script

This script tests the ML bot's learning capabilities by initializing the learning loop,
adding some sample execution results, and checking if the models are being updated.
"""

import os
import sys
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any

# Add the parent directory to the Python path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_ml_learning.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TestMLLearning")

# Import the LearningLoop
from backend.ai.learning_loop import LearningLoop

def test_learning_loop_initialization():
    """Test the initialization of the learning loop."""
    logger.info("Testing learning loop initialization...")
    
    # Initialize the learning loop
    learning_loop = LearningLoop()
    
    # Check if the learning loop is initialized
    if learning_loop:
        logger.info("Learning loop initialized successfully")
        
        # Start the learning loop
        learning_loop.start()
        logger.info("Learning loop started")
        
        return learning_loop
    else:
        logger.error("Failed to initialize learning loop")
        return None

def add_sample_execution_results(learning_loop: LearningLoop):
    """Add sample execution results to the learning loop."""
    logger.info("Adding sample execution results...")
    
    # Create sample execution results
    execution_results = [
        {
            "id": "exec_001",
            "timestamp": datetime.now().isoformat(),
            "network": "ethereum",
            "token_in": "WETH",
            "token_out": "USDC",
            "amount_in": 1.0,
            "amount_out": 1800.0,
            "profit_usd": 20.0,
            "gas_used": 230000,
            "gas_price": 50.0,
            "gas_cost_usd": 5.0,
            "net_profit_usd": 15.0,
            "execution_time_ms": 3500,
            "slippage_actual": 0.003,
            "route": [
                {"dex": "uniswap_v3", "token_in": "WETH", "token_out": "USDC"},
                {"dex": "sushiswap", "token_in": "USDC", "token_out": "WETH"}
            ],
            "status": "success",
            "tx_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "block_number": 18000000,
            "market_conditions": {
                "eth_price_usd": 1800.0,
                "gas_price_gwei": 50.0,
                "network_congestion": "medium",
                "volatility": "low"
            }
        },
        {
            "id": "exec_002",
            "timestamp": datetime.now().isoformat(),
            "network": "ethereum",
            "token_in": "WETH",
            "token_out": "DAI",
            "amount_in": 0.5,
            "amount_out": 900.0,
            "profit_usd": 10.0,
            "gas_used": 210000,
            "gas_price": 45.0,
            "gas_cost_usd": 4.0,
            "net_profit_usd": 6.0,
            "execution_time_ms": 3200,
            "slippage_actual": 0.002,
            "route": [
                {"dex": "uniswap_v3", "token_in": "WETH", "token_out": "DAI"},
                {"dex": "curve", "token_in": "DAI", "token_out": "WETH"}
            ],
            "status": "success",
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "block_number": 18000050,
            "market_conditions": {
                "eth_price_usd": 1800.0,
                "gas_price_gwei": 45.0,
                "network_congestion": "low",
                "volatility": "low"
            }
        }
    ]
    
    # Add the execution results to the learning loop
    for result in execution_results:
        learning_loop.add_execution_result(result)
        logger.info(f"Added execution result: {result['id']}")
    
    return execution_results

def test_model_update(learning_loop: LearningLoop):
    """Test if the models are being updated."""
    logger.info("Testing model update...")
    
    # Force a model update
    learning_loop.force_model_update()
    
    # Get the learning stats
    learning_stats = learning_loop.get_learning_stats()
    logger.info(f"Learning stats: {json.dumps(learning_stats, indent=2)}")
    
    # Get the model performance
    model_performance = learning_loop.get_model_performance()
    logger.info(f"Model performance: {json.dumps(model_performance, indent=2)}")
    
    return learning_stats, model_performance

def test_strategy_adaptation(learning_loop: LearningLoop):
    """Test if the strategies are being adapted."""
    logger.info("Testing strategy adaptation...")
    
    # Force a strategy adaptation
    learning_loop.force_strategy_adaptation()
    
    # Get the validation stats
    validation_stats = learning_loop.get_validation_stats()
    logger.info(f"Validation stats: {json.dumps(validation_stats, indent=2)}")
    
    return validation_stats

def main():
    """Main function to run the test."""
    logger.info("Starting ML learning test...")
    
    # Test the learning loop initialization
    learning_loop = test_learning_loop_initialization()
    if not learning_loop:
        logger.error("Learning loop initialization test failed, exiting")
        return
    
    # Add sample execution results
    execution_results = add_sample_execution_results(learning_loop)
    
    # Test model update
    learning_stats, model_performance = test_model_update(learning_loop)
    
    # Test strategy adaptation
    validation_stats = test_strategy_adaptation(learning_loop)
    
    # Stop the learning loop
    learning_loop.stop()
    logger.info("Learning loop stopped")
    
    logger.info("ML learning test completed")

if __name__ == "__main__":
    main() 