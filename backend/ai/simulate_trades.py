#!/usr/bin/env python3
"""
Simulate Trades Script

This script simulates trades and adds them to the learning loop for processing.
It's used to demonstrate the learning loop functionality.
"""

import os
import sys
import time
import json
import random
import logging
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the learning_loop module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.learning_loop import LearningLoop

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("simulate_trades.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SimulateTrades")

def generate_random_trade():
    """Generate a random trade."""
    tokens = ["WETH", "USDC", "DAI", "WBTC", "LINK", "UNI", "AAVE", "SNX", "COMP", "MKR"]
    dexes = ["uniswap_v3", "curve", "balancer", "sushiswap", "1inch"]
    networks = ["ethereum", "arbitrum", "polygon", "optimism", "bsc"]
    
    # Random token pair
    token_in = random.choice(tokens)
    token_out = random.choice([t for t in tokens if t != token_in])
    
    # Random amounts
    amount_in = random.uniform(0.1, 10.0)
    amount_out = amount_in * random.uniform(0.95, 1.05)
    
    # Random profit
    expected_profit = random.uniform(0.001, 0.1)
    actual_profit = expected_profit * random.uniform(0.8, 1.2)
    
    # Random gas
    gas_price = random.uniform(10, 100)
    gas_used = random.uniform(100000, 500000)
    gas_cost = (gas_price * 1e-9) * gas_used * 3000  # Assuming ETH price of $3000
    
    # Random status
    status = random.choices(["success", "failed"], weights=[0.8, 0.2])[0]
    
    # Generate trade
    trade = {
        "opportunity_id": f"sim_{int(time.time())}_{random.randint(1000, 9999)}",
        "network": random.choice(networks),
        "token_pair": [token_in, token_out],
        "dex": random.choice(dexes),
        "amount_in": amount_in,
        "amount_out": amount_out,
        "expected_profit": expected_profit,
        "actual_profit": actual_profit if status == "success" else 0,
        "gas_price": gas_price,
        "gas_used": gas_used,
        "gas_cost": gas_cost,
        "status": status,
        "execution_time": random.uniform(100, 2000),
        "timestamp": datetime.now().isoformat(),
        "slippage": random.uniform(0, 0.02),
        "market_conditions": {
            "volatility": random.uniform(0, 1),
            "liquidity": random.uniform(0.5, 1),
            "network_congestion": random.uniform(0, 1)
        }
    }
    
    return trade

def main():
    """Main function to simulate trades."""
    logger.info("Starting trade simulation")
    
    # Create the learning loop instance
    learning_loop = LearningLoop()
    
    # Number of trades to simulate
    num_trades = 50
    
    # Simulate trades
    for i in range(num_trades):
        # Generate a random trade
        trade = generate_random_trade()
        
        # Add the trade to the learning loop
        learning_loop.add_execution_result(trade)
        
        logger.info(f"Added trade {i+1}/{num_trades} to learning loop: {trade['opportunity_id']}")
        
        # Sleep for a random time to simulate real-world timing
        time.sleep(random.uniform(0.1, 0.5))
    
    logger.info(f"Completed simulation of {num_trades} trades")

if __name__ == "__main__":
    main() 