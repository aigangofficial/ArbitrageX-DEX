#!/bin/bash
# ArbitrageX AI System Runner
# This script runs the entire ArbitrageX AI system with a single command.

# Default values
TESTNET=true
VISUALIZE=false
SAVE_RESULTS=false
DAYS=30
MODULES="all"
RUN_TIME=60
FORK_CONFIG=""

# Display help message
function show_help {
    echo "ArbitrageX AI System Runner"
    echo "Usage: ./run_ai_system.sh [options]"
    echo ""
    echo "Options:"
    echo "  --mainnet           Run in mainnet mode (default: testnet)"
    echo "  --visualize         Enable visualization for modules that support it"
    echo "  --save-results      Save results to files"
    echo "  --days <number>     Number of days for historical data (default: 30)"
    echo "  --run-time <secs>   How long to run integration module (default: 60)"
    echo "  --modules <list>    Comma-separated list of modules to run (default: all)"
    echo "                      Available modules: strategy_optimizer, backtesting,"
    echo "                      trade_analyzer, network_adaptation, test_ai_model, integration"
    echo "  --fork-config <file> Path to fork configuration file for mainnet fork mode"
    echo "  --help              Display this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_ai_system.sh --visualize"
    echo "  ./run_ai_system.sh --modules strategy_optimizer,backtesting"
    echo "  ./run_ai_system.sh --modules integration --run-time 300"
    echo "  ./run_ai_system.sh --mainnet --save-results --days 60"
    echo "  ./run_ai_system.sh --modules integration --fork-config fork_config.json"
    exit 0
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --mainnet)
            TESTNET=false
            shift
            ;;
        --visualize)
            VISUALIZE=true
            shift
            ;;
        --save-results)
            SAVE_RESULTS=true
            shift
            ;;
        --days)
            DAYS="$2"
            shift 2
            ;;
        --run-time)
            RUN_TIME="$2"
            shift 2
            ;;
        --modules)
            MODULES="$2"
            shift 2
            ;;
        --fork-config)
            FORK_CONFIG="$2"
            shift 2
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

# Determine mode
if [ -n "$FORK_CONFIG" ]; then
    MODE="MAINNET FORK"
elif [ "$TESTNET" = true ]; then
    MODE="TESTNET"
else
    MODE="MAINNET"
fi

# Check if we're running the integration module directly
if [[ "$MODULES" == "integration" ]]; then
    # Build integration command
    CMD="python3 ai_integration.py"
    
    if [ "$TESTNET" = true ]; then
        CMD="$CMD --testnet"
    fi
    
    CMD="$CMD --run-time $RUN_TIME"
    
    # Add fork configuration if provided
    if [ -n "$FORK_CONFIG" ]; then
        CMD="$CMD --fork-config $FORK_CONFIG"
    fi
    
    # Display command
    echo "Running integration module: $CMD"
    echo ""
    echo "Mode: $MODE"
    echo ""
    
    # Run command
    eval $CMD
else
    # Build command for run_all_ai_modules.py
    CMD="python3 run_all_ai_modules.py"
    
    if [ "$TESTNET" = true ]; then
        CMD="$CMD --testnet"
    fi
    
    if [ "$VISUALIZE" = true ]; then
        CMD="$CMD --visualize"
    fi
    
    if [ "$SAVE_RESULTS" = true ]; then
        CMD="$CMD --save-results"
    fi
    
    CMD="$CMD --days $DAYS --modules $MODULES --run-time $RUN_TIME"
    
    # Add fork configuration if provided
    if [ -n "$FORK_CONFIG" ]; then
        CMD="$CMD --fork-config $FORK_CONFIG"
    fi
    
    # Display command
    echo "Running command: $CMD"
    echo ""
    echo "Mode: $MODE"
    echo ""
    
    # Run command
    eval $CMD
fi 