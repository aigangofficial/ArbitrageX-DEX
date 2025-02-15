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
    this.dexList = ['uniswap', 'sushiswap'];
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
      { tokenA: config.contracts.wmatic, tokenB: config.contracts.quickswapRouter },
      { tokenA: config.contracts.wmatic, tokenB: config.contracts.sushiswapRouter },
    ];

    for (const pair of tokenPairs) {
      try {
        const prices: PriceData[] = await Promise.all(
          this.dexList.map(dex => this.getPriceData(dex, pair.tokenA, pair.tokenB))
        );

        const opportunities = this.findArbitrageOpportunities(prices);

        if (opportunities.length > 0) {
          await this.saveOpportunities(opportunities);
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
        dex: dex.toUpperCase() === 'UNISWAP' ? 'UNISWAP_V2' : 'SUSHISWAP',
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
          // Format data according to MarketData schema
          opportunities.push({
            tokenA: prices[i].tokenA,
            tokenB: prices[i].tokenB,
            exchange: prices[i].dex, // Already formatted in getPriceData
            price: priceA,
            liquidity: prices[i].liquidity,
            timestamp: new Date(),
            spread,
          });

          // Add the second exchange's data
          opportunities.push({
            tokenA: prices[j].tokenA,
            tokenB: prices[j].tokenB,
            exchange: prices[j].dex,
            price: priceB,
            liquidity: prices[j].liquidity,
            timestamp: new Date(),
            spread,
          });
        }
      }
    }

    return opportunities;
  }

  private async saveOpportunities(opportunities: any[]) {
    try {
      const currentBlock = await this.provider.getBlockNumber();

      await MarketData.insertMany(
        opportunities.map(opp => ({
          tokenA: opp.tokenA,
          tokenB: opp.tokenB,
          exchange: opp.exchange,
          price: opp.price,
          liquidity: opp.liquidity,
          timestamp: opp.timestamp,
          blockNumber: currentBlock,
          spread: opp.spread,
        }))
      );

      logger.info('Saved arbitrage opportunities:', {
        count: opportunities.length,
      });
    } catch (error) {
      logger.error('Error saving arbitrage opportunities:', error);
    }
  }
}

export default ArbitrageScanner;
