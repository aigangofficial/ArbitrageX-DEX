# ArbitrageX Extended Simulation (3 Months)

This document explains how to run the extended 3-month simulation of the ArbitrageX bot to evaluate its maximum performance and learning capabilities over an extended period.

## Overview

The extended simulation allows you to:

1. Run a comprehensive 3-month simulation using historical or synthetic market data
2. Test the bot under maximum load conditions with high trading frequency
3. Evaluate the ML model's learning and adaptation over an extended period
4. Generate detailed reports on performance, profitability, and ML improvements
5. Identify the most profitable token pairs, networks, and DEXes

## Prerequisites

Before running the simulation, ensure you have:

1. Python 3.8+ installed with the following dependencies:
   ```bash
   pip install numpy pandas matplotlib tensorflow scikit-learn
   ```
2. At least 4GB of available RAM for running the simulation
3. Approximately 1GB of free disk space for storing metrics and results

## Configuration

The simulation uses several configuration files:

1. `backend/ai/config/learning_loop_config.json`: Configuration for the learning loop
2. `backend/ai/config/alert_config.json`: Configuration for the alerting system
3. Historical market data (optional) in `backend/ai/data/historical/market_data.json`

If historical market data is not available, the simulation will generate synthetic data that mimics real market conditions.

## Running the Simulation

To run the simulation, use the provided shell script:

```bash
./backend/ai/run_extended_simulation.sh [OPTIONS]
```

### Options:

- `--start-date DATE`: Start date for the simulation in YYYY-MM-DD format (default: 3 months ago)
- `--end-date DATE`: End date for the simulation in YYYY-MM-DD format (default: today)
- `--trades-per-day NUM`: Number of trades to simulate per day (default: 48)
- `--learning-interval HOURS`: How often to run the learning loop in hours (default: 4)
- `--data-dir DIR`: Directory with historical market data (default: backend/ai/data/historical)
- `--metrics-dir DIR`: Directory to store metrics (default: backend/ai/metrics/extended_simulation)
- `--results-dir DIR`: Directory to store results (default: backend/ai/results/extended_simulation)
- `--synthetic-data`: Force the use of synthetic data even if historical data exists

### Example:

```bash
./backend/ai/run_extended_simulation.sh --start-date 2023-01-01 --end-date 2023-03-31 --trades-per-day 96 --learning-interval 2
```

This will simulate trading from January 1, 2023, to March 31, 2023, with 96 trades per day and learning every 2 hours.

## Simulation Process

The simulation follows these steps:

1. Load historical market data or generate synthetic data
2. Initialize the monitoring system and learning loop
3. For each day in the simulation period:
   - Simulate the specified number of trades for that day
   - Run the learning loop at specified intervals
   - Track and log metrics
4. Generate a comprehensive report with detailed performance metrics

## Understanding the Results

After the simulation completes, you can analyze the following outputs:

1. **JSON Report**: `backend/ai/results/extended_simulation/simulation_report.json`
   - Contains detailed metrics on trades, profits, and ML performance
   - Includes breakdowns by network, token pair, and DEX
   - Provides monthly performance summaries

2. **Markdown Summary**: `backend/ai/results/extended_simulation/simulation_summary.md`
   - Summarizes the simulation results in a human-readable format
   - Includes tables for monthly breakdown and top performers

3. **Daily Metrics**: `backend/ai/results/extended_simulation/day_*.json`
   - Individual JSON files with detailed metrics for each simulated day

4. **Metrics Files**: `backend/ai/metrics/extended_simulation/*.json`
   - Periodic snapshots of system metrics during the simulation

## Key Metrics to Analyze

1. **Overall Performance**:
   - Total trades and success rate
   - Total profit and average profit per day
   - Gas costs and net profitability

2. **ML Performance**:
   - Initial vs. final prediction accuracy
   - Number of model updates and strategy adaptations
   - Accuracy improvement over time

3. **Token Pair Performance**:
   - Most profitable token pairs
   - Success rates by token pair
   - Volume and liquidity impacts

4. **DEX Performance**:
   - Most profitable DEXes
   - Success rates by DEX
   - Fee impacts on profitability

5. **Monthly Trends**:
   - Performance trends over the 3-month period
   - Adaptation to changing market conditions
   - Profit stability and growth

## Advanced Analysis

For advanced analysis of the simulation results, you can:

1. Use the included daily metrics to plot performance trends over time
2. Compare different token pairs and DEXes to identify optimal trading strategies
3. Analyze the ML model's learning curve and adaptation rate
4. Identify correlations between market conditions and bot performance

## Running Shorter Simulations

If you want to run a shorter simulation to test the system, you can specify a shorter date range:

```bash
./backend/ai/run_extended_simulation.sh --start-date 2023-03-01 --end-date 2023-03-07
```

This will run a one-week simulation instead of the full three months.

## Troubleshooting

If you encounter issues:

1. Check the log file (`extended_simulation.log`) for error messages
2. Ensure all required Python dependencies are installed
3. Try reducing the number of trades per day if you're experiencing memory issues
4. Verify that the historical data format is correct if using your own data

## Conclusion

The extended simulation provides valuable insights into the ArbitrageX bot's performance and learning capabilities over a long period. By analyzing the results, you can optimize the bot's strategies, identify the most profitable markets, and understand how the ML model adapts to changing conditions. 