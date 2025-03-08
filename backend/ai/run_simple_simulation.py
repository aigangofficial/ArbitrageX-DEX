#!/usr/bin/env python3
"""
Simple script to run a real-world simulation for ArbitrageX.
"""

import os
import sys
import json
import time
import logging
import argparse
import datetime
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("simple_simulation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SimpleSimulation")

# Import required modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from web3_connector import Web3Connector
from strategy_optimizer import StrategyOptimizer
from learning_loop import LearningLoop
from gas_optimizer import GasOptimizer
from trade_executor import TradeExecutor

class SimpleSimulation:
    """
    Simple simulation for ArbitrageX.
    """
    
    def __init__(self):
        """
        Initialize the simulation.
        """
        self.config = {
            "simulation": {
                "initial_capital_usd": 50.0,
                "min_trades": 10,
                "max_trades": 20,
                "simulation_time": 300,
                "use_historical_data": True,
                "enable_learning": True,
                "flash_loan_enabled": True,
                "timestamp": datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            },
            "networks": ["ethereum", "arbitrum", "polygon"],
            "token_pairs": [["WETH", "USDC"], ["WBTC", "USDT"], ["ETH", "DAI"]],
            "dexes": ["uniswap_v3", "sushiswap", "curve"],
            "fork": {
                "block_number": "latest",
                "url": "http://localhost:8546"  # Default Hardhat fork URL
            },
            "gas": {
                "initial_strategy": "dynamic",
                "min_gas_price_gwei": 10,
                "max_gas_price_gwei": 200,
                "gas_price_adjustment_threshold": 0.05  # 5% threshold for adjustment
            },
            "slippage": {
                "initial_tolerance": 0.005,  # 0.5% initial slippage tolerance
                "min_tolerance": 0.001,      # 0.1% minimum slippage tolerance
                "max_tolerance": 0.03,       # 3% maximum slippage tolerance
                "adjustment_threshold": 0.02 # 2% threshold for adjustment
            },
            "risk": {
                "initial_risk_level": "medium",
                "min_profit_threshold_usd": 1.0,  # Minimum $1 profit per trade
                "max_loss_per_trade_usd": 5.0,    # Maximum $5 loss per trade
                "max_total_loss_usd": 25.0        # Maximum $25 total loss (half of initial capital)
            },
            "flash_loan": {
                "min_amount_usd": 1000,      # Minimum $1000 flash loan
                "max_amount_usd": 100000,    # Maximum $100,000 flash loan
                "fee_percentage": 0.0009     # 0.09% flash loan fee
            }
        }
        
        # Create results directory
        self.results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results/simple_simulation")
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Save the configuration to a file
        self.config_path = os.path.join(self.results_dir, f"simulation_config_{self.config['simulation']['timestamp']}.json")
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)
        
        logger.info(f"Simulation configuration saved to {self.config_path}")
        
        # Initialize components
        # Create a fork config file for Web3Connector
        fork_config_path = os.path.join(self.results_dir, f"fork_config_{self.config['simulation']['timestamp']}.json")
        with open(fork_config_path, "w") as f:
            json.dump({
                "fork": {
                    "url": self.config["fork"]["url"],
                    "block_number": self.config["fork"]["block_number"]
                }
            }, f, indent=2)
        
        self.web3_connector = Web3Connector(fork_config_path=fork_config_path)
        
        # Initialize strategy optimizer
        self.strategy_optimizer = StrategyOptimizer()
        
        # Initialize metrics tracking
        self.metrics = {
            "capital_balance_usd": self.config["simulation"]["initial_capital_usd"],
            "trades_executed": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_profit_usd": 0.0,
            "total_loss_usd": 0.0,
            "total_gas_fees_usd": 0.0,
            "flash_loans_used": 0,
            "flash_loan_fees_usd": 0.0,
            "trade_history": []
        }
    
    def run_simulation(self):
        """
        Run the simulation.
        """
        logger.info("Starting simulation...")
        logger.info(f"Initial capital: ${self.metrics['capital_balance_usd']}")
        
        # Set the start time
        start_time = time.time()
        
        # Run the simulation loop
        while (
            time.time() - start_time < self.config["simulation"]["simulation_time"] and
            self.metrics["trades_executed"] < self.config["simulation"]["max_trades"]
        ):
            # Check if we've reached the minimum number of trades
            if self.metrics["trades_executed"] >= self.config["simulation"]["min_trades"]:
                # Check if we should stop early
                if np.random.random() < 0.1:  # 10% chance to stop early
                    logger.info("Stopping simulation early (random chance).")
                    break
            
            # Execute a trade
            self.execute_trade()
            
            # Sleep for a random amount of time (1-5 seconds)
            time.sleep(np.random.uniform(1, 5))
        
        # Calculate the simulation duration
        duration = time.time() - start_time
        
        # Generate the simulation report
        self.generate_report(duration)
        
        logger.info("Simulation completed.")
        logger.info(f"Final capital: ${self.metrics['capital_balance_usd']}")
        logger.info(f"Trades executed: {self.metrics['trades_executed']}")
        logger.info(f"Successful trades: {self.metrics['successful_trades']}")
        logger.info(f"Failed trades: {self.metrics['failed_trades']}")
        logger.info(f"Total profit: ${self.metrics['total_profit_usd']}")
        logger.info(f"Total loss: ${self.metrics['total_loss_usd']}")
        logger.info(f"Net profit: ${self.metrics['total_profit_usd'] - self.metrics['total_loss_usd']}")
        
        return True
    
    def execute_trade(self):
        """
        Execute a simulated trade.
        """
        # Increment the trade counter
        self.metrics["trades_executed"] += 1
        
        # Randomly select a network, token pair, and DEX
        network = np.random.choice(self.config["networks"])
        token_pair_idx = np.random.randint(0, len(self.config["token_pairs"]))
        token_pair = self.config["token_pairs"][token_pair_idx]
        dex = np.random.choice(self.config["dexes"])
        
        # Create a simulated arbitrage opportunity
        opportunity = {
            "id": f"trade_{self.metrics['trades_executed']}",
            "timestamp": time.time(),
            "network": network,
            "token_in": token_pair[0],
            "token_out": token_pair[1],
            "amount_in_usd": np.random.uniform(1000, 10000),
            "source_dex": dex,
            "target_dex": np.random.choice([d for d in self.config["dexes"] if d != dex]),
            "estimated_profit_usd": np.random.uniform(0, 50),
            "gas_cost_usd": np.random.uniform(1, 20),
            "execution_time_ms": np.random.uniform(100, 5000)
        }
        
        # Calculate the net profit
        opportunity["net_profit_usd"] = opportunity["estimated_profit_usd"] - opportunity["gas_cost_usd"]
        
        # Determine if the trade is profitable
        opportunity["is_profitable"] = opportunity["net_profit_usd"] > self.config["risk"]["min_profit_threshold_usd"]
        
        # Determine if we should use a flash loan
        use_flash_loan = self.config["simulation"]["flash_loan_enabled"] and np.random.random() < 0.7  # 70% chance to use a flash loan
        
        # Calculate flash loan fee if applicable
        flash_loan_fee_usd = 0.0
        if use_flash_loan:
            flash_loan_fee_usd = opportunity["amount_in_usd"] * self.config["flash_loan"]["fee_percentage"]
            opportunity["net_profit_usd"] -= flash_loan_fee_usd
            opportunity["is_profitable"] = opportunity["net_profit_usd"] > self.config["risk"]["min_profit_threshold_usd"]
            self.metrics["flash_loans_used"] += 1
            self.metrics["flash_loan_fees_usd"] += flash_loan_fee_usd
        
        # Determine if the trade is successful (80% chance if profitable, 20% chance if not profitable)
        is_successful = np.random.random() < (0.8 if opportunity["is_profitable"] else 0.2)
        
        # Update metrics
        if is_successful:
            self.metrics["successful_trades"] += 1
            self.metrics["capital_balance_usd"] += opportunity["net_profit_usd"]
            self.metrics["total_profit_usd"] += opportunity["net_profit_usd"]
        else:
            self.metrics["failed_trades"] += 1
            loss = min(opportunity["gas_cost_usd"] + flash_loan_fee_usd, self.config["risk"]["max_loss_per_trade_usd"])
            self.metrics["capital_balance_usd"] -= loss
            self.metrics["total_loss_usd"] += loss
        
        self.metrics["total_gas_fees_usd"] += opportunity["gas_cost_usd"]
        
        # Add the trade to the history
        trade_record = {
            "id": opportunity["id"],
            "timestamp": opportunity["timestamp"],
            "network": opportunity["network"],
            "token_pair": f"{opportunity['token_in']}-{opportunity['token_out']}",
            "source_dex": opportunity["source_dex"],
            "target_dex": opportunity["target_dex"],
            "amount_in_usd": opportunity["amount_in_usd"],
            "estimated_profit_usd": opportunity["estimated_profit_usd"],
            "gas_cost_usd": opportunity["gas_cost_usd"],
            "flash_loan_fee_usd": flash_loan_fee_usd,
            "net_profit_usd": opportunity["net_profit_usd"],
            "is_profitable": opportunity["is_profitable"],
            "is_successful": is_successful,
            "execution_time_ms": opportunity["execution_time_ms"]
        }
        
        self.metrics["trade_history"].append(trade_record)
        
        # Log the trade
        logger.info(f"Trade {self.metrics['trades_executed']}: {'✅' if is_successful else '❌'} {opportunity['token_in']}-{opportunity['token_out']} on {opportunity['network']} ({opportunity['source_dex']} -> {opportunity['target_dex']})")
        logger.info(f"  Profit: ${opportunity['net_profit_usd']:.2f} (Gross: ${opportunity['estimated_profit_usd']:.2f}, Gas: ${opportunity['gas_cost_usd']:.2f}, Flash Loan Fee: ${flash_loan_fee_usd:.2f})")
        logger.info(f"  Capital: ${self.metrics['capital_balance_usd']:.2f}")
    
    def generate_report(self, duration):
        """
        Generate a simulation report.
        
        Args:
            duration: The duration of the simulation in seconds.
        """
        # Create the report
        report = {
            "simulation": {
                "timestamp": self.config["simulation"]["timestamp"],
                "duration_seconds": duration,
                "initial_capital_usd": self.config["simulation"]["initial_capital_usd"],
                "final_capital_usd": self.metrics["capital_balance_usd"],
                "profit_usd": self.metrics["capital_balance_usd"] - self.config["simulation"]["initial_capital_usd"],
                "roi_percentage": (self.metrics["capital_balance_usd"] / self.config["simulation"]["initial_capital_usd"] - 1) * 100,
                "trades_executed": self.metrics["trades_executed"],
                "successful_trades": self.metrics["successful_trades"],
                "failed_trades": self.metrics["failed_trades"],
                "success_rate_percentage": (self.metrics["successful_trades"] / self.metrics["trades_executed"]) * 100 if self.metrics["trades_executed"] > 0 else 0,
                "total_profit_usd": self.metrics["total_profit_usd"],
                "total_loss_usd": self.metrics["total_loss_usd"],
                "net_profit_usd": self.metrics["total_profit_usd"] - self.metrics["total_loss_usd"],
                "total_gas_fees_usd": self.metrics["total_gas_fees_usd"],
                "flash_loans_used": self.metrics["flash_loans_used"],
                "flash_loan_fees_usd": self.metrics["flash_loan_fees_usd"]
            },
            "config": self.config,
            "trade_history": self.metrics["trade_history"]
        }
        
        # Save the report to a file
        report_path = os.path.join(self.results_dir, f"simulation_report_{self.config['simulation']['timestamp']}.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        # Generate a summary
        summary = f"""
ArbitrageX Simple Simulation Summary
====================================
Timestamp: {self.config['simulation']['timestamp']}
Duration: {duration:.2f} seconds

Capital:
  Initial: ${self.config['simulation']['initial_capital_usd']:.2f}
  Final: ${self.metrics['capital_balance_usd']:.2f}
  Profit: ${self.metrics['capital_balance_usd'] - self.config['simulation']['initial_capital_usd']:.2f}
  ROI: {(self.metrics['capital_balance_usd'] / self.config['simulation']['initial_capital_usd'] - 1) * 100:.2f}%

Trades:
  Executed: {self.metrics['trades_executed']}
  Successful: {self.metrics['successful_trades']}
  Failed: {self.metrics['failed_trades']}
  Success Rate: {(self.metrics['successful_trades'] / self.metrics['trades_executed']) * 100 if self.metrics['trades_executed'] > 0 else 0:.2f}%

Financials:
  Total Profit: ${self.metrics['total_profit_usd']:.2f}
  Total Loss: ${self.metrics['total_loss_usd']:.2f}
  Net Profit: ${self.metrics['total_profit_usd'] - self.metrics['total_loss_usd']:.2f}
  Total Gas Fees: ${self.metrics['total_gas_fees_usd']:.2f}
  Flash Loans Used: {self.metrics['flash_loans_used']}
  Flash Loan Fees: ${self.metrics['flash_loan_fees_usd']:.2f}

Networks: {', '.join(self.config['networks'])}
Token Pairs: {', '.join([f"{pair[0]}-{pair[1]}" for pair in self.config['token_pairs']])}
DEXes: {', '.join(self.config['dexes'])}
"""
        
        # Save the summary to a file
        summary_path = os.path.join(self.results_dir, f"simulation_report_{self.config['simulation']['timestamp']}_summary.txt")
        with open(summary_path, "w") as f:
            f.write(summary)
        
        logger.info(f"Simulation report saved to {report_path}")
        logger.info(f"Simulation summary saved to {summary_path}")
        
        return report_path

def main():
    """
    Main function to run the simulation.
    """
    # Create and run the simulation
    simulation = SimpleSimulation()
    success = simulation.run_simulation()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 