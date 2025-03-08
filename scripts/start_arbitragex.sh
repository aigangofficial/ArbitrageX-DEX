#!/bin/bash

# ArbitrageX One-Command Startup Script
# This script provides a one-command solution to start the entire ArbitrageX system

# Color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Set the base directory to the project root
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE_DIR"

# Create logs directory if it doesn't exist
mkdir -p "$BASE_DIR/logs"

# Print banner
echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   █████╗ ██████╗ ██████╗ ██╗████████╗██████╗  █████╗  ██████╗ ║"
echo "║  ██╔══██╗██╔══██╗██╔══██╗██║╚══██╔══╝██╔══██╗██╔══██╗██╔════╝ ║"
echo "║  ███████║██████╔╝██████╔╝██║   ██║   ██████╔╝███████║██║  ███╗║"
echo "║  ██╔══██║██╔══██╗██╔══██╗██║   ██║   ██╔══██╗██╔══██║██║   ██║║"
echo "║  ██║  ██║██║  ██║██████╔╝██║   ██║   ██║  ██║██║  ██║╚██████╔╝║"
echo "║  ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ║"
echo "║                                                               ║"
echo "║                  AI-Powered Arbitrage Bot                     ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "${YELLOW}If the system doesn't stop properly with Ctrl+C, use:${NC}"
echo -e "${BLUE}./scripts/kill_all_arbitragex.sh${NC}"
echo

# Function to log messages
log() {
  echo -e "${BLUE}$(date '+%Y-%m-%d %H:%M:%S') - $1${NC}" | tee -a "$BASE_DIR/logs/startup.log"
}

# Function to check if a port is in use
is_port_in_use() {
  lsof -i :"$1" >/dev/null 2>&1
  return $?
}

# Kill existing processes
kill_processes() {
  log "Killing existing processes..."
  
  # Kill any existing Node.js processes related to ArbitrageX
  pkill -f "node.*api" || true
  pkill -f "node.*frontend" || true
  pkill -f "node.*bot" || true
  pkill -f "ts-node.*bot" || true
  pkill -f "monitor_services.sh" || true
  pkill -f "hardhat node" || true
  
  # Wait for processes to terminate
  sleep 2
  
  # Check if ports are still in use
  if is_port_in_use 3001; then
    log "Port 3001 is still in use. Forcing termination..."
    lsof -ti:3001 | xargs kill -9 || true
  fi
  
  if is_port_in_use 3002; then
    log "Port 3002 is still in use. Forcing termination..."
    lsof -ti:3002 | xargs kill -9 || true
  fi
  
  if is_port_in_use 8545; then
    log "Port 8545 is still in use. Forcing termination..."
    lsof -ti:8545 | xargs kill -9 || true
  fi
  
  log "All processes terminated."
}

# Start API server
start_api() {
  log "Starting API server on port 3002..."
  cd "$BASE_DIR/backend/api"
  PORT=3002 npm run start > "$BASE_DIR/logs/api.log" 2>&1 &
  API_PID=$!
  echo $API_PID > "$BASE_DIR/logs/api.pid"
  log "API server started with PID $API_PID"
  
  # Wait for API server to start
  log "Waiting for API server to be ready..."
  for i in {1..30}; do
    if curl -s http://localhost:3002/health >/dev/null; then
      log "API server is ready."
      break
    fi
    
    if ! ps -p $API_PID > /dev/null; then
      log "ERROR: API server process died. Check logs/api.log for details."
      exit 1
    fi
    
    sleep 1
    
    if [ $i -eq 30 ]; then
      log "WARNING: API server did not respond in time, but continuing..."
    fi
  done
}

# Start frontend
start_frontend() {
  log "Starting frontend on port 3001..."
  cd "$BASE_DIR/frontend"
  PORT=3001 npm run dev > "$BASE_DIR/logs/frontend.log" 2>&1 &
  FRONTEND_PID=$!
  echo $FRONTEND_PID > "$BASE_DIR/logs/frontend.pid"
  log "Frontend started with PID $FRONTEND_PID"
  
  # Wait for frontend to start
  log "Waiting for frontend to be ready..."
  for i in {1..30}; do
    if curl -s http://localhost:3001 >/dev/null; then
      log "Frontend is ready."
      break
    fi
    
    if ! ps -p $FRONTEND_PID > /dev/null; then
      log "ERROR: Frontend process died. Check logs/frontend.log for details."
      exit 1
    fi
    
    sleep 1
    
    if [ $i -eq 30 ]; then
      log "WARNING: Frontend did not respond in time, but continuing..."
    fi
  done
}

# Start learning loop
start_learning_loop() {
  log "Starting AI Learning Loop..."
  cd "$BASE_DIR"
  python3 "$BASE_DIR/backend/ai/start_learning_loop.py" > "$BASE_DIR/logs/learning_loop.log" 2>&1 &
  LEARNING_LOOP_PID=$!
  echo $LEARNING_LOOP_PID > "$BASE_DIR/logs/learning_loop.pid"
  log "AI Learning Loop started with PID $LEARNING_LOOP_PID"
  
  # Wait for learning loop to start
  log "Waiting for AI Learning Loop to be ready..."
  for i in {1..10}; do
    if [ -f "$BASE_DIR/backend/ai/learning_loop_status.json" ]; then
      log "AI Learning Loop is ready."
      break
    fi
    
    if ! ps -p $LEARNING_LOOP_PID > /dev/null; then
      log "ERROR: AI Learning Loop process died. Check logs/learning_loop.log for details."
      exit 1
    fi
    
    sleep 1
    
    if [ $i -eq 10 ]; then
      log "WARNING: AI Learning Loop did not respond in time, but continuing..."
    fi
  done
}

# Start bot
start_bot() {
  log "Starting ArbitrageX bot..."
  
  # Define bot parameters
  RUN_TIME=3600
  TOKENS="WETH,USDC,DAI"
  DEXES="uniswap_v3,curve,balancer"
  GAS_STRATEGY="dynamic"
  
  # Start the bot using the API
  BOT_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" \
    -d "{\"runTime\": $RUN_TIME, \"tokens\": \"$TOKENS\", \"dexes\": \"$DEXES\", \"gasStrategy\": \"$GAS_STRATEGY\"}" \
    http://localhost:3002/api/v1/bot-control/start)
  
  if [[ "$BOT_RESPONSE" == *"success\":true"* ]]; then
    log "Bot started successfully."
  else
    log "ERROR: Failed to start bot. Response: $BOT_RESPONSE"
    exit 1
  fi
}

# Monitor function to check services periodically
monitor_services() {
  log "Starting service monitor..."
  
  while true; do
    # Check API server
    if ! curl -s http://localhost:3002/health >/dev/null; then
      log "WARNING: API server is not responding. Checking process..."
      if [ -f "$BASE_DIR/logs/api.pid" ]; then
        API_PID=$(cat "$BASE_DIR/logs/api.pid")
        if ! ps -p $API_PID > /dev/null; then
          log "ERROR: API server process (PID: $API_PID) is not running. Restarting..."
          start_api
        fi
      fi
    fi
    
    # Check frontend
    if ! curl -s http://localhost:3001 >/dev/null; then
      log "WARNING: Frontend is not responding. Checking process..."
      if [ -f "$BASE_DIR/logs/frontend.pid" ]; then
        FRONTEND_PID=$(cat "$BASE_DIR/logs/frontend.pid")
        if ! ps -p $FRONTEND_PID > /dev/null; then
          log "ERROR: Frontend process (PID: $FRONTEND_PID) is not running. Restarting..."
          start_frontend
        fi
      fi
    fi
    
    # Check learning loop
    if [ -f "$BASE_DIR/logs/learning_loop.pid" ]; then
      LEARNING_LOOP_PID=$(cat "$BASE_DIR/logs/learning_loop.pid")
      if ! ps -p $LEARNING_LOOP_PID > /dev/null; then
        log "ERROR: AI Learning Loop process (PID: $LEARNING_LOOP_PID) is not running. Restarting..."
        start_learning_loop
      fi
    fi
    
    # Check bot status using both endpoints
    BOT_CONTROL_STATUS=$(curl -s http://localhost:3002/api/v1/bot-control/status)
    BOT_STATUS=$(curl -s http://localhost:3002/api/v1/status)
    
    # Only restart if both endpoints indicate the bot is not running
    if [[ "$BOT_CONTROL_STATUS" != *"\"isRunning\":true"* ]] && [[ "$BOT_STATUS" == *"\"error\""* || "$BOT_STATUS" == *"\"isActive\":false"* ]]; then
      log "WARNING: Bot is not running according to both status endpoints. Restarting..."
      start_bot
    fi
    
    # Sleep for 30 seconds before next check
    sleep 30
  done
}

# Main execution
log "Starting ArbitrageX system..."

# Kill existing processes
kill_processes

# Start components
start_api
start_frontend
start_learning_loop
start_bot

# Start monitor in background
monitor_services &
MONITOR_PID=$!
echo $MONITOR_PID > "$BASE_DIR/logs/monitor.pid"

# Display success message
log "ArbitrageX system started successfully!"
echo -e "${GREEN}Access Information:${NC}"
echo -e "  - API Server: ${CYAN}http://localhost:3002${NC}"
echo -e "  - Frontend Dashboard: ${CYAN}http://localhost:3001${NC}"
echo -e "  - Bot Status: ${CYAN}http://localhost:3002/api/v1/status${NC}"
echo -e "  - WebSocket Stats: ${CYAN}http://localhost:3002/api/v1/websocket/stats${NC}"
echo -e "  - Monitor Log: ${CYAN}tail -f logs/startup.log${NC}"

# Keep the script running to make it easy to stop everything with Ctrl+C
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Set up trap to kill processes on script exit
trap 'echo -e "${YELLOW}\nStopping all services...${NC}"; kill_processes; echo -e "${GREEN}All services stopped.${NC}"; exit 0' INT TERM

# Wait indefinitely
while true; do
  sleep 10
done 