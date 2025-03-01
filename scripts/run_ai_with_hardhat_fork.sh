#!/bin/bash
# ArbitrageX AI with Hardhat Mainnet Fork
# This script starts a Hardhat mainnet fork and runs the AI system against it.

# Default values
FORK_BLOCK="latest"
RUN_TIME=300
MODULES="strategy_optimizer,backtesting,trade_analyzer,network_adaptation,integration"
VISUALIZE=true
SAVE_RESULTS=true

# Display help message
function show_help {
    echo "ArbitrageX AI with Hardhat Mainnet Fork"
    echo "Usage: ./run_ai_with_hardhat_fork.sh [options]"
    echo ""
    echo "Options:"
    echo "  --fork-block <number>  Block number to fork from (default: latest)"
    echo "  --run-time <secs>      How long to run the AI system (in seconds)"
    echo "                         Default: $RUN_TIME"
    echo "  --modules <list>       Comma-separated list of modules to run"
    echo "                         Default: $MODULES"
    echo "  --no-visualize         Disable visualization"
    echo "  --no-save-results      Disable saving results"
    echo "  --help                 Display this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_ai_with_hardhat_fork.sh"
    echo "  ./run_ai_with_hardhat_fork.sh --fork-block 12345678"
    echo "  ./run_ai_with_hardhat_fork.sh --run-time 600"
    echo "  ./run_ai_with_hardhat_fork.sh --modules strategy_optimizer,backtesting"
    exit 0
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --fork-block)
            FORK_BLOCK="$2"
            shift 2
            ;;
        --run-time)
            RUN_TIME="$2"
            shift 2
            ;;
        --modules)
            MODULES="$2"
            shift 2
            ;;
        --no-visualize)
            VISUALIZE=false
            shift
            ;;
        --no-save-results)
            SAVE_RESULTS=false
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

# Ensure we're in the project root
if [ ! -f "hardhat.config.ts" ]; then
    echo "Error: This script must be run from the project root directory"
    exit 1
fi

# Create results directory
mkdir -p results

# Log file
LOG_FILE="results/hardhat_fork_$(date +%Y%m%d_%H%M%S).log"
echo "Logging to $LOG_FILE"

# Start Hardhat node with mainnet fork
echo "Starting Hardhat node with mainnet fork..."
echo "Block number: $FORK_BLOCK"

# Start Hardhat node in the background
npx hardhat node --fork https://eth-mainnet.g.alchemy.com/v2/${ALCHEMY_API_KEY} --fork-block-number $FORK_BLOCK > $LOG_FILE 2>&1 &
HARDHAT_PID=$!

# Wait for Hardhat node to start
echo "Waiting for Hardhat node to start..."
sleep 10

# Check if Hardhat node is running
if ! ps -p $HARDHAT_PID > /dev/null; then
    echo "Error: Hardhat node failed to start. Check $LOG_FILE for details."
    exit 1
fi

echo "Hardhat node started with PID $HARDHAT_PID"

# Create fork configuration
echo "Creating fork configuration..."
cat > backend/ai/hardhat_fork_config.json << EOL
{
  "mode": "mainnet_fork",
  "fork_url": "http://localhost:8545",
  "fork_block_number": "$FORK_BLOCK",
  "networks": ["ethereum"],
  "tokens": {
    "ethereum": ["WETH", "USDC", "DAI", "USDT", "WBTC", "LINK"]
  },
  "dexes": {
    "ethereum": ["uniswap_v3", "sushiswap", "curve", "balancer"]
  },
  "gas_price_multiplier": 1.1,
  "slippage_tolerance": 0.005,
  "execution_timeout_ms": 5000,
  "simulation_only": true,
  "log_level": "INFO"
}
EOL

# Deploy contracts to the fork
echo "Deploying contracts to the fork..."
npx hardhat run scripts/deploy.ts --network localhost >> $LOG_FILE 2>&1

# Run AI system with fork configuration
echo "Running AI system with fork configuration..."
cd backend/ai

# Build command
CMD="./run_ai_system.sh --modules $MODULES --run-time $RUN_TIME --fork-config hardhat_fork_config.json"

if [ "$VISUALIZE" = true ]; then
    CMD="$CMD --visualize"
fi

if [ "$SAVE_RESULTS" = true ]; then
    CMD="$CMD --save-results"
fi

echo "Running command: $CMD"
$CMD

# Cleanup
echo "Cleaning up..."
kill $HARDHAT_PID

echo "Done!" 