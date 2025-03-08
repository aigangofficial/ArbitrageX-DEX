#!/bin/bash
#
# ArbitrageX Advanced Simulation (3 Months)
#
# This script runs a comprehensive 3-month simulation of the ArbitrageX bot
# using a simplified but realistic simulator that models ML adaptation.
#

# Set up error handling
set -e
trap 'echo "Error occurred at line $LINENO. Command: $BASH_COMMAND"' ERR

# Calculate dates
END_DATE=$(date +"%Y-%m-%d")
# On macOS, we use a different approach for date calculation
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS date command
    START_DATE=$(date -v-3m +"%Y-%m-%d")
else
    # Linux date command
    START_DATE=$(date -d "$END_DATE - 3 months" +"%Y-%m-%d")
fi

# Configuration
TRADES_PER_DAY=${1:-24}  # Default to 24 trades per day
LEARNING_INTERVAL=${2:-6}  # Default to learning every 6 hours
METRICS_DIR="backend/ai/metrics/advanced_simulation"
RESULTS_DIR="backend/ai/results/advanced_simulation"

# Print banner
echo "=========================================================="
echo "  ArbitrageX Advanced Simulation (3 Months)"
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

# Calculate total days
if [[ "$OSTYPE" == "darwin"* ]]; then
    start_date_seconds=$(date -j -f "%Y-%m-%d" "$START_DATE" +%s)
    end_date_seconds=$(date -j -f "%Y-%m-%d" "$END_DATE" +%s)
else
    start_date_seconds=$(date -d "$START_DATE" +%s)
    end_date_seconds=$(date -d "$END_DATE" +%s)
fi
total_days=$(( (end_date_seconds - start_date_seconds) / 86400 ))
echo "Total simulation days: $total_days"

# Calculate estimated execution time (roughly 2 seconds per day)
estimated_seconds=$((total_days * 2))
estimated_minutes=$((estimated_seconds / 60))
estimated_hours=$((estimated_minutes / 60))
estimated_minutes=$((estimated_minutes % 60))

echo "Estimated execution time: $estimated_hours hours and $estimated_minutes minutes"
echo ""
echo "This simulation will generate a comprehensive model of ArbitrageX's performance over a 3-month period."
echo "The simulation will accelerate time but maintain realistic market conditions and learning patterns."
echo ""
echo "Press Ctrl+C to stop the simulation at any time."
echo ""
echo "Starting simulation in 5 seconds..."
sleep 5

# Start time
start_time=$(date +%s)

# Run the simulation
python backend/ai/test_simulation_advanced.py \
  --start-date "$START_DATE" \
  --end-date "$END_DATE" \
  --trades-per-day "$TRADES_PER_DAY" \
  --learning-interval "$LEARNING_INTERVAL" \
  --metrics-dir "$METRICS_DIR" \
  --results-dir "$RESULTS_DIR"

# Check if simulation completed successfully
if [ $? -eq 0 ]; then
  echo "Simulation completed successfully!"
  
  # End time and duration
  end_time=$(date +%s)
  duration=$((end_time - start_time))
  hours=$((duration / 3600))
  minutes=$(((duration % 3600) / 60))
  seconds=$((duration % 60))
  
  echo "Simulation finished in $hours hours, $minutes minutes, and $seconds seconds."
  
  # Check if the report exists
  REPORT_FILE="$RESULTS_DIR/simulation_report.json"
  SUMMARY_FILE="$RESULTS_DIR/simulation_summary.md"
  
  if [ -f "$REPORT_FILE" ] && [ -f "$SUMMARY_FILE" ]; then
    echo "=========================================================="
    echo "  Simulation Summary"
    echo "=========================================================="
    echo ""
    
    # Extract key metrics from the report
    TOTAL_TRADES=$(grep -o '"total_trades": [0-9]*' "$REPORT_FILE" | head -1 | awk '{print $2}')
    SUCCESSFUL_TRADES=$(grep -o '"successful_trades": [0-9]*' "$REPORT_FILE" | head -1 | awk '{print $2}')
    SUCCESS_RATE=$(grep -o '"success_rate": [0-9.]*' "$REPORT_FILE" | head -1 | awk '{print $2}')
    TOTAL_PROFIT=$(grep -o '"total_profit_usd": [0-9.-]*' "$REPORT_FILE" | head -1 | awk '{print $2}')
    AVG_PROFIT_PER_DAY=$(grep -o '"avg_profit_per_day_usd": [0-9.-]*' "$REPORT_FILE" | head -1 | awk '{print $2}')
    INITIAL_ACCURACY=$(grep -o '"initial_prediction_accuracy": [0-9.]*' "$REPORT_FILE" | head -1 | awk '{print $2}')
    FINAL_ACCURACY=$(grep -o '"final_prediction_accuracy": [0-9.]*' "$REPORT_FILE" | head -1 | awk '{print $2}')
    ACCURACY_IMPROVEMENT=$(grep -o '"accuracy_improvement": [0-9.]*' "$REPORT_FILE" | head -1 | awk '{print $2}')
    
    echo "Total Trades: $TOTAL_TRADES"
    echo "Successful Trades: $SUCCESSFUL_TRADES"
    echo "Success Rate: $SUCCESS_RATE%"
    echo "Total Profit: \$$TOTAL_PROFIT"
    echo "Average Profit per Day: \$$AVG_PROFIT_PER_DAY"
    echo "Initial Prediction Accuracy: $INITIAL_ACCURACY%"
    echo "Final Prediction Accuracy: $FINAL_ACCURACY%"
    echo "Accuracy Improvement: $ACCURACY_IMPROVEMENT%"
    echo "=========================================================="
    echo ""
    echo "Detailed report available at: $REPORT_FILE"
    echo "Summary report available at: $SUMMARY_FILE"
    
    # Display top 3 most profitable token pairs from the summary
    echo ""
    echo "Top 3 Most Profitable Token Pairs:"
    grep -A 5 "^## Top 5 Most Profitable Token Pairs" "$SUMMARY_FILE" | grep "|" | grep -v "Token Pair" | grep -v "----" | head -3
    
    # Display top DEX from the summary
    echo ""
    echo "Most Profitable DEX:"
    grep -A 3 "^## Top 3 Most Profitable DEXes" "$SUMMARY_FILE" | grep "|" | grep -v "DEX" | grep -v "----" | head -1
    
  else
    echo "Warning: Simulation reports not found."
  fi
  
  # Suggest next steps
  echo ""
  echo "Next steps:"
  echo "1. Review the detailed metrics in $METRICS_DIR"
  echo "2. Analyze the simulation report in $RESULTS_DIR"
  echo "3. Check the log file for detailed information: test_simulation_advanced.log"
else
  echo "Simulation failed. Check the log file for details: test_simulation_advanced.log"
fi

echo ""
echo "Thank you for using ArbitrageX!" 