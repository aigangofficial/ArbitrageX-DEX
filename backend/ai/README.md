# ArbitrageX AI Module

This directory contains the AI components of the ArbitrageX project, which provide intelligent arbitrage opportunity detection, strategy optimization, and multi-network adaptation.

## Components

The AI module consists of the following key components:

1. **Strategy Optimizer** (`strategy_optimizer_demo.py`)
   - Core AI model for predicting arbitrage opportunities
   - Calculates confidence scores and profitability metrics

2. **Network Adaptation** (`network_demo.py`)
   - Adapts strategies across multiple blockchain networks
   - Optimizes for network-specific conditions and time patterns

3. **Multi-Scenario Testing** (`test_ai_model.py`)
   - Tests AI model performance across various scenarios
   - Provides detailed performance metrics

## Running the AI Components

### Prerequisites

- Python 3.8+
- Required packages: numpy, pandas, matplotlib (for visualization)

### Strategy Optimizer Demo

To run the strategy optimizer demo:

```bash
python strategy_optimizer_demo.py
```

This will demonstrate a single arbitrage opportunity prediction with detailed metrics.

### Multi-Scenario Testing

To test the AI model across multiple scenarios:

```bash
python test_ai_model.py
```

This will run the AI model against various token pairs, amounts, and routers, showing how it adapts to different conditions.

### Network Adaptation Demo

To see how the AI adapts strategies across different networks:

```bash
python network_demo.py
```

This demonstrates how the AI optimizes strategies for Ethereum, Arbitrum, Polygon, and BSC at different times of day.

## Integration with ArbitrageX

The AI module integrates with the broader ArbitrageX system in the following ways:

1. **Execution Engine Integration**
   - The execution engine calls `predict_opportunity()` before executing trades
   - AI confidence scores determine whether to proceed with execution

2. **Network Selection**
   - The `adapt_strategy()` method informs which network to use for arbitrage
   - Time-based patterns optimize execution timing

3. **Dashboard Integration**
   - AI predictions and metrics are displayed in the user dashboard
   - Strategy performance is tracked and visualized

## Future Development

For details on the future development roadmap, see the comprehensive documentation in `docs/AI_IMPLEMENTATION.md`.

## Example Usage

```python
from strategy_optimizer_demo import StrategyOptimizer

# Initialize the optimizer
optimizer = StrategyOptimizer()

# Define an arbitrage opportunity
opportunity = {
    "token_in": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
    "token_out": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
    "amount": 1000000000000000000,  # 1 ETH in wei
    "router": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"  # Uniswap
}

# Get prediction
result = optimizer.predict_opportunity(opportunity)

# Check if profitable
if result["is_profitable"]:
    print(f"Profitable opportunity found! Expected profit: ${result['net_profit_usd']:.2f}")
else:
    print(f"Not profitable. Net profit: ${result['net_profit_usd']:.2f}")
``` 