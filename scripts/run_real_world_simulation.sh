#!/bin/bash
# Run the ArbitrageX Real-World Simulation
# This script runs a comprehensive simulation that mimics a real-world scenario

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

# Create results directory
mkdir -p backend/ai/results/real_world_simulation

# Parse command line arguments
USE_MAINNET_FORK=true
USE_TESTNET=false
MARKET_DATA=""
SIMULATION_TIME=3600

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mainnet-fork)
            USE_MAINNET_FORK=true
            shift
            ;;
        --testnet)
            USE_TESTNET=true
            USE_MAINNET_FORK=false
            shift
            ;;
        --market-data)
            MARKET_DATA="$2"
            shift 2
            ;;
        --simulation-time)
            SIMULATION_TIME="$2"
            shift 2
            ;;
        --min-trades|--max-trades|--initial-capital|--networks|--token-pairs|--dexes|--debug|--use-historical-data|--enable-learning|--flash-loan-enabled|--no-historical-data|--no-learning|--no-flash-loan)
            # Pass these arguments directly to the Python script
            if [[ "$1" == *"="* ]]; then
                PYTHON_ARGS+=" $1"
                shift
            elif [[ "$1" != --debug && "$1" != --use-historical-data && "$1" != --enable-learning && "$1" != --flash-loan-enabled && "$1" != --no-historical-data && "$1" != --no-learning && "$1" != --no-flash-loan ]]; then
                PYTHON_ARGS+=" $1 $2"
                shift 2
            else
                PYTHON_ARGS+=" $1"
                shift
            fi
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build the command
CMD="cd backend/ai && python3 run_real_world_simulation.py"

# Add simulation time
CMD+=" --simulation-time $SIMULATION_TIME"

# Add any other arguments passed to the script
if [ -n "$PYTHON_ARGS" ]; then
    CMD+=" $PYTHON_ARGS"
fi

# Print the command
echo "Running command: $CMD"

# Run the simulation
eval $CMD

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
LATEST_REPORT=$(find backend/ai/results/real_world_simulation -name "simulation_report_*.json" | sort -r | head -n 1)
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