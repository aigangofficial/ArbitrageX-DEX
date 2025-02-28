import { BigNumber } from '@ethersproject/bignumber';
import { EventEmitter } from 'events';
import { ArbitrageScanner } from '../execution/arbitrageScanner';
import { logger } from '../utils/logger';
import { CEXPriceFeed, PriceUpdate } from './cexPriceFeed';

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

export class PriceAggregator extends EventEmitter {
    private prices: Map<string, AggregatedPrice> = new Map();
    private readonly MIN_PROFIT_THRESHOLD = 0.5; // 0.5% minimum spread
    private updateInterval: NodeJS.Timeout | null = null;
    private readonly UPDATE_INTERVAL = 1000; // 1 second

    constructor(
        private readonly cexFeed: CEXPriceFeed,
        private readonly dexScanner: ArbitrageScanner
    ) {
        super();
        this.setupEventHandlers();
    }

    private setupEventHandlers(): void {
        this.cexFeed.on('priceUpdate', (update: PriceUpdate) => {
            this.handleCEXPriceUpdate(update);
        });

        this.dexScanner.on('arbitrageOpportunity', (opportunity: any) => {
            this.handleDEXPriceUpdate(opportunity);
        });
    }

    private handleCEXPriceUpdate(update: PriceUpdate): void {
        const current = this.prices.get(update.symbol) || {
            symbol: update.symbol,
            dexPrices: {},
            cexPrices: {},
            timestamp: Date.now(),
            arbitrageOpportunities: []
        };

        current.cexPrices[update.exchange] = update.price;
        current.timestamp = update.timestamp;

        this.prices.set(update.symbol, current);
        this.checkArbitrageOpportunities(update.symbol);
    }

    private handleDEXPriceUpdate(opportunity: any): void {
        const symbol = opportunity.pair;
        const current = this.prices.get(symbol) || {
            symbol,
            dexPrices: {
                uniswap: '',
                sushiswap: ''
            },
            cexPrices: {},
            timestamp: Date.now(),
            arbitrageOpportunities: []
        };

        current.dexPrices['uniswap'] = opportunity.uniswapPrice;
        current.dexPrices['sushiswap'] = opportunity.sushiswapPrice;
        current.timestamp = opportunity.timestamp;

        this.prices.set(symbol, current);
        this.checkArbitrageOpportunities(symbol);
    }

    private checkArbitrageOpportunities(symbol: string): void {
        const priceData = this.prices.get(symbol);
        if (!priceData) return;

        const opportunities: ArbitrageOpportunity[] = [];

        // Compare CEX vs DEX prices
        for (const [cexName, cexPrice] of Object.entries(priceData.cexPrices)) {
            for (const [dexName, dexPrice] of Object.entries(priceData.dexPrices)) {
                const spread = this.calculateSpread(
                    BigNumber.from(cexPrice),
                    BigNumber.from(dexPrice)
                );

                if (spread.gte(this.MIN_PROFIT_THRESHOLD)) {
                    opportunities.push({
                        sourceExchange: spread.isNegative() ? dexName : cexName,
                        targetExchange: spread.isNegative() ? cexName : dexName,
                        symbol,
                        spreadPercentage: spread.abs().toString(),
                        estimatedProfit: this.estimateProfit(
                            BigNumber.from(cexPrice),
                            BigNumber.from(dexPrice)
                        ).toString(),
                        timestamp: Date.now()
                    });
                }
            }
        }

        if (opportunities.length > 0) {
            priceData.arbitrageOpportunities = opportunities;
            this.emit('arbitrageOpportunity', opportunities);
        }
    }

    private calculateSpread(price1: BigNumber, price2: BigNumber): BigNumber {
        const diff = price1.sub(price2);
        const min = price1.lt(price2) ? price1 : price2;
        return diff.mul(100).div(min);
    }

    private estimateProfit(price1: BigNumber, price2: BigNumber): BigNumber {
        const diff = price1.sub(price2).abs();
        const amount = BigNumber.from('1000000000000000000'); // 1 ETH
        return diff.mul(amount).div(price1);
    }

    start(): void {
        if (this.updateInterval) return;

        this.cexFeed.start();
        this.dexScanner.start();

        this.updateInterval = setInterval(() => {
            this.emit('priceUpdate', Array.from(this.prices.values()));
        }, this.UPDATE_INTERVAL);

        logger.info('Price aggregator started');
    }

    stop(): void {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }

        this.cexFeed.stop();
        this.dexScanner.stop();
        logger.info('Price aggregator stopped');
    }

    getPrices(): AggregatedPrice[] {
        return Array.from(this.prices.values());
    }

    getArbitrageOpportunities(): ArbitrageOpportunity[] {
        const opportunities: ArbitrageOpportunity[] = [];
        for (const price of this.prices.values()) {
            opportunities.push(...price.arbitrageOpportunities);
        }
        return opportunities;
    }
}

export default PriceAggregator;
