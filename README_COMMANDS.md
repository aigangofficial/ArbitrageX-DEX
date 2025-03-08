# ArbitrageX Unified Command System

This document explains how to use the new unified command system for the ArbitrageX trading bot.

## Quick Start

The ArbitrageX trading bot now features a unified command interface that simplifies management of all components. The main script is `arbitragex.sh` in the root directory.

To get started:

```bash
# Make the script executable (if not already)
chmod +x arbitragex.sh

# View available commands
./arbitragex.sh
```

## Available Commands

### Start the Bot

```bash
./arbitragex.sh start
```

This launches the complete ArbitrageX trading bot with the ML-enhanced strategy, which includes:
- Layer 2 integration for reduced gas costs
- Flash Loan integration for capital efficiency
- MEV protection against front-running and sandwich attacks
- Advanced ML models for strategy optimization

### Stop the Bot

```bash
./arbitragex.sh stop
```

This terminates all ArbitrageX-related processes.

### Check Status

```bash
./arbitragex.sh status
```

Shows whether ArbitrageX is running and displays information about any active processes.

### View Logs

```bash
# Show the last 50 lines of logs
./arbitragex.sh logs

# Show the last 100 lines of logs
./arbitragex.sh logs --lines=100

# Follow logs in real-time (like tail -f)
./arbitragex.sh logs --follow
```

### Clean Up

```bash
./arbitragex.sh cleanup
```

Removes temporary files and optionally clears log files.

### Restart

```bash
./arbitragex.sh restart
```

Stops all running ArbitrageX processes and starts them again.

## Configuration Options

The `start` command supports several options to customize the trading behavior:

```bash
# Run 100 trades instead of the default 50
./arbitragex.sh start --trades=100

# Only use Layer 2 networks for execution
./arbitragex.sh start --l2-only

# Only use Flash Loans for execution
./arbitragex.sh start --flash-only

# Only use the combined L2 + Flash Loan execution
./arbitragex.sh start --combined-only

# Disable machine learning enhancements
./arbitragex.sh start --ml-disabled

# Disable MEV protection
./arbitragex.sh start --mev-disabled

# Use a custom configuration file
./arbitragex.sh start --config=path/to/config.json
```

## Production Mode

By default, ArbitrageX runs in simulation mode. For production deployment with real funds:

```bash
./arbitragex.sh start --no-simulation
```

**⚠️ WARNING**: Production mode connects to real networks and uses real funds. Only use after thorough testing and with appropriate risk management in place.

## Examples

### Example 1: Simulation with 200 Trades

```bash
./arbitragex.sh start --trades=200
```

### Example 2: L2-Only Mode with ML Disabled

```bash
./arbitragex.sh start --l2-only --ml-disabled
```

### Example 3: Production with Custom Config

```bash
./arbitragex.sh start --no-simulation --config=backend/ai/config/my_production_config.json
```

## Logs and Metrics

Logs are stored in:
```
backend/ai/logs/arbitragex.log
```

Performance metrics are saved to:
```
backend/ai/metrics/
```

## Troubleshooting

If you encounter issues:

1. Check the logs: `./arbitragex.sh logs`
2. Ensure all directories are properly set up: `./arbitragex.sh start` (it will create required directories)
3. Make sure no conflicting processes are running: `./arbitragex.sh stop`
4. Try running with fewer enhancements: `./arbitragex.sh start --ml-disabled --mev-disabled`

If problems persist, check the specific component logs and metrics for more detailed information. 