# ArbitrageX Process Management

This document outlines the proper process management workflow for the ArbitrageX project to avoid port conflicts, duplicate processes, and hidden failures.

## 🚀 Process Management Workflow

### 1️⃣ Before Starting a Process, Check if It's Already Running

```bash
# Check if a process is running on a specific port
lsof -i :PORT

# Example: Check if the backend API is running
lsof -i :3000
```

If a process is running on that port, kill it before restarting:

```bash
# Kill a process running on a specific port
fuser -k PORT/tcp

# Example: Kill the backend if it's running
fuser -k 3000/tcp
```

### 2️⃣ Start the Process

Use the correct command from the list of critical processes below.

### 3️⃣ Verify That the Process is Running

```bash
# Check if the process is listening on the correct port
lsof -i :PORT

# Example: Ensure backend is running
lsof -i :3000
```

If no output appears, assume the process failed and try restarting.

### 4️⃣ Confirm That the Service is Functioning

```bash
# Check if the service is responding correctly
curl -X GET http://localhost:PORT/api/health

# Example: Check if the backend API is functioning
curl -X GET http://localhost:3000/api/health
```

If this returns `{ "status": "ok" }`, then the process is working. If not, log the error and do not assume success.

## 📌 List of Critical Processes and Their Ports

For ArbitrageX, these are the ONLY processes that should be running at all times:

| Process Name | Port | Command to Start | Purpose |
|--------------|------|------------------|---------|
| Hardhat Node (Mainnet Fork) | 8546 | `npx hardhat node --fork <RPC_URL> --fork-block-number 19261000` | Runs a local blockchain fork for testing |
| Backend API | 3002 | `npm run start:backend` or `node backend/server.js` | Provides API for frontend & AI components |
| Frontend | 3001 | `npm run start:frontend` or `next start` | Web dashboard for monitoring |
| Execution Bot | 3002 | `npm run bot:start` or `node execution/bot.js` | Executes arbitrage trades |
| AI Strategy Optimizer | N/A | `python3 run_strategy_optimizer.py` | AI-driven arbitrage decision-making |
| MongoDB (if local) | 27017 | `mongod --dbpath /data/db` (if not using Docker) | Stores historical data & trade info |

## 🛠️ Using the Process Management Script

We've created a script to help manage ArbitrageX processes following the workflow described above. The script is located at `scripts/manage_processes.sh`.

### Basic Usage

```bash
# Display help menu
./scripts/manage_processes.sh

# Check if a process is running on a specific port
./scripts/manage_processes.sh check 3000

# Kill a process running on a specific port
./scripts/manage_processes.sh kill 3000

# Start the API server on port 3002
./scripts/manage_processes.sh start-api

# Start all services with default ports
./scripts/manage_processes.sh start-all

# Check the status of all services
./scripts/manage_processes.sh check-all

# Stop all services
./scripts/manage_processes.sh kill-all
```

### Available Commands

- `start-hardhat` - Start the Hardhat node on port 8546
- `start-api` - Start the API server on port 3002
- `start-frontend` - Start the frontend on port 3001
- `start-all` - Start all services (Hardhat, deploy contracts, API, frontend)
- `check-hardhat` - Check if the Hardhat node is running
- `check-api` - Check if the API server is running
- `check-frontend` - Check if the frontend is running
- `check-bot` - Check the bot status
- `check-blockchain` - Check blockchain connectivity
- `check-all` - Check the status of all services
- `kill-hardhat` - Kill the Hardhat node
- `kill-api` - Kill the API server
- `kill-frontend` - Kill the frontend
- `kill-all` - Kill all services
- `test-web3` - Run the Web3 service integration test
- `deploy-contracts` - Deploy contracts to the Hardhat node
- `integration-test` - Run a full integration test

## 🧪 Integration Testing

The process management script includes functionality for running integration tests to ensure that all components of the ArbitrageX system are working together correctly.

### Running the Web3 Service Test

The Web3 service test verifies that the backend API can connect to the blockchain and interact with smart contracts:

```bash
./scripts/manage_processes.sh test-web3
```

This test:
1. Starts a Hardhat node in fork mode
2. Deploys contracts to the fork
3. Starts the backend API
4. Tests the blockchain health endpoint
5. Tests the execution mode endpoint

### Running a Full Integration Test

To run a complete integration test that verifies all components:

```bash
./scripts/manage_processes.sh integration-test
```

This test:
1. Kills any existing processes
2. Starts a fresh Hardhat node
3. Deploys contracts to the node
4. Runs the Web3 service test

## 🚀 Why This Fixes the Issue

- ✅ Ensures you do not assume a process is running unless it actually responds correctly
- ✅ Prevents duplicate processes from running
- ✅ Forces you to kill old processes before restarting
- ✅ Helps detect hidden failures before they cause problems
- ✅ Verifies blockchain connectivity and contract interactions

## 📝 Best Practices

1. **Always check before starting**: Never assume a port is free or a process is not running.
2. **Verify after starting**: Always verify that a process has started successfully and is responding correctly.
3. **Use the script**: The `manage_processes.sh` script implements the workflow and handles the details for you.
4. **Monitor logs**: Check the logs in the `logs/` directory for any errors or issues.
5. **One process per port**: Ensure that only one process is using each port.
6. **Consistent port usage**: Always use the same ports for the same processes to avoid confusion.
7. **Document changes**: If you change the port for a process, update the documentation and inform the team.
8. **Run integration tests regularly**: Use the integration test functionality to ensure all components work together.

## 📌 Troubleshooting

If you encounter issues with process management, try the following:

1. **Check all running processes**: Use `./scripts/manage_processes.sh check-all` to see what's running.
2. **Stop all processes**: Use `./scripts/manage_processes.sh kill-all` to stop all processes and start fresh.
3. **Check logs**: Look at the logs in the `logs/` directory for any errors or issues.
4. **Run the integration test**: Use `./scripts/manage_processes.sh integration-test` to verify all components.
5. **Check blockchain connectivity**: Use `./scripts/manage_processes.sh check-blockchain` to verify the connection to the blockchain.
6. **Restart the system**: In some cases, a system restart may be necessary to clear all processes.
7. **Check for zombie processes**: Use `ps aux | grep node` to check for any zombie processes that may be causing issues.

## Real Service Implementation

The ArbitrageX system now uses real service implementations for all components, even in testing and fork modes. This ensures consistent behavior across all environments and improves the reliability of the system.

### Real Services Overview

1. **MongoDB Service**: Uses real MongoDB connections for all database operations
   - Connection status is checked using actual MongoDB ping
   - Proper error handling for connection failures

2. **Redis Service**: Connects to a real Redis instance for caching and pub/sub messaging
   - Connection status is verified with Redis ping
   - Clean connection closing on shutdown

3. **AI Service**: Executes real Python scripts for AI predictions and status checks
   - Dynamically creates status check script if not present
   - Runs the strategy optimizer for real predictions

4. **Web3 Service**: Connects to real blockchain nodes or local forks
   - Verifies blockchain connectivity
   - Initializes contract instances with real signers

### Health Checking

The health endpoint now checks the actual status of all services:

```bash
# Check the health of all services
curl http://localhost:3002/health
```

Example response:
```json
{
  "status": "healthy",
  "services": {
    "mongodb": "connected",
    "redis": "connected",
    "ai": "ready",
    "web3": "connected"
  },
  "timestamp": "2025-03-04T04:25:06.261Z"
}
```

### Blockchain Health

The blockchain health endpoint provides detailed information about the blockchain connection:

```bash
# Check blockchain health
curl http://localhost:3002/api/v1/blockchain/health
```

Example response:
```json
{
  "status": "connected",
  "provider": {
    "url": "http://127.0.0.1:8546",
    "network": "hardhat",
    "chainId": 31337
  },
  "contracts": {
    "arbitrageExecutor": "0xb6057e08a11da09a998985874FE2119e98dB3D5D",
    "flashLoanService": "0xad203b3144f8c09a20532957174fc0366291643c",
    "uniswapRouter": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "sushiswapRouter": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"
  }
}
```

### Integration Testing

The process management script includes commands for testing the real service implementations:

```bash
# Run Web3 service integration test
./scripts/manage_processes.sh integration-test

# Run AI-Web3 integration test
./scripts/manage_processes.sh ai-web3-integration-test
```

These tests verify that all services are working correctly with real implementations. 