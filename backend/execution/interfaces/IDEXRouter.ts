import { BaseContract, BigNumberish } from 'ethers';

export interface IDEXRouter extends BaseContract {
    getAmountsOut(amountIn: BigNumberish, path: string[]): Promise<bigint[]>;
    factory(): Promise<string>;
    WETH(): Promise<string>;
    swapExactTokensForTokens(
        amountIn: BigNumberish,
        amountOutMin: BigNumberish,
        path: string[],
        to: string,
        deadline: BigNumberish
    ): Promise<bigint[]>;
}

export const ROUTER_ABI = [
    'function getAmountsOut(uint amountIn, address[] memory path) view returns (uint[] memory amounts)',
    'function factory() external pure returns (address)',
    'function WETH() external pure returns (address)',
    'function swapExactTokensForTokens(uint amountIn, uint amountOutMin, address[] calldata path, address to, uint deadline) external returns (uint[] memory amounts)'
];

export class DEXRouterFactory {
    static connect(address: string, provider: any): IDEXRouter {
        return new BaseContract(address, ROUTER_ABI, provider) as IDEXRouter;
    }
}
