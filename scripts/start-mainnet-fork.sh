#!/bin/bash
# Start a mainnet fork and deploy the contracts

# Set up colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting ArbitrageX on Mainnet Fork${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
  echo -e "${RED}Error: .env file not found. Please create one from .env.example${NC}"
  exit 1
fi

# Extract MAINNET_RPC_URL from .env
MAINNET_RPC_URL=$(grep MAINNET_RPC_URL .env | cut -d '=' -f2)

if [ -z "$MAINNET_RPC_URL" ]; then
  echo -e "${RED}Error: MAINNET_RPC_URL not found in .env file${NC}"
  exit 1
fi

# Set the fork block number
FORK_BLOCK_NUMBER=$(grep FORK_BLOCK_NUMBER .env | cut -d '=' -f2 || echo "19261000")

echo -e "${YELLOW}Starting Hardhat node with mainnet fork at block ${FORK_BLOCK_NUMBER}...${NC}"

# Check if port 8545 is already in use
if lsof -Pi :8545 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${RED}Error: Port 8545 is already in use. Another node might be running.${NC}"
    echo -e "${YELLOW}Try running: lsof -i :8545 to see what's using the port${NC}"
    echo -e "${YELLOW}Then kill the process with: kill -9 PID${NC}"
    exit 1
fi

# Start Hardhat node in the background with output redirected to a log file
npx hardhat node --fork $MAINNET_RPC_URL --fork-block-number $FORK_BLOCK_NUMBER > hardhat-node.log 2>&1 &
NODE_PID=$!

# Wait for node to start
echo -e "${YELLOW}Waiting for node to start...${NC}"

# Wait longer and check if the node is actually running
MAX_ATTEMPTS=60  # Increased from 30 to 60
ATTEMPT=0
NODE_READY=false

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  ATTEMPT=$((ATTEMPT+1))
  echo -e "${YELLOW}Waiting for node to initialize (attempt $ATTEMPT/$MAX_ATTEMPTS)...${NC}"
  
  # Check if the node is responding
  if curl -s -X POST -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' http://127.0.0.1:8545 | grep -q "result"; then
    NODE_READY=true
    echo -e "${GREEN}Node is ready!${NC}"
    # Wait a bit more to ensure the node is fully initialized
    sleep 5
    break
  fi
  
  # Check if the node process is still running
  if ! ps -p $NODE_PID > /dev/null; then
    echo -e "${RED}Error: Hardhat node process died unexpectedly${NC}"
    echo -e "${YELLOW}Check hardhat-node.log for details${NC}"
    exit 1
  fi
  
  sleep 3  # Increased from 2 to 3 seconds
done

if [ "$NODE_READY" = false ]; then
  echo -e "${RED}Error: Hardhat node failed to start after multiple attempts${NC}"
  echo -e "${YELLOW}Check hardhat-node.log for details${NC}"
  kill $NODE_PID 2>/dev/null
  exit 1
fi

# Deploy contracts
echo -e "${YELLOW}Deploying contracts to mainnet fork...${NC}"

# Run the deployment in a separate process
npx hardhat run scripts/deploy.ts --network localhost

# Check if deployment was successful
DEPLOY_STATUS=$?
if [ $DEPLOY_STATUS -eq 0 ]; then
  echo -e "${GREEN}✅ Deployment successful!${NC}"
  echo -e "${YELLOW}Hardhat node is running in the background with PID ${NODE_PID}${NC}"
  echo -e "${YELLOW}To stop the node, run: kill ${NODE_PID}${NC}"
  echo -e "${GREEN}🎉 ArbitrageX is now running on a mainnet fork!${NC}"
  echo -e "${YELLOW}Press Ctrl+C to stop the node${NC}"
  
  # Keep the script running to keep the node running
  wait $NODE_PID
else
  echo -e "${RED}❌ Deployment failed with status code ${DEPLOY_STATUS}!${NC}"
  echo -e "${YELLOW}Stopping Hardhat node...${NC}"
  kill $NODE_PID 2>/dev/null
  echo -e "${YELLOW}Check the output above for deployment errors${NC}"
  exit 1
fi 