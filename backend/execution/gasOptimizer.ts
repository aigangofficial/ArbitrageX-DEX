import { ethers } from 'ethers';

export class GasOptimizer {
    private readonly MAX_GWEI = 150; // Maximum gas price we're willing to pay
    private readonly MIN_GWEI = 10;  // Minimum gas price for transaction to be included
    private readonly SPEED_MULTIPLIER = 1.1; // Multiply base fee by this to get included faster

    constructor(private provider: ethers.Provider) {}

    public async getOptimalGasPrice(): Promise<ethers.BigNumber> {
        try {
            // Get latest block to check current network conditions
            const block = await this.provider.getBlock('latest');
            
            if (!block) {
                throw new Error('Could not fetch latest block');
            }

            // Calculate optimal gas price based on network conditions
            const baseFeePerGas = block.baseFeePerGas || ethers.parseUnits('20', 'gwei');
            let optimalPrice = baseFeePerGas.mul(Math.floor(this.SPEED_MULTIPLIER * 100)).div(100);

            // Ensure gas price is within our limits
            const maxPrice = ethers.parseUnits(this.MAX_GWEI.toString(), 'gwei');
            const minPrice = ethers.parseUnits(this.MIN_GWEI.toString(), 'gwei');

            if (optimalPrice.gt(maxPrice)) {
                optimalPrice = maxPrice;
            } else if (optimalPrice.lt(minPrice)) {
                optimalPrice = minPrice;
            }

            return optimalPrice;
        } catch (error) {
            console.error('Error calculating optimal gas price:', error);
            // Return default gas price if calculation fails
            return ethers.parseUnits('20', 'gwei');
        }
    }

    public async estimateGasLimit(tx: ethers.providers.TransactionRequest): Promise<ethers.BigNumber> {
        try {
            const gasEstimate = await this.provider.estimateGas(tx);
            // Add 20% buffer to gas estimate
            return gasEstimate.mul(120).div(100);
        } catch (error) {
            console.error('Error estimating gas limit:', error);
            throw error;
        }
    }
} 