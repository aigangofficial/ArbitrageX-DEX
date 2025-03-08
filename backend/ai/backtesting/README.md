# ArbitrageX Backtesting Framework

This module provides a comprehensive backtesting framework for evaluating ArbitrageX trading strategies against historical market data.

## Features

- **Flexible Configuration**: Configure backtests with different strategies, time periods, and parameters
- **Multiple Strategies**: Test base, L2, Flash Loan, MEV-protected, combined, and ML-enhanced strategies
- **Performance Metrics**: Calculate key metrics like Sharpe ratio, drawdown, and win rate
- **Visualization**: Generate equity curves and trade distribution charts
- **HTML Reports**: Create detailed reports with performance analysis
- **Strategy Comparison**: Compare multiple strategies side-by-side

## Usage

### Command Line Interface

Run backtests from the command line using the `arbitragex.sh` script:

```bash
# Simple backtest of ML-enhanced strategy
./arbitragex.sh backtest --strategy=ml_enhanced --days=30

# Compare all strategies
./arbitragex.sh backtest --compare-all --days=60

# Generate a default configuration file
./arbitragex.sh backtest --strategy=l2 --generate-config

# Run a backtest with custom parameters
./arbitragex.sh backtest --strategy=flash --initial-capital=5 --trade-size=0.5
```

### Command Line Options

- `--strategy`: Trading strategy to backtest (base, l2, flash, combined, mev_protected, ml_enhanced)
- `--start-date`: Start date in YYYY-MM-DD format
- `--end-date`: End date in YYYY-MM-DD format
- `--initial-capital`: Initial capital in ETH
- `--trade-size`: Trade size in ETH
- `--token-pairs`: Token pairs to include in the backtest
- `--config`: Path to custom config file
- `--disable-l2`: Disable Layer 2 networks
- `--disable-flash`: Disable Flash Loans
- `--disable-mev`: Disable MEV protection
- `--disable-ml`: Disable ML enhancements
- `--compare-all`: Compare all strategies
- `--days`: Number of days to backtest
- `--output-dir`: Directory to save reports
- `--generate-config`: Generate a default config file

### Using as a Library

```python
from backend.ai.backtesting import Backtester, BacktestConfig
from datetime import datetime

# Create a configuration
config = BacktestConfig(
    strategy_name="ml_enhanced",
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 3, 31),
    initial_capital=10.0,
    data_source="simulated"
)

# Create backtester
backtester = Backtester(config)

# Run backtest
results = backtester.run_backtest()

# Generate report
report_file = backtester.generate_report(results)
print(f"Report generated: {report_file}")
```

## Output

The backtesting framework generates comprehensive HTML reports that include:

- **Performance Summary**: Key metrics like total return, win rate, and Sharpe ratio
- **Equity Curve**: Visualization of capital growth over time
- **Trade Distribution**: Breakdown of profits by token pair
- **Execution Method Distribution**: Analysis of trade execution methods
- **Detailed Trade History**: List of all trades executed during the backtest

## Directory Structure

- `backtester.py`: Core backtesting engine
- `backtest_cli.py`: Command-line interface
- `__init__.py`: Package initialization

Reports and metrics are saved to:
```
backend/ai/metrics/backtest/
```

Configuration files are saved to:
```
backend/ai/config/backtest/
``` 