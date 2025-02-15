import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

export const config = {
  network: {
    rpc: process.env.NETWORK_RPC || 'http://localhost:8545',
    name: process.env.NETWORK_NAME || 'localhost',
    chainId: parseInt(process.env.CHAIN_ID || '1337'),
  },
  contracts: {
    flashLoanService: process.env.FLASH_LOAN_SERVICE || '',
    quickswapRouter: process.env.AMOY_QUICKSWAP_ROUTER || '',
    sushiswapRouter: process.env.AMOY_SUSHISWAP_ROUTER || '',
    wmatic: process.env.AMOY_WMATIC || '',
    usdc: process.env.AMOY_USDC || '',
    usdt: process.env.AMOY_USDT || '',
    dai: process.env.AMOY_DAI || '',
  },
  database: {
    uri: process.env.MONGODB_URI || 'mongodb://localhost:27017/arbitragex',
  },
  api: {
    port: parseInt(process.env.API_PORT || '3000'),
    wsPort: parseInt(process.env.WS_PORT || '3001'),
    corsOrigin: process.env.CORS_ORIGIN || 'http://localhost:3001',
  },
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    directory: process.env.LOG_DIRECTORY || 'logs',
  },
  security: {
    minProfitThreshold: parseFloat(process.env.MIN_PROFIT_THRESHOLD || '0.01'),
    maxSlippage: parseFloat(process.env.MAX_SLIPPAGE || '0.5'),
    gasPriceLimit: parseInt(process.env.GAS_PRICE_LIMIT || '100'),
  },
};
