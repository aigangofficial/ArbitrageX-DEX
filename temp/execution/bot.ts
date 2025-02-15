import { ethers } from 'ethers';
import { WebSocketServer } from 'ws';
import { PriceFetcher } from '../services/priceFetcher';
// import { ArbitrageOpportunity } from '../types/trading';
import { ArbitrageExecutor__factory } from '../../typechain-types';
import { ITradeResult } from '../types/contracts';
import { ArbitrageScanner } from './arbitrageScanner';
import { GasOptimizer } from './gasOptimizer';

interface ArbitrageOpportunity {
  tokenA: string;
  tokenB: string;
  amountIn: string;
  amountOut: string;
}

export class Bot {
  private readonly _scanner: ArbitrageScanner;
  private readonly gasOptimizer: GasOptimizer;
  private isRunning: boolean;

  constructor(config: {
    provider: ethers.JsonRpcProvider;
    flashLoanAddress: string;
    wsServer: WebSocketServer;
    uniswapRouterAddress: string;
    sushiswapRouterAddress: string;
    wethAddress: string;
  }) {
    this.gasOptimizer = new GasOptimizer(config.provider);
    this._scanner = new ArbitrageScanner(
      config.provider,
      config.wsServer,
      config.flashLoanAddress,
      config.uniswapRouterAddress,
      config.sushiswapRouterAddress,
      config.wethAddress
    );
    this.isRunning = false;
  }

  public async start(): Promise<void> {
    if (this.isRunning) {
      console.log('Bot is already running');
      return;
    }
    this.isRunning = true;
    console.log('Bot started');

    // Start scanning for opportunities
    await this._scanner.startScanning();
  }

  public stop(): void {
    this.isRunning = false;
    this._scanner.stopScanning();
    console.log('Bot stopped');
  }

  protected async executeTradeWithGas(opportunity: ArbitrageOpportunity): Promise<ITradeResult> {
    const gasPrice = await this.gasOptimizer.getOptimalGasPrice();
    const contract = ArbitrageExecutor__factory.connect(
      opportunity.tokenA,
      this._scanner.getProvider()
    );

    try {
      const tx = await contract.executeArbitrage(
        opportunity.tokenA,
        opportunity.tokenB,
        ethers.parseEther(opportunity.amountIn),
        true,
        {
          gasPrice,
        }
      );

      const txReceipt = await tx.wait();

      let actualProfit = 0;
      try {
        const priceData = await new PriceFetcher().getRealTimePrices([
          opportunity.tokenA,
          opportunity.tokenB,
        ]);

        actualProfit =
          parseFloat(ethers.formatEther(opportunity.amountOut)) *
            (priceData[opportunity.tokenB] || 0) -
          parseFloat(ethers.formatEther(opportunity.amountIn)) *
            (priceData[opportunity.tokenA] || 0);
      } catch (error) {
        console.error('Price fetch failed:', error);
        actualProfit = 0;
      }

      return {
        success: true,
        profit: ethers.parseEther(actualProfit.toFixed(4)),
        gasUsed: txReceipt?.gasUsed || 0n,
      };
    } catch (error) {
      return {
        success: false,
        profit: 0n,
        gasUsed: 0n,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }
}
