import { ethers } from 'ethers';
import { config } from '../api/config';
import { logger } from '../api/utils/logger';
import { MarketData } from '../database/models';
import GasOptimizer from './gasOptimizer';
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

interface ArbitrageOpportunity {
  exchange: string;
  tokenA: string;
  tokenB: string;
  price: number;
  liquidity: number;
  timestamp: Date;
  blockNumber: number;
  spread: number;
}

interface IDEXRouter {
  estimateGas: {
    swapExactTokensForTokens(
      amountIn: bigint,
      amountOutMin: bigint,
      path: string[],
      to: string,
      deadline: number
    ): Promise<bigint>;
  };
  getAmountsOut(amountIn: bigint, path: string[]): Promise<bigint[]>;
  address: string;
}

export class ArbitrageScanner {
  private provider: ethers.Provider;
  private quickswapRouter: IDEXRouter;
  private sushiswapRouter: IDEXRouter;
  private aavePool: any;
  private tradeExecutor: TradeExecutor;
  private gasOptimizer: GasOptimizer;
  private isScanning: boolean;
  private tokenPairs: TokenPair[];

  constructor(
    provider: ethers.Provider,
    quickswapRouterAddress: string,
    sushiswapRouterAddress: string,
    aavePoolAddress: string
  ) {
    this.provider = provider;
    this.gasOptimizer = new GasOptimizer();

    // Initialize contracts with proper interface casting
    this.quickswapRouter = new ethers.Contract(
      quickswapRouterAddress,
      [
        'function getAmountsOut(uint amountIn, address[] memory path) view returns (uint[] memory amounts)',
      ],
      provider
    ) as unknown as IDEXRouter;

    this.sushiswapRouter = new ethers.Contract(
      sushiswapRouterAddress,
      [
        'function getAmountsOut(uint amountIn, address[] memory path) view returns (uint[] memory amounts)',
      ],
      provider
    ) as unknown as IDEXRouter;

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

    // Initialize token pairs using config
    const wmatic = process.env.AMOY_WMATIC || '';
    const usdc = process.env.AMOY_USDC || '';
    const usdt = process.env.AMOY_USDT || '';
    const dai = process.env.AMOY_DAI || '';

    this.tokenPairs = [
      { tokenA: wmatic, tokenB: usdc },
      { tokenA: wmatic, tokenB: usdt },
      { tokenA: wmatic, tokenB: dai },
      { tokenA: usdc, tokenB: usdt },
      { tokenA: usdc, tokenB: dai },
      { tokenA: usdt, tokenB: dai },
    ].filter(pair => pair.tokenA && pair.tokenB);

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
                    hasTokenA: Boolean(opp.tokenA),
                    hasTokenB: Boolean(opp.tokenB),
                    tokenALength: opp.tokenA?.length,
                    tokenBLength: opp.tokenB?.length,
                    hasExchange: Boolean(opp.exchange),
                    hasPrice: typeof opp.price === 'number',
                    hasLiquidity: typeof opp.liquidity === 'number',
                    hasTimestamp: typeof opp.timestamp === 'number',
                    hasBlockNumber: typeof opp.blockNumber === 'number',
                  })),
                },
                null,
                2
              )
            );

            // Log each opportunity before saving
            opportunities.forEach((opp, index) => {
              logger.info(`Opportunity ${index + 1} data:`, {
                tokenA: opp.tokenA,
                tokenB: opp.tokenB,
                exchange: opp.exchange,
                price: opp.price,
                liquidity: opp.liquidity,
                timestamp: opp.timestamp,
                blockNumber: opp.blockNumber,
                spread: opp.spread,
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
    const minProfitThreshold = config.security.minProfitThreshold || 0.5;

    for (let i = 0; i < prices.length; i++) {
      for (let j = i + 1; j < prices.length; j++) {
        const priceA = prices[i].price;
        const priceB = prices[j].price;
        const spread = Math.abs((priceA - priceB) / Math.min(priceA, priceB)) * 100;

        if (spread >= minProfitThreshold) {
          const buyDex = priceA < priceB ? prices[i] : prices[j];
          const sellDex = priceA < priceB ? prices[j] : prices[i];

          if (await this.validateOpportunity(buyDex, sellDex, spread)) {
            try {
              await this.tradeExecutor.executeArbitrage({
                buyDex: buyDex.dex,
                sellDex: sellDex.dex,
                tokenA: buyDex.tokenA,
                tokenB: buyDex.tokenB,
                amount: ethers.parseEther('1'),
                expectedProfit: spread,
              });

              opportunities.push({
                exchange: buyDex.dex,
                tokenA: buyDex.tokenA,
                tokenB: buyDex.tokenB,
                price: buyDex.price,
                liquidity: buyDex.liquidity,
                timestamp: new Date(buyDex.timestamp * 1000),
                blockNumber: buyDex.blockNumber,
                spread,
              });
            } catch (error) {
              logger.error('Failed to execute arbitrage:', error);
            }
          }
        }
      }
    }
    return opportunities;
  }

  private async validateOpportunity(
    buyDex: PriceData,
    sellDex: PriceData,
    spread: number
  ): Promise<boolean> {
    // Add validation logic here
    const minLiquidity = ethers.parseEther('1000'); // Minimum 1000 tokens liquidity

    if (buyDex.liquidity < minLiquidity || sellDex.liquidity < minLiquidity) {
      logger.info('Insufficient liquidity for arbitrage');
      return false;
    }

    // Validate that the spread is still profitable after gas costs
    const estimatedGasCost = await this.tradeExecutor.estimateGasCost(
      buyDex.dex,
      sellDex.dex,
      buyDex.tokenA,
      buyDex.tokenB
    );

    const profitAfterGas = spread - estimatedGasCost;
    if (profitAfterGas <= 0) {
      logger.info('Opportunity not profitable after gas costs');
      return false;
    }

    return true;
  }
}

export default ArbitrageScanner;
