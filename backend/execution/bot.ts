import { ethers } from 'ethers';
import { WebSocketServer } from 'ws';
import { ArbitrageOpportunity } from '../types/trading';
import { ArbitrageScanner } from './arbitrageScanner';
import { GasOptimizer } from './gasOptimizer';

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
  }) {
    this.gasOptimizer = new GasOptimizer(config.provider);
    this._scanner = new ArbitrageScanner(
      config.provider,
      config.wsServer,
      config.flashLoanAddress,
      config.uniswapRouterAddress,
      config.sushiswapRouterAddress
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

  protected async executeTradeWithGas(opportunity: ArbitrageOpportunity): Promise<{
    txHash: string;
    profit: string;
    gasUsed: string;
  }> {
    const gasPrice = await this.gasOptimizer.getOptimalGasPrice();
    const contract = new ethers.Contract(
      opportunity.tokenA,
      [
        'function executeArbitrage(address tokenA, address tokenB, uint256 amount) external returns (uint256)',
      ],
      this._scanner.getProvider()
    );

    const tx = await contract.executeArbitrage(
      opportunity.tokenA,
      opportunity.tokenB,
      opportunity.amountIn,
      {
        gasPrice,
      }
    );

    const txReceipt = await tx.wait();

    return {
      txHash: txReceipt?.hash ?? '',
      profit: '0', // TODO: Calculate actual profit
      gasUsed: txReceipt?.gasUsed?.toString() ?? '0',
    };
  }
}
