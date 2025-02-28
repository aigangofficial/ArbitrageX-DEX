import dotenv from 'dotenv';
import { ethers } from 'ethers';
import path from 'path';

// Load environment variables from config/.env
dotenv.config({ path: path.resolve(__dirname, '.env') });

export const NETWORKS = {
  fork: {
    name: 'mainnet-fork',
    chainId: 1,
    rpc: process.env.MAINNET_RPC_URL,
    contracts: {
      aavePool: '0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9',
      uniswapV2Router: '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
      sushiswapRouter: '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F'
    },
    tokens: {
      weth: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
      usdc: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
      usdt: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
      dai: '0x6B175474E89094C44Da98b954EedeAC495271d0F'
    }
  },
  gas: {
    maxFeePerGas: ethers.parseUnits('50', 'gwei'),
    maxPriorityFeePerGas: ethers.parseUnits('25', 'gwei'),
    gasLimit: 2_000_000,
    priceBuffer: Number(process.env.GAS_PRICE_BUFFER || '110'),
    maxGasPrice: BigInt(process.env.MAX_GAS_PRICE || '100000000000'),
  }
} as const;

export const FORK_CONFIG = {
  blockNumber: 19261000,
  enabled: true,
  ignoreUnknownTxType: true,
  timeout: 0
} as const;

export default NETWORKS;
