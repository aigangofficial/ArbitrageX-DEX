import dotenv from 'dotenv';
import { ethers } from 'ethers';
import path from 'path';

// Load environment variables from config/.env
dotenv.config({ path: path.resolve(__dirname, '.env') });

export const AMOY_CONFIG = {
  rpc: process.env.AMOY_RPC || 'https://polygon-amoy.public.blastapi.io',
  chainId: 80002,
  contracts: {
    aavePool: process.env.AMOY_AAVE_POOL || '0x357D51124f59836DeD84c8a1730D72B749d8BC23',
    quickswapRouter:
      process.env.AMOY_QUICKSWAP_ROUTER || '0x8954AfA98594b838bda56FE4C12a09D7739D179b',
    sushiswapRouter:
      process.env.AMOY_SUSHISWAP_ROUTER || '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
    wmatic: process.env.AMOY_WMATIC || '0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889',
  },
  gas: {
    maxFeePerGas: ethers.parseUnits('50', 'gwei'),
    maxPriorityFeePerGas: ethers.parseUnits('25', 'gwei'),
    gasLimit: 2_000_000,
    priceBuffer: Number(process.env.GAS_PRICE_BUFFER || '110'),
    maxGasPrice: BigInt(process.env.MAX_GAS_PRICE || '100000000000'),
  },
} as const;

export const getProvider = () => {
  return new ethers.JsonRpcProvider(AMOY_CONFIG.rpc);
};
