# ArbitrageX MEV Protection

## Overview

ArbitrageX MEV Protection is a critical security component designed to protect your arbitrage trades from Miner Extractable Value (MEV) attacks such as front-running, sandwich attacks, and transaction reordering. By integrating with private transaction pools and employing advanced risk assessment techniques, the MEV Protection module ensures that your profitable trading opportunities remain profitable even in highly competitive markets.

## What is MEV?

Miner Extractable Value (MEV) refers to the profit that miners (or validators in proof-of-stake systems) can extract by reordering, including, or excluding transactions in the blocks they produce. Common MEV extraction techniques include:

1. **Front-running**: Miners or other actors detect your pending transaction and insert their own transaction before yours, benefiting from the price impact your transaction would cause.

2. **Sandwich Attacks**: Your transaction is sandwiched between two transactions from an attacker - one before (front-running) and one after (back-running) - extracting value from the price movements.

3. **Transaction Reordering**: Miners reorder transactions in a block to maximize their profit, potentially at the expense of regular users.

## Key Features

### 1. Flashbots Integration

The ArbitrageX MEV Protection system integrates with Flashbots, a research and development organization focused on mitigating the negative externalities of MEV:

- **Private Transaction Pools**: Submit transactions directly to miners, bypassing the public mempool
- **Bundle Transactions**: Group multiple transactions to be executed atomically in the same block
- **Priority Bidding**: Specify priority fees to incentivize miners to include your transactions

### 2. Risk Assessment

Before executing trades, the system conducts a thorough MEV risk assessment:

- **Token Pair Analysis**: Identifies high-risk token pairs with significant trading volume and volatility
- **DEX Vulnerability Evaluation**: Assesses which decentralized exchanges are more susceptible to MEV
- **Profit Impact Simulation**: Simulates potential impact of sandwich attacks on your expected profit
- **Dynamic Risk Scoring**: Assigns a risk level (Low, Medium, High, Extreme) to each trade

### 3. Multi-Level Protection

The MEV Protection system offers four levels of protection based on trade characteristics:

- **None**: No protection applied (used for Layer 2 networks with minimal MEV risk)
- **Basic**: Standard Flashbots protection for everyday trades
- **Enhanced**: Advanced protection combining Flashbots with transaction bundling
- **Maximum**: Comprehensive protection including reduced slippage, forced bundling, and optional L2 execution

### 4. Layer 2 Integration

Layer 2 networks often have reduced MEV risk due to their different consensus mechanisms and lower competition:

- **Network-Specific Risk Assessment**: Evaluates MEV risk for each supported L2 network
- **Protected L2 Networks**: Applies MEV protection on high-risk L2 networks (Arbitrum, Optimism)
- **Safe L2 Networks**: Skips protection on networks with minimal MEV risk (Polygon, Base)

### 5. Flash Loan Protection

Flash Loan transactions are particularly vulnerable to MEV due to their large size and high profitability:

- **Forced Private Transactions**: All Flash Loan transactions are automatically routed through private pools
- **Size-Based Protection**: Higher protection levels for larger Flash Loan amounts
- **Bundle Atomicity**: Ensures all Flash Loan operations execute atomically in a single block

## Protection Workflow

The MEV Protection system follows this process for each trade:

1. **Risk Assessment**: Evaluate the MEV risk level of the trading opportunity based on token pair, DEX, expected profit, position size, and slippage
2. **Protection Level Selection**: Determine the appropriate protection level based on risk assessment and trade characteristics
3. **Protection Method Selection**: Choose the specific protection method (Flashbots, transaction bundling, etc.)
4. **Pre-Execution Simulation**: Simulate potential sandwich attacks to assess profitability after MEV
5. **Protection Application**: Apply the selected protection method to the transaction
6. **Execution Monitoring**: Track protection success rate and profit saved from MEV attacks

## Usage

### Running MEV-Protected Strategy

To run the MEV-protected combined strategy, use the provided shell script:

```bash
./backend/ai/run_mev_protected_strategy.sh
```

### Command-Line Options

The script supports several command-line options:

- `--trades=N`: Specify the number of trades to simulate (default: 50)
- `--l2-only`: Only use Layer 2 networks for execution
- `--flash-only`: Only use Flash Loans for execution
- `--combined-only`: Only use the combined L2 + Flash Loan execution method
- `--mev-protection=LEVEL`: Specify MEV protection level (none, basic, enhanced, maximum)
- `--config=PATH`: Specify a custom configuration file

Examples:

```bash
# Run with enhanced MEV protection (default)
./backend/ai/run_mev_protected_strategy.sh

# Run with maximum MEV protection
./backend/ai/run_mev_protected_strategy.sh --mev-protection=maximum

# Run L2-only trades with basic protection
./backend/ai/run_mev_protected_strategy.sh --l2-only --mev-protection=basic
```

## Configuration

The MEV protection system uses a comprehensive configuration file to customize behavior. Key configuration sections include:

### 1. MEV Protection Configuration

```json
"mev_protection": {
    "enabled": true,
    "default_method": "flashbots",
    "flashbots": {
        "relay_url": "https://relay.flashbots.net",
        "min_priority_fee_gwei": 1.5,
        "target_block_count": 3,
        "max_blocks_to_wait": 25
    },
    "transaction_bundling": {
        "enabled": true,
        "max_bundle_size": 4,
        "bundle_timeout_sec": 30
    },
    "simulation": {
        "enabled": true,
        "min_profit_threshold_after_mev": 0.5,
        "sandwich_attack_simulation": true,
        "skip_highly_vulnerable_trades": true
    }
}
```

### 2. Protection Integration Configuration

```json
"mev_protection_integration": {
    "enabled": true,
    "default_protection_level": "basic",
    "l1_protection": {
        "enabled": true,
        "risk_threshold_for_protection": "low",
        "skip_trades_with_extreme_risk": true
    },
    "l2_protection": {
        "enabled": true,
        "networks_requiring_protection": ["arbitrum", "optimism"],
        "networks_without_protection": ["polygon", "base"]
    },
    "flash_loan_protection": {
        "enabled": true,
        "force_private_transactions": true,
        "min_size_for_protection": 2.0
    }
}
```

## Performance Metrics

The MEV protection system tracks detailed metrics to evaluate its effectiveness:

- **Protected Transactions**: Number of transactions that received MEV protection
- **Protection Success Rate**: Percentage of protected transactions that executed successfully
- **Estimated Profit Saved**: USD value of profit saved from potential MEV attacks
- **Protection Level Distribution**: Breakdown of trades by protection level
- **Method Success Rates**: Success rates for different protection methods
- **Network-Specific Metrics**: Protection metrics broken down by network

## Implementation Details

### MEV Protection Manager

The core `MEVProtectionManager` class provides:

1. **Risk Assessment**: Evaluates the MEV risk for each trade
2. **Protection Method Selection**: Selects the optimal protection method based on risk level
3. **Sandwich Attack Simulation**: Simulates the potential impact of sandwich attacks
4. **Transaction Protection**: Applies the selected protection method to transactions

### MEV Protection Integrator

The `MEVProtectionIntegrator` class integrates MEV protection with the trading strategy:

1. **Protection Level Determination**: Selects the appropriate protection level for each trade
2. **Opportunity Enhancement**: Adds MEV protection details to trading opportunities
3. **Protected Transaction Execution**: Executes transactions with the selected protection
4. **Metrics Tracking**: Tracks protection performance and effectiveness

### MEV-Protected Combined Strategy

The `OptimizedStrategyMEVProtected` class extends the combined strategy with MEV protection:

1. **Opportunity Evaluation**: Evaluates trading opportunities with MEV risk consideration
2. **Protected Trade Execution**: Executes trades with appropriate MEV protection
3. **Fallback Execution**: Falls back to unprotected execution if protection fails
4. **Comprehensive Metrics**: Tracks both strategy and protection metrics

## Requirements

- **Web3.py**: For Ethereum blockchain interaction
- **Eth-Account**: For signing and managing transactions
- **Private API Keys**: For production, you'll need API keys for Flashbots and other private transaction services

## Setup

To set up the MEV protection system, run the provided setup tool:

```bash
python tools/create_mev_protected_strategy.py
```

This tool will:
1. Check for required dependencies
2. Create necessary directories
3. Make all required scripts executable
4. Prepare the environment for running MEV-protected trades

## Best Practices

For optimal MEV protection:

1. **Use Enhanced Protection** for high-value trades (>$50 profit or >5 ETH position size)
2. **Use Maximum Protection** for critical trades (>$100 profit or >10 ETH position size)
3. **Reduce Slippage** for highly vulnerable token pairs to minimize sandwich attack impact
4. **Consider L2 Networks** for trades with extreme MEV risk, as they generally have lower MEV activity
5. **Regularly Review Metrics** to fine-tune protection strategies based on performance

## Next Steps

1. **Production API Keys**: Obtain API keys for Flashbots and other private transaction services
2. **Custom Private Keys**: Replace the example private key with your secure trading keys
3. **Extended Testing**: Run longer simulations to validate protection effectiveness
4. **Risk Threshold Tuning**: Adjust risk thresholds based on real-world performance
5. **Additional Protection Methods**: Explore integration with other MEV protection services

## License

ArbitrageX MEV Protection is proprietary software. All rights reserved. 