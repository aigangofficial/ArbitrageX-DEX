#!/usr/bin/env python3
"""
Gas Optimizer Module for ArbitrageX

This module optimizes gas prices and usage for arbitrage trades.
It implements various strategies to estimate gas prices and usage
to ensure trades are executed efficiently.
"""

import os
import json
import time
import random
import logging
import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gas_optimizer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GasOptimizer")

class GasOptimizer:
    """
    Gas Optimizer class for ArbitrageX trades.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the Gas Optimizer module.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.load_config()
        self.results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
        os.makedirs(self.results_dir, exist_ok=True)
        logger.info("Gas Optimizer module initialized")
    
    def load_config(self):
        """
        Load the configuration from the config file.
        """
        try:
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.config = {}
    
    def optimize_gas_for_trades(self, mev_results_path: str) -> str:
        """
        Optimize gas for the trades from MEV protection.
        
        Args:
            mev_results_path: Path to the MEV protection results file
        
        Returns:
            Path to the gas optimization results file
        """
        logger.info(f"Optimizing gas for trades from {mev_results_path}")
        
        # Load MEV protection results
        try:
            with open(mev_results_path, "r") as f:
                mev_results = json.load(f)
            logger.info(f"MEV protection results loaded from {mev_results_path}")
        except Exception as e:
            logger.error(f"Error loading MEV protection results: {e}")
            return ""
        
        # Get trades from MEV results
        trades = mev_results.get("trades", [])
        logger.info(f"Found {len(trades)} trades to optimize gas for")
        
        # Optimize gas for each trade
        optimized_trades = []
        for trade in trades:
            optimized_trade = self.optimize_gas(trade)
            optimized_trades.append(optimized_trade)
        
        # Create results
        results = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "config": self.config,
            "trades": optimized_trades
        }
        
        # Save results to file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(self.results_dir, f"gas_estimation_{timestamp}.json")
        
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Gas optimization results saved to {results_file}")
        
        # Log summary
        avg_gas_price = sum([t.get("gas_price", 0) for t in optimized_trades]) / len(optimized_trades) if optimized_trades else 0
        avg_gas_used = sum([t.get("gas_used", 0) for t in optimized_trades]) / len(optimized_trades) if optimized_trades else 0
        avg_gas_cost = sum([t.get("gas_cost", 0) for t in optimized_trades]) / len(optimized_trades) if optimized_trades else 0
        
        logger.info(f"Average gas price: {avg_gas_price:.2f} Gwei")
        logger.info(f"Average gas used: {avg_gas_used:.2f}")
        logger.info(f"Average gas cost: ${avg_gas_cost:.2f}")
        
        return results_file
    
    def optimize_gas(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize gas for a single trade.
        
        Args:
            trade: Trade to optimize gas for
        
        Returns:
            Optimized trade
        """
        # Create a copy of the trade as the optimized trade
        optimized_trade = trade.copy()
        
        # Get the gas strategy from the config
        gas_strategy = self.config.get("gas_strategy", "dynamic")
        
        # Estimate gas price based on the strategy
        gas_price = self.estimate_gas_price(gas_strategy)
        
        # Estimate gas used based on the trade
        gas_used = self.estimate_gas_used(trade)
        
        # Calculate gas cost
        gas_cost = self.calculate_gas_cost(gas_price, gas_used)
        
        # Update the optimized trade
        optimized_trade["gas_price"] = gas_price
        optimized_trade["gas_used"] = gas_used
        optimized_trade["gas_cost"] = gas_cost
        optimized_trade["expected_profit"] = trade.get("expected_profit", 0) - gas_cost
        
        logger.info(f"Optimized gas for trade: {gas_price:.2f} Gwei, {gas_used:.2f} gas, ${gas_cost:.2f} cost")
        
        return optimized_trade
    
    def estimate_gas_price(self, strategy: str) -> float:
        """
        Estimate gas price based on the strategy.
        
        Args:
            strategy: Gas price strategy
        
        Returns:
            Estimated gas price in Gwei
        """
        # Base gas prices for different strategies
        base_gas_prices = {
            "static": 20.0,
            "dynamic": 25.0,
            "aggressive": 30.0
        }
        
        # Get the base gas price for the strategy
        base_gas_price = base_gas_prices.get(strategy, 20.0)
        
        # Add some randomness to simulate real-world variability
        gas_price = base_gas_price * random.uniform(0.8, 1.2)
        
        # Simulate network congestion
        network = self.config.get("network", "ethereum")
        if network == "ethereum":
            gas_price *= random.uniform(1.0, 1.5)  # Ethereum tends to have higher gas prices
        elif network == "arbitrum":
            gas_price *= random.uniform(0.5, 0.8)  # Arbitrum tends to have lower gas prices
        elif network == "polygon":
            gas_price *= random.uniform(0.3, 0.5)  # Polygon tends to have even lower gas prices
        
        logger.info(f"Estimated gas price for {strategy} strategy on {network}: {gas_price:.2f} Gwei")
        
        return gas_price
    
    def estimate_gas_used(self, trade: Dict[str, Any]) -> float:
        """
        Estimate gas used for a trade.
        
        Args:
            trade: Trade to estimate gas used for
        
        Returns:
            Estimated gas used
        """
        # Base gas used for different trade types
        base_gas_used = {
            "simple_swap": 150000,
            "multi_hop": 250000,
            "flash_loan": 350000
        }
        
        # Determine trade type based on the trade details
        # For this simulation, we'll just use a random trade type
        trade_type = random.choice(list(base_gas_used.keys()))
        
        # Get the base gas used for the trade type
        base = base_gas_used.get(trade_type, 200000)
        
        # Add some randomness to simulate real-world variability
        gas_used = base * random.uniform(0.9, 1.1)
        
        # Adjust based on MEV protection
        if trade.get("mev_protected", False):
            protection_strategy = trade.get("protection_strategy", "none")
            if protection_strategy == "private_tx":
                gas_used *= 1.1  # Private transactions may use more gas
            elif protection_strategy == "flashbots":
                gas_used *= 1.05  # Flashbots may use slightly more gas
            elif protection_strategy == "gas_price_bump":
                gas_used *= 1.0  # Gas price bump doesn't affect gas used
        
        logger.info(f"Estimated gas used for {trade_type} trade: {gas_used:.2f}")
        
        return gas_used
    
    def calculate_gas_cost(self, gas_price: float, gas_used: float) -> float:
        """
        Calculate gas cost for a trade.
        
        Args:
            gas_price: Gas price in Gwei
            gas_used: Gas used
        
        Returns:
            Gas cost in USD
        """
        # Convert gas price from Gwei to ETH
        gas_price_eth = gas_price * 1e-9
        
        # Calculate gas cost in ETH
        gas_cost_eth = gas_price_eth * gas_used
        
        # Convert gas cost from ETH to USD
        # For this simulation, we'll use a fixed ETH price
        eth_price_usd = 3000.0
        gas_cost_usd = gas_cost_eth * eth_price_usd
        
        logger.info(f"Calculated gas cost: {gas_cost_eth:.6f} ETH (${gas_cost_usd:.2f})")
        
        return gas_cost_usd

if __name__ == "__main__":
    # Example usage
    config_path = "small_scale_test_config.json"
    mev_results_path = "results/mev_protection_20250301_101017.json"
    
    gas = GasOptimizer(config_path)
    results_file = gas.optimize_gas_for_trades(mev_results_path)
    
    print(f"Gas optimization results saved to {results_file}") 