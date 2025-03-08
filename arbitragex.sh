#!/bin/bash

# ArbitrageX Unified Command
# This script provides a single entry point for all ArbitrageX functionality

# Set strict error handling
set -e
trap 'echo "Error occurred at line $LINENO. Command: $BASH_COMMAND"' ERR

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print usage information
print_usage() {
    echo -e "${CYAN}ArbitrageX Trading Bot - Unified Command${NC}"
    echo ""
    echo "Usage: ./arbitragex.sh [command] [options]"
    echo ""
    echo "Commands:"
    echo "  start       Start the ArbitrageX trading bot"
    echo "  stop        Stop all ArbitrageX processes"
    echo "  restart     Restart the ArbitrageX trading bot"
    echo "  status      Check the status of ArbitrageX processes"
    echo "  logs        Show the logs from the ArbitrageX trading bot"
    echo "  cleanup     Clean up temporary files and logs"
    echo "  backtest    Run backtests on different strategies"
    echo "  security    Manage security features (key storage, hardware wallets, etc.)"
    echo "  notify      Manage notification settings and send test notifications"
    echo "  dashboard   Manage the web dashboard"
    echo ""
    echo "Options for 'start' command:"
    echo "  --trades=N              Number of trades to simulate (default: 50)"
    echo "  --no-simulation         Run with real connections (WARNING: Uses real funds!)"
    echo "  --ml-disabled           Disable machine learning enhancements"
    echo "  --l2-only               Only use Layer 2 networks for execution"
    echo "  --flash-only            Only use Flash Loans for execution"
    echo "  --combined-only         Only use the combined L2 + Flash Loan execution"
    echo "  --mev-disabled          Disable MEV protection"
    echo "  --config=PATH           Specify a custom configuration file"
    echo ""
    echo "Options for 'logs' command:"
    echo "  --follow                Follow log output (like 'tail -f')"
    echo "  --lines=N               Show last N lines (default: 50)"
    echo ""
    echo "Options for 'backtest' command:"
    echo "  --strategy=NAME         Trading strategy to backtest (base, l2, flash, combined, mev_protected, ml_enhanced)"
    echo "  --start-date=DATE       Start date in YYYY-MM-DD format"
    echo "  --end-date=DATE         End date in YYYY-MM-DD format"
    echo "  --initial-capital=N     Initial capital in ETH (default: 10.0)"
    echo "  --days=N                Number of days to backtest (default: 90)"
    echo "  --compare-all           Compare all strategies"
    echo "  --generate-config       Generate a default config for the specified strategy"
    echo ""
    echo "Options for 'security' command:"
    echo "  store-key               Store a private key securely"
    echo "  validate-tx             Validate a transaction"
    echo "  sign-tx                 Sign a transaction"
    echo "  generate-token          Generate an API token"
    echo "  validate-token          Validate an API token"
    echo "  update-config           Update security configuration"
    echo "  enable-hw-wallet        Enable hardware wallet"
    echo "  show-config             Show current security configuration"
    echo ""
    echo "Options for 'notify' command:"
    echo "  send                    Send a notification"
    echo "  send-template           Send a notification using a template"
    echo "  config                  Configure notification settings"
    echo "  channel                 Manage notification channels"
    echo "  history                 View notification history"
    echo "  setup                   Run setup wizard for notification channels"
    echo "  test                    Send test notifications"
    echo ""
    echo "Options for 'dashboard' command:"
    echo "  start                   Start the web dashboard"
    echo "  stop                    Stop the web dashboard"
    echo "  status                  Check if the dashboard is running"
    echo "  create-user             Create a new dashboard user"
    echo "  generate-key            Generate a new API key"
    echo "  configure               Configure dashboard settings"
    echo "  reset                   Reset dashboard to defaults"
    echo ""
}

# Function to check if ArbitrageX is running
check_status() {
    # Find Python processes related to ArbitrageX
    PYTHON_PIDS=$(ps aux | grep -E "python.*backend/ai/.*_strategy.py" | grep -v grep | awk '{print $2}')
    
    # Find shell script processes related to ArbitrageX
    SHELL_PIDS=$(ps aux | grep -E "bash.*backend/ai/run_.*_strategy.sh" | grep -v grep | awk '{print $2}')
    
    # Combine all PIDs
    ALL_PIDS="$PYTHON_PIDS $SHELL_PIDS"
    
    if [ -n "$ALL_PIDS" ]; then
        echo -e "${GREEN}ArbitrageX is running.${NC}"
        echo "Active processes:"
        for PID in $ALL_PIDS; do
            COMMAND=$(ps -p $PID -o command=)
            echo "  PID $PID: $COMMAND"
        done
        return 0
    else
        echo -e "${YELLOW}ArbitrageX is not running.${NC}"
        return 1
    fi
}

# Function to create required log directory
ensure_log_directory() {
    mkdir -p backend/ai/logs
}

# Function to start ArbitrageX
start_arbitragex() {
    # First ensure log directory exists
    ensure_log_directory
    
    # Run with all arguments passed to this function
    ./run_arbitragex.sh "$@"
}

# Function to stop ArbitrageX
stop_arbitragex() {
    ./kill_arbitragex.sh
}

# Function to show logs
show_logs() {
    LOG_FILE="backend/ai/logs/arbitragex.log"
    
    # Default options
    FOLLOW=false
    LINES=50
    
    # Parse options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --follow)
                FOLLOW=true
                shift
                ;;
            --lines=*)
                LINES="${1#*=}"
                shift
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                echo "Usage: ./arbitragex.sh logs [--follow] [--lines=N]"
                exit 1
                ;;
        esac
    done
    
    # Check if log file exists
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${YELLOW}Log file does not exist. Has ArbitrageX been run yet?${NC}"
        return 1
    fi
    
    # Show logs
    if [ "$FOLLOW" = true ]; then
        echo -e "${CYAN}Showing last $LINES lines of logs and following new entries. Press Ctrl+C to stop.${NC}"
        tail -n $LINES -f $LOG_FILE
    else
        echo -e "${CYAN}Showing last $LINES lines of logs:${NC}"
        tail -n $LINES $LOG_FILE
    fi
}

# Function to clean up
cleanup() {
    echo -e "${YELLOW}Cleaning up ArbitrageX files...${NC}"
    
    # Remove lock files
    find backend/ai -name "*.lock" -type f -delete
    
    # Remove temporary swap files
    find backend/ai -name "*.swp" -type f -delete
    find backend/ai -name "*.swo" -type f -delete
    
    # Optionally truncate log files
    read -p "Do you want to clear log files as well? (y/n): " CLEAR_LOGS
    if [[ $CLEAR_LOGS == "y" || $CLEAR_LOGS == "Y" ]]; then
        echo "Clearing log files..."
        > backend/ai/logs/arbitragex.log
    fi
    
    echo -e "${GREEN}Cleanup completed.${NC}"
}

# Function to run backtests
run_backtest() {
    echo -e "${BLUE}ArbitrageX Backtesting Tool${NC}"
    echo "======================================================"

    # Ensure required directories exist
    mkdir -p backend/ai/metrics/backtest
    mkdir -p backend/ai/config/backtest
    
    # Make sure the backtesting script is executable
    chmod +x backend/ai/backtesting/backtester.py
    chmod +x backend/ai/backtesting/backtest_cli.py
    
    # Build the command
    CMD="python backend/ai/backtesting/backtest_cli.py"
    
    # Pass through all arguments
    for arg in "$@"; do
        CMD="$CMD $arg"
    done
    
    # If no arguments provided, show help
    if [ $# -eq 0 ]; then
        CMD="$CMD --help"
    fi
    
    # Print command and run
    echo -e "${YELLOW}Running: $CMD${NC}"
    echo "======================================================"
    
    eval $CMD
    
    if [ $? -eq 0 ]; then
        echo "======================================================"
        echo -e "${GREEN}Backtest completed successfully!${NC}"
        echo "Results are available in the backend/ai/metrics/backtest directory."
        echo "======================================================"
    else
        echo "======================================================"
        echo -e "${RED}Backtest failed. Check logs for errors.${NC}"
        echo "======================================================"
    fi
}

# Function to manage security features
manage_security() {
    echo -e "${BLUE}ArbitrageX Security Management${NC}"
    echo "======================================================"

    # Ensure required directories exist
    mkdir -p backend/ai/config

    # Make sure the security scripts are executable
    chmod +x backend/ai/security/security_manager.py
    chmod +x backend/ai/security/security_cli.py
    
    # Build the command
    CMD="python backend/ai/security/security_cli.py"
    
    # First argument is the security command
    if [ $# -eq 0 ]; then
        echo -e "${RED}Error: Missing security command.${NC}"
        echo -e "Usage: ./arbitragex.sh security [command] [options]"
        echo -e "Available commands:"
        echo -e "  store-key           Store a private key securely"
        echo -e "  validate-tx         Validate a transaction"
        echo -e "  sign-tx             Sign a transaction"
        echo -e "  generate-token      Generate an API token"
        echo -e "  validate-token      Validate an API token"
        echo -e "  update-config       Update security configuration"
        echo -e "  enable-hw-wallet    Enable hardware wallet"
        echo -e "  show-config         Show current security configuration"
        return 1
    fi
    
    SECURITY_COMMAND=$1
    shift
    
    case $SECURITY_COMMAND in
        store-key|validate-tx|sign-tx|generate-token|validate-token|update-config|enable-hw-wallet|show-config)
            CMD="$CMD $SECURITY_COMMAND"
            ;;
        *)
            echo -e "${RED}Error: Unknown security command: $SECURITY_COMMAND${NC}"
            echo -e "Available commands:"
            echo -e "  store-key           Store a private key securely"
            echo -e "  validate-tx         Validate a transaction"
            echo -e "  sign-tx             Sign a transaction"
            echo -e "  generate-token      Generate an API token"
            echo -e "  validate-token      Validate an API token"
            echo -e "  update-config       Update security configuration"
            echo -e "  enable-hw-wallet    Enable hardware wallet"
            echo -e "  show-config         Show current security configuration"
            return 1
            ;;
    esac
    
    # Pass through all other arguments
    for arg in "$@"; do
        CMD="$CMD $arg"
    done
    
    # Print command and run
    echo -e "${YELLOW}Running: $CMD${NC}"
    echo "======================================================"
    
    eval $CMD
    
    if [ $? -eq 0 ]; then
        echo "======================================================"
        echo -e "${GREEN}Security command completed successfully!${NC}"
        echo "======================================================"
    else
        echo "======================================================"
        echo -e "${RED}Security command failed. Check logs for errors.${NC}"
        echo "======================================================"
    fi
}

# Function to manage notification system
manage_notifications() {
    echo -e "${BLUE}ArbitrageX Notification Management${NC}"
    echo "======================================================"

    # Ensure required directories exist
    mkdir -p backend/ai/config
    mkdir -p backend/ai/logs

    # Make sure the notification scripts are executable
    chmod +x backend/ai/notifications/notification_cli.py
    
    # Build the command
    CMD="python backend/ai/notifications/notification_cli.py"
    
    # First argument is the notification command
    if [ $# -eq 0 ]; then
        echo -e "${RED}Error: Missing notification command.${NC}"
        echo -e "Usage: ./arbitragex.sh notify [command] [options]"
        echo -e "Available commands:"
        echo -e "  send                Send a notification"
        echo -e "  send-template       Send a notification using a template"
        echo -e "  config              Configure notification settings"
        echo -e "  channel             Manage notification channels"
        echo -e "  history             View notification history"
        echo -e "  setup               Run setup wizard for notification channels"
        echo -e "  test                Send test notifications"
        return 1
    fi
    
    NOTIFICATION_COMMAND=$1
    shift
    
    case $NOTIFICATION_COMMAND in
        send|send-template|config|channel|history|setup|test)
            CMD="$CMD $NOTIFICATION_COMMAND"
            ;;
        *)
            echo -e "${RED}Error: Unknown notification command: $NOTIFICATION_COMMAND${NC}"
            echo -e "Available commands:"
            echo -e "  send                Send a notification"
            echo -e "  send-template       Send a notification using a template"
            echo -e "  config              Configure notification settings"
            echo -e "  channel             Manage notification channels"
            echo -e "  history             View notification history"
            echo -e "  setup               Run setup wizard for notification channels"
            echo -e "  test                Send test notifications"
            return 1
            ;;
    esac
    
    # Pass through all other arguments
    for arg in "$@"; do
        CMD="$CMD $arg"
    done
    
    # Print command and run
    echo -e "${YELLOW}Running: $CMD${NC}"
    echo "======================================================"
    
    eval $CMD
    
    if [ $? -eq 0 ]; then
        echo "======================================================"
        echo -e "${GREEN}Notification command completed successfully!${NC}"
        echo "======================================================"
    else
        echo "======================================================"
        echo -e "${RED}Notification command failed. Check logs for errors.${NC}"
        echo "======================================================"
    fi
}

# Function to manage web dashboard
manage_dashboard() {
    echo -e "${BLUE}ArbitrageX Web Dashboard Management${NC}"
    echo "======================================================"

    # Ensure required directories exist
    mkdir -p backend/ai/config
    mkdir -p backend/ai/logs

    # Make sure the dashboard scripts are executable
    chmod +x backend/ai/dashboard/app.py
    chmod +x backend/ai/dashboard/dashboard_cli.py
    
    # Build the command
    CMD="python backend/ai/dashboard/dashboard_cli.py"
    
    # First argument is the dashboard command
    if [ $# -eq 0 ]; then
        echo -e "${RED}Error: Missing dashboard command.${NC}"
        echo -e "Usage: ./arbitragex.sh dashboard [command] [options]"
        echo -e "Available commands:"
        echo -e "  start               Start the web dashboard"
        echo -e "  stop                Stop the web dashboard"
        echo -e "  status              Check if the dashboard is running"
        echo -e "  create-user         Create a new dashboard user"
        echo -e "  generate-key        Generate a new API key"
        echo -e "  configure           Configure dashboard settings"
        echo -e "  reset               Reset dashboard to defaults"
        return 1
    fi
    
    DASHBOARD_COMMAND=$1
    shift
    
    case $DASHBOARD_COMMAND in
        start|stop|status|create-user|generate-key|configure|reset)
            CMD="$CMD $DASHBOARD_COMMAND"
            ;;
        *)
            echo -e "${RED}Error: Unknown dashboard command: $DASHBOARD_COMMAND${NC}"
            echo -e "Available commands:"
            echo -e "  start               Start the web dashboard"
            echo -e "  stop                Stop the web dashboard"
            echo -e "  status              Check if the dashboard is running"
            echo -e "  create-user         Create a new dashboard user"
            echo -e "  generate-key        Generate a new API key"
            echo -e "  configure           Configure dashboard settings"
            echo -e "  reset               Reset dashboard to defaults"
            return 1
            ;;
    esac
    
    # Pass through all other arguments
    for arg in "$@"; do
        CMD="$CMD $arg"
    done
    
    # Print command and run
    echo -e "${YELLOW}Running: $CMD${NC}"
    echo "======================================================"
    
    eval $CMD
    
    if [ $? -eq 0 ]; then
        echo "======================================================"
        echo -e "${GREEN}Dashboard command completed successfully!${NC}"
        echo "======================================================"
    else
        echo "======================================================"
        echo -e "${RED}Dashboard command failed. Check logs for errors.${NC}"
        echo "======================================================"
    fi
}

# Make sure run_arbitragex.sh and kill_arbitragex.sh are executable
chmod +x run_arbitragex.sh kill_arbitragex.sh

# Command processing
if [ $# -eq 0 ]; then
    print_usage
    exit 0
fi

COMMAND=$1
shift

case $COMMAND in
    start)
        start_arbitragex "$@"
        ;;
    stop)
        stop_arbitragex
        ;;
    restart)
        stop_arbitragex
        echo "Waiting 3 seconds before restart..."
        sleep 3
        start_arbitragex "$@"
        ;;
    status)
        check_status
        ;;
    logs)
        show_logs "$@"
        ;;
    cleanup)
        cleanup
        ;;
    backtest)
        run_backtest "$@"
        ;;
    security)
        manage_security "$@"
        ;;
    notify)
        manage_notifications "$@"
        ;;
    dashboard)
        manage_dashboard "$@"
        ;;
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        print_usage
        exit 1
        ;;
esac 