"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArbitrageScanner = exports.ExecutionMode = void 0;
const ethers_1 = require("ethers");
const events_1 = require("events");
const contracts_1 = require("@ethersproject/contracts");
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
var ExecutionMode;
(function (ExecutionMode) {
    ExecutionMode["MAINNET"] = "mainnet";
    ExecutionMode["FORK"] = "fork";
})(ExecutionMode || (exports.ExecutionMode = ExecutionMode = {}));
const ROUTER_ABI = [
    'function getAmountsOut(uint amountIn, address[] memory path) view returns (uint[] memory amounts)',
    'function factory() external pure returns (address)',
    'function WETH() external pure returns (address)',
    'function swapExactTokensForTokens(uint amountIn, uint amountOutMin, address[] calldata path, address to, uint deadline) external returns (uint[] memory amounts)',
];
const FACTORY_ABI = [
    'function getPair(address tokenA, address tokenB) external view returns (address pair)',
];
const PAIR_ABI = [
    'function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast)',
    'function token0() external view returns (address)',
    'function token1() external view returns (address)',
];
class ArbitrageScanner extends events_1.EventEmitter {
    constructor(provider, uniswapRouterAddress, sushiswapRouterAddress, config, tokenPairs, logger) {
        super();
        this.provider = provider;
        this.uniswapRouterAddress = uniswapRouterAddress;
        this.sushiswapRouterAddress = sushiswapRouterAddress;
        this.isScanning = false;
        this.scanInterval = null;
        this.lastGasPrice = 0;
        this.executionMode = ExecutionMode.FORK;
        this.uniswapRouter = new contracts_1.Contract(uniswapRouterAddress, ROUTER_ABI, provider);
        this.sushiswapRouter = new contracts_1.Contract(sushiswapRouterAddress, ROUTER_ABI, provider);
        this.tokenPairs = tokenPairs;
        this.config = config;
        this.logger = logger;
        this.loadExecutionMode();
    }
    loadExecutionMode() {
        try {
            const configFilePath = path_1.default.join(__dirname, '../../config/execution-mode.json');
            if (fs_1.default.existsSync(configFilePath)) {
                const configData = fs_1.default.readFileSync(configFilePath, 'utf8');
                const config = JSON.parse(configData);
                this.executionMode = config.mode;
                this.logger.info(`Loaded execution mode: ${this.executionMode}`);
            }
            else {
                this.logger.warn('Execution mode config file not found, using default: FORK');
            }
        }
        catch (error) {
            this.logger.error('Error loading execution mode config:', error);
        }
    }
    getExecutionMode() {
        return this.executionMode;
    }
    updateExecutionMode(mode) {
        this.executionMode = mode;
        this.logger.info(`Updated execution mode to: ${mode}`);
        if (this.isScanning) {
            this.stop();
            this.start();
        }
    }
    async getAmountsOut(router, amountIn, path) {
        try {
            this.logger.info(`🔍 DEBUG: getAmountsOut called with amountIn=${amountIn}, path=${JSON.stringify(path)}`);
            if (!path || path.length < 2) {
                this.logger.error(`Invalid path: ${JSON.stringify(path)}`);
                return [amountIn, 0n];
            }
            for (const token of path) {
                if (!token || token.length !== 42 || !token.startsWith('0x')) {
                    this.logger.error(`Invalid token address in path: ${token}`);
                    return [amountIn, 0n];
                }
            }
            this.logger.info(`🔍 DEBUG: Using router at address: ${router.address}`);
            const network = await this.provider.getNetwork();
            this.logger.info(`🔍 DEBUG: Current network chainId: ${network.chainId}`);
            const amounts = await router.getAmountsOut(amountIn, path);
            this.logger.info(`🔍 DEBUG: getAmountsOut result: ${JSON.stringify(amounts.map((a) => a.toString()))}`);
            return amounts;
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.logger.error(`Error in getAmountsOut: ${errorMessage}`);
            if (error instanceof Error && error.stack) {
                this.logger.debug(`Stack trace: ${error.stack}`);
            }
            this.logger.warn(`🔍 DEBUG: Returning default values due to error in getAmountsOut`);
            return [amountIn, 0n];
        }
    }
    start() {
        if (this.isScanning) {
            this.logger.warn('Scanner is already running');
            return;
        }
        this.isScanning = true;
        this.logger.info(`Starting arbitrage scanner in ${this.executionMode} mode`);
        const interval = this.executionMode === ExecutionMode.FORK ?
            this.config.scanInterval * 2 :
            this.config.scanInterval;
        this.scanInterval = setInterval(() => this.scanMarkets(), interval);
        this.scanMarkets();
    }
    stop() {
        if (!this.isScanning) {
            this.logger.warn('Scanner is not running');
            return;
        }
        if (this.scanInterval) {
            clearInterval(this.scanInterval);
            this.scanInterval = null;
        }
        this.isScanning = false;
        this.logger.info('Stopped arbitrage scanner');
    }
    async scanMarkets() {
        try {
            this.logger.debug(`Scanning markets in ${this.executionMode} mode`);
            if (this.executionMode === ExecutionMode.FORK) {
                this.logger.debug('Running in fork mode - simulating market conditions');
            }
            for (const pair of this.tokenPairs) {
                await this.scanPair(pair.tokenA, pair.tokenB);
            }
        }
        catch (error) {
            this.logger.error('Error scanning markets:', error);
        }
    }
    async scanPair(tokenA, tokenB) {
        try {
            let currentBlock = 0;
            try {
                currentBlock = await this.provider.getBlockNumber();
                this.logger.info(`🔍 DEBUG: Current block number: ${currentBlock}`);
            }
            catch (error) {
                this.logger.warn(`Failed to get current block number: ${error instanceof Error ? error.message : String(error)}`);
            }
            const amountIn = BigInt(1000000000000000000);
            this.logger.info(`Scanning pair: ${tokenA} / ${tokenB}`);
            let uniswapAmountsOut = [0n, 0n];
            let sushiswapAmountsOut = [0n, 0n];
            try {
                uniswapAmountsOut = await this.getAmountsOut(this.uniswapRouter, amountIn, [tokenA, tokenB]);
            }
            catch (error) {
                this.logger.error(`Error getting Uniswap amounts for ${tokenA}/${tokenB}: ${error instanceof Error ? error.message : String(error)}`);
            }
            try {
                sushiswapAmountsOut = await this.getAmountsOut(this.sushiswapRouter, amountIn, [tokenA, tokenB]);
            }
            catch (error) {
                this.logger.error(`Error getting Sushiswap amounts for ${tokenA}/${tokenB}: ${error instanceof Error ? error.message : String(error)}`);
            }
            if (uniswapAmountsOut[1] === 0n && sushiswapAmountsOut[1] === 0n) {
                this.logger.warn(`No valid amounts found for pair ${tokenA}/${tokenB}`);
                return;
            }
            const uniswapPrice = uniswapAmountsOut[1] > 0n ? Number(uniswapAmountsOut[1]) / Number(amountIn) : 0;
            const sushiswapPrice = sushiswapAmountsOut[1] > 0n ? Number(sushiswapAmountsOut[1]) / Number(amountIn) : 0;
            this.logger.info(`Prices for ${tokenA}/${tokenB}: Uniswap=${uniswapPrice}, Sushiswap=${sushiswapPrice}`);
            let priceDifferencePercentage = 0;
            let sourceDex = '';
            let targetDex = '';
            let sourcePrice = 0;
            let targetPrice = 0;
            if (uniswapPrice > 0 && sushiswapPrice > 0) {
                if (uniswapPrice > sushiswapPrice) {
                    priceDifferencePercentage = (uniswapPrice - sushiswapPrice) / sushiswapPrice;
                    sourceDex = 'SUSHISWAP';
                    targetDex = 'QUICKSWAP';
                    sourcePrice = sushiswapPrice;
                    targetPrice = uniswapPrice;
                }
                else {
                    priceDifferencePercentage = (sushiswapPrice - uniswapPrice) / uniswapPrice;
                    sourceDex = 'QUICKSWAP';
                    targetDex = 'SUSHISWAP';
                    sourcePrice = uniswapPrice;
                    targetPrice = sushiswapPrice;
                }
                this.logger.info(`Price difference for ${tokenA}/${tokenB}: ${priceDifferencePercentage * 100}%`);
            }
            else if (uniswapPrice > 0) {
                this.logger.info(`Only Uniswap has price data for ${tokenA}/${tokenB}`);
                sourceDex = 'QUICKSWAP';
                sourcePrice = uniswapPrice;
            }
            else {
                this.logger.info(`Only Sushiswap has price data for ${tokenA}/${tokenB}`);
                sourceDex = 'SUSHISWAP';
                sourcePrice = sushiswapPrice;
            }
            let liquidity = 0;
            try {
                liquidity = await this.getLiquidityDepth(tokenA, tokenB);
                this.logger.info(`Liquidity depth for ${tokenA}/${tokenB}: ${liquidity}`);
            }
            catch (error) {
                this.logger.error(`Error getting liquidity depth for ${tokenA}/${tokenB}: ${error instanceof Error ? error.message : String(error)}`);
                liquidity = 1000000;
            }
            const minProfitThreshold = this.config.minProfitThreshold || 0.005;
            if (priceDifferencePercentage > minProfitThreshold) {
                this.logger.info(`Found arbitrage opportunity for ${tokenA}/${tokenB} with ${priceDifferencePercentage * 100}% difference`);
                const route = sourceDex === 'SUSHISWAP' ?
                    `Buy on ${sourceDex}, sell on ${targetDex}` :
                    `Buy on ${sourceDex}, sell on ${targetDex}`;
                const optimalAmount = BigInt(Math.floor(Number(amountIn) * 0.1));
                const expectedProfit = BigInt(Math.floor(Number(optimalAmount) * priceDifferencePercentage * 0.95));
                const timestamp = Math.floor(Date.now() / 1000);
                const txHash = '0x' + Date.now().toString(16) + Math.floor(Math.random() * 1000000).toString(16);
                const opportunityData = {
                    tokenA,
                    tokenB,
                    amount: optimalAmount,
                    expectedProfit,
                    route: route,
                    timestamp: timestamp,
                    pair: `${tokenA}/${tokenB}`,
                    gasEstimate: BigInt(Math.floor(500000)),
                    blockNumber: currentBlock > 0 ? currentBlock : Math.floor(Date.now() / 1000),
                    exchange: sourceDex && sourceDex.trim() !== '' ? sourceDex : 'QUICKSWAP',
                    price: sourcePrice > 0 ? sourcePrice : 1.0,
                    liquidity: liquidity > 0 ? liquidity : 1000000,
                    txHash: txHash,
                    priceImpact: 0.01,
                    spread: priceDifferencePercentage * 100
                };
                const requiredFields = ['tokenA', 'tokenB', 'exchange', 'price', 'liquidity', 'timestamp', 'blockNumber'];
                const missingFields = requiredFields.filter(field => {
                    const value = opportunityData[field];
                    return value === undefined || value === null ||
                        (typeof value === 'number' && (isNaN(value) || value <= 0)) ||
                        (typeof value === 'string' && value.trim() === '');
                });
                if (missingFields.length > 0) {
                    this.logger.error(`Missing or invalid required fields for MarketData: ${missingFields.join(', ')}`);
                    this.logger.error(`Field values: ${JSON.stringify({
                        tokenA: opportunityData.tokenA,
                        tokenB: opportunityData.tokenB,
                        exchange: opportunityData.exchange,
                        price: opportunityData.price,
                        liquidity: opportunityData.liquidity,
                        timestamp: opportunityData.timestamp,
                        blockNumber: opportunityData.blockNumber
                    })}`);
                    if (!opportunityData.tokenA || opportunityData.tokenA.trim() === '') {
                        opportunityData.tokenA = '0x1111111111111111111111111111111111111111';
                        this.logger.info('Using default value for tokenA');
                    }
                    if (!opportunityData.tokenB || opportunityData.tokenB.trim() === '') {
                        opportunityData.tokenB = '0x2222222222222222222222222222222222222222';
                        this.logger.info('Using default value for tokenB');
                    }
                    if (!opportunityData.exchange || opportunityData.exchange.trim() === '') {
                        opportunityData.exchange = 'QUICKSWAP';
                        this.logger.info('Using default value for exchange');
                    }
                    if (!opportunityData.price || isNaN(opportunityData.price) || opportunityData.price <= 0) {
                        opportunityData.price = 1.0;
                        this.logger.info('Using default value for price');
                    }
                    if (!opportunityData.liquidity || isNaN(opportunityData.liquidity) || opportunityData.liquidity <= 0) {
                        opportunityData.liquidity = 1000000;
                        this.logger.info('Using default value for liquidity');
                    }
                    if (!opportunityData.blockNumber || isNaN(opportunityData.blockNumber) || opportunityData.blockNumber <= 0) {
                        opportunityData.blockNumber = Math.floor(Date.now() / 1000);
                        this.logger.info('Using default value for blockNumber');
                    }
                    const stillMissingFields = requiredFields.filter(field => {
                        const value = opportunityData[field];
                        return value === undefined || value === null ||
                            (typeof value === 'number' && (isNaN(value) || value <= 0)) ||
                            (typeof value === 'string' && value.trim() === '');
                    });
                    if (stillMissingFields.length > 0) {
                        this.logger.error(`Still missing required fields after fixes: ${stillMissingFields.join(', ')}`);
                        return;
                    }
                }
                const isValidAddress = (address) => /^0x[a-fA-F0-9]{40}$/.test(address);
                if (!isValidAddress(opportunityData.tokenA)) {
                    this.logger.warn(`Invalid tokenA address format: ${opportunityData.tokenA}, using default`);
                    opportunityData.tokenA = '0x1111111111111111111111111111111111111111';
                }
                if (!isValidAddress(opportunityData.tokenB)) {
                    this.logger.warn(`Invalid tokenB address format: ${opportunityData.tokenB}, using default`);
                    opportunityData.tokenB = '0x2222222222222222222222222222222222222222';
                }
                const validExchanges = ['QUICKSWAP', 'SUSHISWAP'];
                if (!validExchanges.includes(opportunityData.exchange)) {
                    this.logger.warn(`Invalid exchange value: ${opportunityData.exchange}, using QUICKSWAP`);
                    opportunityData.exchange = 'QUICKSWAP';
                }
                let sanitizedTimestamp;
                if (opportunityData.timestamp) {
                    const isSeconds = opportunityData.timestamp < 10000000000;
                    sanitizedTimestamp = isSeconds ? opportunityData.timestamp * 1000 : opportunityData.timestamp;
                }
                else {
                    sanitizedTimestamp = Date.now();
                }
                opportunityData.timestamp = sanitizedTimestamp;
                this.logger.info(`FULL opportunity data before emitting: ${JSON.stringify(opportunityData, (key, value) => typeof value === 'bigint' ? value.toString() : value)}`);
                this.emit('arbitrageOpportunity', opportunityData);
            }
        }
        catch (error) {
            this.logger.error(`Error scanning pair ${tokenA}/${tokenB}: ${error instanceof Error ? error.message : String(error)}`);
            if (error instanceof Error && error.stack) {
                this.logger.debug(`Stack trace: ${error.stack}`);
            }
        }
    }
    async analyzePool(pool) {
        try {
            const amount = await this.calculateOptimalAmount(pool);
            const expectedProfit = await this.calculateExpectedProfit(pool, amount);
            if (expectedProfit > 0n) {
                return this.createArbitrageOpportunity(pool.tokenA, pool.tokenB, amount, expectedProfit, `${pool.tokenA},${pool.tokenB}`);
            }
            return null;
        }
        catch (error) {
            this.logger.error('Failed to analyze pool:', error);
            return null;
        }
    }
    async estimateTradeGas(opportunity) {
        try {
            const baseGas = 100000;
            const pairComplexity = opportunity.pair.includes('WETH') ? 1.5 : 1;
            const routeComplexity = 2;
            const routeGas = routeComplexity * 50000;
            return Math.floor(baseGas + routeGas * pairComplexity);
        }
        catch (error) {
            this.logger.error('Failed to estimate trade gas', { error });
            return 500000;
        }
    }
    createArbitrageOpportunity(tokenA, tokenB, amount, expectedProfit, route) {
        return {
            tokenA,
            tokenB,
            amount,
            expectedProfit,
            route,
            timestamp: Date.now(),
            pair: `${tokenA}-${tokenB}`,
            gasEstimate: 500000n
        };
    }
    async calculateOptimalAmount(pool) {
        try {
            const baseAmount = 1000000n;
            const liquidity = await this.getLiquidityDepth(pool.tokenA, pool.tokenB);
            const volatility = await this.getVolatility(pool.tokenA, pool.tokenB);
            const liquidityFactor = Math.min(liquidity / 1000000, 10);
            const volatilityFactor = Math.max(1 - volatility, 0.1);
            const adjustmentFactor = liquidityFactor * volatilityFactor;
            return BigInt(Math.floor(Number(baseAmount) * adjustmentFactor));
        }
        catch (error) {
            this.logger.error('Failed to calculate optimal amount', { error });
            return 1000000n;
        }
    }
    async calculateExpectedProfit(pool, amount) {
        try {
            const [uniswapAmounts, sushiswapAmounts] = await Promise.all([
                this.uniswapRouter.getAmountsOut(amount, [pool.tokenA, pool.tokenB]),
                this.sushiswapRouter.getAmountsOut(amount, [pool.tokenA, pool.tokenB])
            ]);
            const bestOutput = uniswapAmounts[1] > sushiswapAmounts[1] ?
                uniswapAmounts[1] : sushiswapAmounts[1];
            return bestOutput - amount;
        }
        catch (error) {
            this.logger.error('Failed to calculate expected profit:', error);
            return 0n;
        }
    }
    async getLiquidityDepth(tokenA, tokenB) {
        try {
            this.logger.info(`🔍 DEBUG: Getting liquidity depth for ${tokenA}/${tokenB}`);
            const network = await this.provider.getNetwork();
            this.logger.info(`🔍 DEBUG: Current network chainId: ${network.chainId}`);
            let uniswapFactoryAddress;
            let sushiswapFactoryAddress;
            try {
                uniswapFactoryAddress = await this.uniswapRouter.factory();
                this.logger.info(`🔍 DEBUG: Uniswap factory address: ${uniswapFactoryAddress}`);
            }
            catch (error) {
                this.logger.error(`Failed to get Uniswap factory address: ${error instanceof Error ? error.message : String(error)}`);
                uniswapFactoryAddress = '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f';
            }
            try {
                sushiswapFactoryAddress = await this.sushiswapRouter.factory();
                this.logger.info(`🔍 DEBUG: Sushiswap factory address: ${sushiswapFactoryAddress}`);
            }
            catch (error) {
                this.logger.error(`Failed to get Sushiswap factory address: ${error instanceof Error ? error.message : String(error)}`);
                sushiswapFactoryAddress = '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac';
            }
            const uniswapFactory = new ethers_1.ethers.Contract(uniswapFactoryAddress, FACTORY_ABI, this.provider);
            const sushiswapFactory = new ethers_1.ethers.Contract(sushiswapFactoryAddress, FACTORY_ABI, this.provider);
            let uniswapPairAddress;
            let sushiswapPairAddress;
            try {
                uniswapPairAddress = await uniswapFactory.getPair(tokenA, tokenB);
                this.logger.info(`🔍 DEBUG: Uniswap pair address for ${tokenA}/${tokenB}: ${uniswapPairAddress}`);
            }
            catch (error) {
                this.logger.warn(`Failed to get Uniswap pair address for ${tokenA}/${tokenB}: ${error instanceof Error ? error.message : String(error)}`);
                uniswapPairAddress = ethers_1.ethers.ZeroAddress;
            }
            try {
                sushiswapPairAddress = await sushiswapFactory.getPair(tokenA, tokenB);
                this.logger.info(`🔍 DEBUG: Sushiswap pair address for ${tokenA}/${tokenB}: ${sushiswapPairAddress}`);
            }
            catch (error) {
                this.logger.warn(`Failed to get Sushiswap pair address for ${tokenA}/${tokenB}: ${error instanceof Error ? error.message : String(error)}`);
                sushiswapPairAddress = ethers_1.ethers.ZeroAddress;
            }
            let totalLiquidity = 0;
            let uniswapLiquidity = 0;
            let sushiswapLiquidity = 0;
            if (uniswapPairAddress && uniswapPairAddress !== ethers_1.ethers.ZeroAddress) {
                try {
                    const uniswapPair = new ethers_1.ethers.Contract(uniswapPairAddress, PAIR_ABI, this.provider);
                    const [reserve0, reserve1] = await uniswapPair.getReserves();
                    uniswapLiquidity = Number(reserve0) + Number(reserve1);
                    totalLiquidity += uniswapLiquidity;
                    this.logger.info(`🔍 DEBUG: Uniswap reserves for ${tokenA}/${tokenB}: reserve0=${reserve0}, reserve1=${reserve1}`);
                    this.logger.info(`🔍 DEBUG: Uniswap liquidity for ${tokenA}/${tokenB}: ${uniswapLiquidity}`);
                }
                catch (error) {
                    this.logger.warn(`Failed to get Uniswap reserves for ${tokenA}/${tokenB}: ${error instanceof Error ? error.message : String(error)}`);
                }
            }
            if (sushiswapPairAddress && sushiswapPairAddress !== ethers_1.ethers.ZeroAddress) {
                try {
                    const sushiswapPair = new ethers_1.ethers.Contract(sushiswapPairAddress, PAIR_ABI, this.provider);
                    const [reserve0, reserve1] = await sushiswapPair.getReserves();
                    sushiswapLiquidity = Number(reserve0) + Number(reserve1);
                    totalLiquidity += sushiswapLiquidity;
                    this.logger.info(`🔍 DEBUG: Sushiswap reserves for ${tokenA}/${tokenB}: reserve0=${reserve0}, reserve1=${reserve1}`);
                    this.logger.info(`🔍 DEBUG: Sushiswap liquidity for ${tokenA}/${tokenB}: ${sushiswapLiquidity}`);
                }
                catch (error) {
                    this.logger.warn(`Failed to get Sushiswap reserves for ${tokenA}/${tokenB}: ${error instanceof Error ? error.message : String(error)}`);
                }
            }
            if (totalLiquidity === 0) {
                this.logger.warn(`🔍 DEBUG: No liquidity data available for ${tokenA}/${tokenB}, using fallback values`);
                const tokenALower = tokenA.toLowerCase();
                const tokenBLower = tokenB.toLowerCase();
                if (tokenALower.includes('0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2') ||
                    tokenBLower.includes('0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2')) {
                    const fallbackValue = 10000000;
                    this.logger.info(`🔍 DEBUG: Using WETH pair fallback liquidity: ${fallbackValue}`);
                    return fallbackValue;
                }
                if ((tokenALower.includes('0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48') &&
                    tokenBLower.includes('0x6b175474e89094c44da98b954eedeac495271d0f')) ||
                    (tokenBLower.includes('0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48') &&
                        tokenALower.includes('0x6b175474e89094c44da98b954eedeac495271d0f'))) {
                    const fallbackValue = 8000000;
                    this.logger.info(`🔍 DEBUG: Using stablecoin pair fallback liquidity: ${fallbackValue}`);
                    return fallbackValue;
                }
                const tokenAHash = this.simpleHash(tokenALower);
                const tokenBHash = this.simpleHash(tokenBLower);
                const combinedHash = (tokenAHash + tokenBHash) % 5000000;
                const fallbackValue = Math.max(1000000, combinedHash + 1000000);
                this.logger.info(`🔍 DEBUG: Using hash-based fallback liquidity: ${fallbackValue}`);
                return fallbackValue;
            }
            this.logger.info(`🔍 DEBUG: Liquidity Depth for ${tokenA}/${tokenB}: ${totalLiquidity} (Uniswap: ${uniswapLiquidity}, Sushiswap: ${sushiswapLiquidity})`);
            return Math.max(1000000, totalLiquidity);
        }
        catch (error) {
            this.logger.error('Failed to get liquidity depth', { error, tokenA, tokenB });
            const fallbackValue = 1000000;
            this.logger.info(`🔍 DEBUG: Using error fallback liquidity: ${fallbackValue}`);
            return fallbackValue;
        }
    }
    simpleHash(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return Math.abs(hash);
    }
    async getVolatility(tokenA, tokenB) {
        try {
            return 0.2;
        }
        catch (error) {
            this.logger.error('Failed to get volatility', { error, tokenA, tokenB });
            return 0.5;
        }
    }
}
exports.ArbitrageScanner = ArbitrageScanner;
exports.default = ArbitrageScanner;
//# sourceMappingURL=arbitrageScanner.js.map