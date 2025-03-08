#!/bin/bash
#
# ArbitrageX Flash Loan-Enhanced Strategy Runner
#
# This script runs the optimized trading strategy with Flash Loan integration
# to enable capital-efficient trading without requiring substantial upfront capital.
#

# Set up error handling
set -e
trap 'echo "Error occurred at line $LINENO. Command: $BASH_COMMAND"' ERR

# Configuration
CONFIG_DIR="backend/ai/config"
CONFIG_FILE="${CONFIG_DIR}/flash_strategy.json"
TRADES=${1:-50}  # Default to 50 trades if not specified
FLASH_ONLY=${2:-false}  # Default to using both base and flash loan strategies

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_DIR"

# Create default configuration if it doesn't exist
if [ ! -f "$CONFIG_FILE" ]; then
  echo "Creating default Flash Loan configuration file..."
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
  "flash_config": {
    "enable_flash_loans": true,
    "prefer_flash_loans": true,
    "min_profit_multiplier": 1.5,
    "flash_metrics_dir": "backend/ai/metrics/flash_optimized",
    "providers": {
      "aave": {
        "enabled": true,
        "fee_percentage": 0.0009
      },
      "uniswap": {
        "enabled": true,
        "fee_percentage": 0.0005
      },
      "balancer": {
        "enabled": true,
        "fee_percentage": 0.0006
      }
    }
  }
}
EOF
  echo "Default Flash Loan configuration created at $CONFIG_FILE"
fi

# Print banner
echo "=========================================================="
echo "  ArbitrageX Flash Loan-Enhanced Optimized Strategy"
echo "=========================================================="
echo "Configuration: $CONFIG_FILE"
echo "Trades to simulate: $TRADES"
echo "Flash Loan Only: $FLASH_ONLY"
echo "=========================================================="
echo ""
echo "This strategy implements Flash Loan integration to enable"
echo "capital-efficient trading, including:"
echo "  - Aave, Uniswap, and Balancer flash loan support"
echo "  - Automatic provider selection based on fees"
echo "  - Dynamic position sizing with flash loans"
echo "  - 3-5x capital efficiency without additional funds"
echo ""
echo "Starting in 3 seconds..."
sleep 3

# Build flash only flag if needed
FLASH_ONLY_FLAG=""
if [ "$FLASH_ONLY" = "true" ]; then
  FLASH_ONLY_FLAG="--flash-only"
fi

# Run the Flash Loan-enhanced optimized strategy
python backend/ai/optimized_strategy_flash.py --config "$CONFIG_FILE" --simulate --trades "$TRADES" $FLASH_ONLY_FLAG

# Check if simulation completed successfully
if [ $? -eq 0 ]; then
  echo ""
  echo "=========================================================="
  echo "  Next Steps"
  echo "=========================================================="
  echo ""
  echo "1. Review the Flash Loan metrics in backend/ai/metrics/flash_optimized/"
  echo "2. Adjust Flash Loan configuration in $CONFIG_FILE"
  echo "3. Run a longer simulation with more trades:"
  echo "   ./backend/ai/run_flash_strategy.sh 200 true"
  echo ""
  echo "For production deployment, remove the --simulate flag in the script"
  echo "and implement the actual trade execution logic."
else
  echo "Simulation failed. Check the log file for details: optimized_strategy_flash.log"
fi

echo ""
echo "Thank you for using ArbitrageX!" 