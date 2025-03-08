#!/bin/bash

# ArbitrageX Master Runner
# This script kills any existing ArbitrageX processes and starts the complete trading bot with all enhancements

# Set strict error handling
set -e
trap 'echo "Error occurred at line $LINENO. Command: $BASH_COMMAND"' ERR

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print a colorful banner
print_banner() {
    echo -e "${BLUE}"
    echo "    _          _     _ _                       __   __"
    echo "   / \\   _ __ | |__ (_) |_ _ __ __ _  __ _  __\\ \\ / /"
    echo "  / _ \\ | '_ \\| '_ \\| | __| '__/ _\` |/ _\` |/ _ \\ V / "
    echo " / ___ \\| |_) | |_) | | |_| | | (_| | (_| |  __/| |  "
    echo "/_/   \\_\\ .__/|_.__/|_|\\__|_|  \\__,_|\\__, |\\___||_|  "
    echo "        |_|                          |___/           "
    echo -e "${NC}"
    echo -e "${GREEN}Complete Trading Bot with All Enhancements${NC}"
    echo "======================================================"
}

# Kill existing ArbitrageX processes
kill_existing() {
    echo -e "${YELLOW}Checking for existing ArbitrageX processes...${NC}"
    
    # Find any python processes running ArbitrageX scripts
    PIDS=$(ps aux | grep -E "python.*backend/ai/.*_strategy.py" | grep -v grep | awk '{print $2}')
    
    if [ -n "$PIDS" ]; then
        echo -e "${YELLOW}Found existing ArbitrageX processes. Terminating...${NC}"
        for PID in $PIDS; do
            echo "Killing process $PID"
            kill -9 $PID 2>/dev/null || true
        done
        echo -e "${GREEN}All existing ArbitrageX processes terminated.${NC}"
    else
        echo -e "${GREEN}No existing ArbitrageX processes found.${NC}"
    fi
    
    echo "======================================================"
}

# Create required directories
setup_directories() {
    echo -e "${YELLOW}Setting up directories...${NC}"
    
    mkdir -p backend/ai/config
    mkdir -p backend/ai/metrics/ml_enhanced
    mkdir -p backend/ai/metrics/mev_protection
    mkdir -p backend/ai/metrics/l2
    mkdir -p backend/ai/metrics/flash_loan
    mkdir -p backend/ai/metrics/combined
    mkdir -p backend/ai/models/reinforcement_learning
    mkdir -p backend/ai/models/price_impact
    mkdir -p backend/ai/models/volatility
    
    # Create logs directory
    mkdir -p backend/ai/logs
    
    # Create log file if it doesn't exist
    LOG_FILE="backend/ai/logs/arbitragex.log"
    if [ ! -f "$LOG_FILE" ]; then
        echo "Creating log file: $LOG_FILE"
        touch "$LOG_FILE"
        echo "$(date) - ArbitrageX log file created" >> "$LOG_FILE"
    fi
    
    echo -e "${GREEN}All required directories created.${NC}"
    echo "======================================================"
}

# Main function to run the ArbitrageX trading bot
run_arbitragex() {
    # Parse command line arguments
    TRADES=50
    SIMULATION_MODE=true
    ML_DISABLED=false
    L2_ONLY=false
    FLASH_ONLY=false
    COMBINED_ONLY=false
    MEV_DISABLED=false
    CONFIG_FILE="backend/ai/config/ml_enhanced_strategy.json"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --trades=*)
                TRADES="${1#*=}"
                shift
                ;;
            --no-simulation)
                SIMULATION_MODE=false
                shift
                ;;
            --ml-disabled)
                ML_DISABLED=true
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
            --mev-disabled)
                MEV_DISABLED=true
                shift
                ;;
            --config=*)
                CONFIG_FILE="${1#*=}"
                shift
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                echo "Usage: $0 [--trades=N] [--no-simulation] [--ml-disabled] [--l2-only] [--flash-only] [--combined-only] [--mev-disabled] [--config=path/to/config.json]"
                exit 1
                ;;
        esac
    done
    
    # Make shell scripts executable if they aren't already
    echo -e "${YELLOW}Ensuring all scripts are executable...${NC}"
    chmod +x backend/ai/run_ml_enhanced_strategy.sh
    chmod +x backend/ai/run_mev_protected_strategy.sh
    chmod +x backend/ai/run_flash_strategy.sh
    chmod +x backend/ai/run_l2_strategy.sh
    chmod +x backend/ai/advanced_ml_models.py
    chmod +x backend/ai/ml_enhanced_strategy.py
    
    # Log startup information
    LOG_FILE="backend/ai/logs/arbitragex.log"
    echo "$(date) - Starting ArbitrageX with trades=$TRADES simulation=$SIMULATION_MODE" >> "$LOG_FILE"
    
    # Build command with flags
    CMD="backend/ai/run_ml_enhanced_strategy.sh --trades=$TRADES"
    
    if [ "$L2_ONLY" = true ]; then
        CMD="$CMD --l2-only"
        echo "$(date) - L2 only mode enabled" >> "$LOG_FILE"
    elif [ "$FLASH_ONLY" = true ]; then
        CMD="$CMD --flash-only"
        echo "$(date) - Flash loan only mode enabled" >> "$LOG_FILE"
    elif [ "$COMBINED_ONLY" = true ]; then
        CMD="$CMD --combined-only"
        echo "$(date) - Combined mode only enabled" >> "$LOG_FILE"
    fi
    
    if [ "$ML_DISABLED" = true ]; then
        CMD="$CMD --ml-disabled"
        echo "$(date) - ML enhancements disabled" >> "$LOG_FILE"
    fi
    
    if [ "$MEV_DISABLED" = true ]; then
        # We'll pass this to the Python script directly
        export ARBITRAGEX_MEV_DISABLED=true
        echo "$(date) - MEV protection disabled" >> "$LOG_FILE"
    fi
    
    if [ "$SIMULATION_MODE" = false ]; then
        # In non-simulation mode, we'll use real API keys and connect to actual networks
        echo -e "${RED}WARNING: Running in non-simulation mode with real connections${NC}"
        export ARBITRAGEX_SIMULATION=false
        echo "$(date) - PRODUCTION MODE - Using real connections and funds" >> "$LOG_FILE"
    else
        export ARBITRAGEX_SIMULATION=true
    fi
    
    CMD="$CMD --config=$CONFIG_FILE"
    
    # Start ArbitrageX
    echo -e "${YELLOW}Starting ArbitrageX with command: ${CMD}${NC}"
    echo "======================================================"
    
    # Run the command
    ./$CMD
    
    # Check if it was successful
    if [ $? -eq 0 ]; then
        echo "======================================================"
        echo -e "${GREEN}ArbitrageX started successfully!${NC}"
        echo "======================================================"
        echo "The trading bot is now running."
        echo "To monitor logs, check: tail -f backend/ai/logs/arbitragex.log"
        echo "To stop all ArbitrageX processes, run: ./kill_arbitragex.sh"
        echo "======================================================"
        
        # Log success
        echo "$(date) - ArbitrageX started successfully" >> "$LOG_FILE"
    else
        echo "======================================================"
        echo -e "${RED}Failed to start ArbitrageX. Check logs for errors.${NC}"
        echo "======================================================"
        
        # Log failure
        echo "$(date) - ERROR: Failed to start ArbitrageX" >> "$LOG_FILE"
    fi
}

# Main execution
print_banner
kill_existing
setup_directories
run_arbitragex "$@" 