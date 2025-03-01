#!/bin/bash
# ArbitrageX Mainnet Fork Test Runner
# This script runs the mainnet fork test with common options.

# Default values
MODULES="strategy_optimizer,backtesting,trade_analyzer,network_adaptation,integration"
RUN_TIME=300
BLOCK_NUMBER="latest"
VISUALIZE=true
SAVE_RESULTS=true

# Display help message
function show_help {
    echo "ArbitrageX Mainnet Fork Test Runner"
    echo "Usage: ./run_mainnet_fork.sh [options]"
    echo ""
    echo "Options:"
    echo "  --modules <list>     Comma-separated list of modules to run"
    echo "                       Default: $MODULES"
    echo "  --run-time <secs>    How long to run the integration module (in seconds)"
    echo "                       Default: $RUN_TIME"
    echo "  --block <number>     Block number to fork from (default: latest)"
    echo "  --no-visualize       Disable visualization"
    echo "  --no-save-results    Disable saving results"
    echo "  --help               Display this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_mainnet_fork.sh"
    echo "  ./run_mainnet_fork.sh --modules strategy_optimizer,backtesting"
    echo "  ./run_mainnet_fork.sh --run-time 600"
    echo "  ./run_mainnet_fork.sh --block 12345678"
    exit 0
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --modules)
            MODULES="$2"
            shift 2
            ;;
        --run-time)
            RUN_TIME="$2"
            shift 2
            ;;
        --block)
            BLOCK_NUMBER="$2"
            shift 2
            ;;
        --no-visualize)
            VISUALIZE=false
            shift
            ;;
        --no-save-results)
            SAVE_RESULTS=false
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            ;;
    esac
done

# Build command
CMD="python3 run_mainnet_fork_test.py --block-number $BLOCK_NUMBER --modules $MODULES --run-time $RUN_TIME"

if [ "$VISUALIZE" = false ]; then
    CMD="$CMD --no-visualize"
fi

if [ "$SAVE_RESULTS" = false ]; then
    CMD="$CMD --no-save-results"
fi

# Display command
echo "Running command: $CMD"
echo ""

# Run command
eval $CMD 