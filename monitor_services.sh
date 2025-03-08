#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== ArbitrageX Services Monitor ===${NC}"
echo "Monitoring all ArbitrageX services..."

# Function to check if a process is running
check_process() {
  local process_pattern=$1
  local service_name=$2
  
  if pgrep -f "$process_pattern" > /dev/null; then
    echo -e "${GREEN}✓ $service_name is running${NC}"
    return 0
  else
    echo -e "${RED}✗ $service_name is not running${NC}"
    return 1
  fi
}

# Function to check if a port is in use
check_port() {
  local port=$1
  local service_name=$2
  
  if lsof -i :$port -sTCP:LISTEN > /dev/null; then
    echo -e "${GREEN}✓ $service_name is listening on port $port${NC}"
    return 0
  else
    echo -e "${RED}✗ $service_name is not listening on port $port${NC}"
    return 1
  fi
}

# Function to check log files
check_logs() {
  local log_file=$1
  local service_name=$2
  
  if [ -f "$log_file" ]; then
    echo -e "${GREEN}✓ Log file for $service_name exists${NC}"
    echo -e "${CYAN}Last 5 lines of $service_name log:${NC}"
    tail -n 5 "$log_file"
    return 0
  else
    echo -e "${YELLOW}! Log file for $service_name not found: $log_file${NC}"
    return 1
  fi
}

# Main monitoring loop
echo "Press Ctrl+C to stop monitoring"
iteration=1

while true; do
  echo -e "\n${BLUE}=== Monitoring Iteration $iteration ===${NC}"
  echo "Time: $(date)"
  
  # Check bot service
  echo -e "\n${YELLOW}Checking Arbitrage Bot:${NC}"
  check_process "bot.py" "Arbitrage Bot"
  check_logs "logs/bot.log" "Arbitrage Bot"
  
  # Check API service
  echo -e "\n${YELLOW}Checking API Server:${NC}"
  check_process "api/server.py" "API Server"
  check_port 3000 "API Server"
  check_logs "logs/api.log" "API Server"
  
  # Check Frontend service
  echo -e "\n${YELLOW}Checking Frontend:${NC}"
  check_process "next dev" "Frontend"
  check_port 3001 "Frontend"
  check_logs "logs/frontend.log" "Frontend"
  
  # Check for trade activity
  echo -e "\n${YELLOW}Checking for Recent Trade Activity:${NC}"
  if [ -d "backend/results" ]; then
    recent_trades=$(find backend/results -type f -name "*.json" -mmin -5 | wc -l)
    if [ $recent_trades -gt 0 ]; then
      echo -e "${GREEN}✓ Found $recent_trades new trade results in the last 5 minutes${NC}"
    else
      echo -e "${YELLOW}! No new trade results in the last 5 minutes${NC}"
    fi
  else
    echo -e "${YELLOW}! Results directory not found${NC}"
  fi
  
  # Wait before next check
  echo -e "\nWaiting 30 seconds before next check..."
  sleep 30
  
  iteration=$((iteration + 1))
done 