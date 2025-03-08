#!/bin/bash

# ArbitrageX Process Management Script
# This script helps manage the various processes required for the ArbitrageX project

# Color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a port is in use
check_port() {
  lsof -i:$1 > /dev/null 2>&1
  return $?
}

# Function to kill a process running on a specific port
kill_port() {
  if check_port $1; then
    echo -e "${YELLOW}Killing process on port $1...${NC}"
    
    # Get the PID of the process using the port
    local pid
    
    # Different command for macOS vs Linux
    if [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS
      pid=$(lsof -ti:$1)
    else
      # Linux
      pid=$(fuser $1/tcp 2>/dev/null)
    fi
    
    if [ -n "$pid" ]; then
      # Kill the process
      kill -9 $pid 2>/dev/null
      sleep 2
      
      if check_port $1; then
        echo -e "${RED}Failed to kill process on port $1.${NC}"
        return 1
      else
        echo -e "${GREEN}Process on port $1 killed.${NC}"
        return 0
      fi
    else
      echo -e "${RED}Could not find PID for process on port $1.${NC}"
      return 1
    fi
  else
    echo -e "${GREEN}No process found on port $1.${NC}"
    return 0
  fi
}

# Function to start the Hardhat node
start_hardhat() {
  if check_port 8545; then
    echo -e "${YELLOW}A process is already running on port 8545. Attempting to kill it...${NC}"
    kill_port 8545
    if [ $? -ne 0 ]; then
      echo -e "${RED}Failed to kill process on port 8545. Please kill it manually.${NC}"
      return 1
    fi
    # Wait a moment for the port to be released
    sleep 3
  fi

  echo -e "${BLUE}Starting Hardhat node on port 8545...${NC}"
  cd $(dirname $0)/..
  mkdir -p logs
  npx hardhat node --hostname 127.0.0.1 --port 8545 > logs/hardhat.log 2>&1 &
  sleep 5

  if check_port 8545; then
    echo -e "${GREEN}Hardhat node started successfully on port 8545.${NC}"
    return 0
  else
    echo -e "${RED}Failed to start Hardhat node.${NC}"
    return 1
  fi
}

# Function to start the API server
start_api() {
  if check_port 3002; then
    echo -e "${RED}A process is already running on port 3002. Please kill it first.${NC}"
    return 1
  fi

  echo -e "${BLUE}Starting API server on port 3002...${NC}"
  cd $(dirname $0)/../backend/api
  PORT=3002 npm start > ../../logs/api.log 2>&1 &
  sleep 5

  if check_port 3002; then
    echo -e "${GREEN}API server started successfully on port 3002.${NC}"
    return 0
  else
    echo -e "${RED}Failed to start API server.${NC}"
    return 1
  fi
}

# Function to start the frontend
start_frontend() {
  if check_port 3001; then
    echo -e "${YELLOW}A process is already running on port 3001. Attempting to kill it...${NC}"
    kill_port 3001
    if [ $? -ne 0 ]; then
      echo -e "${RED}Failed to kill process on port 3001. Please kill it manually.${NC}"
      return 1
    fi
    # Wait a moment for the port to be released
    sleep 3
  fi

  echo -e "${BLUE}Starting frontend on port 3001...${NC}"
  
  # Get the absolute path to the project root
  local project_root="$(cd "$(dirname "$0")/.." && pwd)"
  
  # Change to the frontend directory using the absolute path
  cd "$project_root/frontend" || {
    echo -e "${RED}Frontend directory not found at $project_root/frontend${NC}"
    return 1
  }
  
  PORT=3001 npm run dev > "$project_root/logs/frontend.log" 2>&1 &
  sleep 5

  if check_port 3001; then
    echo -e "${GREEN}Frontend started successfully on port 3001.${NC}"
    return 0
  else
    echo -e "${RED}Failed to start frontend.${NC}"
    return 1
  fi
}

# Function to start the bot
start_bot() {
  if check_port 3002; then
    echo -e "${RED}A process is already running on port 3002. Please kill it first.${NC}"
    return 1
  fi

  echo -e "${BLUE}Starting bot on port 3002...${NC}"
  cd $(dirname $0)/../backend/bot
  PORT=3002 python3 bot.py > ../../logs/bot.log 2>&1 &
  sleep 5

  if check_port 3002; then
    echo -e "${GREEN}Bot started successfully on port 3002.${NC}"
    return 0
  else
    echo -e "${RED}Failed to start bot.${NC}"
    return 1
  fi
}

# Function to check the status of the Hardhat node
check_hardhat() {
  if check_port 8545; then
    echo -e "${GREEN}Hardhat node is running on port 8545.${NC}"
    return 0
  else
    echo -e "${RED}Hardhat node is not running.${NC}"
    return 1
  fi
}

# Function to check the status of the API server
check_api() {
  if check_port 3002; then
    echo -e "${GREEN}API server is running on port 3002.${NC}"
    return 0
  else
    echo -e "${RED}API server is not running.${NC}"
    return 1
  fi
}

# Function to check the status of the frontend
check_frontend() {
  if check_port 3001; then
    echo -e "${GREEN}Frontend is running on port 3001.${NC}"
    return 0
  else
    echo -e "${RED}Frontend is not running.${NC}"
    return 1
  fi
}

# Function to check the status of the bot
check_bot() {
  # Check if the bot status endpoint is responding
  if curl -s http://127.0.0.1:3002/api/v1/status > /dev/null; then
    local status=$(curl -s http://127.0.0.1:3002/api/v1/status)
    if [[ $status == *"error"* ]]; then
      echo -e "${YELLOW}Bot status: $status${NC}"
      return 1
    else
      echo -e "${GREEN}Bot status: $status${NC}"
      return 0
    fi
  else
    echo -e "${RED}Bot status endpoint is not responding.${NC}"
    return 1
  fi
}

# Function to check blockchain connectivity
check_blockchain() {
  # Check if the blockchain health endpoint is responding
  if curl -s http://127.0.0.1:3002/api/v1/blockchain/health > /dev/null; then
    local status=$(curl -s http://127.0.0.1:3002/api/v1/blockchain/health)
    if [[ $status == *"connected"* ]]; then
      echo -e "${GREEN}Blockchain connection: Connected${NC}"
      return 0
    else
      echo -e "${YELLOW}Blockchain connection: Disconnected${NC}"
      return 1
    fi
  else
    echo -e "${RED}Blockchain health endpoint is not responding.${NC}"
    return 1
  fi
}

# Function to check AI service status
check_ai() {
  # Check if the AI status endpoint is responding
  if curl -s http://127.0.0.1:3002/api/v1/ai/status > /dev/null; then
    local status=$(curl -s http://127.0.0.1:3002/api/v1/ai/status)
    if [[ $status == *"error"* ]]; then
      echo -e "${YELLOW}AI service status: $status${NC}"
      return 1
    else
      echo -e "${GREEN}AI service status: $status${NC}"
      return 0
    fi
  else
    echo -e "${RED}AI service status endpoint is not responding.${NC}"
    return 1
  fi
}

# Function to run the Web3 service test
test_web3_service() {
  echo -e "${BLUE}Running Web3 service integration test...${NC}"
  cd $(dirname $0)/..
  node scripts/test_web3_service.js
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}Web3 service integration test passed.${NC}"
    return 0
  else
    echo -e "${RED}Web3 service integration test failed.${NC}"
    return 1
  fi
}

# Function to run the AI-Web3 integration test
test_ai_web3_integration() {
  echo -e "${BLUE}Running AI-Web3 integration test...${NC}"
  cd $(dirname $0)/..
  node scripts/test_ai_web3_integration.js
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}AI-Web3 integration test passed.${NC}"
    return 0
  else
    echo -e "${RED}AI-Web3 integration test failed.${NC}"
    return 1
  fi
}

# Function to run the AI strategy optimizer directly
run_strategy_optimizer() {
  echo -e "${BLUE}Running AI strategy optimizer...${NC}"
  cd $(dirname $0)/../backend/ai
  python3 run_strategy_optimizer.py --fork
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}AI strategy optimizer executed successfully.${NC}"
    return 0
  else
    echo -e "${RED}AI strategy optimizer execution failed.${NC}"
    return 1
  fi
}

# Function to deploy contracts to the Hardhat node
deploy_contracts() {
  echo -e "${BLUE}Deploying contracts to the Hardhat node...${NC}"
  cd $(dirname $0)/..
  npx hardhat run scripts/deploy.ts --network localhost
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}Contracts deployed successfully.${NC}"
    return 0
  else
    echo -e "${RED}Contract deployment failed.${NC}"
    return 1
  fi
}

# Function to check all services
check_all() {
  echo -e "${BLUE}Checking all services...${NC}"
  check_hardhat
  check_api
  check_frontend
  check_bot
  check_blockchain
  check_ai
}

# Function to start all services
start_all() {
  echo -e "${BLUE}Starting all ArbitrageX services...${NC}"
  
  # First kill all existing processes
  echo -e "${YELLOW}Killing any existing services...${NC}"
  kill_all
  
  # Wait a moment for processes to fully terminate
  sleep 3
  
  # Start Hardhat node
  start_hardhat
  if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to start Hardhat node. Aborting.${NC}"
    return 1
  fi
  
  # Deploy contracts if needed
  deploy_contracts
  
  # Start API server
  start_api
  if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to start API server. Aborting.${NC}"
    return 1
  fi
  
  # Start frontend
  start_frontend
  if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to start frontend. Aborting.${NC}"
    return 1
  fi
  
  # Start bot if needed
  start_bot
  
  echo -e "${GREEN}All services started successfully.${NC}"
  echo -e "${BLUE}Services running:${NC}"
  echo -e "  - Hardhat node: http://localhost:8545"
  echo -e "  - API server: http://localhost:3002"
  echo -e "  - Frontend: http://localhost:3001"
  
  return 0
}

# Function to kill all services
kill_all() {
  echo -e "${YELLOW}Killing all services...${NC}"
  
  # First try to kill by port
  kill_port 8545 || true
  kill_port 3002 || true
  kill_port 3001 || true
  
  # Then try to kill by process name for more stubborn processes
  echo -e "${YELLOW}Ensuring all processes are terminated...${NC}"
  pkill -f "hardhat node" 2>/dev/null || true
  pkill -f "node.*api" 2>/dev/null || true
  pkill -f "node.*frontend" 2>/dev/null || true
  pkill -f "ts-node.*bot" 2>/dev/null || true
  
  # Wait a moment to ensure processes are terminated
  sleep 2
  
  # Verify all processes are killed
  local all_killed=true
  
  if check_port 8545; then
    echo -e "${RED}Failed to kill Hardhat node on port 8545.${NC}"
    all_killed=false
  fi
  
  if check_port 3002; then
    echo -e "${RED}Failed to kill API server on port 3002.${NC}"
    all_killed=false
  fi
  
  if check_port 3001; then
    echo -e "${RED}Failed to kill frontend on port 3001.${NC}"
    all_killed=false
  fi
  
  if $all_killed; then
    echo -e "${GREEN}All services killed successfully.${NC}"
  else
    echo -e "${YELLOW}Some services could not be killed. You may need to kill them manually.${NC}"
  fi
}

# Function to run a full integration test
run_integration_test() {
  echo -e "${BLUE}Running full integration test...${NC}"
  
  # Kill any existing processes
  kill_all
  
  # Start Hardhat node
  start_hardhat
  sleep 5
  
  # Deploy contracts
  deploy_contracts
  sleep 2
  
  # Run Web3 service test
  test_web3_service
  
  echo -e "${GREEN}Integration test completed.${NC}"
}

# Function to run the full AI-Web3 integration test
run_ai_web3_integration_test() {
  echo -e "${BLUE}Running full AI-Web3 integration test...${NC}"
  
  # Kill any existing processes
  kill_all
  
  # Start Hardhat node
  start_hardhat
  if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to start Hardhat node. Aborting test.${NC}"
    return 1
  fi
  
  # Deploy contracts
  deploy_contracts
  if [ $? -ne 0 ]; then
    echo -e "${RED}Contract deployment failed. Aborting test.${NC}"
    # Cleanup
    kill_port 8545
    return 1
  fi
  
  # Run AI-Web3 integration test
  test_ai_web3_integration
  test_result=$?
  
  # If the test fails, try running the strategy optimizer directly
  if [ $test_result -ne 0 ]; then
    echo -e "${YELLOW}AI-Web3 integration test failed. Trying to run strategy optimizer directly...${NC}"
    run_strategy_optimizer
    optimizer_result=$?
    
    if [ $optimizer_result -ne 0 ]; then
      echo -e "${RED}Strategy optimizer also failed. Integration test unsuccessful.${NC}"
      # Cleanup
      kill_port 8545
      kill_port 3002
      return 1
    fi
  fi
  
  # Cleanup
  kill_port 8545
  kill_port 3002
  
  echo -e "${GREEN}AI-Web3 integration test completed.${NC}"
  return $test_result
}

# Function to verify AI components
verify_ai_components() {
  echo -e "${BLUE}Verifying AI components...${NC}"
  
  # Check if required Python modules are installed
  echo -e "${YELLOW}Checking Python dependencies...${NC}"
  cd $(dirname $0)/../backend/ai
  
  # List of required Python packages
  REQUIRED_PACKAGES="numpy pandas tensorflow scikit-learn web3 matplotlib seaborn"
  
  for package in $REQUIRED_PACKAGES; do
    python3 -c "import $package" 2>/dev/null
    if [ $? -ne 0 ]; then
      echo -e "${RED}Missing Python package: $package${NC}"
      echo -e "${YELLOW}Installing $package...${NC}"
      pip install $package
      if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install $package. Please install it manually.${NC}"
        return 1
      fi
    else
      echo -e "${GREEN}Python package $package is installed.${NC}"
    fi
  done
  
  # Check if required AI modules exist
  echo -e "${YELLOW}Checking AI modules...${NC}"
  REQUIRED_MODULES="strategy_optimizer.py web3_connector.py trade_analyzer.py backtesting.py"
  
  for module in $REQUIRED_MODULES; do
    if [ ! -f "$module" ]; then
      echo -e "${RED}Missing AI module: $module${NC}"
      return 1
    else
      echo -e "${GREEN}AI module $module exists.${NC}"
    fi
  done
  
  echo -e "${GREEN}AI components verification completed successfully.${NC}"
  return 0
}

# Function to run the real-world simulation
run_real_world_simulation() {
  echo -e "${BLUE}Running ArbitrageX Real-World Simulation...${NC}"
  
  # Check if the script exists
  if [ ! -f "./scripts/run_real_world_simulation.sh" ]; then
    echo -e "${RED}Error: Real-world simulation script not found.${NC}"
    return 1
  fi
  
  # Run the simulation script
  ./scripts/run_real_world_simulation.sh "$@"
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}Real-world simulation completed successfully.${NC}"
    return 0
  else
    echo -e "${RED}Real-world simulation failed.${NC}"
    return 1
  fi
}

# Function to restart all services
restart_all() {
  echo -e "${BLUE}Restarting all ArbitrageX services...${NC}"
  
  # Kill all existing services
  kill_all
  
  # Wait a moment for processes to fully terminate
  sleep 3
  
  # Start all services
  start_all
  
  return $?
}

# Main function to handle command line arguments
main() {
  case "$1" in
    start-hardhat)
      start_hardhat
      ;;
    start-api)
      start_api
      ;;
    start-frontend)
      start_frontend
      ;;
    start-bot)
      start_bot
      ;;
    start-all)
      start_all
      ;;
    restart-all)
      restart_all
      ;;
    check-hardhat)
      check_hardhat
      ;;
    check-api)
      check_api
      ;;
    check-frontend)
      check_frontend
      ;;
    check-bot)
      check_bot
      ;;
    check-blockchain)
      check_blockchain
      ;;
    check-ai)
      check_ai
      ;;
    check-all)
      check_all
      ;;
    kill-hardhat)
      kill_port 8545
      ;;
    kill-api)
      kill_port 3002
      ;;
    kill-frontend)
      kill_port 3001
      ;;
    kill-all)
      kill_all
      ;;
    test-web3)
      test_web3_service
      ;;
    test-ai-web3)
      test_ai_web3_integration
      ;;
    run-strategy-optimizer)
      run_strategy_optimizer
      ;;
    deploy-contracts)
      deploy_contracts
      ;;
    integration-test)
      run_integration_test
      ;;
    ai-web3-integration-test)
      run_ai_web3_integration_test
      ;;
    verify-ai)
      verify_ai_components
      ;;
    run-real-world-simulation)
      shift
      run_real_world_simulation "$@"
      ;;
    *)
      echo -e "${BLUE}ArbitrageX Process Management Script${NC}"
      echo -e "${YELLOW}Usage:${NC}"
      echo -e "  $0 start-hardhat    - Start the Hardhat node"
      echo -e "  $0 start-api        - Start the API server"
      echo -e "  $0 start-frontend   - Start the frontend"
      echo -e "  $0 start-bot        - Start the bot"
      echo -e "  $0 start-all        - Start all services"
      echo -e "  $0 restart-all      - Restart all services"
      echo -e "  $0 check-hardhat    - Check if the Hardhat node is running"
      echo -e "  $0 check-api        - Check if the API server is running"
      echo -e "  $0 check-frontend   - Check if the frontend is running"
      echo -e "  $0 check-bot        - Check the bot status"
      echo -e "  $0 check-blockchain - Check blockchain connectivity"
      echo -e "  $0 check-ai         - Check AI service status"
      echo -e "  $0 check-all        - Check all services"
      echo -e "  $0 kill-hardhat     - Kill the Hardhat node"
      echo -e "  $0 kill-api         - Kill the API server"
      echo -e "  $0 kill-frontend    - Kill the frontend"
      echo -e "  $0 kill-all         - Kill all services"
      echo -e "  $0 test-web3        - Run the Web3 service integration test"
      echo -e "  $0 test-ai-web3     - Run the AI-Web3 integration test"
      echo -e "  $0 run-strategy-optimizer - Run the AI strategy optimizer directly"
      echo -e "  $0 deploy-contracts - Deploy contracts to the Hardhat node"
      echo -e "  $0 integration-test - Run a full integration test"
      echo -e "  $0 ai-web3-integration-test - Run a full AI-Web3 integration test"
      echo -e "  $0 verify-ai        - Verify AI components and dependencies"
      echo -e "  $0 run-real-world-simulation - Run the real-world simulation"
      echo
      echo -e "${YELLOW}Note:${NC} If services don't stop properly, use the force kill script:"
      echo -e "  ./scripts/kill_all_arbitragex.sh"
      ;;
  esac
}

# Call the main function with all command line arguments
main "$@"