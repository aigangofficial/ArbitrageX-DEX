export interface PriceData {
  tokenA: string;
  tokenB: string;
  uniswapPrice: {
    price: bigint;
    liquidity: bigint;
  };
  sushiswapPrice: {
    price: bigint;
    liquidity: bigint;
  };
}

export interface ArbitrageOpportunity {
  tokenA: string;
  tokenB: string;
  amountIn: bigint;
  expectedProfit: bigint;
  route: {
    sourceExchange: string;
    targetExchange: string;
    path: string[];
  };
  _id?: string;
}
