import { EventEmitter } from 'events';
import { ArbitrageScanner } from '../execution/arbitrageScanner';
import { CEXPriceFeed } from './cexPriceFeed';
interface AggregatedPrice {
    symbol: string;
    dexPrices: {
        [exchange: string]: string;
    };
    cexPrices: {
        [exchange: string]: string;
    };
    timestamp: number;
    arbitrageOpportunities: ArbitrageOpportunity[];
}
interface ArbitrageOpportunity {
    sourceExchange: string;
    targetExchange: string;
    symbol: string;
    spreadPercentage: string;
    estimatedProfit: string;
    timestamp: number;
}
export declare class PriceAggregator extends EventEmitter {
    private readonly cexFeed;
    private readonly dexScanner;
    private prices;
    private readonly MIN_PROFIT_THRESHOLD;
    private updateInterval;
    private readonly UPDATE_INTERVAL;
    constructor(cexFeed: CEXPriceFeed, dexScanner: ArbitrageScanner);
    private setupEventHandlers;
    private handleCEXPriceUpdate;
    private handleDEXPriceUpdate;
    private checkArbitrageOpportunities;
    private calculateSpread;
    private estimateProfit;
    start(): void;
    stop(): void;
    getPrices(): AggregatedPrice[];
    getArbitrageOpportunities(): ArbitrageOpportunity[];
}
export default PriceAggregator;
