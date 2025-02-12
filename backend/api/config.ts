import dotenv from 'dotenv';
import { resolve } from 'path';

// Load environment variables from config/.env
dotenv.config({ path: resolve(__dirname, '../../config/.env') });

export const config = {
  network: {
    name: 'amoy',
    chainId: 80002,
    rpc: process.env.AMOY_RPC || 'https://rpc-amoy.polygon.technology',
  },
  contracts: {
    flashLoanService: '0x47BB8898208387dD09a33557675DB48824761d1E',
    arbitrageExecutor: '0x1F2dCDd24430c300431329FEC10a32bf3d67EE8f',
    aavePool: '0x357D51124f59836DeD84c8a1730D72B749d8BC23',
    quickswapRouter: '0x8954AfA98594b838bda56FE4C12a09D7739D179b',
    sushiswapRouter: '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
    wmatic: '0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889',
  },
  database: {
    uri: process.env.MONGODB_URI || 'mongodb://mongodb:27017/arbitragex',
    options: {
      maxPoolSize: Number(process.env.MONGODB_MAX_POOL_SIZE) || 10,
      minPoolSize: Number(process.env.MONGODB_MIN_POOL_SIZE) || 5,
    },
  },
  api: {
    port: Number(process.env.PORT) || 3000,
    wsPort: Number(process.env.WS_PORT) || 3001,
    corsOrigin: process.env.CORS_ORIGIN || 'http://localhost:3000',
  },
  trading: {
    minProfitBps: Number(process.env.MIN_PROFIT_BPS) || 50,
    maxSlippageBps: Number(process.env.MAX_SLIPPAGE_BPS) || 100,
    gasMultiplier: Number(process.env.GAS_PRICE_MULTIPLIER) || 1.1,
    maxGasPrice: Number(process.env.MAX_GAS_PRICE) || 100, // in Gwei
  },
} as const;
