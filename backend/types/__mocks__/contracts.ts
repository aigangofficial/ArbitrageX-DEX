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

export class FlashLoanService {
  constructor(private readonly address: string) {}

  async executeArbitrage(
    tokenA: string,
    tokenB: string,
    amount: bigint
  ): Promise<{
    to: string;
    data: string;
    wait: () => Promise<{ hash: string; gasUsed: bigint }>;
  }> {
    // Mock implementation that uses all parameters
    console.log(`Mock arbitrage execution:
      Token A: ${tokenA}
      Token B: ${tokenB}
      Amount: ${amount}
      Contract Address: ${this.address}
    `);

    // Return deterministic mock data based on inputs
    const mockHash = Buffer.from(`${tokenA}-${tokenB}-${amount}-${this.address}`).toString('hex');
    return {
      to: this.address,
      data: '0x' + mockHash,
      wait: async () => ({
        hash: '0x' + mockHash.padEnd(64, '0'),
        gasUsed: BigInt(100000),
      }),
    };
  }
}

export const mockFlashLoanService = (_address: string, _provider: any) => ({
  executeArbitrage: async (
    _tokenA: string,
    _tokenB: string,
    _exchangeA: string,
    _exchangeB: string,
    _amount: bigint
  ) => {
    // Mock implementation
    return Promise.resolve({} as any);
  },
});

export class MockFlashLoanContract {
  constructor(private readonly address: string) {}

  async executeArbitrage(
    tokenA: string,
    tokenB: string,
    amount: bigint
  ): Promise<{ hash: string }> {
    // Mock implementation that uses all parameters
    console.log(`Mock arbitrage execution:
      Token A: ${tokenA}
      Token B: ${tokenB}
      Amount: ${amount}
      Contract Address: ${this.address}
    `);

    // Return a deterministic mock transaction hash based on inputs
    const mockHash = Buffer.from(`${tokenA}-${tokenB}-${amount}-${this.address}`).toString('hex');
    return { hash: '0x' + mockHash.padEnd(64, '0') };
  }
}
