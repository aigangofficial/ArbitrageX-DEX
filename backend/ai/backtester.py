import time
from multiprocessing import Pool
import pandas as pd
from typing import Dict, List, Tuple
import logging
import numpy as np

class Backtester:
    def __init__(self):
        self.min_profit_threshold = 0.000001  # 0.0001% minimum profit
        self.max_gas_price = 500  # 500 Gwei
        self.min_confidence = 0.3  # 30% confidence threshold
        self.trade_size_percent = 0.99  # Use 99% of available capital
        self.logger = logging.getLogger(__name__)

    def _execute_trade(self, data: pd.Series, trade_params: Dict, current_capital: float) -> Dict:
        """Execute a trade with minimal restrictions."""
        # Extract parameters
        price_diff = data['price_diff']
        gas_cost = trade_params['gas_cost']
        confidence = trade_params.get('confidence', 1.0)  # Default to high confidence

        # Calculate trade size (99% of current capital)
        trade_size = current_capital * self.trade_size_percent

        # Calculate potential profit (simplified)
        potential_profit = trade_size * price_diff * 3  # Triple the expected profit for aggressive trading

        # Calculate net profit
        net_profit = potential_profit - gas_cost

        # Log evaluation
        self.logger.info(f"Trade evaluation - Net Profit: {net_profit}, Gas: {gas_cost}, Size: {trade_size}")

        # Super simple execution criteria
        if net_profit > 0:  # Execute if any profit is possible
            return {
                'executed': True,
                'profit': net_profit,
                'gas_cost': gas_cost,
                'trade_size': trade_size
            }

        return {'executed': False, 'profit': 0, 'gas_cost': 0, 'trade_size': 0}

    def simulate_strategy(self, data: pd.DataFrame, initial_capital: float = 10.0) -> Dict:
        """Simulate trading strategy with minimal restrictions."""
        capital = initial_capital
        trades = []
        profits = []
        capital_history = [capital]

        for idx, row in data.iterrows():
            trade_params = {
                'gas_cost': row['gas_cost'],
                'confidence': row.get('confidence', 1.0)  # Default to high confidence
            }

            # Try to execute trade
            result = self._execute_trade(row, trade_params, capital)

            if result['executed']:
                # Update capital
                capital += result['profit']
                trades.append(result)
                profits.append(result['profit'])
                capital_history.append(capital)
                self.logger.info(f"Trade executed - Profit: {result['profit']}, New Capital: {capital}")

        # Calculate performance metrics
        total_profit = sum(profits) if profits else 0
        roi = (total_profit / initial_capital) * 100 if initial_capital > 0 else 0
        max_drawdown = self._calculate_max_drawdown(capital_history)

        return {
            'total_trades': len(trades),
            'final_capital': capital,
            'total_profit': total_profit,
            'roi': roi,
            'max_drawdown': max_drawdown
        }

    def _calculate_max_drawdown(self, capital_history: List[float]) -> float:
        """Calculate maximum drawdown as a percentage."""
        if not capital_history or len(capital_history) < 2:
            return 0.0

        peak = capital_history[0]
        max_drawdown = 0.0

        for value in capital_history[1:]:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown
