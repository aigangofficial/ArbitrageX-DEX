const path = require('path');

// Mock environment variables
process.env.NETWORK_RPC = 'https://mainnet.infura.io/v3/test';
process.env.CHAIN_ID = '1';
process.env.NETWORK_NAME = 'ethereum';

// Mainnet addresses
process.env.UNISWAP_ROUTER_ADDRESS = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'; // Uniswap V2 Router
process.env.SUSHISWAP_ROUTER_ADDRESS = '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F'; // SushiSwap Router
process.env.AAVE_POOL_ADDRESS = '0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9'; // Aave V2 Pool
process.env.WETH_ADDRESS = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'; // WETH
process.env.USDC_ADDRESS = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'; // USDC
process.env.USDT_ADDRESS = '0xdAC17F958D2ee523a2206206994597C13D831ec7'; // USDT

// AI Model settings
process.env.AI_MODEL_PATH = path.join(__dirname, '../ai/models/trading_ai.pth');
process.env.AI_TRAINING_DATA = path.join(__dirname, '../ai/data/training_data.csv');

// Test settings
jest.setTimeout(30000);

// Suppress console logs during tests
global.console = {
  ...console,
  log: jest.fn(),
  error: jest.fn(),
  warn: jest.fn(),
  info: jest.fn(),
};
