#!/bin/bash
#
# ArbitrageX Extended Fork Test
#
# This script runs an extended test of the ArbitrageX bot on a forked mainnet,
# with enhanced monitoring and learning loop integration.
#

# Set up error handling
set -e
trap 'echo "Error occurred at line $LINENO. Command: $BASH_COMMAND"' ERR

# Configuration
TRADES=${1:-10}  # Default to 10 trades if not specified
INTERVAL=${2:-5}  # Default to 5 seconds between trades
METRICS_DIR="backend/ai/metrics/extended_test"
RESULTS_DIR="backend/ai/results/extended_test"
LOG_FILE="test_fork_trade_extended.log"

# Print banner
echo "=========================================================="
echo "  ArbitrageX Extended Fork Test"
echo "=========================================================="
echo "Trades: $TRADES"
echo "Interval between trades: $INTERVAL seconds"
echo "Metrics directory: $METRICS_DIR"
echo "Results directory: $RESULTS_DIR"
echo "Log file: $LOG_FILE"
echo "=========================================================="

# Create directories
mkdir -p "$METRICS_DIR"
mkdir -p "$RESULTS_DIR"

# Check if Python dependencies are installed
echo "Checking Python dependencies..."
pip install -q numpy pandas matplotlib tensorflow scikit-learn

# Check if Hardhat is installed
if ! command -v npx &> /dev/null; then
    echo "Error: npx command not found. Please install Node.js and npm."
    exit 1
fi

# Check if Hardhat is installed in the project
if [ ! -d "node_modules/hardhat" ]; then
    echo "Installing Hardhat..."
    npm install --save-dev hardhat
fi

# Check if fork configuration exists
if [ ! -f "backend/ai/hardhat_fork_config.json" ]; then
    echo "Error: Fork configuration file not found."
    exit 1
fi

# Start Hardhat node with forked mainnet
echo "Starting Hardhat node with forked mainnet..."
FORK_BLOCK=$(grep -o '"fork_block_number": "[^"]*"' backend/ai/hardhat_fork_config.json | cut -d'"' -f4)

# Start Hardhat node in the background
npx hardhat node --fork https://eth-mainnet.alchemyapi.io/v2/YOUR_ALCHEMY_KEY --fork-block-number $FORK_BLOCK > hardhat-node.log 2>&1 &
HARDHAT_PID=$!

# Wait for Hardhat node to start
echo "Waiting for Hardhat node to start..."
sleep 10

# Check if Hardhat node is running
if ! ps -p $HARDHAT_PID > /dev/null; then
    echo "Error: Hardhat node failed to start. Check hardhat-node.log for details."
    exit 1
fi

echo "Hardhat node started with PID $HARDHAT_PID"

# Start the test
echo "Starting extended fork test..."
echo "This will execute $TRADES trades with $INTERVAL seconds between trades."
echo ""
echo "Press Ctrl+C to stop the test at any time."
echo ""

# Run the test
python backend/ai/test_fork_trade_extended.py \
    --trades "$TRADES" \
    --interval "$INTERVAL" \
    --metrics-dir "$METRICS_DIR" \
    --results-dir "$RESULTS_DIR"

# Check if test completed successfully
TEST_EXIT_CODE=$?

# Stop Hardhat node
echo "Stopping Hardhat node..."
kill $HARDHAT_PID

# Check if test was successful
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "Test completed successfully!"
    
    # Generate summary report
    echo "Generating summary report..."
    REPORT_FILE="$RESULTS_DIR/test_report.json"
    
    if [ -f "$REPORT_FILE" ]; then
        echo "=========================================================="
        echo "  Test Summary"
        echo "=========================================================="
        
        # Extract key metrics from the report
        TOTAL_TRADES=$(grep -o '"total_trades": [0-9]*' "$REPORT_FILE" | awk '{print $2}')
        SUCCESSFUL_TRADES=$(grep -o '"successful_trades": [0-9]*' "$REPORT_FILE" | awk '{print $2}')
        SUCCESS_RATE=$(grep -o '"success_rate": [0-9.]*' "$REPORT_FILE" | awk '{print $2}')
        TOTAL_PROFIT=$(grep -o '"total_profit": [0-9.]*' "$REPORT_FILE" | awk '{print $2}')
        
        echo "Total Trades: $TOTAL_TRADES"
        echo "Successful Trades: $SUCCESSFUL_TRADES"
        echo "Success Rate: $SUCCESS_RATE%"
        echo "Total Profit: \$$TOTAL_PROFIT"
        echo "=========================================================="
        echo "Detailed report available at: $REPORT_FILE"
    else
        echo "Warning: Test report not found."
    fi
    
    # Suggest next steps
    echo ""
    echo "Next steps:"
    echo "1. Review the detailed metrics in $METRICS_DIR"
    echo "2. Analyze the test report in $RESULTS_DIR"
    echo "3. Check the log file for detailed information: $LOG_FILE"
else
    echo "Test failed. Check the log file for details: $LOG_FILE"
fi

echo ""
echo "Thank you for using ArbitrageX!" 