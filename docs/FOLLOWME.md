# @followme - ArbitrageX System Guide

## 🔹 Quick Reference

### Common Commands

| Action | Command |
|--------|---------|
| Start the system | `./scripts/start_arbitragex.sh` |
| Stop the system | `./scripts/kill_all_arbitragex.sh` |
| Check system status | `ps aux \| grep -E "hardhat\|node.*api\|node.*frontend\|monitor_services.sh" \| grep -v grep` |
| View logs | `tail -f logs/monitor.log` |
| Check API health | `curl -s http://localhost:3002/health` |
| Check blockchain | `curl -s http://localhost:3002/api/v1/blockchain/health` |
| Check AI status | `curl -s http://localhost:3002/api/v1/ai/status` |
| Generate trade report | `./scripts/generate_trade_summary.sh` |

### Service URLs

| Service | URL |
|---------|-----|
| Hardhat Node | http://localhost:8545 |
| API Server | http://localhost:3002 |
| Frontend Dashboard | http://localhost:3001 |

## 🔹 System Overview

ArbitrageX is an AI-powered arbitrage trading bot that:
- Uses AI to predict, optimize, and execute profitable trades
- Leverages flash loans for high-speed, risk-free arbitrage
- Operates across multiple chains (Ethereum, Arbitrum, Polygon, BSC)
- Provides a frontend dashboard for real-time monitoring & strategy control

## 🔹 System Architecture

### 1. Core Components

| Component | Port | Description |
|-----------|------|-------------|
| Hardhat Node | 8545 | Local blockchain node that forks Ethereum mainnet |
| API Server | 3002 | Backend API for bot operations and frontend integration |
| Frontend | 3001 | Dashboard UI for monitoring and controlling the bot |
| Monitor Service | N/A | Background service that ensures all components are running |

### 2. Directory Structure

```
arbitragex-new/
├── contracts/                # Smart contracts (Solidity)
│   ├── ArbitrageExecutor.sol # Main arbitrage execution contract
│   └── FlashLoanService.sol  # Flash loan management
├── backend/                  # Node.js backend
│   ├── api/                  # API services
│   ├── ai/                   # AI prediction models
│   └── execution/            # Trade execution logic
├── frontend/                 # Next.js dashboard
├── scripts/                  # Management scripts
│   ├── start_arbitragex.sh   # One-command startup script
│   ├── kill_all_arbitragex.sh # Force kill script
│   ├── manage_processes.sh   # Process management script
│   ├── monitor_services.sh   # Service monitoring script
│   └── generate_trade_summary.sh # Trade report generator
├── logs/                     # Log files for all services
└── reports/                  # Trade summary reports and data
```

## 🔹 Management Scripts

We've created several scripts to manage the ArbitrageX system:

### 1. `start_arbitragex.sh`

One-command solution to start the entire system:
- Kills any existing services
- Starts Hardhat node, API server, and frontend
- Deploys contracts to the Hardhat node
- Starts the monitor service
- Displays access information

### 2. `kill_all_arbitragex.sh`

Force kill script to terminate all ArbitrageX processes:
- Kills monitor scripts
- Kills Hardhat node
- Kills API server
- Kills frontend
- Kills any remaining process management scripts
- Checks ports to ensure they're free

### 3. `manage_processes.sh`

Process management script with various commands:
- `start-hardhat`: Starts the Hardhat node
- `start-api`: Starts the API server
- `start-frontend`: Starts the frontend
- `start-all`: Starts all services
- `restart-all`: Restarts all services
- `kill-all`: Kills all services
- `check-all`: Checks the status of all services

### 4. `monitor_services.sh`

Continuous monitoring script that:
- Checks if all services are running
- Restarts any failed services
- Verifies blockchain connectivity
- Logs the status of all services

## 🔹 Common Issues and Solutions

### 1. Frontend Path Issue

**Problem**: The frontend fails to start with an error about the directory not being found.

**Solution**: We fixed the path in `manage_processes.sh` to use an absolute path to the frontend directory.

### 2. API Health Endpoint

**Problem**: The monitor script reports that the API health check fails.

**Solution**: We fixed the monitor script to use the correct health endpoint (`/health` instead of `/api/health`).

### 3. Blockchain Connection Issues

**Problem**: The monitor script continuously restarts the Hardhat node due to blockchain connection issues.

**Solution**: We added a restart counter to prevent continuous restarts. After 3 restart attempts, the script will wait for the next check cycle before trying again.

### 4. Process Termination

**Problem**: When stopping the system, some processes remain running.

**Solution**: We created the `kill_all_arbitragex.sh` script to forcefully terminate all processes and added signal handling to the monitor script for graceful shutdowns.

### 5. Monitor Script Continuously Restarts Services

**Symptoms**:
- Services keep restarting in the monitor log
- System is unstable

**Solutions**:
1. Stop all services: `./scripts/kill_all_arbitragex.sh`
2. Check the monitor script for errors: `cat scripts/monitor_services.sh`
3. Start services manually one by one to identify the issue:
   ```bash
   ./scripts/manage_processes.sh start-hardhat
   ./scripts/manage_processes.sh start-api
   ./scripts/manage_processes.sh start-frontend
   ```
4. Once all services are stable, start the monitor: `./scripts/monitor_services.sh` 

### 6. Execution Mode Synchronization Issues

**Symptoms**:
- API reports "Execution modes out of sync" in logs
- API shows execution mode as "fork" but blockchain shows "production" (or vice versa)
- Sync status endpoint returns `{"isInSync": false}`

**Solutions**:
1. Use the troubleshooting script to check all execution modes at once:
   ```bash
   npx hardhat run scripts/check_mode.js --network localhost
   ```
2. Check the actual contract execution mode directly:
   ```bash
   npx hardhat console --network localhost
   > const flashLoanService = await ethers.getContractAt('FlashLoanService', '0xad203b3144f8c09a20532957174fc0366291643c')
   > const mode = await flashLoanService.getExecutionMode()
   > console.log(mode.toString())
   ```
3. Check the API's interpretation of the mode:
   ```bash
   curl -s http://localhost:3002/api/v1/blockchain/contract-execution-mode
   ```
4. If there's a discrepancy, check the Web3Service implementation in `backend/api/services/Web3Service.ts` to ensure it correctly interprets the BigInt value returned from the contract.
5. Restart the API server after making any changes:
   ```bash
   pkill -f "node.*api" && cd backend/api && npm run start
   ```

## 🔹 How to Use the System

### Starting the System

```bash
./scripts/start_arbitragex.sh
```

### Monitoring the System

```bash
tail -f logs/monitor.log
```

### Accessing Services

- Hardhat Node: http://localhost:8545
- API Server: http://localhost:3002
- Frontend Dashboard: http://localhost:3001

### Stopping the System

```bash
# Press Ctrl+C in the terminal where start_arbitragex.sh is running
# If that doesn't work, use:
./scripts/kill_all_arbitragex.sh
```

## 🔹 API Endpoints

The API server provides several endpoints:

- `/`: Root endpoint with API information
- `/health`: Health check endpoint
- `/api/v1/ai/status`: AI service status
- `/api/v1/blockchain/health`: Blockchain connection status
- `/api/v1/execution-mode`: Current execution mode (fork/mainnet)

### Health Endpoints
- `/health` - API server health check
- `/api/v1/blockchain/health` - Blockchain connection health check

### Trade Endpoints
- `/api/v1/trades` - Get recent trades (default limit: 10)
- `/api/v1/trades/stats` - Get trade statistics and bot status
- `/api/v1/trades/:txHash` - Get a specific trade by transaction hash
- `/api/v1/trades/execute` - Execute a new arbitrage trade (POST)

### Market Data Endpoints
- `/api/v1/market/data` - Get current market prices for tokens

## 🔹 Trade Monitoring & Reporting

ArbitrageX includes tools for monitoring and reporting on trade activity:

### Trade Summary Generator

The system includes a trade summary generator that creates detailed reports of trading activity with USD value conversion:

```bash
# Generate a trade summary report
./scripts/generate_trade_summary.sh
```

This script:
1. Fetches the latest trade data from the API
2. Retrieves current market prices for all tokens
3. Calculates USD values for all trade amounts and profits
4. Generates a comprehensive markdown report
5. Creates a timestamped archive copy for historical reference

### Trade Summary Report Contents

The generated report includes:
- Available trade endpoints
- Current trade statistics (total trades, success rate, total profit in ETH and USD)
- Recent trades with detailed information (timestamps, amounts, profits, gas costs)
- Current market prices for all tokens
- Instructions for accessing trade results via API and frontend

### Automated Monitoring

The monitor script checks for new trades every minute and logs the results to `logs/monitor.log`. You can view the latest trade activity with:

```bash
tail -f logs/monitor.log | grep "trade results"
```

### Viewing Trade Reports

Trade summary reports are stored in the `reports/` directory:
- Latest report: `reports/trade_results_summary.md`
- Historical reports: `reports/trade_results_summary_YYYYMMDD_HHMMSS.md`

## 🔹 System Verification

To verify that the system is running correctly:

1. Check if all processes are running:
   ```bash
   ps aux | grep -E "hardhat|node.*api|node.*frontend|monitor_services.sh" | grep -v grep
   ```

2. Check if the frontend is accessible:
   ```bash
   curl -s http://localhost:3001 | head -n 20
   ```

3. Check if the API is accessible:
   ```bash
   curl -s http://localhost:3002/
   ```

4. Check the blockchain connection:
   ```bash
   curl -s http://localhost:3002/api/v1/blockchain/health
   ```

5. Check the AI service status:
   ```bash
   curl -s http://localhost:3002/api/v1/ai/status
   ```

## 🔹 Recent Fixes

1. **API Health Endpoint**: Fixed the API health endpoint in the monitor script to use `/health` instead of `/api/health`.

2. **Blockchain Connection Check**: Added a restart counter to the monitor script to prevent continuous restarts of the Hardhat node.

3. **Frontend Path Verification**: Verified the frontend path in the `manage_processes.sh` script to ensure it uses an absolute path.

4. **Trade Results Endpoint**: Updated the trade results endpoint in the monitor script to use the correct path `/api/v1/trades` instead of `/api/trades/recent`.

5. **Improved Trade Results Detection**: Enhanced the monitor script to properly parse the JSON response from the trades endpoint and display the number of trades found.

6. **Execution Mode Synchronization**: Fixed the execution mode synchronization issue between the API and blockchain contract. The Web3Service was incorrectly interpreting the BigInt value (1n) returned from the contract as "production" mode instead of "fork" mode. Modified the comparison to convert the BigInt to a string before comparison.

7. **Added Execution Mode Troubleshooting Tool**: Created a `scripts/check_mode.js` script to easily verify the execution mode of the FlashLoanService contract and compare it with the API's interpretation. This tool helps diagnose synchronization issues between the blockchain contract and the API server.

8. **Improved Bot Status Monitoring**: Enhanced the bot status check in the monitoring script to use both the bot control endpoint and the bot status endpoint. This prevents unnecessary bot restarts when the bot is actually running but one of the status indicators is temporarily unavailable.

9. **Fixed Logs Directory Issue**: Updated scripts to use absolute paths for logs directory to ensure it exists before logging, preventing potential errors when scripts are run from different directories.

10. **Enhanced Kill Script**: Improved the kill script to properly terminate the monitor process and remove PID files to avoid stale references.

## 🔹 Starting and Stopping ArbitrageX

### Starting the System

We've created a single command to start the entire ArbitrageX system:

```bash
./scripts/start_arbitragex.sh
```

This script:
1. Kills any existing ArbitrageX processes
2. Starts the API server on port 3002
3. Starts the frontend on port 3001
4. Starts the ArbitrageX bot with default parameters:
   - Run time: 3600 seconds
   - Tokens: WETH, USDC, DAI
   - DEXes: Uniswap V3, Curve, Balancer
   - Gas strategy: Dynamic
5. Starts a monitor service that:
   - Checks if the API server is running
   - Checks if the frontend is running
   - Checks if the bot is running using both status endpoints
   - Restarts any component that has stopped

### Starting the Bot with Optimized CPU Usage

If you're experiencing high CPU usage, we've created an optimized version of the bot startup script:

```bash
./scripts/start_optimized_bot.sh
```

This script:
1. Kills any existing ArbitrageX processes
2. Ensures the Hardhat node is running
3. Starts the ArbitrageX bot with optimized parameters:
   - Run time: 3600 seconds
   - Tokens: WETH, USDC, DAI
   - DEXes: Uniswap V3, Curve, Balancer
   - Gas strategy: Conservative (lower gas usage)
   - Debug mode: Disabled (reduces logging overhead)
   - Scan interval: 15 seconds (reduced frequency)
   - Status updates: 30 seconds (reduced frequency)
   - Exponential backoff for errors

The optimized script implements several CPU-saving features:
- Connection backoff strategy to prevent excessive reconnection attempts
- Conditional debug logging to reduce logging overhead
- Circuit breaker for repeated errors to prevent CPU spikes
- Adaptive status update frequency based on system health
- Conservative gas strategy to reduce computational load

Normal CPU usage expectations:
- Idle mode: 5-15% CPU
- Scanning mode: 30-70% CPU
- Execution mode: 100-150% CPU

If you're seeing CPU usage above 200%, use the optimized script instead.

### Stopping the System

To stop all ArbitrageX processes:

```bash
./scripts/kill_all_arbitragex.sh
```

This script:
1. Kills the monitor process first to prevent it from restarting other processes
2. Kills all API server processes
3. Kills all frontend processes
4. Kills all bot processes
5. Kills any hardhat node processes
6. Checks if ports 3001, 3002, and 8545 are still in use and forces termination if needed
7. Removes PID files to prevent stale references

### Monitoring the System

Once the system is running, you can monitor it using:

```bash
# Check if all processes are running
ps aux | grep -E "node.*api|node.*frontend|monitor_services" | grep -v grep

# View the startup log
tail -f logs/startup.log

# Check the bot status
curl -s http://localhost:3002/api/v1/status

# Check the bot control status
curl -s http://localhost:3002/api/v1/bot-control/status

# Check WebSocket statistics
curl -s http://localhost:3002/api/v1/websocket/stats
```

### Troubleshooting Bot Status Issues

If the bot status is not updating correctly:

1. Check if the bot is running:
   ```bash
   curl -s http://localhost:3002/api/v1/bot-control/status
   ```

2. If the bot is running but the status is not updating, manually update the status:
   ```bash
   curl -s -X POST -H "Content-Type: application/json" \
     -d '{"memoryUsage": {"heapUsed": 50000000, "heapTotal": 100000000, "external": 10000000}, "cpuUsage": 0.2, "pendingTransactions": 0, "network": "Ethereum", "version": "1.0.0"}' \
     http://localhost:3002/api/v1/status/update
   ```

3. Verify the status was updated:
   ```bash
   curl -s http://localhost:3002/api/v1/status
   ```

## 🔹 Recent Improvements

1. **Process Management**:
   - Added a comprehensive process management script
   - Implemented continuous monitoring
   - Created a one-command startup solution
   - Added a force kill script for reliable cleanup

2. **Error Handling**:
   - Improved error handling and process termination
   - Added signal handling for graceful shutdowns
   - Fixed path issues for consistent operation
   - Implemented health checks for all services

3. **System Integration**:
   - Connected the API server to the blockchain
   - Integrated the AI service with the API
   - Connected the frontend to the API
   - Deployed contracts to the Hardhat node

4. **Trade Monitoring & Reporting**:
   - Added trade summary generator with USD value conversion
   - Created automated reporting with timestamped archives
   - Implemented market price tracking for all tokens
   - Enhanced monitor script to properly detect and report trades

## 🔹 Next Steps

1. **✅ Fixed API Health Endpoint**: Updated the monitor script to use the correct health endpoint (`/health` instead of `/api/health`).

2. **✅ Improved Blockchain Connection**: Added a restart counter to prevent continuous restarts of the Hardhat node and ensure more stable operation.

3. **✅ Enhanced Trade Reporting**: Added trade summary generator with USD value conversion for all tokens and automated reporting.

4. **Enhance Frontend**: Add more features to the frontend dashboard, such as real-time trade monitoring and strategy configuration.

5. **Implement AI Trading**: Develop and integrate the AI trading strategies with the blockchain for automated arbitrage execution.

6. **Multi-Chain Support**: Extend the system to support multiple blockchains for cross-chain arbitrage opportunities.

## 🔹 Troubleshooting Guide

### 1. System Won't Start

**Symptoms**: 
- `start_arbitragex.sh` fails to start some or all services
- Error messages about ports being in use

**Solutions**:
1. Kill all existing processes: `./scripts/kill_all_arbitragex.sh`
2. Check if ports are still in use: `lsof -i :8545,3001,3002`
3. Manually kill any processes using those ports: `kill -9 <PID>`
4. Try starting the system again: `./scripts/start_arbitragex.sh`

### 2. Blockchain Connection Issues

**Symptoms**:
- Monitor log shows repeated Hardhat node restarts
- API returns "unknown" for blockchain connection

**Solutions**:
1. Stop all services: `./scripts/kill_all_arbitragex.sh`
2. Start the Hardhat node manually: `./scripts/manage_processes.sh start-hardhat`
3. Verify it's running: `curl -s http://localhost:8545`
4. Start the API server: `./scripts/manage_processes.sh start-api`
5. Check the connection: `curl -s http://localhost:3002/api/v1/blockchain/health`

### 3. Frontend Not Loading

**Symptoms**:
- Frontend URL shows blank page or error
- `curl` command to frontend returns empty response

**Solutions**:
1. Check if the frontend process is running: `ps aux | grep "node.*frontend" | grep -v grep`
2. Restart the frontend: `./scripts/manage_processes.sh start-frontend`
3. Check the frontend logs: `tail -f logs/frontend.log`

### 4. API Endpoints Not Working

**Symptoms**:
- API endpoints return 404 errors
- "Cannot GET" messages in responses

**Solutions**:
1. Verify the API server is running: `curl -s http://localhost:3002/`
2. Check the API logs for errors: `tail -f logs/api.log`
3. Restart the API server: `./scripts/manage_processes.sh start-api`

### 5. Monitor Script Continuously Restarts Services

**Symptoms**:
- Services keep restarting in the monitor log
- System is unstable

**Solutions**:
1. Stop all services: `./scripts/kill_all_arbitragex.sh`
2. Check the monitor script for errors: `cat scripts/monitor_services.sh`
3. Start services manually one by one to identify the issue:
   ```bash
   ./scripts/manage_processes.sh start-hardhat
   ./scripts/manage_processes.sh start-api
   ./scripts/manage_processes.sh start-frontend
   ```
4. Once all services are stable, start the monitor: `./scripts/monitor_services.sh` 

### 6. Execution Mode Synchronization Issues

**Symptoms**:
- API reports "Execution modes out of sync" in logs
- API shows execution mode as "fork" but blockchain shows "production" (or vice versa)
- Sync status endpoint returns `{"isInSync": false}`

**Solutions**:
1. Use the troubleshooting script to check all execution modes at once:
   ```bash
   npx hardhat run scripts/check_mode.js --network localhost
   ```
2. Check the actual contract execution mode directly:
   ```bash
   npx hardhat console --network localhost
   > const flashLoanService = await ethers.getContractAt('FlashLoanService', '0xad203b3144f8c09a20532957174fc0366291643c')
   > const mode = await flashLoanService.getExecutionMode()
   > console.log(mode.toString())
   ```
3. Check the API's interpretation of the mode:
   ```bash
   curl -s http://localhost:3002/api/v1/blockchain/contract-execution-mode
   ```
4. If there's a discrepancy, check the Web3Service implementation in `backend/api/services/Web3Service.ts` to ensure it correctly interprets the BigInt value returned from the contract.
5. Restart the API server after making any changes:
   ```bash
   pkill -f "node.*api" && cd backend/api && npm run start
   ``` 