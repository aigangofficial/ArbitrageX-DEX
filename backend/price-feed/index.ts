import dotenv from 'dotenv';
import { ethers } from 'ethers';
import Redis from 'ioredis';
import { MongoClient } from 'mongodb';
import { logger } from '../api/utils/logger';
import { IDEXRouter } from '../execution/interfaces/IDEXRouter';

dotenv.config();

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
        tokenA: process.env.AMOY_WETH!,
        tokenB: process.env.AMOY_USDC!,
      },
      {
        tokenA: process.env.AMOY_WETH!,
        tokenB: process.env.AMOY_USDT!,
      },
      {
        tokenA: process.env.AMOY_USDC!,
        tokenB: process.env.AMOY_USDT!,
      },
    ];
  }

  private async validatePair(tokenA: string, tokenB: string, exchange: string): Promise<boolean> {
    try {
      // Get factory address based on exchange
      const factoryAddress = exchange === 'quickswap' ? QUICKSWAP_FACTORY : SUSHISWAP_FACTORY;

      // Create factory contract instance
      const factory = new ethers.Contract(factoryAddress, FACTORY_ABI, this.provider);

      // Get pair address
      const pairAddress = await factory.getPair(tokenA, tokenB);

      // Check if pair exists
      if (pairAddress === ethers.ZeroAddress) {
        logger.warn(`No liquidity pair exists for ${tokenA}/${tokenB} on ${exchange}`);
        return false;
      }

      // Create pair contract instance
      const pair = new ethers.Contract(pairAddress, PAIR_ABI, this.provider);

      // Get reserves to validate liquidity
      const [reserve0, reserve1] = await pair.getReserves();

      // Check if pair has liquidity
      if (reserve0 === 0n || reserve1 === 0n) {
        logger.warn(`No liquidity for ${tokenA}/${tokenB} on ${exchange}`);
        return false;
      }

      return true;
    } catch (error) {
      logger.error(`Error validating pair ${tokenA}/${tokenB} on ${exchange}:`, error);
      return false;
    }
  }

  private async fetchPrice(
    tokenA: string,
    tokenB: string,
    exchange: string
  ): Promise<PriceData | null> {
    try {
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
      const path = [tokenA, tokenB];
      const amounts = await router.getAmountsOut(ethers.parseEther('1'), path);

      // Calculate price and liquidity
      const price = Number(ethers.formatEther(amounts[1]));
      const liquidity = Number(ethers.formatEther(reserveA));

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
      logger.error(`Error fetching price for ${tokenA}/${tokenB} on ${exchange}:`, error);
      return null;
    }
  }

  private async updatePrices() {
    try {
      // Get current block number
      const blockNumber = await this.provider.getBlockNumber();

      // Fetch prices for all token pairs on all exchanges
      for (const { tokenA, tokenB } of this.tokenPairs) {
        // Validate and fetch prices from QuickSwap
        if (await this.validatePair(tokenA, tokenB, 'quickswap')) {
          const quickswapPrice = await this.fetchPrice(tokenA, tokenB, 'quickswap');
          if (quickswapPrice) {
            await this.mongodb.db('arbitragex').collection('prices').insertOne(quickswapPrice);
            await this.redis.set(
              `price:${tokenA}:${tokenB}:quickswap`,
              JSON.stringify(quickswapPrice)
            );
          }
        }

        // Validate and fetch prices from SushiSwap
        if (await this.validatePair(tokenA, tokenB, 'sushiswap')) {
          const sushiswapPrice = await this.fetchPrice(tokenA, tokenB, 'sushiswap');
          if (sushiswapPrice) {
            await this.mongodb.db('arbitragex').collection('prices').insertOne(sushiswapPrice);
            await this.redis.set(
              `price:${tokenA}:${tokenB}:sushiswap`,
              JSON.stringify(sushiswapPrice)
            );
          }
        }
      }
    } catch (error) {
      logger.error('Error updating prices:', error);
    }
  }

  public async start() {
    try {
      // Connect to MongoDB
      await this.mongodb.connect();
      logger.info('Connected to MongoDB');

      // Start price update interval
      setInterval(() => this.updatePrices(), this.updateInterval);
      logger.info('Price feed started');

      // Initial price update
      await this.updatePrices();
    } catch (error) {
      logger.error('Error starting price feed:', error);
      throw error;
    }
  }

  public async stop() {
    try {
      // Clear update interval
      clearInterval(this.updateInterval);

      // Close MongoDB connection
      await this.mongodb.close();
      logger.info('Price feed stopped');
    } catch (error) {
      logger.error('Error stopping price feed:', error);
      throw error;
    }
  }
}

export default RealPriceFeed;
