#!/bin/bash
#
# ArbitrageX Test Simulation
#
# This script runs a short test simulation (2 days) to verify that the
# extended simulation system works correctly.
#

# Set up error handling
set -e
trap 'echo "Error occurred at line $LINENO. Command: $BASH_COMMAND"' ERR

# Calculate dates for macOS
END_DATE=$(date +"%Y-%m-%d")
# On macOS, we use a different approach for date calculation
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS date command
    START_DATE=$(date -v-2d +"%Y-%m-%d")
else
    # Linux date command
    START_DATE=$(date -d "$END_DATE - 2 days" +"%Y-%m-%d")
fi

METRICS_DIR="backend/ai/metrics/test_simulation"
RESULTS_DIR="backend/ai/results/test_simulation"

# Print banner
echo "=========================================================="
echo "  ArbitrageX Test Simulation (2 Days)"
echo "=========================================================="
echo "Start Date: $START_DATE"
echo "End Date: $END_DATE"
echo "Trades Per Day: 12 (1 per 2 hours)"
echo "Learning Interval: 6 hours"
echo "=========================================================="

# Create directories
mkdir -p "$METRICS_DIR"
mkdir -p "$RESULTS_DIR"

# Run the simulation with synthetic data
python backend/ai/run_extended_simulation.py \
  --start-date "$START_DATE" \
  --end-date "$END_DATE" \
  --trades-per-day 12 \
  --learning-interval 6 \
  --metrics-dir "$METRICS_DIR" \
  --results-dir "$RESULTS_DIR" \
  --synthetic-data

# Check if simulation completed successfully
if [ $? -eq 0 ]; then
  echo "Test simulation completed successfully!"
  
  # Check if the report exists
  REPORT_FILE="$RESULTS_DIR/simulation_report.json"
  
  if [ -f "$REPORT_FILE" ]; then
    echo "=========================================================="
    echo "  Test Simulation Summary"
    echo "=========================================================="
    
    # Extract key metrics from the report
    TOTAL_TRADES=$(grep -o '"total_trades": [0-9]*' "$REPORT_FILE" | head -1 | awk '{print $2}')
    SUCCESSFUL_TRADES=$(grep -o '"successful_trades": [0-9]*' "$REPORT_FILE" | head -1 | awk '{print $2}')
    SUCCESS_RATE=$(grep -o '"success_rate": [0-9.]*' "$REPORT_FILE" | head -1 | awk '{print $2}')
    TOTAL_PROFIT=$(grep -o '"total_profit_usd": [0-9.]*' "$REPORT_FILE" | head -1 | awk '{print $2}')
    
    echo "Total Trades: $TOTAL_TRADES"
    echo "Successful Trades: $SUCCESSFUL_TRADES"
    echo "Success Rate: $SUCCESS_RATE%"
    echo "Total Profit: \$$TOTAL_PROFIT"
    echo "=========================================================="
    echo ""
    echo "Detailed report available at: $REPORT_FILE"
    echo ""
    echo "If this test simulation worked correctly, you can now run the full 3-month simulation:"
    echo ""
    echo "  ./backend/ai/run_extended_simulation.sh"
    echo ""
  else
    echo "Warning: Simulation report not found."
  fi
else
  echo "Test simulation failed. Check the log file for details: extended_simulation.log"
fi 