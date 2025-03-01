#!/bin/bash
# ArbitrageX Multi-Pair Test
# This script runs mainnet fork tests with multiple token pairs to find profitable opportunities.

# Default values
RUN_TIME=60
VISUALIZE=true
SAVE_RESULTS=true
BLOCK_NUMBER="18000000"  # Using a specific block number instead of "latest"

# Create results directory
mkdir -p results

# Log file
LOG_FILE="results/multi_pair_test_$(date +%Y%m%d_%H%M%S).log"
echo "Logging to $LOG_FILE"
echo "Starting multi-pair test at $(date)" | tee -a $LOG_FILE

# Token pairs to test
TOKEN_PAIRS=(
  "WETH-USDC"
  "WETH-DAI"
  "WBTC-USDC"
  "WBTC-WETH"
  "LINK-USDC"
  "UNI-USDC"
  "AAVE-WETH"
  "COMP-USDC"
  "SNX-WETH"
  "YFI-WETH"
)

# Create a summary file
SUMMARY_FILE="results/multi_pair_summary_$(date +%Y%m%d_%H%M%S).md"
echo "# ArbitrageX Multi-Pair Test Results" > $SUMMARY_FILE
echo "" >> $SUMMARY_FILE
echo "Test conducted on: $(date)" >> $SUMMARY_FILE
echo "" >> $SUMMARY_FILE
echo "| Token Pair | Total Predictions | Profitable Predictions | Success Rate | Total Expected Profit | Avg Confidence | Avg Execution Time |" >> $SUMMARY_FILE
echo "|------------|-------------------|------------------------|--------------|----------------------|----------------|---------------------|" >> $SUMMARY_FILE

# Test each token pair
for PAIR in "${TOKEN_PAIRS[@]}"; do
  echo "===== Testing $PAIR =====" | tee -a $LOG_FILE
  
  # Create fork configuration for this pair
  CONFIG_FILE="fork_config_${PAIR}.json"
  cat > $CONFIG_FILE << EOL
{
  "mode": "mainnet_fork",
  "fork_url": "https://eth-mainnet.g.alchemy.com/v2/\${ALCHEMY_API_KEY}",
  "fork_block_number": "$BLOCK_NUMBER",
  "networks": ["ethereum"],
  "tokens": {
    "ethereum": ["${PAIR%-*}", "${PAIR#*-}"]
  },
  "dexes": {
    "ethereum": ["uniswap_v3", "sushiswap", "curve", "balancer", "1inch"]
  },
  "token_pair": "$PAIR",
  "gas_price_multiplier": 1.1,
  "slippage_tolerance": 0.005,
  "execution_timeout_ms": 5000,
  "simulation_only": true,
  "log_level": "INFO"
}
EOL

  # Run the test
  echo "Running test for $PAIR..." | tee -a $LOG_FILE
  
  # Build command
  CMD="python3 run_mainnet_fork_test.py --block-number $BLOCK_NUMBER --modules strategy_optimizer --run-time $RUN_TIME --fork-config $CONFIG_FILE"
  
  if [ "$VISUALIZE" = false ]; then
    CMD="$CMD --no-visualize"
  fi
  
  if [ "$SAVE_RESULTS" = false ]; then
    CMD="$CMD --no-save-results"
  fi
  
  # Run command and capture output
  echo "Executing: $CMD" | tee -a $LOG_FILE
  OUTPUT=$(eval $CMD 2>&1)
  echo "$OUTPUT" >> $LOG_FILE
  
  # Extract results
  REPORT_PATH=$(echo "$OUTPUT" | grep "Report generated at:" | awk '{print $4}')
  
  if [ -n "$REPORT_PATH" ] && [ -f "$REPORT_PATH" ]; then
    # Parse the report
    TOTAL_PREDICTIONS=$(grep "Total predictions:" "$REPORT_PATH" | awk '{print $3}')
    PROFITABLE_PREDICTIONS=$(grep "Profitable predictions:" "$REPORT_PATH" | awk '{print $3}')
    SUCCESS_RATE=$(grep "Profitable predictions:" "$REPORT_PATH" | awk -F'[(%)]' '{print $2}')
    TOTAL_PROFIT=$(grep "Total expected profit:" "$REPORT_PATH" | awk '{print $4}')
    AVG_CONFIDENCE=$(grep "Average confidence score:" "$REPORT_PATH" | awk '{print $4}')
    
    if grep -q "Average execution time:" "$REPORT_PATH"; then
      AVG_EXECUTION=$(grep "Average execution time:" "$REPORT_PATH" | awk '{print $4 " " $5}')
    else
      AVG_EXECUTION="N/A"
    fi
    
    # Add to summary
    echo "| $PAIR | $TOTAL_PREDICTIONS | $PROFITABLE_PREDICTIONS | ${SUCCESS_RATE}% | $TOTAL_PROFIT | $AVG_CONFIDENCE | $AVG_EXECUTION |" >> $SUMMARY_FILE
    
    echo "Results for $PAIR:" | tee -a $LOG_FILE
    echo "  Total Predictions: $TOTAL_PREDICTIONS" | tee -a $LOG_FILE
    echo "  Profitable Predictions: $PROFITABLE_PREDICTIONS (${SUCCESS_RATE}%)" | tee -a $LOG_FILE
    echo "  Total Expected Profit: $TOTAL_PROFIT" | tee -a $LOG_FILE
    echo "  Average Confidence: $AVG_CONFIDENCE" | tee -a $LOG_FILE
    echo "  Average Execution Time: $AVG_EXECUTION" | tee -a $LOG_FILE
  else
    echo "Error: Could not find report for $PAIR" | tee -a $LOG_FILE
    echo "| $PAIR | Error | Error | Error | Error | Error | Error |" >> $SUMMARY_FILE
  fi
  
  # Clean up the fork config file
  rm -f $CONFIG_FILE
  
  echo "" | tee -a $LOG_FILE
done

# Add conclusion to summary
echo "" >> $SUMMARY_FILE
echo "## Conclusion" >> $SUMMARY_FILE
echo "" >> $SUMMARY_FILE
echo "This test evaluated ArbitrageX's performance across multiple token pairs to identify the most profitable opportunities." >> $SUMMARY_FILE
echo "The results can be used to optimize the system's token pair selection strategy and improve overall profitability." >> $SUMMARY_FILE

echo "Multi-pair test completed. Summary available at: $SUMMARY_FILE" | tee -a $LOG_FILE 