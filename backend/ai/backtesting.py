import pandas as pd
import numpy as np
from typing import List, Dict, Callable
from datetime import datetime, timedelta
from .strategy_optimizer import StrategyOptimizer
from .trade_analyzer import TradeAnalyzer

class Backtester:
    def __init__(self):
        self.optimizer = StrategyOptimizer()
        self.analyzer = TradeAnalyzer()
        self.results = {}

    def load_historical_data(self, data: List[Dict]):
        """Load historical market data for backtesting"""
        self.historical_data = pd.DataFrame(data)
        self.historical_data['timestamp'] = pd.to_datetime(self.historical_data['timestamp'])
        self.historical_data.sort_values('timestamp', inplace=True)

    def simulate_strategy(self, 
                        strategy: Callable,
                        initial_capital: float = 10.0,
                        max_trades_per_day: int = 10,
                        min_profit_threshold: float = 0.001) -> Dict:
        """
        Simulate trading strategy on historical data
        
        Args:
            strategy: Trading strategy function that returns trade decisions
            initial_capital: Starting capital in ETH
            max_trades_per_day: Maximum number of trades allowed per day
            min_profit_threshold: Minimum profit required to execute trade
        """
        if self.historical_data.empty:
            raise ValueError("No historical data loaded")

        capital = initial_capital
        trades = []
        daily_trades = 0
        current_date = None

        for _, row in self.historical_data.iterrows():
            # Reset daily trade counter on new day
            if current_date != row['timestamp'].date():
                current_date = row['timestamp'].date()
                daily_trades = 0

            if daily_trades >= max_trades_per_day:
                continue

            # Get strategy decision
            trade_params = strategy(row)
            if not trade_params['execute']:
                continue

            # Calculate expected profit and costs
            expected_profit = trade_params['expected_profit']
            gas_cost = row['gas_price'] * 200000  # Estimated gas units for arbitrage

            # Execute trade if profitable
            if expected_profit > min_profit_threshold and expected_profit > gas_cost:
                trade_result = {
                    'timestamp': row['timestamp'],
                    'entry_price': row['price'],
                    'gas_cost': gas_cost,
                    'expected_profit': expected_profit,
                    'actual_profit': expected_profit - gas_cost,
                    'success': True
                }
                
                capital += trade_result['actual_profit']
                trades.append(trade_result)
                daily_trades += 1

        # Calculate performance metrics
        self.results = {
            'total_trades': len(trades),
            'final_capital': capital,
            'total_profit': capital - initial_capital,
            'roi_percent': ((capital - initial_capital) / initial_capital) * 100,
            'trades': trades
        }

        # Analyze trades
        self.analyzer.load_trades(trades)
        self.results['analysis'] = self.analyzer.get_performance_summary()
        self.results['recommendations'] = self.analyzer.get_optimization_recommendations()

        return self.results

    def optimize_parameters(self, param_ranges: Dict) -> Dict:
        """Find optimal strategy parameters through grid search"""
        best_profit = float('-inf')
        best_params = {}

        # Generate parameter combinations
        param_combinations = self._generate_param_combinations(param_ranges)

        for params in param_combinations:
            # Create strategy with current parameters
            strategy = lambda x, p=params: self._base_strategy(x, p)
            
            # Run simulation
            results = self.simulate_strategy(strategy)
            
            # Update best parameters if current profit is higher
            if results['total_profit'] > best_profit:
                best_profit = results['total_profit']
                best_params = params

        return {
            'best_parameters': best_params,
            'expected_profit': best_profit
        }

    def _base_strategy(self, data: pd.Series, params: Dict) -> Dict:
        """Basic arbitrage strategy implementation"""
        price_diff = abs(data['dex1_price'] - data['dex2_price'])
        price_threshold = params.get('price_threshold', 0.01)
        
        return {
            'execute': price_diff > price_threshold,
            'expected_profit': price_diff if price_diff > price_threshold else 0
        }

    def _generate_param_combinations(self, param_ranges: Dict) -> List[Dict]:
        """Generate all combinations of parameters for grid search"""
        param_combinations = [{}]
        
        for param_name, param_range in param_ranges.items():
            new_combinations = []
            for value in param_range:
                for combo in param_combinations:
                    new_combo = combo.copy()
                    new_combo[param_name] = value
                    new_combinations.append(new_combo)
            param_combinations = new_combinations

        return param_combinations

if __name__ == "__main__":
    # Example usage
    backtester = Backtester()
    
    # Sample historical data
    historical_data = [
        {
            'timestamp': datetime.now() - timedelta(hours=i),
            'price': 1000 + np.random.normal(0, 10),
            'dex1_price': 1000 + np.random.normal(0, 5),
            'dex2_price': 1000 + np.random.normal(0, 5),
            'gas_price': 50 + np.random.normal(0, 5)
        }
        for i in range(24 * 7)  # One week of hourly data
    ]
    
    backtester.load_historical_data(historical_data)
    
    # Define parameter ranges for optimization
    param_ranges = {
        'price_threshold': [0.005, 0.01, 0.015, 0.02],
        'max_gas_price': [40, 50, 60, 70]
    }
    
    # Find optimal parameters
    optimal_params = backtester.optimize_parameters(param_ranges)
    print("Optimal Parameters:", optimal_params)
    
    # Run simulation with optimal parameters
    strategy = lambda x: backtester._base_strategy(x, optimal_params['best_parameters'])
    results = backtester.simulate_strategy(strategy)
    print("Simulation Results:", results) 