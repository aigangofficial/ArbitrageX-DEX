#!/bin/bash
#
# ArbitrageX Optimized Strategy Runner
#
# This script runs the optimized trading strategy with improved gas optimization,
# risk management, and profit thresholds based on the 3-month simulation analysis.
#

# Set up error handling
set -e
trap 'echo "Error occurred at line $LINENO. Command: $BASH_COMMAND"' ERR

# Configuration
CONFIG_DIR="backend/ai/config"
CONFIG_FILE="${CONFIG_DIR}/optimized_strategy.json"
TRADES=${1:-50}  # Default to 50 trades if not specified

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_DIR"

# Create default configuration if it doesn't exist
if [ ! -f "$CONFIG_FILE" ]; then
  echo "Creating default configuration file..."
  cat > "$CONFIG_FILE" << EOF
{
  "max_concurrent_trades": 3,
  "min_opportunity_score": 1.2,
  "enable_batch_execution": true,
  "enable_circuit_breakers": true,
  "enable_dynamic_position_sizing": true,
  "metrics_save_interval": 1800
}
EOF
  echo "Default configuration created at $CONFIG_FILE"
fi

# Print banner
echo "=========================================================="
echo "  ArbitrageX Optimized Strategy"
echo "=========================================================="
echo "Configuration: $CONFIG_FILE"
echo "Trades to simulate: $TRADES"
echo "=========================================================="
echo ""
echo "This strategy implements the improvements identified in the"
echo "3-month simulation analysis, including:"
echo "  - Gas optimization with predictive pricing"
echo "  - Dynamic position sizing based on token pair performance"
echo "  - Circuit breakers to limit losses"
echo "  - Specialized strategies for high-performing token pairs"
echo ""
echo "Starting in 3 seconds..."
sleep 3

# Run the optimized strategy
python backend/ai/optimized_strategy.py --config "$CONFIG_FILE" --simulate --trades "$TRADES"

# Check if simulation completed successfully
if [ $? -eq 0 ]; then
  echo ""
  echo "=========================================================="
  echo "  Next Steps"
  echo "=========================================================="
  echo ""
  echo "1. Review the metrics in backend/ai/metrics/optimized/"
  echo "2. Adjust configuration in $CONFIG_FILE"
  echo "3. Run a longer simulation with more trades:"
  echo "   ./backend/ai/run_optimized_strategy.sh 200"
  echo ""
  echo "For production deployment, remove the --simulate flag in the script"
  echo "and implement the actual trade execution logic."
else
  echo "Simulation failed. Check the log file for details: optimized_strategy.log"
fi

echo ""
echo "Thank you for using ArbitrageX!" 