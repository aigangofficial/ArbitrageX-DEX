import { Contract, JsonRpcProvider } from 'ethers';
import { Logger } from 'winston';
import { getConfig } from '../api/config';

interface LiquidityPool {
    address: string;
    chainId: number;
    token0: string;
    token1: string;
    reserve0: bigint;
    reserve1: bigint;
    fee: number;
    lastPrice: bigint;
    tokenA: string;
    tokenB: string;
    lastUpdate: number;
}

interface LiquiditySnapshot {
    chainId: number;
    dex: string;
    pool: string;
    liquidity: bigint;
    priceUSD: number;
    timestamp: number;
}

export class LiquidityMonitor {
    private config = getConfig();
    private logger: Logger;
    private providers: Map<number, JsonRpcProvider> = new Map();
    private pools: Map<string, LiquidityPool> = new Map();
    private snapshots: LiquiditySnapshot[] = [];
    private updateInterval: NodeJS.Timeout | null = null;

    constructor(logger: Logger) {
        this.logger = logger;
        this.initializeProviders();
    }

    async start() {
        await this.discoverPools();
        this.updateInterval = setInterval(() => this.updateLiquidity(), 15000);
    }

    stop() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    private initializeProviders() {
        Object.entries(this.config.chains).forEach(([chainId, chain]) => {
            const provider = new JsonRpcProvider(chain.rpcUrl);
            this.providers.set(Number(chainId), provider);
        });
    }

    private async discoverPools() {
        for (const [chainId, provider] of this.providers) {
            try {
                await this.findLiquidityPools(chainId, provider);
            } catch (error) {
                this.logger.error(`Error discovering pools on chain ${chainId}:`, error);
            }
        }
    }

    private async findLiquidityPools(chainId: number, provider: JsonRpcProvider) {
        // Implement pool discovery logic for each supported DEX
        // This would query factory contracts to get pool addresses
    }

    private async updateLiquidity() {
        const updates: Promise<void>[] = [];

        for (const [poolKey, pool] of this.pools) {
            updates.push(this.updatePoolLiquidity(poolKey, pool));
        }

        await Promise.allSettled(updates);
        this.analyzeSnapshots();
    }

    private async updatePoolLiquidity(poolKey: string, pool: LiquidityPool) {
        try {
            const [chainId, dex] = poolKey.split('-');
            const provider = this.providers.get(Number(chainId));
            if (!provider) return;

            const poolContract = new Contract(
                pool.address,
                [
                    'function getReserves() view returns (uint112, uint112, uint32)',
                    'function token0() view returns (address)',
                    'function token1() view returns (address)',
                    'function fee() view returns (uint24)'
                ],
                provider
            );

            const [reserve0, reserve1] = await poolContract.getReserves();
            const fee = await poolContract.fee();
            const token0 = await poolContract.token0();
            const token1 = await poolContract.token1();
            
            // Update pool data
            pool.reserve0 = reserve0;
            pool.reserve1 = reserve1;
            pool.fee = Number(fee) / 10000; // Convert from basis points
            pool.token0 = token0;
            pool.token1 = token1;
            pool.tokenA = token0;
            pool.tokenB = token1;
            pool.chainId = Number(chainId);
            pool.lastUpdate = Date.now();
            pool.lastPrice = await this.getTokenPrice(token0, Number(chainId));

            const snapshot: LiquiditySnapshot = {
                chainId: Number(chainId),
                dex,
                pool: pool.address,
                liquidity: this.calculateTotalLiquidity(reserve0, reserve1),
                priceUSD: await this.getPoolPriceUSD(pool, reserve0, reserve1),
                timestamp: Date.now()
            };

            this.snapshots.push(snapshot);
            this.trimSnapshots();

        } catch (error) {
            this.logger.error(`Error updating pool ${poolKey}:`, error);
        }
    }

    private calculateTotalLiquidity(reserve0: bigint, reserve1: bigint): bigint {
        // Implement liquidity calculation based on reserves and token prices
        return reserve0 + reserve1; // Simplified version
    }

    private async getPoolPriceUSD(
        pool: LiquidityPool,
        reserve0: bigint,
        reserve1: bigint
    ): Promise<number> {
        // Implement price calculation using oracle data
        return 0;
    }

    private async getTokenPrice(token: string, chainId: number): Promise<bigint> {
        // Implement price fetching logic
        return 0n; // Placeholder
    }

    private trimSnapshots() {
        const oneHourAgo = Date.now() - 3600000;
        this.snapshots = this.snapshots.filter(s => s.timestamp > oneHourAgo);
    }

    private analyzeSnapshots() {
        // Analyze liquidity trends and detect anomalies
        for (const [poolKey, pool] of this.pools) {
            const poolSnapshots = this.snapshots.filter(
                s => s.pool === pool.address
            ).sort((a, b) => b.timestamp - a.timestamp);

            if (poolSnapshots.length < 2) continue;

            const latestSnapshot = poolSnapshots[0];
            const previousSnapshot = poolSnapshots[1];

            const liquidityChange = Number(latestSnapshot.liquidity - previousSnapshot.liquidity) / 
                                 Number(previousSnapshot.liquidity);

            if (Math.abs(liquidityChange) > 0.1) { // 10% threshold
                this.logger.warn(`Significant liquidity change in pool ${poolKey}: ${liquidityChange * 100}%`);
            }
        }
    }

    getLiquidityDepth(chainId: number, token: string): bigint {
        let totalLiquidity = 0n;
        
        for (const [_, pool] of this.pools) {
            if (pool.token0 === token || pool.token1 === token) {
                totalLiquidity += pool.token0 === token ? pool.reserve0 : pool.reserve1;
            }
        }

        return totalLiquidity;
    }

    async isLiquidityAdequate(
        chainId: number,
        token: string,
        amount: bigint
    ): Promise<boolean> {
        const liquidity = this.getLiquidityDepth(chainId, token);
        const threshold = amount * 10n; // Require 10x liquidity for safety
        return liquidity >= threshold;
    }

    getTrackedPools(): LiquidityPool[] {
        return Array.from(this.pools.values());
    }
} 