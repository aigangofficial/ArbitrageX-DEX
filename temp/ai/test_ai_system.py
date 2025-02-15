import numpy as np
from datetime import datetime, timedelta
from strategy_optimizer import StrategyOptimizer
from trade_analyzer import TradeAnalyzer
from backtesting import Backtester, SimulationConfig
import matplotlib.pyplot as plt
import seaborn as sns
import random
import pandas as pd
from collections import defaultdict

def generate_sample_data(num_samples=720):
    """Generate sample trading data for testing."""
    data = []
    for i in range(num_samples):
        timestamp = datetime.now() - timedelta(hours=i)
        price_a = random.uniform(1000, 2000)
        price_b = price_a * (1 + random.uniform(-0.02, 0.02))
        price_diff = abs(price_a - price_b) / price_a

        # Generate more realistic market conditions
        liquidity_pool_size = random.uniform(100000, 1000000)  # Base liquidity
        if random.random() < 0.2:  # 20% chance of low liquidity
            liquidity_pool_size *= 0.1

        volatility = random.uniform(0.05, 0.15)  # Base volatility
        if random.random() < 0.3:  # 30% chance of high volatility
            volatility *= 3

        gas_price = random.uniform(20, 60)  # Base gas price
        if random.random() < 0.25:  # 25% chance of high gas
            gas_price *= 2

        volume_24h = random.uniform(500000, 5000000)  # Base volume
        if random.random() < 0.2:  # 20% chance of low volume
            volume_24h *= 0.2

        # Calculate potential profit with more realistic constraints
        base_profit = price_diff * random.uniform(5000, 10000)
        gas_cost = gas_price * 121000 * 1e-9  # Standard gas units for DEX trade

        # Apply market condition effects
        if volatility > 0.3:  # High volatility
            base_profit *= random.uniform(0.5, 1.5)  # More variance in profits
        if liquidity_pool_size < 200000:  # Low liquidity
            base_profit *= 0.7  # Reduced profits due to slippage
        if gas_price > 100:  # High gas
            base_profit *= 0.5  # Reduced profits due to costs

        potential_profit = max(0, base_profit - gas_cost)

        # Determine success based on market conditions
        success_prob = 0.85  # Base success rate
        if volatility > 0.3:
            success_prob *= 0.9  # 10% more likely to fail in high volatility
        if liquidity_pool_size < 200000:
            success_prob *= 0.85  # 15% more likely to fail in low liquidity
        if gas_price > 100:
            success_prob *= 0.92  # 8% more likely to fail in high gas

        success = potential_profit > gas_cost and random.random() < success_prob

        data.append({
            'timestamp': timestamp,
            'price_a': price_a,
            'price_b': price_b,
            'price_diff': price_diff,
            'potential_profit': potential_profit,
            'gas_cost': gas_cost,
            'gas_price': gas_price,
            'confidence': random.uniform(0.3, 1.0),
            'volume_24h': volume_24h,
            'liquidity_pool_size': liquidity_pool_size,
            'volatility': volatility,
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'trade_size': random.uniform(1000, 10000),
            'success': success,
            'failed': not success
        })

    return pd.DataFrame(data)

def test_strategy_optimizer():
    """Test the strategy optimizer component"""
    print("\n=== Testing Strategy Optimizer ===")
    optimizer = StrategyOptimizer()

    # Test with sample trade data
    sample_trade = {
        'price_difference': 0.02,
        'volume_24h': 1000000,
        'liquidity_pool_size': 500000,
        'gas_price': 50,
        'network_congestion': 0.7,
        'historical_success_rate': 0.85
    }

    # Test parameter optimization
    params = optimizer.optimize_parameters(sample_trade)
    print("\nOptimized Parameters:")
    for param, value in params.items():
        print(f"{param}: {value}")

    # Test prediction
    prob = optimizer.predict_success_probability(sample_trade)
    print(f"\nPredicted Success Probability: {prob:.2%}")

def test_trade_analyzer(historical_data):
    """Test the trade analyzer functionality."""
    print("\n=== Testing Trade Analyzer ===")

    try:
        # Create sample trades with all required fields
        trades = pd.DataFrame({
            'timestamp': historical_data['timestamp'],
            'potential_profit': historical_data['potential_profit'],
            'gas_cost': historical_data['gas_cost'],
            'gas_price': historical_data['gas_price'],
            'volume': historical_data['volume_24h'],
            'volatility': historical_data['volatility'],
            'trade_size': historical_data['trade_size'],
            'hour': historical_data['hour'],
            'day_of_week': historical_data['day_of_week'],
            'success': historical_data['success']
        })

        # Initialize and test analyzer
        analyzer = TradeAnalyzer()
        analyzer.load_trades(trades)

        # Print performance summary
        print("\nPerformance Summary:")
        print(f"Total Trades: {analyzer.metrics['total_trades']}")
        print(f"Success Rate: {analyzer.metrics['success_rate']:.2f}%")
        print(f"Total Profit: {analyzer.metrics['total_profit']:.4f} ETH")
        print(f"Average Profit: {analyzer.metrics['avg_profit']:.4f} ETH")

        # Get and print optimization recommendations
        recommendations = analyzer.get_optimization_recommendations()
        print("\nOptimization Recommendations:\n")
        for rec in recommendations:
            print(f"{rec['aspect']}:")
            print(f"Finding: {rec['finding']}")
            print(f"Suggestion: {rec['suggestion']}")
            print(f"Impact: {rec['impact']}\n")

        # Generate and save performance plots
        analyzer.plot_performance('performance_analysis.png')
        print("Performance plots saved to 'performance_analysis.png'")

    except Exception as e:
        print(f"Error during trade analysis: {str(e)}")

def test_backtester(historical_data):
    """Test the backtester with historical data."""
    print("\nTesting Backtester...")

    # Configure backtester
    backtester = Backtester(historical_data)

    # Define parameter ranges for optimization
    param_ranges = {
        'min_profit_threshold': np.linspace(0.001, 0.01, 10),
        'max_gas_price': np.linspace(20, 100, 9),
        'confidence_score': np.linspace(0.3, 0.8, 6),
        'trade_size': np.linspace(1000, 10000, 10)
    }

    # Run optimization with error handling
    try:
        # Add market conditions to historical data
        for i, row in historical_data.iterrows():
            # Determine market condition based on data
            if row['volatility'] > 0.3:
                condition = 'high_volatility'
                failure_prob = 0.10
            elif row['liquidity_pool_size'] < 200000:
                condition = 'low_liquidity'
                failure_prob = 0.15
            elif row['gas_price'] > 100:
                condition = 'high_gas'
                failure_prob = 0.08
            elif row['price_diff'] > 0.02:
                condition = 'high_opportunity'
                failure_prob = 0.05
            else:
                condition = 'normal'
                failure_prob = 0.03

            # Simulate trade failure based on market condition
            historical_data.at[i, 'failed'] = np.random.random() < failure_prob
            historical_data.at[i, 'market_condition'] = condition

            # Update success based on failure and profitability
            historical_data.at[i, 'success'] = (not historical_data.at[i, 'failed'] and
                                              historical_data.at[i, 'potential_profit'] >
                                              historical_data.at[i, 'gas_cost'])

        best_params = backtester.optimize_parameters(param_ranges)
        print(f"\nOptimal Parameters: {best_params}")

        print("\nRunning simulation with optimal parameters...")
        results = backtester.run_simulation(best_params['best_parameters'])

        print("\nSimulation Results:")
        print(f"Total Trades: {results.get('total_trades', 0)}")
        print(f"Total Profit: {results.get('total_profit', 0):.4f} ETH")
        print(f"Success Rate: {results.get('success_rate', 0):.2f}%")
        print(f"Max Drawdown: {results.get('max_drawdown', 0):.2f}%")

        if results.get('market_condition_performance'):
            print("\nPerformance by Market Condition:")
            for condition, metrics in results['market_condition_performance'].items():
                print(f"\n{condition}:")
                print(f"  Trades: {metrics['trades']}")
                print(f"  Success Rate: {metrics.get('success_rate', 0):.2f}%")
                print(f"  Average Profit: {metrics['avg_profit']:.4f} ETH")
                print(f"  Total Profit: {metrics['total_profit']:.4f} ETH")

        return results
    except Exception as e:
        print(f"Error during backtesting: {str(e)}")
        return None

def _parallel_simulation(self, params: dict) -> dict:
    """Run simulations in parallel chunks."""
    chunk_size = 100
    all_trades = []
    market_conditions = defaultdict(lambda: {'trades': 0, 'profit': 0.0, 'successful_trades': 0})

    for i in range(0, len(self.historical_data), chunk_size):
        chunk = self.historical_data.iloc[i:i + chunk_size]
        chunk_results = self._process_chunk(chunk, params)

        if chunk_results:
            all_trades.extend(chunk_results)

            # Track performance by market condition
            for trade in chunk_results:
                condition = trade.get('market_condition', 'UNKNOWN')
                market_conditions[condition]['trades'] += 1
                market_conditions[condition]['profit'] += trade.get('profit', 0)
                if trade.get('profit', 0) > 0:
                    market_conditions[condition]['successful_trades'] += 1

    if not all_trades:
        return {
            'total_trades': 0,
            'total_profit': 0.0,
            'success_rate': 0.0,
            'max_drawdown': 0.0,
            'market_condition_performance': {}
        }

    total_profit = sum(trade.get('profit', 0) for trade in all_trades)
    successful_trades = len([t for t in all_trades if t.get('profit', 0) > 0])
    success_rate = (successful_trades / len(all_trades)) * 100 if all_trades else 0

    # Calculate max drawdown
    cumulative_profits = np.cumsum([trade.get('profit', 0) for trade in all_trades])
    max_drawdown = 0
    peak = cumulative_profits[0]
    for profit in cumulative_profits:
        if profit > peak:
            peak = profit
        drawdown = (peak - profit) / peak if peak > 0 else 0
        max_drawdown = max(max_drawdown, drawdown)

    # Format market condition performance
    market_condition_performance = {}
    for condition, stats in market_conditions.items():
        if stats['trades'] > 0:
            market_condition_performance[condition] = {
                'trades': stats['trades'],
                'total_profit': stats['profit'],
                'avg_profit': stats['profit'] / stats['trades'] if stats['trades'] > 0 else 0,
                'success_rate': (stats['successful_trades'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            }

    return {
        'total_trades': len(all_trades),
        'total_profit': total_profit,
        'success_rate': success_rate,
        'max_drawdown': max_drawdown * 100,
        'market_condition_performance': market_condition_performance
    }

def main():
    """Main test function"""
    print("Generating sample data...")
    historical_data = generate_sample_data(num_samples=720)
    print(f"Generated {len(historical_data)} data points")

    # Run component tests
    test_strategy_optimizer()
    test_trade_analyzer(historical_data)
    test_backtester(historical_data)

if __name__ == "__main__":
    main()
