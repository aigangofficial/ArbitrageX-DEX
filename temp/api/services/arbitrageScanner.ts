import { ethers } from 'ethers';
import { WebSocketServer } from 'ws';
import { ArbitrageScanner as CoreScanner } from '../../execution/arbitrageScanner';
import { config } from '../config';

export class ArbitrageScanner {
  private readonly coreScanner: CoreScanner;

  constructor() {
    const provider = new ethers.JsonRpcProvider(config.network.rpc);
    const wsServer = new WebSocketServer({ port: config.api.wsPort });

    this.coreScanner = new CoreScanner(
      provider,
      wsServer,
      config.contracts.flashLoanService,
      config.contracts.quickswapRouter,
      config.contracts.sushiswapRouter,
      config.contracts.wmatic
    );
  }

  public async startScanning(): Promise<void> {
    return this.coreScanner.startScanning();
  }

  public stopScanning(): void {
    return this.coreScanner.stopScanning();
  }

  public getConnectedClients(): number {
    return (this.coreScanner as any).wsServer?.clients?.size || 0;
  }
}
