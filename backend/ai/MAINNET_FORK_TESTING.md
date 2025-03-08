# ArbitrageX Mainnet Fork Testing

This document provides an overview of the mainnet fork testing capabilities in ArbitrageX.

## Overview

Mainnet fork testing allows the ArbitrageX AI system to be tested against real-world liquidity conditions without risking actual funds. This is achieved by:

1. Creating a local fork of the Ethereum mainnet (or other supported networks)
2. Running the AI system against this fork
3. Analyzing the results to evaluate performance

## Testing Components

The mainnet fork testing system consists of the following components:

### 1. Python Scripts

- `run_mainnet_fork_test.py`: Core script that runs the AI modules with a fork configuration
- `run_mainnet_fork.sh`: Shell script wrapper for the Python script with common options

### 2. Hardhat Integration

- `run_ai_with_hardhat_fork.sh`: Script that starts a Hardhat mainnet fork and runs the AI system against it

### 3. Fork Configuration

- `fork_config.json`: Configuration file for the mainnet fork test
- `hardhat_fork_config.json`: Configuration file for the Hardhat mainnet fork

## Running Tests

### Basic Usage

```bash
# Run with default options
./run_mainnet_fork.sh

# Run with specific modules
./run_mainnet_fork.sh --modules strategy_optimizer,backtesting

# Run with longer integration time
./run_mainnet_fork.sh --run-time 600

# Run with a specific block number
./run_mainnet_fork.sh --block 12345678
```

### With Hardhat Fork

```bash
# From project root
./scripts/run_ai_with_hardhat_fork.sh

# With specific options
./scripts/run_ai_with_hardhat_fork.sh --fork-block 12345678 --run-time 600
```

## Test Results

The mainnet fork tests generate comprehensive reports with the following information:

- Summary of predictions (total, profitable, percentage)
- Expected profit analysis
- Performance metrics (execution times)
- Network, token pair, and DEX distribution
- Overall conclusion about AI system performance

Reports are saved in the `results` directory with timestamps for easy reference.

## Interpreting Results

The test results provide insights into:

1. **Profitability**: What percentage of identified arbitrage opportunities are profitable
2. **Performance**: How quickly the AI system can identify and execute trades
3. **Distribution**: Which networks, token pairs, and DEXes are most profitable
4. **Confidence**: How confident the AI system is in its predictions

## Next Steps

Based on the test results, the following actions may be taken:

1. **Optimize AI Models**: If profitability is low, the AI models may need to be retrained or optimized
2. **Improve Execution**: If execution times are high, the execution engine may need to be optimized
3. **Expand Coverage**: If certain networks or token pairs are more profitable, coverage may be expanded
4. **Adjust Parameters**: Gas price multipliers, slippage tolerance, and other parameters may be adjusted

## Conclusion

Mainnet fork testing is a critical component of the ArbitrageX development process, allowing the AI system to be tested and optimized in realistic market conditions without risking actual funds.
