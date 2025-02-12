import { ethers } from 'ethers';

export interface ContractTransaction extends ethers.ContractTransaction {
  wait(): Promise<ethers.ContractReceipt>;
}

export interface IFlashLoanService {
  executeArbitrage(
    tokenA: string,
    tokenB: string,
    exchangeA: string,
    exchangeB: string,
    amount: bigint
  ): Promise<ContractTransaction>;
}

export class FlashLoanService implements IFlashLoanService {
  constructor(address: string, provider: ethers.Provider);

  executeArbitrage(
    tokenA: string,
    tokenB: string,
    exchangeA: string,
    exchangeB: string,
    amount: bigint
  ): Promise<ContractTransaction>;
}

export interface IUniswapV2Router02 {
  getAmountsOut(amountIn: bigint, path: string[]): Promise<bigint[]>;

  swapExactTokensForTokens(
    amountIn: bigint,
    amountOutMin: bigint,
    path: string[],
    to: string,
    deadline: bigint
  ): Promise<ContractTransaction>;
}
