import axios from 'axios';
import fs from 'fs/promises';
import path from 'path';
import { config } from '../api/config';

export class PriceFetcher {
  private readonly coinGeckoURL = 'https://api.coingecko.com/api/v3/simple/price';
  private readonly priceDataPath: string;

  constructor() {
    this.priceDataPath = path.join(process.cwd(), 'data', 'price-data.json');
  }

  async getRealTimePrices(coinIds: string[]): Promise<Record<string, number>> {
    try {
      // First try to read from cache
      const cachedData = await this.readPriceData();
      const now = Date.now();
      const CACHE_TIMEOUT = 5 * 60 * 1000; // 5 minutes

      // If cache is fresh, use it
      if (cachedData && now - cachedData.timestamp < CACHE_TIMEOUT) {
        return cachedData.prices;
      }

      const response = await axios.get(this.coinGeckoURL, {
        params: {
          ids: coinIds.join(','),
          vs_currencies: 'usd',
          x_cg_pro_api_key: config.trading.coinGeckoKey,
        },
      });
      const prices = response.data;

      // Save to cache
      await this.savePriceData(prices);
      return prices;
    } catch (error) {
      console.error('Price fetch error:', error);
      return {};
    }
  }

  private async savePriceData(prices: Record<string, number>): Promise<void> {
    const data = {
      timestamp: Date.now(),
      prices,
    };
    await fs.writeFile(this.priceDataPath, JSON.stringify(data, null, 2));
  }

  private async readPriceData(): Promise<{
    timestamp: number;
    prices: Record<string, number>;
  } | null> {
    try {
      const data = await fs.readFile(this.priceDataPath, 'utf-8');
      return JSON.parse(data);
    } catch {
      return null;
    }
  }

  async storeHistoricalData() {
    // Implementation for historical data storage
  }
}
