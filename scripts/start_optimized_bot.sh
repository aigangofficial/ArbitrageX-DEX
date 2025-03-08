#!/bin/bash

# ArbitrageX Optimized Bot Startup Script
# This script starts the bot with optimized settings to reduce CPU usage

# Color codes for better readability
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Set the base directory to the project root
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE_DIR"

# Create logs directory if it doesn't exist
mkdir -p "$BASE_DIR/logs"

# Print banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   █████╗ ██████╗ ██████╗ ██╗████████╗██████╗  █████╗  ██████╗ ║"
echo "║  ██╔══██╗██╔══██╗██╔══██╗██║╚══██╔══╝██╔══██╗██╔══██╗██╔════╝ ║"
echo "║  ███████║██████╔╝██████╔╝██║   ██║   ██████╔╝███████║██║  ███╗║"
echo "║  ██╔══██║██╔══██╗██╔══██╗██║   ██║   ██╔══██╗██╔══██║██║   ██║║"
echo "║  ██║  ██║██║  ██║██████╔╝██║   ██║   ██║  ██║██║  ██║╚██████╔╝║"
echo "║  ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ║"
echo "║                                                               ║"
echo "║                  OPTIMIZED BOT STARTUP                        ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to log messages
log() {
  echo -e "${BLUE}$(date '+%Y-%m-%d %H:%M:%S') - $1${NC}" | tee -a "$BASE_DIR/logs/optimized_bot.log"
}

# Kill any existing bot processes
log "Killing any existing bot processes..."
./scripts/kill_all_arbitragex.sh

# Check if Hardhat node is running
if ! curl -s http://localhost:8545 > /dev/null; then
  log "Starting Hardhat node..."
  npx hardhat node > "$BASE_DIR/logs/hardhat.log" 2>&1 &
  HARDHAT_PID=$!
  echo $HARDHAT_PID > "$BASE_DIR/logs/hardhat.pid"
  
  # Wait for Hardhat node to start
  log "Waiting for Hardhat node to be ready..."
  for i in {1..30}; do
    if curl -s http://localhost:8545 > /dev/null; then
      log "Hardhat node is ready."
      break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
      log "WARNING: Hardhat node did not respond in time, but continuing..."
    fi
  done
else
  log "Hardhat node is already running."
fi

# Define bot parameters
RUN_TIME=3600
TOKENS="WETH,USDC,DAI"
DEXES="uniswap_v3,curve,balancer"
GAS_STRATEGY="conservative"

# Set environment variables for optimized performance
export NODE_ENV="production"
export DEBUG_MODE="false"
export LOG_LEVEL="info"
export SCAN_INTERVAL="15000"  # 15 seconds between scans

log "Starting bot with optimized settings..."
log "Run time: ${RUN_TIME} seconds"
log "Tokens: ${TOKENS}"
log "DEXes: ${DEXES}"
log "Gas strategy: ${GAS_STRATEGY}"
log "Debug mode: disabled"
log "Log level: info"
log "Scan interval: 15 seconds"

# Start the bot with optimized settings
cd "$BASE_DIR/backend/execution"
npx ts-node bot.ts --run-time $RUN_TIME --tokens $TOKENS --dexes $DEXES --gas-strategy $GAS_STRATEGY > "$BASE_DIR/logs/optimized_bot.log" 2>&1 &
BOT_PID=$!
echo $BOT_PID > "$BASE_DIR/logs/bot.pid"

log "Bot started with PID $BOT_PID"
log "Log file: $BASE_DIR/logs/optimized_bot.log"

echo -e "${GREEN}Bot is running with optimized settings to reduce CPU usage.${NC}"
echo -e "${YELLOW}To monitor the bot, use: tail -f $BASE_DIR/logs/optimized_bot.log${NC}"
echo -e "${YELLOW}To stop the bot, use: ./scripts/kill_all_arbitragex.sh${NC}" 