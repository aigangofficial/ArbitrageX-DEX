#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArbitrageX ML-Enhanced Combined Strategy

This module integrates the advanced ML models with the combined strategy
to create a fully optimized trading system with reinforcement learning,
price impact prediction, and volatility tracking.
"""

import os
import json
import time
import logging
import argparse
from typing import Dict, List, Tuple, Optional, Any

# Import the combined strategy
from optimized_strategy_combined import OptimizedStrategyCombined

# Import the advanced ML models
from advanced_ml_models import ModelManager, ModelType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ml_enhanced_strategy.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("MLEnhancedStrategy")


class MLEnhancedStrategy(OptimizedStrategyCombined):
    """
    ML-Enhanced Combined Strategy that integrates advanced ML models
    with the combined strategy for maximum profitability.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the ML-enhanced combined strategy.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        # Initialize the base combined strategy
        super().__init__(config_path)
        
        # Initialize the ML model manager
        self.model_manager = ModelManager(config_path)
        
        # ML-specific configuration
        self.ml_config = {
            "enabled": True,
            "apply_price_impact": True,
            "apply_volatility": True,
            "apply_reinforcement_learning": True,
            "metrics_dir": "backend/ai/metrics/ml_enhanced"
        }
        
        # Update config with ML settings if available
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    if "ml_config" in loaded_config:
                        self.ml_config.update(loaded_config["ml_config"])
                logger.info(f"Loaded ML configuration from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load ML configuration: {e}")
        
        # Create metrics directory
        os.makedirs(self.ml_config["metrics_dir"], exist_ok=True)
        
        # Track ML-specific metrics
        self.ml_enhanced_trades = 0
        self.ml_rejected_trades = 0
        self.ml_improvements = {
            "price_impact": 0.0,
            "volatility": 0.0,
            "reinforcement_learning": 0.0
        }
        
        logger.info("ML-Enhanced Combined Strategy initialized")
    
    def evaluate_opportunity(self, opportunity: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluate a trading opportunity with ML enhancements.
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            Tuple of (should_execute, enhanced_opportunity)
        """
        # First, apply ML enhancements to the opportunity
        if self.ml_config["enabled"]:
            try:
                # Apply ML models to enhance the opportunity
                ml_enhanced = self.model_manager.enhance_trade_opportunity(opportunity)
                
                # Track ML enhancements
                self.ml_enhanced_trades += 1
                
                # Track improvements
                if "position_size_adjustment" in ml_enhanced:
                    original = ml_enhanced["position_size_adjustment"]["original"]
                    adjusted = ml_enhanced["position_size_adjustment"]["adjusted"]
                    improvement = abs(adjusted - original)
                    self.ml_improvements["volatility"] += improvement
                
                if "slippage_adjustment" in ml_enhanced:
                    original = ml_enhanced["slippage_adjustment"]["original"]
                    adjusted = ml_enhanced["slippage_adjustment"]["adjusted"]
                    improvement = abs(adjusted - original)
                    self.ml_improvements["price_impact"] += improvement
                
                if "execution_recommendation" in ml_enhanced:
                    # Simple heuristic for RL improvement tracking
                    self.ml_improvements["reinforcement_learning"] += ml_enhanced.get("execution_confidence", 0.0) * 0.1
                
                # Use the ML-enhanced opportunity for further evaluation
                opportunity = ml_enhanced
                
                logger.info(f"Applied ML enhancements to opportunity for {opportunity.get('token_pair', 'unknown')}")
            except Exception as e:
                logger.error(f"Error applying ML enhancements: {str(e)}")
        
        # Then, evaluate using the combined strategy
        should_execute, enhanced = super().evaluate_opportunity(opportunity)
        
        # Track rejected trades
        if not should_execute:
            self.ml_rejected_trades += 1
        
        return should_execute, enhanced
    
    def execute_trade(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trade with ML-enhanced parameters.
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            Dictionary with trade results
        """
        # Execute the trade using the combined strategy
        result = super().execute_trade(opportunity)
        
        # Update ML models with the trade result
        if self.ml_config["enabled"] and self.ml_config["apply_reinforcement_learning"]:
            try:
                # Extract state and action from the opportunity
                state = {
                    "token_pair": opportunity.get("token_pair", ""),
                    "dex": opportunity.get("dex", ""),
                    "position_size": opportunity.get("position_size", 0.0),
                    "expected_profit": opportunity.get("expected_profit", 0.0),
                    "gas_price": opportunity.get("gas_price", 0.0),
                    "market_volatility": opportunity.get("market_volatility", "medium")
                }
                
                # Extract action from the opportunity
                action = opportunity.get("execution_recommendation", {
                    "execution_method": opportunity.get("execution_method", "base"),
                    "l2_network": opportunity.get("network", "arbitrum"),
                    "flash_loan_provider": opportunity.get("flash_loan_provider", "aave"),
                    "trade_size_multiplier": 1.0,
                    "slippage_tolerance_multiplier": 1.0
                })
                
                # Update the RL model with the trade result
                self.model_manager.observe_trade_result(state, action, result)
                
                logger.info(f"Updated ML models with trade result for {opportunity.get('token_pair', 'unknown')}")
            except Exception as e:
                logger.error(f"Error updating ML models: {str(e)}")
        
        return result
    
    def save_metrics(self) -> None:
        """Save current performance metrics to a file, including ML metrics."""
        # Save combined metrics
        super().save_metrics()
        
        # Save ML metrics
        ml_metrics = self.get_ml_metrics()
        
        # Generate filename with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{self.ml_config['metrics_dir']}/ml_enhanced_metrics_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(ml_metrics, f, indent=2)
            logger.info(f"ML metrics saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save ML metrics: {e}")
        
        # Also save metrics from the ML models
        try:
            model_metrics = self.model_manager.get_all_metrics()
            model_metrics_file = f"{self.ml_config['metrics_dir']}/ml_models_metrics_{timestamp}.json"
            with open(model_metrics_file, 'w') as f:
                json.dump(model_metrics, f, indent=2)
            logger.info(f"ML model metrics saved to {model_metrics_file}")
        except Exception as e:
            logger.error(f"Failed to save ML model metrics: {e}")
    
    def get_ml_metrics(self) -> Dict[str, Any]:
        """
        Get current ML metrics.
        
        Returns:
            Dictionary with ML metrics
        """
        # Get metrics from the combined strategy
        combined_metrics = self.get_combined_metrics()
        
        # Calculate ML-specific metrics
        total_trades = self.ml_enhanced_trades + self.ml_rejected_trades
        enhancement_rate = 0.0 if total_trades == 0 else (self.ml_enhanced_trades / total_trades) * 100
        
        # Combine all metrics
        ml_metrics = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "ml_enhanced_trades": self.ml_enhanced_trades,
            "ml_rejected_trades": self.ml_rejected_trades,
            "total_trades": total_trades,
            "enhancement_rate": enhancement_rate,
            "ml_improvements": self.ml_improvements,
            "combined_strategy_metrics": combined_metrics
        }
        
        return ml_metrics


def main():
    """Main function to demonstrate the ML-enhanced combined strategy."""
    parser = argparse.ArgumentParser(description="ArbitrageX ML-Enhanced Combined Strategy")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--simulate", action="store_true", help="Run a simulation")
    parser.add_argument("--trades", type=int, default=10, help="Number of trades to simulate")
    parser.add_argument("--l2-only", action="store_true", help="Only use Layer 2 networks")
    parser.add_argument("--flash-only", action="store_true", help="Only use Flash Loans")
    parser.add_argument("--combined-only", action="store_true", help="Only use combined L2 + Flash Loan execution")
    parser.add_argument("--ml-disabled", action="store_true", help="Disable ML enhancements")
    args = parser.parse_args()
    
    # Initialize strategy
    strategy = MLEnhancedStrategy(args.config)
    
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
    
    # Apply ML flag
    if args.ml_disabled:
        strategy.ml_config["enabled"] = False
    
    if args.simulate:
        logger.info(f"Running ML-enhanced simulation with {args.trades} trades")
        
        # Import random for simulation
        import random
        from datetime import datetime
        
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
                "max_slippage": random.uniform(0.003, 0.015),
                "timestamp": datetime.now().isoformat()
            }
            
            # Evaluate opportunity
            should_execute, enhanced = strategy.evaluate_opportunity(opportunity)
            
            # Execute trade if approved
            if should_execute:
                result = strategy.execute_trade(enhanced)
                execution_method = enhanced.get("execution_method", "base")
                ml_enhanced = "ML-enhanced" if strategy.ml_config["enabled"] else "standard"
                
                profit = result.get("profit", 0.0)
                logger.info(f"Trade {i+1}: {execution_method} ({ml_enhanced}), {result['success']}, ${profit:.2f}")
            else:
                logger.info(f"Trade {i+1}: Rejected")
        
        # Save final metrics
        strategy.save_metrics()
        
        # Print summary
        metrics = strategy.get_metrics()
        ml_metrics = strategy.get_ml_metrics()
        combined_metrics = strategy.get_combined_metrics()
        
        print("\nSimulation Summary:")
        print(f"Total Trades: {metrics['total_trades']}")
        print(f"Successful Trades: {metrics['successful_trades']}")
        print(f"Success Rate: {metrics['success_rate']:.2%}")
        print(f"Total Profit: ${metrics['total_profit_usd']:.2f}")
        print(f"Average Profit per Trade: ${metrics['average_profit_per_trade']:.2f}")
        
        if strategy.ml_config["enabled"]:
            print("\nML Enhancement Summary:")
            print(f"ML-Enhanced Trades: {ml_metrics['ml_enhanced_trades']}")
            print(f"ML-Rejected Trades: {ml_metrics['ml_rejected_trades']}")
            print(f"Enhancement Rate: {ml_metrics['enhancement_rate']:.1f}%")
            
            print("\nML Improvements:")
            for improvement_type, value in ml_metrics["ml_improvements"].items():
                print(f"  {improvement_type.replace('_', ' ').title()}: {value:.2f}")
        
        print("\nExecution Breakdown:")
        execution_breakdown = combined_metrics["execution_breakdown"]
        total = metrics['total_trades']
        if total > 0:
            print(f"Base Strategy: {execution_breakdown['base_trades']} trades ({(execution_breakdown['base_trades']/total):.2%})")
            print(f"Layer 2: {execution_breakdown['l2_trades']} trades ({(execution_breakdown['l2_trades']/total):.2%})")
            print(f"Flash Loan: {execution_breakdown['flash_trades']} trades ({(execution_breakdown['flash_trades']/total):.2%})")
            print(f"L2 + Flash Loan: {execution_breakdown['l2_flash_trades']} trades ({(execution_breakdown['l2_flash_trades']/total):.2%})")
    else:
        logger.info("ML-enhanced combined strategy initialized. Use --simulate to run a simulation.")


if __name__ == "__main__":
    main() 