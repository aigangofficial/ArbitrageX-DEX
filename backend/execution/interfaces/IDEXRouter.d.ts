import { BaseContract, BigNumberish } from 'ethers';
export interface IDEXRouter extends BaseContract {
    getAmountsOut(amountIn: BigNumberish, path: string[]): Promise<bigint[]>;
    factory(): Promise<string>;
    WETH(): Promise<string>;
    swapExactTokensForTokens(amountIn: BigNumberish, amountOutMin: BigNumberish, path: string[], to: string, deadline: BigNumberish): Promise<bigint[]>;
}
export declare const ROUTER_ABI: string[];
export declare class DEXRouterFactory {
    static connect(address: string, provider: any): IDEXRouter;
}
