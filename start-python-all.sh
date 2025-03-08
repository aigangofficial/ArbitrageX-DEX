#!/bin/bash
# Startup script for the entire Python ArbitrageX system

# Set the Python path to include the current directory
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Log startup
echo "Starting ArbitrageX Python system..."
echo "PYTHONPATH: $PYTHONPATH"

# Start the API server in the background
echo "Starting API server..."
./start-python-api.sh &
API_PID=$!

# Give the API server a moment to start
sleep 2

# Start the bot
echo "Starting bot..."
./start-python-bot.sh &
BOT_PID=$!

# Function to handle shutdown
function cleanup {
  echo "Shutting down ArbitrageX Python system..."
  kill $API_PID $BOT_PID 2>/dev/null
  wait $API_PID $BOT_PID 2>/dev/null
  echo "Shutdown complete."
  exit 0
}

# Set up signal handling
trap cleanup SIGINT SIGTERM

# Wait for processes to finish
echo "ArbitrageX Python system is running. Press Ctrl+C to stop."
wait $API_PID $BOT_PID 