import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
import json

class AdaptiveRiskManager:
    def __init__(self,
                 max_drawdown: float = 0.20,  # 20% max drawdown threshold
                 volatility_window: int = 24,  # 24-hour lookback period
                 liquidity_safety: float = 0.30,  # 30% of observed liquidity
                 max_exposure: float = 0.10,  # 10% max capital exposure
                 min_profit_threshold: float = 0.002  # 0.2% minimum profit threshold
                ):
        self.max_drawdown = max_drawdown
        self.volatility_window = volatility_window
        self.liquidity_safety = liquidity_safety
        self.max_exposure = max_exposure
        self.min_profit_threshold = min_profit_threshold

        self.risk_metrics = {
            'current_drawdown': 0.0,
            'peak_value': 0.0,
            'consecutive_losses': 0,
            'volatility': 0.0,
            'liquidity_risk': 0.0,
            'exposure_ratio': 0.0
        }

        self.trade_history = []
        self.logger = logging.getLogger(__name__)

    def analyze_market_risk(self, prices: pd.Series, volumes: pd.Series) -> Dict:
        """Calculate various risk metrics based on market data."""
        try:
            # Calculate returns
            returns = prices.pct_change().dropna()

            # Calculate volatility
            volatility = returns.std() * np.sqrt(self.volatility_window)

            # Calculate liquidity risk
            avg_volume = volumes.mean()
            volume_volatility = volumes.std() / avg_volume if avg_volume > 0 else 1
            liquidity_risk = volume_volatility * (1 / (volumes.iloc[-1] / volumes.mean()))

            # Calculate market impact
            market_impact = 1 / (volumes.iloc[-1] * prices.iloc[-1])

            risk_score = (volatility * 0.4 +
                         liquidity_risk * 0.3 +
                         market_impact * 0.3)

            return {
                'volatility': float(volatility),
                'liquidity_risk': float(liquidity_risk),
                'market_impact': float(market_impact),
                'risk_score': float(risk_score)
            }
        except Exception as e:
            self.logger.error(f"Error in market risk analysis: {str(e)}")
            return {
                'volatility': 1.0,
                'liquidity_risk': 1.0,
                'market_impact': 1.0,
                'risk_score': 1.0
            }

    def validate_trade_execution(self, trade: Dict) -> Tuple[bool, str]:
        """Validate if a trade meets risk management criteria."""
        try:
            # Check profit threshold
            if trade['expected_profit'] < self.min_profit_threshold:
                return False, "Expected profit below minimum threshold"

            # Check position size
            if trade['position_size'] > self.max_exposure:
                return False, "Position size exceeds maximum exposure"

            # Check market impact
            if trade['market_impact'] > 0.01:  # 1% max market impact
                return False, "Market impact too high"

            # Check current drawdown
            if self.risk_metrics['current_drawdown'] > self.max_drawdown:
                return False, "Current drawdown exceeds maximum threshold"

            # Check consecutive losses
            if self.risk_metrics['consecutive_losses'] >= 3:
                return False, "Too many consecutive losses"

            return True, "Trade meets risk criteria"
        except Exception as e:
            self.logger.error(f"Error in trade validation: {str(e)}")
            return False, "Error in trade validation"

    def update_risk_metrics(self, trade_result: Dict):
        """Update risk metrics based on trade results."""
        try:
            current_value = trade_result['portfolio_value']

            # Update peak value
            if current_value > self.risk_metrics['peak_value']:
                self.risk_metrics['peak_value'] = current_value

            # Update drawdown
            if self.risk_metrics['peak_value'] > 0:
                self.risk_metrics['current_drawdown'] = (
                    self.risk_metrics['peak_value'] - current_value
                ) / self.risk_metrics['peak_value']

            # Update consecutive losses
            if trade_result['profit'] < 0:
                self.risk_metrics['consecutive_losses'] += 1
            else:
                self.risk_metrics['consecutive_losses'] = 0

            # Update volatility
            self.risk_metrics['volatility'] = trade_result['volatility']

            # Store trade result
            self.trade_history.append({
                'timestamp': datetime.now().isoformat(),
                'profit': trade_result['profit'],
                'portfolio_value': current_value
            })

            # Trim history to last 1000 trades
            if len(self.trade_history) > 1000:
                self.trade_history = self.trade_history[-1000:]

        except Exception as e:
            self.logger.error(f"Error updating risk metrics: {str(e)}")

    def get_risk_report(self) -> Dict:
        """Generate a comprehensive risk report."""
        try:
            if not self.trade_history:
                return {
                    'status': 'No trade history available',
                    'risk_metrics': self.risk_metrics
                }

            profits = [trade['profit'] for trade in self.trade_history]

            return {
                'current_drawdown': self.risk_metrics['current_drawdown'],
                'peak_value': self.risk_metrics['peak_value'],
                'consecutive_losses': self.risk_metrics['consecutive_losses'],
                'volatility': self.risk_metrics['volatility'],
                'total_trades': len(self.trade_history),
                'profitable_trades': len([p for p in profits if p > 0]),
                'average_profit': np.mean(profits) if profits else 0,
                'profit_std': np.std(profits) if profits else 0,
                'sharpe_ratio': (np.mean(profits) / np.std(profits)) if profits and np.std(profits) > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"Error generating risk report: {str(e)}")
            return {'status': 'Error generating risk report'}

if __name__ == "__main__":
    # Example usage of AdaptiveRiskManager
    import pandas as pd
    import numpy as np

    # Initialize risk manager
    risk_manager = AdaptiveRiskManager()

    # Simulate some market data
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='H')
    prices = pd.Series(np.random.normal(100, 2, len(dates)), index=dates)
    volumes = pd.Series(np.random.normal(1000000, 200000, len(dates)), index=dates)

    # Analyze market risk
    risk_analysis = risk_manager.analyze_market_risk(prices, volumes)
    print("\nMarket Risk Analysis:")
    print(json.dumps(risk_analysis, indent=2))

    # Simulate a trade
    trade = {
        'expected_profit': 0.005,  # 0.5% expected profit
        'position_size': 0.05,     # 5% of portfolio
        'market_impact': 0.005,    # 0.5% market impact
    }

    # Validate trade
    is_valid, message = risk_manager.validate_trade_execution(trade)
    print(f"\nTrade Validation:")
    print(f"Valid: {is_valid}")
    print(f"Message: {message}")

    # Update metrics with trade result
    trade_result = {
        'profit': 0.004,           # 0.4% actual profit
        'portfolio_value': 105000,  # Current portfolio value
        'volatility': risk_analysis['volatility']
    }
    risk_manager.update_risk_metrics(trade_result)

    # Get risk report
    risk_report = risk_manager.get_risk_report()
    print("\nRisk Report:")
    print(json.dumps(risk_report, indent=2))
