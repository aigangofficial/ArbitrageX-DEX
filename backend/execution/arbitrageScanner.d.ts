import { EventEmitter } from 'events';
import { Logger } from 'winston';
import { ArbitrageOpportunity } from '../ai/interfaces/simulation';
import { Provider } from '@ethersproject/abstract-provider';
interface TokenPair {
    tokenA: string;
    tokenB: string;
}
interface ScannerConfig {
    minProfitThreshold: number;
    minNetProfit: number;
    gasLimit: number;
    scanInterval: number;
    maxGasPrice: number;
    gasMultiplier: number;
}
export declare class ArbitrageScanner extends EventEmitter {
    private readonly provider;
    private readonly uniswapRouterAddress;
    private readonly sushiswapRouterAddress;
    private uniswapRouter;
    private sushiswapRouter;
    private isScanning;
    private scanInterval;
    private tokenPairs;
    private config;
    private lastGasPrice;
    private logger;
    constructor(provider: Provider, uniswapRouterAddress: string, sushiswapRouterAddress: string, config: ScannerConfig, tokenPairs: TokenPair[], logger: Logger);
    private getAmountsOut;
    start(): void;
    stop(): void;
    private scanMarkets;
    private scanPair;
    analyzePool(pool: {
        tokenA: string;
        tokenB: string;
    }): Promise<ArbitrageOpportunity | null>;
    estimateTradeGas(opportunity: ArbitrageOpportunity): Promise<bigint>;
    private createArbitrageOpportunity;
    private calculateOptimalAmount;
    private calculateExpectedProfit;
}
export default ArbitrageScanner;
