import { ethers } from 'ethers';

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
  swapExactTokensForTokens(
    amountIn: bigint,
    amountOutMin: bigint,
    path: string[],
    to: string,
    deadline: number
  ): Promise<bigint[]>;
  factory(): Promise<string>;
  address: string;
}

export class DEXRouterFactory {
  static connect(address: string, provider: ethers.JsonRpcProvider): IDEXRouter {
    const abi = [
      'function getAmountsOut(uint amountIn, address[] memory path) view returns (uint[] memory amounts)',
      'function swapExactTokensForTokens(uint amountIn, uint amountOutMin, address[] memory path, address to, uint deadline) returns (uint[] memory amounts)',
      'function estimateGas() view returns (uint256)'
    ];

    return new ethers.Contract(address, abi, provider) as unknown as IDEXRouter;
  }
}
