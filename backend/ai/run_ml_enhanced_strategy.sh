#!/bin/bash

# ArbitrageX ML-Enhanced Strategy Runner
# This script runs the ML-enhanced combined strategy with advanced machine learning models

# Error handling
set -e
trap 'echo "Error occurred at line $LINENO. Command: $BASH_COMMAND"' ERR

# Configuration
CONFIG_DIR="backend/ai/config"
CONFIG_FILE="$CONFIG_DIR/ml_enhanced_strategy.json"
TRADES=50
L2_ONLY=false
FLASH_ONLY=false
COMBINED_ONLY=false
ML_DISABLED=false

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
        "metrics_dir": "backend/ai/metrics/ml_enhanced"
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
    },
    "mev_protection": {
        "enabled": true,
        "default_method": "flashbots",
        "flashbots": {
            "relay_url": "https://relay.flashbots.net",
            "min_priority_fee_gwei": 1.5,
            "target_block_count": 3,
            "max_blocks_to_wait": 25
        },
        "transaction_bundling": {
            "enabled": true,
            "max_bundle_size": 4,
            "bundle_timeout_sec": 30
        },
        "simulation": {
            "enabled": true,
            "min_profit_threshold_after_mev": 0.5,
            "sandwich_attack_simulation": true,
            "skip_highly_vulnerable_trades": true
        },
        "fallback_to_public": false,
        "metrics_dir": "backend/ai/metrics/mev_protection"
    },
    "ml_config": {
        "enabled": true,
        "apply_price_impact": true,
        "apply_volatility": true,
        "apply_reinforcement_learning": true,
        "metrics_dir": "backend/ai/metrics/ml_enhanced"
    },
    "ml_models": {
        "reinforcement_learning": {
            "learning_rate": 0.001,
            "discount_factor": 0.95,
            "exploration_rate": 0.1,
            "min_exploration_rate": 0.01,
            "exploration_decay": 0.995
        },
        "price_impact": {
            "token_pairs": {
                "WETH-USDC": {"historical_impact_mean": 0.0015, "historical_impact_std": 0.0008},
                "WETH-DAI": {"historical_impact_mean": 0.0018, "historical_impact_std": 0.0010},
                "WBTC-USDC": {"historical_impact_mean": 0.0020, "historical_impact_std": 0.0012},
                "LINK-USDC": {"historical_impact_mean": 0.0025, "historical_impact_std": 0.0015}
            }
        },
        "volatility": {
            "lookback_periods": [1, 4, 24, 168],
            "volatility_thresholds": {
                "very_low": 0.01,
                "low": 0.025,
                "medium": 0.05,
                "high": 0.10,
                "very_high": 0.20
            }
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
        --ml-disabled)
            ML_DISABLED=true
            shift
            ;;
        --config=*)
            CONFIG_FILE="${1#*=}"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--trades=N] [--l2-only] [--flash-only] [--combined-only] [--ml-disabled] [--config=path/to/config.json]"
            exit 1
            ;;
    esac
done

# Create metrics directories
mkdir -p "backend/ai/metrics/ml_enhanced"
mkdir -p "backend/ai/metrics/mev_protection"
mkdir -p "backend/ai/models/reinforcement_learning"
mkdir -p "backend/ai/models/price_impact"
mkdir -p "backend/ai/models/volatility"

# Print banner
echo "========================================================"
echo "ArbitrageX ML-Enhanced Strategy Runner"
echo "========================================================"
echo "Configuration file: $CONFIG_FILE"
echo "Number of trades to simulate: $TRADES"
echo "ML Enhancements: $([ "$ML_DISABLED" = true ] && echo "Disabled" || echo "Enabled")"

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
echo ""
echo "This strategy combines:"
echo "1. Layer 2 integration for reduced gas costs"
echo "2. Flash Loan integration for capital efficiency"
echo "3. MEV protection to prevent front-running and sandwich attacks"
echo "4. Advanced ML models for strategy optimization:"
echo "   - Reinforcement Learning for execution method selection"
echo "   - Price Impact Prediction for slippage optimization"
echo "   - Volatility Tracking for position sizing and timing"
echo "========================================================"

# Countdown
echo "Starting in 3 seconds..."
sleep 1
echo "2..."
sleep 1
echo "1..."
sleep 1
echo "Starting ML-enhanced simulation..."

# Build command with appropriate flags
CMD="python backend/ai/ml_enhanced_strategy.py --config $CONFIG_FILE --simulate --trades $TRADES"

if [ "$L2_ONLY" = true ]; then
    CMD="$CMD --l2-only"
elif [ "$FLASH_ONLY" = true ]; then
    CMD="$CMD --flash-only"
elif [ "$COMBINED_ONLY" = true ]; then
    CMD="$CMD --combined-only"
fi

if [ "$ML_DISABLED" = true ]; then
    CMD="$CMD --ml-disabled"
fi

# Run the simulation
echo "Executing: $CMD"
eval $CMD

# Check if simulation was successful
if [ $? -eq 0 ]; then
    echo "========================================================"
    echo "ML-Enhanced Simulation completed successfully!"
    echo "========================================================"
    echo "Next steps:"
    echo "1. Review metrics in backend/ai/metrics/ml_enhanced/"
    echo "2. Review ML model metrics in backend/ai/metrics/ml_enhanced/"
    echo "3. Adjust configuration in $CONFIG_FILE"
    echo "4. Run a longer simulation with more trades"
    echo "5. Deploy to production with real ML models"
    echo "========================================================"
else
    echo "========================================================"
    echo "Simulation failed. Please check the logs for errors."
    echo "========================================================"
fi

echo "Thank you for using ArbitrageX!" 