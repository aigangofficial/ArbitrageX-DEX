"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const dotenv_1 = __importDefault(require("dotenv"));
const ethers_1 = require("ethers");
const ioredis_1 = __importDefault(require("ioredis"));
const mongodb_1 = require("mongodb");
const logger_1 = require("../api/utils/logger");
dotenv_1.default.config();
const DEX_ROUTER_ABI = [
    'function getAmountsOut(uint amountIn, address[] memory path) view returns (uint[] memory amounts)',
    'function factory() external pure returns (address)',
    'function WETH() external pure returns (address)',
];
const FACTORY_ABI = [
    {
        constant: true,
        inputs: [],
        name: 'allPairsLength',
        outputs: [{ name: '', type: 'uint256' }],
        payable: false,
        stateMutability: 'view',
        type: 'function',
    },
    {
        constant: true,
        inputs: [
            { name: 'tokenA', type: 'address' },
            { name: 'tokenB', type: 'address' },
        ],
        name: 'getPair',
        outputs: [{ name: 'pair', type: 'address' }],
        payable: false,
        stateMutability: 'view',
        type: 'function',
    },
];
const PAIR_ABI = [
    {
        constant: true,
        inputs: [],
        name: 'getReserves',
        outputs: [
            { name: '_reserve0', type: 'uint112' },
            { name: '_reserve1', type: 'uint112' },
            { name: '_blockTimestampLast', type: 'uint32' },
        ],
        payable: false,
        stateMutability: 'view',
        type: 'function',
    },
    {
        constant: true,
        inputs: [],
        name: 'token0',
        outputs: [{ name: '', type: 'address' }],
        payable: false,
        stateMutability: 'view',
        type: 'function',
    },
    {
        constant: true,
        inputs: [],
        name: 'token1',
        outputs: [{ name: '', type: 'address' }],
        payable: false,
        stateMutability: 'view',
        type: 'function',
    },
];
const QUICKSWAP_FACTORY = '0x2b0c70a1b0a37bb3ec6cb7748b4572e990c2a37d';
const SUSHISWAP_FACTORY = '0xc35DADB65012eC5796536bD9864eD8773aBc74C4';
class RealPriceFeed {
    constructor() {
        this.mongodb = new mongodb_1.MongoClient('mongodb://admin:password123@mongodb:27017/arbitragex?authSource=admin');
        this.redis = new ioredis_1.default(process.env.REDIS_URI || 'redis://redis:6379');
        this.updateInterval = parseInt(process.env.UPDATE_INTERVAL || '5000');
        this.provider = new ethers_1.ethers.JsonRpcProvider(process.env.NETWORK_RPC);
        this.dexRouters = {
            quickswap: new ethers_1.ethers.Contract(process.env.AMOY_QUICKSWAP_ROUTER, DEX_ROUTER_ABI, this.provider),
            sushiswap: new ethers_1.ethers.Contract(process.env.AMOY_SUSHISWAP_ROUTER, DEX_ROUTER_ABI, this.provider),
        };
        this.tokenPairs = [
            {
                tokenA: process.env.AMOY_WETH,
                tokenB: process.env.AMOY_USDC,
            },
            {
                tokenA: process.env.AMOY_WETH,
                tokenB: process.env.AMOY_USDT,
            },
            {
                tokenA: process.env.AMOY_USDC,
                tokenB: process.env.AMOY_USDT,
            },
        ];
    }
    async validatePair(tokenA, tokenB, exchange) {
        try {
            const factoryAddress = exchange === 'quickswap' ? QUICKSWAP_FACTORY : SUSHISWAP_FACTORY;
            const factory = new ethers_1.ethers.Contract(factoryAddress, FACTORY_ABI, this.provider);
            const pairAddress = await factory.getPair(tokenA, tokenB);
            if (pairAddress === ethers_1.ethers.ZeroAddress) {
                logger_1.logger.warn(`No liquidity pair exists for ${tokenA}/${tokenB} on ${exchange}`);
                return false;
            }
            const pair = new ethers_1.ethers.Contract(pairAddress, PAIR_ABI, this.provider);
            const [reserve0, reserve1] = await pair.getReserves();
            if (reserve0 === 0n || reserve1 === 0n) {
                logger_1.logger.warn(`No liquidity for ${tokenA}/${tokenB} on ${exchange}`);
                return false;
            }
            return true;
        }
        catch (error) {
            logger_1.logger.error(`Error validating pair ${tokenA}/${tokenB} on ${exchange}:`, error);
            return false;
        }
    }
    async fetchPrice(tokenA, tokenB, exchange) {
        try {
            const factoryAddress = exchange === 'quickswap' ? QUICKSWAP_FACTORY : SUSHISWAP_FACTORY;
            const factory = new ethers_1.ethers.Contract(factoryAddress, FACTORY_ABI, this.provider);
            const pairAddress = await factory.getPair(tokenA, tokenB);
            const pair = new ethers_1.ethers.Contract(pairAddress, PAIR_ABI, this.provider);
            const [reserve0, reserve1] = await pair.getReserves();
            const token0 = await pair.token0();
            const [reserveA, reserveB] = token0.toLowerCase() === tokenA.toLowerCase() ? [reserve0, reserve1] : [reserve1, reserve0];
            const router = this.dexRouters[exchange];
            const path = [tokenA, tokenB];
            const amounts = await router.getAmountsOut(ethers_1.ethers.parseEther('1'), path);
            const price = Number(ethers_1.ethers.formatEther(amounts[1]));
            const liquidity = Number(ethers_1.ethers.formatEther(reserveA));
            const blockNumber = await this.provider.getBlockNumber();
            return {
                tokenA,
                tokenB,
                exchange,
                price,
                liquidity,
                timestamp: new Date(),
                blockNumber,
            };
        }
        catch (error) {
            logger_1.logger.error(`Error fetching price for ${tokenA}/${tokenB} on ${exchange}:`, error);
            return null;
        }
    }
    async updatePrices() {
        try {
            const blockNumber = await this.provider.getBlockNumber();
            for (const { tokenA, tokenB } of this.tokenPairs) {
                if (await this.validatePair(tokenA, tokenB, 'quickswap')) {
                    const quickswapPrice = await this.fetchPrice(tokenA, tokenB, 'quickswap');
                    if (quickswapPrice) {
                        await this.mongodb.db('arbitragex').collection('prices').insertOne(quickswapPrice);
                        await this.redis.set(`price:${tokenA}:${tokenB}:quickswap`, JSON.stringify(quickswapPrice));
                    }
                }
                if (await this.validatePair(tokenA, tokenB, 'sushiswap')) {
                    const sushiswapPrice = await this.fetchPrice(tokenA, tokenB, 'sushiswap');
                    if (sushiswapPrice) {
                        await this.mongodb.db('arbitragex').collection('prices').insertOne(sushiswapPrice);
                        await this.redis.set(`price:${tokenA}:${tokenB}:sushiswap`, JSON.stringify(sushiswapPrice));
                    }
                }
            }
        }
        catch (error) {
            logger_1.logger.error('Error updating prices:', error);
        }
    }
    async start() {
        try {
            await this.mongodb.connect();
            logger_1.logger.info('Connected to MongoDB');
            setInterval(() => this.updatePrices(), this.updateInterval);
            logger_1.logger.info('Price feed started');
            await this.updatePrices();
        }
        catch (error) {
            logger_1.logger.error('Error starting price feed:', error);
            throw error;
        }
    }
    async stop() {
        try {
            clearInterval(this.updateInterval);
            await this.mongodb.close();
            logger_1.logger.info('Price feed stopped');
        }
        catch (error) {
            logger_1.logger.error('Error stopping price feed:', error);
            throw error;
        }
    }
}
exports.default = RealPriceFeed;
//# sourceMappingURL=index.js.map