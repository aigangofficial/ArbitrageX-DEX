# Enhanced Monitoring System for ArbitrageX

This directory contains the enhanced monitoring system for the ArbitrageX system, which provides comprehensive monitoring, alerting, and performance tracking capabilities.

## Overview

The enhanced monitoring system consists of the following components:

- **Performance Metrics Tracking**: Tracks trade execution metrics, profit/loss, gas costs, and execution times.
- **System Resource Monitoring**: Monitors CPU, memory, and disk usage of the ArbitrageX system.
- **Alerting System**: Generates alerts based on configurable thresholds for various metrics.
- **Comprehensive Testing Framework**: Runs extended tests with multiple token pairs, networks, and DEXes.

## Installation

To install the required dependencies for the enhanced monitoring system, run:

```bash
python backend/ai/install_monitoring_deps.py
```

## Usage

### Running the Enhanced Monitoring System

To run the enhanced monitoring system standalone:

```bash
python backend/ai/run_enhanced_monitoring.py --metrics-dir backend/ai/metrics --save-interval 300 --monitor-interval 60
```

Options:
- `--metrics-dir`: Directory to store metrics (default: `backend/ai/metrics`)
- `--alert-config`: Path to alert configuration file (default: `backend/ai/config/alert_config.json`)
- `--save-interval`: Interval in seconds to save metrics (default: 300)
- `--monitor-interval`: Interval in seconds to monitor system resources (default: 60)

### Running Comprehensive Tests with Monitoring

To run comprehensive tests with enhanced monitoring:

```bash
python backend/ai/run_monitored_test.py --duration 3600 --networks ethereum --token-pairs WETH-USDC --dexes uniswap_v3,sushiswap
```

Options:
- `--duration`: Test duration in seconds (default: 3600)
- `--networks`: Comma-separated list of networks to test (default: ethereum)
- `--token-pairs`: Comma-separated list of token pairs to test (default: WETH-USDC)
- `--dexes`: Comma-separated list of DEXes to test (default: uniswap_v3,sushiswap)
- `--fork-config`: Path to fork configuration file (default: backend/ai/hardhat_fork_config.json)
- `--results-dir`: Directory to store test results (default: backend/ai/results/comprehensive_test)
- `--metrics-dir`: Directory to store metrics (default: backend/ai/metrics)
- `--alert-config`: Path to alert configuration file (default: backend/ai/config/alert_config.json)
- `--save-interval`: Interval in seconds to save metrics (default: 300)
- `--monitor-interval`: Interval in seconds to monitor system resources (default: 60)

### Running System Resource Monitoring Standalone

To run the system resource monitor standalone:

```bash
python backend/ai/system_monitor.py
```

This will display CPU, memory, and disk usage every 5 seconds for 60 seconds.

## Configuration

### Alert Configuration

The alert configuration file (`backend/ai/config/alert_config.json`) contains the following settings:

```json
{
  "enabled": true,
  "log_alerts": true,
  "email_alerts": false,
  "email_config": {
    "smtp_server": "smtp.example.com",
    "smtp_port": 587,
    "smtp_username": "alerts@example.com",
    "smtp_password": "password",
    "from_email": "alerts@example.com",
    "to_email": "admin@example.com"
  },
  "thresholds": {
    "consecutive_failed_trades": 3,
    "low_success_rate": 0.5,
    "negative_profit_threshold": -10.0,
    "high_gas_cost_percent": 50.0,
    "execution_time_threshold_ms": 5000.0,
    "cpu_usage_threshold_percent": 80.0,
    "memory_usage_threshold_mb": 1000.0,
    "disk_usage_threshold_mb": 10000.0
  }
}
```

## Metrics

The enhanced monitoring system tracks the following metrics:

### Trade Metrics
- Total trades
- Successful trades
- Failed trades
- Success rate
- Total profit (USD)
- Gas cost (USD)
- Net profit (USD)
- Average profit per trade (USD)

### Performance Metrics
- Average execution time (ms)
- Maximum execution time (ms)
- Minimum execution time (ms)

### ML Metrics
- Model updates
- Strategy adaptations
- Prediction accuracy

### System Metrics
- CPU usage (%)
- Memory usage (MB and %)
- Disk usage (MB and %)
- Process CPU usage (%)
- Process memory usage (MB)
- Process uptime (seconds)
- System uptime (seconds)

### Network-Specific Metrics
- Trades per network
- Successful trades per network
- Net profit per network (USD)

### Token Pair-Specific Metrics
- Trades per token pair
- Successful trades per token pair
- Net profit per token pair (USD)

### DEX-Specific Metrics
- Trades per DEX
- Successful trades per DEX
- Net profit per DEX (USD)

## Alerts

The enhanced monitoring system generates alerts for the following conditions:

- Consecutive failed trades
- Low success rate
- Negative profit
- High gas cost
- High execution time
- High CPU usage
- High memory usage
- High disk usage

Alerts can be logged to the console and sent via email (if configured).

## Files

- `enhanced_monitoring.py`: Main enhanced monitoring system
- `system_monitor.py`: System resource monitor
- `run_enhanced_monitoring.py`: Script to run the enhanced monitoring system
- `run_comprehensive_test.py`: Comprehensive testing framework
- `run_monitored_test.py`: Script to run comprehensive tests with monitoring
- `install_monitoring_deps.py`: Script to install required dependencies
- `MONITORING_README.md`: This README file 