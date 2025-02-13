import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict
from itertools import product
from typing import Dict, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from .risk_analyzer import AdaptiveRiskManager
from .trade_analyzer import TradeAnalyzer

class MarketPredictor:
    """Predicts market conditions and opportunities."""
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def predict(self, data):
        """Make predictions based on market data."""
        return 0.5  # Default prediction for now

class RiskAnalyzer:
    """Analyzes trading risks and provides risk metrics."""
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze(self, data):
        """Analyze risk metrics from trading data."""
        return {'risk_score': 0.5}  # Default risk analysis for now

class MarketCondition(Enum):
    NORMAL = "normal"
    HIGH_VOLATILITY = "high_volatility"
    LOW_LIQUIDITY = "low_liquidity"
    HIGH_GAS = "high_gas"
    HIGH_OPPORTUNITY = "high_opportunity"
    OPTIMAL = "optimal"

@dataclass
class SimulationConfig:
    initial_capital: float = 10.0
    max_trades_per_day: int = 10
    min_profit_threshold: float = 0.001
    gas_price_threshold: float = 100
    slippage_tolerance: float = 0.005
    max_drawdown_limit: float = 0.1
    risk_free_rate: float = 0.02
    confidence_level: float = 0.95

class Backtester:
    """Backtesting system for arbitrage strategies."""

    def __init__(self, historical_data=None):
        """Initialize the backtester with historical data and configuration."""
        self.historical_data = historical_data
        self.config = SimulationConfig()
        self.logger = logging.getLogger(__name__)

        # Initialize performance metrics
        self.total_trades = 0
        self.successful_trades = 0
        self.total_profit = 0
        self.trades_by_condition = defaultdict(list)

        # Load ML models
        self.logger.info("Created new models")
        self.market_predictor = MarketPredictor()
        self.risk_analyzer = RiskAnalyzer()

    def load_historical_data(self, data):
        """Load and clean historical market data for backtesting."""
        if isinstance(data, list):
            data = pd.DataFrame(data)

        self.historical_data = data.copy()

        # Clean and validate numerical columns
        numerical_columns = ['price_a', 'price_b', 'gas_price', 'liquidity_pool_size', 'volatility', 'volume_24h', 'price_diff']
        for col in numerical_columns:
            if col in self.historical_data.columns:
                # Replace inf/-inf with NaN
                self.historical_data[col] = pd.to_numeric(self.historical_data[col], errors='coerce')
                self.historical_data[col] = self.historical_data[col].replace([np.inf, -np.inf], np.nan)

                # Fill NaN with appropriate values
                if col in ['price_a', 'price_b']:
                    # Use forward fill then backward fill for prices
                    self.historical_data[col] = self.historical_data[col].fillna(method='ffill').fillna(method='bfill')
                elif col == 'gas_price':
                    # Use median gas price for missing values
                    self.historical_data[col] = self.historical_data[col].fillna(self.historical_data[col].median())
                elif col == 'liquidity_pool_size':
                    # Use minimum liquidity for missing values
                    min_liquidity = self.historical_data[col].min()
                    self.historical_data[col] = self.historical_data[col].fillna(min_liquidity if pd.notnull(min_liquidity) else 100000)
                elif col == 'volatility':
                    # Use mean volatility for missing values
                    mean_vol = self.historical_data[col].mean()
                    self.historical_data[col] = self.historical_data[col].fillna(mean_vol if pd.notnull(mean_vol) else 0.1)
                elif col == 'volume_24h':
                    # Use median volume for missing values
                    median_vol = self.historical_data[col].median()
                    self.historical_data[col] = self.historical_data[col].fillna(median_vol if pd.notnull(median_vol) else 1000000)
                elif col == 'price_diff':
                    # Calculate price difference if missing
                    if pd.isnull(self.historical_data[col]).any():
                        self.historical_data[col] = abs(self.historical_data['price_a'] - self.historical_data['price_b']) / \
                                                  ((self.historical_data['price_a'] + self.historical_data['price_b']) / 2)

        # Ensure required columns exist
        required_columns = ['timestamp', 'price_a', 'price_b', 'gas_price']
        missing_columns = [col for col in required_columns if col not in self.historical_data.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Convert timestamp to datetime if needed
        if 'timestamp' in self.historical_data.columns:
        self.historical_data['timestamp'] = pd.to_datetime(self.historical_data['timestamp'])

        # Sort by timestamp
        self.historical_data = self.historical_data.sort_values('timestamp')

        # Remove duplicates
        self.historical_data = self.historical_data.drop_duplicates(subset=['timestamp'])

        # Reset index
        self.historical_data = self.historical_data.reset_index(drop=True)

        # Add minimum values to prevent division by zero
        self.historical_data['price_a'] = self.historical_data['price_a'].clip(lower=0.000001)
        self.historical_data['price_b'] = self.historical_data['price_b'].clip(lower=0.000001)
        self.historical_data['liquidity_pool_size'] = self.historical_data['liquidity_pool_size'].clip(lower=1.0)
        self.historical_data['volume_24h'] = self.historical_data['volume_24h'].clip(lower=1.0)

        self.logger.info(f"Loaded and cleaned {len(self.historical_data)} data points")

    def _base_strategy(self, row, params):
        """Base arbitrage strategy implementation."""
        if not isinstance(row, pd.Series):
            return None

        # Extract parameters
        min_profit = params.get('min_profit_threshold', 0.002)
        max_gas = params.get('max_gas_price', 50)
        trade_size = params.get('trade_size', 1000)

        # Calculate potential profit
        price_diff = abs(row['price_a'] - row['price_b'])
        avg_price = (row['price_a'] + row['price_b']) / 2
        price_diff_pct = price_diff / avg_price

        # Only trade if price difference is significant
        if price_diff_pct < min_profit:
            return None

        # Introduce failure probabilities based on market conditions
        market_condition = self._determine_market_condition(row)
        failure_probabilities = {
            MarketCondition.HIGH_VOLATILITY: 0.10,  # 10% failure in high volatility
            MarketCondition.HIGH_GAS: 0.08,         # 8% failure in high gas
            MarketCondition.LOW_LIQUIDITY: 0.15,    # 15% failure in low liquidity
            MarketCondition.NORMAL: 0.03            # 3% failure in normal conditions
        }

        failure_prob = failure_probabilities.get(market_condition, 0.05)
        if np.random.random() < failure_prob:
            return None

        # Calculate slippage based on trade size and liquidity
        liquidity = row.get('liquidity_pool_size', trade_size * 10)  # Assume 10x buffer if not provided
        slippage_base = trade_size / liquidity  # Basic slippage calculation

        # Add volatility impact on slippage
        volatility = row.get('volatility', 0.1)
        slippage = min(0.1, slippage_base * (1 + volatility * 5))  # Cap at 10% slippage

        # Calculate potential profit in ETH with slippage
        potential_profit = (price_diff / avg_price) * trade_size * (1 - slippage)

        # Estimate gas cost with dynamic multiplier based on network congestion
        gas_units = 121000  # Base gas units
        gas_multiplier = 1.0

        if row['gas_price'] > 50:  # High gas scenario
            gas_multiplier = 1.5
        if row['gas_price'] > 100:  # Very high gas scenario
            gas_multiplier = 2.0
            return None  # Reject trade due to extreme gas costs

        gas_cost = row['gas_price'] * gas_units * 1e-9 * gas_multiplier  # Convert to ETH

        # Add DEX fees (0.3% per swap) with increased fees in high volatility
        base_fee = 0.003  # 0.3% per swap
        if market_condition == MarketCondition.HIGH_VOLATILITY:
            base_fee *= 1.5  # 50% higher fees in volatile markets

        dex_fees = trade_size * (base_fee * 2)  # Two swaps

        # Calculate net profit after all costs
        net_profit = potential_profit - gas_cost - dex_fees

        # More stringent profitability check in different market conditions
        min_profit_multiplier = 1.0
        if market_condition == MarketCondition.HIGH_VOLATILITY:
            min_profit_multiplier = 2.0  # Require 2x minimum profit in volatile markets
        elif market_condition == MarketCondition.HIGH_GAS:
            min_profit_multiplier = 1.5  # Require 1.5x minimum profit in high gas

        if net_profit <= (min_profit * min_profit_multiplier) or row['gas_price'] > max_gas:
            return None

        # Calculate confidence score with market condition impact
        confidence = min(1.0, price_diff_pct / 0.01)  # Base confidence
        if market_condition == MarketCondition.HIGH_VOLATILITY:
            confidence *= 0.7  # Reduce confidence in volatile markets
        elif market_condition == MarketCondition.LOW_LIQUIDITY:
            confidence *= 0.8  # Reduce confidence in low liquidity

        if confidence < params.get('confidence_score', 0.3):
            return None

        return {
            'trade_size': trade_size,
            'expected_profit': net_profit,
            'actual_profit': net_profit * (1 - slippage),  # Account for execution slippage
            'gas_cost': gas_cost,
            'dex_fees': dex_fees,
            'slippage': slippage,
            'confidence': confidence,
            'market_condition': market_condition
        }

    def run_simulation(self, params):
        """Run a full backtest simulation with given parameters."""
        if self.historical_data is None or len(self.historical_data) == 0:
            return {
                'total_trades': 0,
                'total_profit': 0,
                'success_rate': 0,
                'max_drawdown': 0,
                'market_condition_performance': {}
            }

        results = []
        market_conditions = defaultdict(lambda: {'trades': 0, 'profit': 0.0, 'successful_trades': 0})
        total_trades = 0
        successful_trades = 0

        for _, row in self.historical_data.iterrows():
            # Determine market condition
            condition = self._determine_market_condition(row)

            # Try to execute trade
            trade = self._base_strategy(row, params)
            if trade:
                # Apply market condition-based failure probabilities
                failure_probabilities = {
                    MarketCondition.HIGH_VOLATILITY: 0.10,  # 10% failure in high volatility
                    MarketCondition.HIGH_GAS: 0.08,         # 8% failure in high gas
                    MarketCondition.LOW_LIQUIDITY: 0.15,    # 15% failure in low liquidity
                    MarketCondition.NORMAL: 0.03            # 3% failure in normal conditions
                }

                failure_prob = failure_probabilities.get(condition, 0.05)
                trade_failed = np.random.random() < failure_prob

                if trade_failed:
                    trade['actual_profit'] = -trade['gas_cost']  # Lost gas on failed transaction
                    trade['success'] = False
                    trade['failed'] = True
                else:
                    trade['success'] = trade['actual_profit'] > 0
                    trade['failed'] = False

                trade['market_condition'] = condition
                results.append(trade)

                # Track performance by market condition
                market_conditions[condition.value]['trades'] += 1
                market_conditions[condition.value]['profit'] += trade['actual_profit']
                if trade['success']:
                    market_conditions[condition.value]['successful_trades'] += 1
                    successful_trades += 1
                total_trades += 1

        if not results:
            return {
                'total_trades': 0,
                'total_profit': 0,
                'success_rate': 0,
                'max_drawdown': 0,
                'market_condition_performance': {}
            }

        # Calculate total profit using actual profits
        total_profit = sum(r['actual_profit'] for r in results)

        # Calculate success rate based on actual successful trades
        success_rate = (successful_trades / total_trades) * 100 if total_trades > 0 else 0

        # Calculate market condition performance metrics
        market_condition_performance = {}
        for condition, stats in market_conditions.items():
            if stats['trades'] > 0:
                market_condition_performance[condition] = {
                    'trades': stats['trades'],
                    'total_profit': stats['profit'],
                    'avg_profit': stats['profit'] / stats['trades'],
                    'success_rate': (stats['successful_trades'] / stats['trades']) * 100
                }

        return {
            'total_trades': total_trades,
            'total_profit': total_profit,
            'success_rate': success_rate,
            'max_drawdown': self._calculate_max_drawdown([r['actual_profit'] for r in results]),
            'market_condition_performance': market_condition_performance
        }

    def _calculate_max_drawdown(self, profits):
        """Calculate the maximum drawdown from a list of profits using rolling window analysis."""
        if not profits:
            return 0

        # Convert profits to cumulative equity curve
        cumulative = np.cumsum(profits)
        rolling_max = np.maximum.accumulate(cumulative)
        drawdowns = np.zeros_like(cumulative)

        # Calculate drawdowns at each point
        for i in range(len(cumulative)):
            if i == 0:
                drawdowns[i] = 0
            else:
                peak = rolling_max[i]
                if peak == 0:
                    drawdowns[i] = 0
                else:
                    drawdown = (peak - cumulative[i]) / peak * 100
                    drawdowns[i] = drawdown

        # Use rolling window to smooth out noise and capture sustained drawdowns
        window_size = min(30, len(drawdowns))  # 30-period window or smaller if less data
        if window_size > 1:
            smoothed_drawdowns = pd.Series(drawdowns).rolling(window=window_size, min_periods=1).mean()
            max_dd = float(smoothed_drawdowns.max())
        else:
            max_dd = float(np.max(drawdowns))

        # Add minimum drawdown to account for trading costs and slippage
        base_drawdown = 2.0  # Minimum 2% drawdown due to trading costs
        return max(base_drawdown, max_dd)

    def optimize_parameters(self, param_ranges):
        """Find optimal parameters through grid search."""
        best_profit = float('-inf')
        best_params = None

        # Generate parameter combinations
        param_combinations = [dict(zip(param_ranges.keys(), v))
                            for v in product(*param_ranges.values())]

        for params in param_combinations:
            results = self.run_simulation(params)
            total_profit = results['total_profit']

            if total_profit > best_profit:
                best_profit = total_profit
                best_params = params

        return {
            'best_parameters': best_params,
            'expected_profit': best_profit
        }

    def _setup_logger(self) -> logging.Logger:
        """Configure logging for backtesting"""
        logger = logging.getLogger('backtester')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _analyze_market_conditions(self):
        """Analyze and label market conditions"""
        if self.historical_data.empty:
            return

        for idx, row in self.historical_data.iterrows():
            condition = self._determine_market_condition(row)
            self.market_conditions.append(condition)

        self.historical_data['market_condition'] = self.market_conditions
        condition_stats = pd.Series(self.market_conditions).value_counts()
        self.logger.info(f"Market condition distribution: {condition_stats.to_dict()}")

    def _determine_market_condition(self, row):
        """Determine market condition based on current data row."""
        if not hasattr(self, 'market_stats'):
            # Calculate market statistics once
            self.market_stats = {
                'liquidity_25th': np.percentile(self.historical_data['liquidity_pool_size'], 25),
                'volatility_75th': np.percentile(self.historical_data['volatility'], 75),
                'price_diff_75th': np.percentile(self.historical_data['price_diff'], 75),
                'gas_price_75th': np.percentile(self.historical_data['gas_price'], 75)
            }

        # Extract metrics
        liquidity = row.get('liquidity_pool_size', float('inf'))
        volatility = row.get('volatility', 0)
        price_diff = abs(row['price_a'] - row['price_b']) / ((row['price_a'] + row['price_b']) / 2)
        gas_price = row['gas_price']

        # Determine market condition based on thresholds
        if liquidity < self.market_stats['liquidity_25th']:
            return MarketCondition.LOW_LIQUIDITY
        elif volatility > self.market_stats['volatility_75th']:
            return MarketCondition.HIGH_VOLATILITY
        elif price_diff > self.market_stats['price_diff_75th']:
            return MarketCondition.HIGH_OPPORTUNITY
        elif gas_price > self.market_stats['gas_price_75th']:
            return MarketCondition.HIGH_GAS
        else:
            return MarketCondition.NORMAL

    def simulate_strategy(self,
                        strategy: Callable,
                        parallel: bool = True) -> Dict:
        """
        Simulate trading strategy with parallel execution support

        Args:
            strategy: Trading strategy function that returns trade decisions
            parallel: Whether to use parallel processing for simulation
        """
        if self.historical_data.empty:
            raise ValueError("No historical data loaded")

        self.logger.info("Starting strategy simulation...")

        if parallel:
            return self._parallel_simulation(strategy)
        else:
            return self._sequential_simulation(strategy)

    def _sequential_simulation(self, strategy: Callable) -> Dict:
        """Run simulation sequentially"""
        capital = self.config.initial_capital
        trades = []
        daily_trades = 0
        current_date = None
        max_drawdown = 0
        peak_capital = capital

        for idx, row in self.historical_data.iterrows():
            # Reset daily trade counter on new day
            if current_date != row['timestamp'].date():
                current_date = row['timestamp'].date()
                daily_trades = 0

            if daily_trades >= self.config.max_trades_per_day:
                continue

            # Get strategy decision
            trade_params = strategy(row)
            if not trade_params.get('execute', False):
                continue

            # Simulate trade execution
            trade_result = self._execute_trade(row, trade_params, capital)

            if trade_result['success']:
                capital += trade_result['actual_profit']
                trades.append(trade_result)
                daily_trades += 1

                # Update maximum drawdown
                peak_capital = max(peak_capital, capital)
                drawdown = (peak_capital - capital) / peak_capital
                max_drawdown = max(max_drawdown, drawdown)

                # Check drawdown limit
                if drawdown > self.config.max_drawdown_limit:
                    self.logger.warning(f"Maximum drawdown limit reached: {drawdown:.2%}")
                    break

        return self._calculate_simulation_results(trades, capital, max_drawdown)

    def _parallel_simulation(self, strategy: Callable) -> Dict:
        """Run simulation in parallel chunks."""
        all_trades = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            chunk_size = len(self.historical_data) // 4
            for i in range(0, len(self.historical_data), chunk_size):
                chunk = self.historical_data.iloc[i:i + chunk_size]
                futures.append(executor.submit(self._process_chunk, chunk, strategy))

            for future in futures:
                chunk_results = future.result()
                all_trades.extend(chunk_results)

        if not all_trades:
            return {
                'total_profit': 0,
                'success_rate': 0,
                'max_drawdown': 0,
                'trades_executed': 0
            }

        # Calculate metrics
        total_profit = sum(trade['expected_profit'] for trade in all_trades)
        trades_executed = len(all_trades)
        success_rate = len([t for t in all_trades if t['expected_profit'] > 0]) / trades_executed if trades_executed > 0 else 0

        # Calculate max drawdown
        cumulative_profits = np.cumsum([trade['expected_profit'] for trade in all_trades])
        peak = np.maximum.accumulate(cumulative_profits)
        drawdowns = (peak - cumulative_profits) / peak
        max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0

        return {
            'total_profit': total_profit,
            'success_rate': success_rate,
            'max_drawdown': max_drawdown,
            'trades_executed': trades_executed
        }

    def _process_chunk(self, chunk: pd.DataFrame, strategy: Callable) -> List[Dict]:
        """Process a chunk of data with the given strategy."""
        results = []
        for _, row in chunk.iterrows():
            trade_params = strategy(row)
            if trade_params is not None:  # Only process if we have trade parameters
                results.append({
                    'timestamp': row.get('timestamp', pd.Timestamp.now()),
                    'trade_size': trade_params['trade_size'],
                    'expected_profit': trade_params['expected_profit'],
                    'gas_cost': trade_params['gas_cost'],
                    'dex_fees': trade_params['dex_fees'],
                    'confidence': trade_params['confidence'],
                    'market_condition': row.get('market_condition', MarketCondition.NORMAL)
                })
        return results

    def _execute_trade(self, data: pd.Series, trade_params: Dict, current_capital: float) -> Dict:
        """Simulate execution of a single trade"""
        expected_profit = trade_params.get('expected_profit', 0)
        gas_cost = data['gas_price'] * 200000  # Estimated gas units for arbitrage

        # Apply slippage to expected profit
        slippage = np.random.uniform(0, self.config.slippage_tolerance)
        actual_profit = expected_profit * (1 - slippage)

        # Determine market condition and failure probability
        market_condition = self._determine_market_condition(data)
        failure_probabilities = {
            MarketCondition.HIGH_VOLATILITY: 0.10,  # 10% failure in high volatility
            MarketCondition.HIGH_GAS: 0.08,         # 8% failure in high gas
            MarketCondition.LOW_LIQUIDITY: 0.15,    # 15% failure in low liquidity
            MarketCondition.NORMAL: 0.03            # 3% failure in normal conditions
        }

        failure_prob = failure_probabilities.get(market_condition, 0.05)
        trade_failed = np.random.random() < failure_prob

        # Check if trade is profitable and didn't fail
        is_profitable = actual_profit > self.config.min_profit_threshold and actual_profit > gas_cost
        success = is_profitable and not trade_failed

        # If trade failed, simulate a loss
        if trade_failed:
            actual_profit = -gas_cost  # Lost gas fees on failed transaction
        elif not is_profitable:
            actual_profit = 0  # No trade executed

        # Ensure timestamp is included in trade result
        return {
            'timestamp': pd.to_datetime(data['timestamp']),  # Convert to datetime if not already
            'entry_price': data.get('price', 0),
            'gas_cost': gas_cost,
            'expected_profit': expected_profit,
            'actual_profit': actual_profit,
            'slippage': slippage,
            'success': success,
            'market_condition': market_condition,
            'volume': data.get('volume_24h', 0),
            'volatility': data.get('volatility', 0),
            'trade_size': data.get('liquidity_pool_size', 0) * 0.01,
            'failed': trade_failed
        }

    def _calculate_simulation_results(self, trades: List[Dict], final_capital: float, max_drawdown: float) -> Dict:
        """Calculate comprehensive simulation results"""
        if not trades:
            return {
                'total_trades': 0,
                'final_capital': final_capital,
                'total_profit': 0,
                'roi_percent': 0,
                'max_drawdown_percent': 0,
                'trades': [],
                'analysis': {},
                'market_condition_performance': {},
                'risk_metrics': {}
            }

        self.analyzer.load_trades(trades)
        analysis = self.analyzer.get_performance_summary()

        results = {
            'total_trades': len(trades),
            'final_capital': final_capital,
            'total_profit': final_capital - self.config.initial_capital,
            'roi_percent': ((final_capital - self.config.initial_capital) / self.config.initial_capital) * 100,
            'max_drawdown_percent': max_drawdown * 100,
            'trades': trades,
            'analysis': analysis,
            'market_condition_performance': self._analyze_condition_performance(trades),
            'risk_metrics': self._calculate_risk_metrics(trades)
        }

        self.logger.info(f"Simulation completed with {len(trades)} trades and {results['roi_percent']:.2f}% ROI")
        return results

    def _analyze_condition_performance(self, trades: List[Dict]) -> Dict:
        """Analyze performance under different market conditions"""
        condition_results = {}

        for condition in MarketCondition:
            condition_trades = [t for t in trades if t['market_condition'] == condition]
            if condition_trades:
                profits = [t['actual_profit'] for t in condition_trades]
                condition_results[condition.value] = {
                    'trade_count': len(condition_trades),
                    'total_profit': sum(profits),
                    'avg_profit': np.mean(profits),
                    'success_rate': len([t for t in condition_trades if t['success']]) / len(condition_trades)
                }

        return condition_results

    def _calculate_risk_metrics(self, trades: List[Dict]) -> Dict:
        """Calculate additional risk metrics"""
        if not trades:
            return {}

        profits = np.array([t['actual_profit'] for t in trades])

        return {
            'profit_std': np.std(profits),
            'sharpe_ratio': self._calculate_sharpe_ratio(profits),
            'sortino_ratio': self._calculate_sortino_ratio(profits),
            'var': self._calculate_var(profits),
            'expected_shortfall': self._calculate_expected_shortfall(profits)
        }

    def _calculate_sharpe_ratio(self, profits: np.ndarray) -> float:
        """Calculate Sharpe ratio"""
        if len(profits) < 2:
            return 0
        excess_returns = profits - (self.config.risk_free_rate / 365)
        return np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) != 0 else 0

    def _calculate_sortino_ratio(self, profits: np.ndarray) -> float:
        """Calculate Sortino ratio"""
        if len(profits) < 2:
            return 0
        excess_returns = profits - (self.config.risk_free_rate / 365)
        downside_returns = excess_returns[excess_returns < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0
        return np.mean(excess_returns) / downside_std if downside_std != 0 else 0

    def _calculate_var(self, profits: np.ndarray) -> float:
        """Calculate Value at Risk"""
        if len(profits) < 2:
            return 0
        return np.percentile(profits, (1 - self.config.confidence_level) * 100)

    def _calculate_expected_shortfall(self, profits: np.ndarray) -> float:
        """Calculate Expected Shortfall (CVaR)"""
        if len(profits) < 2:
            return 0
        var = self._calculate_var(profits)
        return np.mean(profits[profits <= var])

class BacktestEngine:
    def __init__(self,
                 initial_capital: float = 100000,  # $100k starting capital
                 max_trades_per_day: int = 50,     # Maximum trades per day
                 min_profit_threshold: float = 0.002,  # 0.2% minimum profit
                 max_slippage: float = 0.005,      # 0.5% max slippage
                 gas_price_multiplier: float = 1.1  # 10% gas price buffer
                ):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_trades_per_day = max_trades_per_day
        self.min_profit_threshold = min_profit_threshold
        self.max_slippage = max_slippage
        self.gas_price_multiplier = gas_price_multiplier

        self.risk_manager = AdaptiveRiskManager()
        self.trade_analyzer = TradeAnalyzer()

        self.trades = []
        self.daily_stats = []
        self.market_states = []

        self.logger = logging.getLogger(__name__)

    def run_backtest(self,
                    price_data: pd.DataFrame,
                    volume_data: pd.DataFrame,
                    gas_data: pd.DataFrame,
                    start_date: datetime,
                    end_date: datetime) -> Dict:
        """Run backtest simulation over specified period."""
        try:
            current_date = start_date
            while current_date <= end_date:
                daily_stats = self._simulate_trading_day(
                    current_date,
                    price_data.loc[current_date:current_date + timedelta(days=1)],
                    volume_data.loc[current_date:current_date + timedelta(days=1)],
                    gas_data.loc[current_date:current_date + timedelta(days=1)]
                )

                self.daily_stats.append(daily_stats)
                current_date += timedelta(days=1)

            return self._generate_backtest_report()

        except Exception as e:
            self.logger.error(f"Error in backtest simulation: {str(e)}")
            return {'error': str(e)}

    def _simulate_trading_day(self,
                            date: datetime,
                            prices: pd.DataFrame,
                            volumes: pd.DataFrame,
                            gas_prices: pd.DataFrame) -> Dict:
        """Simulate trading activity for a single day."""
        try:
            trades_today = 0
            daily_profit = 0
            opportunities = 0

            # Iterate through each hour of the day
            for hour in range(24):
                current_time = date + timedelta(hours=hour)

                # Skip if max trades reached
                if trades_today >= self.max_trades_per_day:
                    break

                # Get current market state
                market_data = self._get_market_snapshot(
                    current_time,
                    prices,
                    volumes,
                    gas_prices
                )

                # Analyze opportunity
                opportunity = self.trade_analyzer.analyze_trade_opportunity(
                    market_data,
                    {'estimated_gas_cost': market_data['gas_price'] * self.gas_price_multiplier}
                )

                if opportunity['is_profitable']:
                    opportunities += 1

                    # Validate with risk manager
                    is_valid, message = self.risk_manager.validate_trade_execution({
                        'expected_profit': opportunity['profit_ratio'],
                        'position_size': opportunity['max_trade_size'] / self.current_capital,
                        'market_impact': opportunity['price_ratio'] - 1
                    })

                    if is_valid:
                        # Execute trade
                        trade_result = self._execute_trade(opportunity, market_data)
                        daily_profit += trade_result['profit']
                        trades_today += 1

                        # Update analytics
                        self.trade_analyzer.analyze_trade_performance(trade_result)
                        self.risk_manager.update_risk_metrics({
                            'profit': trade_result['profit'],
                            'portfolio_value': self.current_capital,
                            'volatility': market_data['volatility']
                        })

            return {
                'date': date.isoformat(),
                'trades_executed': trades_today,
                'opportunities_found': opportunities,
                'daily_profit': float(daily_profit),
                'ending_capital': float(self.current_capital),
                'success_rate': trades_today / opportunities if opportunities > 0 else 0
            }

        except Exception as e:
            self.logger.error(f"Error in daily simulation: {str(e)}")
            return {
                'date': date.isoformat(),
                'error': str(e)
            }

    def _get_market_snapshot(self,
                           timestamp: datetime,
                           prices: pd.DataFrame,
                           volumes: pd.DataFrame,
                           gas_prices: pd.DataFrame) -> Dict:
        """Get market state at specific timestamp."""
        try:
            current_prices = prices.loc[timestamp]
            current_volumes = volumes.loc[timestamp]
            current_gas = gas_prices.loc[timestamp]['gas_price']

            # Calculate volatility
            price_volatility = prices.pct_change().rolling(window=24).std().loc[timestamp]

        return {
                'price_a': float(current_prices['dex_a']),
                'price_b': float(current_prices['dex_b']),
                'liquidity_a': float(current_volumes['dex_a']),
                'liquidity_b': float(current_volumes['dex_b']),
                'gas_price': float(current_gas),
                'volatility': float(price_volatility)
            }

        except Exception as e:
            self.logger.error(f"Error getting market snapshot: {str(e)}")
            return {
                'error': str(e)
            }

    def _execute_trade(self, opportunity: Dict, market_data: Dict) -> Dict:
        """Simulate trade execution with slippage and gas costs."""
        try:
            # Apply random slippage
            actual_slippage = np.random.uniform(0, self.max_slippage)
            actual_profit = opportunity['estimated_net_profit'] * (1 - actual_slippage)

            # Calculate gas cost
            gas_cost = market_data['gas_price'] * self.gas_price_multiplier

            # Update capital
            trade_profit = actual_profit - gas_cost
            self.current_capital += trade_profit

            # Record trade
            trade = {
                'timestamp': datetime.now().isoformat(),
                'profit': float(trade_profit),
                'size': float(opportunity['max_trade_size']),
                'gas_used': float(gas_cost),
                'slippage': float(actual_slippage),
                'duration': np.random.randint(15, 45)  # Random duration between 15-45 seconds
            }

            self.trades.append(trade)
            return trade

        except Exception as e:
            self.logger.error(f"Error executing trade: {str(e)}")
            return {'error': str(e)}

    def _generate_backtest_report(self) -> Dict:
        """Generate comprehensive backtest results."""
        try:
            if not self.daily_stats:
                return {'status': 'No backtest data available'}

            # Calculate overall metrics
            total_trades = sum(day['trades_executed'] for day in self.daily_stats)
            total_opportunities = sum(day['opportunities_found'] for day in self.daily_stats)
            total_profit = sum(day['daily_profit'] for day in self.daily_stats)

            # Calculate daily returns
            daily_returns = pd.Series([day['daily_profit'] for day in self.daily_stats])

            return {
                'summary': {
                    'total_trades': total_trades,
                    'total_opportunities': total_opportunities,
                    'total_profit': float(total_profit),
                    'final_capital': float(self.current_capital),
                    'return_on_capital': float((self.current_capital - self.initial_capital) / self.initial_capital),
                    'sharpe_ratio': float(daily_returns.mean() / daily_returns.std() * np.sqrt(252)) if len(daily_returns) > 1 else 0,
                    'success_rate': total_trades / total_opportunities if total_opportunities > 0 else 0
                },
                'daily_metrics': self.daily_stats,
                'risk_metrics': self.risk_manager.get_risk_report(),
                'trade_metrics': self.trade_analyzer.get_market_state()
            }

        except Exception as e:
            self.logger.error(f"Error generating backtest report: {str(e)}")
            return {'error': str(e)}

if __name__ == "__main__":
    # Example usage
    engine = BacktestEngine()

    # Generate sample data
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='H')

    # Price data for two DEXes
    prices = pd.DataFrame({
        'dex_a': np.random.normal(1000, 20, len(dates)),
        'dex_b': np.random.normal(1002, 20, len(dates))
    }, index=dates)

    # Volume data
    volumes = pd.DataFrame({
        'dex_a': np.random.normal(1000000, 200000, len(dates)),
        'dex_b': np.random.normal(900000, 180000, len(dates))
    }, index=dates)

    # Gas price data
    gas_prices = pd.DataFrame({
        'gas_price': np.random.normal(50, 10, len(dates))
    }, index=dates)

    # Run backtest
    results = engine.run_backtest(
        prices,
        volumes,
        gas_prices,
        start_date=dates[0],
        end_date=dates[-1]
    )

    # Print results
    print("\nBacktest Results:")
    print(json.dumps(results['summary'], indent=2))

    print("\nRisk Metrics:")
    print(json.dumps(results['risk_metrics'], indent=2))

    print("\nTrade Metrics:")
    print(json.dumps(results['trade_metrics'], indent=2))
