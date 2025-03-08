#!/bin/bash
# Startup script for the Python ArbitrageX bot

# Set the Python path to include the current directory
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Log startup
echo "Starting ArbitrageX Python bot..."
echo "PYTHONPATH: $PYTHONPATH"

# Run the bot
python backend/bot/bot_core.py

# Exit with the bot's exit code
exit $? 