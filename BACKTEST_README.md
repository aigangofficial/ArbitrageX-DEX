# ArbitrageX Backtest Automation

This directory contains scripts to automate the running, monitoring, and analysis of backtests for the ArbitrageX trading system.

## Available Scripts

### 1. `run_backtest.sh`
The basic script to run a backtest with default parameters.

```bash
./run_backtest.sh
```

### 2. `monitor_backtest.sh`
A monitoring script that checks the progress of a running backtest.

```bash
./monitor_backtest.sh
```

This script will:
- Check if the backtest process is running
- Monitor for new result files
- Display the most recent log entries
- Automatically detect when the backtest completes

### 3. `run_and_monitor_backtest.sh`
A combined script that starts a backtest and automatically begins monitoring it.

```bash
./run_and_monitor_backtest.sh
```

This script:
- Sets up the environment with Infura as the RPC provider
- Starts the backtest with default parameters
- Automatically begins monitoring the progress
- Provides real-time updates on the backtest status

### 4. `analyze_backtest_results.sh`
A script to analyze the results after a backtest has completed.

```bash
./analyze_backtest_results.sh
```

This script will:
- Check for result files in the realistic backtest directory
- Analyze JSON result files for profit, ROI, and trade information
- List visualization files
- Analyze log files for errors and warnings
- Provide a summary of the backtest performance

## Customizing Parameters

To customize the backtest parameters, you can edit the `run_and_monitor_backtest.sh` script and modify the following variables:

```bash
# Parameters
INVESTMENT=50
DAYS=3
MIN_PROFIT=0.5
MIN_LIQUIDITY=10000
```

## Troubleshooting

If you encounter issues with the backtest:

1. Check the log file at `logs/realistic_backtest.log`
2. Ensure your RPC provider (Infura) is correctly configured
3. Verify that all dependencies are installed
4. Check for error messages in the monitoring output

## Viewing Results

After a successful backtest:

1. JSON result files will be available in `backend/ai/results/realistic_backtest/`
2. Visualization files (PNG) will be in the same directory
3. Run the analysis script for a summary of the results

## Advanced Usage

For advanced usage, you can modify the scripts to:

- Use different RPC providers
- Change the monitoring interval
- Add notifications when the backtest completes
- Customize the analysis output format

## Requirements

- Bash shell
- Python 3
- jq (optional, for better JSON parsing in the analysis script) 