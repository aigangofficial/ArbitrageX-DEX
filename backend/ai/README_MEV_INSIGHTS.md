# MEV Protection Insights

## Overview

The MEV Protection Insights module provides comprehensive monitoring and analysis of MEV (Miner Extractable Value) protection activities in the ArbitrageX trading bot. This feature offers:

✅ **Live Status Monitoring** - Shows if MEV protection is ON or OFF
✅ **Protection Level Tracking** - Tracks how many transactions were secured from front-running
✅ **Estimated Savings Display** - Displays how much profit was saved from MEV attackers

## Implementation Details

The MEV Protection Insights feature is implemented through several key components:

1. **Flashbots API Integration** - Submit trades directly to miners, bypassing the public mempool where they would be visible to frontrunners
2. **MEV Risk Scanning** - Analyze each trade for potential MEV risk and apply appropriate protection
3. **Protection Level Metrics** - Track the number of trades protected at each level (Basic, Enhanced, Maximum)
4. **Savings Estimation** - Calculate the potential profit saved from front-running and sandwich attacks
5. **Risk Level Analysis** - Categorize trades by MEV risk level (Low, Medium, High, Extreme)
6. **Web Dashboard** - Visualize MEV protection activities and metrics in real-time

## Directory Structure

```
backend/ai/
├── mev_protection.py               # Core MEV protection functionality
├── mev_protection_integration.py   # Integration with trading strategies
├── mev_protection_insights.py      # Protection metrics and insights tracking
├── run_mev_protection_insights.py  # Demo script for protection insights
├── run_mev_insights.sh             # Shell script to run demo and dashboard
└── dashboard/
    ├── app.py                      # Web dashboard application
    └── templates/
        └── mev_protection.html     # MEV Protection Insights dashboard template
```

## Getting Started

### Prerequisites

- Python 3.8 or later
- Required Python packages (Flask, web3, etc.) as listed in `dashboard/requirements.txt`

### Running the Demo

To see the MEV Protection Insights in action, run the demo script:

```bash
cd backend/ai
./run_mev_insights.sh demo
```

This will simulate a series of transactions with various MEV protection levels and display the metrics.

### Starting the Dashboard

To view the MEV Protection Insights dashboard:

```bash
cd backend/ai
./run_mev_insights.sh dashboard
```

Then open your browser and navigate to: http://localhost:5000/mev_protection

### Using Both

To run the demo and then start the dashboard:

```bash
cd backend/ai
./run_mev_insights.sh
```

## Features

### Protection Status Monitoring

The MEV Protection Insights module tracks the current status of MEV protection (enabled or disabled) and provides a toggle to control it from the dashboard.

### Protection Level Metrics

Transactions are protected at different levels based on their value and MEV risk:

- **Basic Protection**: Standard protection for regular trades with moderate MEV risk
- **Enhanced Protection**: Advanced protection for higher-value trades or those with elevated MEV risk
- **Maximum Protection**: Comprehensive protection for high-value trades or those with extreme MEV risk

### MEV Risk Assessment

Each transaction is analyzed for potential MEV risk and categorized into one of four risk levels:

- **Low**: Minimal risk of MEV attacks
- **Medium**: Moderate risk of MEV attacks
- **High**: Significant risk of MEV attacks
- **Extreme**: Very high risk of MEV attacks

### Protection Methods

Various protection methods are used depending on the transaction characteristics:

- **Flashbots**: Submit transactions directly to miners, bypassing the public mempool
- **Eden Network**: Prioritize transactions through the Eden Network
- **Bloxroute**: Use Bloxroute's Ethical Relay for private transaction submission
- **Transaction Bundle**: Group multiple transactions to be executed atomically
- **Backrun Only**: Allow only backrunning (not front-running or sandwiching)

### Estimated Savings

The module estimates the potential profit saved from MEV attacks based on:

- Transaction value
- MEV risk level
- Current market conditions
- Historical MEV attack patterns

### Dashboard Views

The web dashboard provides multiple views of MEV protection data:

- **Status Cards**: Quick overview of protection status, transaction counts, and estimated savings
- **Protection Level Chart**: Distribution of transactions across protection levels
- **Risk Level Chart**: Distribution of transactions across risk levels
- **Savings Chart**: Historical trend of estimated savings over time
- **Protection Methods Table**: Breakdown of transactions by protection method
- **High Risk Trades Table**: Details of recent high-risk trades and their protection

## API Endpoints

The following API endpoints are available for the MEV Protection Insights:

- **GET /api/mev-protection/metrics**: Get current MEV protection metrics
- **GET /api/mev-protection/insights**: Get MEV protection insights (historical data, high-risk trades, etc.)
- **GET /api/mev-protection/summary**: Get a summary of MEV protection status and metrics
- **POST /api/mev-protection/toggle**: Toggle MEV protection on/off
- **POST /api/mev-protection/settings**: Update MEV protection settings

## Integration with Trading Strategies

The MEV Protection Insights module is integrated with the trading strategies through the `MEVProtectionIntegrator` class. The integration process:

1. Assess each trading opportunity for MEV risk
2. Determine the appropriate protection level based on transaction value and risk
3. Apply the selected protection method
4. Track protection metrics and estimated savings
5. Provide real-time feedback through the dashboard

## Code Example

Here's a simple example of how to use the MEV Protection Insights module:

```python
from mev_protection import MEVProtectionManager, MEVRiskLevel
from mev_protection_integration import MEVProtectionIntegrator
from mev_protection_insights import MEVProtectionInsights

# Initialize components
insights_tracker = MEVProtectionInsights()
integrator = MEVProtectionIntegrator()

# Enable MEV protection
insights_tracker.set_protection_status(True)

# Process a transaction
transaction = {
    "value": 1.5,  # ETH
    "gas_price": 20,  # Gwei
    "transaction": {
        "from": "0x...",
        "to": "0x...",
        "value": 1.5 * 10**18,
        "gas": 200000,
        "gasPrice": 20 * 10**9,
        "data": "0x..."
    }
}

# Enhance with MEV protection
protected_tx = integrator.enhance_opportunity_with_protection(transaction)

# Execute the protected transaction
result = integrator.execute_protected_transaction(protected_tx, "private_key")

# Get metrics
metrics = insights_tracker.get_metrics()
print(f"Protected Transactions: {metrics['protected_transactions']['total']}")
print(f"Estimated Savings: ${metrics['estimated_savings']:.2f}")
```

## Future Enhancements

Planned future enhancements for the MEV Protection Insights feature:

1. **Advanced MEV Simulation**: Simulate potential MEV attacks to better estimate savings
2. **Machine Learning Risk Assessment**: Use ML to improve MEV risk assessment accuracy
3. **Cross-chain MEV Monitoring**: Track MEV protection metrics across multiple blockchains
4. **Protection Optimization**: Automatically adjust protection methods based on historical performance
5. **API Integration**: Provide an API for external tools to access MEV protection metrics

## Troubleshooting

If you encounter issues with the MEV Protection Insights:

- Check the log files: `mev_protection_insights.log` and `mev_protection_integration.log`
- Ensure all required Python packages are installed
- Verify that the Flashbots API is accessible from your environment
- Check the network connections for external API calls

## License

This module is part of the ArbitrageX trading bot and is subject to the same licensing terms as the main project. 