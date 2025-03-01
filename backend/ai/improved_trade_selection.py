#!/usr/bin/env python3
"""
ArbitrageX Improved Trade Selection

This module enhances the trade selection process by prioritizing historically successful trades
rather than just high-confidence trades. It uses MongoDB-stored past trades to train the AI
on which pairs & conditions actually lead to profits.
"""

import os
import sys
import json
import logging
import datetime
import random
from typing import Dict, List, Any, Tuple, Optional
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ImprovedTradeSelection")

class ImprovedTradeSelection:
    """
    Enhanced trade selection model that prioritizes historically successful trades.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the improved trade selection model.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.historical_data = self._load_historical_data()
        self.network_success_rates = {}
        self.token_pair_success_rates = {}
        self.dex_combination_success_rates = {}
        self.profitable_thresholds = {}
        self.mongodb_client = None
        self.mongodb_db = None
        
        # Initialize MongoDB connection if enabled
        if self.config["mongodb_enabled"]:
            self._initialize_mongodb()
        
        # Process historical data to extract success patterns
        self._process_historical_data()
        
        logger.info("Improved trade selection model initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            "min_historical_trades": 5,
            "min_success_rate": 0.4,
            "min_expected_profit": 2.0,
            "confidence_weight": 0.3,
            "success_rate_weight": 0.4,
            "profit_weight": 0.3,  # Increased weight for profit
            "gas_cost_threshold": {
                "ethereum": 20.0,
                "arbitrum": 1.5,
                "polygon": 0.5,
                "optimism": 1.0,
                "bsc": 0.8
            },
            "network_preferences": {
                "arbitrum": 1.2,
                "polygon": 1.3,
                "ethereum": 0.8,
                "bsc": 0.9,
                "optimism": 1.0
            },
            "token_pair_preferences": {
                "WETH-USDC": 1.3,
                "WETH-DAI": 1.1,
                "WBTC-USDC": 1.0,
                "WMATIC-USDC": 1.2,
                "LINK-WETH": 0.9
            },
            "dex_preferences": {
                "uniswap_v3": 1.2,
                "sushiswap": 1.0,
                "curve": 1.1,
                "balancer": 0.9,
                "quickswap": 1.1
            },
            "batch_size_by_network": {
                "ethereum": 8,
                "arbitrum": 5,
                "polygon": 4,
                "optimism": 5,
                "bsc": 6
            },
            "gas_strategy_by_network": {
                "ethereum": "conservative",
                "arbitrum": "aggressive",
                "polygon": "aggressive",
                "optimism": "dynamic",
                "bsc": "dynamic"
            },
            "profit_scaling_factor": 0.05,  # New parameter for profit scaling
            "execution_speed_weight": 0.2,  # New parameter for execution speed
            "historical_data_path": "data/trade_history.json",
            "mongodb_enabled": False,
            "mongodb_uri": "mongodb://localhost:27017/",
            "mongodb_db": "arbitragex",
            "mongodb_collection": "trade_history",
            "dynamic_threshold_adjustment": True,  # New parameter for dynamic thresholds
            "profit_threshold_multiplier": 1.5,  # New parameter for profit threshold
            "high_profit_threshold_usd": 10.0,  # New parameter for high profit threshold
            "execution_time_threshold_ms": 200  # New parameter for execution time threshold
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    user_config = json.load(f)
                    # Merge user config with default config
                    for key, value in user_config.items():
                        if key in default_config and isinstance(default_config[key], dict) and isinstance(value, dict):
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading config from {config_path}: {e}")
        
        return default_config
    
    def _initialize_mongodb(self) -> None:
        """
        Initialize MongoDB connection.
        """
        if not self.config["mongodb_enabled"]:
            logger.info("MongoDB is disabled in configuration")
            return
        
        try:
            # Connect to MongoDB
            self.mongodb_client = MongoClient(self.config["mongodb_uri"], serverSelectionTimeoutMS=5000)
            # Check if connection is successful
            self.mongodb_client.admin.command('ping')
            self.mongodb_db = self.mongodb_client[self.config["mongodb_db"]]
            logger.info(f"Connected to MongoDB: {self.config['mongodb_uri']}")
        except ConnectionFailure as e:
            logger.error(f"MongoDB connection failed: {e}")
            self.mongodb_client = None
            self.mongodb_db = None
        except Exception as e:
            logger.error(f"Error initializing MongoDB: {e}")
            self.mongodb_client = None
            self.mongodb_db = None
    
    def _load_historical_data(self) -> List[Dict[str, Any]]:
        """
        Load historical trade data from file or MongoDB.
        
        Returns:
            List of historical trades
        """
        # Try to load from MongoDB first if enabled
        if self.config["mongodb_enabled"] and self.mongodb_db:
            try:
                collection = self.mongodb_db[self.config["mongodb_collection"]]
                trades = list(collection.find({}, {'_id': 0}))
                if trades:
                    logger.info(f"Loaded {len(trades)} historical trades from MongoDB")
                    return trades
            except Exception as e:
                logger.error(f"Error loading historical data from MongoDB: {e}")
        
        # Fall back to file-based data
        try:
            data_path = self.config["historical_data_path"]
            if os.path.exists(data_path):
                with open(data_path, "r") as f:
                    trades = json.load(f)
                logger.info(f"Loaded {len(trades)} historical trades from {data_path}")
                return trades
            else:
                logger.warning(f"Historical data file not found: {data_path}")
                return self._generate_sample_data()
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            return self._generate_sample_data()
    
    def _generate_sample_data(self) -> List[Dict[str, Any]]:
        """
        Generate sample historical data for testing.
        
        Returns:
            List of sample trades
        """
        logger.warning("Generating sample historical data")
        
        networks = ["ethereum", "arbitrum", "polygon", "optimism", "bsc"]
        token_pairs = ["WETH-USDC", "WETH-DAI", "WBTC-USDC", "WMATIC-USDC", "LINK-WETH"]
        dexes = ["uniswap_v3", "sushiswap", "curve", "balancer", "quickswap"]
        
        sample_data = []
        
        # Generate 100 sample trades
        for i in range(100):
            network = random.choice(networks)
            token_pair = random.choice(token_pairs)
            buy_dex = random.choice(dexes)
            sell_dex = random.choice([d for d in dexes if d != buy_dex])
            
            # Generate random timestamp within the last 30 days
            timestamp = datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 30))
            
            # Generate random trade data
            amount = random.uniform(0.1, 10.0)
            gas_price = random.uniform(10, 100)
            gas_used = random.uniform(100000, 500000)
            
            # Determine success and profit based on network and token pair
            # More profitable for Arbitrum and Polygon
            if network in ["arbitrum", "polygon"]:
                success = random.random() < 0.7  # 70% success rate
                profit = random.uniform(5, 30) if success else random.uniform(-20, 0)
            else:
                success = random.random() < 0.5  # 50% success rate
                profit = random.uniform(2, 15) if success else random.uniform(-15, 0)
            
            # Create trade record
            trade = {
                "timestamp": timestamp.isoformat(),
                "network": network,
                "token_pair": token_pair,
                "buy_dex": buy_dex,
                "sell_dex": sell_dex,
                "amount": amount,
                "gas_price": gas_price,
                "gas_used": gas_used,
                "profit": profit,
                "success": success,
                "execution_time_ms": random.uniform(50, 500)
            }
            
            sample_data.append(trade)
        
        return sample_data
    
    def _process_historical_data(self) -> None:
        """
        Process historical data to extract success patterns.
        """
        if not self.historical_data:
            logger.warning("No historical data available for processing")
            return
        
        logger.info(f"Processing {len(self.historical_data)} historical trades")
        
        # Initialize counters
        network_stats = {}
        token_pair_stats = {}
        dex_combo_stats = {}
        
        # Process each trade
        for trade in self.historical_data:
            network = trade.get("network")
            token_pair = trade.get("token_pair")
            buy_dex = trade.get("buy_dex")
            sell_dex = trade.get("sell_dex")
            profit = trade.get("profit", 0)
            success = trade.get("success", False)
            execution_time = trade.get("execution_time_ms", 200)
            
            if not all([network, token_pair, buy_dex, sell_dex]):
                continue
            
            # Create DEX combination key
            dex_combo = f"{buy_dex}-{sell_dex}"
            
            # Update network statistics
            if network not in network_stats:
                network_stats[network] = {"success_count": 0, "total_count": 0, "total_profit": 0, "avg_execution_time": 0}
            
            network_stats[network]["total_count"] += 1
            if success:
                network_stats[network]["success_count"] += 1
            network_stats[network]["total_profit"] += profit
            network_stats[network]["avg_execution_time"] = (
                (network_stats[network]["avg_execution_time"] * (network_stats[network]["total_count"] - 1) + execution_time) / 
                network_stats[network]["total_count"]
            )
            
            # Update token pair statistics
            if token_pair not in token_pair_stats:
                token_pair_stats[token_pair] = {"success_count": 0, "total_count": 0, "total_profit": 0, "avg_execution_time": 0}
            
            token_pair_stats[token_pair]["total_count"] += 1
            if success:
                token_pair_stats[token_pair]["success_count"] += 1
            token_pair_stats[token_pair]["total_profit"] += profit
            token_pair_stats[token_pair]["avg_execution_time"] = (
                (token_pair_stats[token_pair]["avg_execution_time"] * (token_pair_stats[token_pair]["total_count"] - 1) + execution_time) / 
                token_pair_stats[token_pair]["total_count"]
            )
            
            # Update DEX combination statistics
            if dex_combo not in dex_combo_stats:
                dex_combo_stats[dex_combo] = {"success_count": 0, "total_count": 0, "total_profit": 0, "avg_execution_time": 0}
            
            dex_combo_stats[dex_combo]["total_count"] += 1
            if success:
                dex_combo_stats[dex_combo]["success_count"] += 1
            dex_combo_stats[dex_combo]["total_profit"] += profit
            dex_combo_stats[dex_combo]["avg_execution_time"] = (
                (dex_combo_stats[dex_combo]["avg_execution_time"] * (dex_combo_stats[dex_combo]["total_count"] - 1) + execution_time) / 
                dex_combo_stats[dex_combo]["total_count"]
            )
        
        # Calculate success rates and average profits
        for network, stats in network_stats.items():
            success_rate = stats["success_count"] / stats["total_count"] if stats["total_count"] > 0 else 0
            avg_profit = stats["total_profit"] / stats["total_count"] if stats["total_count"] > 0 else 0
            
            self.network_success_rates[network] = {
                "success_rate": success_rate,
                "avg_profit": avg_profit,
                "total_trades": stats["total_count"],
                "avg_execution_time": stats["avg_execution_time"]
            }
            
            # Set profitable threshold based on historical data
            self.profitable_thresholds[network] = max(2.0, avg_profit * self.config["profit_threshold_multiplier"])
        
        for token_pair, stats in token_pair_stats.items():
            success_rate = stats["success_count"] / stats["total_count"] if stats["total_count"] > 0 else 0
            avg_profit = stats["total_profit"] / stats["total_count"] if stats["total_count"] > 0 else 0
            
            self.token_pair_success_rates[token_pair] = {
                "success_rate": success_rate,
                "avg_profit": avg_profit,
                "total_trades": stats["total_count"],
                "avg_execution_time": stats["avg_execution_time"]
            }
        
        for dex_combo, stats in dex_combo_stats.items():
            success_rate = stats["success_count"] / stats["total_count"] if stats["total_count"] > 0 else 0
            avg_profit = stats["total_profit"] / stats["total_count"] if stats["total_count"] > 0 else 0
            
            self.dex_combination_success_rates[dex_combo] = {
                "success_rate": success_rate,
                "avg_profit": avg_profit,
                "total_trades": stats["total_count"],
                "avg_execution_time": stats["avg_execution_time"]
            }
        
        logger.info(f"Processed historical data: {len(network_stats)} networks, {len(token_pair_stats)} token pairs, {len(dex_combo_stats)} DEX combinations")
    
    def evaluate_trade(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a trade prediction using historical success patterns.
        
        Args:
            prediction: Trade prediction to evaluate
            
        Returns:
            Enhanced prediction with historical success metrics
        """
        network = prediction.get("network")
        token_pair = prediction.get("token_pair")
        buy_dex = prediction.get("buy_exchange") or prediction.get("buy_dex")
        sell_dex = prediction.get("sell_exchange") or prediction.get("sell_dex")
        confidence_score = prediction.get("confidence_score", 0.5)
        expected_profit = prediction.get("net_profit_usd", 0)
        gas_cost = prediction.get("gas_cost_usd", 0)
        execution_time = prediction.get("execution_time_ms", 200)
        
        # Skip evaluation if missing critical data
        if not all([network, token_pair, buy_dex, sell_dex]):
            logger.warning("Missing critical data in prediction, skipping evaluation")
            prediction["historical_success_rate"] = 0
            prediction["historical_avg_profit"] = 0
            prediction["enhanced_confidence"] = confidence_score
            prediction["should_execute"] = False
            prediction["evaluation_reason"] = "Missing critical data"
            return prediction
        
        # Create DEX combination key
        dex_combo = f"{buy_dex}-{sell_dex}"
        
        # Get historical success rates
        network_stats = self.network_success_rates.get(network, {"success_rate": 0, "avg_profit": 0, "total_trades": 0, "avg_execution_time": 200})
        token_pair_stats = self.token_pair_success_rates.get(token_pair, {"success_rate": 0, "avg_profit": 0, "total_trades": 0, "avg_execution_time": 200})
        dex_combo_stats = self.dex_combination_success_rates.get(dex_combo, {"success_rate": 0, "avg_profit": 0, "total_trades": 0, "avg_execution_time": 200})
        
        # Calculate weighted historical success rate
        historical_success_rate = (
            network_stats["success_rate"] * 0.3 +
            token_pair_stats["success_rate"] * 0.4 +
            dex_combo_stats["success_rate"] * 0.3
        )
        
        # Calculate weighted historical average profit
        historical_avg_profit = (
            network_stats["avg_profit"] * 0.3 +
            token_pair_stats["avg_profit"] * 0.4 +
            dex_combo_stats["avg_profit"] * 0.3
        )
        
        # Calculate profit score (higher for more profitable trades)
        profit_score = min(1.0, expected_profit / self.config["high_profit_threshold_usd"])
        
        # Calculate execution speed score (higher for faster execution)
        avg_execution_time = (
            network_stats["avg_execution_time"] * 0.3 +
            token_pair_stats["avg_execution_time"] * 0.4 +
            dex_combo_stats["avg_execution_time"] * 0.3
        )
        execution_speed_score = min(1.0, self.config["execution_time_threshold_ms"] / max(1, execution_time))
        
        # Calculate gas efficiency score (higher for lower gas costs)
        gas_threshold = self.config["gas_cost_threshold"].get(network, 5.0)
        gas_efficiency_score = min(1.0, gas_threshold / max(0.1, gas_cost))
        
        # Apply network preference multiplier
        network_multiplier = self.config["network_preferences"].get(network, 1.0)
        
        # Apply token pair preference multiplier
        token_pair_multiplier = self.config["token_pair_preferences"].get(token_pair, 1.0)
        
        # Apply DEX preference multiplier
        buy_dex_multiplier = self.config["dex_preferences"].get(buy_dex, 1.0)
        sell_dex_multiplier = self.config["dex_preferences"].get(sell_dex, 1.0)
        dex_multiplier = (buy_dex_multiplier + sell_dex_multiplier) / 2
        
        # Calculate enhanced confidence score with new factors
        enhanced_confidence = (
            confidence_score * self.config["confidence_weight"] +
            historical_success_rate * self.config["success_rate_weight"] +
            profit_score * self.config["profit_weight"] +
            execution_speed_score * self.config["execution_speed_weight"]
        ) * network_multiplier * token_pair_multiplier * dex_multiplier
        
        # Ensure enhanced confidence is between 0 and 1
        enhanced_confidence = max(0.0, min(1.0, enhanced_confidence))
        
        # Determine if we should execute the trade
        min_trades = self.config["min_historical_trades"]
        min_success_rate = self.config["min_success_rate"]
        min_expected_profit = self.config["min_expected_profit"]
        
        # Get network-specific profit threshold
        profit_threshold = self.profitable_thresholds.get(network, min_expected_profit)
        
        # Dynamic threshold adjustment based on gas costs
        if self.config["dynamic_threshold_adjustment"]:
            # Increase threshold for high gas networks
            profit_threshold = max(profit_threshold, gas_cost * 1.5)
        
        # Check if we have enough historical data
        has_enough_data = (
            network_stats["total_trades"] >= min_trades or
            token_pair_stats["total_trades"] >= min_trades or
            dex_combo_stats["total_trades"] >= min_trades
        )
        
        # Check if the success rate is high enough
        has_good_success_rate = historical_success_rate >= min_success_rate
        
        # Check if the expected profit is high enough
        has_good_profit = expected_profit >= min_expected_profit
        
        # Check if the profit exceeds the network-specific threshold
        exceeds_threshold = expected_profit >= profit_threshold
        
        # Check if the profit is significantly higher than gas costs
        is_profitable_after_gas = expected_profit >= (gas_cost * 1.5)
        
        # Determine if we should execute
        should_execute = (
            has_enough_data and 
            has_good_success_rate and 
            has_good_profit and 
            exceeds_threshold and 
            is_profitable_after_gas
        )
        
        # For high-profit opportunities, consider executing even with limited historical data
        if expected_profit >= self.config["high_profit_threshold_usd"] and is_profitable_after_gas:
            should_execute = True
            reason = "High profit opportunity"
        # Determine reason for decision
        elif not has_enough_data:
            reason = f"Insufficient historical data (need {min_trades} trades)"
        elif not has_good_success_rate:
            reason = f"Low historical success rate ({historical_success_rate:.2f} < {min_success_rate})"
        elif not has_good_profit:
            reason = f"Low expected profit (${expected_profit:.2f} < ${min_expected_profit})"
        elif not exceeds_threshold:
            reason = f"Profit below network threshold (${expected_profit:.2f} < ${profit_threshold:.2f})"
        elif not is_profitable_after_gas:
            reason = f"Not profitable after gas costs (profit: ${expected_profit:.2f}, gas: ${gas_cost:.2f})"
        else:
            reason = "All criteria passed"
        
        # Add historical metrics to prediction
        prediction["historical_success_rate"] = historical_success_rate
        prediction["historical_avg_profit"] = historical_avg_profit
        prediction["enhanced_confidence"] = enhanced_confidence
        prediction["should_execute"] = should_execute
        prediction["evaluation_reason"] = reason
        prediction["profit_score"] = profit_score
        prediction["execution_speed_score"] = execution_speed_score
        prediction["gas_efficiency_score"] = gas_efficiency_score
        
        # Add network-specific metrics
        prediction["network_success_rate"] = network_stats["success_rate"]
        prediction["network_avg_profit"] = network_stats["avg_profit"]
        prediction["network_total_trades"] = network_stats["total_trades"]
        
        # Add token pair metrics
        prediction["token_pair_success_rate"] = token_pair_stats["success_rate"]
        prediction["token_pair_avg_profit"] = token_pair_stats["avg_profit"]
        prediction["token_pair_total_trades"] = token_pair_stats["total_trades"]
        
        # Add DEX combination metrics
        prediction["dex_combo_success_rate"] = dex_combo_stats["success_rate"]
        prediction["dex_combo_avg_profit"] = dex_combo_stats["avg_profit"]
        prediction["dex_combo_total_trades"] = dex_combo_stats["total_trades"]
        
        # Add profit threshold information
        prediction["profit_threshold"] = profit_threshold
        prediction["min_expected_profit"] = min_expected_profit
        
        logger.info(f"Evaluated trade: {token_pair} on {network} - "
                   f"Enhanced confidence: {enhanced_confidence:.4f}, "
                   f"Should execute: {should_execute}, "
                   f"Reason: {reason}")
        
        return prediction

# Example usage
if __name__ == "__main__":
    # Create improved trade selection model
    model = ImprovedTradeSelection()
    
    # Example prediction
    prediction = {
        "network": "arbitrum",
        "token_pair": "WETH-USDC",
        "buy_exchange": "uniswap_v3",
        "sell_exchange": "sushiswap",
        "confidence_score": 0.85,
        "net_profit_usd": 12.5,
        "gas_cost_usd": 1.2,
        "execution_time_ms": 150
    }
    
    # Evaluate prediction
    enhanced_prediction = model.evaluate_trade(prediction)
    
    # Print results
    print(json.dumps(enhanced_prediction, indent=2)) 