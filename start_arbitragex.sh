#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== ArbitrageX Full System Startup ===${NC}"
echo "This script will start all ArbitrageX services"

# Function to check if a port is already in use
check_port() {
  local port=$1
  if lsof -i :$port -sTCP:LISTEN > /dev/null; then
    return 0
  else
    return 1
  fi
}

# Function to kill processes using a specific port
kill_port_process() {
  local port=$1
  local pid=$(lsof -t -i:$port)
  if [ ! -z "$pid" ]; then
    echo -e "${YELLOW}Killing process using port $port (PID: $pid)${NC}"
    kill -9 $pid
  fi
}

# Check and create necessary directories
echo -e "\n${YELLOW}Checking and creating necessary directories...${NC}"
mkdir -p backend/execution/logs
mkdir -p backend/api/logs
mkdir -p logs

# 1. Start the Bot
echo -e "\n${BLUE}Starting ArbitrageX Bot...${NC}"
cd backend/execution
npm run bot:start > ../../logs/bot.log 2>&1 &
BOT_PID=$!
echo "Bot started with PID: $BOT_PID"
cd ../..

# Wait a moment for the bot to initialize
sleep 5

# 2. Start the API Server
echo -e "\n${BLUE}Starting API Server...${NC}"
# Check if port 3000 is in use
if check_port 3000; then
  echo -e "${YELLOW}Port 3000 is already in use. Killing the process...${NC}"
  kill_port_process 3000
  sleep 2
fi

cd backend/api
npm run start > ../../logs/api.log 2>&1 &
API_PID=$!
echo "API Server started with PID: $API_PID"
cd ../..

# Wait a moment for the API server to initialize
sleep 5

# 3. Start the Frontend
echo -e "\n${BLUE}Starting Frontend Dashboard...${NC}"
# Check if port 3001 is in use
if check_port 3001; then
  echo -e "${YELLOW}Port 3001 is already in use. Killing the process...${NC}"
  kill_port_process 3001
  sleep 2
fi

cd frontend
PORT=3001 npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"
cd ..

# Wait a moment for the frontend to initialize
sleep 5

# 4. Start the monitoring script
echo -e "\n${BLUE}Starting Service Monitor...${NC}"
./monitor_services.sh > logs/monitor.log 2>&1 &
MONITOR_PID=$!
echo "Monitor started with PID: $MONITOR_PID"

echo -e "\n${GREEN}All ArbitrageX services have been started!${NC}"
echo -e "Bot PID: $BOT_PID"
echo -e "API Server PID: $API_PID"
echo -e "Frontend PID: $FRONTEND_PID"
echo -e "Monitor PID: $MONITOR_PID"
echo -e "\n${YELLOW}Access the dashboard at: http://localhost:3001${NC}"
echo -e "${YELLOW}API endpoints available at: http://localhost:3000${NC}"
echo -e "\n${BLUE}Log files are available in the logs directory${NC}"
echo -e "To stop all services, run: ./stop_arbitragex.sh" 