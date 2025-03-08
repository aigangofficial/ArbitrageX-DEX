#!/bin/bash
# ArbitrageX Deploy to Hardhat Fork
# This script deploys contracts to a Hardhat fork and saves the addresses for the Strategy Optimizer.

# Check if Hardhat node is running
echo "Checking if Hardhat node is running..."
if ! curl -s -X POST -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' http://localhost:8545 > /dev/null; then
    echo "Error: Hardhat node is not running. Please start it with:"
    echo "npx hardhat node --fork https://mainnet.infura.io/v3/YOUR_API_KEY --fork-block-number 19261000"
    exit 1
fi

echo "Hardhat node is running."

# Deploy contracts to the fork
echo "Deploying contracts to the fork..."
npx hardhat run scripts/deploy.ts --network localhost

# Check if deployment was successful
if [ $? -ne 0 ]; then
    echo "Error: Contract deployment failed."
    exit 1
fi

# Check if contract addresses file exists
if [ ! -f "backend/config/contractAddresses.json" ]; then
    echo "Error: Contract addresses file not found."
    echo "Creating directory structure..."
    mkdir -p backend/config
    
    # Create a default contract addresses file
    echo "Creating default contract addresses file..."
    cat > backend/config/contractAddresses.json << EOL
{
    "arbitrageExecutor": "",
    "flashLoanService": ""
}
EOL
fi

# Copy contract addresses to backend config
echo "Copying contract addresses to backend config..."
cp artifacts/contractAddresses.json backend/config/

echo "Contracts deployed successfully to the Hardhat fork."
echo "Contract addresses saved to backend/config/contractAddresses.json"

# Run the Strategy Optimizer with the fork configuration
echo "Do you want to run the Strategy Optimizer with the fork configuration? (y/n)"
read -r run_optimizer

if [ "$run_optimizer" = "y" ]; then
    echo "Running Strategy Optimizer with fork configuration..."
    cd backend/ai
    python3 run_mainnet_fork_test.py --fork-block 0 --run-time 60 --modules strategy_optimizer
else
    echo "Skipping Strategy Optimizer."
fi

echo "Done!" 