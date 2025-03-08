#!/bin/bash
# Restart Learning Loop Script
# This script stops any existing learning loop processes and starts a new one with improved implementation

# Set the working directory to the project root
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

# Configuration
PYTHON_PATH=${PYTHON_PATH:-"python3"}
LEARNING_LOOP_SCRIPT="backend/ai/start_learning_loop.py"
LEARNING_LOOP_LOG="logs/learning_loop.log"
LEARNING_LOOP_PID_FILE="backend/ai/learning_loop.pid"
DEBUG_MODE=false
UPDATE_INTERVAL=30

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --debug)
      DEBUG_MODE=true
      shift
      ;;
    --update-interval)
      UPDATE_INTERVAL="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --debug                Enable debug logging"
      echo "  --update-interval N    Set status file update interval in seconds (default: 30)"
      echo "  --help                 Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to check if the learning loop is running
check_learning_loop() {
  if [ -f "$LEARNING_LOOP_PID_FILE" ]; then
    PID=$(cat "$LEARNING_LOOP_PID_FILE")
    if ps -p "$PID" > /dev/null; then
      echo "Learning loop is running with PID $PID"
      return 0
    else
      echo "Learning loop PID file exists but process is not running"
      rm -f "$LEARNING_LOOP_PID_FILE"
      return 1
    fi
  else
    echo "Learning loop is not running"
    return 1
  fi
}

# Function to stop the learning loop
stop_learning_loop() {
  if [ -f "$LEARNING_LOOP_PID_FILE" ]; then
    PID=$(cat "$LEARNING_LOOP_PID_FILE")
    if ps -p "$PID" > /dev/null; then
      echo "Stopping learning loop process (PID: $PID)..."
      kill "$PID"
      sleep 2
      if ps -p "$PID" > /dev/null; then
        echo "Process did not terminate gracefully, forcing..."
        kill -9 "$PID"
      fi
    fi
    rm -f "$LEARNING_LOOP_PID_FILE"
  fi
  
  # Also check for any other learning loop processes
  echo "Checking for other learning loop processes..."
  PIDS=$(pgrep -f "python.*start_learning_loop.py")
  if [ -n "$PIDS" ]; then
    echo "Found additional learning loop processes, stopping them..."
    for PID in $PIDS; do
      echo "Stopping process $PID..."
      kill "$PID" 2>/dev/null
      sleep 1
      if ps -p "$PID" > /dev/null; then
        echo "Process did not terminate gracefully, forcing..."
        kill -9 "$PID" 2>/dev/null
      fi
    done
  fi
}

# Stop any existing learning loop processes
echo "Checking for existing learning loop processes..."
check_learning_loop
if [ $? -eq 0 ]; then
  echo "Stopping existing learning loop process..."
  stop_learning_loop
fi

# Start the learning loop
echo "Starting learning loop..."
CMD="$PYTHON_PATH $LEARNING_LOOP_SCRIPT --update-interval $UPDATE_INTERVAL"

if [ "$DEBUG_MODE" = true ]; then
  CMD="$CMD --debug"
  echo "Debug mode enabled"
fi

echo "Running command: $CMD"
nohup $CMD > "$LEARNING_LOOP_LOG" 2>&1 &
PID=$!

# Save the PID to a file
echo $PID > "$LEARNING_LOOP_PID_FILE"
echo "Learning loop started with PID $PID"
echo "Logs are being written to $LEARNING_LOOP_LOG"

# Wait a moment to ensure the process started successfully
sleep 2
if ps -p "$PID" > /dev/null; then
  echo "Learning loop is running successfully"
  
  # Check the status file
  STATUS_FILE="backend/ai/learning_loop_status.json"
  if [ -f "$STATUS_FILE" ]; then
    echo "Learning loop status file created successfully"
    echo "Status file contents:"
    cat "$STATUS_FILE"
  else
    echo "Warning: Learning loop status file not created yet"
  fi
else
  echo "Error: Learning loop failed to start"
  echo "Check the logs for details: $LEARNING_LOOP_LOG"
  exit 1
fi

echo "Learning loop restart completed successfully"
echo "To monitor the learning loop, use: tail -f $LEARNING_LOOP_LOG"
echo "To check the learning loop status, use: python3 backend/ai/learning_loop_monitor.py" 