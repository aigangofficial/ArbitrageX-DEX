#!/bin/bash

# ArbitrageX Service Monitor
# This script continuously monitors all services and restarts any that fail

# Color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Path to the process management script
MANAGE_SCRIPT="$(dirname $0)/manage_processes.sh"

# Log file
LOG_FILE="../logs/monitor.log"

# Create logs directory if it doesn't exist
mkdir -p $(dirname $LOG_FILE)

# Function to log messages
log() {
  local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
  echo -e "${timestamp} - $1" >> $LOG_FILE
}

# Function to check if a port is in use
check_port() {
  lsof -i:$1 > /dev/null 2>&1
  return $?
}

# Function to check and restart services if needed
check_and_restart() {
  log "Checking all ArbitrageX services..."
  
  # Check Hardhat node
  if ! check_port 8545; then
    log "Hardhat node is not running. Restarting..."
    $MANAGE_SCRIPT start-hardhat > /dev/null 2>&1
    sleep 5
  else
    log "Hardhat node is running."
  fi
  
  # Check API server
  if ! check_port 3002; then
    log "API server is not running. Restarting..."
    $MANAGE_SCRIPT start-api > /dev/null 2>&1
    sleep 5
  else
    log "API server is running."
  fi
  
  # Check frontend
  if ! check_port 3001; then
    log "Frontend is not running. Restarting..."
    $MANAGE_SCRIPT start-frontend > /dev/null 2>&1
    sleep 5
  else
    log "Frontend is running."
  fi
  
  # Check blockchain connectivity
  local blockchain_status=$(curl -s http://localhost:3002/api/v1/blockchain/health 2>/dev/null)
  if [[ "$blockchain_status" == *"connected"* ]]; then
    log "Blockchain connection is established."
  else
    # Add a counter to prevent continuous restarts
    if [[ -f /tmp/hardhat_restart_count ]]; then
      count=$(cat /tmp/hardhat_restart_count)
      if [[ $count -ge 3 ]]; then
        log "Hardhat node has been restarted 3 times already. Skipping restart to prevent loop."
        echo "0" > /tmp/hardhat_restart_count
        return
      else
        echo $((count+1)) > /tmp/hardhat_restart_count
      fi
    else
      echo "1" > /tmp/hardhat_restart_count
    fi
    
    log "Blockchain connection is not established. Restarting Hardhat node..."
    $MANAGE_SCRIPT kill-hardhat > /dev/null 2>&1
    sleep 2
    $MANAGE_SCRIPT start-hardhat > /dev/null 2>&1
    sleep 5
  fi
  
  # Check for new trade results
  local trade_results=$(curl -s http://localhost:3002/api/v1/trades 2>/dev/null)
  if [[ "$trade_results" == *"error"* || -z "$trade_results" ]]; then
    log "No new trade results found in the last 5 minutes."
  elif [[ "$trade_results" == *"\"success\":true"* && "$trade_results" == *"\"trades\":"* ]]; then
    # Extract the number of trades if possible
    local trade_count=$(echo "$trade_results" | grep -o '"trades":\[[^]]*\]' | grep -o '{' | wc -l)
    if [[ $trade_count -gt 0 ]]; then
      log "Found $trade_count trade results."
    else
      log "No new trade results found in the last 5 minutes."
    fi
  else
    log "No new trade results found in the last 5 minutes."
  fi
  
  # Check API health
  local api_health=$(curl -s http://localhost:3002/health 2>/dev/null)
  if [[ "$api_health" == *"healthy"* ]]; then
    log "API health check passed."
  else
    log "API health check failed. Response: $api_health"
  fi
  
  # Check frontend health
  local frontend_health=$(curl -s http://localhost:3001 2>/dev/null)
  if [[ -n "$frontend_health" ]]; then
    log "Frontend is accessible."
  else
    log "Frontend is not accessible."
  fi
  
  log "Service check completed."
}

# Function to handle termination signals
handle_exit() {
  log "Monitor service received termination signal. Shutting down..."
  exit 0
}

# Main monitoring loop
main() {
  log "Starting ArbitrageX service monitor..."
  
  # Set up signal handlers
  trap 'handle_exit' INT TERM
  
  # Initial check and restart
  check_and_restart
  
  # Continuous monitoring
  while true; do
    sleep 60  # Check every minute
    check_and_restart
  done
}

# Redirect all output to the log file
exec >> $LOG_FILE 2>&1

# Start the monitoring
main 