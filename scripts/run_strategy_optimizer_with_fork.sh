#!/bin/bash
# ArbitrageX Strategy Optimizer with Hardhat Fork
# This script runs the entire process of starting a Hardhat fork, deploying contracts,
# and running the Strategy Optimizer with real blockchain data.

# Default values
FORK_BLOCK=0
RUN_TIME=300
MODULES="strategy_optimizer"
NETWORK="mainnet"
FORK_URL=${ETHEREUM_RPC_URL:-"https://eth-mainnet.g.alchemy.com/v2/your-api-key"}

# Display help message
function show_help {
    echo "ArbitrageX Strategy Optimizer with Hardhat Fork"
    echo "Usage: ./run_strategy_optimizer_with_fork.sh [options]"
    echo ""
    echo "Options:"
    echo "  --fork-block <number>  Block number to fork from (default: latest)"
    echo "  --fork-url <url>       URL of the Ethereum node to fork from"
    echo "                         Default: https://eth-mainnet.g.alchemy.com/v2/\${ALCHEMY_API_KEY}"
    echo "  --run-time <secs>      How long to run the optimizer (in seconds)"
    echo "                         Default: $RUN_TIME"
    echo "  --modules <list>       Comma-separated list of modules to run"
    echo "                         Default: $MODULES"
    echo "  --network <network>    Network to run the optimizer on"
    echo "                         Default: $NETWORK"
    echo "  --help                 Display this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_strategy_optimizer_with_fork.sh"
    echo "  ./run_strategy_optimizer_with_fork.sh --fork-block 19261000"
    echo "  ./run_strategy_optimizer_with_fork.sh --run-time 600"
    echo "  ./run_strategy_optimizer_with_fork.sh --modules strategy_optimizer,backtesting"
    exit 0
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --fork-block)
            FORK_BLOCK="$2"
            shift
            shift
            ;;
        --run-time)
            RUN_TIME="$2"
            shift
            shift
            ;;
        --modules)
            MODULES="$2"
            shift
            shift
            ;;
        --network)
            NETWORK="$2"
            shift
            shift
            ;;
        --fork-url)
            FORK_URL="$2"
            shift
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            ;;
    esac
done

# Check if .env file exists and source it
if [ -f .env ]; then
    echo "Loading environment variables from .env file"
    export $(grep -v '^#' .env | xargs)
fi

# Ensure the FORK_URL is set
if [[ -z "$FORK_URL" ]]; then
    echo "Error: FORK_URL is not set. Please set it in .env file or provide it as an argument."
    exit 1
fi

# Ensure we're in the project root
if [ ! -f "hardhat.config.ts" ]; then
    echo "Error: This script must be run from the project root directory"
    exit 1
fi

# Create results directory
mkdir -p results

# Log file
LOG_FILE="results/strategy_optimizer_fork_$(date +%Y%m%d_%H%M%S).log"
echo "Logging to $LOG_FILE"

# Kill any existing Hardhat node
pkill -f "hardhat node" || true

# Start Hardhat node in fork mode in the background
echo "Starting Hardhat node in fork mode..."
echo "Fork URL: $FORK_URL"
echo "Fork Block: $FORK_BLOCK"

# Start Hardhat node with fork
if [ "$FORK_BLOCK" -eq 0 ]; then
    npx hardhat node --fork $FORK_URL > $LOG_FILE 2>&1 &
else
    npx hardhat node --fork $FORK_URL --fork-block-number $FORK_BLOCK > $LOG_FILE 2>&1 &
fi

# Get the PID of the Hardhat node
HARDHAT_PID=$!

# Wait for Hardhat node to start
echo "Waiting for Hardhat node to start..."
sleep 10

# Check if Hardhat node is running
if ! ps -p $HARDHAT_PID > /dev/null; then
    echo "Error: Hardhat node failed to start. Check $LOG_FILE for details."
    exit 1
fi

echo "Hardhat node started with PID: $HARDHAT_PID"

# Deploy contracts to the fork
echo "Deploying contracts to the fork..."
npx hardhat run scripts/deploy.ts --network localhost >> $LOG_FILE 2>&1

# Check if deployment was successful
if [ $? -ne 0 ]; then
    echo "Error: Contract deployment failed. Check $LOG_FILE for details."
    
    # Kill Hardhat node if we started it
    if [ -n "$HARDHAT_PID" ]; then
        echo "Cleaning up..."
        kill $HARDHAT_PID
    fi
    
    exit 1
fi

echo "Contracts deployed successfully to the Hardhat fork."

# Create fork configuration
echo "Creating fork configuration..."
cat > backend/ai/fork_config.json << EOL
{
  "mode": "mainnet_fork",
  "fork_url": "http://localhost:8545",
  "fork_block_number": "$FORK_BLOCK",
  "networks": ["ethereum"],
  "tokens": {
    "ethereum": ["WETH", "USDC", "DAI", "WBTC"]
  },
  "dexes": {
    "ethereum": ["uniswap_v2", "sushiswap"]
  },
  "gas_price_multiplier": 1.1,
  "slippage_tolerance": 0.005,
  "execution_timeout_ms": 5000,
  "simulation_only": false,
  "log_level": "INFO"
}
EOL

# Install required Python packages
echo "Checking for required Python packages..."
pip install web3 > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Error: Failed to install web3 package. Please install it manually:"
    echo "pip install web3"
    
    # Kill Hardhat node if we started it
    if [ -n "$HARDHAT_PID" ]; then
        echo "Cleaning up..."
        kill $HARDHAT_PID
    fi
    
    exit 1
fi

# Set environment variables for the strategy optimizer
export FORK_MODE=true
export HARDHAT_FORK_URL="http://localhost:8545"
export FORK_NETWORK=$NETWORK

# Run the strategy optimizer
echo "Running strategy optimizer with modules: $MODULES for $RUN_TIME seconds..."
cd backend/ai
python run_mainnet_fork_test.py --modules $MODULES --run-time $RUN_TIME --fork-url $HARDHAT_FORK_URL --network $NETWORK

# Capture the exit code
EXIT_CODE=$?

# Kill the Hardhat node
echo "Stopping Hardhat node..."
kill $HARDHAT_PID

echo "Strategy optimizer completed with exit code: $EXIT_CODE"
exit $EXIT_CODE 