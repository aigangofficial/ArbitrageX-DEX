import { ethers } from 'ethers';
import { EventEmitter } from 'events';
import { config } from '../api/config';
import { logger } from '../api/utils/logger';
import { MarketData } from '../database/models';
import GasOptimizer from './gasOptimizer';
import { DEXRouterFactory, IDEXRouter } from './interfaces/IDEXRouter';
import { TradeExecutor } from './tradeExecutor';

// Router ABI for DEX interactions
const ROUTER_ABI = [
  'function getAmountsOut(uint256 amountIn, address[] calldata path) external view returns (uint256[] memory amounts)',
  'function swapExactTokensForTokens(uint256 amountIn, uint256 amountOutMin, address[] calldata path, address to, uint256 deadline) external returns (uint256[] memory amounts)',
  'function factory() external view returns (address)',
  'function WETH() external view returns (address)',
];

// Aave V3 Pool ABI for flash loans
const AAVE_POOL_ABI = [
  'function flashLoan(address receiverAddress, address[] calldata assets, uint256[] calldata amounts, uint256[] calldata modes, address onBehalfOf, bytes calldata params, uint16 referralCode) external returns (bool)',
  'function FLASHLOAN_PREMIUM_TOTAL() view returns (uint256)',
];

interface PriceData {
  dex: string;
  tokenA: string;
  tokenB: string;
  price: number;
  liquidity: number;
  timestamp: number;
  blockNumber: number;
}

interface TokenPair {
  tokenA: string;
  tokenB: string;
}

interface ScannerConfig {
  minProfitThreshold: number;
  minNetProfit: number;
  gasLimit: number;
  scanInterval: number;
}

interface ArbitrageOpportunity {
  pair: string;
  dexA: string;
  dexB: string;
  priceA: number;
  priceB: number;
  spread: number;
  timestamp: number;
  netProfit?: number;
}

export class ArbitrageScanner extends EventEmitter {
  private provider: ethers.JsonRpcProvider;
  private quickswapRouter: IDEXRouter;
  private sushiswapRouter: IDEXRouter;
  private aavePool: any;
  private tradeExecutor: TradeExecutor;
  private gasOptimizer: GasOptimizer;
  private isScanning: boolean;
  private tokenPairs: TokenPair[];
  private config: ScannerConfig;

  constructor(
    provider: ethers.JsonRpcProvider,
    quickswapRouterAddress: string,
    sushiswapRouterAddress: string,
    aavePoolAddress: string,
    config: ScannerConfig,
    tokenPairs: TokenPair[]
  ) {
    super();
    this.provider = provider;
    this.gasOptimizer = new GasOptimizer();

    // Initialize contracts with proper interface casting
    this.quickswapRouter = DEXRouterFactory.connect(quickswapRouterAddress, provider);
    this.sushiswapRouter = DEXRouterFactory.connect(sushiswapRouterAddress, provider);

    this.aavePool = new ethers.Contract(
      aavePoolAddress,
      [
        'function flashLoan(address receiverAddress, address[] calldata assets, uint256[] calldata amounts, uint256[] calldata modes, address onBehalfOf, bytes calldata params, uint16 referralCode)',
      ],
      provider
    );

    this.tradeExecutor = new TradeExecutor(
      this.provider,
      this.quickswapRouter,
      this.sushiswapRouter,
      this.aavePool
    );

    this.isScanning = false;
    this.config = config;
    this.tokenPairs = tokenPairs;

    logger.info(`Initialized ${this.tokenPairs.length} token pairs for scanning`);
    logger.info('Token pairs:', this.tokenPairs);
  }

  public getIsScanning(): boolean {
    return this.isScanning;
  }

  public async start() {
    if (this.isScanning) {
      logger.warn('Arbitrage scanner is already running');
      return;
    }

    this.isScanning = true;
    logger.info('Starting arbitrage scanner');

    while (this.isScanning) {
      try {
        await this.scanMarkets();
        await new Promise(resolve => setTimeout(resolve, 5000)); // 5 second interval
      } catch (error) {
        logger.error('Error in arbitrage scanner:', error);
        await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5s on error
      }
    }
  }

  public stop() {
    this.isScanning = false;
    logger.info('Stopping arbitrage scanner');
  }

  private async scanMarkets() {
    for (const pair of this.tokenPairs) {
      try {
        logger.info('Processing token pair:', {
          tokenA: pair.tokenA,
          tokenB: pair.tokenB,
          tokenAExists: Boolean(pair.tokenA),
          tokenBExists: Boolean(pair.tokenB),
          tokenALength: pair.tokenA?.length,
          tokenBLength: pair.tokenB?.length,
        });

        const prices: PriceData[] = await Promise.all(
          ['QUICKSWAP', 'SUSHISWAP'].map(dex => this.getPriceData(dex, pair.tokenA, pair.tokenB))
        );

        const opportunities = await this.findArbitrageOpportunities(prices);

        if (opportunities.length > 0) {
          // Save each opportunity to the database
          try {
            logger.info(
              'Attempting to save opportunities:',
              JSON.stringify(
                {
                  tokenPair: pair,
                  prices,
                  opportunities,
                  opportunityValidation: opportunities.map(opp => ({
                    hasPair: Boolean(opp.pair),
                    hasDexA: Boolean(opp.dexA),
                    hasDexB: Boolean(opp.dexB),
                    hasPriceA: typeof opp.priceA === 'number',
                    hasPriceB: typeof opp.priceB === 'number',
                    hasSpread: typeof opp.spread === 'number',
                    hasTimestamp: typeof opp.timestamp === 'number',
                    hasNetProfit: typeof opp.netProfit === 'number'
                  })),
                },
                null,
                2
              )
            );

            // Log each opportunity before saving
            opportunities.forEach((opp, index) => {
              logger.info(`Opportunity ${index + 1} data:`, {
                pair: opp.pair,
                dexA: opp.dexA,
                dexB: opp.dexB,
                priceA: opp.priceA,
                priceB: opp.priceB,
                spread: opp.spread,
                timestamp: opp.timestamp,
                netProfit: opp.netProfit
              });
            });

            await MarketData.insertMany(opportunities).catch(error => {
              if (error.name === 'ValidationError') {
                logger.error('MongoDB validation error:', {
                  error: error.message,
                  errors: error.errors,
                  validationErrors: Object.keys(error.errors).map(field => ({
                    field,
                    message: error.errors[field].message,
                    value: error.errors[field].value,
                    valueType: typeof error.errors[field].value,
                  })),
                });
              }
              throw error;
            });
          } catch (error) {
            logger.error('Error saving arbitrage opportunities:', error);
          }
        }
      } catch (error) {
        logger.error('Error scanning pair:', {
          tokenA: pair.tokenA,
          tokenB: pair.tokenB,
          error,
        });
      }
    }
  }

  private async getPriceData(dex: string, tokenA: string, tokenB: string): Promise<PriceData> {
    try {
      // Verify token contracts exist
      const tokenACode = await this.provider.getCode(tokenA);
      const tokenBCode = await this.provider.getCode(tokenB);

      if (tokenACode === '0x' || tokenBCode === '0x') {
        throw new Error(`Invalid token contract: ${tokenACode === '0x' ? tokenA : tokenB}`);
      }

      const routerAbi = [
        'function getAmountsOut(uint256 amountIn, address[] calldata path) external view returns (uint256[] memory amounts)',
        'function WETH() external pure returns (address)',
      ];

      const routerAddress =
        dex === 'QUICKSWAP' ? config.contracts.quickswapRouter : config.contracts.sushiswapRouter;

      // Verify router contract exists
      const routerCode = await this.provider.getCode(routerAddress);
      if (routerCode === '0x') {
        throw new Error(`Invalid router contract for ${dex}: ${routerAddress}`);
      }

      const router = new ethers.Contract(routerAddress, routerAbi, this.provider);

      const path = [tokenA, tokenB];
      const amountIn = ethers.parseEther('1'); // 1 token as base amount

      logger.info('Fetching price data:', {
        dex,
        router: routerAddress,
        tokenA,
        tokenB,
        amountIn: amountIn.toString(),
      });

      const amounts = await router.getAmountsOut(amountIn, path);
      const price = Number(ethers.formatEther(amounts[1]));

      // Get current block for timestamp
      const block = await this.provider.getBlock('latest');
      if (!block) throw new Error('Could not get latest block');

      return {
        dex: dex.toUpperCase(),
        tokenA,
        tokenB,
        price,
        liquidity: amounts[1], // Using output amount as liquidity indicator
        timestamp: block.timestamp,
        blockNumber: block.number,
      };
    } catch (error) {
      logger.error('Error getting price data:', {
        dex,
        tokenA,
        tokenB,
        error:
          error instanceof Error
            ? {
                message: error.message,
                stack: error.stack,
              }
            : error,
      });
      throw error;
    }
  }

  private async findArbitrageOpportunities(prices: PriceData[]): Promise<ArbitrageOpportunity[]> {
    const opportunities: ArbitrageOpportunity[] = [];

    for (const pair of this.tokenPairs) {
      const pairPrices = prices.filter(p =>
        p.tokenA === pair.tokenA && p.tokenB === pair.tokenB
      );

      for (let i = 0; i < pairPrices.length; i++) {
        for (let j = i + 1; j < pairPrices.length; j++) {
          const buyDex = pairPrices[i];
          const sellDex = pairPrices[j];

          try {
            const spread = Math.abs(buyDex.price - sellDex.price);
            const spreadPercentage = (spread / Math.min(buyDex.price, sellDex.price)) * 100;

            if (spreadPercentage >= this.config.minProfitThreshold) {
              const gasEstimate = await this.estimateArbitrageGas();
              const netProfit = await this.calculateNetProfit(spread, gasEstimate);

              if (netProfit > this.config.minNetProfit) {
                opportunities.push({
                  pair: `${pair.tokenA}/${pair.tokenB}`,
                  dexA: buyDex.dex,
                  dexB: sellDex.dex,
                  priceA: buyDex.price,
                  priceB: sellDex.price,
                  spread: spreadPercentage,
                  timestamp: Date.now(),
                  netProfit
                });
              }
            }
          } catch (error) {
            console.error('Error calculating arbitrage opportunity:', error);
          }
        }
      }
    }

    return opportunities;
  }

  private async calculateNetProfit(spread: number, gasEstimate: bigint): Promise<number> {
    try {
      const feeData = await this.provider.getFeeData();
      if (!feeData.gasPrice) {
        throw new Error('Could not get gas price');
      }
      const gasCost = Number(ethers.formatEther(gasEstimate * feeData.gasPrice));
      return spread - gasCost;
    } catch (error) {
      logger.error('Error calculating net profit:', error);
      throw error;
    }
  }

  private async estimateArbitrageGas(): Promise<bigint> {
    return BigInt(this.config.gasLimit);
  }
}

export default ArbitrageScanner;
