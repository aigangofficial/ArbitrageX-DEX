import { ethers } from 'ethers';

export interface IUniswapV2Router02 {
  getAmountsOut(amountIn: bigint, path: string[]): Promise<bigint[]>;
}

export interface FlashLoanService {
  executeArbitrage(
    tokenA: string,
    tokenB: string,
    amount: bigint
  ): Promise<ethers.ContractTransactionResponse>;
}

export interface ArbitrageExecutor {
  executeArbitrage(
    tokenA: string,
    tokenB: string,
    amount: bigint
  ): Promise<ethers.ContractTransactionResponse>;
}
