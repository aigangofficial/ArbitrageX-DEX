import { Provider } from '@ethersproject/abstract-provider';
import { JsonRpcProvider } from '@ethersproject/providers';
import { getConfig } from '../api/config';
import { ArbitrageScanner } from './arbitrageScanner';
import { logger } from '../utils/logger';
import winston from 'winston';
import { Contract } from 'ethers';
import mongoose from 'mongoose';
import connectDB from '../database/connection';
import ArbitrageService from '../services/arbitrageService';
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

// Add or update these constants for the lock file
const LOCK_FILE_PATH = path.join(__dirname, 'bot.lock');
const PID_FILE_PATH = path.join(__dirname, 'bot.pid');

// Ensure logs directory exists
const logsDir = path.join(__dirname, 'logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

// Function to kill any running instances of the bot
function killRunningInstances(): boolean {
  try {
    logger.info('Checking for running bot instances...');
    
    // Check for running bot processes
    const botProcesses = [
      'ts-node bot.ts',
      'node dist/execution/bot.js',
      'npm run bot:start'
    ];
    
    let processesKilled = false;
    
    for (const processPattern of botProcesses) {
      try {
        // Use a more precise pattern that matches how the process actually runs
        const result = execSync(`pkill -f "${processPattern}" || echo "No processes found to kill"`).toString().trim();
        if (!result.includes('No processes found to kill')) {
          logger.info(`Killed processes matching: ${processPattern}`);
          processesKilled = true;
        }
      } catch (error) {
        logger.warn(`Error killing processes matching ${processPattern}: ${error instanceof Error ? error.message : String(error)}`);
      }
    }
    
    if (!processesKilled) {
      logger.info('No running bot instances found.');
    } else {
      // Give processes time to fully terminate
      execSync('sleep 1');
    }
    
    return processesKilled;
  } catch (error) {
    logger.warn(`Error killing running instances: ${error instanceof Error ? error.message : String(error)}`);
    return false;
  }
}

// Kill any running instances before starting
killRunningInstances();

// Check if another instance is running
if (checkLock()) {
  logger.error('Another instance of the bot is already running. Exiting.');
  process.exit(1);
}

// Create lock file
createLock();
logger.info(`Bot started with PID ${process.pid}`);

// Add or update these functions for lock file management
function checkLock(): boolean {
  try {
    if (fs.existsSync(LOCK_FILE_PATH)) {
      // Check if the process is still running
      const pid = fs.readFileSync(PID_FILE_PATH, 'utf8').trim();
      try {
        // Try to send a signal to the process to check if it's running
        process.kill(parseInt(pid, 10), 0);
        logger.error(`Bot is already running with PID ${pid}`);
        return true;
      } catch (e) {
        // Process doesn't exist, so we can remove the stale lock
        logger.warn(`Removing stale lock file for non-existent PID ${pid}`);
        removeLock();
        return false;
      }
    }
    return false;
  } catch (error) {
    logger.error(`Error checking lock file: ${error instanceof Error ? error.message : String(error)}`);
    return false;
  }
}

function createLock(): void {
  try {
    // Write the current PID to the lock file
    fs.writeFileSync(LOCK_FILE_PATH, 'LOCKED');
    fs.writeFileSync(PID_FILE_PATH, process.pid.toString());
    logger.info(`Created lock file with PID ${process.pid}`);
    
    // Register cleanup handlers
    process.on('exit', removeLock);
    process.on('SIGINT', () => {
      logger.info('Bot stopped by user (SIGINT)');
      removeLock();
      process.exit(0);
    });
    process.on('SIGTERM', () => {
      logger.info('Bot stopped by system (SIGTERM)');
      removeLock();
      process.exit(0);
    });
    process.on('uncaughtException', (error) => {
      logger.error(`Uncaught exception: ${error instanceof Error ? error.message : String(error)}`);
      removeLock();
      process.exit(1);
    });
  } catch (error) {
    logger.error(`Error creating lock file: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
  }
}

function removeLock(): void {
  try {
    if (fs.existsSync(LOCK_FILE_PATH)) {
      fs.unlinkSync(LOCK_FILE_PATH);
      logger.info('Removed lock file');
    }
    if (fs.existsSync(PID_FILE_PATH)) {
      fs.unlinkSync(PID_FILE_PATH);
      logger.info('Removed PID file');
    }
  } catch (error) {
    logger.error(`Error removing lock file: ${error instanceof Error ? error.message : String(error)}`);
  }
}

// Add a more robust cleanup function
function cleanupAndExit(exitCode: number = 0, reason: string = 'unknown'): void {
  logger.info(`Bot stopping. Reason: ${reason}`);
  
  // Stop the scanner if it exists
  try {
    if (global.scanner) {
      logger.info('Stopping scanner...');
      global.scanner.stop();
    }
  } catch (error) {
    logger.error(`Error stopping scanner: ${error instanceof Error ? error.message : String(error)}`);
  }
  
  // Remove lock files
  removeLock();
  
  // Exit with the provided code
  logger.info(`Exiting with code ${exitCode}`);
  process.exit(exitCode);
}

// Declare global namespace for TypeScript
declare global {
  var scanner: any;
}

// ERC20 ABI for token validation
const ERC20_ABI = [
  "function name() view returns (string)",
  "function symbol() view returns (string)",
  "function decimals() view returns (uint8)",
  "function balanceOf(address) view returns (uint)"
];

// Parse command line arguments
const args = process.argv.slice(2);
let runTime = 600; // Default 10 minutes
let tokens = 'WETH,USDC,DAI';
let dexes = 'uniswap_v3,curve,balancer';
let gasStrategy = 'dynamic';

// Parse command line arguments
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--run-time' && i + 1 < args.length) {
    runTime = parseInt(args[i + 1], 10);
    i++;
  } else if (args[i] === '--tokens' && i + 1 < args.length) {
    tokens = args[i + 1];
    i++;
  } else if (args[i] === '--dexes' && i + 1 < args.length) {
    dexes = args[i + 1];
    i++;
  } else if (args[i] === '--gas-strategy' && i + 1 < args.length) {
    gasStrategy = args[i + 1];
    i++;
  }
}

logger.info(`Starting ArbitrageX bot with the following configuration:`);
logger.info(`Run time: ${runTime} seconds`);
logger.info(`Tokens: ${tokens}`);
logger.info(`DEXes: ${dexes}`);
logger.info(`Gas strategy: ${gasStrategy}`);

const config = getConfig();
let provider: Provider;

// Try to connect to the primary RPC provider
try {
  provider = new JsonRpcProvider(config.network.rpc) as unknown as Provider;
  logger.info(`Connected to primary RPC provider: ${config.network.rpc.split('/')[2]}`);
} catch (error) {
  // If primary fails, try a fallback provider
  const errorMessage = error instanceof Error ? error.message : String(error);
  logger.warn(`Failed to connect to primary RPC provider: ${errorMessage}`);
  
  // Fallback to Alchemy if available, or use a public endpoint
  const fallbackRpc = process.env.FALLBACK_RPC || 'https://eth-mainnet.g.alchemy.com/v2/demo';
  logger.info(`Trying fallback RPC provider: ${fallbackRpc.split('/')[2]}`);
  provider = new JsonRpcProvider(fallbackRpc) as unknown as Provider;
}

// Parse tokens from command line
const tokenList = tokens.split(',');
const tokenPairs = [];

// Helper function to validate token contract
async function validateTokenContract(address: string): Promise<boolean> {
  try {
    if (!address || address.length !== 42) {
      logger.warn(`Invalid token address format: ${address}`);
      return false;
    }

    // Get the current network from the provider
    const network = await provider.getNetwork();
    const chainId = Number(network.chainId);
    
    logger.info(`Validating token on network with chainId: ${chainId}`);

    // Define network-specific token addresses
    const networkTokens: Record<number, Record<string, string>> = {
      // Ethereum Mainnet (1)
      1: {
        WETH: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
        USDC: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
        USDT: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
        DAI: '0x6B175474E89094C44Da98b954EedeAC495271d0F'
      },
      // Polygon (137)
      137: {
        WETH: '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
        USDC: '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
        USDT: '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
        DAI: '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063'
      },
      // Arbitrum (42161)
      42161: {
        WETH: '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
        USDC: '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',
        USDT: '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
        DAI: '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1'
      },
      // BSC (56)
      56: {
        WETH: '0x2170Ed0880ac9A755fd29B2688956BD959F933F8', // WETH on BSC
        USDC: '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
        USDT: '0x55d398326f99059fF775485246999027B3197955',
        DAI: '0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3'
      }
    };

    // Check if the address matches any known token on the current network
    let isKnownToken = false;
    let tokenSymbol = '';
    
    // Check if the address matches any known token on the current network
    if (networkTokens[chainId]) {
      for (const [symbol, tokenAddress] of Object.entries(networkTokens[chainId])) {
        if (address.toLowerCase() === tokenAddress.toLowerCase()) {
          isKnownToken = true;
          tokenSymbol = symbol;
          logger.info(`Address ${address} recognized as ${symbol} on network ${chainId}`);
          break;
        }
      }
    }
    
    // Check if the address is from a different network
    if (!isKnownToken) {
      for (const [networkId, tokens] of Object.entries(networkTokens)) {
        const netId = parseInt(networkId);
        if (netId !== chainId) {
          for (const [symbol, tokenAddress] of Object.entries(tokens)) {
            if (address.toLowerCase() === tokenAddress.toLowerCase()) {
              logger.warn(`Address ${address} is ${symbol} from network ${networkId}, but we're on network ${chainId}`);
              
              // If we're in fork mode, we can proceed with tokens from other networks
              if (process.env.EXECUTION_MODE === 'fork') {
                logger.info(`Running in fork mode, allowing token from different network`);
                return true;
              }
              
              // Get the correct address for this token on the current network
              const correctAddress = networkTokens[chainId]?.[symbol];
              if (correctAddress) {
                logger.warn(`Should use ${correctAddress} for ${symbol} on network ${chainId} instead`);
              }
              
              return false;
            }
          }
        }
      }
    }

    // If we're in fork mode and it's a known token, we can skip the contract validation
    if (process.env.EXECUTION_MODE === 'fork' && isKnownToken) {
      logger.info(`Running in fork mode with known token ${tokenSymbol}, skipping contract validation`);
      return true;
    }

    // Attempt to validate the token contract on-chain
    try {
      const tokenContract = new Contract(address, ERC20_ABI, provider as any);
      const [symbol, decimals] = await Promise.all([
        tokenContract.symbol(),
        tokenContract.decimals()
      ]);

      logger.info(`Validated token ${symbol} with ${decimals} decimals at address ${address}`);
      return true;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      logger.error(`Failed to validate token contract at ${address}: ${errorMessage}`);
      
      // If we're in fork mode, we might want to proceed despite validation failures
      if (process.env.EXECUTION_MODE === 'fork') {
        logger.warn(`Running in fork mode - proceeding with token ${address} despite validation failure`);
        return true;
      }
      
      return false;
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    logger.error(`Error in validateTokenContract: ${errorMessage}`);
    return false;
  }
}

// Helper function to get token address from symbol
async function getTokenAddress(symbol: string, config: any): Promise<string | null> {
  const upperSymbol = symbol.toUpperCase();
  
  // Get the current network from the provider
  let chainId: number = 1; // Default to Ethereum mainnet
  try {
    const network = await provider.getNetwork();
    chainId = Number(network.chainId);
    logger.info(`Current network chainId: ${chainId}`);
  } catch (error) {
    logger.error(`Failed to get network: ${error instanceof Error ? error.message : String(error)}`);
  }
  
  // Network-specific token addresses
  const networkTokens: Record<number, Record<string, string>> = {
    // Ethereum Mainnet (1)
    1: {
      WETH: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
      USDC: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
      USDT: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
      DAI: '0x6B175474E89094C44Da98b954EedeAC495271d0F'
    },
    // Polygon (137)
    137: {
      WETH: '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
      USDC: '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
      USDT: '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
      DAI: '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063'
    },
    // Arbitrum (42161)
    42161: {
      WETH: '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
      USDC: '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',
      USDT: '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
      DAI: '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1'
    },
    // BSC (56)
    56: {
      WETH: '0x2170Ed0880ac9A755fd29B2688956BD959F933F8', // WETH on BSC
      USDC: '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
      USDT: '0x55d398326f99059fF775485246999027B3197955',
      DAI: '0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3'
    }
  };
  
  // First try to get from network-specific addresses
  if (networkTokens[chainId] && networkTokens[chainId][upperSymbol]) {
    const address = networkTokens[chainId][upperSymbol];
    logger.info(`Using network-specific address for ${upperSymbol} on chainId ${chainId}: ${address}`);
    return address;
  }
  
  // Then try to get from config or environment variables
  let address: string | null = null;
  
  switch (upperSymbol) {
    case 'WETH':
      address = config.contracts.weth || process.env.WETH_ADDRESS;
      break;
    case 'USDC':
      address = config.contracts.usdc || process.env.USDC_ADDRESS;
      break;
    case 'DAI':
      address = config.contracts.dai || process.env.DAI_ADDRESS;
      break;
    case 'USDT':
      address = config.contracts.usdt || process.env.USDT_ADDRESS;
      break;
    default:
      logger.warn(`Unknown token symbol: ${symbol}`);
      return null;
  }
  
  // If address is still null, use fallback from Ethereum mainnet
  if (!address && networkTokens[1][upperSymbol]) {
    address = networkTokens[1][upperSymbol];
    logger.warn(`Using Ethereum mainnet fallback address for ${upperSymbol}: ${address}`);
  }
  
  if (!address) {
    logger.error(`No address found for token: ${symbol}`);
    return null;
  }
  
  return address;
}

// Configure gas strategy
const gasConfig = {
  minProfitThreshold: config.security?.minProfitThreshold || 0.001,
  minNetProfit: 0.001, // 0.1% minimum net profit
  gasLimit: 500000,    // 500k gas limit
  scanInterval: 5000,  // 5 second interval
  maxGasPrice: gasStrategy === 'conservative' ? 50000000000 : 
               gasStrategy === 'aggressive' ? 200000000000 : 100000000000, // 50/100/200 gwei
  gasMultiplier: gasStrategy === 'conservative' ? 1.05 : 
                 gasStrategy === 'aggressive' ? 1.2 : 1.1   // 5%/10%/20% buffer
};

// Create a minimal Winston logger that satisfies the ArbitrageScanner requirements
const scannerLogger = winston.createLogger({
  level: 'info',
  format: winston.format.simple(),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

// Override the log methods to use our custom logger
scannerLogger.info = (message: any) => {
  if (typeof message === 'string') {
    logger.info(message);
  } else {
    logger.info(JSON.stringify(message));
  }
  return scannerLogger;
};

scannerLogger.warn = (message: any) => {
  if (typeof message === 'string') {
    logger.warn(message);
  } else {
    logger.warn(JSON.stringify(message));
  }
  return scannerLogger;
};

scannerLogger.error = (message: any) => {
  if (typeof message === 'string') {
    logger.error(message);
  } else {
    logger.error(JSON.stringify(message));
  }
  return scannerLogger;
};

// Validate and create token pairs
async function setupTokenPairs() {
  const validatedPairs = [];
  
  // Create token pairs from the token list
  for (let i = 0; i < tokenList.length; i++) {
    for (let j = i + 1; j < tokenList.length; j++) {
      const tokenA = tokenList[i].trim();
      const tokenB = tokenList[j].trim();
      
      // Map token symbols to addresses
      const tokenAAddress = await getTokenAddress(tokenA, config);
      const tokenBAddress = await getTokenAddress(tokenB, config);
      
      if (tokenAAddress && tokenBAddress) {
        logger.info(`Validating token pair: ${tokenA}(${tokenAAddress}) - ${tokenB}(${tokenBAddress})`);
        
        // Validate both token contracts
        const [isValidTokenA, isValidTokenB] = await Promise.all([
          validateTokenContract(tokenAAddress),
          validateTokenContract(tokenBAddress)
        ]);
        
        if (isValidTokenA && isValidTokenB) {
          logger.info(`Adding validated token pair: ${tokenA}(${tokenAAddress}) - ${tokenB}(${tokenBAddress})`);
          validatedPairs.push({
            tokenA: tokenAAddress,
            tokenB: tokenBAddress
          });
        } else {
          logger.warn(`Skipping invalid token pair: ${tokenA}(${tokenAAddress}) - ${tokenB}(${tokenBAddress})`);
        }
      } else {
        logger.warn(`Skipping token pair due to missing address: ${tokenA} - ${tokenB}`);
      }
    }
  }
  
  return validatedPairs;
}

// Main function to start the bot
async function startBot() {
  try {
    // Connect to MongoDB if not already connected
    if (mongoose.connection.readyState === 0) {
      logger.info('Connecting to MongoDB...');
      await connectDB();
      logger.info('MongoDB connection established');
    } else {
      logger.info('MongoDB already connected');
    }
    
    // Validate token pairs
    const validatedPairs = await setupTokenPairs();
    
    if (validatedPairs.length === 0) {
      logger.error('No valid token pairs found. Cannot start scanner.');
      process.exit(1);
    }
    
    // Create and start the scanner
    const scanner = new ArbitrageScanner(
      provider,
      config.contracts.uniswapRouter,
      config.contracts.sushiswapRouter,
      gasConfig,
      validatedPairs,
      scannerLogger
    );
    
    // Store scanner in global object for access in signal handlers
    global.scanner = scanner;
    
    // Initialize the arbitrage service with the scanner as the event emitter
    const arbitrageService = new ArbitrageService(scanner);
    
    // Start the scanner
    logger.info(`Starting arbitrage scanner with ${validatedPairs.length} validated token pairs`);
    scanner.start();
    
    // Set a timeout to stop the bot after the specified run time
    setTimeout(() => {
      logger.info(`Run time of ${runTime} seconds reached, stopping bot`);
      cleanupAndExit(0, 'Run time reached');
    }, runTime * 1000);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    logger.error(`Failed to start bot: ${errorMessage}`);
    cleanupAndExit(1, `Failed to start bot: ${errorMessage}`);
  }
}

// Start the bot
startBot().catch(error => {
  const errorMessage = error instanceof Error ? error.message : String(error);
  logger.error(`Unhandled error in bot startup: ${errorMessage}`);
  process.exit(1);
});

// Add SIGUSR1 and SIGUSR2 handlers for more robust signal handling
process.on('SIGUSR1', () => {
  cleanupAndExit(0, 'SIGUSR1 signal received');
});

process.on('SIGUSR2', () => {
  cleanupAndExit(0, 'SIGUSR2 signal received');
}); 