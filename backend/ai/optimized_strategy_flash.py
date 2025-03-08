#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArbitrageX Optimized Strategy with Flash Loan Integration

This module enhances the optimized trading strategy with Flash Loan support
to enable capital-efficient trading without requiring substantial upfront capital.
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
        logging.FileHandler("optimized_strategy_flash.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("OptimizedStrategyFlash")


class OptimizedStrategyFlash(OptimizedStrategy):
    """
    Enhanced optimized strategy with Flash Loan support for capital efficiency.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Flash Loan-enhanced optimized strategy.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        # Initialize the base optimized strategy
        super().__init__(config_path)
        
        # Initialize Flash Loan-specific components
        self.flash_loan_manager = FlashLoanManager(config_path)
        self.flash_loan_executor = FlashLoanExecutor(config_path)
        self.flash_loan_evaluator = FlashLoanOpportunityEvaluator(self.flash_loan_manager, config_path)
        
        # Flash Loan-specific configuration
        self.flash_config = {
            "enable_flash_loans": True,
            "prefer_flash_loans": True,  # Prefer flash loans when profitable
            "min_profit_multiplier": 2.0,  # Minimum profit multiplier to use flash loans
            "flash_metrics_dir": "backend/ai/metrics/flash_optimized"
        }
        
        # Update config with Flash Loan-specific settings if available
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    if "flash_config" in loaded_config:
                        self.flash_config.update(loaded_config["flash_config"])
                logger.info(f"Loaded Flash Loan configuration from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load Flash Loan configuration: {e}")
        
        # Create metrics directory
        os.makedirs(self.flash_config["flash_metrics_dir"], exist_ok=True)
        
        # Track Flash Loan-specific performance
        self.flash_trades = 0
        self.flash_successful_trades = 0
        self.flash_total_profit = 0.0
        self.flash_total_fees = 0.0
        self.flash_provider_performance = {
            provider.value: {"trades": 0, "successful_trades": 0, "total_profit": 0.0, "total_fees": 0.0}
            for provider in FlashLoanProvider
        }
        
        logger.info("Flash Loan-enhanced optimized strategy initialized")
    
    def evaluate_opportunity(self, opportunity: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluate a trading opportunity with potential Flash Loan enhancement.
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            Tuple of (should_execute, enhanced_opportunity)
        """
        # First, evaluate using the base strategy
        base_should_execute, base_enhanced = super().evaluate_opportunity(opportunity)
        
        # If Flash Loans are disabled, return the base evaluation
        if not self.flash_config["enable_flash_loans"]:
            return base_should_execute, base_enhanced
        
        # If base strategy rejected the opportunity, no need to evaluate for Flash Loans
        if not base_should_execute:
            return False, base_enhanced
        
        # Add position size to the opportunity for Flash Loan evaluation
        opportunity_with_size = base_enhanced.copy()
        if "position_size" not in opportunity_with_size:
            # Use dynamic position size if available, otherwise default
            opportunity_with_size["position_size"] = opportunity_with_size.get("position_size", 1.0)
        
        # Evaluate for Flash Loan potential
        should_use_flash_loan, flash_enhanced = self.flash_loan_evaluator.evaluate_opportunity(opportunity_with_size)
        
        # If Flash Loan is not suitable, use base evaluation
        if not should_use_flash_loan:
            logger.info("Flash Loan not suitable, using base strategy")
            base_enhanced["use_flash_loan"] = False
            return base_should_execute, base_enhanced
        
        # Compare profitability with and without Flash Loan
        base_profit = base_enhanced.get("expected_profit", 0.0)
        flash_profit = flash_enhanced.get("flash_loan_net_profit", 0.0)
        
        # Decide whether to use Flash Loan
        if self.flash_config["prefer_flash_loans"] and flash_profit > 0:
            # Prefer Flash Loans even if slightly less profitable
            use_flash = True
        else:
            # Use whichever is more profitable
            use_flash = flash_profit > base_profit * self.flash_config["min_profit_multiplier"]
        
        if use_flash:
            logger.info(f"Using Flash Loan with profit ${flash_profit:.2f} (base: ${base_profit:.2f})")
            flash_enhanced["execution_method"] = "flash_loan"
            return True, flash_enhanced
        else:
            logger.info(f"Using base strategy with profit ${base_profit:.2f} (flash: ${flash_profit:.2f})")
            base_enhanced["execution_method"] = "base"
            base_enhanced["use_flash_loan"] = False
            return base_should_execute, base_enhanced
    
    def execute_trade(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trade with or without Flash Loan based on the opportunity.
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            Dictionary with trade results
        """
        # Check which execution method to use
        execution_method = opportunity.get("execution_method", "base")
        
        if execution_method == "flash_loan" and opportunity.get("use_flash_loan", False):
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
                self.flash_total_fees += result.get("fee", 0.0)
            
            # Update provider-specific performance
            provider = result.get("provider")
            if provider in self.flash_provider_performance:
                self.flash_provider_performance[provider]["trades"] += 1
                if result.get("success", False):
                    self.flash_provider_performance[provider]["successful_trades"] += 1
                    self.flash_provider_performance[provider]["total_profit"] += result.get("net_profit", 0.0)
                    self.flash_provider_performance[provider]["total_fees"] += result.get("fee", 0.0)
            
            # Also update base metrics for consistency
            self.total_trades += 1
            if result.get("success", False):
                self.successful_trades += 1
                self.total_profit += result.get("net_profit", 0.0)
            
            return result
        else:
            # Execute using the base strategy
            return super().execute_trade(opportunity)
    
    def save_metrics(self) -> None:
        """Save current performance metrics to a file, including Flash Loan-specific metrics."""
        # Save base metrics
        super().save_metrics()
        
        # Save Flash Loan-specific metrics
        flash_metrics = self.get_flash_metrics()
        
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.flash_config['flash_metrics_dir']}/flash_metrics_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(flash_metrics, f, indent=2)
            logger.info(f"Flash Loan metrics saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save Flash Loan metrics: {e}")
    
    def get_flash_metrics(self) -> Dict[str, Any]:
        """
        Get current Flash Loan-specific performance metrics.
        
        Returns:
            Dictionary with Flash Loan performance metrics
        """
        now = datetime.datetime.now()
        runtime = (now - self.start_time).total_seconds() / 3600  # Runtime in hours
        
        flash_metrics = {
            "timestamp": now.isoformat(),
            "runtime_hours": runtime,
            "flash_trades": self.flash_trades,
            "flash_successful_trades": self.flash_successful_trades,
            "flash_success_rate": (self.flash_successful_trades / self.flash_trades) if self.flash_trades > 0 else 0,
            "flash_total_profit_usd": self.flash_total_profit,
            "flash_total_fees_usd": self.flash_total_fees,
            "flash_average_profit_per_trade": (self.flash_total_profit / self.flash_trades) if self.flash_trades > 0 else 0,
            "flash_profit_per_hour": self.flash_total_profit / runtime if runtime > 0 else 0,
            "flash_provider_performance": self.flash_provider_performance,
            "base_vs_flash_comparison": {
                "base_trades": self.total_trades - self.flash_trades,
                "flash_trades": self.flash_trades,
                "base_profit": self.total_profit - self.flash_total_profit,
                "flash_profit": self.flash_total_profit,
                "base_success_rate": ((self.successful_trades - self.flash_successful_trades) / 
                                     (self.total_trades - self.flash_trades)) 
                                     if (self.total_trades - self.flash_trades) > 0 else 0,
                "flash_success_rate": (self.flash_successful_trades / self.flash_trades) if self.flash_trades > 0 else 0
            }
        }
        
        return flash_metrics


def main():
    """Main function to demonstrate the Flash Loan-enhanced optimized strategy."""
    parser = argparse.ArgumentParser(description="ArbitrageX Flash Loan-Enhanced Optimized Strategy")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--simulate", action="store_true", help="Run a simulation")
    parser.add_argument("--trades", type=int, default=10, help="Number of trades to simulate")
    parser.add_argument("--flash-only", action="store_true", help="Only use Flash Loans")
    args = parser.parse_args()
    
    # Initialize strategy
    strategy = OptimizedStrategyFlash(args.config)
    
    # If flash-only flag is set, update config
    if args.flash_only:
        strategy.flash_config["prefer_flash_loans"] = True
    
    if args.simulate:
        logger.info(f"Running Flash Loan-enhanced simulation with {args.trades} trades")
        
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
                if execution_method == "flash_loan":
                    provider = enhanced.get("flash_loan_provider", "unknown")
                    profit = result.get("net_profit", 0.0)
                    logger.info(f"Trade {i+1}: Flash Loan ({provider}), {result['success']}, ${profit:.2f}")
                else:
                    profit = result.get("profit", 0.0)
                    logger.info(f"Trade {i+1}: Base strategy, {result['success']}, ${profit:.2f}")
            else:
                logger.info(f"Trade {i+1}: Rejected")
        
        # Save final metrics
        strategy.save_metrics()
        
        # Print summary
        metrics = strategy.get_metrics()
        flash_metrics = strategy.get_flash_metrics()
        
        print("\nSimulation Summary:")
        print(f"Total Trades: {metrics['total_trades']}")
        print(f"Successful Trades: {metrics['successful_trades']}")
        print(f"Success Rate: {metrics['success_rate']:.2%}")
        print(f"Total Profit: ${metrics['total_profit_usd']:.2f}")
        print(f"Average Profit per Trade: ${metrics['average_profit_per_trade']:.2f}")
        
        print("\nFlash Loan Performance:")
        print(f"Flash Loan Trades: {flash_metrics['flash_trades']} ({(flash_metrics['flash_trades']/metrics['total_trades']):.2%} of total)")
        print(f"Flash Loan Success Rate: {flash_metrics['flash_success_rate']:.2%}")
        print(f"Flash Loan Total Profit: ${flash_metrics['flash_total_profit_usd']:.2f}")
        print(f"Flash Loan Total Fees: ${flash_metrics['flash_total_fees_usd']:.2f}")
        print(f"Flash Loan Average Profit per Trade: ${flash_metrics['flash_average_profit_per_trade']:.2f}")
        
        # Print provider breakdown if Flash Loan trades were executed
        if flash_metrics['flash_trades'] > 0:
            print("\nFlash Loan Provider Performance:")
            for provider, perf in flash_metrics['flash_provider_performance'].items():
                if perf['trades'] > 0:
                    success_rate = perf['successful_trades'] / perf['trades'] if perf['trades'] > 0 else 0
                    avg_profit = perf['total_profit'] / perf['trades'] if perf['trades'] > 0 else 0
                    avg_fee = perf['total_fees'] / perf['trades'] if perf['trades'] > 0 else 0
                    print(f"  {provider}: {perf['trades']} trades, {success_rate:.2%} success, ${perf['total_profit']:.2f} profit, ${perf['total_fees']:.2f} fees (${avg_profit:.2f}/trade)")
    else:
        logger.info("Flash Loan-enhanced strategy initialized. Use --simulate to run a simulation.")


if __name__ == "__main__":
    main() 