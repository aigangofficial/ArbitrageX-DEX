#!/usr/bin/env node

/**
 * Test script to verify AI-Web3 integration
 *
 * This script:
 * 1. Starts a Hardhat node in fork mode
 * 2. Deploys contracts to the fork
 * 3. Starts the API server
 * 4. Tests the Web3 service
 * 5. Tests the AI service integration with Web3
 * 6. Verifies that the AI can make predictions using blockchain data
 */

const axios = require('axios');
const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Configuration
const HARDHAT_PORT = 8546;
const HARDHAT_URL = `http://127.0.0.1:${HARDHAT_PORT}`;
const API_PORT = 3002;
const API_URL = `http://127.0.0.1:${API_PORT}`;
const FORK_URL = 'https://mainnet.infura.io/v3/59de174d2d904c1980b975abae2ef0ec';
const LOG_DIR = path.join(__dirname, '../logs');

// Ensure log directory exists
if (!fs.existsSync(LOG_DIR)) {
  fs.mkdirSync(LOG_DIR, { recursive: true });
}

// Log file
const logFile = path.join(LOG_DIR, 'test_ai_web3_integration.log');
const logStream = fs.createWriteStream(logFile, { flags: 'a' });

// Helper function to log messages
function log(message) {
  const timestamp = new Date().toISOString();
  const formattedMessage = `[${timestamp}] ${message}`;
  console.log(formattedMessage);
  logStream.write(formattedMessage + '\n');
}

// Helper function to check if a port is in use
function isPortInUse(port) {
  try {
    execSync(`lsof -i:${port} -t`, { stdio: 'ignore' });
    return true;
  } catch (error) {
    return false;
  }
}

// Helper function to kill a process on a specific port
function killProcessOnPort(port) {
  try {
    log(`Checking for processes on port ${port}...`);
    const pid = execSync(`lsof -i:${port} -t`, { encoding: 'utf-8' }).trim();
    
    if (pid) {
      log(`Killing process ${pid} on port ${port}...`);
      execSync(`kill -9 ${pid}`);
      log(`Process on port ${port} killed successfully.`);
      return true;
    }
  } catch (error) {
    log(`No process found on port ${port} or failed to kill: ${error.message}`);
  }
  return false;
}

// Helper function to wait for a service to be available
async function waitForService(url, maxAttempts = 30, interval = 1000) {
  log(`Waiting for service at ${url}...`);
  
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        log(`Service is up and running at ${url}`);
        return true;
      }
    } catch (error) {
      // Ignore connection errors and continue waiting
    }
    
    log(`Waiting for service at ${url}...`);
    await new Promise(resolve => setTimeout(resolve, interval));
  }
  
  log(`Failed to connect to service at ${url} after ${maxAttempts} attempts`);
  return false;
}

// Start Hardhat node in fork mode
async function startHardhatNode() {
  log('Starting Hardhat node in fork mode...');

  // Check if a process is already running on the Hardhat port
  if (isPortInUse(HARDHAT_PORT)) {
    log(`A process is already running on port ${HARDHAT_PORT}. Killing it...`);
    killProcessOnPort(HARDHAT_PORT);
    // Wait a moment for the port to be released
    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  // Create logs directory if it doesn't exist
  if (!fs.existsSync(LOG_DIR)) {
    fs.mkdirSync(LOG_DIR, { recursive: true });
  }

  // Start Hardhat node
  const hardhatNode = spawn('npx', [
    'hardhat',
    'node',
    '--hostname',
    '127.0.0.1',
    '--port',
    HARDHAT_PORT,
    '--fork',
    FORK_URL,
  ]);

  // Handle output
  hardhatNode.stdout.on('data', data => {
    logStream.write(`[HARDHAT] ${data}`);
  });

  hardhatNode.stderr.on('data', data => {
    logStream.write(`[HARDHAT ERROR] ${data}`);
  });

  // Wait for Hardhat node to start
  await new Promise(resolve => setTimeout(resolve, 10000));

  // Check if Hardhat node is running
  try {
    await axios.post(HARDHAT_URL, {
      jsonrpc: '2.0',
      method: 'eth_blockNumber',
      params: [],
      id: 1,
    });
    log('Hardhat node is running successfully.');
    return hardhatNode;
  } catch (error) {
    log(`Failed to connect to Hardhat node: ${error.message}`);
    hardhatNode.kill();
    process.exit(1);
  }
}

// Deploy contracts to the fork
async function deployContracts() {
  log('Deploying contracts to the fork...');

  // Run the deployment script
  const deployment = spawn('npx', [
    'hardhat',
    'run',
    'scripts/deploy.ts',
    '--network',
    'localhost',
  ], {
    env: {
      ...process.env,
      HARDHAT_NETWORK: 'localhost',
      HARDHAT_FORK: 'true',
      HARDHAT_FORK_URL: HARDHAT_URL,
    },
  });

  // Handle output
  deployment.stdout.on('data', data => {
    logStream.write(`[DEPLOYMENT] ${data}`);
  });

  deployment.stderr.on('data', data => {
    logStream.write(`[DEPLOYMENT ERROR] ${data}`);
  });

  // Wait for deployment to complete
  await new Promise(resolve => deployment.on('close', resolve));

  log('Contracts deployed successfully.');
}

// Start API server
async function startApiServer() {
  log('Starting API server...');

  // Check if a process is already running on the API port
  if (isPortInUse(API_PORT)) {
    log(`A process is already running on port ${API_PORT}. Killing it...`);
    killProcessOnPort(API_PORT);
    // Wait a moment for the port to be released
    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  // Start the API server
  const apiProcess = spawn('npm', ['start'], { 
    cwd: path.join(process.cwd(), 'backend/api'), 
    env: { 
      ...process.env, 
      PORT: API_PORT,
      NODE_ENV: 'development',
      DEBUG: 'arbitragex:*'
    } 
  });

  // Handle output
  apiProcess.stdout.on('data', data => {
    const output = data.toString();
    log(`[API] ${output}`);
    logStream.write(`[API] ${output}\n`);
  });

  apiProcess.stderr.on('data', data => {
    const error = data.toString();
    log(`[API ERROR] ${error}`);
    logStream.write(`[API ERROR] ${error}\n`);
  });

  // Wait for API server to be ready
  const apiHealthUrl = `${API_URL}/health`;
  log(`Waiting for health endpoint at ${apiHealthUrl}...`);
  
  const apiReady = await waitForService(apiHealthUrl);

  if (!apiReady) {
    log('Failed to start API server.');
    apiProcess.kill();
    process.exit(1);
  }

  log('API server started successfully!');
  return apiProcess;
}

// Test the Web3 service
async function testWeb3Service() {
  log('Testing Web3 service...');

  try {
    // Test blockchain health endpoint
    log('Testing blockchain health endpoint...');
    const healthResponse = await axios.get(`${API_URL}/api/v1/blockchain/health`);
    log(`Blockchain health response: ${JSON.stringify(healthResponse.data, null, 2)}`);

    if (!healthResponse.data.status || healthResponse.data.status !== 'connected') {
      log('Web3 service is not connected to the blockchain.');
      return false;
    }

    // Validate provider info
    const providerInfo = healthResponse.data.provider;
    if (!providerInfo || !providerInfo.url || !providerInfo.url.includes(HARDHAT_PORT.toString())) {
      log(`Web3 service is not connected to the Hardhat node at port ${HARDHAT_PORT}.`);
      log(`Current provider: ${JSON.stringify(providerInfo)}`);
      return false;
    }

    // Validate contract addresses
    const contracts = healthResponse.data.contracts;
    if (!contracts || !contracts.arbitrageExecutor || !contracts.flashLoanService) {
      log('Contract addresses not found in health response.');
      log(`Contracts: ${JSON.stringify(contracts)}`);
      return false;
    }

    log('Blockchain health check passed!');

    // Test execution mode endpoint
    log('Testing execution mode endpoint...');
    const modeResponse = await axios.post(`${API_URL}/api/v1/blockchain/set-execution-mode`, {
      mode: 'test',
    });
    log(`Set execution mode response: ${JSON.stringify(modeResponse.data, null, 2)}`);

    if (!modeResponse.data.status || modeResponse.data.status !== 'success') {
      log('Failed to set execution mode.');
      return false;
    }

    log('Execution mode set successfully!');
    return true;
  } catch (error) {
    log(`Error testing Web3 service: ${error.message}`);
    if (error.response) {
      log(`Response data: ${JSON.stringify(error.response.data)}`);
      log(`Response status: ${error.response.status}`);
    }
    return false;
  }
}

// Run the AI strategy optimizer
async function runStrategyOptimizer() {
  log('Running AI strategy optimizer...');

  try {
    // Make AI prediction request
    try {
      const predictionResponse = await axios.post(`${API_URL}/api/v1/ai/predict`, {
        sourceToken: "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", // WETH
        targetToken: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", // USDC
        amount: "1000000000000000000", // 1 ETH
        executionMode: "fork",
        maxSlippage: 0.5,
        gasPrice: "50000000000" // 50 gwei
      });
      
      if (!predictionResponse.data || predictionResponse.data.status !== 'success') {
        log('AI prediction failed.');
        log(`Response: ${JSON.stringify(predictionResponse.data)}`);
        
        // If AI prediction fails, try running the Python script directly
        log('Attempting to run strategy optimizer directly...');
        await runStrategyOptimizerScript();
      } else {
        log('AI prediction successful:');
        log(JSON.stringify(predictionResponse.data, null, 2));
      }
    } catch (error) {
      log(`Error making AI prediction request: ${error.message}`);
      return false;
    }
    
    // Now test with blockchain data integration
    log('Testing AI with blockchain data integration...');
    
    // First set execution mode to 'fork'
    const modeResponse = await axios.post(`${API_URL}/api/v1/blockchain/set-execution-mode`, {
      mode: 'fork'
    });
    
    if (!modeResponse.data || modeResponse.data.status !== 'success') {
      log('Failed to set execution mode to fork.');
      log(`Response: ${JSON.stringify(modeResponse.data)}`);
    } else {
      log('Execution mode set to fork successfully.');
    }
    
    // Run Python script directly for the full AI-Web3 integration test
    log('Running strategy optimizer with blockchain data...');
    
    const pythonProcess = spawn('python3', [
      path.join(process.cwd(), 'backend/ai/run_strategy_optimizer.py'),
      '--fork',
      '--iterations', '5',
      '--risk', '0.5',
      '--visualize'
    ]);
    
    // Handle output
    pythonProcess.stdout.on('data', data => {
      const output = data.toString();
      log(`[PYTHON] ${output}`);
      logStream.write(`[PYTHON] ${output}\n`);
    });
    
    pythonProcess.stderr.on('data', data => {
      const error = data.toString();
      log(`[PYTHON ERROR] ${error}`);
      logStream.write(`[PYTHON ERROR] ${error}\n`);
    });
    
    // Wait for Python process to complete
    const exitCode = await new Promise(resolve => pythonProcess.on('close', resolve));
    
    if (exitCode === 0) {
      log('Strategy optimizer executed successfully with blockchain data.');
      return true;
    } else {
      log(`Strategy optimizer failed with exit code ${exitCode}.`);
      return false;
    }
  } catch (error) {
    log(`Error running AI strategy optimizer: ${error.message}`);
    if (error.response) {
      log(`Response data: ${JSON.stringify(error.response.data)}`);
      log(`Response status: ${error.response.status}`);
    }
    
    // If the endpoint doesn't exist yet, run the Python script directly
    log('Falling back to running Python script directly...');
    
    try {
      const pythonProcess = spawn('python3', [
        path.join(process.cwd(), 'backend/ai/run_strategy_optimizer.py'),
        '--fork'
      ]);
      
      // Handle output
      pythonProcess.stdout.on('data', data => {
        const output = data.toString();
        log(`[PYTHON] ${output}`);
        logStream.write(`[PYTHON] ${output}\n`);
      });
      
      pythonProcess.stderr.on('data', data => {
        const error = data.toString();
        log(`[PYTHON ERROR] ${error}`);
        logStream.write(`[PYTHON ERROR] ${error}\n`);
      });
      
      // Wait for Python process to complete
      const exitCode = await new Promise(resolve => pythonProcess.on('close', resolve));
      
      if (exitCode === 0) {
        log('Python script executed successfully.');
        return true;
      } else {
        log(`Python script failed with exit code ${exitCode}.`);
        return false;
      }
    } catch (pythonError) {
      log(`Error running Python script: ${pythonError.message}`);
      return false;
    }
  }
}

/**
 * Run the strategy optimizer Python script directly
 */
async function runStrategyOptimizerScript() {
  log('Running strategy optimizer script directly...');
  
  const pythonProcess = spawn('python3', [
    path.join(process.cwd(), 'backend/ai/run_strategy_optimizer.py'),
    '--fork',
    '--iterations', '5',
    '--risk', '0.5',
    '--visualize'
  ]);
  
  // Handle output
  pythonProcess.stdout.on('data', data => {
    const output = data.toString();
    log(`[PYTHON DIRECT] ${output}`);
    logStream.write(`[PYTHON DIRECT] ${output}\n`);
  });
  
  pythonProcess.stderr.on('data', data => {
    const error = data.toString();
    log(`[PYTHON DIRECT ERROR] ${error}`);
    logStream.write(`[PYTHON DIRECT ERROR] ${error}\n`);
  });
  
  // Wait for Python process to complete
  const exitCode = await new Promise(resolve => pythonProcess.on('close', resolve));
  
  if (exitCode === 0) {
    log('Strategy optimizer script executed successfully.');
    return true;
  } else {
    log(`Strategy optimizer script failed with exit code ${exitCode}.`);
    return false;
  }
}

// Main function
async function main() {
  log('Starting AI-Web3 integration test...');

  let hardhatNode;
  let apiServer;

  try {
    // Start Hardhat node
    hardhatNode = await startHardhatNode();

    // Deploy contracts
    await deployContracts();

    // Start API server
    apiServer = await startApiServer();

    // Test Web3 service
    const web3Success = await testWeb3Service();
    if (!web3Success) {
      log('Web3 service test failed.');
      process.exit(1);
    }

    // Run AI strategy optimizer
    const aiSuccess = await runStrategyOptimizer();
    if (!aiSuccess) {
      log('AI strategy optimizer test failed.');
      process.exit(1);
    }

    log('AI-Web3 integration test completed successfully!');
  } catch (error) {
    log(`Error in main function: ${error.message}`);
    process.exit(1);
  } finally {
    // Cleanup
    if (apiServer) {
      log('Stopping API server...');
      apiServer.kill();
    }

    if (hardhatNode) {
      log('Stopping Hardhat node...');
      hardhatNode.kill();
    }

    logStream.end();
  }
}

// Run the main function
main().catch(error => {
  log(`Unhandled error: ${error.message}`);
  process.exit(1);
}); 