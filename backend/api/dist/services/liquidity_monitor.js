"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LiquidityMonitor = void 0;
const ethers_1 = require("ethers");
const config_1 = require("../api/config");
class LiquidityMonitor {
    constructor(logger) {
        this.config = (0, config_1.getConfig)();
        this.providers = new Map();
        this.pools = new Map();
        this.snapshots = [];
        this.updateInterval = null;
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
    initializeProviders() {
        Object.entries(this.config.chains).forEach(([chainId, chain]) => {
            const provider = new ethers_1.JsonRpcProvider(chain.rpcUrl);
            this.providers.set(Number(chainId), provider);
        });
    }
    async discoverPools() {
        for (const [chainId, provider] of this.providers) {
            try {
                await this.findLiquidityPools(chainId, provider);
            }
            catch (error) {
                this.logger.error(`Error discovering pools on chain ${chainId}:`, error);
            }
        }
    }
    async findLiquidityPools(chainId, provider) {
    }
    async updateLiquidity() {
        const updates = [];
        for (const [poolKey, pool] of this.pools) {
            updates.push(this.updatePoolLiquidity(poolKey, pool));
        }
        await Promise.allSettled(updates);
        this.analyzeSnapshots();
    }
    async updatePoolLiquidity(poolKey, pool) {
        try {
            const [chainId, dex] = poolKey.split('-');
            const provider = this.providers.get(Number(chainId));
            if (!provider)
                return;
            const poolContract = new ethers_1.Contract(pool.address, [
                'function getReserves() view returns (uint112, uint112, uint32)',
                'function token0() view returns (address)',
                'function token1() view returns (address)',
                'function fee() view returns (uint24)'
            ], provider);
            const [reserve0, reserve1] = await poolContract.getReserves();
            const fee = await poolContract.fee();
            const token0 = await poolContract.token0();
            const token1 = await poolContract.token1();
            pool.reserve0 = reserve0;
            pool.reserve1 = reserve1;
            pool.fee = Number(fee) / 10000;
            pool.token0 = token0;
            pool.token1 = token1;
            pool.tokenA = token0;
            pool.tokenB = token1;
            pool.chainId = Number(chainId);
            pool.lastUpdate = Date.now();
            pool.lastPrice = await this.getTokenPrice(token0, Number(chainId));
            const snapshot = {
                chainId: Number(chainId),
                dex,
                pool: pool.address,
                liquidity: this.calculateTotalLiquidity(reserve0, reserve1),
                priceUSD: await this.getPoolPriceUSD(pool, reserve0, reserve1),
                timestamp: Date.now()
            };
            this.snapshots.push(snapshot);
            this.trimSnapshots();
        }
        catch (error) {
            this.logger.error(`Error updating pool ${poolKey}:`, error);
        }
    }
    calculateTotalLiquidity(reserve0, reserve1) {
        return reserve0 + reserve1;
    }
    async getPoolPriceUSD(pool, reserve0, reserve1) {
        return 0;
    }
    async getTokenPrice(token, chainId) {
        return 0n;
    }
    trimSnapshots() {
        const oneHourAgo = Date.now() - 3600000;
        this.snapshots = this.snapshots.filter(s => s.timestamp > oneHourAgo);
    }
    analyzeSnapshots() {
        for (const [poolKey, pool] of this.pools) {
            const poolSnapshots = this.snapshots.filter(s => s.pool === pool.address).sort((a, b) => b.timestamp - a.timestamp);
            if (poolSnapshots.length < 2)
                continue;
            const latestSnapshot = poolSnapshots[0];
            const previousSnapshot = poolSnapshots[1];
            const liquidityChange = Number(latestSnapshot.liquidity - previousSnapshot.liquidity) /
                Number(previousSnapshot.liquidity);
            if (Math.abs(liquidityChange) > 0.1) {
                this.logger.warn(`Significant liquidity change in pool ${poolKey}: ${liquidityChange * 100}%`);
            }
        }
    }
    getLiquidityDepth(chainId, token) {
        let totalLiquidity = 0n;
        for (const [_, pool] of this.pools) {
            if (pool.token0 === token || pool.token1 === token) {
                totalLiquidity += pool.token0 === token ? pool.reserve0 : pool.reserve1;
            }
        }
        return totalLiquidity;
    }
    async isLiquidityAdequate(chainId, token, amount) {
        const liquidity = this.getLiquidityDepth(chainId, token);
        const threshold = amount * 10n;
        return liquidity >= threshold;
    }
    getTrackedPools() {
        return Array.from(this.pools.values());
    }
}
exports.LiquidityMonitor = LiquidityMonitor;
//# sourceMappingURL=liquidity_monitor.js.map