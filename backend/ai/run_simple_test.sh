#!/bin/bash
#
# Run a simple ArbitrageX simulation test
#

# Set up error handling
set -e
trap 'echo "Error occurred at line $LINENO. Command: $BASH_COMMAND"' ERR

# Configuration
START_DATE="2025-03-06"
END_DATE="2025-03-07"
TRADES_PER_DAY=10
LEARNING_INTERVAL=6
METRICS_DIR="backend/ai/metrics/simple_test"
RESULTS_DIR="backend/ai/results/simple_test"

# Print banner
echo "=========================================================="
echo "  ArbitrageX Simple Test Simulation"
echo "=========================================================="
echo "Start Date: $START_DATE"
echo "End Date: $END_DATE"
echo "Trades Per Day: $TRADES_PER_DAY"
echo "Learning Interval: $LEARNING_INTERVAL hours"
echo "Metrics Directory: $METRICS_DIR"
echo "Results Directory: $RESULTS_DIR"
echo "=========================================================="

# Create directories
mkdir -p "$METRICS_DIR"
mkdir -p "$RESULTS_DIR"

# Make test script executable
chmod +x backend/ai/test_simulation.py

# Run the simulation
python backend/ai/test_simulation.py \
  --start-date "$START_DATE" \
  --end-date "$END_DATE" \
  --trades-per-day "$TRADES_PER_DAY" \
  --learning-interval "$LEARNING_INTERVAL" \
  --metrics-dir "$METRICS_DIR" \
  --results-dir "$RESULTS_DIR" \
  --synthetic-data

# Check if simulation completed successfully
if [ $? -eq 0 ]; then
  echo "Simulation completed successfully!"
  
  # Check if the report exists
  REPORT_FILE="$RESULTS_DIR/simulation_report.json"
  
  if [ -f "$REPORT_FILE" ]; then
    echo "=========================================================="
    echo "  Simulation Summary"
    echo "=========================================================="
    
    # Extract key metrics from the report
    TOTAL_TRADES=$(grep -o '"total_trades": [0-9]*' "$REPORT_FILE" | awk '{print $2}')
    SUCCESSFUL_TRADES=$(grep -o '"successful_trades": [0-9]*' "$REPORT_FILE" | awk '{print $2}')
    SUCCESS_RATE=$(grep -o '"success_rate": [0-9.]*' "$REPORT_FILE" | awk '{print $2}')
    TOTAL_PROFIT=$(grep -o '"total_profit_usd": [0-9.]*' "$REPORT_FILE" | awk '{print $2}')
    AVG_PROFIT=$(grep -o '"avg_profit_per_day_usd": [0-9.]*' "$REPORT_FILE" | awk '{print $2}')
    
    echo "Total Trades: $TOTAL_TRADES"
    echo "Successful Trades: $SUCCESSFUL_TRADES"
    echo "Success Rate: $SUCCESS_RATE%"
    echo "Total Profit: \$$TOTAL_PROFIT"
    echo "Average Profit per Day: \$$AVG_PROFIT"
    echo "=========================================================="
    echo ""
    echo "Detailed report available at: $REPORT_FILE"
  else
    echo "Warning: Simulation report not found."
  fi
else
  echo "Simulation failed. Check the log file for details: test_simulation.log"
fi

echo ""
echo "Thank you for using ArbitrageX!" 