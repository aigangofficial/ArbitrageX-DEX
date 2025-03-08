#!/bin/bash
#
# ArbitrageX Multiple Fork Tests
#
# This script runs multiple fork tests with monitoring to evaluate
# the bot's performance and learning capabilities.
#

# Set up error handling
set -e
trap 'echo "Error occurred at line $LINENO. Command: $BASH_COMMAND"' ERR

# Configuration
NUM_TESTS=${1:-10}  # Default to 10 tests if not specified
INTERVAL=${2:-5}    # Default to 5 seconds between tests
METRICS_DIR="backend/ai/metrics/multiple_tests"
RESULTS_DIR="backend/ai/results/multiple_tests"
LOG_FILE="multiple_fork_tests.log"

# Print banner
echo "=========================================================="
echo "  ArbitrageX Multiple Fork Tests"
echo "=========================================================="
echo "Number of tests: $NUM_TESTS"
echo "Interval between tests: $INTERVAL seconds"
echo "Metrics directory: $METRICS_DIR"
echo "Results directory: $RESULTS_DIR"
echo "Log file: $LOG_FILE"
echo "=========================================================="

# Create directories
mkdir -p "$METRICS_DIR"
mkdir -p "$RESULTS_DIR"

# Initialize metrics
echo "{\"total_tests\": $NUM_TESTS, \"successful_tests\": 0, \"total_profit\": 0.0, \"trades\": []}" > "$RESULTS_DIR/summary.json"

# Start monitoring
echo "Starting enhanced monitoring..."
python backend/ai/run_enhanced_monitoring.py --save-interval 60 --monitor-interval 30 --metrics-dir "$METRICS_DIR" &
MONITORING_PID=$!

# Wait for monitoring to start
sleep 5

# Run tests
echo "Running $NUM_TESTS fork tests..."
for ((i=1; i<=$NUM_TESTS; i++)); do
    echo "Running test $i of $NUM_TESTS..."
    
    # Run the test
    python backend/ai/test_fork_trade.py
    
    # Extract results from the log file
    SUCCESS=$(grep -c "Trade simulation completed successfully" test_fork_trade.log || echo "0")
    PROFIT=$(grep -o "Profit: [0-9.]*" test_fork_trade.log | awk '{print $2}' || echo "0.0")
    
    # Update summary
    CURRENT_SUMMARY=$(cat "$RESULTS_DIR/summary.json")
    SUCCESSFUL_TESTS=$(echo "$CURRENT_SUMMARY" | grep -o '"successful_tests": [0-9]*' | awk '{print $2}')
    TOTAL_PROFIT=$(echo "$CURRENT_SUMMARY" | grep -o '"total_profit": [0-9.]*' | awk '{print $2}')
    
    if [ "$SUCCESS" -eq "1" ]; then
        SUCCESSFUL_TESTS=$((SUCCESSFUL_TESTS + 1))
        TOTAL_PROFIT=$(echo "$TOTAL_PROFIT + $PROFIT" | bc)
    fi
    
    # Update summary file
    echo "$CURRENT_SUMMARY" | sed "s/\"successful_tests\": [0-9]*/\"successful_tests\": $SUCCESSFUL_TESTS/" | sed "s/\"total_profit\": [0-9.]*/\"total_profit\": $TOTAL_PROFIT/" > "$RESULTS_DIR/summary.json"
    
    # Add trade to trades array
    TRADE_JSON="{\"test\": $i, \"success\": $([ "$SUCCESS" -eq "1" ] && echo "true" || echo "false"), \"profit\": $PROFIT}"
    CURRENT_SUMMARY=$(cat "$RESULTS_DIR/summary.json")
    echo "$CURRENT_SUMMARY" | sed "s/\"trades\": \[/\"trades\": \[$TRADE_JSON,/" > "$RESULTS_DIR/summary.json"
    
    # Print progress
    echo "Test $i completed. Success: $([ "$SUCCESS" -eq "1" ] && echo "Yes" || echo "No"), Profit: \$$PROFIT"
    
    # Wait before next test
    if [ $i -lt $NUM_TESTS ]; then
        echo "Waiting $INTERVAL seconds before next test..."
        sleep $INTERVAL
    fi
done

# Stop monitoring
echo "Stopping monitoring..."
kill $MONITORING_PID

# Generate final report
echo "Generating final report..."
SUMMARY=$(cat "$RESULTS_DIR/summary.json")
TOTAL_TESTS=$(echo "$SUMMARY" | grep -o '"total_tests": [0-9]*' | awk '{print $2}')
SUCCESSFUL_TESTS=$(echo "$SUMMARY" | grep -o '"successful_tests": [0-9]*' | awk '{print $2}')
TOTAL_PROFIT=$(echo "$SUMMARY" | grep -o '"total_profit": [0-9.]*' | awk '{print $2}')
SUCCESS_RATE=$(echo "scale=2; $SUCCESSFUL_TESTS * 100 / $TOTAL_TESTS" | bc)
AVG_PROFIT=$(echo "scale=2; $TOTAL_PROFIT / $TOTAL_TESTS" | bc)

# Print summary
echo "=========================================================="
echo "  Test Summary"
echo "=========================================================="
echo "Total Tests: $TOTAL_TESTS"
echo "Successful Tests: $SUCCESSFUL_TESTS"
echo "Success Rate: $SUCCESS_RATE%"
echo "Total Profit: \$$TOTAL_PROFIT"
echo "Average Profit per Test: \$$AVG_PROFIT"
echo "=========================================================="
echo "Detailed report available at: $RESULTS_DIR/summary.json"

# Suggest next steps
echo ""
echo "Next steps:"
echo "1. Review the detailed metrics in $METRICS_DIR"
echo "2. Analyze the test report in $RESULTS_DIR"
echo "3. Check the log file for detailed information: $LOG_FILE"

echo ""
echo "Thank you for using ArbitrageX!" 