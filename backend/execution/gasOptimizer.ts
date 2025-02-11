import { ethers } from 'ethers';

export class GasOptimizer {
  private readonly MAX_GWEI = 150; // Maximum gas price we're willing to pay
  private readonly MIN_GWEI = 10; // Minimum gas price for transaction to be included
  private readonly SPEED_MULTIPLIER = 1.1; // 10% faster than base fee
  private readonly provider: ethers.Provider;

  constructor(provider: ethers.Provider) {
    this.provider = provider;
  }

  public async getOptimalGasPrice(): Promise<bigint> {
    try {
      const feeData = await this.provider.getFeeData();
      const baseFeePerGas = feeData.gasPrice || feeData.maxFeePerGas || BigInt(0);

      if (!baseFeePerGas) {
        throw new Error('Could not determine base fee');
      }

      // Calculate optimal price (multiply by SPEED_MULTIPLIER)
      const multiplier = BigInt(Math.floor(this.SPEED_MULTIPLIER * 100));
      const optimalPrice = (baseFeePerGas * multiplier) / BigInt(100);

      // Ensure price is within bounds
      const maxPrice = BigInt(this.MAX_GWEI) * BigInt(1e9); // Convert to wei
      const minPrice = BigInt(this.MIN_GWEI) * BigInt(1e9); // Convert to wei

      if (optimalPrice > maxPrice) return maxPrice;
      if (optimalPrice < minPrice) return minPrice;

      return optimalPrice;
    } catch (error) {
      console.error('Error calculating optimal gas price:', error);
      throw error;
    }
  }

  public async estimateGasLimit(tx: ethers.TransactionRequest): Promise<bigint> {
    try {
      const gasEstimate = await this.provider.estimateGas(tx);

      // Add 20% buffer for safety
      return (gasEstimate * BigInt(120)) / BigInt(100);
    } catch (error) {
      console.error('Error estimating gas limit:', error);
      throw error;
    }
  }
}
