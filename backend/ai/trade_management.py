"""
ArbitrageX Trade Management Module

This module combines functionality from:
- trade_executor.py: Executes trades based on AI decisions
- trade_validator.py: Validates trades for safety and profitability
- trade_analyzer.py: Analyzes trade patterns and performance
- improved_trade_selection.py: Selects optimal trades using AI
"""

import os
import json
import logging
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any
from pathlib import Path
import tensorflow as tf
from web3 import Web3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trade_management.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("trade_management")

# Load configuration
def load_config(config_path: str) -> Dict:
    """Load configuration from a JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {e}")
        return {}

# ===== TRADE VALIDATION FUNCTIONALITY =====

class TradeValidator:
    """Validates trades for safety and profitability."""
    
    def __init__(self, config_path: str = "config/trade_validator_config.json"):
        self.config = load_config(config_path)
        self.min_profit_threshold = self.config.get("min_profit_threshold", 0.01)
        self.max_gas_price = self.config.get("max_gas_price", 100)
        self.max_slippage = self.config.get("max_slippage", 0.02)
        self.blacklisted_tokens = self.config.get("blacklisted_tokens", [])
        self.safety_checks_enabled = self.config.get("safety_checks_enabled", True)
        logger.info(f"Trade validator initialized with min profit: {self.min_profit_threshold}, max gas: {self.max_gas_price}")
    
    def validate_trade(self, trade: Dict) -> Tuple[bool, str]:
        """
        Validate a trade for safety and profitability.
        
        Args:
            trade: Dictionary containing trade details
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check for blacklisted tokens
        if trade.get("tokenA") in self.blacklisted_tokens or trade.get("tokenB") in self.blacklisted_tokens:
            return False, "Trade contains blacklisted token"
        
        # Check profitability
        expected_profit = trade.get("expectedProfit", 0)
        if expected_profit < self.min_profit_threshold:
            return False, f"Expected profit {expected_profit} below threshold {self.min_profit_threshold}"
        
        # Check gas price
        gas_price = trade.get("gasPrice", 0)
        if gas_price > self.max_gas_price:
            return False, f"Gas price {gas_price} above maximum {self.max_gas_price}"
        
        # Check slippage
        slippage = trade.get("slippage", 0)
        if slippage > self.max_slippage:
            return False, f"Slippage {slippage} above maximum {self.max_slippage}"
        
        # All checks passed
        return True, "Trade validated successfully"
    
    def test_validation(self, test_trade: Dict) -> None:
        """Run validation test on a sample trade."""
        is_valid, reason = self.validate_trade(test_trade)
        logger.info(f"Test validation result: {is_valid}, reason: {reason}")

# ===== TRADE EXECUTION FUNCTIONALITY =====

class TradeExecutor:
    """Executes trades based on AI decisions."""
    
    def __init__(self, config_path: str = "config/trade_executor_config.json"):
        self.config = load_config(config_path)
        self.validator = TradeValidator()
        self.web3_provider = self.config.get("web3_provider", "http://localhost:8545")
        self.max_concurrent_trades = self.config.get("max_concurrent_trades", 3)
        self.active_trades = 0
        self.execution_mode = self.config.get("execution_mode", "simulation")
        logger.info(f"Trade executor initialized in {self.execution_mode} mode")
    
    def connect_to_blockchain(self) -> bool:
        """Connect to the blockchain."""
        try:
            self.web3 = Web3(Web3.HTTPProvider(self.web3_provider))
            connected = self.web3.is_connected()
            logger.info(f"Blockchain connection status: {connected}")
            return connected
        except Exception as e:
            logger.error(f"Error connecting to blockchain: {e}")
            return False
    
    def execute_trade(self, trade: Dict) -> Dict:
        """
        Execute a trade after validation.
        
        Args:
            trade: Dictionary containing trade details
            
        Returns:
            Dictionary with execution results
        """
        # Validate trade first
        is_valid, reason = self.validator.validate_trade(trade)
        if not is_valid:
            logger.warning(f"Trade validation failed: {reason}")
            return {"success": False, "reason": reason}
        
        # Check if we can execute more trades
        if self.active_trades >= self.max_concurrent_trades:
            logger.warning(f"Maximum concurrent trades ({self.max_concurrent_trades}) reached")
            return {"success": False, "reason": "Maximum concurrent trades reached"}
        
        # Execute trade based on mode
        if self.execution_mode == "simulation":
            return self._execute_simulated_trade(trade)
        else:
            return self._execute_real_trade(trade)
    
    def _execute_simulated_trade(self, trade: Dict) -> Dict:
        """Execute a simulated trade."""
        logger.info(f"Simulating trade: {trade}")
        self.active_trades += 1
        
        # Simulate execution time
        time.sleep(2)
        
        # Simulate success with some randomness
        success = np.random.random() > 0.2
        
        self.active_trades -= 1
        
        if success:
            return {
                "success": True,
                "txHash": f"0x{os.urandom(32).hex()}",
                "executionTime": datetime.now().isoformat(),
                "gasUsed": np.random.randint(100000, 500000),
                "actualProfit": trade.get("expectedProfit") * np.random.uniform(0.8, 1.2)
            }
        else:
            return {
                "success": False,
                "reason": "Simulation randomly failed",
                "executionTime": datetime.now().isoformat()
            }
    
    def _execute_real_trade(self, trade: Dict) -> Dict:
        """Execute a real trade on the blockchain."""
        logger.info(f"Executing real trade: {trade}")
        self.active_trades += 1
        
        try:
            # Connect to blockchain if not already connected
            if not hasattr(self, 'web3') or not self.web3.is_connected():
                connected = self.connect_to_blockchain()
                if not connected:
                    self.active_trades -= 1
                    return {"success": False, "reason": "Failed to connect to blockchain"}
            
            # Real trade execution would go here
            # This is a placeholder for actual blockchain interaction
            logger.info("Real blockchain interaction would happen here")
            
            self.active_trades -= 1
            return {
                "success": True,
                "txHash": f"0x{os.urandom(32).hex()}",
                "executionTime": datetime.now().isoformat(),
                "gasUsed": np.random.randint(100000, 500000),
                "actualProfit": trade.get("expectedProfit") * 0.95
            }
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            self.active_trades -= 1
            return {"success": False, "reason": str(e)}

# ===== TRADE ANALYSIS FUNCTIONALITY =====

class TradeAnalyzer:
    """Analyzes trade patterns and performance."""
    
    def __init__(self, config_path: str = "config/trade_analyzer_config.json"):
        self.config = load_config(config_path)
        self.analysis_window = self.config.get("analysis_window_days", 7)
        self.min_trades_for_analysis = self.config.get("min_trades_for_analysis", 10)
        logger.info(f"Trade analyzer initialized with {self.analysis_window} day window")
    
    def load_trade_history(self, history_path: str) -> pd.DataFrame:
        """Load trade history from a file."""
        try:
            if history_path.endswith('.csv'):
                return pd.read_csv(history_path)
            elif history_path.endswith('.json'):
                with open(history_path, 'r') as f:
                    return pd.DataFrame(json.load(f))
            else:
                logger.error(f"Unsupported file format: {history_path}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading trade history: {e}")
            return pd.DataFrame()
    
    def analyze_performance(self, trades: pd.DataFrame) -> Dict:
        """
        Analyze trade performance metrics.
        
        Args:
            trades: DataFrame containing trade history
            
        Returns:
            Dictionary with performance metrics
        """
        if len(trades) < self.min_trades_for_analysis:
            logger.warning(f"Not enough trades for analysis. Need {self.min_trades_for_analysis}, got {len(trades)}")
            return {"error": "Not enough trades for analysis"}
        
        # Filter to recent trades
        cutoff_date = datetime.now() - timedelta(days=self.analysis_window)
        if 'executionTime' in trades.columns:
            trades['executionTime'] = pd.to_datetime(trades['executionTime'])
            recent_trades = trades[trades['executionTime'] >= cutoff_date]
        else:
            recent_trades = trades
        
        # Calculate metrics
        success_rate = len(recent_trades[recent_trades['success'] == True]) / len(recent_trades) if len(recent_trades) > 0 else 0
        
        profit_column = 'actualProfit' if 'actualProfit' in recent_trades.columns else 'profit'
        if profit_column in recent_trades.columns:
            total_profit = recent_trades[profit_column].sum()
            avg_profit = recent_trades[profit_column].mean()
            median_profit = recent_trades[profit_column].median()
        else:
            total_profit = avg_profit = median_profit = 0
        
        gas_column = 'gasUsed' if 'gasUsed' in recent_trades.columns else 'gas'
        if gas_column in recent_trades.columns:
            avg_gas = recent_trades[gas_column].mean()
        else:
            avg_gas = 0
        
        return {
            "period_days": self.analysis_window,
            "total_trades": len(recent_trades),
            "success_rate": success_rate,
            "total_profit": total_profit,
            "average_profit": avg_profit,
            "median_profit": median_profit,
            "average_gas": avg_gas,
            "analysis_time": datetime.now().isoformat()
        }
    
    def identify_patterns(self, trades: pd.DataFrame) -> Dict:
        """
        Identify patterns in trading activity.
        
        Args:
            trades: DataFrame containing trade history
            
        Returns:
            Dictionary with identified patterns
        """
        if len(trades) < self.min_trades_for_analysis:
            return {"error": "Not enough trades for pattern analysis"}
        
        patterns = {}
        
        # Time-based patterns
        if 'executionTime' in trades.columns:
            trades['executionTime'] = pd.to_datetime(trades['executionTime'])
            trades['hour'] = trades['executionTime'].dt.hour
            trades['day_of_week'] = trades['executionTime'].dt.dayofweek
            
            hourly_success = trades.groupby('hour')['success'].mean()
            best_hour = hourly_success.idxmax()
            worst_hour = hourly_success.idxmin()
            
            daily_success = trades.groupby('day_of_week')['success'].mean()
            best_day = daily_success.idxmax()
            worst_day = daily_success.idxmin()
            
            patterns["time_patterns"] = {
                "best_hour": int(best_hour),
                "worst_hour": int(worst_hour),
                "best_day": int(best_day),
                "worst_day": int(worst_day)
            }
        
        # Token patterns
        if 'tokenA' in trades.columns and 'tokenB' in trades.columns:
            token_pairs = trades.groupby(['tokenA', 'tokenB'])['success'].agg(['count', 'mean'])
            token_pairs = token_pairs.sort_values('count', ascending=False)
            
            most_common_pairs = []
            for idx, row in token_pairs.head(5).iterrows():
                most_common_pairs.append({
                    "tokenA": idx[0],
                    "tokenB": idx[1],
                    "count": int(row['count']),
                    "success_rate": float(row['mean'])
                })
            
            patterns["token_patterns"] = {
                "most_common_pairs": most_common_pairs
            }
        
        return patterns

# ===== TRADE SELECTION FUNCTIONALITY =====

class TradeSelector:
    """Selects optimal trades using AI."""
    
    def __init__(self, config_path: str = "config/trade_selection_config.json"):
        self.config = load_config(config_path)
        self.model_path = self.config.get("model_path", "models/trade_selection_model.h5")
        self.feature_columns = self.config.get("feature_columns", [])
        self.min_confidence = self.config.get("min_confidence", 0.7)
        self.max_trades_per_hour = self.config.get("max_trades_per_hour", 10)
        self.trades_this_hour = 0
        self.hour_reset_time = datetime.now() + timedelta(hours=1)
        
        # Load model if available
        self.model = None
        if os.path.exists(self.model_path):
            try:
                self.model = tf.keras.models.load_model(self.model_path)
                logger.info(f"Loaded trade selection model from {self.model_path}")
            except Exception as e:
                logger.error(f"Error loading model: {e}")
    
    def reset_hourly_counter(self) -> None:
        """Reset the hourly trade counter if needed."""
        if datetime.now() >= self.hour_reset_time:
            self.trades_this_hour = 0
            self.hour_reset_time = datetime.now() + timedelta(hours=1)
            logger.info("Reset hourly trade counter")
    
    def prepare_features(self, trade_opportunity: Dict) -> np.ndarray:
        """
        Prepare features for the prediction model.
        
        Args:
            trade_opportunity: Dictionary with trade opportunity details
            
        Returns:
            NumPy array of features
        """
        features = []
        
        for col in self.feature_columns:
            if col in trade_opportunity:
                features.append(trade_opportunity[col])
            else:
                features.append(0)  # Default value for missing features
        
        return np.array(features).reshape(1, -1)
    
    def select_trade(self, opportunities: List[Dict]) -> Optional[Dict]:
        """
        Select the best trade from a list of opportunities.
        
        Args:
            opportunities: List of trade opportunity dictionaries
            
        Returns:
            Selected trade or None if no good opportunities
        """
        self.reset_hourly_counter()
        
        if self.trades_this_hour >= self.max_trades_per_hour:
            logger.info(f"Maximum trades per hour ({self.max_trades_per_hour}) reached")
            return None
        
        if not opportunities:
            logger.info("No trade opportunities provided")
            return None
        
        # If no model, use simple heuristic
        if self.model is None:
            logger.info("No model available, using profit heuristic")
            best_trade = max(opportunities, key=lambda x: x.get('expectedProfit', 0))
            
            # Check if it meets minimum profit threshold
            if best_trade.get('expectedProfit', 0) > self.config.get("min_profit_threshold", 0.01):
                self.trades_this_hour += 1
                return best_trade
            else:
                return None
        
        # Use model for prediction
        best_score = 0
        best_trade = None
        
        for trade in opportunities:
            features = self.prepare_features(trade)
            
            # Predict success probability
            prediction = self.model.predict(features)[0][0]
            
            # Combine with expected profit for a score
            expected_profit = trade.get('expectedProfit', 0)
            score = prediction * expected_profit
            
            if score > best_score and prediction >= self.min_confidence:
                best_score = score
                best_trade = trade
        
        if best_trade:
            self.trades_this_hour += 1
            logger.info(f"Selected trade with score {best_score:.4f}")
        else:
            logger.info("No trade met the confidence threshold")
        
        return best_trade
    
    def batch_evaluate(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Evaluate and rank multiple trade opportunities.
        
        Args:
            opportunities: List of trade opportunity dictionaries
            
        Returns:
            List of trades with added confidence scores, sorted by score
        """
        if not opportunities:
            return []
        
        # If no model, use simple heuristic
        if self.model is None:
            for trade in opportunities:
                trade['confidence'] = 0.5  # Default confidence
                trade['score'] = trade.get('expectedProfit', 0) * 0.5
            
            return sorted(opportunities, key=lambda x: x.get('score', 0), reverse=True)
        
        # Use model for prediction
        for trade in opportunities:
            features = self.prepare_features(trade)
            
            # Predict success probability
            prediction = float(self.model.predict(features)[0][0])
            trade['confidence'] = prediction
            
            # Calculate score
            expected_profit = trade.get('expectedProfit', 0)
            trade['score'] = prediction * expected_profit
        
        # Sort by score
        return sorted(opportunities, key=lambda x: x.get('score', 0), reverse=True)

# ===== MAIN FUNCTIONALITY =====

def main():
    """Main function for testing the trade management module."""
    logger.info("Testing Trade Management Module")
    
    # Initialize components
    validator = TradeValidator()
    executor = TradeExecutor()
    analyzer = TradeAnalyzer()
    selector = TradeSelector()
    
    # Test with a sample trade
    sample_trade = {
        "tokenA": "ETH",
        "tokenB": "USDC",
        "expectedProfit": 0.05,
        "gasPrice": 50,
        "slippage": 0.01,
        "executionTime": datetime.now().isoformat()
    }
    
    # Validate
    is_valid, reason = validator.validate_trade(sample_trade)
    logger.info(f"Validation result: {is_valid}, reason: {reason}")
    
    # Execute if valid
    if is_valid:
        result = executor.execute_trade(sample_trade)
        logger.info(f"Execution result: {result}")
    
    # Generate some sample trade history
    sample_history = []
    for i in range(20):
        success = np.random.random() > 0.3
        profit = np.random.uniform(0.01, 0.1) if success else 0
        sample_history.append({
            "tokenA": np.random.choice(["ETH", "BTC", "LINK"]),
            "tokenB": np.random.choice(["USDC", "DAI", "USDT"]),
            "success": success,
            "actualProfit": profit,
            "gasUsed": np.random.randint(100000, 500000),
            "executionTime": (datetime.now() - timedelta(days=np.random.randint(0, 14))).isoformat()
        })
    
    # Analyze
    df = pd.DataFrame(sample_history)
    performance = analyzer.analyze_performance(df)
    logger.info(f"Performance analysis: {performance}")
    
    patterns = analyzer.identify_patterns(df)
    logger.info(f"Pattern analysis: {patterns}")
    
    # Generate trade opportunities
    opportunities = []
    for i in range(5):
        opportunities.append({
            "tokenA": np.random.choice(["ETH", "BTC", "LINK"]),
            "tokenB": np.random.choice(["USDC", "DAI", "USDT"]),
            "expectedProfit": np.random.uniform(0.01, 0.1),
            "gasPrice": np.random.randint(20, 100),
            "slippage": np.random.uniform(0.005, 0.02),
            "liquidity": np.random.uniform(10000, 1000000),
            "volatility": np.random.uniform(0.01, 0.05)
        })
    
    # Select best trade
    selected = selector.select_trade(opportunities)
    logger.info(f"Selected trade: {selected}")
    
    # Rank all opportunities
    ranked = selector.batch_evaluate(opportunities)
    logger.info(f"Ranked opportunities: {ranked}")

if __name__ == "__main__":
    main() 