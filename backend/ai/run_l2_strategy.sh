#!/bin/bash
#
# ArbitrageX L2-Enhanced Strategy Runner
#
# This script runs the optimized trading strategy with Layer 2 integration
# to dramatically reduce gas costs and improve profitability.
#

# Set up error handling
set -e
trap 'echo "Error occurred at line $LINENO. Command: $BASH_COMMAND"' ERR

# Configuration
CONFIG_DIR="backend/ai/config"
CONFIG_FILE="${CONFIG_DIR}/l2_strategy.json"
TRADES=${1:-50}  # Default to 50 trades if not specified
L2_ONLY=${2:-false}  # Default to using both L1 and L2

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_DIR"

# Create default configuration if it doesn't exist
if [ ! -f "$CONFIG_FILE" ]; then
  echo "Creating default L2 configuration file..."
  cat > "$CONFIG_FILE" << EOF
{
  "max_concurrent_trades": 3,
  "min_opportunity_score": 1.0,
  "enable_batch_execution": true,
  "enable_circuit_breakers": true,
  "enable_dynamic_position_sizing": true,
  "metrics_save_interval": 1800,
  "gas_price_threshold": 30,
  "min_profit_threshold": 0.005,
  "max_slippage": 0.02,
  "risk_management": {
    "max_daily_loss": 200.0,
    "max_consecutive_losses": 8,
    "position_size_base": 0.5,
    "circuit_breaker_timeout": 1800,
    "success_rate_threshold": 0.5
  },
  "l2_config": {
    "enable_l2": true,
    "prefer_l2": true,
    "l2_networks": [
      "arbitrum",
      "optimism",
      "base",
      "polygon"
    ],
    "l2_metrics_dir": "backend/ai/metrics/l2_optimized"
  }
}
EOF
  echo "Default L2 configuration created at $CONFIG_FILE"
fi

# Print banner
echo "=========================================================="
echo "  ArbitrageX L2-Enhanced Optimized Strategy"
echo "=========================================================="
echo "Configuration: $CONFIG_FILE"
echo "Trades to simulate: $TRADES"
echo "L2 Only: $L2_ONLY"
echo "=========================================================="
echo ""
echo "This strategy implements Layer 2 integration to dramatically"
echo "reduce gas costs and improve profitability, including:"
echo "  - Arbitrum, Optimism, Base, and Polygon support"
echo "  - Automatic network selection based on gas costs"
echo "  - Cross-layer arbitrage opportunities"
echo "  - 90-95% gas cost reduction compared to L1"
echo ""
echo "Starting in 3 seconds..."
sleep 3

# Build L2 only flag if needed
L2_ONLY_FLAG=""
if [ "$L2_ONLY" = "true" ]; then
  L2_ONLY_FLAG="--l2-only"
fi

# Run the L2-enhanced optimized strategy
python backend/ai/optimized_strategy_l2.py --config "$CONFIG_FILE" --simulate --trades "$TRADES" $L2_ONLY_FLAG

# Check if simulation completed successfully
if [ $? -eq 0 ]; then
  echo ""
  echo "=========================================================="
  echo "  Next Steps"
  echo "=========================================================="
  echo ""
  echo "1. Review the L2 metrics in backend/ai/metrics/l2_optimized/"
  echo "2. Adjust L2 configuration in $CONFIG_FILE"
  echo "3. Run a longer simulation with more trades:"
  echo "   ./backend/ai/run_l2_strategy.sh 200 true"
  echo ""
  echo "For production deployment, remove the --simulate flag in the script"
  echo "and implement the actual trade execution logic."
else
  echo "Simulation failed. Check the log file for details: optimized_strategy_l2.log"
fi

echo ""
echo "Thank you for using ArbitrageX!" 