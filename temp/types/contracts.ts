import { AddressLike, BigNumberish, BytesLike } from 'ethers';
import { ArbitrageExecutor, FlashLoanService } from '../../typechain-types';

export interface IUniswapV2Router02 {
  getAmountsOut(amountIn: BigNumberish, path: AddressLike[]): Promise<BigNumberish[]>;
}

export type FlashLoanServiceContract = FlashLoanService;
export type ArbitrageExecutorContract = ArbitrageExecutor;

export interface IFlashLoanParams {
  tokenA: AddressLike;
  tokenB: AddressLike;
  amount: BigNumberish;
  params: BytesLike;
}

export interface IArbitrageParams {
  tokenA: AddressLike;
  tokenB: AddressLike;
  amountIn: BigNumberish;
  startWithUniswap: boolean;
}

export interface ITradeResult {
  success: boolean;
  profit: BigNumberish;
  gasUsed: BigNumberish;
  error?: string;
}
