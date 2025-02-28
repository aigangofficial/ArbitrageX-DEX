import * as dotenv from 'dotenv';
import { resolve } from 'path';

// Load environment variables from .env.root
dotenv.config({ path: resolve(__dirname, '../../.env.root') });

import { ethers } from 'ethers';
import { config } from '../api/config';
import { logger } from '../api/utils/logger';
import { TradeExecutor } from './tradeExecutor';

// Router ABI - only methods we need
const ROUTER_ABI = [
  'function getAmountsOut(uint amountIn, address[] memory path) external view returns (uint[] memory amounts)',
  'function swapExactTokensForTokens(uint amountIn, uint amountOutMin, address[] calldata path, address to, uint deadline) external returns (uint[] memory amounts)',
];

// Aave Pool ABI - only methods we need
const AAVE_POOL_ABI = [
  'function flashLoanSimple(address receiverAddress, address asset, uint256 amount, bytes calldata params, uint16 referralCode) external returns (bool)',
];

// Factory ABI for getting pairs
const FACTORY_ABI = [
  'function getPair(address tokenA, address tokenB) external view returns (address pair)',
  'function allPairs(uint) external view returns (address pair)',
  'function allPairsLength() external view returns (uint)',
];

const PAIR_ABI = [
  'function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast)',
  'function token0() external view returns (address)',
  'function token1() external view returns (address)',
];

// Debug environment variables
logger.info('Environment variables:', {
  NETWORK_RPC: process.env.NETWORK_RPC,
  NETWORK_NAME: process.env.NETWORK_NAME,
  CHAIN_ID: process.env.CHAIN_ID,
});

// Log config values for debugging
logger.info('Using configuration:', {
  network: {
    rpc: config.network.rpc,
    name: config.network.name,
    chainId: config.network.chainId,
  },
  contracts: {
    uniswapRouter: config.contracts.uniswapRouter,
    sushiswapRouter: config.contracts.sushiswapRouter,
    wmatic: config.contracts.wmatic,
    usdt: config.contracts.usdt,
  },
});

async function validateNetwork() {
  try {
    const provider = new ethers.JsonRpcProvider(config.network.rpc);
    const network = await provider.getNetwork();

    logger.info('Connected to network:', {
      name: network.name,
      chainId: network.chainId,
    });

    return true;
  } catch (error) {
    logger.error('Network validation failed:', error);
    return false;
  }
}

interface IDEXRouter {
  estimateGas: {
    swapExactTokensForTokens(
      amountIn: bigint,
      amountOutMin: bigint,
      path: string[],
      to: string,
      deadline: number
    ): Promise<bigint>;
  };
  getAmountsOut(amountIn: bigint, path: string[]): Promise<bigint[]>;
  address: string;
}

async function validateContracts() {
  try {
    const provider = new ethers.JsonRpcProvider(config.network.rpc);

    // Initialize contracts
    const uniswapRouter = new ethers.Contract(
      config.contracts.uniswapRouter,
      ROUTER_ABI,
      provider
    ) as unknown as IDEXRouter;

    const sushiswapRouter = new ethers.Contract(
      config.contracts.sushiswapRouter,
      ROUTER_ABI,
      provider
    ) as unknown as IDEXRouter;

    const aavePool = new ethers.Contract(config.contracts.aavePool, AAVE_POOL_ABI, provider);

    // Create trade executor
    const executor = new TradeExecutor(provider, uniswapRouter, sushiswapRouter, aavePool);

    // Test parameters
    const tokenA = config.contracts.weth;
    const tokenB = config.contracts.usdc;
    const amountIn = ethers.parseUnits('1', '18'); // 1 ETH

    // Test getAmountsOut
    const amountsUniswap = await uniswapRouter.getAmountsOut(amountIn, [tokenA, tokenB]);
    const amountsSushiswap = await sushiswapRouter.getAmountsOut(amountIn, [tokenA, tokenB]);

    logger.info('Price comparison:', {
      uniswap: amountsUniswap[1].toString(),
      sushiswap: amountsSushiswap[1].toString(),
    });

    return true;
  } catch (error) {
    logger.error('Contract validation failed:', error);
    return false;
  }
}

async function runTestSimulation() {
  try {
    // Validate network connection
    if (!(await validateNetwork())) {
      throw new Error('Network validation failed');
    }

    // Validate contract interactions
    if (!(await validateContracts())) {
      throw new Error('Contract validation failed');
    }

    logger.info('Test simulation completed successfully');
  } catch (error) {
    logger.error('Test simulation failed:', error);
    process.exit(1);
  }
}

runTestSimulation().catch(console.error);
