"""
Strategy Optimizer Module for ArbitrageX

This module is responsible for optimizing arbitrage trading strategies using machine learning
and historical data analysis. It identifies optimal parameters for different market conditions
and adapts strategies based on network conditions and time-based patterns.
"""

import numpy as np
import pandas as pd
import tensorflow as tf
# Import Keras directly for newer TensorFlow versions
import keras
from keras.models import Sequential, load_model
from keras.layers import Dense, LSTM, Dropout, BatchNormalization
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import json
import os
import logging
import time
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Tuple, Optional, Union, Any
from pathlib import Path
import uuid
from dataclasses import dataclass
import argparse

# Import Web3 connector for real blockchain data
from backend.ai.web3_connector import Web3Connector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("strategy_optimizer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("StrategyOptimizer")

# Parse command line arguments
parser = argparse.ArgumentParser(description='Strategy Optimizer for ArbitrageX')
parser.add_argument('--market-data', type=str, help='Market data in JSON format')
parser.add_argument('--mainnet-fork', type=str, default='true', help='Use mainnet fork data')
parser.add_argument('--testnet', action='store_true', help='Run in testnet mode')
parser.add_argument('--version', action='store_true', help='Show version information')
args = parser.parse_args()

# Check if running in testnet mode
TESTNET_MODE = args.testnet
if TESTNET_MODE:
    logger.info("Running in TESTNET mode")

# Check if using mainnet fork data
USE_MAINNET_FORK = args.mainnet_fork.lower() == 'true'
if USE_MAINNET_FORK:
    logger.info("Using MAINNET FORK data for real blockchain interaction")

@dataclass
class Strategy:
    """Data class to represent a trading strategy with its parameters and performance metrics."""
    id: str
    name: str
    parameters: Dict[str, Any]
    performance: Dict[str, float] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.performance is None:
            self.performance = {}

@dataclass
class OptimizationResult:
    """Data class to store the results of a strategy optimization run."""
    best_strategy: Strategy
    all_strategies: List[Strategy]
    optimization_metrics: Dict[str, Any]
    optimization_time: float
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class StrategyOptimizer:
    """
    Main class for optimizing arbitrage strategies using machine learning.
    
    This class is responsible for:
    1. Loading and preprocessing historical data
    2. Training ML models for strategy optimization
    3. Evaluating strategies on different market conditions
    4. Adapting strategies based on network conditions and time patterns
    5. Predicting profitable arbitrage opportunities
    """
    
    def __init__(self, config_path: str = None, fork_config_path: str = None, testnet: bool = None, mainnet_fork: str = None):
        """
        Initialize the StrategyOptimizer with configuration.
        
        Args:
            config_path: Path to configuration file (optional)
            fork_config_path: Path to fork configuration file (optional)
            testnet: Whether to run in testnet mode (optional)
            mainnet_fork: Whether to use mainnet fork data (optional)
        """
        # Set testnet mode
        self.testnet_mode = testnet if testnet is not None else TESTNET_MODE
        if self.testnet_mode:
            logger.info("Running in TESTNET mode")
            
        # Set mainnet fork mode
        self.use_mainnet_fork = True
        if mainnet_fork is not None:
            self.use_mainnet_fork = mainnet_fork.lower() == 'true'
        else:
            self.use_mainnet_fork = USE_MAINNET_FORK
            
        if self.use_mainnet_fork:
            logger.info("Using MAINNET FORK data for real blockchain interaction")
            
        self.config = self._load_config(config_path)
        self.models = {}
        self.scalers = {}
        self.strategies = []
        self.current_strategy = None
        self.historical_data = None
        
        # Initialize Web3 connector if fork_config_path is provided
        self.web3_connector = None
        self.use_web3 = False
        if fork_config_path:
            try:
                self.web3_connector = Web3Connector(fork_config_path)
                self.use_web3 = self.web3_connector.is_connected()
                if self.use_web3:
                    logger.info("Web3 connector initialized and connected to Hardhat fork")
                else:
                    logger.warning("Web3 connector initialized but not connected to Hardhat fork")
            except Exception as e:
                logger.error(f"Error initializing Web3 connector: {e}")
        
        # Load default strategy
        self.default_strategy = self._create_default_strategy()
        
        logger.info("StrategyOptimizer initialized")
    
    def _create_default_strategy(self) -> Strategy:
        """
        Create a default strategy with reasonable parameters.
        
        Returns:
            Default strategy
        """
        return Strategy(
            id=str(uuid.uuid4()),
            name="Default Strategy",
            parameters={
                "min_profit_threshold_usd": 50.0,
                "max_gas_price_gwei": 100,
                "slippage_tolerance_bps": 50,  # 0.5%
                "execution_timeout_ms": 5000,
                "min_confidence_threshold": 0.7,
                "preferred_dex": "uniswap_v3",
                "preferred_network": "ethereum",
                "gas_price_multiplier": 1.1,
                "execution_priority": "medium"
            }
        )
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """
        Load configuration from a JSON file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            "models_dir": "models/",
            "data_path": "data/",
            "min_confidence_threshold": 0.7,
            "max_gas_price_gwei": 100,
            "min_profit_threshold_usd": 50,
            "networks": ["ethereum", "arbitrum", "polygon", "optimism", "base"],
            "update_interval_seconds": 3600,
            "feature_importance_threshold": 0.05,
            "max_slippage_bps": 100,  # 1%
            "time_window_seconds": 300,
            "backtest_days": 30
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
                    logger.info(f"Configuration loaded from {config_path}")
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        return default_config
    
    def predict_opportunity(self, opportunity: Dict) -> Dict:
        """
        Predict if an arbitrage opportunity is profitable using the trained model.
        
        Args:
            opportunity: Dictionary containing opportunity details
                - token_in: Address of input token
                - token_out: Address of output token
                - amount: Amount of input token (in wei)
                - router: Address of the router to use
                
        Returns:
            Dictionary with prediction results:
                - is_profitable: Boolean indicating if opportunity is profitable
                - confidence: Confidence score (0-1)
                - estimated_profit_usd: Estimated profit in USD
                - execution_time_ms: Estimated execution time in milliseconds
                - gas_cost_usd: Estimated gas cost in USD
        """
        start_time = time.time()
        
        # Check if we should use Web3 for real blockchain data
        if self.use_web3 and self.web3_connector:
            # Get real blockchain data for the prediction
            try:
                # Get token balances
                token_in_balance = self.web3_connector.get_token_balance(
                    opportunity["token_in"], 
                    self.web3_connector.web3.eth.accounts[0]
                )
                
                # Get pool information
                pool_info = self.web3_connector.get_uniswap_pool_info(
                    opportunity["token_in"],
                    opportunity["token_out"]
                )
                
                # Get flash loan availability
                flash_loan_available = self.web3_connector.get_aave_flash_loan_availability(
                    opportunity["token_in"]
                )
                
                # Add real blockchain data to the opportunity
                opportunity["token_in_balance"] = token_in_balance
                opportunity["pool_info"] = pool_info
                opportunity["flash_loan_available"] = flash_loan_available
                
                logger.info("Using real blockchain data from Hardhat fork for prediction")
            except Exception as e:
                logger.error(f"Error getting blockchain data: {e}")
        
        # Get the best strategy for the current market conditions
        strategy = self._get_best_strategy()
        
        # Extract features from the opportunity
        features = self._extract_features(opportunity)
        
        # If we have a trained model, use it for prediction
        if "opportunity_classifier" in self.models:
            model = self.models["opportunity_classifier"]
            scaler = self.scalers.get("opportunity_classifier")
            
            # Scale features if a scaler is available
            if scaler:
                features_scaled = scaler.transform([features])
            else:
                features_scaled = np.array([features])
            
            # Make prediction
            prediction = model.predict(features_scaled)[0][0]
            confidence = float(prediction)
            
            # Determine if profitable based on confidence threshold
            is_profitable = confidence >= strategy.parameters["min_confidence_threshold"]
        else:
            # If no model is available, use a simple heuristic
            estimated_profit_usd = self._estimate_profit(opportunity)
            gas_cost_usd = self._estimate_gas_cost(opportunity)
            net_profit_usd = estimated_profit_usd - gas_cost_usd
            
            is_profitable = net_profit_usd > strategy.parameters["min_profit_threshold_usd"]
            confidence = 0.5 + (net_profit_usd / 100) if is_profitable else 0.5 - (abs(net_profit_usd) / 100)
            confidence = max(0.01, min(0.99, confidence))  # Clamp between 0.01 and 0.99
        
        # Calculate estimated profit and gas cost
        estimated_profit_usd = self._estimate_profit(opportunity)
        gas_cost_usd = self._estimate_gas_cost(opportunity)
        net_profit_usd = estimated_profit_usd - gas_cost_usd
        
        # Calculate execution time
        execution_time_ms = time.time() - start_time
        execution_time_ms *= 1000  # Convert to milliseconds
        
        # Prepare result
        result = {
            "is_profitable": is_profitable,
            "confidence": confidence,
            "estimated_profit_usd": estimated_profit_usd,
            "gas_cost_usd": gas_cost_usd,
            "net_profit_usd": net_profit_usd,
            "execution_time_ms": execution_time_ms,
            "strategy_recommendations": {
                "optimal_gas_price_gwei": strategy.parameters["max_gas_price_gwei"],
                "recommended_dex": strategy.parameters["preferred_dex"],
                "slippage_tolerance_percent": strategy.parameters["slippage_tolerance_bps"] / 100,
                "execution_priority": strategy.parameters["execution_priority"]
            }
        }
        
        return result
    
    def _load_strategies(self) -> List[Strategy]:
        """Load existing strategies from disk."""
        strategies_file = Path(self.config["data_path"]) / "strategies.json"
        if not os.path.exists(strategies_file):
            # Create a default strategy
            default_strategy = Strategy(
                id=str(uuid.uuid4()),
                name="default_strategy",
                parameters={
                    "entry_threshold": 0.5,
                    "exit_threshold": 0.3,
                    "max_slippage": 0.5,
                    "gas_price_multiplier": 1.1,
                    "min_profit_threshold": 0.2,
                    "max_trade_size": 10.0,
                    "time_window": 60,  # seconds
                    "risk_tolerance": 0.5,
                    "use_flash_loans": True,
                    "max_hops": 3,
                    "dex_priority": ["uniswap", "sushiswap", "curve"],
                    "network_priority": ["ethereum", "arbitrum", "polygon", "optimism"]
                },
                created_at=datetime.now()
            )
            return [default_strategy]
        
        try:
            with open(strategies_file, 'r') as f:
                strategies_data = json.load(f)
                
            strategies = []
            for strategy_data in strategies_data:
                strategy = Strategy(
                    id=strategy_data['id'],
                    name=strategy_data['name'],
                    parameters=strategy_data['parameters'],
                    performance=strategy_data.get('performance'),
                    created_at=datetime.fromisoformat(strategy_data['created_at']) if 'created_at' in strategy_data else None
                )
                strategies.append(strategy)
                
            return strategies
        except Exception as e:
            logger.error(f"Error loading strategies: {e}")
            return []
    
    def _save_strategies(self):
        """Save strategies to disk."""
        strategies_file = Path(self.config["data_path"]) / "strategies.json"
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(strategies_file), exist_ok=True)
            
            # Convert strategies to JSON-serializable format
            strategies_data = []
            for strategy in self.strategies:
                strategy_dict = {
                    "id": strategy.id,
                    "name": strategy.name,
                    "parameters": strategy.parameters,
                    "performance": strategy.performance,
                    "created_at": strategy.created_at.isoformat() if strategy.created_at else None
                }
                strategies_data.append(strategy_dict)
                
            with open(strategies_file, 'w') as f:
                json.dump(strategies_data, f, indent=2)
                
            logger.info(f"Saved {len(self.strategies)} strategies to {strategies_file}")
        except Exception as e:
            logger.error(f"Error saving strategies: {e}")
    
    def load_historical_data(self, file_path: str) -> pd.DataFrame:
        """
        Load historical arbitrage data for strategy optimization.
        
        Args:
            file_path: Path to the CSV file containing historical data
            
        Returns:
            DataFrame containing historical data
        """
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Loaded historical data from {file_path}: {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            # Generate synthetic data for demonstration
            return self._generate_synthetic_data()
    
    def _generate_synthetic_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """Generate synthetic data for demonstration purposes."""
        logger.warning("Generating synthetic data for demonstration")
        
        np.random.seed(42)
        
        # Generate timestamps for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        timestamps = [start_date + timedelta(minutes=i*30) for i in range(n_samples)]
        
        # Generate synthetic features
        data = {
            'timestamp': timestamps,
            'gas_price': np.random.gamma(2, 20, n_samples),  # Gas prices in gwei
            'eth_price': np.random.normal(2000, 100, n_samples),  # ETH price in USD
            'network_congestion': np.random.uniform(0, 1, n_samples),  # Network congestion level
            'trade_volume_24h': np.random.lognormal(10, 1, n_samples),  # 24h trading volume
            'liquidity_pool_size': np.random.lognormal(15, 1, n_samples),  # Liquidity pool size
            'price_volatility': np.random.gamma(2, 0.01, n_samples),  # Price volatility
            'competitor_activity': np.random.poisson(5, n_samples),  # Number of competitor trades
            'dex_1_price': np.random.normal(1, 0.01, n_samples),  # Price on DEX 1
            'dex_2_price': np.random.normal(1.005, 0.01, n_samples),  # Price on DEX 2
            'dex_3_price': np.random.normal(0.995, 0.01, n_samples),  # Price on DEX 3
            'network': np.random.choice(['ethereum', 'arbitrum', 'polygon', 'optimism'], n_samples),
            'token_pair': np.random.choice(['ETH-USDC', 'ETH-USDT', 'WBTC-ETH', 'LINK-ETH'], n_samples),
        }
        
        # Calculate potential profit
        price_diffs = np.maximum(
            np.maximum(data['dex_1_price'], data['dex_2_price']) - 
            np.minimum(data['dex_1_price'], data['dex_2_price']),
            np.maximum(data['dex_2_price'], data['dex_3_price']) - 
            np.minimum(data['dex_2_price'], data['dex_3_price'])
        )
        
        # Calculate gas cost in token terms
        gas_cost = data['gas_price'] * 150000 / 1e9 / data['eth_price']
        
        # Calculate net profit
        data['potential_profit'] = price_diffs - gas_cost
        data['profitable'] = data['potential_profit'] > 0
        
        # Add some noise to make it more realistic
        data['potential_profit'] = np.where(
            data['profitable'],
            data['potential_profit'] * np.random.uniform(0.8, 1.2, n_samples),
            data['potential_profit'] * np.random.uniform(0.5, 1.5, n_samples)
        )
        
        return pd.DataFrame(data)
    
    def optimize_strategy(self, 
                         historical_data: pd.DataFrame,
                         optimization_metric: str = "profit",
                         risk_tolerance: float = 0.5,
                         n_iterations: int = 100) -> OptimizationResult:
        """
        Optimize trading strategy parameters based on historical data.
        
        Args:
            historical_data: DataFrame containing historical arbitrage data
            optimization_metric: Metric to optimize for (profit, win_rate, sharpe)
            risk_tolerance: Risk tolerance level (0-1)
            n_iterations: Number of optimization iterations
            
        Returns:
            OptimizationResult containing the best strategy and optimization metrics
        """
        logger.info(f"Starting strategy optimization with {n_iterations} iterations")
        start_time = datetime.now()
        
        # Initialize list to store all evaluated strategies
        evaluated_strategies = []
        
        # Start with the best existing strategy as a baseline
        best_strategy = self._get_best_strategy()
        best_performance = self._evaluate_strategy(best_strategy, historical_data)
        best_strategy.performance = best_performance
        evaluated_strategies.append(best_strategy)
        
        # Optimization loop
        for i in range(n_iterations):
            # Generate a new strategy with random variations
            new_strategy = self._generate_strategy_variation(best_strategy, i/n_iterations)
            
            # Evaluate the new strategy
            performance = self._evaluate_strategy(new_strategy, historical_data)
            new_strategy.performance = performance
            evaluated_strategies.append(new_strategy)
            
            # Update best strategy if this one is better
            if self._is_better_strategy(new_strategy, best_strategy, optimization_metric, risk_tolerance):
                best_strategy = new_strategy
                best_performance = performance
                logger.info(f"Iteration {i+1}/{n_iterations}: Found better strategy with {optimization_metric}={best_performance.get(optimization_metric, 0):.4f}")
        
        # Calculate optimization time
        optimization_time = (datetime.now() - start_time).total_seconds()
        
        # Create optimization result
        result = OptimizationResult(
            best_strategy=best_strategy,
            all_strategies=evaluated_strategies,
            optimization_metrics={
                "iterations": n_iterations,
                "optimization_metric": optimization_metric,
                "risk_tolerance": risk_tolerance,
                "best_performance": best_performance
            },
            optimization_time=optimization_time
        )
        
        # Add the best strategy to our collection if it's better than existing ones
        if not any(s.id == best_strategy.id for s in self.strategies):
            self.strategies.append(best_strategy)
            self._save_strategies()
        
        logger.info(f"Strategy optimization completed in {optimization_time:.2f} seconds")
        return result
    
    def _get_best_strategy(self) -> Strategy:
        """Get the best performing strategy from existing strategies."""
        if not self.strategies or len(self.strategies) == 1:
            return self.default_strategy
        
        # Find strategies with performance data
        strategies_with_performance = [s for s in self.strategies if s.performance and "profit" in s.performance]
        
        if not strategies_with_performance:
            return self.default_strategy
        
        # Sort by profit and return the best one
        return sorted(strategies_with_performance, key=lambda s: s.performance.get("profit", 0), reverse=True)[0]
    
    def _generate_strategy_variation(self, base_strategy: Strategy, exploration_factor: float) -> Strategy:
        """
        Generate a new strategy by varying parameters of the base strategy.
        
        Args:
            base_strategy: The strategy to base the new one on
            exploration_factor: Factor controlling exploration vs exploitation (0-1)
            
        Returns:
            A new Strategy object with varied parameters
        """
        # Copy base strategy parameters
        new_params = base_strategy.parameters.copy()
        
        # Adjust numerical parameters with random variations
        for param in ["entry_threshold", "exit_threshold", "max_slippage", 
                     "gas_price_multiplier", "min_profit_threshold", "max_trade_size",
                     "time_window", "risk_tolerance"]:
            if param in new_params:
                # Scale exploration based on the exploration factor
                variation = np.random.normal(0, 0.1 * exploration_factor)
                new_value = new_params[param] * (1 + variation)
                
                # Ensure parameters stay within reasonable bounds
                if param in ["entry_threshold", "exit_threshold", "max_slippage", "risk_tolerance"]:
                    new_value = max(0.01, min(0.99, new_value))
                elif param in ["gas_price_multiplier"]:
                    new_value = max(1.0, min(2.0, new_value))
                elif param in ["min_profit_threshold"]:
                    new_value = max(0.01, min(1.0, new_value))
                elif param in ["max_trade_size"]:
                    new_value = max(0.1, min(100.0, new_value))
                elif param in ["time_window"]:
                    new_value = max(10, min(300, new_value))
                
                new_params[param] = new_value
        
        # Occasionally change boolean parameters
        if "use_flash_loans" in new_params and np.random.random() < 0.1 * exploration_factor:
            new_params["use_flash_loans"] = not new_params["use_flash_loans"]
        
        # Occasionally change max_hops
        if "max_hops" in new_params and np.random.random() < 0.1 * exploration_factor:
            new_params["max_hops"] = max(1, min(5, new_params["max_hops"] + np.random.choice([-1, 0, 1])))
        
        # Occasionally shuffle priority lists
        if "dex_priority" in new_params and np.random.random() < 0.2 * exploration_factor:
            dex_list = new_params["dex_priority"].copy()
            np.random.shuffle(dex_list)
            new_params["dex_priority"] = dex_list
        
        if "network_priority" in new_params and np.random.random() < 0.2 * exploration_factor:
            network_list = new_params["network_priority"].copy()
            np.random.shuffle(network_list)
            new_params["network_priority"] = network_list
        
        # Create new strategy
        return Strategy(
            id=str(uuid.uuid4()),
            name=f"variant_of_{base_strategy.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            parameters=new_params
        )
    
    def _evaluate_strategy(self, strategy: Strategy, historical_data: pd.DataFrame) -> Dict[str, float]:
        """
        Evaluate a strategy on historical data.
        
        Args:
            strategy: Strategy to evaluate
            historical_data: DataFrame containing historical data
            
        Returns:
            Dictionary of performance metrics
        """
        # Extract strategy parameters
        params = strategy.parameters
        entry_threshold = params.get("entry_threshold", 0.5)
        exit_threshold = params.get("exit_threshold", 0.3)
        max_slippage = params.get("max_slippage", 0.5)
        gas_price_multiplier = params.get("gas_price_multiplier", 1.1)
        min_profit_threshold = params.get("min_profit_threshold", 0.2)
        
        # Apply strategy rules to historical data
        # In a real implementation, this would be a more sophisticated simulation
        
        # Calculate adjusted gas cost based on the multiplier
        adjusted_gas_cost = historical_data['gas_price'] * gas_price_multiplier * 150000 / 1e9 / historical_data['eth_price']
        
        # Calculate adjusted profit after slippage
        adjusted_profit = historical_data['potential_profit'] * (1 - np.random.uniform(0, max_slippage, len(historical_data)))
        
        # Determine which trades would be executed based on strategy parameters
        execute_trade = (
            (adjusted_profit > min_profit_threshold) &  # Profit threshold
            (historical_data['price_volatility'] < entry_threshold) &  # Entry based on volatility
            (historical_data['network_congestion'] < 1 - exit_threshold)  # Exit based on congestion
        )
        
        # Calculate performance metrics
        if execute_trade.sum() > 0:
            executed_profits = adjusted_profit[execute_trade] - adjusted_gas_cost[execute_trade]
            
            total_profit = executed_profits.sum()
            win_rate = (executed_profits > 0).mean()
            avg_profit_per_trade = executed_profits.mean()
            
            # Calculate Sharpe ratio (risk-adjusted return)
            if executed_profits.std() > 0:
                sharpe_ratio = executed_profits.mean() / executed_profits.std() * np.sqrt(252)  # Annualized
            else:
                sharpe_ratio = 0
                
            # Calculate max drawdown
            cumulative_returns = (1 + executed_profits).cumprod()
            max_drawdown = 1 - (cumulative_returns / cumulative_returns.cummax()).min()
            
            # Calculate trade frequency
            trade_frequency = execute_trade.sum() / len(historical_data)

            return {
                "profit": total_profit,
                "win_rate": win_rate,
                "avg_profit_per_trade": avg_profit_per_trade,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "trade_frequency": trade_frequency,
                "trades_executed": execute_trade.sum(),
                "total_opportunities": len(historical_data)
            }
        else:
            return {
                "profit": 0,
                "win_rate": 0,
                "avg_profit_per_trade": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 1,
                "trade_frequency": 0,
                "trades_executed": 0,
                "total_opportunities": len(historical_data)
            }
    
    def _is_better_strategy(self, 
                           strategy1: Strategy, 
                           strategy2: Strategy, 
                           metric: str = "profit",
                           risk_tolerance: float = 0.5) -> bool:
        """
        Determine if strategy1 is better than strategy2 based on the given metric and risk tolerance.
        
        Args:
            strategy1: First strategy to compare
            strategy2: Second strategy to compare
            metric: Metric to use for comparison
            risk_tolerance: Risk tolerance level (0-1)
            
        Returns:
            True if strategy1 is better than strategy2, False otherwise
        """
        if not strategy1.performance or not strategy2.performance:
            return False
        
        # Get primary metric values
        metric1 = strategy1.performance.get(metric, 0)
        metric2 = strategy2.performance.get(metric, 0)
        
        # If optimizing for profit or Sharpe ratio, higher is better
        if metric in ["profit", "sharpe_ratio", "win_rate"]:
            # If metrics are very close, consider risk
            if abs(metric1 - metric2) / max(abs(metric2), 1e-10) < 0.05:
                # For similar performance, prefer the strategy with lower drawdown if risk tolerance is low
                if risk_tolerance < 0.5:
                    return strategy1.performance.get("max_drawdown", 1) < strategy2.performance.get("max_drawdown", 1)
                # For high risk tolerance, prefer the strategy with higher trade frequency
                else:
                    return strategy1.performance.get("trade_frequency", 0) > strategy2.performance.get("trade_frequency", 0)
            return metric1 > metric2
        
        # If optimizing for drawdown, lower is better
        elif metric == "max_drawdown":
            return metric1 < metric2
        
        # Default comparison
        return metric1 > metric2
    
    def get_best_strategy_for_market(self, 
                                    market_conditions: Dict[str, Any],
                                    optimization_metric: str = "profit") -> Strategy:
        """
        Get the best strategy for the current market conditions.
        
        Args:
            market_conditions: Dictionary of current market conditions
            optimization_metric: Metric to use for selecting the best strategy
            
        Returns:
            The best strategy for the current market conditions
        """
        if not self.strategies or len(self.strategies) <= 1:
            return self.default_strategy
        
        # Filter strategies with performance data
        valid_strategies = [s for s in self.strategies if s.performance and optimization_metric in s.performance]
        
        if not valid_strategies:
            return self.default_strategy
        
        # Sort by the optimization metric
        if optimization_metric in ["profit", "sharpe_ratio", "win_rate"]:
            sorted_strategies = sorted(valid_strategies, 
                                      key=lambda s: s.performance.get(optimization_metric, 0), 
                                      reverse=True)
        else:
            sorted_strategies = sorted(valid_strategies, 
                                      key=lambda s: s.performance.get(optimization_metric, 0))
        
        return sorted_strategies[0]
    
    def visualize_optimization_results(self, result: OptimizationResult, save_path: Optional[str] = None):
        """
        Visualize the results of strategy optimization.
        
        Args:
            result: OptimizationResult from optimize_strategy
            save_path: Path to save the visualization, if None, display only
        """
        if not result or not result.all_strategies:
            logger.warning("No optimization results to visualize")
            return
        
        # Extract performance metrics for all strategies
        profits = [s.performance.get("profit", 0) for s in result.all_strategies]
        win_rates = [s.performance.get("win_rate", 0) for s in result.all_strategies]
        sharpe_ratios = [s.performance.get("sharpe_ratio", 0) for s in result.all_strategies]
        drawdowns = [s.performance.get("max_drawdown", 1) for s in result.all_strategies]
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle("Strategy Optimization Results", fontsize=16)
        
        # Plot profit distribution
        axes[0, 0].hist(profits, bins=20, alpha=0.7)
        axes[0, 0].axvline(result.best_strategy.performance.get("profit", 0), color='r', linestyle='--', 
                         label=f'Best Strategy: {result.best_strategy.performance.get("profit", 0):.4f}')
        axes[0, 0].set_title("Profit Distribution")
        axes[0, 0].set_xlabel("Total Profit")
        axes[0, 0].set_ylabel("Frequency")
        axes[0, 0].legend()
        
        # Plot win rate distribution
        axes[0, 1].hist(win_rates, bins=20, alpha=0.7)
        axes[0, 1].axvline(result.best_strategy.performance.get("win_rate", 0), color='r', linestyle='--',
                         label=f'Best Strategy: {result.best_strategy.performance.get("win_rate", 0):.4f}')
        axes[0, 1].set_title("Win Rate Distribution")
        axes[0, 1].set_xlabel("Win Rate")
        axes[0, 1].set_ylabel("Frequency")
        axes[0, 1].legend()
        
        # Plot Sharpe ratio distribution
        axes[1, 0].hist(sharpe_ratios, bins=20, alpha=0.7)
        axes[1, 0].axvline(result.best_strategy.performance.get("sharpe_ratio", 0), color='r', linestyle='--',
                         label=f'Best Strategy: {result.best_strategy.performance.get("sharpe_ratio", 0):.4f}')
        axes[1, 0].set_title("Sharpe Ratio Distribution")
        axes[1, 0].set_xlabel("Sharpe Ratio")
        axes[1, 0].set_ylabel("Frequency")
        axes[1, 0].legend()
        
        # Plot max drawdown distribution
        axes[1, 1].hist(drawdowns, bins=20, alpha=0.7)
        axes[1, 1].axvline(result.best_strategy.performance.get("max_drawdown", 1), color='r', linestyle='--',
                         label=f'Best Strategy: {result.best_strategy.performance.get("max_drawdown", 1):.4f}')
        axes[1, 1].set_title("Max Drawdown Distribution")
        axes[1, 1].set_xlabel("Max Drawdown")
        axes[1, 1].set_ylabel("Frequency")
        axes[1, 1].legend()
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Saved optimization visualization to {save_path}")
        else:
            plt.show()

    def _extract_features(self, opportunity: Dict) -> List[float]:
        """
        Extract features from an opportunity for model prediction.
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            List of features
        """
        # Example features (in a real implementation, these would be more sophisticated)
        features = [
            float(opportunity.get("amount", 0)) / 1e18,  # Normalize amount
            float(opportunity.get("gas_price", 50)),  # Gas price in Gwei
            float(opportunity.get("slippage", 0.5)),  # Slippage in percentage
            float(opportunity.get("token_in_balance", 0)) / 1e18 if "token_in_balance" in opportunity else 0,
            float(opportunity.get("flash_loan_available", 0)) / 1e18 if "flash_loan_available" in opportunity else 0
        ]
        
        return features
    
    def _estimate_profit(self, opportunity: Dict) -> float:
        """
        Estimate the profit for an opportunity in USD.
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            Estimated profit in USD
        """
        # In a real implementation, this would use real blockchain data
        # and sophisticated price calculations
        
        # For now, use a simple random value for demonstration
        if "estimated_profit_usd" in opportunity:
            return float(opportunity["estimated_profit_usd"])
        
        # Generate a random profit between $1 and $20
        return round(np.random.uniform(1, 20), 2)
    
    def _estimate_gas_cost(self, opportunity: Dict) -> float:
        """
        Estimate the gas cost for an opportunity in USD.
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            Estimated gas cost in USD
        """
        # In a real implementation, this would use real gas price data
        # and estimate the gas usage based on the operation
        
        # For now, use a simple random value for demonstration
        if "gas_cost_usd" in opportunity:
            return float(opportunity["gas_cost_usd"])
        
        # Generate a random gas cost between $5 and $15
        return round(np.random.uniform(5, 15), 2)
    
    def execute_opportunity(self, opportunity: Dict) -> Dict:
        """
        Execute an arbitrage opportunity on the blockchain.
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            Dictionary with execution results
        """
        if not self.use_web3 or not self.web3_connector:
            logger.warning("Web3 connector not available, cannot execute opportunity")
        return {
                "success": False,
                "error": "Web3 connector not available",
                "simulated": True
            }
        
        try:
            # Execute the arbitrage using the Web3 connector
            result = self.web3_connector.execute_arbitrage(opportunity)
            
            # Log the result
            if result["success"]:
                logger.info(f"Arbitrage executed successfully: {result}")
            else:
                logger.error(f"Arbitrage execution failed: {result}")
            
            return result
        except Exception as e:
            logger.error(f"Error executing arbitrage: {e}")
            return {
                "success": False,
                "error": str(e),
                "simulated": False
            }

# Example usage
if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="ArbitrageX Strategy Optimizer")
    parser.add_argument("--testnet", action="store_true", help="Run in testnet mode")
    parser.add_argument("--data", type=str, default="backend/ai/data/arbitrage_history.csv", help="Path to historical data CSV file")
    parser.add_argument("--iterations", type=int, default=50, help="Number of optimization iterations")
    parser.add_argument("--risk", type=float, default=0.5, help="Risk tolerance (0-1)")
    parser.add_argument("--metric", type=str, default="profit", help="Optimization metric (profit, sharpe_ratio, win_rate)")
    parser.add_argument("--visualize", action="store_true", help="Visualize results")
    args = parser.parse_args()
    
    # Initialize the strategy optimizer
    optimizer = StrategyOptimizer()
    
    # Print mode
    if args.testnet:
        print("Running in TESTNET mode")
    else:
        print("Running in MAINNET mode")
    
    # Load historical data (or generate synthetic data if file doesn't exist)
    historical_data = optimizer.load_historical_data(args.data)
    
    # Optimize strategy
    result = optimizer.optimize_strategy(
        historical_data=historical_data,
        optimization_metric=args.metric,
        risk_tolerance=args.risk,
        n_iterations=args.iterations
    )
    
    # Print best strategy
    best_strategy = result.best_strategy
    print(f"Best Strategy: {best_strategy.name}")
    print(f"Parameters: {json.dumps(best_strategy.parameters, indent=2)}")
    print(f"Performance: {json.dumps(best_strategy.performance, indent=2)}")
    
    # Visualize results if requested
    if args.visualize:
        optimizer.visualize_optimization_results(result, save_path="backend/ai/data/strategy_optimization_results.png")
    
    # Get best strategy for current market conditions
    current_market = {
        "gas_price": 25,  # gwei
        "network_congestion": 0.3,
        "price_volatility": 0.02,
        "eth_price": 2100
    }
    
    recommended_strategy = optimizer.get_best_strategy_for_market(current_market)
    print(f"\nRecommended strategy for current market: {recommended_strategy.name}")
    print(f"Expected profit: {recommended_strategy.performance.get('profit', 0):.4f}")
    print(f"Win rate: {recommended_strategy.performance.get('win_rate', 0):.4f}")
