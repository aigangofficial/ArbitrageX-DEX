"""
Trade Analyzer Module for ArbitrageX

This module is responsible for analyzing real-time trade data, identifying patterns,
and providing insights for optimizing arbitrage strategies. It processes transaction
data from multiple DEXes and networks to identify profitable opportunities.
"""

import numpy as np
import pandas as pd
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any
from pathlib import Path
import matplotlib.pyplot as plt
from collections import deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trade_analyzer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TradeAnalyzer")

class TradeAnalyzer:
    """
    Analyzes real-time trade data to identify patterns and optimize arbitrage strategies.
    """
    
    def __init__(self, config_path: str = "backend/ai/config/trade_analyzer_config.json"):
        """
        Initialize the trade analyzer.
        
        Args:
            config_path: Path to the configuration file
        """
        logger.info("Initializing Trade Analyzer")
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize data structures
        self.recent_trades = deque(maxlen=self.config.get("max_recent_trades", 1000))
        self.trade_history = {}
        self.token_metrics = {}
        self.network_metrics = {}
        self.dex_metrics = {}
        self.time_patterns = {}
        
        # Load historical data if available
        self._load_historical_data()
        
        logger.info("Trade Analyzer initialized successfully")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file."""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {config_path}")
                return config
            else:
                logger.warning(f"Config file not found at {config_path}, using default values")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration values."""
        return {
            "max_recent_trades": 1000,
            "min_profit_threshold": 0.001,  # Minimum profit to consider (in ETH)
            "time_window_analysis": 24,  # Hours to analyze for time patterns
            "token_pair_limit": 50,  # Maximum number of token pairs to track
            "data_storage_path": "backend/ai/data/trade_history",
            "networks": ["ethereum", "arbitrum", "polygon", "optimism"],
            "dexes": ["uniswap", "sushiswap", "curve", "balancer", "1inch"],
            "analysis_interval": 3600,  # Seconds between full analysis runs
            "visualization_enabled": True
        }

    def _load_historical_data(self):
        """Load historical trade data if available."""
        data_path = Path(self.config.get("data_storage_path", "backend/ai/data/trade_history"))
        data_path.mkdir(exist_ok=True, parents=True)
        
        history_file = data_path / "trade_history.json"
        
        try:
            if history_file.exists():
                with open(history_file, 'r') as f:
                    data = json.load(f)
                
                # Load trade history
                self.trade_history = data.get("trade_history", {})
                
                # Load metrics
                self.token_metrics = data.get("token_metrics", {})
                self.network_metrics = data.get("network_metrics", {})
                self.dex_metrics = data.get("dex_metrics", {})
                self.time_patterns = data.get("time_patterns", {})
                
                # Load recent trades
                recent_trades = data.get("recent_trades", [])
                self.recent_trades = deque(recent_trades, maxlen=self.config.get("max_recent_trades", 1000))
                
                logger.info(f"Loaded historical data with {len(self.trade_history)} trade records")
            else:
                logger.info("No historical data found, starting with empty dataset")
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
    
    def _save_historical_data(self):
        """Save historical trade data to disk."""
        data_path = Path(self.config.get("data_storage_path", "backend/ai/data/trade_history"))
        data_path.mkdir(exist_ok=True, parents=True)
        
        history_file = data_path / "trade_history.json"
        
        try:
            # Prepare data for serialization
            data = {
                "trade_history": self.trade_history,
                "token_metrics": self.token_metrics,
                "network_metrics": self.network_metrics,
                "dex_metrics": self.dex_metrics,
                "time_patterns": self.time_patterns,
                "recent_trades": list(self.recent_trades),
                "last_update": datetime.now().isoformat()
            }
            
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved historical data with {len(self.trade_history)} trade records")
        except Exception as e:
            logger.error(f"Error saving historical data: {e}")
    
    def analyze_trade(self, trade_data: Dict) -> Dict:
        """
        Analyze a trade and update metrics.
        
        Args:
            trade_data: Dictionary containing trade data
            
        Returns:
            Dictionary with analysis results
        """
        # Validate required fields
        required_fields = ["timestamp", "network", "token_pair", "buy_dex", "sell_dex", 
                          "amount", "gas_price", "gas_used", "profit", "success"]
        
        for field in required_fields:
            if field not in trade_data:
                logger.warning(f"Missing required field in trade data: {field}")
                return {"error": f"Missing required field: {field}"}
        
        # Add trade to recent trades
        trade_id = f"trade_{int(time.time())}_{len(self.recent_trades)}"
        trade_data["trade_id"] = trade_id
        
        # Add datetime for easier analysis
        if "timestamp" in trade_data:
            trade_time = datetime.fromtimestamp(trade_data["timestamp"])
            trade_data["hour"] = trade_time.hour
            trade_data["day_of_week"] = trade_time.weekday()
            trade_data["date"] = trade_time.strftime("%Y-%m-%d")
        
        # Add to recent trades
        self.recent_trades.append(trade_data)
        
        # Add to trade history
        self.trade_history[trade_id] = trade_data
        
        # Update metrics
        self._update_metrics(trade_data)
        
        # Save data periodically (every 10 trades)
        if len(self.recent_trades) % 10 == 0:
            self._save_historical_data()
        
        # Return analysis results
        return self._get_trade_analysis(trade_data)
    
    def _update_metrics(self, trade_data: Dict):
        """
        Update metrics based on new trade data.
        
        Args:
            trade_data: Dictionary containing trade data
        """
        # Extract key data
        network = trade_data.get("network", "unknown")
        token_pair = trade_data.get("token_pair", "unknown")
        buy_dex = trade_data.get("buy_dex", "unknown")
        sell_dex = trade_data.get("sell_dex", "unknown")
        hour = trade_data.get("hour", 0)
        day_of_week = trade_data.get("day_of_week", 0)
        success = trade_data.get("success", False)
        profit = trade_data.get("profit", 0)
        gas_cost = trade_data.get("gas_used", 0) * trade_data.get("gas_price", 0) / 1e9  # Convert to ETH
        
        # Update network metrics
        if network not in self.network_metrics:
            self.network_metrics[network] = {
                "total_trades": 0,
                "successful_trades": 0,
                "total_profit": 0,
                "total_gas_cost": 0,
                "avg_profit": 0,
                "success_rate": 0
            }
        
        self.network_metrics[network]["total_trades"] += 1
        if success:
            self.network_metrics[network]["successful_trades"] += 1
            self.network_metrics[network]["total_profit"] += profit
        
        self.network_metrics[network]["total_gas_cost"] += gas_cost
        
        # Update success rate and average profit
        if self.network_metrics[network]["successful_trades"] > 0:
            self.network_metrics[network]["avg_profit"] = (
                self.network_metrics[network]["total_profit"] / 
                self.network_metrics[network]["successful_trades"]
            )
        
        self.network_metrics[network]["success_rate"] = (
            self.network_metrics[network]["successful_trades"] / 
            self.network_metrics[network]["total_trades"]
        )
        
        # Update token pair metrics
        if token_pair not in self.token_metrics:
            self.token_metrics[token_pair] = {
                "total_trades": 0,
                "successful_trades": 0,
                "total_profit": 0,
                "avg_profit": 0,
                "success_rate": 0,
                "best_buy_dex": None,
                "best_sell_dex": None,
                "dex_profits": {}
            }
        
        self.token_metrics[token_pair]["total_trades"] += 1
        if success:
            self.token_metrics[token_pair]["successful_trades"] += 1
            self.token_metrics[token_pair]["total_profit"] += profit
            
            # Track DEX performance for this token pair
            dex_key = f"{buy_dex}_{sell_dex}"
            if dex_key not in self.token_metrics[token_pair]["dex_profits"]:
                self.token_metrics[token_pair]["dex_profits"][dex_key] = {
                    "total_profit": 0,
                    "count": 0
                }
            
            self.token_metrics[token_pair]["dex_profits"][dex_key]["total_profit"] += profit
            self.token_metrics[token_pair]["dex_profits"][dex_key]["count"] += 1
        
        # Update success rate and average profit
        if self.token_metrics[token_pair]["successful_trades"] > 0:
            self.token_metrics[token_pair]["avg_profit"] = (
                self.token_metrics[token_pair]["total_profit"] / 
                self.token_metrics[token_pair]["successful_trades"]
            )
        
        self.token_metrics[token_pair]["success_rate"] = (
            self.token_metrics[token_pair]["successful_trades"] / 
            self.token_metrics[token_pair]["total_trades"]
        )
        
        # Update best DEX combination
        if self.token_metrics[token_pair]["dex_profits"]:
            best_dex_combo = max(
                self.token_metrics[token_pair]["dex_profits"].items(),
                key=lambda x: x[1]["total_profit"] / max(x[1]["count"], 1)
            )[0]
            
            buy_dex, sell_dex = best_dex_combo.split("_")
            self.token_metrics[token_pair]["best_buy_dex"] = buy_dex
            self.token_metrics[token_pair]["best_sell_dex"] = sell_dex
        
        # Update DEX metrics
        for dex in [buy_dex, sell_dex]:
            if dex not in self.dex_metrics:
                self.dex_metrics[dex] = {
                    "total_trades": 0,
                    "successful_trades": 0,
                    "total_profit": 0,
                    "avg_profit": 0,
                    "success_rate": 0
                }
            
            self.dex_metrics[dex]["total_trades"] += 1
            if success:
                self.dex_metrics[dex]["successful_trades"] += 1
                self.dex_metrics[dex]["total_profit"] += profit / 2  # Split profit between buy and sell DEX
            
            # Update success rate and average profit
            if self.dex_metrics[dex]["successful_trades"] > 0:
                self.dex_metrics[dex]["avg_profit"] = (
                    self.dex_metrics[dex]["total_profit"] / 
                    self.dex_metrics[dex]["successful_trades"]
                )
            
            self.dex_metrics[dex]["success_rate"] = (
                self.dex_metrics[dex]["successful_trades"] / 
                self.dex_metrics[dex]["total_trades"]
            )
        
        # Update time patterns
        hour_key = f"hour_{hour}"
        if hour_key not in self.time_patterns:
            self.time_patterns[hour_key] = {
                "total_trades": 0,
                "successful_trades": 0,
                "total_profit": 0,
                "avg_profit": 0,
                "success_rate": 0
            }
        
        self.time_patterns[hour_key]["total_trades"] += 1
        if success:
            self.time_patterns[hour_key]["successful_trades"] += 1
            self.time_patterns[hour_key]["total_profit"] += profit
        
        # Update success rate and average profit
        if self.time_patterns[hour_key]["successful_trades"] > 0:
            self.time_patterns[hour_key]["avg_profit"] = (
                self.time_patterns[hour_key]["total_profit"] / 
                self.time_patterns[hour_key]["successful_trades"]
            )
        
        self.time_patterns[hour_key]["success_rate"] = (
            self.time_patterns[hour_key]["successful_trades"] / 
            self.time_patterns[hour_key]["total_trades"]
        )
        
        # Update day of week patterns
        day_key = f"day_{day_of_week}"
        if day_key not in self.time_patterns:
            self.time_patterns[day_key] = {
                "total_trades": 0,
                "successful_trades": 0,
                "total_profit": 0,
                "avg_profit": 0,
                "success_rate": 0
            }
        
        self.time_patterns[day_key]["total_trades"] += 1
        if success:
            self.time_patterns[day_key]["successful_trades"] += 1
            self.time_patterns[day_key]["total_profit"] += profit
        
        # Update success rate and average profit
        if self.time_patterns[day_key]["successful_trades"] > 0:
            self.time_patterns[day_key]["avg_profit"] = (
                self.time_patterns[day_key]["total_profit"] / 
                self.time_patterns[day_key]["successful_trades"]
            )
        
        self.time_patterns[day_key]["success_rate"] = (
            self.time_patterns[day_key]["successful_trades"] / 
            self.time_patterns[day_key]["total_trades"]
        )

    def _get_trade_analysis(self, trade_data: Dict) -> Dict:
        """
        Get analysis results for a specific trade.
        
        Args:
            trade_data: Dictionary containing trade data
            
        Returns:
            Dictionary with analysis results
        """
        network = trade_data.get("network", "unknown")
        token_pair = trade_data.get("token_pair", "unknown")
        buy_dex = trade_data.get("buy_dex", "unknown")
        sell_dex = trade_data.get("sell_dex", "unknown")
        profit = trade_data.get("profit", 0)
        success = trade_data.get("success", False)
        
        # Get network performance
        network_performance = self.network_metrics.get(network, {})
        
        # Get token pair performance
        token_performance = self.token_metrics.get(token_pair, {})
        
        # Get time-based performance
        hour = trade_data.get("hour", 0)
        hour_key = f"hour_{hour}"
        hour_performance = self.time_patterns.get(hour_key, {})
        
        # Get DEX performance
        buy_dex_performance = self.dex_metrics.get(buy_dex, {})
        sell_dex_performance = self.dex_metrics.get(sell_dex, {})
        
        # Calculate relative performance
        relative_profit = 0
        if token_performance.get("avg_profit", 0) > 0:
            relative_profit = profit / token_performance["avg_profit"]
        
        # Generate analysis
        analysis = {
            "trade_id": trade_data.get("trade_id", "unknown"),
            "success": success,
            "profit": profit,
            "network": {
                "name": network,
                "avg_profit": network_performance.get("avg_profit", 0),
                "success_rate": network_performance.get("success_rate", 0)
            },
            "token_pair": {
                "name": token_pair,
                "avg_profit": token_performance.get("avg_profit", 0),
                "success_rate": token_performance.get("success_rate", 0),
                "best_buy_dex": token_performance.get("best_buy_dex", None),
                "best_sell_dex": token_performance.get("best_sell_dex", None)
            },
            "time": {
                "hour": hour,
                "avg_profit_at_hour": hour_performance.get("avg_profit", 0),
                "success_rate_at_hour": hour_performance.get("success_rate", 0)
            },
            "dexes": {
                "buy_dex": {
                    "name": buy_dex,
                    "avg_profit": buy_dex_performance.get("avg_profit", 0),
                    "success_rate": buy_dex_performance.get("success_rate", 0)
                },
                "sell_dex": {
                    "name": sell_dex,
                    "avg_profit": sell_dex_performance.get("avg_profit", 0),
                    "success_rate": sell_dex_performance.get("success_rate", 0)
                }
            },
            "relative_performance": {
                "vs_token_avg": relative_profit,
                "vs_network_avg": network_performance.get("avg_profit", 0) > 0 and profit / network_performance["avg_profit"] or 0
            },
            "recommendations": self._generate_recommendations(trade_data)
        }
        
        return analysis
    
    def _generate_recommendations(self, trade_data: Dict) -> List[str]:
        """
        Generate recommendations based on trade data.
        
        Args:
            trade_data: Dictionary containing trade data
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        network = trade_data.get("network", "unknown")
        token_pair = trade_data.get("token_pair", "unknown")
        buy_dex = trade_data.get("buy_dex", "unknown")
        sell_dex = trade_data.get("sell_dex", "unknown")
        profit = trade_data.get("profit", 0)
        success = trade_data.get("success", False)
        hour = trade_data.get("hour", 0)
        
        # Check if there's a better DEX combination for this token pair
        token_performance = self.token_metrics.get(token_pair, {})
        best_buy_dex = token_performance.get("best_buy_dex", None)
        best_sell_dex = token_performance.get("best_sell_dex", None)
        
        if best_buy_dex and best_sell_dex and (best_buy_dex != buy_dex or best_sell_dex != sell_dex):
            recommendations.append(
                f"Consider using {best_buy_dex} for buying and {best_sell_dex} for selling {token_pair}"
            )
        
        # Check if there's a better time for this token pair
        best_hour = None
        best_hour_profit = 0
        
        for i in range(24):
            hour_key = f"hour_{i}"
            if hour_key in self.time_patterns:
                hour_data = self.time_patterns[hour_key]
                hour_profit = hour_data.get("avg_profit", 0) * hour_data.get("success_rate", 0)
                
                if hour_profit > best_hour_profit:
                    best_hour_profit = hour_profit
                    best_hour = i
        
        if best_hour is not None and best_hour != hour and best_hour_profit > 0:
            recommendations.append(
                f"Consider trading {token_pair} at hour {best_hour} UTC for potentially better profits"
            )
        
        # Check if there's a better network for this token pair
        best_network = None
        best_network_profit = 0
        
        for net, data in self.network_metrics.items():
            net_profit = data.get("avg_profit", 0) * data.get("success_rate", 0)
            
            if net_profit > best_network_profit:
                best_network_profit = net_profit
                best_network = net
        
        if best_network and best_network != network and best_network_profit > 0:
            recommendations.append(
                f"Consider trading on {best_network} network for potentially better profits"
            )
        
        # Add general recommendations
        if not success:
            recommendations.append(
                "This trade was unsuccessful. Consider increasing slippage tolerance or gas price."
            )
        elif profit < self.config.get("min_profit_threshold", 0.001):
            recommendations.append(
                "This trade had low profitability. Consider setting a higher minimum profit threshold."
            )
        
        return recommendations
    
    def get_best_trading_opportunities(self) -> List[Dict]:
        """
        Get the best trading opportunities based on historical data.
        
        Returns:
            List of dictionaries containing trading opportunities
        """
        opportunities = []
        
        # Find the best token pairs
        sorted_tokens = sorted(
            self.token_metrics.items(),
            key=lambda x: x[1].get("avg_profit", 0) * x[1].get("success_rate", 0),
            reverse=True
        )
        
        # Get the top token pairs
        top_tokens = sorted_tokens[:min(10, len(sorted_tokens))]
        
        for token_pair, data in top_tokens:
            # Skip if not enough data
            if data.get("total_trades", 0) < 5:
                continue
            
            # Find the best DEX combination
            best_buy_dex = data.get("best_buy_dex", None)
            best_sell_dex = data.get("best_sell_dex", None)
            
            # Find the best time
            best_hour = None
            best_hour_profit = 0
            
            for i in range(24):
                hour_key = f"hour_{i}"
                if hour_key in self.time_patterns:
                    hour_data = self.time_patterns[hour_key]
                    hour_profit = hour_data.get("avg_profit", 0) * hour_data.get("success_rate", 0)
                    
                    if hour_profit > best_hour_profit:
                        best_hour_profit = hour_profit
                        best_hour = i
            
            # Find the best network
            best_network = None
            best_network_profit = 0
            
            for net, net_data in self.network_metrics.items():
                net_profit = net_data.get("avg_profit", 0) * net_data.get("success_rate", 0)
                
                if net_profit > best_network_profit:
                    best_network_profit = net_profit
                    best_network = net
            
            # Create opportunity
            opportunity = {
                "token_pair": token_pair,
                "avg_profit": data.get("avg_profit", 0),
                "success_rate": data.get("success_rate", 0),
                "expected_profit": data.get("avg_profit", 0) * data.get("success_rate", 0),
                "best_buy_dex": best_buy_dex,
                "best_sell_dex": best_sell_dex,
                "best_hour": best_hour,
                "best_network": best_network,
                "total_trades": data.get("total_trades", 0),
                "confidence_score": min(1.0, data.get("total_trades", 0) / 20)  # Scale confidence based on number of trades
            }
            
            opportunities.append(opportunity)
        
        return opportunities
    
    def get_time_based_patterns(self) -> Dict:
        """
        Get time-based trading patterns.
        
        Returns:
            Dictionary containing time-based patterns
        """
        # Extract hour patterns
        hour_patterns = {}
        for i in range(24):
            hour_key = f"hour_{i}"
            if hour_key in self.time_patterns:
                hour_data = self.time_patterns[hour_key]
                hour_patterns[i] = {
                    "avg_profit": hour_data.get("avg_profit", 0),
                    "success_rate": hour_data.get("success_rate", 0),
                    "total_trades": hour_data.get("total_trades", 0)
                }
        
        # Extract day of week patterns
        day_patterns = {}
        for i in range(7):
            day_key = f"day_{i}"
            if day_key in self.time_patterns:
                day_data = self.time_patterns[day_key]
                day_patterns[i] = {
                    "avg_profit": day_data.get("avg_profit", 0),
                    "success_rate": day_data.get("success_rate", 0),
                    "total_trades": day_data.get("total_trades", 0)
                }
        
        # Find best hours
        best_hours = sorted(
            hour_patterns.items(),
            key=lambda x: x[1]["avg_profit"] * x[1]["success_rate"],
            reverse=True
        )
        
        # Find best days
        best_days = sorted(
            day_patterns.items(),
            key=lambda x: x[1]["avg_profit"] * x[1]["success_rate"],
            reverse=True
        )
        
        return {
            "hour_patterns": hour_patterns,
            "day_patterns": day_patterns,
            "best_hours": [hour for hour, _ in best_hours[:5]],
            "best_days": [day for day, _ in best_days],
            "worst_hours": [hour for hour, _ in best_hours[-5:]],
            "worst_days": [day for day, _ in best_days[-3:]]
        }

    def visualize_time_patterns(self, save_path: Optional[str] = None):
        """
        Visualize time-based trading patterns.
        
        Args:
            save_path: Path to save the visualization, if None, display only
        """
        if not self.config.get("visualization_enabled", True):
            logger.warning("Visualization is disabled in config")
            return
        
        # Extract hour patterns
        hours = []
        profits = []
        success_rates = []
        
        for i in range(24):
            hour_key = f"hour_{i}"
            if hour_key in self.time_patterns:
                hour_data = self.time_patterns[hour_key]
                hours.append(i)
                profits.append(hour_data.get("avg_profit", 0))
                success_rates.append(hour_data.get("success_rate", 0))
        
        if not hours:
            logger.warning("No time pattern data available for visualization")
            return
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        fig.suptitle("Time-Based Trading Patterns", fontsize=16)
        
        # Plot average profit by hour
        ax1.bar(hours, profits, color='blue', alpha=0.7)
        ax1.set_title("Average Profit by Hour of Day (UTC)")
        ax1.set_xlabel("Hour")
        ax1.set_ylabel("Average Profit (ETH)")
        ax1.set_xticks(hours)
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # Plot success rate by hour
        ax2.bar(hours, success_rates, color='green', alpha=0.7)
        ax2.set_title("Success Rate by Hour of Day (UTC)")
        ax2.set_xlabel("Hour")
        ax2.set_ylabel("Success Rate")
        ax2.set_xticks(hours)
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Saved time pattern visualization to {save_path}")
        else:
            plt.show()
    
    def visualize_network_comparison(self, save_path: Optional[str] = None):
        """
        Visualize network performance comparison.
        
        Args:
            save_path: Path to save the visualization, if None, display only
        """
        if not self.config.get("visualization_enabled", True):
            logger.warning("Visualization is disabled in config")
            return
        
        if not self.network_metrics:
            logger.warning("No network data available for visualization")
            return
        
        # Extract network data
        networks = list(self.network_metrics.keys())
        profits = [self.network_metrics[net].get("avg_profit", 0) for net in networks]
        success_rates = [self.network_metrics[net].get("success_rate", 0) for net in networks]
        total_profits = [self.network_metrics[net].get("total_profit", 0) for net in networks]
        
        # Create figure with subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15))
        fig.suptitle("Network Performance Comparison", fontsize=16)
        
        # Plot average profit by network
        ax1.bar(networks, profits, color='blue', alpha=0.7)
        ax1.set_title("Average Profit by Network")
        ax1.set_xlabel("Network")
        ax1.set_ylabel("Average Profit (ETH)")
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # Plot success rate by network
        ax2.bar(networks, success_rates, color='green', alpha=0.7)
        ax2.set_title("Success Rate by Network")
        ax2.set_xlabel("Network")
        ax2.set_ylabel("Success Rate")
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        # Plot total profit by network
        ax3.bar(networks, total_profits, color='purple', alpha=0.7)
        ax3.set_title("Total Profit by Network")
        ax3.set_xlabel("Network")
        ax3.set_ylabel("Total Profit (ETH)")
        ax3.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Saved network comparison visualization to {save_path}")
        else:
            plt.show()
    
    def visualize_token_pair_performance(self, top_n: int = 10, save_path: Optional[str] = None):
        """
        Visualize token pair performance.
        
        Args:
            top_n: Number of top token pairs to visualize
            save_path: Path to save the visualization, if None, display only
        """
        if not self.config.get("visualization_enabled", True):
            logger.warning("Visualization is disabled in config")
            return
        
        if not self.token_metrics:
            logger.warning("No token pair data available for visualization")
            return
        
        # Sort token pairs by expected profit (avg_profit * success_rate)
        sorted_tokens = sorted(
            self.token_metrics.items(),
            key=lambda x: x[1].get("avg_profit", 0) * x[1].get("success_rate", 0),
            reverse=True
        )
        
        # Get top N token pairs
        top_tokens = sorted_tokens[:min(top_n, len(sorted_tokens))]
        
        # Extract token pair data
        token_pairs = [pair for pair, _ in top_tokens]
        profits = [data.get("avg_profit", 0) for _, data in top_tokens]
        success_rates = [data.get("success_rate", 0) for _, data in top_tokens]
        expected_profits = [p * s for p, s in zip(profits, success_rates)]
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        fig.suptitle(f"Top {len(token_pairs)} Token Pair Performance", fontsize=16)
        
        # Plot average profit by token pair
        ax1.barh(token_pairs, profits, color='blue', alpha=0.7)
        ax1.set_title("Average Profit by Token Pair")
        ax1.set_xlabel("Average Profit (ETH)")
        ax1.set_ylabel("Token Pair")
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # Plot expected profit by token pair
        ax2.barh(token_pairs, expected_profits, color='green', alpha=0.7)
        ax2.set_title("Expected Profit by Token Pair (Avg Profit * Success Rate)")
        ax2.set_xlabel("Expected Profit (ETH)")
        ax2.set_ylabel("Token Pair")
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Saved token pair performance visualization to {save_path}")
        else:
            plt.show()

# Example usage
if __name__ == "__main__":
    # Initialize the trade analyzer
    analyzer = TradeAnalyzer()
    
    # Example trade data
    example_trade = {
        "timestamp": int(time.time()),
        "network": "ethereum",
        "token_pair": "ETH-USDC",
        "buy_dex": "uniswap",
        "sell_dex": "sushiswap",
        "amount": 1.0,
        "gas_price": 50000000000,  # 50 Gwei
        "gas_used": 150000,
        "profit": 0.05,
        "success": True
    }
    
    # Analyze the trade
    analysis = analyzer.analyze_trade(example_trade)
    print(f"Trade Analysis: {json.dumps(analysis, indent=2)}")
    
    # Add more example trades
    for i in range(10):
        # Generate random trade data
        trade = {
            "timestamp": int(time.time()) - i * 3600,  # 1 hour apart
            "network": np.random.choice(["ethereum", "arbitrum", "polygon", "optimism"]),
            "token_pair": np.random.choice(["ETH-USDC", "ETH-USDT", "WBTC-ETH", "LINK-ETH"]),
            "buy_dex": np.random.choice(["uniswap", "sushiswap", "curve"]),
            "sell_dex": np.random.choice(["uniswap", "sushiswap", "curve"]),
            "amount": np.random.uniform(0.1, 5.0),
            "gas_price": np.random.randint(20, 100) * 1000000000,  # 20-100 Gwei
            "gas_used": np.random.randint(100000, 300000),
            "profit": np.random.uniform(-0.01, 0.1),
            "success": np.random.random() > 0.2  # 80% success rate
        }
        
        analyzer.analyze_trade(trade)
    
    # Get best trading opportunities
    opportunities = analyzer.get_best_trading_opportunities()
    print(f"\nBest Trading Opportunities: {json.dumps(opportunities, indent=2)}")
    
    # Get time-based patterns
    time_patterns = analyzer.get_time_based_patterns()
    print(f"\nTime-Based Patterns: {json.dumps(time_patterns, indent=2)}")
    
    # Visualize time patterns
    analyzer.visualize_time_patterns("backend/ai/data/time_patterns.png")
    
    # Visualize network comparison
    analyzer.visualize_network_comparison("backend/ai/data/network_comparison.png")
    
    # Visualize token pair performance
    analyzer.visualize_token_pair_performance(5, "backend/ai/data/token_performance.png") 