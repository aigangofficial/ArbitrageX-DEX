#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArbitrageX Optimized Strategy with Layer 2 Integration

This module enhances the optimized trading strategy with Layer 2 support
to dramatically reduce gas costs and improve profitability.
"""

import os
import json
import time
import logging
import random
import datetime
import argparse
from typing import Dict, List, Tuple, Optional, Any

# Import the original optimized strategy components
from optimized_strategy import (
    GasOptimizer, RiskManager, StrategyOptimizer, OptimizedStrategy
)

# Import Layer 2 integration components
from l2_integration import (
    L2Network, L2GasTracker, L2OpportunityEvaluator, L2Executor
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("optimized_strategy_l2.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("OptimizedStrategyL2")


class OptimizedStrategyL2(OptimizedStrategy):
    """
    Enhanced optimized strategy with Layer 2 support for improved profitability.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the L2-enhanced optimized strategy.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        # Initialize the base optimized strategy
        super().__init__(config_path)
        
        # Initialize L2-specific components
        self.l2_gas_tracker = L2GasTracker(config_path)
        self.l2_opportunity_evaluator = L2OpportunityEvaluator(self.l2_gas_tracker, config_path)
        self.l2_executor = L2Executor(config_path)
        
        # L2-specific configuration
        self.l2_config = {
            "enable_l2": True,
            "prefer_l2": True,  # Prefer L2 networks over L1 when profitable
            "l2_networks": [
                L2Network.ARBITRUM.value,
                L2Network.OPTIMISM.value,
                L2Network.BASE.value,
                L2Network.POLYGON.value
            ],
            "l2_metrics_dir": "backend/ai/metrics/l2_optimized"
        }
        
        # Update config with L2-specific settings if available
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    if "l2_config" in loaded_config:
                        self.l2_config.update(loaded_config["l2_config"])
                logger.info(f"Loaded L2 configuration from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load L2 configuration: {e}")
        
        # Create metrics directory
        os.makedirs(self.l2_config["l2_metrics_dir"], exist_ok=True)
        
        # Track L2-specific performance
        self.l2_trades = 0
        self.l2_successful_trades = 0
        self.l2_total_profit = 0.0
        self.l2_network_performance = {
            network: {"trades": 0, "successful_trades": 0, "total_profit": 0.0}
            for network in self.l2_config["l2_networks"]
        }
        
        logger.info("L2-enhanced optimized strategy initialized")
    
    def evaluate_opportunity(self, opportunity: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluate a trading opportunity across both L1 and L2 networks.
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            Tuple of (should_execute, enhanced_opportunity)
        """
        # First, evaluate on L1 using the base strategy
        l1_should_execute, l1_enhanced = super().evaluate_opportunity(opportunity)
        
        # If L2 is disabled, return the L1 evaluation
        if not self.l2_config["enable_l2"]:
            return l1_should_execute, l1_enhanced
        
        # Evaluate on L2 networks
        best_l2_network, l2_enhanced = self.l2_opportunity_evaluator.find_best_l2_network(opportunity)
        
        # If no suitable L2 network found
        if best_l2_network is None:
            logger.info("No suitable L2 network found, using L1 evaluation")
            return l1_should_execute, l1_enhanced
        
        # Compare L1 and L2 profitability
        l1_net_profit = l1_enhanced.get("net_profit", 0.0) if l1_should_execute else 0.0
        l2_net_profit = l2_enhanced.get("l2_net_profit_usd", 0.0)
        
        # Decide whether to use L1 or L2
        if self.l2_config["prefer_l2"] and l2_net_profit > 0:
            # Prefer L2 even if L1 is slightly more profitable
            use_l2 = True
        else:
            # Use whichever is more profitable
            use_l2 = l2_net_profit > l1_net_profit
        
        if use_l2:
            logger.info(f"Using L2 network {best_l2_network.value} with profit ${l2_net_profit:.2f} (L1: ${l1_net_profit:.2f})")
            l2_enhanced["execution_layer"] = "L2"
            return True, l2_enhanced
        else:
            logger.info(f"Using L1 with profit ${l1_net_profit:.2f} (L2: ${l2_net_profit:.2f})")
            l1_enhanced["execution_layer"] = "L1"
            return l1_should_execute, l1_enhanced
    
    def execute_trade(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trade on either L1 or L2 based on the opportunity.
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            Dictionary with trade results
        """
        # Check which execution layer to use
        execution_layer = opportunity.get("execution_layer", "L1")
        
        if execution_layer == "L2":
            # Execute on L2
            result = self.l2_executor.execute_trade(opportunity)
            
            # Update L2-specific metrics
            self.l2_trades += 1
            if result.get("success", False):
                self.l2_successful_trades += 1
                self.l2_total_profit += result.get("net_profit", 0.0)
            
            # Update network-specific performance
            network = result.get("network")
            if network in self.l2_network_performance:
                self.l2_network_performance[network]["trades"] += 1
                if result.get("success", False):
                    self.l2_network_performance[network]["successful_trades"] += 1
                    self.l2_network_performance[network]["total_profit"] += result.get("net_profit", 0.0)
            
            # Also update base metrics for consistency
            self.total_trades += 1
            if result.get("success", False):
                self.successful_trades += 1
                self.total_profit += result.get("net_profit", 0.0)
            
            return result
        else:
            # Execute on L1 using the base strategy
            return super().execute_trade(opportunity)
    
    def save_metrics(self) -> None:
        """Save current performance metrics to a file, including L2-specific metrics."""
        # Save base metrics
        super().save_metrics()
        
        # Save L2-specific metrics
        l2_metrics = self.get_l2_metrics()
        
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.l2_config['l2_metrics_dir']}/l2_metrics_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(l2_metrics, f, indent=2)
            logger.info(f"L2 metrics saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save L2 metrics: {e}")
    
    def get_l2_metrics(self) -> Dict[str, Any]:
        """
        Get current L2-specific performance metrics.
        
        Returns:
            Dictionary with L2 performance metrics
        """
        now = datetime.datetime.now()
        runtime = (now - self.start_time).total_seconds() / 3600  # Runtime in hours
        
        l2_metrics = {
            "timestamp": now.isoformat(),
            "runtime_hours": runtime,
            "l2_trades": self.l2_trades,
            "l2_successful_trades": self.l2_successful_trades,
            "l2_success_rate": (self.l2_successful_trades / self.l2_trades) if self.l2_trades > 0 else 0,
            "l2_total_profit_usd": self.l2_total_profit,
            "l2_average_profit_per_trade": (self.l2_total_profit / self.l2_trades) if self.l2_trades > 0 else 0,
            "l2_profit_per_hour": self.l2_total_profit / runtime if runtime > 0 else 0,
            "l2_network_performance": self.l2_network_performance,
            "l1_vs_l2_comparison": {
                "l1_trades": self.total_trades - self.l2_trades,
                "l2_trades": self.l2_trades,
                "l1_profit": self.total_profit - self.l2_total_profit,
                "l2_profit": self.l2_total_profit,
                "l1_success_rate": ((self.successful_trades - self.l2_successful_trades) / 
                                   (self.total_trades - self.l2_trades)) 
                                   if (self.total_trades - self.l2_trades) > 0 else 0,
                "l2_success_rate": (self.l2_successful_trades / self.l2_trades) if self.l2_trades > 0 else 0
            }
        }
        
        return l2_metrics


def main():
    """Main function to demonstrate the L2-enhanced optimized strategy."""
    parser = argparse.ArgumentParser(description="ArbitrageX L2-Enhanced Optimized Strategy")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--simulate", action="store_true", help="Run a simulation")
    parser.add_argument("--trades", type=int, default=10, help="Number of trades to simulate")
    parser.add_argument("--l2-only", action="store_true", help="Only use L2 networks")
    args = parser.parse_args()
    
    # Initialize strategy
    strategy = OptimizedStrategyL2(args.config)
    
    # If l2-only flag is set, update config
    if args.l2_only:
        strategy.l2_config["prefer_l2"] = True
    
    if args.simulate:
        logger.info(f"Running L2-enhanced simulation with {args.trades} trades")
        
        # Simulate trades
        for i in range(args.trades):
            # Generate a random opportunity with more favorable parameters
            opportunity = {
                "token_pair": random.choice(["LINK-USDC", "WETH-DAI", "WETH-USDC", "WBTC-USDC"]),
                "dex": random.choice(["curve", "balancer", "sushiswap"]),
                "expected_profit": random.uniform(20, 100),  # Higher profit
                "expected_profit_pct": random.uniform(0.01, 0.05),  # Higher profit percentage
                "gas_price": random.uniform(10, 25),  # Lower gas price
                "estimated_gas": random.uniform(150000, 250000)  # Lower gas usage
            }
            
            # Evaluate opportunity
            should_execute, enhanced = strategy.evaluate_opportunity(opportunity)
            
            # Execute trade if approved
            if should_execute:
                result = strategy.execute_trade(enhanced)
                execution_layer = enhanced.get("execution_layer", "L1")
                logger.info(f"Trade {i+1}: {execution_layer}, {result['success']}, ${result.get('net_profit', result.get('profit', 0)):.2f}")
            else:
                logger.info(f"Trade {i+1}: Rejected")
        
        # Save final metrics
        strategy.save_metrics()
        
        # Print summary
        metrics = strategy.get_metrics()
        l2_metrics = strategy.get_l2_metrics()
        
        print("\nSimulation Summary:")
        print(f"Total Trades: {metrics['total_trades']}")
        print(f"Successful Trades: {metrics['successful_trades']}")
        print(f"Success Rate: {metrics['success_rate']:.2%}")
        print(f"Total Profit: ${metrics['total_profit_usd']:.2f}")
        print(f"Average Profit per Trade: ${metrics['average_profit_per_trade']:.2f}")
        
        print("\nL2 Performance:")
        print(f"L2 Trades: {l2_metrics['l2_trades']} ({(l2_metrics['l2_trades']/metrics['total_trades']):.2%} of total)")
        print(f"L2 Success Rate: {l2_metrics['l2_success_rate']:.2%}")
        print(f"L2 Total Profit: ${l2_metrics['l2_total_profit_usd']:.2f} ({(l2_metrics['l2_total_profit_usd']/metrics['total_profit_usd']):.2%} of total)")
        
        # Print network breakdown if L2 trades were executed
        if l2_metrics['l2_trades'] > 0:
            print("\nL2 Network Performance:")
            for network, perf in l2_metrics['l2_network_performance'].items():
                if perf['trades'] > 0:
                    success_rate = perf['successful_trades'] / perf['trades'] if perf['trades'] > 0 else 0
                    avg_profit = perf['total_profit'] / perf['trades'] if perf['trades'] > 0 else 0
                    print(f"  {network}: {perf['trades']} trades, {success_rate:.2%} success, ${perf['total_profit']:.2f} profit (${avg_profit:.2f}/trade)")
    else:
        logger.info("L2-enhanced strategy initialized. Use --simulate to run a simulation.")


if __name__ == "__main__":
    main() 