#!/bin/bash

# ArbitrageX Combined Strategy Runner
# This script runs the combined strategy that integrates both Layer 2 and Flash Loan enhancements

# Error handling
set -e
trap 'echo "Error occurred at line $LINENO. Command: $BASH_COMMAND"' ERR

# Configuration
CONFIG_DIR="backend/ai/config"
CONFIG_FILE="$CONFIG_DIR/combined_strategy.json"
TRADES=50
L2_ONLY=false
FLASH_ONLY=false
COMBINED_ONLY=false

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_DIR"

# Create default config file if it doesn't exist
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creating default configuration file at $CONFIG_FILE"
    cat > "$CONFIG_FILE" << EOF
{
    "trade_management": {
        "max_concurrent_trades": 5,
        "max_daily_trades": 100,
        "min_profit_threshold_usd": 10.0,
        "min_profit_percentage": 0.005
    },
    "risk_management": {
        "max_position_size_eth": 5.0,
        "max_gas_price_gwei": 50,
        "max_slippage_percentage": 1.0,
        "max_daily_loss_usd": 500
    },
    "combined_config": {
        "enable_l2": true,
        "enable_flash_loans": true,
        "prefer_l2": true,
        "prefer_flash_loans": true,
        "l2_flash_combined": true,
        "metrics_dir": "backend/ai/metrics/combined_optimized"
    },
    "l2_networks": {
        "arbitrum": {
            "enabled": true,
            "rpc_url": "https://arb1.arbitrum.io/rpc",
            "priority": 1
        },
        "optimism": {
            "enabled": true,
            "rpc_url": "https://mainnet.optimism.io",
            "priority": 2
        },
        "polygon": {
            "enabled": true,
            "rpc_url": "https://polygon-rpc.com",
            "priority": 3
        },
        "base": {
            "enabled": true,
            "rpc_url": "https://mainnet.base.org",
            "priority": 4
        }
    },
    "flash_loan_providers": {
        "aave": {
            "enabled": true,
            "fee_percentage": 0.09,
            "priority": 1
        },
        "uniswap": {
            "enabled": true,
            "fee_percentage": 0.3,
            "priority": 2
        },
        "balancer": {
            "enabled": true,
            "fee_percentage": 0.1,
            "priority": 3
        },
        "maker": {
            "enabled": true,
            "fee_percentage": 0.05,
            "priority": 4
        }
    }
}
EOF
fi

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --trades=*)
            TRADES="${1#*=}"
            shift
            ;;
        --l2-only)
            L2_ONLY=true
            shift
            ;;
        --flash-only)
            FLASH_ONLY=true
            shift
            ;;
        --combined-only)
            COMBINED_ONLY=true
            shift
            ;;
        --config=*)
            CONFIG_FILE="${1#*=}"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--trades=N] [--l2-only] [--flash-only] [--combined-only] [--config=path/to/config.json]"
            exit 1
            ;;
    esac
done

# Create metrics directory
mkdir -p "backend/ai/metrics/combined_optimized"

# Print banner
echo "========================================================"
echo "ArbitrageX Combined Strategy Runner"
echo "========================================================"
echo "Configuration file: $CONFIG_FILE"
echo "Number of trades to simulate: $TRADES"
if [ "$L2_ONLY" = true ]; then
    echo "Mode: Layer 2 only"
elif [ "$FLASH_ONLY" = true ]; then
    echo "Mode: Flash Loan only"
elif [ "$COMBINED_ONLY" = true ]; then
    echo "Mode: Combined L2 + Flash Loan only"
else
    echo "Mode: All strategies (Base, L2, Flash Loan, Combined)"
fi
echo "========================================================"

# Countdown
echo "Starting in 3 seconds..."
sleep 1
echo "2..."
sleep 1
echo "1..."
sleep 1
echo "Starting simulation..."

# Build command with appropriate flags
CMD="python backend/ai/optimized_strategy_combined.py --config $CONFIG_FILE --simulate --trades $TRADES"

if [ "$L2_ONLY" = true ]; then
    CMD="$CMD --l2-only"
elif [ "$FLASH_ONLY" = true ]; then
    CMD="$CMD --flash-only"
elif [ "$COMBINED_ONLY" = true ]; then
    CMD="$CMD --combined-only"
fi

# Run the simulation
echo "Executing: $CMD"
eval $CMD

# Check if simulation was successful
if [ $? -eq 0 ]; then
    echo "========================================================"
    echo "Simulation completed successfully!"
    echo "========================================================"
    echo "Next steps:"
    echo "1. Review metrics in backend/ai/metrics/combined_optimized/"
    echo "2. Adjust configuration in $CONFIG_FILE"
    echo "3. Run a longer simulation with more trades"
    echo "4. Deploy to production"
    echo "========================================================"
else
    echo "========================================================"
    echo "Simulation failed. Please check the logs for errors."
    echo "========================================================"
fi

echo "Thank you for using ArbitrageX!" 