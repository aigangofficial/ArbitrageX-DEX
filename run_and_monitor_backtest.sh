#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== ArbitrageX Backtest Runner & Monitor ===${NC}"
echo "This script will start the backtest and monitor its progress"

# Set environment variables
export ETHEREUM_RPC_URL="https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161"

# Parameters
INVESTMENT=50
DAYS=3
MIN_PROFIT=0.5
MIN_LIQUIDITY=10000

echo -e "${YELLOW}Backtest Parameters:${NC}"
echo "Investment: $INVESTMENT"
echo "Days: $DAYS"
echo "Min Profit USD: $MIN_PROFIT"
echo "Min Liquidity: $MIN_LIQUIDITY"
echo "RPC URL: $ETHEREUM_RPC_URL"

# Start the backtest in the background
echo -e "\n${BLUE}Starting backtest process...${NC}"
python3 backend/ai/run_realistic_backtest.py --investment $INVESTMENT --days $DAYS --min-profit-usd $MIN_PROFIT --min-liquidity $MIN_LIQUIDITY &

# Get the PID of the backtest process
BACKTEST_PID=$!
echo "Backtest process started with PID: $BACKTEST_PID"

# Give the process a moment to initialize
sleep 5

# Start monitoring
echo -e "\n${BLUE}Starting monitoring...${NC}"
./monitor_backtest.sh

# Check if the backtest is still running when monitoring ends
if ps -p $BACKTEST_PID > /dev/null; then
    echo -e "${YELLOW}Backtest process is still running with PID: $BACKTEST_PID${NC}"
    echo "You can continue to monitor it manually or press Ctrl+C to stop it."
else
    echo -e "${GREEN}Backtest process has completed.${NC}"
fi

echo -e "\n${GREEN}Script execution complete.${NC}" 