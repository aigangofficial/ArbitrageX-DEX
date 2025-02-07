import { ethers } from 'ethers';
import { config } from '../api/config';
import { ArbitrageScanner } from './arbitrageScanner';
import { GasOptimizer } from './gasOptimizer';

export class ArbitrageBot {
    private provider: ethers.providers.JsonRpcProvider;
    private wallet: ethers.Wallet;
    private scanner: ArbitrageScanner;
    private gasOptimizer: GasOptimizer;
    private isRunning: boolean = false;

    constructor(
        private readonly privateKey: string,
        private readonly network: 'sepolia' | 'mainnet' = 'sepolia'
    ) {
        this.provider = new ethers.providers.JsonRpcProvider(config.networks[network].rpcUrl);
        this.wallet = new ethers.Wallet(privateKey, this.provider);
        this.scanner = new ArbitrageScanner(this.provider);
        this.gasOptimizer = new GasOptimizer(this.provider);
    }

    public async start() {
        if (this.isRunning) return;
        this.isRunning = true;
        
        console.log(`Starting arbitrage bot on ${this.network}`);
        
        while (this.isRunning) {
            try {
                // 1. Scan for opportunities
                const opportunities = await this.scanner.findArbitrageOpportunities();
                
                // 2. Filter profitable trades accounting for gas
                const profitableOpportunities = opportunities.filter(async (opp) => {
                    const gasPrice = await this.gasOptimizer.getOptimalGasPrice();
                    const gasCost = gasPrice.mul(opp.estimatedGas);
                    return opp.expectedProfit.gt(gasCost);
                });

                // 3. Execute the most profitable trade
                if (profitableOpportunities.length > 0) {
                    const bestTrade = profitableOpportunities[0];
                    await this.executeTrade(bestTrade);
                }

                // 4. Wait before next scan
                await new Promise(resolve => setTimeout(resolve, 1000));
            } catch (error) {
                console.error('Error in arbitrage loop:', error);
                await new Promise(resolve => setTimeout(resolve, 5000));
            }
        }
    }

    public stop() {
        this.isRunning = false;
        console.log('Stopping arbitrage bot');
    }

    private async executeTrade(trade: any) {
        try {
            const gasPrice = await this.gasOptimizer.getOptimalGasPrice();
            const tx = await trade.execute(this.wallet, { gasPrice });
            console.log(`Trade executed: ${tx.hash}`);
            await tx.wait();
        } catch (error) {
            console.error('Trade execution failed:', error);
        }
    }
} 