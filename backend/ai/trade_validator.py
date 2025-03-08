"""
Trade Validator Module for ArbitrageX

This module implements enhanced validation criteria for trades to filter out
unprofitable or risky trades. It provides a comprehensive validation system
that considers multiple factors including profitability, gas costs, slippage,
market conditions, and historical performance.
"""

import os
import json
import logging
import time
import math
import pickle
import joblib
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union, Any
from pathlib import Path

# Import machine learning libraries (will be installed if needed)
try:
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("Machine learning libraries not available. ML features will be disabled.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trade_validator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TradeValidator")

class TradeValidator:
    """
    Enhanced trade validation system for ArbitrageX.
    
    This class implements a multi-factor validation system that considers:
    1. Profitability thresholds
    2. Gas cost efficiency
    3. Slippage tolerance
    4. Market depth and liquidity
    5. Historical success rates
    6. Front-running risk
    7. Network congestion
    """
    
    def __init__(self, config_path: str = "backend/ai/config/trade_validator_config.json"):
        """
        Initialize the trade validator.
        
        Args:
            config_path: Path to the configuration file
        """
        logger.info("Initializing Trade Validator")
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Create results directory
        self.results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "validation")
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Create models directory
        self.models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Initialize validation statistics
        self.validation_stats = {
            "total_validations": 0,
            "passed_validations": 0,
            "failed_validations": 0,
            "failure_reasons": {},
            "validation_history": [],
            "threshold_adjustments": []
        }
        
        # Initialize machine learning components
        self.ml_model = None
        self.scaler = None
        self.ml_enabled = self.config.get("enable_ml_validation", False) and ML_AVAILABLE
        
        if self.ml_enabled:
            self._initialize_ml_components()
            
        # Initialize validation cache
        self.validation_cache = {}
        self.cache_ttl = self.config.get("validation_cache_ttl", 60)  # 60 seconds default
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Initialize A/B testing if enabled
        self.ab_testing_enabled = self.config.get("enable_ab_testing", False)
        if self.ab_testing_enabled:
            self._initialize_ab_testing()
        
        logger.info("Trade Validator initialized successfully")
    
    def _load_config(self, config_path: str) -> Dict:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Configuration dictionary
        """
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
        """
        Get default configuration values.
        
        Returns:
            Default configuration dictionary
        """
        return {
            "min_profit_threshold": 10.0,  # Minimum profit in USD
            "min_profit_percentage": 0.5,  # Minimum profit as percentage of trade size
            "max_gas_cost_percentage": 40.0,  # Maximum gas cost as percentage of expected profit
            "max_slippage_tolerance": 3.0,  # Maximum slippage tolerance in percentage
            "min_liquidity_score": 0.6,  # Minimum liquidity score (0-1)
            "min_historical_success_rate": 0.6,  # Minimum historical success rate
            "max_front_running_risk": 0.7,  # Maximum front-running risk score (0-1)
            "max_network_congestion": 0.8,  # Maximum network congestion score (0-1)
            "validation_history_limit": 1000,  # Maximum number of validation results to store
            "enable_strict_mode": False,  # Enable strict validation mode
            "enable_adaptive_thresholds": True,  # Enable adaptive thresholds based on market conditions
            "enable_detailed_logging": True,  # Enable detailed validation logging
            "enable_ml_validation": False,  # Enable machine learning validation
            "validation_cache_ttl": 60,  # Validation cache TTL in seconds
            "enable_portfolio_based_thresholds": True,  # Enable portfolio-based thresholds
            "enable_ab_testing": False  # Enable A/B testing
        }
    
    def validate_trade(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a trade against multiple criteria.
        
        Args:
            trade: Trade to validate
            
        Returns:
            Validation result dictionary
        """
        # Check cache first if enabled
        if self.config.get("enable_validation_cache", True):
            cached_result = self.get_cached_validation(trade)
            if cached_result:
                return cached_result
        
        # Initialize validation result
        validation_result = {
            "trade_id": trade.get("trade_id", f"trade_{int(time.time())}"),
            "timestamp": datetime.now().isoformat(),
            "is_valid": True,
            "validation_score": 100.0,  # Start with perfect score and deduct points
            "failure_reasons": [],
            "warnings": [],
            "validation_details": {}
        }
        
        # Apply network-specific validation rules if available
        self._apply_network_specific_rules(trade, validation_result)
        
        # Validate profitability
        self._validate_profitability(trade, validation_result)
        
        # Validate gas costs
        self._validate_gas_costs(trade, validation_result)
        
        # Validate slippage
        self._validate_slippage(trade, validation_result)
        
        # Validate liquidity
        self._validate_liquidity(trade, validation_result)
        
        # Validate historical performance
        self._validate_historical_performance(trade, validation_result)
        
        # Validate front-running risk
        self._validate_front_running_risk(trade, validation_result)
        
        # Validate network conditions
        self._validate_network_conditions(trade, validation_result)
        
        # Validate cross-chain aspects if applicable
        if trade.get("is_cross_chain", False):
            self._validate_cross_chain_trade(trade, validation_result)
        
        # Apply ML-based validation if enabled
        if self.ml_enabled and self.ml_model is not None:
            self._validate_with_ml(trade, validation_result)
        
        # Apply strict mode if enabled
        if self.config.get("enable_strict_mode", False) and validation_result["validation_score"] < 80:
            validation_result["is_valid"] = False
            validation_result["failure_reasons"].append("Failed strict mode validation (score < 80)")
        
        # Update validation statistics
        self._update_validation_stats(validation_result)
        
        # Cache validation result if enabled
        if self.config.get("enable_validation_cache", True):
            self.cache_validation_result(trade, validation_result)
        
        # Log validation result
        if self.config.get("enable_detailed_logging", True):
            if validation_result["is_valid"]:
                logger.info(f"Trade {validation_result['trade_id']} passed validation with score {validation_result['validation_score']:.2f}")
            else:
                logger.warning(f"Trade {validation_result['trade_id']} failed validation with score {validation_result['validation_score']:.2f}: {validation_result['failure_reasons']}")
        
        return validation_result
    
    def _validate_profitability(self, trade: Dict[str, Any], validation_result: Dict[str, Any]):
        """
        Validate trade profitability.
        
        Args:
            trade: Trade to validate
            validation_result: Validation result to update
        """
        # Get profitability thresholds
        min_profit_threshold = self.config.get("min_profit_threshold", 10.0)
        min_profit_percentage = self.config.get("min_profit_percentage", 0.5)
        
        # Get trade details
        expected_profit = trade.get("expected_profit", 0)
        trade_size = trade.get("amount", 0)
        
        # Calculate profit percentage
        profit_percentage = 0
        if trade_size > 0:
            profit_percentage = (expected_profit / trade_size) * 100
        
        # Add validation details
        validation_result["validation_details"]["profitability"] = {
            "expected_profit": expected_profit,
            "trade_size": trade_size,
            "profit_percentage": profit_percentage,
            "min_profit_threshold": min_profit_threshold,
            "min_profit_percentage": min_profit_percentage
        }
        
        # Validate absolute profit
        if expected_profit < min_profit_threshold:
            validation_result["is_valid"] = False
            validation_result["failure_reasons"].append(f"Expected profit (${expected_profit:.2f}) below threshold (${min_profit_threshold:.2f})")
            validation_result["validation_score"] -= 30
        
        # Validate profit percentage
        if profit_percentage < min_profit_percentage:
            validation_result["warnings"].append(f"Profit percentage ({profit_percentage:.2f}%) below threshold ({min_profit_percentage:.2f}%)")
            validation_result["validation_score"] -= 10
    
    def _validate_gas_costs(self, trade: Dict[str, Any], validation_result: Dict[str, Any]):
        """
        Validate gas costs.
        
        Args:
            trade: Trade to validate
            validation_result: Validation result to update
        """
        # Get gas cost threshold
        max_gas_cost_percentage = self.config.get("max_gas_cost_percentage", 40.0)
        
        # Get trade details
        expected_profit = trade.get("expected_profit", 0)
        gas_price = trade.get("gas_price", 0)
        gas_used = trade.get("gas_used", 0)
        gas_cost = trade.get("gas_cost", 0)
        
        # Calculate gas cost percentage
        gas_cost_percentage = 0
        if expected_profit > 0:
            gas_cost_percentage = (gas_cost / expected_profit) * 100
        
        # Add validation details
        validation_result["validation_details"]["gas_costs"] = {
            "gas_price": gas_price,
            "gas_used": gas_used,
            "gas_cost": gas_cost,
            "gas_cost_percentage": gas_cost_percentage,
            "max_gas_cost_percentage": max_gas_cost_percentage
        }
        
        # Validate gas cost percentage
        if gas_cost_percentage > max_gas_cost_percentage:
            validation_result["is_valid"] = False
            validation_result["failure_reasons"].append(f"Gas cost percentage ({gas_cost_percentage:.2f}%) exceeds threshold ({max_gas_cost_percentage:.2f}%)")
            validation_result["validation_score"] -= 25
    
    def _validate_slippage(self, trade: Dict[str, Any], validation_result: Dict[str, Any]):
        """
        Validate slippage tolerance.
        
        Args:
            trade: Trade to validate
            validation_result: Validation result to update
        """
        # Get slippage threshold
        max_slippage_tolerance = self.config.get("max_slippage_tolerance", 3.0)
        
        # Get trade details
        expected_slippage = trade.get("expected_slippage", 0) * 100  # Convert to percentage
        
        # Add validation details
        validation_result["validation_details"]["slippage"] = {
            "expected_slippage": expected_slippage,
            "max_slippage_tolerance": max_slippage_tolerance
        }
        
        # Validate slippage
        if expected_slippage > max_slippage_tolerance:
            validation_result["is_valid"] = False
            validation_result["failure_reasons"].append(f"Expected slippage ({expected_slippage:.2f}%) exceeds tolerance ({max_slippage_tolerance:.2f}%)")
            validation_result["validation_score"] -= 20
    
    def _validate_liquidity(self, trade: Dict[str, Any], validation_result: Dict[str, Any]):
        """
        Validate market liquidity.
        
        Args:
            trade: Trade to validate
            validation_result: Validation result to update
        """
        # Get liquidity threshold
        min_liquidity_score = self.config.get("min_liquidity_score", 0.6)
        
        # Get trade details
        liquidity_score = trade.get("liquidity_score", 1.0)
        
        # Add validation details
        validation_result["validation_details"]["liquidity"] = {
            "liquidity_score": liquidity_score,
            "min_liquidity_score": min_liquidity_score
        }
        
        # Validate liquidity
        if liquidity_score < min_liquidity_score:
            validation_result["warnings"].append(f"Liquidity score ({liquidity_score:.2f}) below threshold ({min_liquidity_score:.2f})")
            validation_result["validation_score"] -= 15
    
    def _validate_historical_performance(self, trade: Dict[str, Any], validation_result: Dict[str, Any]):
        """
        Validate historical performance.
        
        Args:
            trade: Trade to validate
            validation_result: Validation result to update
        """
        # Get historical performance threshold
        min_historical_success_rate = self.config.get("min_historical_success_rate", 0.6)
        
        # Get trade details
        token_pair = trade.get("token_pair", "unknown")
        dex = trade.get("dex", "unknown")
        historical_success_rate = trade.get("historical_success_rate", 1.0)
        
        # Add validation details
        validation_result["validation_details"]["historical_performance"] = {
            "token_pair": token_pair,
            "dex": dex,
            "historical_success_rate": historical_success_rate,
            "min_historical_success_rate": min_historical_success_rate
        }
        
        # Validate historical performance
        if historical_success_rate < min_historical_success_rate:
            validation_result["warnings"].append(f"Historical success rate ({historical_success_rate:.2f}) below threshold ({min_historical_success_rate:.2f})")
            validation_result["validation_score"] -= 10
    
    def _validate_front_running_risk(self, trade: Dict[str, Any], validation_result: Dict[str, Any]):
        """
        Validate front-running risk with enhanced MEV protection analysis.
        
        Args:
            trade: Trade to validate
            validation_result: Validation result to update
        """
        # Get front-running risk threshold
        max_front_running_risk = self.config.get("max_front_running_risk", 0.7)
        
        # Perform enhanced MEV risk analysis
        mev_analysis = self._analyze_mev_risk(trade)
        
        # Add validation details
        validation_result["validation_details"]["front_running_risk"] = {
            "front_running_risk": mev_analysis["mev_risk_score"],
            "max_front_running_risk": max_front_running_risk,
            "mev_factors": mev_analysis["mev_factors"],
            "protection_methods": mev_analysis["protection_methods"],
            "recommended_protection": mev_analysis["recommended_protection"]
        }
        
        # Validate front-running risk
        if mev_analysis["mev_risk_score"] > max_front_running_risk:
            validation_result["warnings"].append(
                f"Front-running risk ({mev_analysis['mev_risk_score']:.2f}) exceeds threshold ({max_front_running_risk:.2f})"
            )
            validation_result["validation_score"] -= 15
            
            # Add protection recommendation
            validation_result["warnings"].append(
                f"Recommended MEV protection: {mev_analysis['recommended_protection']}"
            )
            
            # If risk is very high, fail validation
            if mev_analysis["mev_risk_score"] > 0.9:
                validation_result["is_valid"] = False
                validation_result["failure_reasons"].append(f"Front-running risk ({mev_analysis['mev_risk_score']:.2f}) is extremely high")
    
    def _analyze_mev_risk(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze MEV risk for a trade with advanced metrics.
        
        Args:
            trade: Trade to analyze
            
        Returns:
            MEV risk analysis dictionary
        """
        # Basic factors from current implementation
        token_pair = trade.get("token_pair", "unknown")
        network = trade.get("network", "unknown")
        expected_profit = trade.get("expected_profit", 0)
        front_running_risk = trade.get("front_running_risk", 0.0)
        
        # Enhanced MEV analysis factors
        mev_factors = {
            # Token popularity factor (higher = more MEV bots watching)
            "token_popularity": self._get_token_popularity(token_pair),
            
            # Recent MEV activity on this pair
            "recent_mev_activity": self._get_recent_mev_activity(token_pair, network),
            
            # Profit attractiveness (how likely to attract MEV)
            "profit_attractiveness": min(1.0, expected_profit / 100),
            
            # DEX vulnerability to MEV
            "dex_vulnerability": self._get_dex_mev_vulnerability(trade.get("dex", "unknown")),
            
            # Current mempool congestion
            "mempool_congestion": trade.get("network_congestion", 0.5)
        }
        
        # Calculate weighted MEV risk score
        weights = {
            "token_popularity": 0.25,
            "recent_mev_activity": 0.3,
            "profit_attractiveness": 0.2,
            "dex_vulnerability": 0.15,
            "mempool_congestion": 0.1
        }
        
        # Use existing front_running_risk as a base and adjust with weighted factors
        base_risk = front_running_risk if front_running_risk > 0 else 0.5
        weighted_factor_score = sum(score * weights[factor] for factor, score in mev_factors.items())
        
        # Combine base risk and weighted factors (70% base, 30% factors)
        mev_risk_score = (base_risk * 0.7) + (weighted_factor_score * 0.3)
        
        # Get available MEV protection methods
        protection_methods = self._get_available_mev_protection(network)
        
        return {
            "mev_risk_score": mev_risk_score,
            "mev_factors": mev_factors,
            "protection_methods": protection_methods,
            "recommended_protection": self._recommend_mev_protection(mev_risk_score, network)
        }
    
    def _get_token_popularity(self, token_pair: str) -> float:
        """
        Get token popularity score (0-1).
        
        Args:
            token_pair: Token pair to check
            
        Returns:
            Popularity score (0-1)
        """
        # In a real implementation, this would query a database of token popularity
        # For now, use a simple lookup for common pairs
        popular_pairs = {
            "WETH-USDC": 0.95,
            "WETH-USDT": 0.93,
            "WBTC-USDC": 0.90,
            "WETH-DAI": 0.85,
            "WBTC-WETH": 0.82,
            "LINK-WETH": 0.75,
            "UNI-WETH": 0.70,
            "AAVE-WETH": 0.65
        }
        
        return popular_pairs.get(token_pair, 0.5)
    
    def _get_recent_mev_activity(self, token_pair: str, network: str) -> float:
        """
        Get recent MEV activity score for a token pair on a network (0-1).
        
        Args:
            token_pair: Token pair to check
            network: Network to check
            
        Returns:
            Recent MEV activity score (0-1)
        """
        # In a real implementation, this would query recent MEV activity
        # For now, use a simple lookup for common pairs and networks
        high_mev_pairs = ["WETH-USDC", "WETH-USDT", "WBTC-USDC"]
        medium_mev_pairs = ["WETH-DAI", "WBTC-WETH", "LINK-WETH"]
        
        high_mev_networks = ["ethereum", "bsc"]
        medium_mev_networks = ["arbitrum", "polygon"]
        
        if token_pair in high_mev_pairs and network in high_mev_networks:
            return 0.9
        elif token_pair in high_mev_pairs and network in medium_mev_networks:
            return 0.7
        elif token_pair in medium_mev_pairs and network in high_mev_networks:
            return 0.6
        elif token_pair in medium_mev_pairs and network in medium_mev_networks:
            return 0.4
        else:
            return 0.3
    
    def _get_dex_mev_vulnerability(self, dex: str) -> float:
        """
        Get DEX vulnerability to MEV (0-1).
        
        Args:
            dex: DEX to check
            
        Returns:
            DEX vulnerability score (0-1)
        """
        # In a real implementation, this would be based on DEX architecture
        vulnerabilities = {
            "uniswap_v2": 0.8,
            "sushiswap": 0.75,
            "uniswap_v3": 0.6,
            "curve": 0.5,
            "balancer": 0.55,
            "dodo": 0.4
        }
        
        return vulnerabilities.get(dex, 0.6)
    
    def _get_available_mev_protection(self, network: str) -> List[str]:
        """
        Get available MEV protection methods for a network.
        
        Args:
            network: Network to check
            
        Returns:
            List of available protection methods
        """
        # Common protection methods
        common_methods = ["private_tx", "time_delay"]
        
        # Network-specific methods
        if network == "ethereum":
            return common_methods + ["flashbots", "eden", "mev_blocker"]
        elif network == "arbitrum":
            return common_methods + ["arbitrum_sequencer"]
        elif network == "polygon":
            return common_methods + ["polygon_shield"]
        elif network == "bsc":
            return common_methods + ["bsc_relay"]
        else:
            return common_methods
    
    def _recommend_mev_protection(self, risk_score: float, network: str) -> str:
        """
        Recommend MEV protection method based on risk score and network.
        
        Args:
            risk_score: MEV risk score
            network: Network
            
        Returns:
            Recommended protection method
        """
        available_methods = self._get_available_mev_protection(network)
        
        if risk_score > 0.8:
            # High risk - use strongest protection
            if "flashbots" in available_methods and network == "ethereum":
                return "flashbots"
            elif "arbitrum_sequencer" in available_methods and network == "arbitrum":
                return "arbitrum_sequencer"
            elif "polygon_shield" in available_methods and network == "polygon":
                return "polygon_shield"
            elif "bsc_relay" in available_methods and network == "bsc":
                return "bsc_relay"
            else:
                return "private_tx"
        elif risk_score > 0.5:
            # Medium risk
            if "private_tx" in available_methods:
                return "private_tx"
            else:
                return "time_delay"
        else:
            # Low risk
            return "standard_tx"
    
    def _validate_network_conditions(self, trade: Dict[str, Any], validation_result: Dict[str, Any]):
        """
        Validate network conditions.
        
        Args:
            trade: Trade to validate
            validation_result: Validation result to update
        """
        # Get network congestion threshold
        max_network_congestion = self.config.get("max_network_congestion", 0.8)
        
        # Get trade details
        network = trade.get("network", "unknown")
        network_congestion = trade.get("network_congestion", 0.0)
        
        # Add validation details
        validation_result["validation_details"]["network_conditions"] = {
            "network": network,
            "network_congestion": network_congestion,
            "max_network_congestion": max_network_congestion
        }
        
        # Validate network congestion
        if network_congestion > max_network_congestion:
            validation_result["warnings"].append(f"Network congestion ({network_congestion:.2f}) exceeds threshold ({max_network_congestion:.2f})")
            validation_result["validation_score"] -= 10
    
    def _update_validation_stats(self, validation_result: Dict[str, Any]):
        """
        Update validation statistics.
        
        Args:
            validation_result: Validation result
        """
        # Update counters
        self.validation_stats["total_validations"] += 1
        
        if validation_result["is_valid"]:
            self.validation_stats["passed_validations"] += 1
        else:
            self.validation_stats["failed_validations"] += 1
            
            # Update failure reasons
            for reason in validation_result["failure_reasons"]:
                if reason in self.validation_stats["failure_reasons"]:
                    self.validation_stats["failure_reasons"][reason] += 1
                else:
                    self.validation_stats["failure_reasons"][reason] = 1
        
        # Add to validation history
        self.validation_stats["validation_history"].append({
            "trade_id": validation_result["trade_id"],
            "timestamp": validation_result["timestamp"],
            "is_valid": validation_result["is_valid"],
            "validation_score": validation_result["validation_score"],
            "failure_reasons": validation_result["failure_reasons"]
        })
        
        # Limit validation history size
        history_limit = self.config.get("validation_history_limit", 1000)
        if len(self.validation_stats["validation_history"]) > history_limit:
            self.validation_stats["validation_history"] = self.validation_stats["validation_history"][-history_limit:]
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """
        Get validation statistics.
        
        Returns:
            Validation statistics dictionary
        """
        return self.validation_stats
    
    def save_validation_stats(self):
        """Save validation statistics to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stats_file = os.path.join(self.results_dir, f"validation_stats_{timestamp}.json")
        
        try:
            with open(stats_file, 'w') as f:
                json.dump(self.validation_stats, f, indent=2)
            logger.info(f"Validation statistics saved to {stats_file}")
        except Exception as e:
            logger.error(f"Error saving validation statistics: {e}")
    
    def adjust_thresholds(self, market_conditions: Dict[str, Any]):
        """
        Adjust validation thresholds based on market conditions.
        
        Args:
            market_conditions: Dictionary containing market conditions
        """
        if not self.config.get("enable_adaptive_thresholds", True):
            return
        
        # Get market volatility
        market_volatility = market_conditions.get("market_volatility", 0.0)
        
        # Adjust profit threshold based on volatility
        # Higher volatility = higher profit threshold
        base_profit_threshold = self._get_default_config()["min_profit_threshold"]
        volatility_factor = 1.0 + (market_volatility * 2.0)  # Scale factor based on volatility
        self.config["min_profit_threshold"] = base_profit_threshold * volatility_factor
        
        # Adjust slippage tolerance based on volatility
        # Higher volatility = higher slippage tolerance
        base_slippage_tolerance = self._get_default_config()["max_slippage_tolerance"]
        self.config["max_slippage_tolerance"] = base_slippage_tolerance * volatility_factor
        
        # Adjust gas cost percentage based on network congestion
        # Higher congestion = higher gas cost percentage allowed
        network_congestion = market_conditions.get("network_congestion", 0.0)
        base_gas_cost_percentage = self._get_default_config()["max_gas_cost_percentage"]
        congestion_factor = 1.0 + (network_congestion * 0.5)  # Scale factor based on congestion
        self.config["max_gas_cost_percentage"] = base_gas_cost_percentage * congestion_factor
        
        logger.info(f"Adjusted validation thresholds based on market conditions: "
                   f"profit threshold=${self.config['min_profit_threshold']:.2f}, "
                   f"slippage tolerance={self.config['max_slippage_tolerance']:.2f}%, "
                   f"gas cost percentage={self.config['max_gas_cost_percentage']:.2f}%")

    def _initialize_ml_components(self):
        """Initialize machine learning components."""
        try:
            # Try to load existing model
            model_path = os.path.join(self.models_dir, "validation_model.pkl")
            scaler_path = os.path.join(self.models_dir, "feature_scaler.pkl")
            
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                self.ml_model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                logger.info("Loaded existing ML model and scaler")
            else:
                # Initialize new model and scaler
                self.ml_model = GradientBoostingClassifier()
                self.scaler = StandardScaler()
                logger.info("Initialized new ML model and scaler")
                
            logger.info("ML components initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ML components: {e}")
            self.ml_enabled = False

    def _validate_with_ml(self, trade: Dict[str, Any], validation_result: Dict[str, Any]):
        """
        Validate trade using machine learning model.
        
        Args:
            trade: Trade to validate
            validation_result: Validation result to update
        """
        try:
            # Extract features for ML prediction
            features = self._extract_ml_features(trade)
            
            if features is None:
                validation_result["warnings"].append("Could not extract features for ML validation")
                return
            
            # Scale features if scaler is available
            if self.scaler is not None:
                features_scaled = self.scaler.transform([features])
            else:
                features_scaled = [features]
            
            # Make prediction
            success_probability = self.ml_model.predict_proba(features_scaled)[0][1]
            
            # Add validation details
            validation_result["validation_details"]["ml_validation"] = {
                "success_probability": success_probability,
                "threshold": self.config.get("ml_success_probability_threshold", 0.6)
            }
            
            # Validate success probability
            if success_probability < self.config.get("ml_success_probability_threshold", 0.6):
                validation_result["warnings"].append(f"ML success probability ({success_probability:.2f}) below threshold ({self.config.get('ml_success_probability_threshold', 0.6):.2f})")
                validation_result["validation_score"] -= 15
                
                # If probability is very low, fail validation
                if success_probability < 0.3:
                    validation_result["is_valid"] = False
                    validation_result["failure_reasons"].append(f"ML success probability ({success_probability:.2f}) is extremely low")
            
            logger.debug(f"ML validation: success probability = {success_probability:.2f}")
        except Exception as e:
            logger.error(f"Error in ML validation: {e}")
            validation_result["warnings"].append(f"ML validation error: {str(e)}")
    
    def _extract_ml_features(self, trade: Dict[str, Any]) -> List[float]:
        """
        Extract features from trade for ML prediction.
        
        Args:
            trade: Trade to extract features from
            
        Returns:
            List of features
        """
        try:
            # Extract relevant features
            features = [
                trade.get("expected_profit", 0),
                trade.get("gas_cost", 0) / max(trade.get("expected_profit", 0.01), 0.01),  # Gas cost ratio
                trade.get("expected_slippage", 0) * 100,  # Convert to percentage
                trade.get("liquidity_score", 0),
                trade.get("historical_success_rate", 0),
                trade.get("front_running_risk", 0),
                trade.get("network_congestion", 0)
            ]
            
            return features
        except Exception as e:
            logger.error(f"Error extracting ML features: {e}")
            return None

    def _apply_network_specific_rules(self, trade: Dict[str, Any], validation_result: Dict[str, Any]):
        """
        Apply network-specific validation rules.
        
        Args:
            trade: Trade to validate
            validation_result: Validation result to update
        """
        network = trade.get("network", "unknown")
        
        # Get network-specific settings
        network_settings = self.config.get("network_specific_settings", {}).get(network, {})
        
        if not network_settings:
            return
            
        # Apply network-specific thresholds
        for key, value in network_settings.items():
            if key in self.config:
                # Temporarily override global setting with network-specific setting
                original_value = self.config[key]
                self.config[key] = value
                
                # Restore original value after validation
                # This will be done by the calling method for each validation step
        
        # Network-specific validation logic
        if network == "ethereum":
            # Ethereum-specific rules
            if trade.get("gas_price", 0) < self._get_ethereum_base_fee(trade) * 1.1:
                validation_result["warnings"].append("Gas price may be too low for Ethereum")
                validation_result["validation_score"] -= 5
                
        elif network == "arbitrum":
            # Arbitrum-specific rules
            if trade.get("expected_profit", 0) < 20 and trade.get("amount", 0) < 1000:
                validation_result["warnings"].append("Small trades on Arbitrum may not be cost-effective")
                validation_result["validation_score"] -= 10
                
        elif network == "polygon":
            # Polygon-specific rules
            if trade.get("expected_slippage", 0) < 0.005:
                validation_result["warnings"].append("Slippage estimate may be too optimistic for Polygon")
                validation_result["validation_score"] -= 5
                
        elif network == "bsc":
            # BSC-specific rules
            if not trade.get("is_flash_loan", False) and trade.get("amount", 0) > 10000:
                validation_result["warnings"].append("Large non-flash loan trades on BSC may face front-running")
                validation_result["validation_score"] -= 15
    
    def _get_ethereum_base_fee(self, trade: Dict[str, Any]) -> float:
        """
        Get Ethereum base fee estimate.
        
        Args:
            trade: Trade containing network information
            
        Returns:
            Estimated base fee in Gwei
        """
        # In a real implementation, this would query the current base fee
        # For now, use a simple estimate based on network congestion
        network_congestion = trade.get("network_congestion", 0.5)
        base_fee = 15.0 + (network_congestion * 30.0)  # 15-45 Gwei based on congestion
        return base_fee
        
    def train_validation_model(self, historical_data: List[Dict[str, Any]]) -> bool:
        """
        Train a machine learning model to predict trade success probability.
        
        Args:
            historical_data: List of historical trades with outcomes
            
        Returns:
            True if training was successful, False otherwise
        """
        if not ML_AVAILABLE:
            logger.warning("Machine learning libraries not available. Cannot train model.")
            return False
            
        try:
            logger.info(f"Training validation model with {len(historical_data)} historical trades")
            
            # Extract features and labels from historical data
            features = []
            labels = []
            
            for trade in historical_data:
                # Extract features
                trade_features = self._extract_ml_features(trade)
                
                if trade_features is None:
                    continue
                
                # Extract label (1 for successful trades, 0 for failed trades)
                success = 1 if trade.get("status") == "completed" and trade.get("actual_profit", 0) > 0 else 0
                
                features.append(trade_features)
                labels.append(success)
            
            if len(features) < 10:
                logger.warning("Not enough valid training samples (minimum 10 required)")
                return False
                
            # Scale features
            self.scaler = StandardScaler()
            features_scaled = self.scaler.fit_transform(features)
            
            # Train model
            self.ml_model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=3,
                random_state=42
            )
            self.ml_model.fit(features_scaled, labels)
            
            # Save model and scaler
            joblib.dump(self.ml_model, os.path.join(self.models_dir, "validation_model.pkl"))
            joblib.dump(self.scaler, os.path.join(self.models_dir, "feature_scaler.pkl"))
            
            # Enable ML validation
            self.ml_enabled = True
            self.config["enable_ml_validation"] = True
            
            logger.info("Validation model trained and saved successfully")
            
            # Calculate and log training accuracy
            predictions = self.ml_model.predict(features_scaled)
            accuracy = sum(predictions == labels) / len(labels)
            logger.info(f"Training accuracy: {accuracy:.2f}")
            
            return True
        except Exception as e:
            logger.error(f"Error training validation model: {e}")
            return False

    def get_cache_key(self, trade: Dict[str, Any]) -> str:
        """
        Generate a cache key for a trade.
        
        Args:
            trade: Trade to generate cache key for
            
        Returns:
            Cache key string
        """
        # Include key trade parameters in the cache key
        key_params = [
            trade.get("token_pair", ""),
            trade.get("dex", ""),
            trade.get("network", ""),
            str(round(trade.get("amount", 0), 2)),
            str(round(trade.get("expected_profit", 0), 2)),
            str(round(trade.get("gas_price", 0), 2))
        ]
        return ":".join(key_params)
    
    def get_cached_validation(self, trade: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get cached validation result if available and not expired.
        
        Args:
            trade: Trade to get cached validation for
            
        Returns:
            Cached validation result or None if not found or expired
        """
        cache_key = self.get_cache_key(trade)
        
        if cache_key in self.validation_cache:
            cached_result, timestamp = self.validation_cache[cache_key]
            
            # Check if cache entry is still valid
            if time.time() - timestamp < self.cache_ttl:
                self.cache_hits += 1
                logger.debug(f"Cache hit for trade {trade.get('trade_id', 'unknown')}")
                return cached_result
        
        self.cache_misses += 1
        logger.debug(f"Cache miss for trade {trade.get('trade_id', 'unknown')}")
        return None
    
    def cache_validation_result(self, trade: Dict[str, Any], validation_result: Dict[str, Any]):
        """
        Cache a validation result.
        
        Args:
            trade: Trade that was validated
            validation_result: Validation result to cache
        """
        cache_key = self.get_cache_key(trade)
        self.validation_cache[cache_key] = (validation_result, time.time())
        
        # Clean up old cache entries
        self._clean_validation_cache()
        
        logger.debug(f"Cached validation result for trade {trade.get('trade_id', 'unknown')}")
    
    def _clean_validation_cache(self):
        """Clean up expired cache entries."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.validation_cache.items()
            if current_time - timestamp > self.cache_ttl
        ]
        
        for key in expired_keys:
            del self.validation_cache[key]
            
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_size": len(self.validation_cache),
            "cache_hit_ratio": self.cache_hits / max(self.cache_hits + self.cache_misses, 1)
        }

    def _validate_cross_chain_trade(self, trade: Dict[str, Any], validation_result: Dict[str, Any]):
        """
        Validate cross-chain specific aspects of a trade.
        
        Args:
            trade: Trade to validate
            validation_result: Validation result to update
        """
        # Get source and destination networks
        source_network = trade.get("source_network", "unknown")
        dest_network = trade.get("destination_network", "unknown")
        
        # Check bridge fees
        bridge_fee = self._get_bridge_fee(source_network, dest_network, trade.get("amount", 0))
        bridge_fee_percentage = (bridge_fee / trade.get("expected_profit", 1)) * 100
        
        # Check bridge time
        bridge_time = self._get_bridge_time(source_network, dest_network)
        
        # Check bridge reliability
        bridge_reliability = self._get_bridge_reliability(source_network, dest_network)
        
        # Add validation details
        validation_result["validation_details"]["cross_chain"] = {
            "source_network": source_network,
            "destination_network": dest_network,
            "bridge_fee": bridge_fee,
            "bridge_fee_percentage": bridge_fee_percentage,
            "bridge_time": bridge_time,
            "bridge_reliability": bridge_reliability,
            "max_bridge_fee_percentage": self.config.get("max_bridge_fee_percentage", 30.0),
            "max_bridge_time": self.config.get("max_bridge_time", 600),
            "min_bridge_reliability": self.config.get("min_bridge_reliability", 0.95)
        }
        
        # Validate bridge fee
        if bridge_fee_percentage > self.config.get("max_bridge_fee_percentage", 30.0):
            validation_result["is_valid"] = False
            validation_result["failure_reasons"].append(
                f"Bridge fee (${bridge_fee:.2f}, {bridge_fee_percentage:.2f}%) exceeds threshold ({self.config.get('max_bridge_fee_percentage', 30.0):.2f}%)"
            )
            validation_result["validation_score"] -= 25
        
        # Validate bridge time
        if bridge_time > self.config.get("max_bridge_time", 600):  # 10 minutes
            validation_result["warnings"].append(
                f"Bridge time ({bridge_time}s) may impact trade timing"
            )
            validation_result["validation_score"] -= 10
        
        # Validate bridge reliability
        if bridge_reliability < self.config.get("min_bridge_reliability", 0.95):
            validation_result["warnings"].append(
                f"Bridge reliability ({bridge_reliability:.2f}) below threshold ({self.config.get('min_bridge_reliability', 0.95):.2f})"
            )
            validation_result["validation_score"] -= 15
            
            # If reliability is very low, fail validation
            if bridge_reliability < 0.8:
                validation_result["is_valid"] = False
                validation_result["failure_reasons"].append(
                    f"Bridge reliability ({bridge_reliability:.2f}) is extremely low"
                )
    
    def _get_bridge_fee(self, source_network: str, dest_network: str, amount: float) -> float:
        """
        Get estimated bridge fee for cross-chain transfer.
        
        Args:
            source_network: Source network
            dest_network: Destination network
            amount: Amount to transfer
            
        Returns:
            Estimated bridge fee in USD
        """
        # In a real implementation, this would query current bridge fees
        # For now, use a simple estimate based on networks and amount
        
        # Base fee by network pair
        base_fees = {
            ("ethereum", "arbitrum"): 5.0,
            ("ethereum", "polygon"): 3.0,
            ("ethereum", "bsc"): 8.0,
            ("arbitrum", "ethereum"): 15.0,
            ("polygon", "ethereum"): 10.0,
            ("bsc", "ethereum"): 12.0,
            ("polygon", "arbitrum"): 7.0,
            ("arbitrum", "polygon"): 7.0,
            ("bsc", "polygon"): 6.0,
            ("polygon", "bsc"): 6.0,
            ("bsc", "arbitrum"): 9.0,
            ("arbitrum", "bsc"): 9.0
        }
        
        # Get base fee for network pair
        base_fee = base_fees.get((source_network, dest_network), 10.0)
        
        # Add percentage-based fee (0.1% of amount)
        percentage_fee = amount * 0.001
        
        return base_fee + percentage_fee
    
    def _get_bridge_time(self, source_network: str, dest_network: str) -> int:
        """
        Get estimated bridge time for cross-chain transfer in seconds.
        
        Args:
            source_network: Source network
            dest_network: Destination network
            
        Returns:
            Estimated bridge time in seconds
        """
        # In a real implementation, this would query current bridge times
        # For now, use a simple estimate based on networks
        
        # Bridge times by network pair (in seconds)
        bridge_times = {
            ("ethereum", "arbitrum"): 120,
            ("ethereum", "polygon"): 300,
            ("ethereum", "bsc"): 600,
            ("arbitrum", "ethereum"): 900,
            ("polygon", "ethereum"): 1200,
            ("bsc", "ethereum"): 1800,
            ("polygon", "arbitrum"): 600,
            ("arbitrum", "polygon"): 600,
            ("bsc", "polygon"): 900,
            ("polygon", "bsc"): 900,
            ("bsc", "arbitrum"): 1200,
            ("arbitrum", "bsc"): 1200
        }
        
        return bridge_times.get((source_network, dest_network), 900)
    
    def _get_bridge_reliability(self, source_network: str, dest_network: str) -> float:
        """
        Get bridge reliability score (0-1).
        
        Args:
            source_network: Source network
            dest_network: Destination network
            
        Returns:
            Bridge reliability score (0-1)
        """
        # In a real implementation, this would query historical bridge reliability
        # For now, use a simple estimate based on networks
        
        # Reliability scores by network pair
        reliability_scores = {
            ("ethereum", "arbitrum"): 0.99,
            ("ethereum", "polygon"): 0.98,
            ("ethereum", "bsc"): 0.95,
            ("arbitrum", "ethereum"): 0.97,
            ("polygon", "ethereum"): 0.96,
            ("bsc", "ethereum"): 0.94,
            ("polygon", "arbitrum"): 0.93,
            ("arbitrum", "polygon"): 0.93,
            ("bsc", "polygon"): 0.92,
            ("polygon", "bsc"): 0.92,
            ("bsc", "arbitrum"): 0.90,
            ("arbitrum", "bsc"): 0.90
        }
        
        return reliability_scores.get((source_network, dest_network), 0.9)

    def adjust_thresholds_based_on_portfolio(self, portfolio_stats: Dict[str, Any]):
        """
        Adjust validation thresholds based on portfolio performance.
        
        Args:
            portfolio_stats: Dictionary containing portfolio performance statistics
        """
        if not self.config.get("enable_portfolio_based_thresholds", True):
            return
            
        logger.info("Adjusting validation thresholds based on portfolio performance")
        
        # Get current profit/loss status
        daily_pnl = portfolio_stats.get("daily_pnl", 0)
        weekly_pnl = portfolio_stats.get("weekly_pnl", 0)
        daily_target = portfolio_stats.get("daily_target", 100)
        
        # Calculate adjustment factors
        if daily_pnl < 0:
            # We're losing money today, be more conservative
            risk_adjustment = 0.8  # Reduce risk by 20%
            logger.info("Daily PnL is negative, reducing risk by 20%")
        elif weekly_pnl < 0:
            # Losing money this week, slightly more conservative
            risk_adjustment = 0.9  # Reduce risk by 10%
            logger.info("Weekly PnL is negative, reducing risk by 10%")
        elif daily_pnl > daily_target:
            # Exceeding daily target, can take more risk
            risk_adjustment = 1.2  # Increase risk tolerance by 20%
            logger.info(f"Daily PnL (${daily_pnl:.2f}) exceeds target (${daily_target:.2f}), increasing risk tolerance by 20%")
        else:
            # Normal conditions
            risk_adjustment = 1.0
            logger.info("Portfolio performance is within normal range, no adjustment needed")
        
        # Store original thresholds for reference
        original_thresholds = {
            "min_profit_threshold": self.config.get("min_profit_threshold", 10.0),
            "max_gas_cost_percentage": self.config.get("max_gas_cost_percentage", 40.0),
            "max_slippage_tolerance": self.config.get("max_slippage_tolerance", 3.0),
            "min_liquidity_score": self.config.get("min_liquidity_score", 0.6),
            "max_front_running_risk": self.config.get("max_front_running_risk", 0.7)
        }
        
        # Apply adjustments to thresholds
        self.config["min_profit_threshold"] = original_thresholds["min_profit_threshold"] * (1 / risk_adjustment)
        self.config["max_gas_cost_percentage"] = original_thresholds["max_gas_cost_percentage"] * risk_adjustment
        self.config["max_slippage_tolerance"] = original_thresholds["max_slippage_tolerance"] * risk_adjustment
        self.config["min_liquidity_score"] = min(1.0, original_thresholds["min_liquidity_score"] / risk_adjustment)
        self.config["max_front_running_risk"] = original_thresholds["max_front_running_risk"] * risk_adjustment
        
        # Log adjusted thresholds
        logger.info(f"Adjusted validation thresholds based on portfolio performance (adjustment factor: {risk_adjustment:.2f}):")
        logger.info(f"  - min_profit_threshold: ${original_thresholds['min_profit_threshold']:.2f} -> ${self.config['min_profit_threshold']:.2f}")
        logger.info(f"  - max_gas_cost_percentage: {original_thresholds['max_gas_cost_percentage']:.2f}% -> {self.config['max_gas_cost_percentage']:.2f}%")
        logger.info(f"  - max_slippage_tolerance: {original_thresholds['max_slippage_tolerance']:.2f}% -> {self.config['max_slippage_tolerance']:.2f}%")
        logger.info(f"  - min_liquidity_score: {original_thresholds['min_liquidity_score']:.2f} -> {self.config['min_liquidity_score']:.2f}")
        logger.info(f"  - max_front_running_risk: {original_thresholds['max_front_running_risk']:.2f} -> {self.config['max_front_running_risk']:.2f}")
        
        # Add adjustment to validation statistics
        self.validation_stats["threshold_adjustments"].append({
            "timestamp": datetime.now().isoformat(),
            "risk_adjustment": risk_adjustment,
            "daily_pnl": daily_pnl,
            "weekly_pnl": weekly_pnl,
            "daily_target": daily_target,
            "original_thresholds": original_thresholds,
            "adjusted_thresholds": {
                "min_profit_threshold": self.config["min_profit_threshold"],
                "max_gas_cost_percentage": self.config["max_gas_cost_percentage"],
                "max_slippage_tolerance": self.config["max_slippage_tolerance"],
                "min_liquidity_score": self.config["min_liquidity_score"],
                "max_front_running_risk": self.config["max_front_running_risk"]
            }
        })

    def _initialize_ab_testing(self):
        """Initialize A/B testing for validation strategies."""
        logger.info("Initializing A/B testing for validation strategies")
        
        # Define validation strategies
        self.strategies = {
            "default": {
                "min_profit_threshold": 12.0,
                "max_gas_cost_percentage": 35.0,
                "max_slippage_tolerance": 2.5,
                "min_liquidity_score": 0.7,
                "min_historical_success_rate": 0.65,
                "max_front_running_risk": 0.6
            },
            "conservative": {
                "min_profit_threshold": 15.0,
                "max_gas_cost_percentage": 25.0,
                "max_slippage_tolerance": 1.5,
                "min_liquidity_score": 0.8,
                "min_historical_success_rate": 0.75,
                "max_front_running_risk": 0.5
            },
            "aggressive": {
                "min_profit_threshold": 8.0,
                "max_gas_cost_percentage": 45.0,
                "max_slippage_tolerance": 3.5,
                "min_liquidity_score": 0.6,
                "min_historical_success_rate": 0.55,
                "max_front_running_risk": 0.7
            }
        }
        
        # Initialize strategy statistics
        self.strategy_stats = {strategy: {
            "trades_validated": 0,
            "trades_executed": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_profit": 0,
            "total_loss": 0,
            "roi": 0
        } for strategy in self.strategies}
        
        logger.info(f"A/B testing initialized with {len(self.strategies)} strategies: {', '.join(self.strategies.keys())}")
        
    def select_validation_strategy(self, trade: Dict[str, Any]) -> str:
        """
        Select a validation strategy for A/B testing.
        
        Args:
            trade: Trade to validate
            
        Returns:
            Selected strategy name
        """
        if not self.ab_testing_enabled:
            return "default"
            
        # Deterministic selection based on trade ID to ensure consistency
        trade_id = trade.get("trade_id", "")
        if not trade_id:
            return "default"
        
        # Use the last character of the trade ID to select a strategy
        char_value = ord(trade_id[-1]) if trade_id else 0
        if char_value % 3 == 0:
            return "conservative"
        elif char_value % 3 == 1:
            return "aggressive"
        else:
            return "default"
            
    def validate_trade_with_strategy(self, trade: Dict[str, Any], strategy: str) -> Dict[str, Any]:
        """
        Validate a trade using a specific strategy.
        
        Args:
            trade: Trade to validate
            strategy: Strategy to use
            
        Returns:
            Validation result
        """
        if not self.ab_testing_enabled or strategy not in self.strategies:
            return self.validate_trade(trade)
            
        # Store original config
        original_config = self.config.copy()
        
        # Apply strategy config
        for key, value in self.strategies[strategy].items():
            self.config[key] = value
            
        # Validate trade with strategy config
        validation_result = self.validate_trade(trade)
        
        # Restore original config
        self.config = original_config
        
        # Update strategy statistics
        self.strategy_stats[strategy]["trades_validated"] += 1
        
        # Add strategy info to validation result
        validation_result["strategy"] = strategy
        validation_result["strategy_config"] = self.strategies[strategy]
        
        return validation_result
        
    def update_ab_testing_stats(self, strategy: str, trade_result: Dict[str, Any]):
        """
        Update A/B testing statistics for a strategy.
        
        Args:
            strategy: Strategy name
            trade_result: Trade execution result
        """
        if not self.ab_testing_enabled or strategy not in self.strategy_stats:
            return
            
        stats = self.strategy_stats[strategy]
        stats["trades_executed"] += 1
        
        if trade_result.get("status") == "completed":
            stats["successful_trades"] += 1
            profit = trade_result.get("actual_profit", 0)
            stats["total_profit"] += profit
        else:
            stats["failed_trades"] += 1
            loss = trade_result.get("gas_cost", 0)
            stats["total_loss"] += loss
            
        # Calculate ROI
        total_cost = stats["total_loss"]
        if stats["total_profit"] > 0 and total_cost > 0:
            stats["roi"] = (stats["total_profit"] / total_cost) * 100
            
        logger.info(f"Updated A/B testing stats for strategy '{strategy}': "
                   f"{stats['successful_trades']}/{stats['trades_executed']} successful trades, "
                   f"${stats['total_profit']:.2f} profit, ${stats['total_loss']:.2f} loss, "
                   f"{stats['roi']:.2f}% ROI")
        
    def get_ab_testing_stats(self) -> Dict[str, Any]:
        """
        Get A/B testing statistics.
        
        Returns:
            A/B testing statistics
        """
        if not self.ab_testing_enabled:
            return {"enabled": False}
            
        # Calculate success rates
        for strategy, stats in self.strategy_stats.items():
            if stats["trades_executed"] > 0:
                stats["success_rate"] = stats["successful_trades"] / stats["trades_executed"]
            else:
                stats["success_rate"] = 0
                
        # Determine best strategy based on ROI
        best_strategy = max(self.strategy_stats.items(), key=lambda x: x[1]["roi"] if x[1]["trades_executed"] > 0 else -1)
        
        return {
            "enabled": True,
            "strategies": self.strategies,
            "stats": self.strategy_stats,
            "best_strategy": best_strategy[0] if best_strategy[1]["trades_executed"] > 0 else "default"
        }

if __name__ == "__main__":
    # Example usage
    validator = TradeValidator()
    
    # Example trade
    trade = {
        "trade_id": "example_trade_1",
        "token_pair": "WETH-USDC",
        "dex": "uniswap_v3",
        "network": "ethereum",
        "amount": 1000.0,
        "expected_profit": 15.0,
        "gas_price": 50.0,  # Gwei
        "gas_used": 250000,
        "gas_cost": 5.0,  # USD
        "expected_slippage": 0.01,  # 1%
        "liquidity_score": 0.8,
        "historical_success_rate": 0.75,
        "front_running_risk": 0.3,
        "network_congestion": 0.5
    }
    
    # Validate trade
    validation_result = validator.validate_trade(trade)
    
    # Print validation result
    print(json.dumps(validation_result, indent=2)) 