import dotenv from 'dotenv';
import { ethers } from 'ethers';
import Redis from 'ioredis';
import { MongoClient } from 'mongodb';
import path from 'path';
import winston from 'winston';
import { IDEXRouter } from '../execution/interfaces/IDEXRouter';

// Configure logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(winston.format.timestamp(), winston.format.json()),
  transports: [
    new winston.transports.File({ filename: 'logs/price-feed.log' }),
    new winston.transports.Console(),
  ],
});

// Load environment variables
dotenv.config({ path: path.resolve(__dirname, '../../.env.root') });

// Validate environment variables
const requiredEnvVars = [
  'NETWORK_RPC',
  'AMOY_QUICKSWAP_ROUTER',
  'AMOY_SUSHISWAP_ROUTER',
  'AMOY_WMATIC',
  'AMOY_USDC',
];

requiredEnvVars.forEach(envVar => {
  if (!process.env[envVar]) {
    throw new Error(`Missing required environment variable: ${envVar}`);
  }
});

// Router ABI for DEX interactions
const DEX_ROUTER_ABI = [
  'function getAmountsOut(uint amountIn, address[] memory path) view returns (uint[] memory amounts)',
  'function factory() external pure returns (address)',
  'function WETH() external pure returns (address)',
];

// Factory ABI for getting pair info
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

// Pair ABI for getting reserves
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

// Hardcoded factory addresses for Polygon Amoy testnet
const QUICKSWAP_FACTORY = '0x2b0c70a1b0a37bb3ec6cb7748b4572e990c2a37d';
const SUSHISWAP_FACTORY = '0xc35DADB65012eC5796536bD9864eD8773aBc74C4';

interface PriceData {
  tokenA: string;
  tokenB: string;
  exchange: string;
  price: number;
  liquidity: number;
  timestamp: Date;
  blockNumber: number;
}

class RealPriceFeed {
  private mongodb: MongoClient;
  private redis: Redis;
  private provider: ethers.JsonRpcProvider;
  private updateInterval: number;
  private dexRouters: { [key: string]: IDEXRouter };
  private tokenPairs: Array<{ tokenA: string; tokenB: string }>;

  constructor() {
    this.mongodb = new MongoClient(
      'mongodb://admin:password123@mongodb:27017/arbitragex?authSource=admin'
    );
    this.redis = new Redis(process.env.REDIS_URI || 'redis://redis:6379');
    this.updateInterval = parseInt(process.env.UPDATE_INTERVAL || '5000');

    // Initialize provider
    this.provider = new ethers.JsonRpcProvider(process.env.NETWORK_RPC);

    // Initialize DEX routers
    this.dexRouters = {
      quickswap: new ethers.Contract(
        process.env.AMOY_QUICKSWAP_ROUTER!,
        DEX_ROUTER_ABI,
        this.provider
      ) as unknown as IDEXRouter,
      sushiswap: new ethers.Contract(
        process.env.AMOY_SUSHISWAP_ROUTER!,
        DEX_ROUTER_ABI,
        this.provider
      ) as unknown as IDEXRouter,
    };

    // Initialize token pairs to monitor
    this.tokenPairs = [
      {
        tokenA: process.env.AMOY_WMATIC || '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',
        tokenB: process.env.AMOY_USDC || '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
      },
    ];

    logger.info(`Initialized token pairs: ${JSON.stringify(this.tokenPairs)}`);
  }

  private async validatePair(tokenA: string, tokenB: string, exchange: string): Promise<boolean> {
    try {
      // Get factory address based on exchange
      const factoryAddress = exchange === 'quickswap' ? QUICKSWAP_FACTORY : SUSHISWAP_FACTORY;
      logger.info(
        `Validating pair ${tokenA}-${tokenB} on ${exchange} (factory: ${factoryAddress})`
      );

      // Create factory contract instance
      const factory = new ethers.Contract(factoryAddress, FACTORY_ABI, this.provider);

      // First verify the factory contract is accessible
      try {
        const factoryCode = await this.provider.getCode(factoryAddress);
        if (factoryCode === '0x' || factoryCode === '0x0') {
          logger.error(`No contract code found at factory address ${factoryAddress}`);
          return false;
        }
      } catch (error) {
        logger.error(`Error verifying factory contract at ${factoryAddress}:`, error);
        return false;
      }

      // Get pair address
      let pairAddress;
      try {
        pairAddress = await factory.getPair(tokenA, tokenB);
        logger.info(`Pair address for ${tokenA}-${tokenB} on ${exchange}: ${pairAddress}`);
      } catch (error) {
        logger.error(`Error getting pair address from factory:`, error);
        return false;
      }

      // Check if pair exists
      if (pairAddress === ethers.ZeroAddress) {
        logger.warn(`No pair exists for ${tokenA}-${tokenB} on ${exchange}`);
        return false;
      }

      // Verify the pair contract
      try {
        const pair = new ethers.Contract(pairAddress, PAIR_ABI, this.provider);
        const [reserve0, reserve1] = await pair.getReserves();

        // Check if pair has liquidity
        if (reserve0.toString() === '0' || reserve1.toString() === '0') {
          logger.warn(`Pair exists but has no liquidity for ${tokenA}-${tokenB} on ${exchange}`);
          return false;
        }

        logger.info(`Validated pair ${tokenA}-${tokenB} on ${exchange} with reserves:`, {
          reserve0: reserve0.toString(),
          reserve1: reserve1.toString(),
        });

        return true;
      } catch (error) {
        logger.error(`Error verifying pair contract:`, error);
        return false;
      }
    } catch (error) {
      logger.error(`Error validating pair ${tokenA}-${tokenB} on ${exchange}:`, error);
      return false;
    }
  }

  private async fetchPrice(
    tokenA: string,
    tokenB: string,
    exchange: string
  ): Promise<PriceData | null> {
    try {
      // Validate pair exists
      const pairExists = await this.validatePair(tokenA, tokenB, exchange);
      if (!pairExists) {
        logger.warn(`No liquidity pair exists for ${tokenA}-${tokenB} on ${exchange}`);
        return null;
      }

      // Get factory address based on exchange
      const factoryAddress = exchange === 'quickswap' ? QUICKSWAP_FACTORY : SUSHISWAP_FACTORY;

      // Create factory contract instance
      const factory = new ethers.Contract(factoryAddress, FACTORY_ABI, this.provider);

      // Get pair address
      const pairAddress = await factory.getPair(tokenA, tokenB);

      // Create pair contract instance
      const pair = new ethers.Contract(pairAddress, PAIR_ABI, this.provider);

      // Get reserves and token ordering
      const [reserve0, reserve1] = await pair.getReserves();
      const token0 = await pair.token0();

      // Order reserves based on token order
      const [reserveA, reserveB] =
        token0.toLowerCase() === tokenA.toLowerCase() ? [reserve0, reserve1] : [reserve1, reserve0];

      // Get amounts out using router
      const router = this.dexRouters[exchange];
      const amountIn = ethers.parseEther('1'); // Use 1 token as input
      const amounts = await router.getAmountsOut(amountIn, [tokenA, tokenB]);

      // Calculate price and liquidity
      const price = Number(ethers.formatEther(amounts[1]));
      const liquidity = Number(ethers.formatEther(BigInt(reserveA)));

      // Get current block
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
    } catch (error) {
      logger.error(`Error fetching price for ${tokenA}-${tokenB} on ${exchange}:`, error);
      return null;
    }
  }

  private async updatePrices() {
    try {
      const prices: PriceData[] = [];

      // Fetch prices for each pair on each DEX
      for (const { tokenA, tokenB } of this.tokenPairs) {
        for (const dex of Object.keys(this.dexRouters)) {
          try {
            const priceData = await this.fetchPrice(tokenA, tokenB, dex);
            if (priceData) {
              prices.push(priceData);

              // Store in Redis for quick access
              const redisKey = `price:${dex}:${tokenA}-${tokenB}`;
              await this.redis.set(redisKey, JSON.stringify(priceData), 'EX', 30);
            }
          } catch (error) {
            logger.error(`Failed to fetch price for ${dex} ${tokenA}-${tokenB}:`, error);
            continue;
          }
        }
      }

      // Store in MongoDB for historical data
      if (prices.length > 0) {
        await this.mongodb.db('arbitragex').collection('marketdata').insertMany(prices);
        logger.info(`Stored ${prices.length} price entries in MongoDB`);
      }

      logger.info(`Updated ${prices.length} price entries with real market data`);
    } catch (error) {
      logger.error('Error updating prices:', error);
    }
  }

  public async start() {
    try {
      await this.mongodb.connect();
      logger.info('Connected to MongoDB');

      this.redis.on('error', (err: Error) => {
        logger.error('Redis error:', err);
      });

      this.redis.on('connect', () => {
        logger.info('Connected to Redis');
      });

      // Start price updates
      setInterval(() => this.updatePrices(), this.updateInterval);
      logger.info('Real price feed started');

      // Initial update
      await this.updatePrices();
    } catch (error) {
      logger.error('Error starting price feed:', error);
      process.exit(1);
    }
  }

  public async stop() {
    await this.mongodb.close();
    await this.redis.quit();
    logger.info('Real price feed stopped');
  }
}

export { RealPriceFeed };
