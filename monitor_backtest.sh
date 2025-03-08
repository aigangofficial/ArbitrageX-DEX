#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== ArbitrageX Backtest Monitoring Script ===${NC}"
echo "Starting monitoring of backtest process..."

# Directory to monitor
RESULTS_DIR="backend/ai/results"
REALISTIC_DIR="backend/ai/results/realistic_backtest"

# Initial file count
initial_count=$(ls -1 $RESULTS_DIR | wc -l)
echo "Initial file count in results directory: $initial_count"

# Check if the backtest process is running
check_process() {
    if pgrep -f "run_realistic_backtest.py" > /dev/null; then
        echo -e "${GREEN}✓ Backtest process is running${NC}"
        return 0
    else
        echo -e "${RED}✗ Backtest process is not running${NC}"
        return 1
    fi
}

# Check for new files in the results directory
check_new_files() {
    current_count=$(ls -1 $RESULTS_DIR | wc -l)
    new_files=$((current_count - initial_count))
    
    if [ $new_files -gt 0 ]; then
        echo -e "${GREEN}✓ $new_files new files generated since monitoring started${NC}"
        
        # Get the most recent files (up to 5)
        echo -e "${BLUE}Most recent files:${NC}"
        ls -lt $RESULTS_DIR | head -n 6 | tail -n 5 | awk '{print $9}'
        
        return 0
    else
        echo -e "${YELLOW}! No new files detected yet${NC}"
        return 1
    fi
}

# Check for realistic backtest results
check_realistic_results() {
    if [ -d "$REALISTIC_DIR" ]; then
        file_count=$(ls -1 $REALISTIC_DIR 2>/dev/null | wc -l)
        if [ $file_count -gt 0 ]; then
            echo -e "${GREEN}✓ Realistic backtest results available: $file_count files${NC}"
            echo -e "${BLUE}Files in realistic_backtest directory:${NC}"
            ls -la $REALISTIC_DIR
            return 0
        else
            echo -e "${YELLOW}! Realistic backtest directory exists but is empty${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}! Realistic backtest directory not created yet${NC}"
        return 1
    fi
}

# Check for log files
check_logs() {
    log_file="logs/realistic_backtest.log"
    if [ -f "$log_file" ]; then
        echo -e "${GREEN}✓ Log file exists${NC}"
        echo -e "${BLUE}Last 5 lines of log:${NC}"
        tail -n 5 $log_file
        return 0
    else
        echo -e "${YELLOW}! Log file not found: $log_file${NC}"
        return 1
    fi
}

# Main monitoring loop
echo "Press Ctrl+C to stop monitoring"
iteration=1

while true; do
    echo -e "\n${BLUE}=== Monitoring Iteration $iteration ===${NC}"
    echo "Time: $(date)"
    
    check_process
    process_status=$?
    
    check_new_files
    check_realistic_results
    check_logs
    
    # If process is not running but we have results, it might have completed
    if [ $process_status -eq 1 ] && [ -d "$REALISTIC_DIR" ]; then
        file_count=$(ls -1 $REALISTIC_DIR 2>/dev/null | wc -l)
        if [ $file_count -gt 0 ]; then
            echo -e "\n${GREEN}=== BACKTEST COMPLETED SUCCESSFULLY ===${NC}"
            echo "Results available in: $REALISTIC_DIR"
            echo "Total result files: $file_count"
            break
        fi
    fi
    
    # Wait before next check
    echo -e "\nWaiting 30 seconds before next check..."
    sleep 30
    
    iteration=$((iteration + 1))
done

echo -e "\n${BLUE}=== Final Results ===${NC}"
echo "Time: $(date)"
check_realistic_results
echo -e "\n${GREEN}Monitoring complete. Check the results directory for detailed output.${NC}" 