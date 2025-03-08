#!/bin/bash

# ArbitrageX Process Killer
# This script terminates all ArbitrageX-related processes and cleans up temporary files

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print a colorful banner
echo -e "${RED}"
echo "    _          _     _ _                       __   __"
echo "   / \\   _ __ | |__ (_) |_ _ __ __ _  __ _  __\\ \\ / /"
echo "  / _ \\ | '_ \\| '_ \\| | __| '__/ _\` |/ _\` |/ _ \\ V / "
echo " / ___ \\| |_) | |_) | | |_| | | (_| | (_| |  __/| |  "
echo "/_/   \\_\\ .__/|_.__/|_|\\__|_|  \\__,_|\\__, |\\___||_|  "
echo "        |_|                          |___/           "
echo -e "${NC}"
echo -e "${RED}Process Terminator${NC}"
echo "======================================================"

# Kill all ArbitrageX-related processes
echo -e "${YELLOW}Terminating all ArbitrageX processes...${NC}"

# Find Python processes related to ArbitrageX
PYTHON_PIDS=$(ps aux | grep -E "python.*backend/ai/.*_strategy.py" | grep -v grep | awk '{print $2}')

# Find shell script processes related to ArbitrageX
SHELL_PIDS=$(ps aux | grep -E "bash.*backend/ai/run_.*_strategy.sh" | grep -v grep | awk '{print $2}')

# Combine all PIDs
ALL_PIDS="$PYTHON_PIDS $SHELL_PIDS"

# Kill processes if any were found
if [ -n "$ALL_PIDS" ]; then
    echo -e "${YELLOW}Found ArbitrageX processes. Terminating...${NC}"
    for PID in $ALL_PIDS; do
        echo "Killing process $PID"
        kill -9 $PID 2>/dev/null || true
    done
    echo -e "${GREEN}All ArbitrageX processes terminated.${NC}"
else
    echo -e "${GREEN}No running ArbitrageX processes found.${NC}"
fi

# Clean up any temporary files
echo -e "${YELLOW}Cleaning up temporary files...${NC}"

# Remove any lock files
find backend/ai -name "*.lock" -type f -delete

# Remove any temporary swap files
find backend/ai -name "*.swp" -type f -delete
find backend/ai -name "*.swo" -type f -delete

echo -e "${GREEN}Temporary files cleaned up.${NC}"
echo "======================================================"

# Final confirmation
echo -e "${GREEN}All ArbitrageX processes have been terminated and temporary files cleaned up.${NC}"
echo "To restart ArbitrageX, run: ./run_arbitragex.sh"
echo "======================================================" 