# ArbitrageX AI System

The ArbitrageX AI System is a sophisticated suite of AI-powered modules designed to identify, analyze, and execute profitable arbitrage opportunities across multiple blockchain networks and decentralized exchanges.

## Overview

The system consists of several interconnected modules that work together to provide a complete arbitrage trading solution:

1. **Strategy Optimizer**: Analyzes market conditions and recommends optimal trading strategies.
2. **Backtesting**: Tests trading strategies against historical data to evaluate performance.
3. **Trade Analyzer**: Identifies patterns and trends in trading data to improve future trades.
4. **Network Adaptation**: Adapts trading strategies to different blockchain networks.
5. **Test AI Model**: Tests the AI model against various scenarios to ensure reliability.
6. **Integration**: Connects all modules together and interfaces with the execution engine.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

### Setup

1. Clone the repository:

   ```
   git clone https://github.com/your-username/arbitragex.git
   cd arbitragex
   ```

2. Create and activate a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Running the Entire AI System

The easiest way to run the AI system is using the provided shell script:

```bash
./run_ai_system.sh [options]
```

Options:

- `--mainnet`: Run in mainnet mode (default: testnet)
- `--visualize`: Enable visualization for modules that support it
- `--save-results`: Save results to files
- `--days <number>`: Number of days for historical data (default: 30)
- `--run-time <secs>`: How long to run integration module (default: 60)
- `--modules <list>`: Comma-separated list of modules to run (default: all)
  - Available modules: strategy_optimizer, backtesting, trade_analyzer, network_adaptation, test_ai_model, integration
- `--help`: Display help message

Examples:

```bash
# Run all modules with visualization
./run_ai_system.sh --visualize

# Run specific modules
./run_ai_system.sh --modules strategy_optimizer,backtesting

# Run integration module for 5 minutes
./run_ai_system.sh --modules integration --run-time 300

# Run in mainnet mode with 60 days of historical data
./run_ai_system.sh --mainnet --save-results --days 60
```

### Running Individual Modules

Each module can also be run individually:

#### Strategy Optimizer

```bash
python3 run_strategy_optimizer.py [--testnet] [--visualize]
```

#### Backtesting

```bash
python3 run_backtesting.py [--testnet] [--visualize] [--days 30] [--compare] [--save-results]
```

#### Trade Analyzer

```bash
python3 run_trade_analyzer.py [--testnet] [--visualize] [--days 30] [--save-results]
```

#### Network Adaptation

```bash
python3 run_network_adaptation.py [--testnet] [--visualize] [--networks ethereum,arbitrum,polygon]
```

#### Test AI Model

```bash
python3 run_test_ai_model.py [--testnet] [--visualize]
```

#### Integration

```bash
python3 ai_integration.py [--testnet] [--run-time 60]
```

## Module Details

### Strategy Optimizer

The Strategy Optimizer analyzes current market conditions and recommends optimal trading strategies. It takes into account:

- Token pair prices across different DEXes
- Gas prices and network congestion
- Historical success rates
- Slippage tolerance

Output includes:

- Profitability assessment
- Confidence score
- Estimated profit
- Gas cost
- Net profit
- Execution time
- Recommendations for gas price, DEX, slippage tolerance, and execution priority

### Backtesting

The Backtesting module tests trading strategies against historical data to evaluate performance. It compares AI-driven strategies with baseline strategies and provides detailed metrics:

- Total trades
- Success rate
- Total profit
- Average profit per trade
- Maximum drawdown
- Sharpe ratio

Visualization options include:

- Profit over time
- Success rate by token pair
- Profit distribution
- Comparison with baseline strategy

### Trade Analyzer

The Trade Analyzer identifies patterns and trends in trading data to improve future trades. It analyzes:

- Best trading hours and days
- Most profitable token pairs
- Most reliable DEXes
- Network congestion patterns

Visualization options include:

- Time-based patterns
- Network comparison
- Token performance

### Network Adaptation

The Network Adaptation module adapts trading strategies to different blockchain networks. It takes into account:

- Network-specific gas prices
- Block times
- Congestion patterns
- DEX liquidity

Output includes:

- Network-specific recommendations
- Adaptation metrics
- Cross-network arbitrage opportunities

### Test AI Model

The Test AI Model module tests the AI model against various scenarios to ensure reliability. It evaluates:

- Different token pairs
- Different input amounts
- Different market conditions
- Edge cases

Output includes:

- Confidence scores
- Profit estimates
- Success rates
- Error analysis

### Integration

The Integration module connects all other modules together and interfaces with the execution engine. It provides:

- Real-time market data collection
- AI prediction execution
- Trade execution criteria evaluation
- Frontend updates
- Result storage

## Architecture

The ArbitrageX AI System follows a modular architecture:

1. **Data Collection Layer**: Gathers market data from various sources.
2. **AI Processing Layer**: Analyzes data and makes predictions.
3. **Execution Layer**: Evaluates predictions and executes trades.
4. **Monitoring Layer**: Tracks performance and provides feedback.
5. **Integration Layer**: Connects all components together.

## Development

### Adding New Features

To add a new feature:

1. Create a new module in the appropriate directory.
2. Update the runner scripts to include the new module.
3. Add tests for the new feature.
4. Update documentation.

### Testing

Run tests using:

```bash
python -m unittest discover tests
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Aave](https://aave.com/) for flash loan protocol
- [Uniswap](https://uniswap.org/), [SushiSwap](https://sushi.com/), and other DEXes for providing liquidity
- [Ethereum](https://ethereum.org/), [Arbitrum](https://arbitrum.io/), [Polygon](https://polygon.technology/), and other networks for providing the infrastructure

## Mainnet Fork Testing

The ArbitrageX AI system can be tested in a mainnet fork environment to validate its performance with real-world liquidity conditions without risking actual funds.

### Running Mainnet Fork Tests

To run a comprehensive mainnet fork test:

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

### Mainnet Fork Test Options

- `--modules <list>`: Comma-separated list of modules to run (default: all modules)
- `--run-time <secs>`: How long to run the integration module in seconds (default: 300)
- `--block <number>`: Block number to fork from (default: latest)
- `--no-visualize`: Disable visualization
- `--no-save-results`: Disable saving results
- `--help`: Display help message

### Test Results

The mainnet fork test generates a comprehensive report with the following information:

- Summary of predictions (total, profitable, percentage)
- Expected profit analysis
- Performance metrics (execution times)
- Network, token pair, and DEX distribution
- Overall conclusion about AI system performance

Reports are saved in the `results` directory with timestamps for easy reference.
