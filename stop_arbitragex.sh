#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== ArbitrageX System Shutdown ===${NC}"
echo "This script will stop all ArbitrageX services"

# Function to kill processes by pattern
kill_process() {
  local pattern=$1
  local service_name=$2
  
  pids=$(pgrep -f "$pattern")
  if [ ! -z "$pids" ]; then
    echo -e "${YELLOW}Stopping $service_name (PIDs: $pids)${NC}"
    kill -9 $pids
    echo -e "${GREEN}$service_name stopped successfully${NC}"
    return 0
  else
    echo -e "${RED}No running $service_name found${NC}"
    return 1
  fi
}

# Function to kill processes using a specific port
kill_port_process() {
  local port=$1
  local service_name=$2
  
  pid=$(lsof -t -i:$port)
  if [ ! -z "$pid" ]; then
    echo -e "${YELLOW}Stopping $service_name on port $port (PID: $pid)${NC}"
    kill -9 $pid
    echo -e "${GREEN}$service_name stopped successfully${NC}"
    return 0
  else
    echo -e "${RED}No process found using port $port${NC}"
    return 1
  fi
}

# 1. Stop the Bot
echo -e "\n${BLUE}Stopping ArbitrageX Bot...${NC}"
kill_process "bot.py" "ArbitrageX Bot"
kill_process "bot:start" "ArbitrageX Bot"

# 2. Stop the API Server
echo -e "\n${BLUE}Stopping API Server...${NC}"
kill_port_process 3000 "API Server"
kill_process "api/server.py" "API Server"

# 3. Stop the Frontend
echo -e "\n${BLUE}Stopping Frontend Dashboard...${NC}"
kill_port_process 3001 "Frontend Dashboard"
kill_process "next dev" "Frontend Dashboard"

# 4. Stop the Monitor
echo -e "\n${BLUE}Stopping Service Monitor...${NC}"
kill_process "monitor_services.sh" "Service Monitor"

# Check if any processes are still running
echo -e "\n${BLUE}Verifying all services are stopped...${NC}"
sleep 2

bot_running=$(pgrep -f "bot.py" || pgrep -f "bot:start")
api_running=$(pgrep -f "api/server.py" || lsof -t -i:3000)
frontend_running=$(pgrep -f "next dev" || lsof -t -i:3001)
monitor_running=$(pgrep -f "monitor_services.sh")

if [ -z "$bot_running" ] && [ -z "$api_running" ] && [ -z "$frontend_running" ] && [ -z "$monitor_running" ]; then
  echo -e "${GREEN}All ArbitrageX services have been stopped successfully!${NC}"
else
  echo -e "${RED}Some services may still be running:${NC}"
  [ ! -z "$bot_running" ] && echo -e "${RED}Bot is still running${NC}"
  [ ! -z "$api_running" ] && echo -e "${RED}API Server is still running${NC}"
  [ ! -z "$frontend_running" ] && echo -e "${RED}Frontend is still running${NC}"
  [ ! -z "$monitor_running" ] && echo -e "${RED}Monitor is still running${NC}"
  
  echo -e "\n${YELLOW}You may need to manually kill these processes${NC}"
fi

echo -e "\n${BLUE}Shutdown process completed${NC}" 