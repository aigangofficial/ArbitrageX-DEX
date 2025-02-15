import { ethers } from 'ethers';
import { config } from '../api/config';
import { logger } from '../api/utils/logger';

class GasOptimizer {
  private provider: ethers.JsonRpcProvider;
  private gasPriceHistory: number[];
  private maxHistorySize: number;

  constructor() {
    this.provider = new ethers.JsonRpcProvider(config.network.rpc);
    this.gasPriceHistory = [];
    this.maxHistorySize = 100; // Keep last 100 gas price readings
  }

  public async getOptimalGasPrice(): Promise<bigint> {
    try {
      const currentGasPrice = await this.provider.getFeeData();

      if (!currentGasPrice.gasPrice) {
        throw new Error('Failed to get current gas price');
      }

      // Add to history and maintain max size
      this.gasPriceHistory.push(Number(currentGasPrice.gasPrice));
      if (this.gasPriceHistory.length > this.maxHistorySize) {
        this.gasPriceHistory.shift();
      }

      // Calculate optimal gas price based on recent history
      const optimalPrice = this.calculateOptimalPrice(currentGasPrice.gasPrice);

      logger.info('Calculated optimal gas price:', {
        current: currentGasPrice.gasPrice.toString(),
        optimal: optimalPrice.toString(),
      });

      return optimalPrice;
    } catch (error) {
      logger.error('Error getting optimal gas price:', error);
      throw error;
    }
  }

  private calculateOptimalPrice(currentPrice: bigint): bigint {
    // If we don't have enough history, return current price
    if (this.gasPriceHistory.length < 10) {
      return currentPrice;
    }

    // Calculate average and standard deviation
    const avg = this.calculateAverage();
    const std = this.calculateStandardDeviation(avg);

    // If current price is significantly lower than average, it's a good time to transact
    if (Number(currentPrice) < avg - std) {
      return currentPrice;
    }

    // If current price is significantly higher than average, wait if possible
    if (Number(currentPrice) > avg + std) {
      // Return a price that's slightly above average
      return BigInt(Math.floor(avg * 1.1));
    }

    // Otherwise, return current price
    return currentPrice;
  }

  private calculateAverage(): number {
    const sum = this.gasPriceHistory.reduce((a, b) => a + b, 0);
    return sum / this.gasPriceHistory.length;
  }

  private calculateStandardDeviation(avg: number): number {
    const squareDiffs = this.gasPriceHistory.map(price => {
      const diff = price - avg;
      return diff * diff;
    });

    const avgSquareDiff = squareDiffs.reduce((a, b) => a + b, 0) / squareDiffs.length;
    return Math.sqrt(avgSquareDiff);
  }

  public async estimateGasLimit(
    to: string,
    data: string,
    value: bigint = BigInt(0)
  ): Promise<bigint> {
    try {
      const gasEstimate = await this.provider.estimateGas({
        to,
        data,
        value,
      });

      // Add 20% buffer to the estimate
      const gasBuffer = (gasEstimate * BigInt(120)) / BigInt(100);

      logger.info('Estimated gas limit:', {
        estimate: gasEstimate.toString(),
        withBuffer: gasBuffer.toString(),
      });

      return gasBuffer;
    } catch (error) {
      logger.error('Error estimating gas limit:', error);
      throw error;
    }
  }

  public async waitForOptimalGas(maxWaitTime: number = 300000): Promise<bigint> {
    const startTime = Date.now();
    let optimalPrice: bigint;

    while (true) {
      optimalPrice = await this.getOptimalGasPrice();

      // If we've found a good price or exceeded max wait time, return the price
      if (Number(optimalPrice) < this.calculateAverage() || Date.now() - startTime > maxWaitTime) {
        return optimalPrice;
      }

      // Wait 15 seconds before checking again
      await new Promise(resolve => setTimeout(resolve, 15000));
    }
  }
}

export default GasOptimizer;
