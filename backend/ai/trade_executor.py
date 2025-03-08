#!/usr/bin/env python3
"""
Trade Executor Module for ArbitrageX

This module executes arbitrage trades on a mainnet fork.
It implements various strategies to execute trades efficiently
and profitably, with detailed logging and reporting.
"""

import os
import json
import time
import random
import logging
import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from trade_validator import TradeValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trade_executor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TradeExecutor")

class TradeExecutor:
    """
    Executes trades based on identified arbitrage opportunities.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the trade executor.
        
        Args:
            config_path: Path to the configuration file
        """
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("trade_executor.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("TradeExecutor")
        self.logger.info("Initializing Trade Executor")
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize trade validator if enabled
        self.trade_validator = None
        if self.config.get("enable_trade_validator", True):
            self.trade_validator = TradeValidator()
            self.logger.info("Trade Validator enabled")
        
        # Initialize execution statistics
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_profit": 0.0,
            "total_gas_cost": 0.0,
            "execution_history": []
        }
        
        self.logger.info("Trade Executor initialized successfully")
    
    def _load_config(self, config_path: str):
        """
        Load the configuration from the config file.
        """
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            self.logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return {}
    
    def execute_trades(self, gas_results_path: str) -> str:
        """
        Execute trades from gas optimization.
        
        Args:
            gas_results_path: Path to the gas optimization results file
        
        Returns:
            Path to the trade execution results file
        """
        self.logger.info(f"Executing trades from {gas_results_path}")
        
        # Load gas optimization results
        try:
            with open(gas_results_path, "r") as f:
                gas_results = json.load(f)
            self.logger.info(f"Gas optimization results loaded from {gas_results_path}")
        except Exception as e:
            self.logger.error(f"Error loading gas optimization results: {e}")
            return ""
        
        # Get trades from gas results
        trades = gas_results.get("trades", [])
        self.logger.info(f"Found {len(trades)} trades to execute")
        
        # Execute each trade
        executed_trades = []
        for trade in trades:
            executed_trade = self.execute_trade(trade)
            executed_trades.append(executed_trade)
        
        # Create results
        results = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "config": self.config,
            "trades": executed_trades
        }
        
        # Save results to file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"results/trade_execution_{timestamp}.json")
        
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        self.logger.info(f"Trade execution results saved to {results_file}")
        
        # Log summary
        successful_trades = [t for t in executed_trades if t.get("status", "") == "completed"]
        failed_trades = [t for t in executed_trades if t.get("status", "") == "failed"]
        
        total_profit = sum([t.get("actual_profit", 0) for t in successful_trades])
        avg_profit = total_profit / len(successful_trades) if successful_trades else 0
        avg_execution_time = sum([t.get("execution_time", 0) for t in executed_trades]) / len(executed_trades) if executed_trades else 0
        
        self.logger.info(f"Executed {len(executed_trades)} trades")
        self.logger.info(f"Successful trades: {len(successful_trades)}")
        self.logger.info(f"Failed trades: {len(failed_trades)}")
        self.logger.info(f"Total profit: ${total_profit:.2f}")
        self.logger.info(f"Average profit per trade: ${avg_profit:.2f}")
        self.logger.info(f"Average execution time: {avg_execution_time:.2f} ms")
        
        return results_file
    
    def execute_trade(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trade based on the provided trade details.
        
        Args:
            trade: Trade details
            
        Returns:
            Execution result
        """
        trade_id = trade.get("trade_id", f"trade_{int(time.time())}")
        self.logger.info(f"Executing trade {trade_id}")
        
        # Validate trade if validator is enabled
        if self.trade_validator:
            validation_result = self.trade_validator.validate_trade(trade)
            
            # If trade is not valid, return early with validation result
            if not validation_result["is_valid"]:
                self.logger.warning(f"Trade {trade_id} failed validation with score {validation_result['validation_score']:.2f}: {validation_result['failure_reasons']}")
                
                # Update execution statistics
                self.execution_stats["total_executions"] += 1
                self.execution_stats["failed_executions"] += 1
                
                # Add to execution history
                execution_result = {
                    "trade_id": trade_id,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "status": "rejected",
                    "reason": "Failed validation",
                    "validation_result": validation_result,
                    "execution_time": 0,
                    "gas_used": 0,
                    "gas_cost": 0,
                    "profit": 0,
                    "net_profit": 0
                }
                
                self.execution_stats["execution_history"].append(execution_result)
                
                return execution_result
            
            self.logger.info(f"Trade {trade_id} passed validation with score {validation_result['validation_score']:.2f}")
        
        # Start execution timer
        start_time = time.time()
        
        # Execute the trade
        try:
            # Simulate trade execution
            # In a real implementation, this would call the smart contract
            execution_time = random.uniform(0.5, 2.0)  # Simulate execution time
            time.sleep(execution_time)  # Simulate blockchain confirmation time
            
            # Get trade details
            token_pair = trade.get("token_pair", "unknown")
            network = trade.get("network", "unknown")
            dex = trade.get("dex", "unknown")
            amount = trade.get("amount", 0)
            expected_profit = trade.get("expected_profit", 0)
            
            # Simulate gas usage and cost
            gas_price = trade.get("gas_price", 50)  # Gwei
            gas_used = trade.get("gas_used", 200000)  # Gas units
            gas_cost = trade.get("gas_cost", 5.0)  # USD
            
            # Simulate actual profit (slightly different from expected)
            profit_variation = random.uniform(-0.1, 0.1)  # +/- 10%
            actual_profit = expected_profit * (1 + profit_variation)
            
            # Calculate net profit
            net_profit = actual_profit - gas_cost
            
            # Update execution statistics
            self.execution_stats["total_executions"] += 1
            self.execution_stats["successful_executions"] += 1
            self.execution_stats["total_profit"] += actual_profit
            self.execution_stats["total_gas_cost"] += gas_cost
            
            # Create execution result
            execution_result = {
                "trade_id": trade_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "completed",
                "token_pair": token_pair,
                "network": network,
                "dex": dex,
                "amount": amount,
                "expected_profit": expected_profit,
                "actual_profit": actual_profit,
                "execution_time": execution_time,
                "gas_price": gas_price,
                "gas_used": gas_used,
                "gas_cost": gas_cost,
                "net_profit": net_profit
            }
            
            # Add validation result if available
            if self.trade_validator:
                execution_result["validation_result"] = validation_result
            
            # Add to execution history
            self.execution_stats["execution_history"].append(execution_result)
            
            self.logger.info(f"Trade {trade_id} executed successfully: profit=${actual_profit:.2f}, gas=${gas_cost:.2f}, net=${net_profit:.2f}")
            
            return execution_result
        except Exception as e:
            self.logger.error(f"Error executing trade {trade_id}: {e}")
            
            # Update execution statistics
            self.execution_stats["total_executions"] += 1
            self.execution_stats["failed_executions"] += 1
            
            # Create execution result
            execution_result = {
                "trade_id": trade_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "failed",
                "error": str(e),
                "execution_time": time.time() - start_time
            }
            
            # Add validation result if available
            if self.trade_validator:
                execution_result["validation_result"] = validation_result
            
            # Add to execution history
            self.execution_stats["execution_history"].append(execution_result)
            
            return execution_result
    
    def simulate_flash_loan(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate a flash loan for a trade.
        
        Args:
            trade: Trade to simulate flash loan for
        
        Returns:
            Flash loan details
        """
        # Determine flash loan amount based on trade size
        token_pair = self.config.get("token_pair", ["WETH", "USDC"])
        trade_size = self.config.get("trade_size", {"eth_amount": 0.1, "usdc_amount": 100})
        
        if token_pair[0] == "WETH":
            flash_loan_amount = trade_size.get("eth_amount", 0.1) * 10  # 10x leverage
            flash_loan_token = "WETH"
        else:
            flash_loan_amount = trade_size.get("usdc_amount", 100) * 10  # 10x leverage
            flash_loan_token = "USDC"
        
        # Calculate flash loan fee (0.09% for Aave V3)
        flash_loan_fee_percentage = 0.0009
        flash_loan_fee = flash_loan_amount * flash_loan_fee_percentage
        
        # Create flash loan details
        flash_loan = {
            "token": flash_loan_token,
            "amount": flash_loan_amount,
            "fee_percentage": flash_loan_fee_percentage,
            "fee": flash_loan_fee,
            "provider": "Aave V3"
        }
        
        logger.info(f"Simulated flash loan: {flash_loan_amount} {flash_loan_token} with fee {flash_loan_fee} {flash_loan_token}")
        
        return flash_loan
    
    def simulate_dex_swap(self, trade: Dict[str, Any], flash_loan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate a DEX swap for a trade.
        
        Args:
            trade: Trade to simulate DEX swap for
            flash_loan: Flash loan details
        
        Returns:
            DEX swap details
        """
        # Get trade details
        token_pair = self.config.get("token_pair", ["WETH", "USDC"])
        dex = self.config.get("dex", "uniswap_v3")
        
        # Determine swap direction
        from_token = token_pair[0]
        to_token = token_pair[1]
        
        # Determine swap amount (use flash loan amount)
        from_amount = flash_loan.get("amount", 0)
        
        # Simulate price impact (0.1-0.5%)
        price_impact_percentage = random.uniform(0.001, 0.005)
        price_impact = from_amount * price_impact_percentage
        
        # Determine exchange rate
        if from_token == "WETH" and to_token == "USDC":
            exchange_rate = 3000.0  # 1 ETH = 3000 USDC
        elif from_token == "USDC" and to_token == "WETH":
            exchange_rate = 1 / 3000.0  # 3000 USDC = 1 ETH
        else:
            exchange_rate = 1.0
        
        # Calculate to amount
        to_amount = from_amount * exchange_rate * (1 - price_impact_percentage)
        
        # Create DEX swap details
        dex_swap = {
            "dex": dex,
            "from_token": from_token,
            "to_token": to_token,
            "from_amount": from_amount,
            "to_amount": to_amount,
            "exchange_rate": exchange_rate,
            "price_impact_percentage": price_impact_percentage,
            "price_impact": price_impact
        }
        
        logger.info(f"Simulated DEX swap: {from_amount} {from_token} to {to_amount} {to_token} on {dex}")
        
        return dex_swap

if __name__ == "__main__":
    # Example usage
    config_path = "small_scale_test_config.json"
    gas_results_path = "results/gas_estimation_20250301_101017.json"
    
    executor = TradeExecutor(config_path)
    results_file = executor.execute_trades(gas_results_path)
    
    print(f"Trade execution results saved to {results_file}") 