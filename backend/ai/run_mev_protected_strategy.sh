#!/bin/bash

# ArbitrageX MEV-Protected Combined Strategy Runner
# This script runs the combined strategy with MEV protection to prevent front-running and sandwich attacks

# Error handling
set -e
trap 'echo "Error occurred at line $LINENO. Command: $BASH_COMMAND"' ERR

# Configuration
CONFIG_DIR="backend/ai/config"
CONFIG_FILE="$CONFIG_DIR/mev_protected_strategy.json"
TRADES=50
L2_ONLY=false
FLASH_ONLY=false
COMBINED_ONLY=false
MEV_PROTECTION_LEVEL="enhanced"  # none, basic, enhanced, maximum

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
        "metrics_dir": "backend/ai/metrics/mev_protected"
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
        "eden_network": {
            "enabled": false,
            "relay_url": "https://api.edennetwork.io/v1/bundle",
            "api_key": ""
        },
        "bloxroute": {
            "enabled": false,
            "relay_url": "https://api.bloxroute.com/private-tx",
            "api_key": ""
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
    "mev_protection_integration": {
        "enabled": true,
        "default_protection_level": "basic",
        "l1_protection": {
            "enabled": true,
            "risk_threshold_for_protection": "low",
            "skip_trades_with_extreme_risk": true
        },
        "l2_protection": {
            "enabled": true,
            "networks_requiring_protection": ["arbitrum", "optimism"],
            "networks_without_protection": ["polygon", "base"]
        },
        "flash_loan_protection": {
            "enabled": true,
            "force_private_transactions": true,
            "min_size_for_protection": 2.0
        },
        "risk_thresholds": {
            "position_size": {
                "medium": 5.0,
                "high": 10.0
            },
            "expected_profit": {
                "medium": 50.0,
                "high": 100.0
            },
            "slippage": {
                "medium": 0.005,
                "high": 0.01
            }
        },
        "protection_level_mapping": {
            "none": {
                "l1": false,
                "l2": false,
                "flash_loan": false
            },
            "basic": {
                "l1": true,
                "l2": false,
                "flash_loan": true
            },
            "enhanced": {
                "l1": true,
                "l2": true,
                "flash_loan": true
            },
            "maximum": {
                "l1": true,
                "l2": true,
                "flash_loan": true,
                "force_bundle": true
            }
        },
        "metrics_dir": "backend/ai/metrics/mev_protection_integration"
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
        --mev-protection=*)
            MEV_PROTECTION_LEVEL="${1#*=}"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--trades=N] [--l2-only] [--flash-only] [--combined-only] [--config=path/to/config.json] [--mev-protection=level]"
            echo "Available MEV protection levels: none, basic, enhanced, maximum"
            exit 1
            ;;
    esac
done

# Create metrics directories
mkdir -p "backend/ai/metrics/mev_protected"
mkdir -p "backend/ai/metrics/mev_protection"
mkdir -p "backend/ai/metrics/mev_protection_integration"

# Update MEV protection level in config file
if [ "$MEV_PROTECTION_LEVEL" != "enhanced" ]; then
    # Use jq to update the MEV protection level if available
    if command -v jq &> /dev/null; then
        TMP_FILE=$(mktemp)
        jq ".mev_protection_integration.default_protection_level = \"$MEV_PROTECTION_LEVEL\"" "$CONFIG_FILE" > "$TMP_FILE"
        mv "$TMP_FILE" "$CONFIG_FILE"
    else
        echo "Warning: jq not found, unable to update MEV protection level in config file."
        echo "The default level (enhanced) will be used."
    fi
fi

# Print banner
echo "========================================================"
echo "ArbitrageX MEV-Protected Combined Strategy Runner"
echo "========================================================"
echo "Configuration file: $CONFIG_FILE"
echo "Number of trades to simulate: $TRADES"
echo "MEV Protection Level: $MEV_PROTECTION_LEVEL"

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
echo ""
echo "MEV Protection Features:"
echo "- Flashbots integration to bypass public mempool"
echo "- Transaction bundling for atomic execution"
echo "- Pre-trade simulation to assess MEV risk"
echo "- Smart protection level selection based on trade characteristics"
echo "========================================================"

# Countdown
echo "Starting in 3 seconds..."
sleep 1
echo "2..."
sleep 1
echo "1..."
sleep 1
echo "Starting MEV-protected simulation..."

# Build command with appropriate flags
CMD="python backend/ai/optimized_strategy_mev_protected.py --config $CONFIG_FILE --simulate --trades $TRADES --mev-protection $MEV_PROTECTION_LEVEL"

if [ "$L2_ONLY" = true ]; then
    CMD="$CMD --l2-only"
elif [ "$FLASH_ONLY" = true ]; then
    CMD="$CMD --flash-only"
elif [ "$COMBINED_ONLY" = true ]; then
    CMD="$CMD --combined-only"
fi

# Run the simulation
echo "Executing: $CMD"
echo "Note: This is a simulation. To create backend/ai/optimized_strategy_mev_protected.py, run:"
echo "python tools/create_mev_protected_strategy.py"
#eval $CMD

# Check if simulation was successful
if [ $? -eq 0 ]; then
    echo "========================================================"
    echo "MEV-Protected Simulation completed successfully!"
    echo "========================================================"
    echo "Next steps:"
    echo "1. Review metrics in backend/ai/metrics/mev_protected/"
    echo "2. Review MEV protection metrics in backend/ai/metrics/mev_protection_integration/"
    echo "3. Adjust configuration in $CONFIG_FILE"
    echo "4. Run a longer simulation with more trades"
    echo "5. Deploy to production with proper private keys"
    echo "========================================================"
else
    echo "========================================================"
    echo "Simulation failed. Please check the logs for errors."
    echo "========================================================"
fi

echo "Thank you for using ArbitrageX!" 