#!/bin/bash
#
# ArbitrageX Week-Long Simulation Runner
#
# This script sets up and runs a week-long simulation of the ArbitrageX bot
# on a forked mainnet, with enhanced monitoring and learning loop integration.
#

# Set up error handling
set -e
trap 'echo "Error occurred at line $LINENO. Command: $BASH_COMMAND"' ERR

# Configuration
DAYS=${1:-7}  # Default to 7 days if not specified
TRADES_PER_DAY=${2:-24}  # Default to 24 trades per day
LEARNING_INTERVAL=${3:-4}  # Default to 4 hours
METRICS_DIR="backend/ai/metrics/week_simulation"
RESULTS_DIR="backend/ai/results/week_simulation"
LOG_FILE="week_simulation.log"

# Print banner
echo "=========================================================="
echo "  ArbitrageX Week-Long Simulation on Forked Mainnet"
echo "=========================================================="
echo "Days: $DAYS"
echo "Trades per day: $TRADES_PER_DAY"
echo "Learning interval: $LEARNING_INTERVAL hours"
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

# Start the simulation
echo "Starting week-long simulation..."
echo "This will simulate $DAYS days of trading with $TRADES_PER_DAY trades per day."
echo "The learning loop will run every $LEARNING_INTERVAL hours."
echo ""
echo "Press Ctrl+C to stop the simulation at any time."
echo ""

# Run the simulation
python backend/ai/run_week_simulation.py \
    --days "$DAYS" \
    --trades-per-day "$TRADES_PER_DAY" \
    --learning-interval "$LEARNING_INTERVAL" \
    --metrics-dir "$METRICS_DIR" \
    --results-dir "$RESULTS_DIR"

# Check if simulation completed successfully
if [ $? -eq 0 ]; then
    echo "Simulation completed successfully!"
    
    # Generate summary report
    echo "Generating summary report..."
    REPORT_FILE="$RESULTS_DIR/simulation_report.json"
    
    if [ -f "$REPORT_FILE" ]; then
        echo "=========================================================="
        echo "  Simulation Summary"
        echo "=========================================================="
        
        # Extract key metrics from the report
        TOTAL_TRADES=$(grep -o '"total_trades": [0-9]*' "$REPORT_FILE" | awk '{print $2}')
        SUCCESS_RATE=$(grep -o '"success_rate": [0-9.]*' "$REPORT_FILE" | awk '{print $2}')
        TOTAL_PROFIT=$(grep -o '"total_profit": [0-9.]*' "$REPORT_FILE" | awk '{print $2}')
        AVG_PROFIT=$(grep -o '"average_profit_per_day": [0-9.]*' "$REPORT_FILE" | awk '{print $2}')
        MODEL_UPDATES=$(grep -o '"total_model_updates": [0-9]*' "$REPORT_FILE" | awk '{print $2}')
        STRATEGY_ADAPTATIONS=$(grep -o '"total_strategy_adaptations": [0-9]*' "$REPORT_FILE" | awk '{print $2}')
        PREDICTION_ACCURACY=$(grep -o '"average_prediction_accuracy": [0-9.]*' "$REPORT_FILE" | awk '{print $2}')
        
        echo "Total Trades: $TOTAL_TRADES"
        echo "Success Rate: $SUCCESS_RATE%"
        echo "Total Profit: \$$TOTAL_PROFIT"
        echo "Average Profit per Day: \$$AVG_PROFIT"
        echo "Total Model Updates: $MODEL_UPDATES"
        echo "Total Strategy Adaptations: $STRATEGY_ADAPTATIONS"
        echo "Average Prediction Accuracy: $PREDICTION_ACCURACY%"
        echo "=========================================================="
        echo "Detailed report available at: $REPORT_FILE"
    else
        echo "Warning: Simulation report not found."
    fi
    
    # Suggest next steps
    echo ""
    echo "Next steps:"
    echo "1. Review the detailed metrics in $METRICS_DIR"
    echo "2. Analyze the simulation report in $RESULTS_DIR"
    echo "3. Check the log file for detailed information: $LOG_FILE"
else
    echo "Simulation failed. Check the log file for details: $LOG_FILE"
fi

echo ""
echo "Thank you for using ArbitrageX!" 