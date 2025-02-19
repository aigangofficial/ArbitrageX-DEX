import dotenv from 'dotenv';
import path from 'path';

// Load environment variables from root .env.root
const envPath = path.resolve(__dirname, '../../.env.root');
console.log('Loading environment variables from:', envPath);
dotenv.config({ path: envPath, override: true });

// Debug loaded environment variables
console.log('Loaded environment variables:', {
  NETWORK_RPC: process.env.NETWORK_RPC,
  NETWORK_NAME: process.env.NETWORK_NAME,
  CHAIN_ID: process.env.CHAIN_ID,
  MUMBAI_QUICKSWAP_ROUTER: process.env.MUMBAI_QUICKSWAP_ROUTER,
  MUMBAI_SUSHISWAP_ROUTER: process.env.MUMBAI_SUSHISWAP_ROUTER,
  MUMBAI_AAVE_POOL: process.env.MUMBAI_AAVE_POOL,
  MUMBAI_WMATIC: process.env.MUMBAI_WMATIC,
  MUMBAI_USDC: process.env.MUMBAI_USDC,
});

export const config = {
  network: {
    rpc: process.env.NETWORK_RPC || 'https://rpc-mumbai.maticvigil.com',
    name: process.env.NETWORK_NAME || 'mumbai',
    chainId: parseInt(process.env.CHAIN_ID || '80001'),
  },
  contracts: {
    quickswapRouter:
      process.env.MUMBAI_QUICKSWAP_ROUTER || '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
    sushiswapRouter:
      process.env.MUMBAI_SUSHISWAP_ROUTER || '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
    aavePool: process.env.MUMBAI_AAVE_POOL || '0x0496275d34753A48320CA58103d5220d394FF77F',
    wmatic: process.env.MUMBAI_WMATIC || '0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889',
    usdc: process.env.MUMBAI_USDC || '0x742DfA5Aa70a8212857966D491D67B09Ce7D6ec7',
    usdt: process.env.MUMBAI_USDC || '0x742DfA5Aa70a8212857966D491D67B09Ce7D6ec7', // Using USDC for testing
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
