#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArbitrageX MEV Protection Insights Module

This module provides insights into MEV protection activities, including:
- Protection status tracking (ON/OFF)
- Protection level metrics (number of protected transactions)
- Estimated savings from MEV attacks
- Risk assessment for trades
"""

import os
import json
import time
import logging
import datetime
from typing import Dict, List, Tuple, Optional, Any, Union
from pathlib import Path

# Import MEV protection components
from mev_protection import MEVProtectionManager, MEVRiskLevel, ProtectionMethod
from mev_protection_integration import MEVProtectionIntegrator, ProtectionLevel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mev_protection_insights.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mev_protection_insights")

class MEVProtectionInsights:
    """
    Class to track and analyze MEV protection metrics and provide insights.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the MEV Protection Insights manager.
        
        Args:
            config_path: Path to the configuration file (optional).
        """
        self.config_path = config_path or os.path.join('config', 'mev_protection_insights.json')
        self.metrics_path = os.path.join('metrics', 'mev_protection_metrics.json')
        self.insights_path = os.path.join('metrics', 'mev_protection_insights.json')
        
        # Ensure metrics directory exists
        Path(os.path.dirname(self.metrics_path)).mkdir(parents=True, exist_ok=True)
        
        # Load or initialize configuration
        self.config = self._load_config()
        
        # Initialize metrics storage
        self.metrics = self._load_metrics()
        
        # Initialize insights
        self.insights = self._load_insights()
        
        # Initialize MEV protection components for status checking
        self.mev_manager = MEVProtectionManager(config_path)
        self.mev_integrator = MEVProtectionIntegrator(config_path)
        
        logger.info("MEV Protection Insights initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                # Default configuration
                config = {
                    "metrics_update_interval": 60,  # seconds
                    "risk_assessment_threshold": {
                        "low": 0.05,
                        "medium": 0.1,
                        "high": 0.2,
                        "extreme": 0.4
                    },
                    "savings_calculation": {
                        "low_risk_factor": 0.01,
                        "medium_risk_factor": 0.05,
                        "high_risk_factor": 0.15,
                        "extreme_risk_factor": 0.3
                    }
                }
                # Save default config
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(config, f, indent=4)
                return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {
                "metrics_update_interval": 60,
                "risk_assessment_threshold": {
                    "low": 0.05,
                    "medium": 0.1,
                    "high": 0.2,
                    "extreme": 0.4
                },
                "savings_calculation": {
                    "low_risk_factor": 0.01,
                    "medium_risk_factor": 0.05,
                    "high_risk_factor": 0.15,
                    "extreme_risk_factor": 0.3
                }
            }
    
    def _load_metrics(self) -> Dict[str, Any]:
        """Load metrics from file or initialize empty metrics."""
        try:
            if os.path.exists(self.metrics_path):
                with open(self.metrics_path, 'r') as f:
                    return json.load(f)
            else:
                # Default metrics structure
                metrics = {
                    "protection_status": False,
                    "protected_transactions": {
                        "total": 0,
                        "basic": 0,
                        "enhanced": 0,
                        "maximum": 0
                    },
                    "risk_levels": {
                        "low": 0,
                        "medium": 0,
                        "high": 0,
                        "extreme": 0
                    },
                    "protection_methods": {
                        "flashbots": 0,
                        "eden_network": 0,
                        "bloxroute": 0,
                        "transaction_bundle": 0,
                        "backrun_only": 0
                    },
                    "estimated_savings": 0.0,
                    "last_updated": datetime.datetime.now().isoformat()
                }
                # Save initial metrics
                with open(self.metrics_path, 'w') as f:
                    json.dump(metrics, f, indent=4)
                return metrics
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")
            return {
                "protection_status": False,
                "protected_transactions": {
                    "total": 0,
                    "basic": 0,
                    "enhanced": 0,
                    "maximum": 0
                },
                "risk_levels": {
                    "low": 0,
                    "medium": 0,
                    "high": 0,
                    "extreme": 0
                },
                "protection_methods": {
                    "flashbots": 0,
                    "eden_network": 0,
                    "bloxroute": 0,
                    "transaction_bundle": 0,
                    "backrun_only": 0
                },
                "estimated_savings": 0.0,
                "last_updated": datetime.datetime.now().isoformat()
            }

    def _load_insights(self) -> Dict[str, Any]:
        """Load insights from file or initialize empty insights."""
        try:
            if os.path.exists(self.insights_path):
                with open(self.insights_path, 'r') as f:
                    return json.load(f)
            else:
                # Default insights structure
                insights = {
                    "historical_data": {
                        "daily": {},
                        "weekly": {},
                        "monthly": {}
                    },
                    "high_risk_trades": [],
                    "protected_vs_unprotected": {
                        "protected": 0,
                        "unprotected": 0
                    },
                    "savings_over_time": [],
                    "last_updated": datetime.datetime.now().isoformat()
                }
                # Save initial insights
                with open(self.insights_path, 'w') as f:
                    json.dump(insights, f, indent=4)
                return insights
        except Exception as e:
            logger.error(f"Error loading insights: {e}")
            return {
                "historical_data": {
                    "daily": {},
                    "weekly": {},
                    "monthly": {}
                },
                "high_risk_trades": [],
                "protected_vs_unprotected": {
                    "protected": 0,
                    "unprotected": 0
                },
                "savings_over_time": [],
                "last_updated": datetime.datetime.now().isoformat()
            }
    
    def get_protection_status(self) -> bool:
        """
        Check if MEV protection is currently enabled.
        
        Returns:
            bool: True if protection is enabled, False otherwise.
        """
        try:
            # Get the current status from the MEV manager's config
            mev_metrics = self.mev_manager.get_protection_metrics()
            protection_enabled = mev_metrics.get("protection_enabled", False)
            
            # Update the metrics
            self.metrics["protection_status"] = protection_enabled
            self._save_metrics()
            
            return protection_enabled
        except Exception as e:
            logger.error(f"Error getting protection status: {e}")
            return self.metrics["protection_status"]
    
    def set_protection_status(self, status: bool) -> bool:
        """
        Enable or disable MEV protection.
        
        Args:
            status: True to enable protection, False to disable.
            
        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        try:
            # Update the protection status in the configuration
            # This would typically involve updating the MEV manager's config
            
            # For now, we'll just update our metrics
            self.metrics["protection_status"] = status
            self._save_metrics()
            
            logger.info(f"MEV protection status set to: {status}")
            return True
        except Exception as e:
            logger.error(f"Error setting protection status: {e}")
            return False
    
    def track_protected_transaction(self, 
                                   transaction: Dict[str, Any], 
                                   protection_level: ProtectionLevel,
                                   risk_level: MEVRiskLevel,
                                   protection_method: ProtectionMethod,
                                   estimated_saving: float) -> None:
        """
        Track a protected transaction and update metrics.
        
        Args:
            transaction: Transaction details.
            protection_level: Level of protection applied.
            risk_level: Assessed MEV risk level.
            protection_method: Method used for protection.
            estimated_saving: Estimated savings from MEV attack.
        """
        try:
            # Update protected transactions count
            self.metrics["protected_transactions"]["total"] += 1
            level_key = protection_level.value.lower()
            if level_key in self.metrics["protected_transactions"]:
                self.metrics["protected_transactions"][level_key] += 1
            
            # Update risk levels count
            risk_key = risk_level.value.lower()
            if risk_key in self.metrics["risk_levels"]:
                self.metrics["risk_levels"][risk_key] += 1
            
            # Update protection methods count
            method_key = protection_method.value.lower()
            if method_key in self.metrics["protection_methods"]:
                self.metrics["protection_methods"][method_key] += 1
            
            # Update estimated savings
            self.metrics["estimated_savings"] += estimated_saving
            
            # Update last updated timestamp
            self.metrics["last_updated"] = datetime.datetime.now().isoformat()
            
            # Save metrics
            self._save_metrics()
            
            # Update insights
            self._update_insights_for_transaction(transaction, protection_level, risk_level, protection_method, estimated_saving)
            
            logger.info(f"Tracked protected transaction with risk level {risk_key}, protection level {level_key}, and estimated saving {estimated_saving}")
        except Exception as e:
            logger.error(f"Error tracking protected transaction: {e}")
    
    def track_unprotected_transaction(self, transaction: Dict[str, Any]) -> None:
        """
        Track an unprotected transaction for comparison metrics.
        
        Args:
            transaction: Transaction details.
        """
        try:
            # Update protected vs unprotected metrics
            self.insights["protected_vs_unprotected"]["unprotected"] += 1
            
            # Save insights
            self._save_insights()
            
            logger.info(f"Tracked unprotected transaction")
        except Exception as e:
            logger.error(f"Error tracking unprotected transaction: {e}")
    
    def _update_insights_for_transaction(self,
                                        transaction: Dict[str, Any],
                                        protection_level: ProtectionLevel,
                                        risk_level: MEVRiskLevel,
                                        protection_method: ProtectionMethod,
                                        estimated_saving: float) -> None:
        """
        Update insights based on a protected transaction.
        
        Args:
            transaction: Transaction details.
            protection_level: Level of protection applied.
            risk_level: Assessed MEV risk level.
            protection_method: Method used for protection.
            estimated_saving: Estimated savings from MEV attack.
        """
        # Get current date for historical data
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        week_str = f"{now.year}-W{now.isocalendar()[1]}"
        month_str = now.strftime("%Y-%m")
        
        # Update daily data
        if date_str not in self.insights["historical_data"]["daily"]:
            self.insights["historical_data"]["daily"][date_str] = {
                "protected_transactions": 0,
                "estimated_savings": 0.0,
                "protection_levels": {
                    "basic": 0, "enhanced": 0, "maximum": 0
                },
                "risk_levels": {
                    "low": 0, "medium": 0, "high": 0, "extreme": 0
                }
            }
        
        self.insights["historical_data"]["daily"][date_str]["protected_transactions"] += 1
        self.insights["historical_data"]["daily"][date_str]["estimated_savings"] += estimated_saving
        self.insights["historical_data"]["daily"][date_str]["protection_levels"][protection_level.value.lower()] += 1
        self.insights["historical_data"]["daily"][date_str]["risk_levels"][risk_level.value.lower()] += 1
        
        # Update weekly data
        if week_str not in self.insights["historical_data"]["weekly"]:
            self.insights["historical_data"]["weekly"][week_str] = {
                "protected_transactions": 0,
                "estimated_savings": 0.0,
                "protection_levels": {
                    "basic": 0, "enhanced": 0, "maximum": 0
                },
                "risk_levels": {
                    "low": 0, "medium": 0, "high": 0, "extreme": 0
                }
            }
        
        self.insights["historical_data"]["weekly"][week_str]["protected_transactions"] += 1
        self.insights["historical_data"]["weekly"][week_str]["estimated_savings"] += estimated_saving
        self.insights["historical_data"]["weekly"][week_str]["protection_levels"][protection_level.value.lower()] += 1
        self.insights["historical_data"]["weekly"][week_str]["risk_levels"][risk_level.value.lower()] += 1
        
        # Update monthly data
        if month_str not in self.insights["historical_data"]["monthly"]:
            self.insights["historical_data"]["monthly"][month_str] = {
                "protected_transactions": 0,
                "estimated_savings": 0.0,
                "protection_levels": {
                    "basic": 0, "enhanced": 0, "maximum": 0
                },
                "risk_levels": {
                    "low": 0, "medium": 0, "high": 0, "extreme": 0
                }
            }
        
        self.insights["historical_data"]["monthly"][month_str]["protected_transactions"] += 1
        self.insights["historical_data"]["monthly"][month_str]["estimated_savings"] += estimated_saving
        self.insights["historical_data"]["monthly"][month_str]["protection_levels"][protection_level.value.lower()] += 1
        self.insights["historical_data"]["monthly"][month_str]["risk_levels"][risk_level.value.lower()] += 1
        
        # Track high risk trades
        if risk_level in [MEVRiskLevel.HIGH, MEVRiskLevel.EXTREME]:
            # Keep only essential information
            high_risk_trade = {
                "timestamp": now.isoformat(),
                "risk_level": risk_level.value,
                "protection_level": protection_level.value,
                "protection_method": protection_method.value,
                "estimated_saving": estimated_saving,
                "trade_value": transaction.get("value", 0)
            }
            self.insights["high_risk_trades"].append(high_risk_trade)
            
            # Keep only the last 100 high risk trades
            if len(self.insights["high_risk_trades"]) > 100:
                self.insights["high_risk_trades"] = self.insights["high_risk_trades"][-100:]
        
        # Update protected vs unprotected count
        self.insights["protected_vs_unprotected"]["protected"] += 1
        
        # Update savings over time
        savings_entry = {
            "timestamp": now.isoformat(),
            "saving": estimated_saving,
            "risk_level": risk_level.value
        }
        self.insights["savings_over_time"].append(savings_entry)
        
        # Keep only the last 1000 savings entries
        if len(self.insights["savings_over_time"]) > 1000:
            self.insights["savings_over_time"] = self.insights["savings_over_time"][-1000:]
        
        # Update last updated timestamp
        self.insights["last_updated"] = now.isoformat()
        
        # Save insights
        self._save_insights()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current MEV protection metrics.
        
        Returns:
            Dict: Current metrics.
        """
        # Ensure we have fresh data
        self.get_protection_status()
        
        # Sync with MEV manager metrics
        try:
            mev_metrics = self.mev_manager.get_protection_metrics()
            integrator_metrics = self.mev_integrator.get_protection_metrics()
            
            # Update our metrics with the latest data from the MEV manager
            if mev_metrics and "protection_methods" in mev_metrics:
                for method, count in mev_metrics["protection_methods"].items():
                    if method in self.metrics["protection_methods"]:
                        self.metrics["protection_methods"][method] = count
            
            if integrator_metrics and "protection_levels" in integrator_metrics:
                for level, count in integrator_metrics["protection_levels"].items():
                    if level in self.metrics["protected_transactions"]:
                        self.metrics["protected_transactions"][level] = count
            
            if mev_metrics and "risk_levels" in mev_metrics:
                for level, count in mev_metrics["risk_levels"].items():
                    if level in self.metrics["risk_levels"]:
                        self.metrics["risk_levels"][level] = count
            
            # Update total protected transactions
            if integrator_metrics and "total_protected" in integrator_metrics:
                self.metrics["protected_transactions"]["total"] = integrator_metrics["total_protected"]
            else:
                # Calculate total from individual levels if not provided
                self.metrics["protected_transactions"]["total"] = sum(
                    count for level, count in self.metrics["protected_transactions"].items() if level != "total"
                )
            
            # Save updated metrics
            self._save_metrics()
        except Exception as e:
            logger.error(f"Error syncing with MEV manager metrics: {e}")
        
        return self.metrics
    
    def get_insights(self) -> Dict[str, Any]:
        """
        Get MEV protection insights.
        
        Returns:
            Dict: Current insights.
        """
        return self.insights
    
    def get_protection_summary(self) -> Dict[str, Any]:
        """
        Get a summary of MEV protection status and metrics.
        
        Returns:
            Dict: Protection summary.
        """
        # Get fresh metrics
        metrics = self.get_metrics()
        insights = self.get_insights()
        
        # Calculate additional summary metrics
        protected_total = metrics["protected_transactions"]["total"]
        unprotected_total = insights["protected_vs_unprotected"]["unprotected"]
        total_transactions = protected_total + unprotected_total
        
        protection_ratio = 0
        if total_transactions > 0:
            protection_ratio = protected_total / total_transactions
        
        # Get top risk level
        top_risk = max(metrics["risk_levels"].items(), key=lambda x: x[1]) if metrics["risk_levels"] else ("none", 0)
        
        # Get top protection method
        top_method = max(metrics["protection_methods"].items(), key=lambda x: x[1]) if metrics["protection_methods"] else ("none", 0)
        
        # Calculate daily savings (last 24 hours)
        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        yesterday_str = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        
        daily_savings = 0
        if today_str in insights["historical_data"]["daily"]:
            daily_savings += insights["historical_data"]["daily"][today_str]["estimated_savings"]
        if yesterday_str in insights["historical_data"]["daily"]:
            # Add partial amount from yesterday based on current time
            hours_from_yesterday = now.hour
            yesterday_contribution = insights["historical_data"]["daily"][yesterday_str]["estimated_savings"] * (hours_from_yesterday / 24)
            daily_savings += yesterday_contribution
        
        # Return summary
        return {
            "protection_status": metrics["protection_status"],
            "protected_transactions": protected_total,
            "protection_ratio": protection_ratio,
            "top_risk_level": top_risk[0],
            "top_protection_method": top_method[0],
            "estimated_total_savings": metrics["estimated_savings"],
            "estimated_daily_savings": daily_savings,
            "high_risk_trades_count": len(insights["high_risk_trades"]),
            "last_updated": metrics["last_updated"]
        }
    
    def estimate_savings_for_transaction(self, transaction: Dict[str, Any], risk_level: MEVRiskLevel) -> float:
        """
        Estimate potential savings from MEV protection for a transaction.
        
        Args:
            transaction: Transaction details.
            risk_level: Assessed MEV risk level.
            
        Returns:
            float: Estimated savings.
        """
        # Get transaction value
        value = transaction.get("value", 0)
        
        # Apply risk factor based on configuration
        risk_factor = 0
        if risk_level == MEVRiskLevel.LOW:
            risk_factor = self.config["savings_calculation"]["low_risk_factor"]
        elif risk_level == MEVRiskLevel.MEDIUM:
            risk_factor = self.config["savings_calculation"]["medium_risk_factor"]
        elif risk_level == MEVRiskLevel.HIGH:
            risk_factor = self.config["savings_calculation"]["high_risk_factor"]
        elif risk_level == MEVRiskLevel.EXTREME:
            risk_factor = self.config["savings_calculation"]["extreme_risk_factor"]
        
        # Calculate estimated savings
        estimated_saving = value * risk_factor
        
        return estimated_saving
    
    def _save_metrics(self) -> None:
        """Save metrics to file."""
        try:
            with open(self.metrics_path, 'w') as f:
                json.dump(self.metrics, f, indent=4)
            logger.debug("Metrics saved successfully")
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def _save_insights(self) -> None:
        """Save insights to file."""
        try:
            with open(self.insights_path, 'w') as f:
                json.dump(self.insights, f, indent=4)
            logger.debug("Insights saved successfully")
        except Exception as e:
            logger.error(f"Error saving insights: {e}")

# Simple test when run directly
if __name__ == "__main__":
    # Create insights manager
    insights_manager = MEVProtectionInsights()
    
    # Get metrics
    metrics = insights_manager.get_metrics()
    print(f"Current MEV Protection Metrics: {json.dumps(metrics, indent=2)}")
    
    # Get insights
    insights = insights_manager.get_insights()
    print(f"Current MEV Protection Insights: {json.dumps(insights, indent=2)}")
    
    # Get summary
    summary = insights_manager.get_protection_summary()
    print(f"MEV Protection Summary: {json.dumps(summary, indent=2)}") 