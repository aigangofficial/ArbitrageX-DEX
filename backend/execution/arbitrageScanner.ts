import { ethers } from 'ethers';
import { config } from '../api/config';
import { logger } from '../api/utils/logger';
import { MarketData } from '../database/models';

interface PriceData {
  dex: string;
  tokenA: string;
  tokenB: string;
  price: number;
  liquidity: number;
  timestamp: Date;
}

class ArbitrageScanner {
  private provider: ethers.JsonRpcProvider;
  private dexList: string[];
  private isScanning: boolean;

  constructor() {
    this.provider = new ethers.JsonRpcProvider(config.network.rpc);
    this.dexList = ['QUICKSWAP', 'SUSHISWAP'];
    this.isScanning = false;
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
    const tokenPairs = [
      { tokenA: config.contracts.wmatic, tokenB: config.contracts.usdc },
      { tokenA: config.contracts.wmatic, tokenB: config.contracts.usdt },
      { tokenA: config.contracts.wmatic, tokenB: config.contracts.dai },
    ];

    for (const pair of tokenPairs) {
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
          this.dexList.map(dex => this.getPriceData(dex, pair.tokenA, pair.tokenB))
        );

        const opportunities = this.findArbitrageOpportunities(prices);

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
                    hasTimestamp: opp.timestamp instanceof Date,
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
      // For demonstration, using mock data with proper structure
      const mockPrice = Math.random() * 100;
      const mockLiquidity = Math.random() * 1000000;

      return {
        dex: dex.toUpperCase() === 'QUICKSWAP' ? 'QUICKSWAP' : 'SUSHISWAP',
        tokenA,
        tokenB,
        price: mockPrice,
        liquidity: mockLiquidity,
        timestamp: new Date(),
      };
    } catch (error) {
      logger.error('Error getting price data:', {
        dex,
        tokenA,
        tokenB,
        error,
      });
      throw error;
    }
  }

  private findArbitrageOpportunities(prices: PriceData[]) {
    const opportunities = [];
    const minProfitThreshold = 0.5; // 0.5% minimum profit threshold

    for (let i = 0; i < prices.length; i++) {
      for (let j = i + 1; j < prices.length; j++) {
        const priceA = prices[i].price;
        const priceB = prices[j].price;
        const spread = Math.abs((priceA - priceB) / priceA) * 100;

        if (spread >= minProfitThreshold) {
          // Log the price data before creating opportunities
          logger.info('Creating opportunity from prices:', {
            price1: {
              dex: prices[i].dex,
              tokenA: prices[i].tokenA,
              tokenB: prices[i].tokenB,
              price: priceA,
              liquidity: prices[i].liquidity,
            },
            price2: {
              dex: prices[j].dex,
              tokenA: prices[j].tokenA,
              tokenB: prices[j].tokenB,
              price: priceB,
              liquidity: prices[j].liquidity,
            },
          });

          // Format data according to MarketData schema
          const opportunity1 = {
            tokenA: prices[i].tokenA,
            tokenB: prices[i].tokenB,
            exchange: prices[i].dex.toUpperCase() === 'QUICKSWAP' ? 'QUICKSWAP' : 'SUSHISWAP',
            price: priceA,
            liquidity: prices[i].liquidity,
            timestamp: new Date(),
            blockNumber: 0, // This will be set by the blockchain
            spread,
          };

          const opportunity2 = {
            tokenA: prices[j].tokenA,
            tokenB: prices[j].tokenB,
            exchange: prices[j].dex.toUpperCase() === 'QUICKSWAP' ? 'QUICKSWAP' : 'SUSHISWAP',
            price: priceB,
            liquidity: prices[j].liquidity,
            timestamp: new Date(),
            blockNumber: 0, // This will be set by the blockchain
            spread,
          };

          // Log the created opportunities
          logger.info('Created opportunities:', {
            opportunity1,
            opportunity2,
          });

          opportunities.push(opportunity1, opportunity2);
        }
      }
    }

    return opportunities;
  }
}

export default ArbitrageScanner;
