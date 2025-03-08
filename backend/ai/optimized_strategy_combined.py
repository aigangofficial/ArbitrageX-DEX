#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArbitrageX Combined Optimized Strategy

This module combines Layer 2 and Flash Loan enhancements into a single strategy
for maximum profitability through both gas cost reduction and capital efficiency.
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

# Import Flash Loan integration components
from flash_loan_integration import (
    FlashLoanProvider, FlashLoanInfo, FlashLoanManager,
    FlashLoanExecutor, FlashLoanOpportunityEvaluator
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("optimized_strategy_combined.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("OptimizedStrategyCombined")


class OptimizedStrategyCombined(OptimizedStrategy):
    """
    Combined optimized strategy with both Layer 2 and Flash Loan support
    for maximum profitability.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the combined optimized strategy.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        # Initialize the base optimized strategy
        super().__init__(config_path)
        
        # Initialize Layer 2 components
        self.l2_gas_tracker = L2GasTracker(config_path)
        self.l2_opportunity_evaluator = L2OpportunityEvaluator(self.l2_gas_tracker, config_path)
        self.l2_executor = L2Executor(config_path)
        
        # Initialize Flash Loan components
        self.flash_loan_manager = FlashLoanManager(config_path)
        self.flash_loan_executor = FlashLoanExecutor(config_path)
        self.flash_loan_evaluator = FlashLoanOpportunityEvaluator(self.flash_loan_manager, config_path)
        
        # Combined configuration
        self.combined_config = {
            "enable_l2": True,
            "enable_flash_loans": True,
            "prefer_l2": True,
            "prefer_flash_loans": True,
            "l2_flash_combined": True,  # Enable L2 + Flash Loan combined execution
            "metrics_dir": "backend/ai/metrics/combined_optimized"
        }
        
        # Update config with combined settings if available
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    if "combined_config" in loaded_config:
                        self.combined_config.update(loaded_config["combined_config"])
                logger.info(f"Loaded combined configuration from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load combined configuration: {e}")
        
        # Create metrics directory
        os.makedirs(self.combined_config["metrics_dir"], exist_ok=True)
        
        # Track combined performance metrics
        self.l2_trades = 0
        self.flash_trades = 0
        self.l2_flash_trades = 0  # Trades using both L2 and Flash Loans
        self.l2_successful_trades = 0
        self.flash_successful_trades = 0
        self.l2_flash_successful_trades = 0
        self.l2_total_profit = 0.0
        self.flash_total_profit = 0.0
        self.l2_flash_total_profit = 0.0
        
        # Network and provider performance
        self.l2_network_performance = {
            network.value: {"trades": 0, "successful_trades": 0, "total_profit": 0.0}
            for network in L2Network
        }
        self.flash_provider_performance = {
            provider.value: {"trades": 0, "successful_trades": 0, "total_profit": 0.0}
            for provider in FlashLoanProvider
        }
        
        logger.info("Combined optimized strategy initialized")
    
    def evaluate_opportunity(self, opportunity: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluate a trading opportunity with both Layer 2 and Flash Loan enhancements.
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            Tuple of (should_execute, enhanced_opportunity)
        """
        # First, evaluate using the base strategy
        base_should_execute, base_enhanced = super().evaluate_opportunity(opportunity)
        
        # If base strategy rejected the opportunity, no need to evaluate further
        if not base_should_execute:
            return False, base_enhanced
        
        # Add position size to the opportunity if not present
        opportunity_with_size = base_enhanced.copy()
        if "position_size" not in opportunity_with_size:
            opportunity_with_size["position_size"] = opportunity_with_size.get("position_size", 1.0)
        
        # Initialize execution options
        execution_options = {
            "base": {
                "should_execute": base_should_execute,
                "enhanced": base_enhanced,
                "profit": base_enhanced.get("expected_profit", 0.0),
                "method": "base"
            }
        }
        
        # Evaluate for Layer 2 if enabled
        if self.combined_config["enable_l2"]:
            l2_best_network, l2_enhanced = self.l2_opportunity_evaluator.find_best_l2_network(opportunity_with_size)
            
            if l2_best_network:
                l2_profit = l2_enhanced.get("l2_net_profit_usd", 0.0)
                l2_enhanced["execution_method"] = "l2"
                l2_enhanced["execution_layer"] = "L2"
                
                execution_options["l2"] = {
                    "should_execute": True,
                    "enhanced": l2_enhanced,
                    "profit": l2_profit,
                    "method": "l2",
                    "network": l2_best_network.value
                }
        
        # Evaluate for Flash Loan if enabled
        if self.combined_config["enable_flash_loans"]:
            should_use_flash_loan, flash_enhanced = self.flash_loan_evaluator.evaluate_opportunity(opportunity_with_size)
            
            if should_use_flash_loan:
                flash_profit = flash_enhanced.get("flash_loan_net_profit", 0.0)
                flash_enhanced["execution_method"] = "flash_loan"
                
                execution_options["flash"] = {
                    "should_execute": True,
                    "enhanced": flash_enhanced,
                    "profit": flash_profit,
                    "method": "flash_loan",
                    "provider": flash_enhanced.get("flash_loan_provider", "")
                }
        
        # Evaluate combined L2 + Flash Loan if both are enabled
        if self.combined_config["enable_l2"] and self.combined_config["enable_flash_loans"] and self.combined_config["l2_flash_combined"]:
            if "l2" in execution_options and "flash" in execution_options:
                # Create a combined opportunity
                l2_flash_enhanced = l2_enhanced.copy()
                
                # Add Flash Loan details to the L2 opportunity
                for key, value in flash_enhanced.items():
                    if key.startswith("flash_loan_"):
                        l2_flash_enhanced[key] = value
                
                l2_flash_enhanced["use_flash_loan"] = True
                l2_flash_enhanced["execution_method"] = "l2_flash"
                l2_flash_enhanced["execution_layer"] = "L2"
                
                # Calculate combined profit (L2 gas savings + Flash Loan profit amplification)
                # This is a simplified calculation; in production, this would be more sophisticated
                l2_gas_savings = base_enhanced.get("expected_profit", 0.0) - l2_enhanced.get("l2_net_profit_usd", 0.0)
                flash_profit_multiplier = flash_enhanced.get("flash_loan_amount", 1.0) / opportunity_with_size.get("position_size", 1.0)
                l2_flash_profit = l2_enhanced.get("l2_net_profit_usd", 0.0) * flash_profit_multiplier
                
                # Subtract Flash Loan fee
                flash_fee_usd = flash_enhanced.get("flash_loan_fee_usd", 0.0)
                l2_flash_profit -= flash_fee_usd
                
                l2_flash_enhanced["l2_flash_profit"] = l2_flash_profit
                
                execution_options["l2_flash"] = {
                    "should_execute": True,
                    "enhanced": l2_flash_enhanced,
                    "profit": l2_flash_profit,
                    "method": "l2_flash",
                    "network": l2_best_network.value,
                    "provider": flash_enhanced.get("flash_loan_provider", "")
                }
        
        # Select the best execution option
        best_option = "base"
        best_profit = execution_options["base"]["profit"]
        
        for option, details in execution_options.items():
            if option == "base":
                continue
                
            option_profit = details["profit"]
            
            # Apply preferences
            if option == "l2" and self.combined_config["prefer_l2"] and option_profit > 0:
                # Prefer L2 even if slightly less profitable
                if option_profit > best_profit * 0.9:
                    best_option = option
                    best_profit = option_profit
            elif option == "flash" and self.combined_config["prefer_flash_loans"] and option_profit > 0:
                # Prefer Flash Loans even if slightly less profitable
                if option_profit > best_profit * 0.9:
                    best_option = option
                    best_profit = option_profit
            elif option == "l2_flash" and self.combined_config["l2_flash_combined"] and option_profit > 0:
                # Always prefer combined approach if profitable
                if option_profit > best_profit * 0.8:
                    best_option = option
                    best_profit = option_profit
            else:
                # Otherwise, use whichever is most profitable
                if option_profit > best_profit:
                    best_option = option
                    best_profit = option_profit
        
        # Log the selected option
        if best_option == "base":
            logger.info(f"Using base strategy with profit ${best_profit:.2f}")
        elif best_option == "l2":
            network = execution_options[best_option]["network"]
            logger.info(f"Using L2 ({network}) with profit ${best_profit:.2f}")
        elif best_option == "flash":
            provider = execution_options[best_option]["provider"]
            logger.info(f"Using Flash Loan ({provider}) with profit ${best_profit:.2f}")
        elif best_option == "l2_flash":
            network = execution_options[best_option]["network"]
            provider = execution_options[best_option]["provider"]
            logger.info(f"Using combined L2 ({network}) + Flash Loan ({provider}) with profit ${best_profit:.2f}")
        
        return execution_options[best_option]["should_execute"], execution_options[best_option]["enhanced"]
    
    def execute_trade(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trade using the selected execution method.
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            Dictionary with trade results
        """
        # Check which execution method to use
        execution_method = opportunity.get("execution_method", "base")
        
        if execution_method == "l2":
            # Execute on Layer 2
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
            
        elif execution_method == "flash_loan":
            # Execute with Flash Loan
            # Create flash loan info
            loan_info = FlashLoanInfo(
                provider=FlashLoanProvider(opportunity["flash_loan_provider"]),
                token=opportunity["flash_loan_token"],
                amount=opportunity["flash_loan_amount"],
                fee_percentage=self.flash_loan_manager.provider_data[FlashLoanProvider(opportunity["flash_loan_provider"])]["fee_percentage"],
                max_loan_amount=self.flash_loan_manager.provider_data[FlashLoanProvider(opportunity["flash_loan_provider"])]["token_limits"].get(opportunity["flash_loan_token"], 0)
            )
            
            # Execute the flash loan
            result = self.flash_loan_executor.execute_flash_loan(loan_info, opportunity)
            
            # Update Flash Loan-specific metrics
            self.flash_trades += 1
            if result.get("success", False):
                self.flash_successful_trades += 1
                self.flash_total_profit += result.get("net_profit", 0.0)
            
            # Update provider-specific performance
            provider = result.get("provider")
            if provider in self.flash_provider_performance:
                self.flash_provider_performance[provider]["trades"] += 1
                if result.get("success", False):
                    self.flash_provider_performance[provider]["successful_trades"] += 1
                    self.flash_provider_performance[provider]["total_profit"] += result.get("net_profit", 0.0)
            
            # Also update base metrics for consistency
            self.total_trades += 1
            if result.get("success", False):
                self.successful_trades += 1
                self.total_profit += result.get("net_profit", 0.0)
            
            return result
            
        elif execution_method == "l2_flash":
            # Execute combined L2 + Flash Loan
            # First, prepare the L2 transaction
            l2_result = self.l2_executor.execute_trade(opportunity)
            
            if not l2_result.get("success", False):
                # If L2 transaction fails, return the result
                logger.warning(f"L2 transaction failed: {l2_result.get('error', 'unknown error')}")
                return l2_result
            
            # Create flash loan info
            loan_info = FlashLoanInfo(
                provider=FlashLoanProvider(opportunity["flash_loan_provider"]),
                token=opportunity["flash_loan_token"],
                amount=opportunity["flash_loan_amount"],
                fee_percentage=self.flash_loan_manager.provider_data[FlashLoanProvider(opportunity["flash_loan_provider"])]["fee_percentage"],
                max_loan_amount=self.flash_loan_manager.provider_data[FlashLoanProvider(opportunity["flash_loan_provider"])]["token_limits"].get(opportunity["flash_loan_token"], 0)
            )
            
            # Execute the flash loan on the L2 network
            flash_result = self.flash_loan_executor.execute_flash_loan(loan_info, opportunity)
            
            # Combine the results
            combined_result = {
                "success": flash_result.get("success", False),
                "network": l2_result.get("network", ""),
                "provider": flash_result.get("provider", ""),
                "token_pair": opportunity.get("token_pair", ""),
                "profit": flash_result.get("net_profit", 0.0),
                "gas_used": l2_result.get("gas_used", 0.0),
                "flash_loan_amount": opportunity.get("flash_loan_amount", 0.0),
                "flash_loan_fee": flash_result.get("fee", 0.0),
                "timestamp": time.time(),
                "execution_method": "l2_flash"
            }
            
            # Update combined metrics
            self.l2_flash_trades += 1
            if combined_result["success"]:
                self.l2_flash_successful_trades += 1
                self.l2_flash_total_profit += combined_result["profit"]
            
            # Update network-specific performance
            network = l2_result.get("network")
            if network in self.l2_network_performance:
                self.l2_network_performance[network]["trades"] += 1
                if combined_result["success"]:
                    self.l2_network_performance[network]["successful_trades"] += 1
                    self.l2_network_performance[network]["total_profit"] += combined_result["profit"]
            
            # Update provider-specific performance
            provider = flash_result.get("provider")
            if provider in self.flash_provider_performance:
                self.flash_provider_performance[provider]["trades"] += 1
                if combined_result["success"]:
                    self.flash_provider_performance[provider]["successful_trades"] += 1
                    self.flash_provider_performance[provider]["total_profit"] += combined_result["profit"]
            
            # Also update base metrics for consistency
            self.total_trades += 1
            if combined_result["success"]:
                self.successful_trades += 1
                self.total_profit += combined_result["profit"]
            
            return combined_result
        else:
            # Execute using the base strategy
            return super().execute_trade(opportunity)
    
    def save_metrics(self) -> None:
        """Save current performance metrics to a file, including combined metrics."""
        # Save base metrics
        super().save_metrics()
        
        # Save combined metrics
        combined_metrics = self.get_combined_metrics()
        
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.combined_config['metrics_dir']}/combined_metrics_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(combined_metrics, f, indent=2)
            logger.info(f"Combined metrics saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save combined metrics: {e}")
    
    def get_combined_metrics(self) -> Dict[str, Any]:
        """
        Get current combined performance metrics.
        
        Returns:
            Dictionary with combined performance metrics
        """
        now = datetime.datetime.now()
        runtime = (now - self.start_time).total_seconds() / 3600  # Runtime in hours
        
        combined_metrics = {
            "timestamp": now.isoformat(),
            "runtime_hours": runtime,
            "total_trades": self.total_trades,
            "successful_trades": self.successful_trades,
            "success_rate": (self.successful_trades / self.total_trades) if self.total_trades > 0 else 0,
            "total_profit_usd": self.total_profit,
            "average_profit_per_trade": (self.total_profit / self.total_trades) if self.total_trades > 0 else 0,
            "profit_per_hour": self.total_profit / runtime if runtime > 0 else 0,
            "execution_breakdown": {
                "base_trades": self.total_trades - self.l2_trades - self.flash_trades - self.l2_flash_trades,
                "l2_trades": self.l2_trades,
                "flash_trades": self.flash_trades,
                "l2_flash_trades": self.l2_flash_trades
            },
            "l2_metrics": {
                "trades": self.l2_trades,
                "successful_trades": self.l2_successful_trades,
                "success_rate": (self.l2_successful_trades / self.l2_trades) if self.l2_trades > 0 else 0,
                "total_profit_usd": self.l2_total_profit,
                "average_profit_per_trade": (self.l2_total_profit / self.l2_trades) if self.l2_trades > 0 else 0,
                "network_performance": self.l2_network_performance
            },
            "flash_metrics": {
                "trades": self.flash_trades,
                "successful_trades": self.flash_successful_trades,
                "success_rate": (self.flash_successful_trades / self.flash_trades) if self.flash_trades > 0 else 0,
                "total_profit_usd": self.flash_total_profit,
                "average_profit_per_trade": (self.flash_total_profit / self.flash_trades) if self.flash_trades > 0 else 0,
                "provider_performance": self.flash_provider_performance
            },
            "l2_flash_metrics": {
                "trades": self.l2_flash_trades,
                "successful_trades": self.l2_flash_successful_trades,
                "success_rate": (self.l2_flash_successful_trades / self.l2_flash_trades) if self.l2_flash_trades > 0 else 0,
                "total_profit_usd": self.l2_flash_total_profit,
                "average_profit_per_trade": (self.l2_flash_total_profit / self.l2_flash_trades) if self.l2_flash_trades > 0 else 0
            }
        }
        
        return combined_metrics


def main():
    """Main function to demonstrate the combined optimized strategy."""
    parser = argparse.ArgumentParser(description="ArbitrageX Combined Optimized Strategy")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--simulate", action="store_true", help="Run a simulation")
    parser.add_argument("--trades", type=int, default=10, help="Number of trades to simulate")
    parser.add_argument("--l2-only", action="store_true", help="Only use Layer 2 networks")
    parser.add_argument("--flash-only", action="store_true", help="Only use Flash Loans")
    parser.add_argument("--combined-only", action="store_true", help="Only use combined L2 + Flash Loan execution")
    args = parser.parse_args()
    
    # Initialize strategy
    strategy = OptimizedStrategyCombined(args.config)
    
    # Apply command-line flags
    if args.l2_only:
        strategy.combined_config["enable_flash_loans"] = False
        strategy.combined_config["l2_flash_combined"] = False
    elif args.flash_only:
        strategy.combined_config["enable_l2"] = False
        strategy.combined_config["l2_flash_combined"] = False
    elif args.combined_only:
        strategy.combined_config["prefer_l2"] = False
        strategy.combined_config["prefer_flash_loans"] = False
    
    if args.simulate:
        logger.info(f"Running combined simulation with {args.trades} trades")
        
        # Simulate trades
        for i in range(args.trades):
            # Generate a random opportunity with more favorable parameters
            opportunity = {
                "token_pair": random.choice(["WETH-USDC", "WETH-DAI", "WBTC-USDC", "LINK-USDC"]),
                "dex": random.choice(["curve", "balancer", "sushiswap"]),
                "expected_profit": random.uniform(20, 100),  # Higher profit
                "expected_profit_pct": random.uniform(0.01, 0.05),  # Higher profit percentage
                "gas_price": random.uniform(10, 25),  # Lower gas price
                "estimated_gas": random.uniform(150000, 250000),  # Lower gas usage
                "position_size": random.uniform(0.5, 2.0)  # Position size in ETH or equivalent
            }
            
            # Evaluate opportunity
            should_execute, enhanced = strategy.evaluate_opportunity(opportunity)
            
            # Execute trade if approved
            if should_execute:
                result = strategy.execute_trade(enhanced)
                execution_method = enhanced.get("execution_method", "base")
                
                if execution_method == "base":
                    profit = result.get("profit", 0.0)
                    logger.info(f"Trade {i+1}: Base strategy, {result['success']}, ${profit:.2f}")
                elif execution_method == "l2":
                    network = enhanced.get("execution_layer", "L2")
                    profit = result.get("net_profit", 0.0)
                    logger.info(f"Trade {i+1}: {network}, {result['success']}, ${profit:.2f}")
                elif execution_method == "flash_loan":
                    provider = enhanced.get("flash_loan_provider", "unknown")
                    profit = result.get("net_profit", 0.0)
                    logger.info(f"Trade {i+1}: Flash Loan ({provider}), {result['success']}, ${profit:.2f}")
                elif execution_method == "l2_flash":
                    network = enhanced.get("execution_layer", "L2")
                    provider = enhanced.get("flash_loan_provider", "unknown")
                    profit = result.get("profit", 0.0)
                    logger.info(f"Trade {i+1}: {network} + Flash Loan ({provider}), {result['success']}, ${profit:.2f}")
            else:
                logger.info(f"Trade {i+1}: Rejected")
        
        # Save final metrics
        strategy.save_metrics()
        
        # Print summary
        metrics = strategy.get_metrics()
        combined_metrics = strategy.get_combined_metrics()
        
        print("\nSimulation Summary:")
        print(f"Total Trades: {metrics['total_trades']}")
        print(f"Successful Trades: {metrics['successful_trades']}")
        print(f"Success Rate: {metrics['success_rate']:.2%}")
        print(f"Total Profit: ${metrics['total_profit_usd']:.2f}")
        print(f"Average Profit per Trade: ${metrics['average_profit_per_trade']:.2f}")
        
        print("\nExecution Breakdown:")
        execution_breakdown = combined_metrics["execution_breakdown"]
        total = metrics['total_trades']
        print(f"Base Strategy: {execution_breakdown['base_trades']} trades ({(execution_breakdown['base_trades']/total):.2%})")
        print(f"Layer 2: {execution_breakdown['l2_trades']} trades ({(execution_breakdown['l2_trades']/total):.2%})")
        print(f"Flash Loan: {execution_breakdown['flash_trades']} trades ({(execution_breakdown['flash_trades']/total):.2%})")
        print(f"L2 + Flash Loan: {execution_breakdown['l2_flash_trades']} trades ({(execution_breakdown['l2_flash_trades']/total):.2%})")
        
        # Print L2 network performance if L2 trades were executed
        l2_metrics = combined_metrics["l2_metrics"]
        if l2_metrics['trades'] > 0:
            print("\nLayer 2 Network Performance:")
            for network, perf in l2_metrics['network_performance'].items():
                if perf['trades'] > 0:
                    success_rate = perf['successful_trades'] / perf['trades'] if perf['trades'] > 0 else 0
                    avg_profit = perf['total_profit'] / perf['trades'] if perf['trades'] > 0 else 0
                    print(f"  {network}: {perf['trades']} trades, {success_rate:.2%} success, ${perf['total_profit']:.2f} profit (${avg_profit:.2f}/trade)")
        
        # Print Flash Loan provider performance if Flash Loan trades were executed
        flash_metrics = combined_metrics["flash_metrics"]
        if flash_metrics['trades'] > 0:
            print("\nFlash Loan Provider Performance:")
            for provider, perf in flash_metrics['provider_performance'].items():
                if perf['trades'] > 0:
                    success_rate = perf['successful_trades'] / perf['trades'] if perf['trades'] > 0 else 0
                    avg_profit = perf['total_profit'] / perf['trades'] if perf['trades'] > 0 else 0
                    print(f"  {provider}: {perf['trades']} trades, {success_rate:.2%} success, ${perf['total_profit']:.2f} profit (${avg_profit:.2f}/trade)")
        
        # Print combined L2 + Flash Loan performance if any such trades were executed
        l2_flash_metrics = combined_metrics["l2_flash_metrics"]
        if l2_flash_metrics['trades'] > 0:
            print("\nCombined L2 + Flash Loan Performance:")
            print(f"Trades: {l2_flash_metrics['trades']}")
            print(f"Success Rate: {l2_flash_metrics['success_rate']:.2%}")
            print(f"Total Profit: ${l2_flash_metrics['total_profit_usd']:.2f}")
            print(f"Average Profit per Trade: ${l2_flash_metrics['average_profit_per_trade']:.2f}")
    else:
        logger.info("Combined strategy initialized. Use --simulate to run a simulation.")


if __name__ == "__main__":
    main() 