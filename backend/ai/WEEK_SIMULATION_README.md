# ArbitrageX Week-Long Simulation on Forked Mainnet

This document explains how to run a week-long simulation of the ArbitrageX bot on a forked mainnet to evaluate its performance, learning capabilities, and adaptation speed.

## Overview

The week-long simulation allows you to:

1. Test the bot's performance on real market data from a forked mainnet
2. Evaluate the ML model's learning capabilities and adaptation speed
3. Track comprehensive metrics including trades, profits, and system resources
4. Generate detailed reports for analysis

The simulation accelerates time, compressing a week of trading into a few hours while maintaining realistic market conditions.

## Prerequisites

Before running the simulation, ensure you have:

1. Node.js and npm installed
2. Hardhat installed (`npm install --save-dev hardhat`)
3. Python dependencies installed:
   ```bash
   pip install numpy pandas matplotlib tensorflow scikit-learn
   ```
4. An Alchemy API key for forking the Ethereum mainnet

## Configuration

The simulation uses the following configuration files:

1. `backend/ai/hardhat_fork_config.json`: Configuration for the forked mainnet
2. `backend/ai/config/learning_loop_config.json`: Configuration for the learning loop
3. `backend/ai/config/alert_config.json`: Configuration for the alerting system

You can modify these files to customize the simulation.

## Running the Simulation

To run the simulation, use the provided shell script:

```bash
./backend/ai/run_week_simulation.sh [DAYS] [TRADES_PER_DAY] [LEARNING_INTERVAL]
```

Parameters:
- `DAYS`: Number of days to simulate (default: 7)
- `TRADES_PER_DAY`: Number of trades to simulate per day (default: 24)
- `LEARNING_INTERVAL`: How often to run the learning loop in hours (default: 4)

Example:
```bash
./backend/ai/run_week_simulation.sh 7 48 2
```
This will simulate 7 days with 48 trades per day and run the learning loop every 2 hours.

Alternatively, you can run the Python script directly:

```bash
python backend/ai/run_week_simulation.py --days 7 --trades-per-day 48 --learning-interval 2
```

## Simulation Process

The simulation follows these steps:

1. Start a Hardhat node with a forked Ethereum mainnet
2. Initialize the Web3Connector and StrategyOptimizer
3. Start the enhanced monitoring system
4. Start the learning loop
5. For each day:
   - Simulate trades throughout the day
   - Run the learning loop at specified intervals
   - Track metrics and system resources
6. Generate a comprehensive report

## Monitoring the Simulation

During the simulation, you can monitor progress in several ways:

1. Check the log file (`week_simulation.log`) for real-time updates
2. Examine the metrics files in `backend/ai/metrics/week_simulation`
3. Review the daily metrics files in `backend/ai/results/week_simulation`

## Analyzing Results

After the simulation completes, you can analyze the results:

1. Review the simulation report (`backend/ai/results/week_simulation/simulation_report.json`)
2. Examine the daily metrics to see how performance improved over time
3. Check the learning loop statistics to see how the ML models adapted

Key metrics to analyze:
- Trade success rate over time
- Profit growth over time
- Number of model updates and strategy adaptations
- Prediction accuracy improvement
- System resource utilization

## Customizing the Simulation

You can customize the simulation by:

1. Modifying the fork configuration to test different networks, tokens, and DEXes
2. Adjusting the learning loop parameters to test different learning strategies
3. Changing the trade generation logic to test different market conditions
4. Modifying the alerting thresholds to test different monitoring strategies

## Troubleshooting

If you encounter issues:

1. Check the log file for error messages
2. Ensure Hardhat is properly installed and configured
3. Verify that your Alchemy API key is valid
4. Check that all required Python dependencies are installed
5. Ensure the fork configuration is correct

## Next Steps

After running the simulation, consider:

1. Optimizing the trading strategies based on the results
2. Adjusting the learning loop parameters for better adaptation
3. Fine-tuning the alerting thresholds for better monitoring
4. Testing with different market conditions and token pairs

## Conclusion

The week-long simulation provides valuable insights into the ArbitrageX bot's performance, learning capabilities, and adaptation speed. By analyzing the results, you can optimize the bot for better performance in real-world trading scenarios. 