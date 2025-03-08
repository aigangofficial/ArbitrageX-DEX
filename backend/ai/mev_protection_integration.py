#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArbitrageX MEV Protection Integration Module

This module integrates MEV protection into the optimized trading strategies,
allowing trades to be protected from front-running and sandwich attacks.
"""

import os
import json
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum

# Import MEV protection components
from mev_protection import (
    MEVProtectionManager, MEVRiskLevel, ProtectionMethod, FlashbotsConnector
)

# Import MEV Protection Insights for tracking
try:
    from mev_protection_insights import MEVProtectionInsights
    HAS_INSIGHTS = True
except ImportError:
    HAS_INSIGHTS = False
    logging.warning("MEV Protection Insights module not found. Insights tracking disabled.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mev_protection_integration.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("MEVProtectionIntegration")


class ProtectionLevel(Enum):
    """Enum for different protection levels."""
    NONE = "none"               # No protection
    BASIC = "basic"             # Basic protection for most trades
    ENHANCED = "enhanced"       # Enhanced protection for high-value trades
    MAXIMUM = "maximum"         # Maximum protection for critical trades


class MEVProtectionIntegrator:
    """
    Integrates MEV protection into the trading strategies.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the MEV protection integrator.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path
        self.mev_manager = MEVProtectionManager(config_path)
        self.config = self._load_config()
        self.metrics = {
            "total_protected": 0,
            "protection_levels": {
                "basic": 0,
                "enhanced": 0,
                "maximum": 0,
                "none": 0
            },
            "total_unprotected": 0,
            "savings": 0.0
        }
        
        # Initialize insights tracking if available
        self.insights_tracker = None
        if HAS_INSIGHTS:
            try:
                self.insights_tracker = MEVProtectionInsights(config_path)
                logging.info("MEV Protection Insights tracking initialized")
            except Exception as e:
                logging.error(f"Error initializing MEV Protection Insights: {e}")
        
        # Initialize protection metrics
        self.protected_trades = 0
        self.unprotected_trades = 0
        self.protection_failures = 0
        self.profit_saved = 0.0
        self.protection_level_stats = {level.value: 0 for level in ProtectionLevel}
        self.network_stats = {}
        self.execution_method_stats = {
            "base": {"protected": 0, "unprotected": 0},
            "l2": {"protected": 0, "unprotected": 0},
            "flash_loan": {"protected": 0, "unprotected": 0},
            "l2_flash": {"protected": 0, "unprotected": 0}
        }
        
        logger.info("MEV Protection Integrator initialized")
    
    def _load_config(self):
        """Load configuration from file or use default values."""
        config = {
            "enabled": True,
            "default_protection_level": ProtectionLevel.BASIC.value,
            "l1_protection": {
                "enabled": True,
                "risk_threshold_for_protection": MEVRiskLevel.LOW.value,
                "skip_trades_with_extreme_risk": True
            },
            "l2_protection": {
                "enabled": True,
                "networks_requiring_protection": ["arbitrum", "optimism"],
                "networks_without_protection": ["polygon", "base"]
            },
            "flash_loan_protection": {
                "enabled": True,
                "force_private_transactions": True,
                "min_size_for_protection": 2.0  # ETH or equivalent
            },
            "risk_thresholds": {
                "position_size": {
                    "medium": 5.0,   # ETH or equivalent
                    "high": 10.0     # ETH or equivalent
                },
                "expected_profit": {
                    "medium": 50.0,  # USD
                    "high": 100.0    # USD
                },
                "slippage": {
                    "medium": 0.005, # 0.5%
                    "high": 0.01     # 1.0%
                }
            },
            "protection_level_mapping": {
                "none": {
                    "l1": False,
                    "l2": False,
                    "flash_loan": False
                },
                "basic": {
                    "l1": True,
                    "l2": False,
                    "flash_loan": True
                },
                "enhanced": {
                    "l1": True,
                    "l2": True,
                    "flash_loan": True
                },
                "maximum": {
                    "l1": True,
                    "l2": True,
                    "flash_loan": True,
                    "force_bundle": True
                }
            },
            "metrics_dir": "backend/ai/metrics/mev_protection_integration"
        }
        
        # Update config from file if provided
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    if "mev_protection_integration" in loaded_config:
                        config.update(loaded_config["mev_protection_integration"])
                logger.info(f"Loaded MEV protection integration configuration from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load MEV protection integration configuration: {e}")
        
        # Create metrics directory
        os.makedirs(config["metrics_dir"], exist_ok=True)
        
        return config
    
    def determine_protection_level(self, opportunity: Dict[str, Any]) -> ProtectionLevel:
        """
        Determine the appropriate protection level for a trading opportunity.
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            Protection level enum value
        """
        # Extract key metrics
        token_pair = opportunity.get("token_pair", "")
        dex = opportunity.get("dex", "")
        execution_method = opportunity.get("execution_method", "base")
        expected_profit = float(opportunity.get("expected_profit", 0.0))
        position_size = float(opportunity.get("position_size", 0.0))
        is_flash_loan = execution_method == "flash_loan" or execution_method == "l2_flash"
        is_l2 = execution_method == "l2" or execution_method == "l2_flash"
        network = opportunity.get("network", "")
        
        # Default to configured default level
        default_level = ProtectionLevel(self.config["default_protection_level"])
        
        # Start with no protection for Layer 2 trades on certain networks
        if is_l2 and network.lower() in self.config["l2_protection"]["networks_without_protection"]:
            return ProtectionLevel.NONE
        
        # Enhanced protection for flash loans above threshold
        if is_flash_loan and position_size >= self.config["flash_loan_protection"]["min_size_for_protection"]:
            return ProtectionLevel.ENHANCED
        
        # Maximum protection for high-value trades
        if position_size >= self.config["risk_thresholds"]["position_size"]["high"]:
            return ProtectionLevel.MAXIMUM
        
        if expected_profit >= self.config["risk_thresholds"]["expected_profit"]["high"]:
            return ProtectionLevel.MAXIMUM
        
        # Enhanced protection for medium-value trades
        if position_size >= self.config["risk_thresholds"]["position_size"]["medium"]:
            return ProtectionLevel.ENHANCED
        
        if expected_profit >= self.config["risk_thresholds"]["expected_profit"]["medium"]:
            return ProtectionLevel.ENHANCED
        
        # Default level for everything else
        return default_level
    
    def should_apply_protection(self, opportunity: Dict[str, Any], protection_level: ProtectionLevel) -> bool:
        """
        Determine if MEV protection should be applied to this opportunity.
        
        Args:
            opportunity: Dictionary containing opportunity details
            protection_level: Determined protection level
            
        Returns:
            Boolean indicating whether to apply protection
        """
        if not self.config["enabled"]:
            return False
        
        if protection_level == ProtectionLevel.NONE:
            return False
        
        # Get protection settings for this level
        level_settings = self.config["protection_level_mapping"][protection_level.value]
        
        # Extract trade details
        execution_method = opportunity.get("execution_method", "base")
        is_flash_loan = execution_method == "flash_loan" or execution_method == "l2_flash"
        is_l2 = execution_method == "l2" or execution_method == "l2_flash"
        
        # Apply protection based on execution method
        if is_l2 and not level_settings.get("l2", False):
            return False
        
        if not is_l2 and not level_settings.get("l1", False):
            return False
        
        if is_flash_loan and not level_settings.get("flash_loan", False):
            return False
        
        return True
    
    def enhance_opportunity_with_protection(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance a trading opportunity with MEV protection if applicable.
        
        Args:
            opportunity: The trading opportunity to enhance.
            
        Returns:
            The enhanced opportunity with MEV protection details.
        """
        # Determine if protection should be applied
        protection_level = self.determine_protection_level(opportunity)
        should_protect = self.should_apply_protection(opportunity, protection_level)
        
        enhanced_opportunity = opportunity.copy()
        
        if should_protect:
            # Assess MEV risk
            risk_level, risk_details = self.mev_manager.assess_mev_risk(opportunity)
            
            # Select protection method
            protection_method = self.mev_manager.select_protection_method(opportunity, risk_level)
            
            # Estimate potential savings
            estimated_saving = 0.0
            if self.insights_tracker:
                estimated_saving = self.insights_tracker.estimate_savings_for_transaction(opportunity, risk_level)
            
            # Apply protection
            enhanced_opportunity["mev_protection"] = {
                "enabled": True,
                "protection_level": protection_level.value,
                "risk_level": risk_level.value,
                "risk_details": risk_details,
                "protection_method": protection_method.value,
                "estimated_saving": estimated_saving
            }
            
            # Update metrics
            self.metrics["total_protected"] += 1
            self.metrics["protection_levels"][protection_level.value.lower()] += 1
            self.metrics["savings"] += estimated_saving
            
            logging.info(f"MEV protection applied to opportunity. Level: {protection_level.value}, "
                         f"Method: {protection_method.value}, Risk: {risk_level.value}")
        else:
            # No protection applied
            enhanced_opportunity["mev_protection"] = {
                "enabled": False,
                "protection_level": "none",
                "risk_level": "unknown",
                "protection_method": "none",
                "estimated_saving": 0.0
            }
            
            # Update metrics
            self.metrics["total_unprotected"] += 1
            self.metrics["protection_levels"]["none"] += 1
            
            logging.info("No MEV protection applied to opportunity")
        
        return enhanced_opportunity
    
    def execute_protected_transaction(self, opportunity: Dict[str, Any], private_key: str) -> Dict[str, Any]:
        """
        Execute a transaction with MEV protection.
        
        Args:
            opportunity: The trading opportunity to execute.
            private_key: The private key to sign the transaction.
            
        Returns:
            The result of the protected transaction.
        """
        # Check if protection is enabled for this opportunity
        mev_protection = opportunity.get("mev_protection", {})
        is_protected = mev_protection.get("enabled", False)
        
        result = {}
        
        if is_protected:
            # Get protection details
            protection_level_str = mev_protection.get("protection_level", "basic")
            risk_level_str = mev_protection.get("risk_level", "low")
            protection_method_str = mev_protection.get("protection_method", "flashbots")
            estimated_saving = mev_protection.get("estimated_saving", 0.0)
            
            # Convert string values to enum types
            protection_level = ProtectionLevel(protection_level_str)
            risk_level = MEVRiskLevel(risk_level_str)
            protection_method = ProtectionMethod(protection_method_str)
            
            # Execute the protected transaction
            tx_data = opportunity.get("transaction", {})
            result = self.mev_manager.protect_transaction(tx_data, private_key)
            
            # Track insights if available
            if self.insights_tracker and result.get("success", False):
                try:
                    self.insights_tracker.track_protected_transaction(
                        opportunity,
                        protection_level,
                        risk_level,
                        protection_method,
                        estimated_saving
                    )
                except Exception as e:
                    logging.error(f"Error tracking protected transaction: {e}")
            
            logging.info(f"Protected transaction executed. Result: {result.get('success', False)}")
        else:
            # Execute normal transaction
            logging.info("Executing unprotected transaction")
            # In a real implementation, we would execute the transaction here
            result = {
                "success": True,
                "hash": "0x0000000000000000000000000000000000000000000000000000000000000000",
                "unprotected": True
            }
            
            # Track unprotected transaction for metrics
            if self.insights_tracker:
                try:
                    self.insights_tracker.track_unprotected_transaction(opportunity)
                except Exception as e:
                    logging.error(f"Error tracking unprotected transaction: {e}")
        
        return result
    
    def get_protection_metrics(self) -> Dict[str, Any]:
        """
        Get current MEV protection metrics.
        
        Returns:
            Dictionary with protection metrics
        """
        total_trades = self.protected_trades + self.unprotected_trades
        protected_percentage = 0.0 if total_trades == 0 else (self.protected_trades / total_trades) * 100
        success_rate = 0.0 if self.protected_trades == 0 else ((self.protected_trades - self.protection_failures) / self.protected_trades) * 100
        
        # Get detailed MEV protection stats
        mev_protection_metrics = self.mev_manager.get_protection_metrics()
        
        return {
            "total_trades": total_trades,
            "protected_trades": self.protected_trades,
            "unprotected_trades": self.unprotected_trades,
            "protection_failures": self.protection_failures,
            "protected_percentage": protected_percentage,
            "protection_success_rate": success_rate,
            "profit_saved_usd": self.profit_saved,
            "protection_level_stats": self.protection_level_stats,
            "network_stats": self.network_stats,
            "execution_method_stats": self.execution_method_stats,
            "mev_protection_details": mev_protection_metrics,
            "metrics": self.metrics
        }
    
    def save_metrics(self) -> None:
        """Save current protection metrics to a file."""
        metrics = self.get_protection_metrics()
        
        # Generate filename with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{self.config['metrics_dir']}/mev_protection_metrics_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(metrics, f, indent=2)
            logger.info(f"MEV protection metrics saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save MEV protection metrics: {e}")


def main():
    """Demonstrate the MEV protection integration."""
    # Initialize MEV protection integrator
    protection_integrator = MEVProtectionIntegrator()
    
    # Example trade opportunities
    opportunities = [
        {
            "token_pair": "WETH-USDC",
            "dex": "uniswap",
            "expected_profit": 75.0,
            "position_size": 8.0,
            "execution_method": "base",
            "max_slippage": 0.01
        },
        {
            "token_pair": "WBTC-USDC",
            "dex": "sushiswap",
            "expected_profit": 120.0,
            "position_size": 12.0,
            "execution_method": "flash_loan",
            "flash_loan_amount": 36.0,
            "max_slippage": 0.005
        },
        {
            "token_pair": "LINK-USDC",
            "dex": "curve",
            "expected_profit": 35.0,
            "position_size": 3.0,
            "execution_method": "l2",
            "network": "arbitrum",
            "max_slippage": 0.008
        },
        {
            "token_pair": "WETH-DAI",
            "dex": "balancer",
            "expected_profit": 150.0,
            "position_size": 10.0,
            "execution_method": "l2_flash",
            "network": "optimism",
            "flash_loan_amount": 30.0,
            "max_slippage": 0.01
        }
    ]
    
    # Example private key (NEVER USE THIS IN PRODUCTION)
    example_private_key = "0x0000000000000000000000000000000000000000000000000000000000000001"
    
    # Process each opportunity
    for i, opportunity in enumerate(opportunities):
        print(f"\nOpportunity {i+1}: {opportunity['token_pair']} on {opportunity['dex']} via {opportunity['execution_method']}")
        
        # Enhance with protection
        enhanced = protection_integrator.enhance_opportunity_with_protection(opportunity)
        
        # Print protection details
        protection_details = enhanced.get("mev_protection", {})
        print(f"Protection Level: {protection_details.get('protection_level', 'none')}")
        print(f"Protection Enabled: {protection_details.get('enabled', False)}")
        
        if protection_details.get("enabled", False):
            print(f"Risk Level: {protection_details.get('risk_level', 'unknown')}")
            print(f"Protection Method: {protection_details.get('protection_method', 'unknown')}")
        
        # Execute transaction
        result = protection_integrator.execute_protected_transaction(enhanced, example_private_key)
        
        # Print result
        print(f"Transaction {'succeeded' if result['success'] else 'failed'}")
        print(f"Protected: {result['protected']}")
        if result.get("hash"):
            print(f"TX Hash: {result['hash']}")
        if result.get("error"):
            print(f"Error: {result['error']}")
    
    # Get and print metrics
    metrics = protection_integrator.get_protection_metrics()
    print("\nMEV Protection Metrics:")
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Protected Trades: {metrics['protected_trades']} ({metrics['protected_percentage']:.1f}%)")
    print(f"Unprotected Trades: {metrics['unprotected_trades']}")
    print(f"Protection Failures: {metrics['protection_failures']}")
    print(f"Success Rate: {metrics['protection_success_rate']:.1f}%")
    print(f"Estimated Profit Saved: ${metrics['profit_saved_usd']:.2f}")
    
    # Save metrics
    protection_integrator.save_metrics()


if __name__ == "__main__":
    main() 