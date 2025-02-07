import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

class TradeAnalyzer:
    def __init__(self):
        self.trades_df = pd.DataFrame()
        self.metrics = {}

    def load_trades(self, trades: List[Dict]):
        """Load trade data into analyzer"""
        self.trades_df = pd.DataFrame(trades)
        self.trades_df['timestamp'] = pd.to_datetime(self.trades_df['timestamp'])
        self._calculate_metrics()

    def _calculate_metrics(self):
        """Calculate key performance metrics"""
        if self.trades_df.empty:
            return

        self.metrics = {
            'total_trades': len(self.trades_df),
            'successful_trades': len(self.trades_df[self.trades_df['success'] == True]),
            'total_profit': self.trades_df['profit'].sum(),
            'average_profit': self.trades_df['profit'].mean(),
            'success_rate': len(self.trades_df[self.trades_df['success'] == True]) / len(self.trades_df),
            'avg_gas_cost': self.trades_df['gas_cost'].mean(),
            'profit_factor': self._calculate_profit_factor()
        }

    def _calculate_profit_factor(self) -> float:
        """Calculate ratio of gross profits to gross losses"""
        profits = self.trades_df[self.trades_df['profit'] > 0]['profit'].sum()
        losses = abs(self.trades_df[self.trades_df['profit'] < 0]['profit'].sum())
        return profits / losses if losses != 0 else float('inf')

    def get_performance_summary(self) -> Dict:
        """Get summary of trading performance"""
        return self.metrics

    def analyze_market_conditions(self) -> Dict:
        """Analyze market conditions impact on trade success"""
        if self.trades_df.empty:
            return {}

        conditions = {
            'high_volatility': self.trades_df['volatility'] > self.trades_df['volatility'].mean(),
            'high_volume': self.trades_df['volume'] > self.trades_df['volume'].mean(),
            'high_gas': self.trades_df['gas_price'] > self.trades_df['gas_price'].mean()
        }

        analysis = {}
        for condition, mask in conditions.items():
            success_rate = self.trades_df[mask]['success'].mean()
            avg_profit = self.trades_df[mask]['profit'].mean()
            analysis[condition] = {
                'success_rate': success_rate,
                'avg_profit': avg_profit
            }

        return analysis

    def plot_performance(self, save_path: str = None):
        """Generate performance visualization"""
        if self.trades_df.empty:
            return

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # Cumulative profit over time
        cumulative_profit = self.trades_df.sort_values('timestamp')['profit'].cumsum()
        ax1.plot(self.trades_df['timestamp'], cumulative_profit)
        ax1.set_title('Cumulative Profit Over Time')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Profit')

        # Success rate by hour
        self.trades_df['hour'] = self.trades_df['timestamp'].dt.hour
        hourly_success = self.trades_df.groupby('hour')['success'].mean()
        ax2.bar(hourly_success.index, hourly_success.values)
        ax2.set_title('Success Rate by Hour')
        ax2.set_xlabel('Hour of Day')
        ax2.set_ylabel('Success Rate')

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path)
        plt.close()

    def get_optimization_recommendations(self) -> List[Dict]:
        """Generate recommendations for strategy optimization"""
        if self.trades_df.empty:
            return []

        recommendations = []

        # Analyze gas price impact
        gas_correlation = self.trades_df['gas_price'].corr(self.trades_df['success'])
        if abs(gas_correlation) > 0.3:
            recommendations.append({
                'aspect': 'gas_price',
                'finding': 'Strong correlation with success rate',
                'suggestion': 'Adjust gas price strategy',
                'correlation': gas_correlation
            })

        # Analyze time-based patterns
        self.trades_df['hour'] = self.trades_df['timestamp'].dt.hour
        best_hour = self.trades_df.groupby('hour')['success'].mean().idxmax()
        recommendations.append({
            'aspect': 'timing',
            'finding': f'Best performance in hour {best_hour}',
            'suggestion': 'Focus trading during optimal hours',
            'best_hour': int(best_hour)
        })

        return recommendations

if __name__ == "__main__":
    # Example usage
    analyzer = TradeAnalyzer()
    
    # Sample trade data
    sample_trades = [
        {
            'timestamp': datetime.now() - timedelta(hours=i),
            'success': i % 2 == 0,
            'profit': 0.1 if i % 2 == 0 else -0.05,
            'gas_cost': 0.02,
            'gas_price': 50 + i,
            'volume': 1000000,
            'volatility': 0.1
        }
        for i in range(24)
    ]
    
    analyzer.load_trades(sample_trades)
    print("Performance Summary:", analyzer.get_performance_summary())
    print("Market Condition Analysis:", analyzer.analyze_market_conditions())
    print("Optimization Recommendations:", analyzer.get_optimization_recommendations()) 