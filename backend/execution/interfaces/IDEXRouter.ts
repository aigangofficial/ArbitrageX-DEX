export interface IDEXRouter {
  estimateGas: {
    swapExactTokensForTokens(
      amountIn: bigint,
      amountOutMin: bigint,
      path: string[],
      to: string,
      deadline: number
    ): Promise<bigint>;
  };
  getAmountsOut(amountIn: bigint, path: string[]): Promise<bigint[]>;
  factory(): Promise<string>;
  address: string;
}
