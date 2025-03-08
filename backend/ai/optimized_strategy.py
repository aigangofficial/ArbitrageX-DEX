#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArbitrageX Optimized Strategy

This module implements the optimized trading strategy based on the 3-month simulation analysis.
It focuses on gas optimization, improved profit thresholds, and better risk management.
"""

import os
import json
import time
import logging
import random
import datetime
from typing import Dict, List, Tuple, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("optimized_strategy.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("OptimizedStrategy")

# Constants - these will be overridden by config values when available
MIN_PROFIT_THRESHOLD = 0.05  # Minimum profit threshold in percentage
GAS_PRICE_THRESHOLD = 50     # Maximum gas price in Gwei
MAX_SLIPPAGE = 0.01          # Maximum allowed slippage
POSITION_SIZE_MIN = 0.1      # Minimum position size in ETH
POSITION_SIZE_MAX = 2.0      # Maximum position size in ETH

class GasOptimizer:
    """
    Optimizes gas usage by predicting optimal gas prices and batching transactions.
    """
    
    def __init__(self, historical_data_path: str = None, config: Dict[str, Any] = None):
        self.gas_price_history = []
        self.gas_price_predictions = {}
        self.last_update = datetime.datetime.now()
        self.update_interval = datetime.timedelta(minutes=15)
        
        # Set gas price threshold from config if available
        self.gas_price_threshold = GAS_PRICE_THRESHOLD
        if config and "gas_price_threshold" in config:
            self.gas_price_threshold = config["gas_price_threshold"]
            logger.info(f"Using configured gas price threshold: {self.gas_price_threshold} Gwei")
        
        # Load historical gas data if available
        if historical_data_path and os.path.exists(historical_data_path):
            try:
                with open(historical_data_path, 'r') as f:
                    self.gas_price_history = json.load(f)
                logger.info(f"Loaded {len(self.gas_price_history)} historical gas price records")
            except Exception as e:
                logger.error(f"Failed to load historical gas data: {e}")
    
    def update_gas_data(self, current_gas_price: float) -> None:
        """
        Update gas price history with current data.
        
        Args:
            current_gas_price: Current gas price in Gwei
        """
        now = datetime.datetime.now()
        self.gas_price_history.append({
            'timestamp': now.isoformat(),
            'gas_price': current_gas_price
        })
        
        # Trim history to keep only last 1000 records
        if len(self.gas_price_history) > 1000:
            self.gas_price_history = self.gas_price_history[-1000:]
    
    def predict_optimal_gas_price(self, hour_of_day: int = None) -> float:
        """
        Predict optimal gas price based on historical data.
        
        Args:
            hour_of_day: Hour of day (0-23) to predict for, defaults to current hour
            
        Returns:
            Predicted optimal gas price in Gwei
        """
        now = datetime.datetime.now()
        if hour_of_day is None:
            hour_of_day = now.hour
            
        # Check if prediction cache needs update
        if (now - self.last_update) > self.update_interval:
            self._update_predictions()
            self.last_update = now
            
        # Return prediction for requested hour
        if hour_of_day in self.gas_price_predictions:
            return self.gas_price_predictions[hour_of_day]
        else:
            # Default to current average if no prediction available
            return self._get_current_average()
    
    def _update_predictions(self) -> None:
        """Update hourly gas price predictions based on historical data."""
        hourly_prices = {hour: [] for hour in range(24)}
        
        # Group historical prices by hour
        for record in self.gas_price_history:
            try:
                timestamp = datetime.datetime.fromisoformat(record['timestamp'])
                hour = timestamp.hour
                hourly_prices[hour].append(record['gas_price'])
            except (ValueError, KeyError) as e:
                logger.warning(f"Invalid gas price record: {e}")
                
        # Calculate average for each hour
        for hour in hourly_prices:
            if hourly_prices[hour]:
                self.gas_price_predictions[hour] = sum(hourly_prices[hour]) / len(hourly_prices[hour])
            else:
                self.gas_price_predictions[hour] = self.gas_price_threshold
    
    def _get_current_average(self) -> float:
        """Get average gas price from recent history."""
        recent_prices = [record['gas_price'] for record in self.gas_price_history[-20:]]
        if recent_prices:
            return sum(recent_prices) / len(recent_prices)
        return self.gas_price_threshold
    
    def should_execute_trade(self, current_gas_price: float, expected_profit: float) -> bool:
        """
        Determine if a trade should be executed based on current gas price and expected profit.
        
        Args:
            current_gas_price: Current gas price in Gwei
            expected_profit: Expected profit from the trade in USD
            
        Returns:
            Boolean indicating whether to proceed with the trade
        """
        optimal_price = self.predict_optimal_gas_price()
        
        # If current price is significantly higher than optimal, consider delaying
        if current_gas_price > optimal_price * 1.5:
            logger.info(f"Gas price too high ({current_gas_price} Gwei). Optimal: {optimal_price} Gwei")
            return False
            
        # If gas price would consume more than 30% of expected profit, don't trade
        estimated_gas_cost = self._estimate_gas_cost(current_gas_price)
        if estimated_gas_cost > expected_profit * 0.3:
            logger.info(f"Gas cost ({estimated_gas_cost} USD) too high relative to expected profit ({expected_profit} USD)")
            return False
            
        return True
    
    def _estimate_gas_cost(self, gas_price: float) -> float:
        """
        Estimate gas cost in USD for a typical arbitrage transaction.
        
        Args:
            gas_price: Gas price in Gwei
            
        Returns:
            Estimated gas cost in USD
        """
        # Typical gas used for an arbitrage transaction
        typical_gas_used = 250000
        
        # Convert Gwei to ETH
        gas_price_eth = gas_price * 1e-9
        
        # Gas cost in ETH
        gas_cost_eth = typical_gas_used * gas_price_eth
        
        # Assume ETH price of $3000 (this would be dynamically fetched in production)
        eth_price_usd = 3000
        
        # Gas cost in USD
        gas_cost_usd = gas_cost_eth * eth_price_usd
        
        return gas_cost_usd

class RiskManager:
    """
    Manages trading risk through dynamic position sizing and circuit breakers.
    """
    
    def __init__(self, config_path: str = None):
        # Default configuration
        self.config = {
            "max_daily_loss": 100.0,  # Maximum daily loss in USD
            "max_consecutive_losses": 5,  # Maximum consecutive losing trades
            "position_size_base": 0.5,  # Base position size in ETH
            "position_size_scaling": 0.2,  # Scaling factor for position size adjustment
            "circuit_breaker_timeout": 3600,  # Timeout in seconds after circuit breaker triggers
            "success_rate_threshold": 0.6,  # Minimum success rate to continue trading
        }
        
        # Performance tracking
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.trade_history = []
        self.circuit_breaker_active = False
        self.circuit_breaker_end_time = 0
        
        # Load configuration if available
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                logger.info(f"Loaded risk management configuration from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load risk configuration: {e}")
    
    def reset_daily_metrics(self) -> None:
        """Reset daily performance metrics."""
        self.daily_pnl = 0.0
        logger.info("Daily risk metrics reset")
    
    def record_trade_result(self, profit_usd: float, success: bool) -> None:
        """
        Record the result of a trade for risk management purposes.
        
        Args:
            profit_usd: Profit/loss in USD
            success: Whether the trade was successful
        """
        self.daily_pnl += profit_usd
        
        trade_record = {
            'timestamp': datetime.datetime.now().isoformat(),
            'profit_usd': profit_usd,
            'success': success
        }
        self.trade_history.append(trade_record)
        
        # Trim history to last 100 trades
        if len(self.trade_history) > 100:
            self.trade_history = self.trade_history[-100:]
        
        # Update consecutive losses counter
        if not success or profit_usd < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
            
        logger.info(f"Trade recorded: profit=${profit_usd:.2f}, success={success}, consecutive_losses={self.consecutive_losses}")
    
    def calculate_position_size(self, token_pair: str, expected_profit_pct: float) -> float:
        """
        Calculate optimal position size based on historical performance and expected profit.
        
        Args:
            token_pair: The token pair being traded
            expected_profit_pct: Expected profit percentage
            
        Returns:
            Position size in ETH
        """
        base_size = self.config["position_size_base"]
        
        # Adjust based on token pair performance
        pair_performance = self._get_token_pair_performance(token_pair)
        performance_factor = 1.0
        
        if pair_performance:
            # Scale up for pairs with good performance
            if pair_performance['success_rate'] > 0.8:
                performance_factor = 1.2
            # Scale down for pairs with poor performance
            elif pair_performance['success_rate'] < 0.6:
                performance_factor = 0.8
        
        # Adjust based on expected profit
        profit_factor = min(1.5, max(0.5, expected_profit_pct / 0.01))  # Normalize around 1% profit
        
        # Calculate final position size
        position_size = base_size * performance_factor * profit_factor
        
        # Apply limits
        position_size = max(POSITION_SIZE_MIN, min(POSITION_SIZE_MAX, position_size))
        
        logger.info(f"Calculated position size: {position_size} ETH for {token_pair}")
        return position_size
    
    def _get_token_pair_performance(self, token_pair: str) -> Optional[Dict[str, float]]:
        """
        Get historical performance metrics for a specific token pair.
        
        Args:
            token_pair: The token pair to analyze
            
        Returns:
            Dictionary with performance metrics or None if insufficient data
        """
        # In a real implementation, this would query a database of historical trades
        # For this example, we'll return None to indicate no historical data
        return None
    
    def check_circuit_breakers(self) -> bool:
        """
        Check if any circuit breakers should be activated.
        
        Returns:
            True if trading should continue, False if circuit breaker is active
        """
        now = time.time()
        
        # If circuit breaker is already active, check if timeout has elapsed
        if self.circuit_breaker_active:
            if now < self.circuit_breaker_end_time:
                remaining = int(self.circuit_breaker_end_time - now)
                logger.info(f"Circuit breaker active. Trading paused for {remaining} more seconds")
                return False
            else:
                logger.info("Circuit breaker timeout elapsed. Resuming trading")
                self.circuit_breaker_active = False
        
        # Check daily loss circuit breaker
        if self.daily_pnl < -self.config["max_daily_loss"]:
            logger.warning(f"Circuit breaker triggered: Daily loss (${abs(self.daily_pnl):.2f}) exceeded threshold (${self.config['max_daily_loss']:.2f})")
            self._activate_circuit_breaker()
            return False
        
        # Check consecutive losses circuit breaker
        if self.consecutive_losses >= self.config["max_consecutive_losses"]:
            logger.warning(f"Circuit breaker triggered: {self.consecutive_losses} consecutive losses exceeded threshold ({self.config['max_consecutive_losses']})")
            self._activate_circuit_breaker()
            return False
        
        # Check success rate circuit breaker
        success_rate = self._calculate_success_rate()
        if success_rate is not None and success_rate < self.config["success_rate_threshold"]:
            logger.warning(f"Circuit breaker triggered: Success rate ({success_rate:.2%}) below threshold ({self.config['success_rate_threshold']:.2%})")
            self._activate_circuit_breaker()
            return False
        
        return True
    
    def _activate_circuit_breaker(self) -> None:
        """Activate the circuit breaker to pause trading."""
        self.circuit_breaker_active = True
        self.circuit_breaker_end_time = time.time() + self.config["circuit_breaker_timeout"]
        logger.warning(f"Circuit breaker activated. Trading paused for {self.config['circuit_breaker_timeout']} seconds")
    
    def _calculate_success_rate(self) -> Optional[float]:
        """
        Calculate the recent trade success rate.
        
        Returns:
            Success rate as a float between 0 and 1, or None if insufficient data
        """
        if len(self.trade_history) < 10:
            return None
            
        recent_trades = self.trade_history[-20:]
        successful_trades = sum(1 for trade in recent_trades if trade['success'])
        return successful_trades / len(recent_trades)

class StrategyOptimizer:
    """
    Optimizes trading strategies based on historical performance and market conditions.
    """
    
    def __init__(self):
        # Token pair specific strategies
        self.token_pair_strategies = {
            "LINK-USDC": {
                "min_profit_threshold": 0.008,  # 0.8%
                "max_slippage": 0.005,  # 0.5%
                "priority": "high"
            },
            "WETH-DAI": {
                "min_profit_threshold": 0.007,  # 0.7%
                "max_slippage": 0.008,  # 0.8%
                "priority": "medium"
            },
            "WETH-USDC": {
                "min_profit_threshold": 0.007,  # 0.7%
                "max_slippage": 0.008,  # 0.8%
                "priority": "medium"
            }
        }
        
        # DEX specific strategies
        self.dex_strategies = {
            "balancer": {
                "fee_adjustment": 0.0005,  # Additional 0.05% fee adjustment
                "priority": "high"
            },
            "curve": {
                "fee_adjustment": 0.0003,  # Additional 0.03% fee adjustment
                "priority": "high"
            },
            "sushiswap": {
                "fee_adjustment": 0.0008,  # Additional 0.08% fee adjustment
                "priority": "medium"
            }
        }
        
        # Performance tracking
        self.strategy_performance = {}
    
    def get_profit_threshold(self, token_pair: str, dex: str) -> float:
        """
        Get the minimum profit threshold for a specific token pair and DEX.
        
        Args:
            token_pair: The token pair being traded
            dex: The DEX being used
            
        Returns:
            Minimum profit threshold as a percentage
        """
        # Start with default threshold
        threshold = MIN_PROFIT_THRESHOLD
        
        # Apply token pair specific threshold if available
        if token_pair in self.token_pair_strategies:
            threshold = self.token_pair_strategies[token_pair]["min_profit_threshold"]
        
        # Adjust for DEX-specific fees if available
        if dex in self.dex_strategies:
            threshold += self.dex_strategies[dex]["fee_adjustment"]
        
        # Apply market condition adjustments (would be more sophisticated in production)
        # For now, just add a small random adjustment to simulate market conditions
        market_adjustment = random.uniform(-0.001, 0.002)
        threshold += market_adjustment
        
        logger.debug(f"Profit threshold for {token_pair} on {dex}: {threshold:.4f}")
        return threshold
    
    def get_max_slippage(self, token_pair: str) -> float:
        """
        Get the maximum allowed slippage for a specific token pair.
        
        Args:
            token_pair: The token pair being traded
            
        Returns:
            Maximum allowed slippage as a percentage
        """
        # Start with default slippage
        slippage = MAX_SLIPPAGE
        
        # Apply token pair specific slippage if available
        if token_pair in self.token_pair_strategies:
            slippage = self.token_pair_strategies[token_pair]["max_slippage"]
        
        return slippage
    
    def evaluate_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a trading opportunity and enhance it with strategy-specific parameters.
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            Enhanced opportunity with strategy parameters
        """
        token_pair = opportunity.get("token_pair", "")
        dex = opportunity.get("dex", "")
        
        # Create a copy of the opportunity to avoid modifying the original
        enhanced = opportunity.copy()
        
        # Add strategy-specific parameters
        enhanced["min_profit_threshold"] = self.get_profit_threshold(token_pair, dex)
        enhanced["max_slippage"] = self.get_max_slippage(token_pair)
        
        # Calculate priority score
        priority = self._calculate_priority(token_pair, dex)
        enhanced["priority_score"] = priority
        
        return enhanced
    
    def _calculate_priority(self, token_pair: str, dex: str) -> float:
        """
        Calculate a priority score for a trading opportunity.
        
        Args:
            token_pair: The token pair being traded
            dex: The DEX being used
            
        Returns:
            Priority score (higher is better)
        """
        score = 1.0  # Default score
        
        # Adjust based on token pair priority
        if token_pair in self.token_pair_strategies:
            if self.token_pair_strategies[token_pair]["priority"] == "high":
                score += 0.3
            elif self.token_pair_strategies[token_pair]["priority"] == "medium":
                score += 0.1
        
        # Adjust based on DEX priority
        if dex in self.dex_strategies:
            if self.dex_strategies[dex]["priority"] == "high":
                score += 0.2
            elif self.dex_strategies[dex]["priority"] == "medium":
                score += 0.1
        
        # Adjust based on historical performance (would be more sophisticated in production)
        # For now, just add a small random adjustment
        performance_adjustment = random.uniform(0, 0.1)
        score += performance_adjustment
        
        return score
    
    def update_strategy_performance(self, token_pair: str, dex: str, profit: float, success: bool) -> None:
        """
        Update performance metrics for a specific strategy.
        
        Args:
            token_pair: The token pair that was traded
            dex: The DEX that was used
            profit: The profit/loss from the trade
            success: Whether the trade was successful
        """
        strategy_key = f"{token_pair}_{dex}"
        
        if strategy_key not in self.strategy_performance:
            self.strategy_performance[strategy_key] = {
                "total_trades": 0,
                "successful_trades": 0,
                "total_profit": 0.0,
                "average_profit": 0.0
            }
        
        # Update metrics
        perf = self.strategy_performance[strategy_key]
        perf["total_trades"] += 1
        if success:
            perf["successful_trades"] += 1
        perf["total_profit"] += profit
        perf["average_profit"] = perf["total_profit"] / perf["total_trades"]
        
        # Adjust strategy parameters based on performance
        self._adjust_strategy_parameters(token_pair, dex, perf)
        
        logger.info(f"Updated performance for {strategy_key}: {perf['successful_trades']}/{perf['total_trades']} trades, ${perf['total_profit']:.2f} profit")
    
    def _adjust_strategy_parameters(self, token_pair: str, dex: str, performance: Dict[str, Any]) -> None:
        """
        Dynamically adjust strategy parameters based on performance.
        
        Args:
            token_pair: The token pair
            dex: The DEX
            performance: Performance metrics
        """
        # Only adjust if we have enough data
        if performance["total_trades"] < 10:
            return
        
        success_rate = performance["successful_trades"] / performance["total_trades"]
        avg_profit = performance["average_profit"]
        
        # Adjust token pair strategy if it exists
        if token_pair in self.token_pair_strategies:
            # If success rate is low but profit is good, increase slippage tolerance
            if success_rate < 0.7 and avg_profit > 0:
                current_slippage = self.token_pair_strategies[token_pair]["max_slippage"]
                self.token_pair_strategies[token_pair]["max_slippage"] = min(0.02, current_slippage * 1.1)
                logger.info(f"Adjusted slippage for {token_pair} to {self.token_pair_strategies[token_pair]['max_slippage']:.4f}")
            
            # If success rate is high but profit is low, increase profit threshold
            if success_rate > 0.8 and avg_profit < 0:
                current_threshold = self.token_pair_strategies[token_pair]["min_profit_threshold"]
                self.token_pair_strategies[token_pair]["min_profit_threshold"] = current_threshold * 1.05
                logger.info(f"Adjusted profit threshold for {token_pair} to {self.token_pair_strategies[token_pair]['min_profit_threshold']:.4f}")
        
        # Similar adjustments could be made for DEX strategies 

class OptimizedStrategy:
    """
    Main strategy class that integrates gas optimization, risk management, and strategy optimization.
    """
    
    def __init__(self, config_path: str = None):
        # Load configuration
        self.config = {
            "max_concurrent_trades": 3,
            "min_opportunity_score": 1.2,
            "enable_batch_execution": True,
            "enable_circuit_breakers": True,
            "enable_dynamic_position_sizing": True,
            "metrics_save_interval": 3600,  # Save metrics every hour
            "gas_price_threshold": GAS_PRICE_THRESHOLD,
            "min_profit_threshold": MIN_PROFIT_THRESHOLD,
            "max_slippage": MAX_SLIPPAGE
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                logger.info(f"Loaded strategy configuration from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load strategy configuration: {e}")
        
        # Update constants with config values (without using global)
        self.min_profit_threshold = self.config.get("min_profit_threshold", MIN_PROFIT_THRESHOLD)
        self.gas_price_threshold = self.config.get("gas_price_threshold", GAS_PRICE_THRESHOLD)
        self.max_slippage = self.config.get("max_slippage", MAX_SLIPPAGE)
        
        # Initialize components with config
        self.gas_optimizer = GasOptimizer(config=self.config)
        self.risk_manager = RiskManager(config_path)
        self.strategy_optimizer = StrategyOptimizer()
        
        # Performance tracking
        self.total_trades = 0
        self.successful_trades = 0
        self.total_profit = 0.0
        self.start_time = datetime.datetime.now()
        
        # Initialize metrics
        self.last_metrics_save = time.time()
        self.metrics_dir = "backend/ai/metrics/optimized"
        os.makedirs(self.metrics_dir, exist_ok=True)
        
        logger.info("Optimized strategy initialized")
    
    def evaluate_opportunity(self, opportunity: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluate a trading opportunity and decide whether to execute it.
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            Tuple of (should_execute, enhanced_opportunity)
        """
        # Check circuit breakers first
        if self.config["enable_circuit_breakers"] and not self.risk_manager.check_circuit_breakers():
            return False, opportunity
        
        # Enhance opportunity with strategy-specific parameters
        enhanced = self.strategy_optimizer.evaluate_opportunity(opportunity)
        
        # Extract key parameters
        token_pair = enhanced.get("token_pair", "")
        dex = enhanced.get("dex", "")
        expected_profit = enhanced.get("expected_profit", 0.0)
        expected_profit_pct = enhanced.get("expected_profit_pct", 0.0)
        gas_price = enhanced.get("gas_price", 0.0)
        priority_score = enhanced.get("priority_score", 0.0)
        min_profit_threshold = enhanced.get("min_profit_threshold", self.min_profit_threshold)
        
        # Check if profit meets threshold
        if expected_profit_pct < min_profit_threshold:
            logger.info(f"Opportunity rejected: Expected profit ({expected_profit_pct:.4f}%) below threshold ({min_profit_threshold:.4f}%)")
            return False, enhanced
        
        # Check if opportunity score meets minimum
        if priority_score < self.config["min_opportunity_score"]:
            logger.info(f"Opportunity rejected: Priority score ({priority_score:.2f}) below minimum ({self.config['min_opportunity_score']:.2f})")
            return False, enhanced
        
        # Check gas price
        if not self.gas_optimizer.should_execute_trade(gas_price, expected_profit):
            logger.info(f"Opportunity rejected: Gas price too high or expected profit too low")
            return False, enhanced
        
        # Calculate position size if dynamic sizing is enabled
        if self.config["enable_dynamic_position_sizing"]:
            position_size = self.risk_manager.calculate_position_size(token_pair, expected_profit_pct)
            enhanced["position_size"] = position_size
        
        logger.info(f"Opportunity accepted: {token_pair} on {dex}, expected profit: ${expected_profit:.2f} ({expected_profit_pct:.4f}%)")
        return True, enhanced
    
    def execute_trade(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trade based on the opportunity.
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            Dictionary with trade results
        """
        # In a real implementation, this would execute the actual trade
        # For this example, we'll simulate the trade result
        
        token_pair = opportunity.get("token_pair", "")
        dex = opportunity.get("dex", "")
        expected_profit = opportunity.get("expected_profit", 0.0)
        
        # Simulate trade execution (success rate based on priority score)
        priority_score = opportunity.get("priority_score", 1.0)
        success_probability = min(0.95, 0.6 + (priority_score - 1.0) * 0.2)
        success = random.random() < success_probability
        
        # Simulate actual profit (with some variance from expected)
        if success:
            profit_variance = random.uniform(-0.3, 0.1)  # Actual profit often lower than expected
            actual_profit = expected_profit * (1 + profit_variance)
        else:
            # Failed trades typically result in a loss
            actual_profit = -expected_profit * random.uniform(0.1, 0.5)
        
        # Record trade result
        self.total_trades += 1
        if success:
            self.successful_trades += 1
        self.total_profit += actual_profit
        
        # Update risk manager
        self.risk_manager.record_trade_result(actual_profit, success)
        
        # Update strategy optimizer
        self.strategy_optimizer.update_strategy_performance(token_pair, dex, actual_profit, success)
        
        # Update gas optimizer with current gas price
        self.gas_optimizer.update_gas_data(opportunity.get("gas_price", 50))
        
        # Save metrics if interval has elapsed
        current_time = time.time()
        if current_time - self.last_metrics_save > self.config["metrics_save_interval"]:
            self.save_metrics()
            self.last_metrics_save = current_time
        
        # Return trade result
        result = {
            "success": success,
            "profit": actual_profit,
            "token_pair": token_pair,
            "dex": dex,
            "timestamp": datetime.datetime.now().isoformat(),
            "gas_used": opportunity.get("estimated_gas", 250000),
            "gas_price": opportunity.get("gas_price", 50)
        }
        
        logger.info(f"Trade executed: {token_pair} on {dex}, success={success}, profit=${actual_profit:.2f}")
        return result
    
    def save_metrics(self) -> None:
        """Save current performance metrics to a file."""
        metrics = self.get_metrics()
        
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.metrics_dir}/optimized_metrics_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(metrics, f, indent=2)
            logger.info(f"Metrics saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        now = datetime.datetime.now()
        runtime = (now - self.start_time).total_seconds() / 3600  # Runtime in hours
        
        metrics = {
            "timestamp": now.isoformat(),
            "runtime_hours": runtime,
            "total_trades": self.total_trades,
            "successful_trades": self.successful_trades,
            "success_rate": (self.successful_trades / self.total_trades) if self.total_trades > 0 else 0,
            "total_profit_usd": self.total_profit,
            "average_profit_per_trade": (self.total_profit / self.total_trades) if self.total_trades > 0 else 0,
            "profit_per_hour": self.total_profit / runtime if runtime > 0 else 0,
            "strategy_performance": self.strategy_optimizer.strategy_performance,
            "circuit_breaker_active": self.risk_manager.circuit_breaker_active
        }
        
        return metrics


def main():
    """Main function to demonstrate the optimized strategy."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ArbitrageX Optimized Strategy")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--simulate", action="store_true", help="Run a simulation")
    parser.add_argument("--trades", type=int, default=10, help="Number of trades to simulate")
    args = parser.parse_args()
    
    # Initialize strategy
    strategy = OptimizedStrategy(args.config)
    
    if args.simulate:
        logger.info(f"Running simulation with {args.trades} trades")
        
        # Simulate trades
        for i in range(args.trades):
            # Generate a random opportunity with more favorable parameters
            opportunity = {
                "token_pair": random.choice(["LINK-USDC", "WETH-DAI", "WETH-USDC", "WBTC-USDC"]),
                "dex": random.choice(["curve", "balancer", "sushiswap"]),
                "expected_profit": random.uniform(20, 100),  # Higher profit
                "expected_profit_pct": random.uniform(0.01, 0.05),  # Higher profit percentage
                "gas_price": random.uniform(10, 25),  # Lower gas price
                "estimated_gas": random.uniform(150000, 250000)  # Lower gas usage
            }
            
            # Evaluate opportunity
            should_execute, enhanced = strategy.evaluate_opportunity(opportunity)
            
            # Execute trade if approved
            if should_execute:
                result = strategy.execute_trade(enhanced)
                logger.info(f"Trade {i+1}: {result['success']}, ${result['profit']:.2f}")
            else:
                logger.info(f"Trade {i+1}: Rejected")
        
        # Save final metrics
        strategy.save_metrics()
        
        # Print summary
        metrics = strategy.get_metrics()
        print("\nSimulation Summary:")
        print(f"Total Trades: {metrics['total_trades']}")
        print(f"Successful Trades: {metrics['successful_trades']}")
        print(f"Success Rate: {metrics['success_rate']:.2%}")
        print(f"Total Profit: ${metrics['total_profit_usd']:.2f}")
        print(f"Average Profit per Trade: ${metrics['average_profit_per_trade']:.2f}")
    else:
        logger.info("Strategy initialized. Use --simulate to run a simulation.")


if __name__ == "__main__":
    main() 