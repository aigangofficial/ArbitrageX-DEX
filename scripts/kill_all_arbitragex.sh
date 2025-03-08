#!/bin/bash

# ArbitrageX Kill Script
# This script kills all ArbitrageX processes

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

# Set timestamp format
timestamp() {
  date "+%Y-%m-%d %H:%M:%S"
}

# Function to log messages
log() {
  echo -e "${BLUE}$(timestamp) - $1${NC}" | tee -a "$BASE_DIR/logs/kill.log"
}

# Function to check if a port is in use
is_port_in_use() {
  lsof -i :"$1" >/dev/null 2>&1
  return $?
}

# Kill all ArbitrageX processes
log "Killing all ArbitrageX processes..."

# Kill monitor processes first to prevent them from restarting other services
log "Killing monitor processes..."

# First try to kill monitor processes using PID file
monitor_pid=$(cat logs/monitor.pid 2>/dev/null)
if [ ! -z "$monitor_pid" ]; then
  log "Killing monitor process with PID $monitor_pid..."
  kill -9 $monitor_pid 2>/dev/null
fi

# Find and kill all monitor processes by name
monitor_pids=$(ps aux | grep "monitor_services.sh" | grep -v grep | awk '{print $2}')
if [ ! -z "$monitor_pids" ]; then
  for pid in $monitor_pids; do
    log "Killing monitor process with PID $pid..."
    kill -9 $pid 2>/dev/null
  done
fi

# Find and kill all bash processes running the monitor script
bash_monitor_pids=$(ps aux | grep "/bin/bash.*monitor_services.sh" | grep -v grep | awk '{print $2}')
if [ ! -z "$bash_monitor_pids" ]; then
  for pid in $bash_monitor_pids; do
    log "Killing bash monitor process with PID $pid..."
    kill -9 $pid 2>/dev/null
  done
fi

# Kill API server processes
log "Killing API server processes..."
api_pids=$(ps aux | grep "node.*api" | grep -v grep | awk '{print $2}')
if [ ! -z "$api_pids" ]; then
  for pid in $api_pids; do
    log "Killing API server process with PID $pid..."
    kill -9 $pid 2>/dev/null
  done
fi

# Kill frontend processes
log "Killing frontend processes..."
frontend_pids=$(ps aux | grep "node.*frontend" | grep -v grep | awk '{print $2}')
if [ ! -z "$frontend_pids" ]; then
  for pid in $frontend_pids; do
    log "Killing frontend process with PID $pid..."
    kill -9 $pid 2>/dev/null
  done
fi

# Kill bot processes
log "Killing bot processes..."
bot_pids=$(ps aux | grep "bot" | grep -v grep | awk '{print $2}')
if [ ! -z "$bot_pids" ]; then
  for pid in $bot_pids; do
    log "Killing bot process with PID $pid..."
    kill -9 $pid 2>/dev/null
  done
fi

# Kill learning loop processes
log "Killing learning loop processes..."
# First try to kill learning loop using PID file
learning_loop_pid=$(cat logs/learning_loop.pid 2>/dev/null)
if [ ! -z "$learning_loop_pid" ]; then
  log "Killing learning loop process with PID $learning_loop_pid..."
  kill -9 $learning_loop_pid 2>/dev/null
fi

# Find and kill all learning loop processes by name
learning_loop_pids=$(ps aux | grep "python.*start_learning_loop.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$learning_loop_pids" ]; then
  for pid in $learning_loop_pids; do
    log "Killing learning loop process with PID $pid..."
    kill -9 $pid 2>/dev/null
  done
fi

# Kill hardhat processes
log "Killing hardhat processes..."
hardhat_pids=$(ps aux | grep "hardhat node" | grep -v grep | awk '{print $2}')
if [ ! -z "$hardhat_pids" ]; then
  for pid in $hardhat_pids; do
    log "Killing hardhat process with PID $pid..."
    kill -9 $pid 2>/dev/null
  done
fi

# Wait for processes to terminate
sleep 2

# Double-check if monitor is still running and force kill it
log "Double-checking if monitor is still running..."
monitor_pids_check=$(ps aux | grep "monitor_services.sh" | grep -v grep | awk '{print $2}')
if [ ! -z "$monitor_pids_check" ]; then
  log "Monitor is still running! Force killing with extreme prejudice..."
  for pid in $monitor_pids_check; do
    log "Force killing monitor process with PID $pid..."
    kill -9 $pid 2>/dev/null
    
    # If process is still running after kill -9, try more aggressive methods
    if ps -p $pid > /dev/null 2>&1; then
      log "Process $pid is still running after kill -9! Using pkill..."
      pkill -9 -f "monitor_services.sh"
    fi
  done
fi

# Check if ports are still in use
for port in 3001 3002 8545; do
  if is_port_in_use $port; then
    log "Port $port is still in use. Forcing termination..."
    pid=$(lsof -i :$port | grep LISTEN | awk '{print $2}')
    if [ ! -z "$pid" ]; then
      log "Killing process with PID $pid..."
      kill -9 $pid 2>/dev/null
      sleep 1
    fi
  fi
done

# Remove PID files to prevent stale references
log "Removing PID files..."
rm -f logs/*.pid 2>/dev/null

# Final check to make sure all processes are terminated
log "Performing final check for any remaining processes..."
remaining_pids=$(ps aux | grep -E "hardhat|node.*api|node.*frontend|monitor_services.sh|bot|python.*start_learning_loop.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$remaining_pids" ]; then
  log "Found remaining processes. Killing them..."
  for pid in $remaining_pids; do
    log "Killing process with PID $pid..."
    kill -9 $pid 2>/dev/null
  done
  
  # Final verification
  sleep 1
  final_check=$(ps aux | grep -E "hardhat|node.*api|node.*frontend|monitor_services.sh|bot|python.*start_learning_loop.py" | grep -v grep | awk '{print $2}')
  if [ ! -z "$final_check" ]; then
    log "WARNING: Some processes could not be terminated. Manual intervention may be required."
    for pid in $final_check; do
      log "Process $pid is still running."
    done
  fi
fi

log "All ArbitrageX processes terminated."
echo -e "${GREEN}All ArbitrageX processes have been terminated.${NC}" 