#!/bin/bash
# Run a simple simulation with the correct arguments

# Set the directory to the project root
cd "$(dirname "$0")/.."

# Check if the Hardhat node is running
if ! curl -s http://localhost:8546 > /dev/null; then
    echo "Starting Hardhat node in fork mode..."
    npx hardhat node --fork ${MAINNET_RPC_URL:-https://mainnet.infura.io/v3/59de174d2d904c1980b975abae2ef0ec} --port 8546 &
    HARDHAT_PID=$!
    
    # Wait for the node to start
    echo "Waiting for Hardhat node to start..."
    sleep 10
    
    # Check if the node started successfully
    if ! curl -s http://localhost:8546 > /dev/null; then
        echo "Failed to start Hardhat node. Please check your RPC URL and try again."
        exit 1
    fi
    
    echo "Hardhat node started successfully."
else
    echo "Hardhat node is already running."
    HARDHAT_PID=""
fi

# Run the simulation
echo "Running simulation..."
python3 backend/ai/run_simple_simulation.py

# Check if the simulation was successful
if [ $? -ne 0 ]; then
    echo "Simulation failed."
    
    # Kill the Hardhat node if we started it
    if [ -n "$HARDHAT_PID" ]; then
        echo "Stopping Hardhat node..."
        kill $HARDHAT_PID
    fi
    
    exit 1
fi

echo "Simulation completed successfully."

# Find the latest report
LATEST_REPORT=$(find backend/ai/results/simple_simulation -name "simulation_report_*.json" | sort -r | head -n 1)
LATEST_SUMMARY=${LATEST_REPORT%.*}_summary.txt

if [ -f "$LATEST_SUMMARY" ]; then
    echo "Simulation summary:"
    echo "===================="
    cat "$LATEST_SUMMARY"
    echo "===================="
    echo "Full report available at: $LATEST_REPORT"
else
    echo "No summary report found."
fi

# Kill the Hardhat node if we started it
if [ -n "$HARDHAT_PID" ]; then
    echo "Stopping Hardhat node..."
    kill $HARDHAT_PID
fi

exit 0 