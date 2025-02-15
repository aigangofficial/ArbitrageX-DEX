export class MockFlashLoanService {
  constructor(_address: string, _provider: unknown) {
    // Mock implementation
  }

  async executeArbitrage(
    _tokenA: string,
    _tokenB: string,
    _exchangeA: string,
    _exchangeB: string,
    _amount: bigint
  ): Promise<any> {
    // Mock implementation
    return Promise.resolve({} as any);
  }
}

export interface IUniswapV2Router02 {
  getAmountsOut(amountIn: bigint, path: string[]): Promise<bigint[]>;
  swapExactTokensForTokens(
    amountIn: bigint,
    amountOutMin: bigint,
    path: string[],
    to: string,
    deadline: bigint
  ): Promise<{ wait: () => Promise<unknown> }>;
}
