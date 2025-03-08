#!/bin/bash

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
echo "║                  AI-Powered Arbitrage Bot                     ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${YELLOW}Enhanced Full Project Startup Script${NC}"
echo "This script will start all components of the ArbitrageX system in the correct order."
echo ""

# Function to check if a port is in use
check_port() {
  lsof -i :$1 > /dev/null 2>&1
  return $?
}

# Function to wait for a service to be available
wait_for_service() {
  local service_name=$1
  local url=$2
  local max_attempts=$3
  local attempt=1
  
  echo -e "${YELLOW}Waiting for $service_name to be available...${NC}"
  
  while [ $attempt -le $max_attempts ]; do
    if curl -s "$url" > /dev/null 2>&1; then
      echo -e "${GREEN}$service_name is available!${NC}"
      return 0
    fi
    
    echo -e "${YELLOW}Attempt $attempt/$max_attempts: $service_name not yet available. Waiting...${NC}"
    sleep 2
    attempt=$((attempt + 1))
  done
  
  echo -e "${RED}$service_name did not become available after $max_attempts attempts.${NC}"
  return 1
}

# Step 1: Kill any existing processes
echo -e "${BLUE}Step 1: Killing any existing ArbitrageX processes...${NC}"
./scripts/kill_all_arbitragex.sh
sleep 2

# Double-check and forcefully kill any remaining processes
echo -e "${YELLOW}Double-checking for any remaining processes...${NC}"

# Check for hardhat processes
hardhat_pids=$(ps aux | grep "hardhat node" | grep -v grep | awk '{print $2}')
if [ ! -z "$hardhat_pids" ]; then
  echo -e "${YELLOW}Found remaining hardhat processes. Killing them...${NC}"
  for pid in $hardhat_pids; do
    kill -9 $pid 2>/dev/null
  done
fi

# Check for API server processes
api_pids=$(ps aux | grep "node.*api" | grep -v grep | awk '{print $2}')
if [ ! -z "$api_pids" ]; then
  echo -e "${YELLOW}Found remaining API server processes. Killing them...${NC}"
  for pid in $api_pids; do
    kill -9 $pid 2>/dev/null
  done
fi

# Check for frontend processes
frontend_pids=$(ps aux | grep "node.*frontend" | grep -v grep | awk '{print $2}')
if [ ! -z "$frontend_pids" ]; then
  echo -e "${YELLOW}Found remaining frontend processes. Killing them...${NC}"
  for pid in $frontend_pids; do
    kill -9 $pid 2>/dev/null
  done
fi

# Check for monitor processes
monitor_pids=$(ps aux | grep "monitor_services.sh" | grep -v grep | awk '{print $2}')
if [ ! -z "$monitor_pids" ]; then
  echo -e "${YELLOW}Found remaining monitor processes. Killing them...${NC}"
  for pid in $monitor_pids; do
    kill -9 $pid 2>/dev/null
  done
fi

# Check for bot processes
bot_pids=$(ps aux | grep "bot" | grep -v grep | awk '{print $2}')
if [ ! -z "$bot_pids" ]; then
  echo -e "${YELLOW}Found remaining bot processes. Killing them...${NC}"
  for pid in $bot_pids; do
    kill -9 $pid 2>/dev/null
  done
fi

# Check if ports are still in use
for port in 8545 3001 3002; do
  if lsof -i :$port > /dev/null 2>&1; then
    echo -e "${YELLOW}Port $port is still in use. Attempting to free it...${NC}"
    pid=$(lsof -i :$port | grep LISTEN | awk '{print $2}')
    if [ ! -z "$pid" ]; then
      kill -9 $pid 2>/dev/null
      sleep 1
    fi
  fi
done

echo -e "${GREEN}All processes should now be terminated.${NC}"
sleep 2

# Step 2: Start Hardhat node
echo -e "${BLUE}Step 2: Starting Hardhat node...${NC}"
./scripts/manage_processes.sh start-hardhat
sleep 5

# Check if Hardhat node is running
if ! check_port 8545; then
  echo -e "${RED}Hardhat node failed to start. Exiting.${NC}"
  exit 1
fi

# Step 3: Deploy contracts to Hardhat node
echo -e "${BLUE}Step 3: Deploying contracts to Hardhat node...${NC}"
./scripts/manage_processes.sh deploy-contracts
sleep 2

# Step 4: Start API server
echo -e "${BLUE}Step 4: Starting API server...${NC}"
./scripts/manage_processes.sh start-api
sleep 5

# Check if API server is running
if ! check_port 3002; then
  echo -e "${RED}API server failed to start. Exiting.${NC}"
  exit 1
fi

# Wait for API server to be fully available
if ! wait_for_service "API server" "http://localhost:3002/health" 10; then
  echo -e "${RED}API server health check failed. Continuing anyway...${NC}"
fi

# Step 5: Check blockchain connection
echo -e "${BLUE}Step 5: Checking blockchain connection...${NC}"
blockchain_status=$(curl -s http://localhost:3002/api/v1/blockchain/health)
if [[ $blockchain_status == *"disconnected"* ]]; then
  echo -e "${YELLOW}API server is not connected to the blockchain. Restarting API server...${NC}"
  ./scripts/manage_processes.sh kill-api
  sleep 2
  ./scripts/manage_processes.sh start-api
  sleep 5
  
  # Check blockchain connection again
  blockchain_status=$(curl -s http://localhost:3002/api/v1/blockchain/health)
  if [[ $blockchain_status == *"disconnected"* ]]; then
    echo -e "${RED}API server still not connected to the blockchain. Continuing anyway...${NC}"
  else
    echo -e "${GREEN}API server successfully connected to the blockchain!${NC}"
  fi
else
  echo -e "${GREEN}API server successfully connected to the blockchain!${NC}"
fi

# Step 6: Start frontend
echo -e "${BLUE}Step 6: Starting frontend...${NC}"
./scripts/manage_processes.sh start-frontend
sleep 5

# Check if frontend is running
if ! check_port 3001; then
  echo -e "${RED}Frontend failed to start. Exiting.${NC}"
  exit 1
fi

# Wait for frontend to be fully available
if ! wait_for_service "Frontend" "http://localhost:3001" 10; then
  echo -e "${RED}Frontend health check failed. Continuing anyway...${NC}"
fi

# Step 7: Start the trading bot
echo -e "${BLUE}Step 7: Starting the trading bot...${NC}"
# Use the API to start the bot instead of a separate process
curl -s -X POST http://localhost:3002/api/v1/bot-control/start -H "Content-Type: application/json" -d '{"runTime": 3600, "tokens": "WETH,USDC,DAI", "dexes": "UniswapV3,Curve,Balancer", "gasStrategy": "dynamic"}' > /dev/null
sleep 5

# Check if the bot started successfully
bot_status=$(curl -s http://localhost:3002/api/v1/bot-control/status 2>/dev/null)
if [[ $bot_status == *"running"* ]]; then
  echo -e "${GREEN}Trading bot started successfully!${NC}"
else
  echo -e "${YELLOW}Trading bot may not have started properly. Check logs for details.${NC}"
  echo -e "${YELLOW}You can manually start it with: curl -X POST http://localhost:3002/api/v1/bot-control/start${NC}"
fi

# Step 8: Start monitor service
echo -e "${BLUE}Step 8: Starting monitor service...${NC}"
# Ensure logs directory exists
mkdir -p logs

# Use nohup with complete redirection and disown to fully detach the process
nohup ./scripts/monitor_services.sh > logs/monitor_output.log 2>&1 </dev/null &
monitor_pid=$!
echo $monitor_pid > logs/monitor.pid
disown $monitor_pid
echo -e "${GREEN}Monitor service started with PID $monitor_pid${NC}"
echo -e "${GREEN}Monitor service output is being redirected to logs/monitor_output.log${NC}"

# Final check
echo -e "${BLUE}Performing final check of all services...${NC}"
echo -e "${YELLOW}Checking Hardhat node...${NC}"
if check_port 8545; then
  echo -e "${GREEN}Hardhat node is running on port 8545.${NC}"
else
  echo -e "${RED}Hardhat node is not running!${NC}"
fi

echo -e "${YELLOW}Checking API server...${NC}"
if check_port 3002; then
  echo -e "${GREEN}API server is running on port 3002.${NC}"
else
  echo -e "${RED}API server is not running!${NC}"
fi

echo -e "${YELLOW}Checking frontend...${NC}"
if check_port 3001; then
  echo -e "${GREEN}Frontend is running on port 3001.${NC}"
else
  echo -e "${RED}Frontend is not running!${NC}"
fi

echo -e "${YELLOW}Checking blockchain connection...${NC}"
blockchain_status=$(curl -s http://localhost:3002/api/v1/blockchain/health)
if [[ $blockchain_status == *"connected"* ]]; then
  echo -e "${GREEN}API server is connected to the blockchain.${NC}"
else
  echo -e "${RED}API server is not connected to the blockchain!${NC}"
fi

echo -e "${YELLOW}Checking trading bot status...${NC}"
bot_status=$(curl -s http://localhost:3002/api/v1/bot-control/status 2>/dev/null)
if [[ $bot_status == *"running"* ]]; then
  echo -e "${GREEN}Trading bot is running.${NC}"
else
  echo -e "${YELLOW}Trading bot may not be running. You can check with:${NC}"
  echo -e "${BLUE}curl -s http://localhost:3002/api/v1/bot-control/status${NC}"
fi

# Print access information
echo ""
echo -e "${GREEN}ArbitrageX system started successfully!${NC}"
echo -e "${BLUE}Access Information:${NC}"
echo -e "- Hardhat Node: ${YELLOW}http://localhost:8545${NC}"
echo -e "- API Server: ${YELLOW}http://localhost:3002${NC}"
echo -e "- Frontend Dashboard: ${YELLOW}http://localhost:3001/new-dashboard${NC}"
echo -e "- Bot Status: ${YELLOW}http://localhost:3002/api/v1/bot-control/status${NC}"
echo -e "- Bot Trades: ${YELLOW}http://localhost:3002/api/v1/trades${NC}"
echo ""
echo -e "${YELLOW}To stop the system, run:${NC}"
echo -e "${BLUE}./scripts/kill_all_arbitragex.sh${NC}"
echo ""
echo -e "${YELLOW}To check system status, run:${NC}"
echo -e "${BLUE}ps aux | grep -E \"hardhat|node.*api|node.*frontend|monitor_services.sh\" | grep -v grep${NC}"
echo ""
echo -e "${YELLOW}To view logs, run:${NC}"
echo -e "${BLUE}tail -f logs/monitor.log${NC}"
echo ""
echo -e "${YELLOW}Bot Control Commands:${NC}"
echo -e "- Start Bot: ${BLUE}curl -X POST http://localhost:3002/api/v1/bot-control/start${NC}"
echo -e "- Stop Bot: ${BLUE}curl -X POST http://localhost:3002/api/v1/bot-control/stop${NC}"
echo -e "- Check Bot Status: ${BLUE}curl http://localhost:3002/api/v1/bot-control/status${NC}" 