import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import logging
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
import json

class TradeAnalyzer:
    def __init__(self,
                 min_profit_threshold: float = 0.002,  # 0.2% minimum profit
                 lookback_window: int = 100,           # Number of trades to analyze
                 volatility_window: int = 24,          # Hours for volatility calculation
                 anomaly_contamination: float = 0.1    # Expected proportion of anomalies
                ):
        self.min_profit_threshold = min_profit_threshold
        self.lookback_window = lookback_window
        self.volatility_window = volatility_window
        self.anomaly_contamination = anomaly_contamination

        self.trade_history = []
        self.market_states = []
        self.anomaly_detector = IsolationForest(
            contamination=anomaly_contamination,
            random_state=42
        )

        self.logger = logging.getLogger(__name__)

    def analyze_trade_opportunity(self,
                                market_data: Dict,
                                trade_params: Dict) -> Dict:
        """Analyze a potential trade opportunity."""
        try:
            # Extract relevant data
            price_a = market_data['price_a']
            price_b = market_data['price_b']
            liquidity_a = market_data['liquidity_a']
            liquidity_b = market_data['liquidity_b']

            # Calculate price difference and potential profit
            price_diff = abs(price_a - price_b)
            price_ratio = max(price_a, price_b) / min(price_a, price_b)

            # Calculate maximum trade size based on liquidity
            max_trade_size = min(liquidity_a, liquidity_b) * 0.1  # 10% of available liquidity

            # Estimate transaction costs
            gas_cost = trade_params.get('estimated_gas_cost', 0)
            dex_fees = trade_params.get('dex_fees', 0.003)  # 0.3% default DEX fee

            # Calculate potential profit
            gross_profit = price_diff * max_trade_size
            total_costs = (gas_cost + (max_trade_size * dex_fees * 2))  # *2 for both trades
            net_profit = gross_profit - total_costs

            # Calculate profit ratio
            profit_ratio = net_profit / (max_trade_size * price_a)

            return {
                'price_difference': float(price_diff),
                'price_ratio': float(price_ratio),
                'max_trade_size': float(max_trade_size),
                'estimated_gross_profit': float(gross_profit),
                'estimated_costs': float(total_costs),
                'estimated_net_profit': float(net_profit),
                'profit_ratio': float(profit_ratio),
                'is_profitable': profit_ratio > self.min_profit_threshold
            }

        except Exception as e:
            self.logger.error(f"Error analyzing trade opportunity: {str(e)}")
            return {
                'error': str(e),
                'is_profitable': False
            }

    def detect_market_anomalies(self,
                              price_data: pd.DataFrame,
                              volume_data: pd.DataFrame) -> Dict:
        """Detect anomalies in market behavior."""
        try:
            # Prepare features for anomaly detection
            features = pd.DataFrame({
                'price_volatility': price_data.pct_change().rolling(self.volatility_window).std(),
                'volume_change': volume_data.pct_change(),
                'price_momentum': price_data.pct_change().rolling(12).mean(),
                'volume_momentum': volume_data.pct_change().rolling(12).mean()
            }).dropna()

            # Standardize features
            scaler = StandardScaler()
            scaled_features = scaler.fit_transform(features)

            # Detect anomalies
            anomaly_labels = self.anomaly_detector.fit_predict(scaled_features)
            anomaly_scores = self.anomaly_detector.score_samples(scaled_features)

            # Calculate anomaly statistics
            anomaly_indices = np.where(anomaly_labels == -1)[0]
            recent_anomalies = len(anomaly_indices[-24:])  # Last 24 periods

            return {
                'anomaly_detected': len(anomaly_indices) > 0,
                'recent_anomalies': int(recent_anomalies),
                'anomaly_score': float(np.mean(anomaly_scores)),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error detecting market anomalies: {str(e)}")
            return {
                'error': str(e),
                'anomaly_detected': False
            }

    def analyze_trade_performance(self, trade_result: Dict) -> Dict:
        """Analyze the performance of a completed trade."""
        try:
            # Store trade result
            self.trade_history.append({
                'timestamp': datetime.now().isoformat(),
                'profit': trade_result['profit'],
                'size': trade_result['size'],
                'duration': trade_result['duration'],
                'gas_used': trade_result['gas_used']
            })

            # Trim history to lookback window
            if len(self.trade_history) > self.lookback_window:
                self.trade_history = self.trade_history[-self.lookback_window:]

            # Calculate performance metrics
            profits = [t['profit'] for t in self.trade_history]
            sizes = [t['size'] for t in self.trade_history]
            gas_costs = [t['gas_used'] for t in self.trade_history]

            return {
                'total_trades': len(self.trade_history),
                'profitable_trades': len([p for p in profits if p > 0]),
                'average_profit': float(np.mean(profits)),
                'profit_std': float(np.std(profits)),
                'average_size': float(np.mean(sizes)),
                'average_gas': float(np.mean(gas_costs)),
                'sharpe_ratio': float(np.mean(profits) / np.std(profits)) if np.std(profits) > 0 else 0,
                'success_rate': len([p for p in profits if p > 0]) / len(profits) if profits else 0
            }

        except Exception as e:
            self.logger.error(f"Error analyzing trade performance: {str(e)}")
            return {'error': str(e)}

    def get_market_state(self) -> Dict:
        """Get current market state analysis."""
        try:
            if not self.trade_history:
                return {'status': 'No trade history available'}

            recent_trades = self.trade_history[-24:]  # Last 24 trades
            recent_profits = [t['profit'] for t in recent_trades]

            return {
                'recent_profit_mean': float(np.mean(recent_profits)),
                'recent_profit_std': float(np.std(recent_profits)),
                'recent_success_rate': len([p for p in recent_profits if p > 0]) / len(recent_profits),
                'market_trend': self._analyze_market_trend(recent_profits),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting market state: {str(e)}")
            return {'error': str(e)}

    def _analyze_market_trend(self, profits: List[float]) -> str:
        """Analyze recent market trend based on profit pattern."""
        if not profits:
            return "unknown"

        # Calculate moving averages
        window = min(12, len(profits))
        recent_ma = np.mean(profits[-window:])
        older_ma = np.mean(profits[:-window]) if len(profits) > window else recent_ma

        # Determine trend
        if recent_ma > older_ma * 1.1:
            return "improving"
        elif recent_ma < older_ma * 0.9:
            return "deteriorating"
        else:
            return "stable"

if __name__ == "__main__":
    # Example usage
    analyzer = TradeAnalyzer()

    # Simulate market data
    market_data = {
        'price_a': 1000.0,
        'price_b': 1002.0,
        'liquidity_a': 1000000,
        'liquidity_b': 900000
    }

    trade_params = {
        'estimated_gas_cost': 50,
        'dex_fees': 0.003
    }

    # Analyze opportunity
    opportunity = analyzer.analyze_trade_opportunity(market_data, trade_params)
    print("\nTrade Opportunity Analysis:")
    print(json.dumps(opportunity, indent=2))

    # Simulate price and volume data for anomaly detection
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='H')
    prices = pd.DataFrame({
        'price': np.random.normal(1000, 20, len(dates))
    }, index=dates)
    volumes = pd.DataFrame({
        'volume': np.random.normal(1000000, 200000, len(dates))
    }, index=dates)

    # Detect anomalies
    anomalies = analyzer.detect_market_anomalies(prices, volumes)
    print("\nMarket Anomaly Detection:")
    print(json.dumps(anomalies, indent=2))

    # Simulate trade result
    trade_result = {
        'profit': 0.005,
        'size': 1000,
        'duration': 30,
        'gas_used': 45
    }

    # Analyze performance
    performance = analyzer.analyze_trade_performance(trade_result)
    print("\nTrade Performance Analysis:")
    print(json.dumps(performance, indent=2))

    # Get market state
    state = analyzer.get_market_state()
    print("\nMarket State Analysis:")
    print(json.dumps(state, indent=2))
