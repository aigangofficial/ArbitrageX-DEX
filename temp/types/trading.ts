import { BigNumberish } from 'ethers';

export interface PriceData {
  uniswapPrice: bigint;
  sushiswapPrice: bigint;
  uniswapLiquidity: bigint;
  sushiswapLiquidity: bigint;
}

export interface ArbitrageOpportunity {
  tokenA: string;
  tokenB: string;
  amountIn: bigint;
  expectedProfit: bigint;
  route: 'UNIV2_TO_SUSHI' | 'SUSHI_TO_UNIV2';
  confidence: number;
}

export interface TradeResult {
  success: boolean;
  profit: BigNumberish;
  gasUsed: BigNumberish;
  error?: string;
}

export interface MarketState {
  prices: PriceData;
  timestamp: number;
  gasPrice: bigint;
  blockNumber: number;
}
