#!/usr/bin/env node

/**
 * Script to start the real backend API server for Web3 service testing
 * 
 * This script:
 * 1. Sets up the necessary environment variables
 * 2. Starts the real backend API server
 * 3. Waits for the API to be available
 */

const { spawn } = require('child_process');
const axios = require('axios');
const path = require('path');
const fs = require('fs');

// Configuration
const API_PORT = 3001;
const API_URL = `http://127.0.0.1:${API_PORT}`;
const HARDHAT_URL = 'http://127.0.0.1:8546';
const LOG_DIR = path.join(__dirname, '../logs');

// Ensure log directory exists
if (!fs.existsSync(LOG_DIR)) {
  fs.mkdirSync(LOG_DIR, { recursive: true });
}

// Log file
const logFile = path.join(LOG_DIR, 'real_api_server.log');
const logStream = fs.createWriteStream(logFile, { flags: 'a' });

// Helper function to log messages
function log(message) {
  const timestamp = new Date().toISOString();
  const formattedMessage = `[${timestamp}] ${message}`;
  console.log(formattedMessage);
  logStream.write(formattedMessage + '\n');
}

// Helper function to wait for a service to be available
async function waitForService(url, maxAttempts = 30, interval = 1000) {
  log(`Waiting for service at ${url}...`);

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      await axios.get(url);
      log(`Service at ${url} is available!`);
      return true;
    } catch (error) {
      if (attempt === maxAttempts) {
        log(`Service at ${url} is not available after ${maxAttempts} attempts.`);
        return false;
      }
      await new Promise(resolve => setTimeout(resolve, interval));
    }
  }

  return false;
}

// Start the real API server
async function startRealApiServer() {
  log('Starting real backend API server...');

  // Create a .env file for the API server
  const envFilePath = path.join(__dirname, '../backend/api/.env');
  const envContent = `
PORT=${API_PORT}
NODE_ENV=development
ETHEREUM_RPC_URL=${HARDHAT_URL}
FORK_MODE=true
LOG_LEVEL=debug
`;

  fs.writeFileSync(envFilePath, envContent);
  log(`Created .env file at ${envFilePath}`);

  // Ensure contract addresses are available
  const contractAddressesPath = path.join(__dirname, '../backend/config/contractAddresses.json');
  if (!fs.existsSync(contractAddressesPath)) {
    log(`Contract addresses file not found at ${contractAddressesPath}. Creating directory...`);
    const contractAddressesDir = path.dirname(contractAddressesPath);
    if (!fs.existsSync(contractAddressesDir)) {
      fs.mkdirSync(contractAddressesDir, { recursive: true });
    }
    
    // We'll wait for the real contract addresses to be populated by the deployment script
    // instead of using mock addresses
    fs.writeFileSync(contractAddressesPath, JSON.stringify({}, null, 2));
    log(`Created empty contract addresses file at ${contractAddressesPath}. It will be populated by the deployment script.`);
  }

  // Ensure ABI files are available
  const abiDir = path.join(__dirname, '../backend/config/abis');
  if (!fs.existsSync(abiDir)) {
    log(`ABI directory not found at ${abiDir}. Creating directory...`);
    fs.mkdirSync(abiDir, { recursive: true });
  }

  // We'll use the real ABIs from the artifacts directory after deployment
  const artifactsDir = path.join(__dirname, '../artifacts/contracts');
  
  const arbitrageExecutorAbiPath = path.join(abiDir, 'ArbitrageExecutor.json');
  if (!fs.existsSync(arbitrageExecutorAbiPath) && fs.existsSync(artifactsDir)) {
    log(`Copying real ArbitrageExecutor ABI from artifacts...`);
    try {
      const artifactPath = path.join(artifactsDir, 'ArbitrageExecutor.sol/ArbitrageExecutor.json');
      if (fs.existsSync(artifactPath)) {
        const artifact = JSON.parse(fs.readFileSync(artifactPath, 'utf8'));
        fs.writeFileSync(arbitrageExecutorAbiPath, JSON.stringify(artifact.abi, null, 2));
        log(`Copied real ArbitrageExecutor ABI to ${arbitrageExecutorAbiPath}`);
      } else {
        log(`ArbitrageExecutor artifact not found at ${artifactPath}`);
      }
    } catch (error) {
      log(`Error copying ArbitrageExecutor ABI: ${error.message}`);
    }
  }

  const flashLoanServiceAbiPath = path.join(abiDir, 'FlashLoanService.json');
  if (!fs.existsSync(flashLoanServiceAbiPath) && fs.existsSync(artifactsDir)) {
    log(`Copying real FlashLoanService ABI from artifacts...`);
    try {
      const artifactPath = path.join(artifactsDir, 'FlashLoanService.sol/FlashLoanService.json');
      if (fs.existsSync(artifactPath)) {
        const artifact = JSON.parse(fs.readFileSync(artifactPath, 'utf8'));
        fs.writeFileSync(flashLoanServiceAbiPath, JSON.stringify(artifact.abi, null, 2));
        log(`Copied real FlashLoanService ABI to ${flashLoanServiceAbiPath}`);
      } else {
        log(`FlashLoanService artifact not found at ${artifactPath}`);
      }
    } catch (error) {
      log(`Error copying FlashLoanService ABI: ${error.message}`);
    }
  }

  // Start the API server
  const apiProcess = spawn('npm', ['start'], {
    cwd: path.join(__dirname, '../backend/api'),
    env: {
      ...process.env,
      PORT: API_PORT,
      NODE_ENV: 'development',
      ETHEREUM_RPC_URL: HARDHAT_URL,
      FORK_MODE: 'true',
      LOG_LEVEL: 'info'
    },
    stdio: 'pipe'
  });

  // Handle output
  apiProcess.stdout.on('data', data => {
    const output = data.toString();
    logStream.write(`[API] ${output}`);
    
    // Also log important messages to console
    if (output.includes('error') || output.includes('Error') || 
        output.includes('started') || output.includes('listening') ||
        output.includes('Web3Service')) {
      console.log(`[API] ${output}`);
    }
  });

  apiProcess.stderr.on('data', data => {
    const error = data.toString();
    logStream.write(`[API ERROR] ${error}`);
    console.error(`[API ERROR] ${error}`);
  });

  // Wait for API server to start
  const isApiAvailable = await waitForService(`${API_URL}/health`);

  if (!isApiAvailable) {
    log('Failed to start API server.');
    apiProcess.kill();
    process.exit(1);
  }

  log('API server started successfully!');
  return apiProcess;
}

// Main function
async function main() {
  try {
    const apiServer = await startRealApiServer();

    // Keep the script running
    log('API server is running. Press Ctrl+C to stop.');

    // Handle process termination
    process.on('SIGINT', () => {
      log('Stopping API server...');
      apiServer.kill();
      logStream.end();
      process.exit(0);
    });
  } catch (error) {
    log(`Error: ${error.message}`);
    process.exit(1);
  }
}

// Run the main function
main().catch(error => {
  log(`Unhandled error: ${error.message}`);
  process.exit(1);
}); 