#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArbitrageX MEV-Protected Combined Strategy

This module combines Layer 2, Flash Loan, and MEV protection into a single strategy
for maximum profitability and security against front-running and sandwich attacks.
"""

import os
import json
import time
import logging
import random
import datetime
import argparse
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum

# Import the combined strategy components
from optimized_strategy_combined import (
    OptimizedStrategyCombined
)

# Import MEV protection components
from mev_protection import (
    MEVProtectionManager, MEVRiskLevel, ProtectionMethod
)

# Import MEV protection integration
from mev_protection_integration import (
    MEVProtectionIntegrator, ProtectionLevel
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("optimized_strategy_mev_protected.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("MEVProtectedStrategy")


class OptimizedStrategyMEVProtected(OptimizedStrategyCombined):
    """
    Combined optimized strategy with MEV protection.
    
    This strategy extends the combined strategy (Layer 2 + Flash Loan)
    with MEV protection to prevent front-running and sandwich attacks.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the MEV-protected combined strategy.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        # Initialize the base combined strategy
        super().__init__(config_path)
        
        # Initialize MEV protection integrator
        self.mev_protection_integrator = MEVProtectionIntegrator(config_path)
        
        # MEV protection configuration
        self.mev_config = {
            "enabled": True,
            "default_protection_level": ProtectionLevel.ENHANCED.value,
            "metrics_dir": "backend/ai/metrics/mev_protected"
        }
        
        # Update config with MEV protection settings if available
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    if "mev_config" in loaded_config:
                        self.mev_config.update(loaded_config["mev_config"])
                logger.info(f"Loaded MEV protection configuration from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load MEV protection configuration: {e}")
        
        # Create metrics directory
        os.makedirs(self.mev_config["metrics_dir"], exist_ok=True)
        
        # Track MEV-related metrics
        self.mev_protected_trades = 0
        self.mev_unprotected_trades = 0
        self.mev_protection_failures = 0
        self.mev_profit_saved = 0.0
        self.mev_protection_level_stats = {level.value: 0 for level in ProtectionLevel}
        
        logger.info("MEV-Protected Combined Strategy initialized")
    
    def evaluate_opportunity(self, opportunity: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluate a trading opportunity with MEV protection consideration.
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            Tuple of (should_execute, enhanced_opportunity)
        """
        # First, evaluate using the combined strategy
        should_execute, enhanced = super().evaluate_opportunity(opportunity)
        
        # If combined strategy rejected the opportunity, no need to evaluate further
        if not should_execute:
            return False, enhanced
        
        # Enhance with MEV protection
        mev_enhanced = self.mev_protection_integrator.enhance_opportunity_with_protection(enhanced)
        
        # Check if the opportunity should be skipped due to MEV risk
        if not mev_enhanced.get("should_execute", True):
            logger.warning(f"Opportunity for {mev_enhanced.get('token_pair', 'unknown')} rejected due to extreme MEV risk")
            return False, mev_enhanced
        
        return True, mev_enhanced
    
    def execute_trade(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trade with MEV protection.
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            Dictionary with trade results
        """
        # IMPORTANT: In a real implementation, you would use the actual private key
        # This is just a placeholder for simulation purposes
        example_private_key = "0x0000000000000000000000000000000000000000000000000000000000000001"
        
        # Check if MEV protection is enabled for this opportunity
        mev_protection = opportunity.get("mev_protection", {})
        is_protected = mev_protection.get("enabled", False)
        
        if not is_protected:
            # Execute without MEV protection using the combined strategy
            self.mev_unprotected_trades += 1
            result = super().execute_trade(opportunity)
            result["mev_protected"] = False
            return result
        
        # Execute with MEV protection
        try:
            # Apply MEV protection
            protection_level = mev_protection.get("level", ProtectionLevel.BASIC.value)
            self.mev_protection_level_stats[protection_level] += 1
            
            # Get the execution method from the opportunity
            execution_method = opportunity.get("execution_method", "base")
            
            # Execute the MEV-protected transaction
            mev_result = self.mev_protection_integrator.execute_protected_transaction(opportunity, example_private_key)
            
            if mev_result["success"]:
                self.mev_protected_trades += 1
                
                # Update profit saved if available
                if "profit_saved" in mev_result:
                    self.mev_profit_saved += mev_result["profit_saved"]
                
                # Create a combined result with all necessary information
                combined_result = {
                    "success": True,
                    "mev_protected": True,
                    "protection_level": protection_level,
                    "protection_method": mev_result.get("protection_method", "unknown"),
                    "tx_hash": mev_result.get("tx_hash", ""),
                    "network": opportunity.get("network", ""),
                    "dex": opportunity.get("dex", ""),
                    "token_pair": opportunity.get("token_pair", ""),
                    "execution_method": execution_method,
                    "profit": float(opportunity.get("expected_profit", 0.0)),  # Simulated profit
                    "profit_saved_from_mev": mev_result.get("profit_saved", 0.0),
                    "timestamp": time.time()
                }
                
                # Update base metrics for consistency
                self.total_trades += 1
                self.successful_trades += 1
                self.total_profit += combined_result["profit"]
                
                # Update execution method specific metrics
                if execution_method == "l2":
                    self.l2_trades += 1
                    self.l2_successful_trades += 1
                    self.l2_total_profit += combined_result["profit"]
                    
                    # Update network-specific performance
                    network = opportunity.get("network", "")
                    if network in self.l2_network_performance:
                        self.l2_network_performance[network]["trades"] += 1
                        self.l2_network_performance[network]["successful_trades"] += 1
                        self.l2_network_performance[network]["total_profit"] += combined_result["profit"]
                    
                elif execution_method == "flash_loan":
                    self.flash_trades += 1
                    self.flash_successful_trades += 1
                    self.flash_total_profit += combined_result["profit"]
                    
                    # Update provider-specific performance
                    provider = opportunity.get("flash_loan_provider", "")
                    if provider in self.flash_provider_performance:
                        self.flash_provider_performance[provider]["trades"] += 1
                        self.flash_provider_performance[provider]["successful_trades"] += 1
                        self.flash_provider_performance[provider]["total_profit"] += combined_result["profit"]
                    
                elif execution_method == "l2_flash":
                    self.l2_flash_trades += 1
                    self.l2_flash_successful_trades += 1
                    self.l2_flash_total_profit += combined_result["profit"]
                    
                    # Update network-specific performance
                    network = opportunity.get("network", "")
                    if network in self.l2_network_performance:
                        self.l2_network_performance[network]["trades"] += 1
                        self.l2_network_performance[network]["successful_trades"] += 1
                        self.l2_network_performance[network]["total_profit"] += combined_result["profit"]
                    
                    # Update provider-specific performance
                    provider = opportunity.get("flash_loan_provider", "")
                    if provider in self.flash_provider_performance:
                        self.flash_provider_performance[provider]["trades"] += 1
                        self.flash_provider_performance[provider]["successful_trades"] += 1
                        self.flash_provider_performance[provider]["total_profit"] += combined_result["profit"]
                
                return combined_result
            else:
                # MEV protection failed
                self.mev_protection_failures += 1
                
                # If MEV protection failed, try executing without it
                logger.warning(f"MEV protection failed: {mev_result.get('error', 'unknown error')}. Falling back to unprotected execution.")
                unprotected_result = super().execute_trade(opportunity)
                unprotected_result["mev_protected"] = False
                unprotected_result["mev_protection_failure"] = True
                unprotected_result["mev_error"] = mev_result.get("error", "unknown error")
                
                return unprotected_result
                
        except Exception as e:
            # Handle any exceptions during MEV-protected execution
            logger.error(f"Error during MEV-protected execution: {str(e)}")
            self.mev_protection_failures += 1
            
            # Fallback to unprotected execution
            try:
                unprotected_result = super().execute_trade(opportunity)
                unprotected_result["mev_protected"] = False
                unprotected_result["mev_protection_failure"] = True
                unprotected_result["mev_error"] = str(e)
                
                return unprotected_result
            except Exception as fallback_error:
                # Both protected and unprotected execution failed
                logger.error(f"Fallback execution also failed: {str(fallback_error)}")
                
                return {
                    "success": False,
                    "mev_protected": False,
                    "error": f"Both MEV-protected and fallback execution failed: {str(e)} / {str(fallback_error)}",
                    "execution_method": opportunity.get("execution_method", "base"),
                    "timestamp": time.time()
                }
    
    def save_metrics(self) -> None:
        """Save current performance metrics to a file, including MEV protection metrics."""
        # Save combined metrics
        super().save_metrics()
        
        # Save MEV protection metrics
        mev_metrics = self.get_mev_metrics()
        
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.mev_config['metrics_dir']}/mev_protected_metrics_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(mev_metrics, f, indent=2)
            logger.info(f"MEV protection metrics saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save MEV protection metrics: {e}")
        
        # Also save metrics from the MEV protection integrator
        self.mev_protection_integrator.save_metrics()
    
    def get_mev_metrics(self) -> Dict[str, Any]:
        """
        Get current MEV protection metrics.
        
        Returns:
            Dictionary with MEV protection metrics
        """
        # Get metrics from the combined strategy
        combined_metrics = self.get_combined_metrics()
        
        # Get metrics from the MEV protection integrator
        integrator_metrics = self.mev_protection_integrator.get_protection_metrics()
        
        # Calculate MEV-specific metrics
        total_trades = self.mev_protected_trades + self.mev_unprotected_trades
        protected_percentage = 0.0 if total_trades == 0 else (self.mev_protected_trades / total_trades) * 100
        success_rate = 0.0 if self.mev_protected_trades == 0 else ((self.mev_protected_trades - self.mev_protection_failures) / self.mev_protected_trades) * 100
        
        # Combine all metrics
        mev_metrics = {
            "timestamp": datetime.datetime.now().isoformat(),
            "mev_protected_trades": self.mev_protected_trades,
            "mev_unprotected_trades": self.mev_unprotected_trades,
            "total_trades": total_trades,
            "protected_percentage": protected_percentage,
            "mev_protection_failures": self.mev_protection_failures,
            "mev_protection_success_rate": success_rate,
            "estimated_profit_saved": self.mev_profit_saved,
            "protection_level_stats": self.mev_protection_level_stats,
            "combined_strategy_metrics": combined_metrics,
            "mev_protection_integrator_metrics": integrator_metrics
        }
        
        return mev_metrics


def main():
    """Main function to demonstrate the MEV-protected combined strategy."""
    parser = argparse.ArgumentParser(description="ArbitrageX MEV-Protected Combined Strategy")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--simulate", action="store_true", help="Run a simulation")
    parser.add_argument("--trades", type=int, default=10, help="Number of trades to simulate")
    parser.add_argument("--l2-only", action="store_true", help="Only use Layer 2 networks")
    parser.add_argument("--flash-only", action="store_true", help="Only use Flash Loans")
    parser.add_argument("--combined-only", action="store_true", help="Only use combined L2 + Flash Loan execution")
    parser.add_argument("--mev-protection", type=str, default="enhanced", choices=["none", "basic", "enhanced", "maximum"], help="MEV protection level")
    args = parser.parse_args()
    
    # Initialize strategy
    strategy = OptimizedStrategyMEVProtected(args.config)
    
    # Apply command-line flags for combined strategy
    if args.l2_only:
        strategy.combined_config["enable_flash_loans"] = False
        strategy.combined_config["l2_flash_combined"] = False
    elif args.flash_only:
        strategy.combined_config["enable_l2"] = False
        strategy.combined_config["l2_flash_combined"] = False
    elif args.combined_only:
        strategy.combined_config["prefer_l2"] = False
        strategy.combined_config["prefer_flash_loans"] = False
    
    # Apply MEV protection level
    strategy.mev_config["default_protection_level"] = args.mev_protection
    
    if args.simulate:
        logger.info(f"Running MEV-protected simulation with {args.trades} trades at protection level {args.mev_protection}")
        
        # Simulate trades
        for i in range(args.trades):
            # Generate a random opportunity
            opportunity = {
                "token_pair": random.choice(["WETH-USDC", "WETH-DAI", "WBTC-USDC", "LINK-USDC"]),
                "dex": random.choice(["uniswap", "sushiswap", "curve", "balancer"]),
                "expected_profit": random.uniform(20, 100),
                "expected_profit_pct": random.uniform(0.01, 0.05),
                "gas_price": random.uniform(10, 25),
                "estimated_gas": random.uniform(150000, 250000),
                "position_size": random.uniform(0.5, 2.0),
                "max_slippage": random.uniform(0.003, 0.015)
            }
            
            # Evaluate opportunity
            should_execute, enhanced = strategy.evaluate_opportunity(opportunity)
            
            # Execute trade if approved
            if should_execute:
                result = strategy.execute_trade(enhanced)
                execution_method = enhanced.get("execution_method", "base")
                mev_protected = result.get("mev_protected", False)
                protection_status = "protected" if mev_protected else "unprotected"
                
                profit = result.get("profit", 0.0)
                logger.info(f"Trade {i+1}: {execution_method} ({protection_status}), {result['success']}, ${profit:.2f}")
            else:
                logger.info(f"Trade {i+1}: Rejected")
        
        # Save final metrics
        strategy.save_metrics()
        
        # Print summary
        metrics = strategy.get_metrics()
        mev_metrics = strategy.get_mev_metrics()
        combined_metrics = strategy.get_combined_metrics()
        
        print("\nSimulation Summary:")
        print(f"Total Trades: {metrics['total_trades']}")
        print(f"Successful Trades: {metrics['successful_trades']}")
        print(f"Success Rate: {metrics['success_rate']:.2%}")
        print(f"Total Profit: ${metrics['total_profit_usd']:.2f}")
        print(f"Average Profit per Trade: ${metrics['average_profit_per_trade']:.2f}")
        
        print("\nMEV Protection Summary:")
        print(f"Protected Trades: {mev_metrics['mev_protected_trades']} ({mev_metrics['protected_percentage']:.1f}%)")
        print(f"Unprotected Trades: {mev_metrics['mev_unprotected_trades']}")
        print(f"Protection Failures: {mev_metrics['mev_protection_failures']}")
        print(f"Estimated Profit Saved from MEV: ${mev_metrics['estimated_profit_saved']:.2f}")
        
        print("\nExecution Breakdown:")
        execution_breakdown = combined_metrics["execution_breakdown"]
        total = metrics['total_trades']
        print(f"Base Strategy: {execution_breakdown['base_trades']} trades ({(execution_breakdown['base_trades']/total):.2%})")
        print(f"Layer 2: {execution_breakdown['l2_trades']} trades ({(execution_breakdown['l2_trades']/total):.2%})")
        print(f"Flash Loan: {execution_breakdown['flash_trades']} trades ({(execution_breakdown['flash_trades']/total):.2%})")
        print(f"L2 + Flash Loan: {execution_breakdown['l2_flash_trades']} trades ({(execution_breakdown['l2_flash_trades']/total):.2%})")
        
        print("\nProtection Level Distribution:")
        for level, count in mev_metrics["protection_level_stats"].items():
            if count > 0:
                percentage = (count / total) * 100
                print(f"  {level.capitalize()}: {count} trades ({percentage:.1f}%)")
    else:
        logger.info("MEV-protected combined strategy initialized. Use --simulate to run a simulation.")


if __name__ == "__main__":
    main() 