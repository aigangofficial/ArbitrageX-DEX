#!/bin/bash
# Startup script for the Python ArbitrageX API server

# Set the Python path to include the current directory
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Log startup
echo "Starting ArbitrageX Python API server..."
echo "PYTHONPATH: $PYTHONPATH"

# Run the API server
python backend/api/server.py

# Exit with the server's exit code
exit $? 