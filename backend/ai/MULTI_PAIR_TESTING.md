# ArbitrageX Multi-Pair Testing System

This document provides an overview of the multi-pair testing system for ArbitrageX, which allows for comprehensive evaluation of the AI system's performance across different token pairs.

## Overview

The multi-pair testing system enables automated testing of the ArbitrageX AI system across multiple token pairs in a mainnet fork environment. This helps identify the most profitable trading opportunities and optimize the system's token pair selection strategy.

## Components

The multi-pair testing system consists of the following components:

1. **Multi-Pair Test Script** (`run_multi_pair_test.sh`): Orchestrates the testing process for multiple token pairs.
2. **Mainnet Fork Test Script** (`run_mainnet_fork_test.py`): Executes tests for individual token pairs in a mainnet fork environment.
3. **AI Module Runner** (`run_all_ai_modules.py`): Runs the AI modules for each token pair.
4. **Results Visualization** (`visualize_multi_pair_results.py`): Generates visualizations from the test results.
5. **Analysis Document** (`results/multi_pair_analysis.md`): Provides a detailed analysis of the test results.

## Usage

### Running a Multi-Pair Test

To run a multi-pair test, execute the following command:

```bash
./run_multi_pair_test.sh
```

This will:
1. Test all configured token pairs (WETH-USDC, WETH-DAI, WBTC-USDC, etc.)
2. Generate a summary file in the `results` directory
3. Log detailed output for each test

### Customizing the Test

You can customize the test by modifying the following variables in `run_multi_pair_test.sh`:

- `RUN_TIME`: Duration of each test in seconds (default: 60)
- `VISUALIZE`: Whether to enable visualization (default: true)
- `SAVE_RESULTS`: Whether to save results (default: true)
- `BLOCK_NUMBER`: Block number to fork from (default: 18000000)
- `TOKEN_PAIRS`: Array of token pairs to test

### Visualizing Results

To generate visualizations from the test results, run:

```bash
python3 visualize_multi_pair_results.py --summary results/multi_pair_summary_YYYYMMDD_HHMMSS.md
```

This will create visualizations in the `results/visualizations` directory, including:
- Success rate by token pair
- Expected profit by token pair
- Confidence vs. success rate scatter plot
- Total vs. profitable predictions
- Execution time by token pair
- Correlation heatmap

## Test Configuration

### Token Pairs

The system is configured to test the following token pairs:
- WETH-USDC
- WETH-DAI
- WBTC-USDC
- WBTC-WETH
- LINK-USDC
- UNI-USDC
- AAVE-WETH
- COMP-USDC
- SNX-WETH
- YFI-WETH

### DEXes

Each test includes the following DEXes:
- Uniswap V3
- Sushiswap
- Curve
- Balancer
- 1inch

### Networks

Currently, tests are performed on the Ethereum network only, but the system can be extended to support other networks.

## Output Files

The multi-pair test generates the following output files:

1. **Summary File** (`results/multi_pair_summary_YYYYMMDD_HHMMSS.md`): Contains a summary of the test results for all token pairs.
2. **Log File** (`results/multi_pair_test_YYYYMMDD_HHMMSS.log`): Contains detailed logs for each test.
3. **Report Files** (`results/mainnet_fork_report_YYYYMMDD_HHMMSS.txt`): Contains detailed reports for each token pair test.
4. **Visualizations** (`results/visualizations/viz_YYYYMMDD_HHMMSS/`): Contains visualizations of the test results.

## Analysis

The system includes a detailed analysis document (`results/multi_pair_analysis.md`) that provides:

1. **Executive Summary**: Overview of the test results
2. **Test Configuration**: Details of the test setup
3. **Performance Overview**: Summary of key performance metrics
4. **Token Pair Performance Ranking**: Ranking of token pairs by success rate
5. **Key Findings**: Important observations from the test results
6. **Recommendations**: Suggestions for improving the system based on the test results

## Extending the System

### Adding New Token Pairs

To add new token pairs, modify the `TOKEN_PAIRS` array in `run_multi_pair_test.sh`:

```bash
TOKEN_PAIRS=(
  "WETH-USDC"
  "WETH-DAI"
  # Add new pairs here
  "NEW-TOKEN-PAIR"
)
```

### Supporting Additional Networks

To support additional networks, modify the fork configuration in `run_multi_pair_test.sh`:

```json
{
  "mode": "mainnet_fork",
  "fork_url": "https://eth-mainnet.g.alchemy.com/v2/${ALCHEMY_API_KEY}",
  "fork_block_number": "$BLOCK_NUMBER",
  "networks": ["ethereum", "arbitrum", "polygon"],  // Add networks here
  "tokens": {
    "ethereum": ["${PAIR%-*}", "${PAIR#*-}"],
    "arbitrum": ["${PAIR%-*}", "${PAIR#*-}"],  // Add tokens for new networks
    "polygon": ["${PAIR%-*}", "${PAIR#*-}"]
  },
  "dexes": {
    "ethereum": ["uniswap_v3", "sushiswap", "curve", "balancer", "1inch"],
    "arbitrum": ["uniswap_v3", "sushiswap", "balancer"],  // Add DEXes for new networks
    "polygon": ["uniswap_v3", "quickswap", "sushiswap"]
  }
}
```

## Troubleshooting

### Common Issues

1. **Missing Reports**: If reports are not generated, check the log file for errors.
2. **Identical Results**: If all token pairs show identical results, ensure that the random seed is properly set based on the token pair.
3. **Visualization Errors**: If visualization fails, ensure that all required Python packages are installed.

### Required Dependencies

- Python 3.6+
- pandas
- matplotlib
- seaborn
- numpy

## Conclusion

The multi-pair testing system provides a comprehensive framework for evaluating the ArbitrageX AI system's performance across different token pairs. By analyzing the results, you can identify the most profitable trading opportunities and optimize the system's token pair selection strategy. 