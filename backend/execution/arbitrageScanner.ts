import { ethers } from 'ethers';
import { WebSocket, WebSocketServer } from 'ws';
import { ArbitrageTrade, IArbitrageTrade } from '../database/models/ArbitrageTrade';
import { ArbitrageExecutor } from '../types/contracts';
import { ArbitrageOpportunity, PriceData } from '../types/trading';

export { PriceData }; // Export the PriceData type

export class ArbitrageScanner {
  protected readonly provider: ethers.JsonRpcProvider;
  private readonly wsServer: WebSocketServer;
  private readonly uniswapRouter: ethers.Contract;
  private readonly sushiswapRouter: ethers.Contract;
  private readonly flashLoanAddress: string;
  private readonly arbitrageExecutor: ArbitrageExecutor;
  private readonly minProfitThreshold: bigint;
  private isScanning: boolean = false;

  constructor(
    provider: ethers.JsonRpcProvider,
    wsServer: WebSocketServer,
    flashLoanAddress: string = '',
    uniswapRouterAddress: string = '',
    sushiswapRouterAddress: string = ''
  ) {
    this.provider = provider;
    this.wsServer = wsServer;
    this.flashLoanAddress = flashLoanAddress;
    this.minProfitThreshold = ethers.parseEther('0.01'); // 0.01 ETH minimum profit

    this.uniswapRouter = new ethers.Contract(
      uniswapRouterAddress || ethers.ZeroAddress,
      [
        'function getAmountsOut(uint amountIn, address[] memory path) view returns (uint[] memory amounts)',
      ],
      provider
    );

    this.sushiswapRouter = new ethers.Contract(
      sushiswapRouterAddress || ethers.ZeroAddress,
      [
        'function getAmountsOut(uint amountIn, address[] memory path) view returns (uint[] memory amounts)',
      ],
      provider
    );

    this.arbitrageExecutor = new ethers.Contract(
      this.flashLoanAddress,
      [
        'function executeArbitrage(address tokenA, address tokenB, uint256 amount) external returns (uint256)',
      ],
      this.provider
    ) as unknown as ArbitrageExecutor;
  }

  public async startScanning() {
    if (this.isScanning) return;
    this.isScanning = true;

    while (this.isScanning) {
      try {
        const trades = await ArbitrageTrade.find({ status: 'pending' })
          .sort({ createdAt: -1 })
          .limit(10)
          .lean()
          .exec();

        for (const trade of trades) {
          if (!trade.route || !trade._id) continue;

          await this.processArbitrageOpportunity({
            tokenA: trade.tokenA,
            tokenB: trade.tokenB,
            amountIn: BigInt(trade.amountIn),
            expectedProfit: BigInt(trade.expectedProfit),
            route: trade.route,
            _id: trade._id.toString(),
          });
        }
      } catch (error) {
        console.error('Error in scanning loop:', error);
      }

      await new Promise(resolve => setTimeout(resolve, 1000)); // 1 second delay
    }
  }

  public stopScanning() {
    this.isScanning = false;
  }

  private async processArbitrageOpportunity(opportunity: ArbitrageOpportunity) {
    try {
      const prices = await this.getPrices(opportunity.tokenA, opportunity.tokenB);
      if (!this.isProfitable(prices)) {
        return;
      }

      // Broadcast opportunity to connected clients
      this.wsServer.clients.forEach((client: WebSocket) => {
        if (client.readyState === WebSocket.OPEN) {
          client.send(
            JSON.stringify({
              type: 'opportunity',
              data: {
                tokenA: opportunity.tokenA,
                tokenB: opportunity.tokenB,
                expectedProfit: opportunity.expectedProfit.toString(),
                route: opportunity.route,
              },
            })
          );
        }
      });

      await this.executeArbitrage(opportunity);
    } catch (error) {
      console.error('Error processing arbitrage opportunity:', error);
      this.broadcastError(error as Error);
    }
  }

  private async executeArbitrage(opportunity: ArbitrageOpportunity) {
    const trade = await ArbitrageTrade.findById(opportunity._id).exec();
    if (!trade) {
      throw new Error('Trade not found');
    }

    try {
      trade.status = 'executing';
      await trade.save();

      this.broadcastExecution(trade);

      const tx = await this.arbitrageExecutor.executeArbitrage(
        opportunity.tokenA,
        opportunity.tokenB,
        opportunity.amountIn
      );

      const receipt = await tx.wait();

      if (receipt) {
        trade.txHash = receipt.hash;
        trade.gasUsed = receipt.gasUsed.toString();
        trade.gasPrice = receipt.gasPrice?.toString() || '0';
        trade.status = 'completed';
        await trade.save();

        this.broadcastCompletion(trade);
      }
    } catch (error) {
      trade.status = 'failed';
      trade.errorMessage = error instanceof Error ? error.message : 'Unknown error';
      await trade.save();

      this.broadcastError(error as Error);
      throw error;
    }
  }

  protected async getPrices(tokenA: string, tokenB: string): Promise<PriceData> {
    const [uniswapPrice, sushiswapPrice] = await Promise.all([
      this.getUniswapPrice(tokenA, tokenB),
      this.getSushiswapPrice(tokenA, tokenB),
    ]);

    return {
      tokenA,
      tokenB,
      uniswapPrice,
      sushiswapPrice,
    };
  }

  private async getUniswapPrice(
    tokenA: string,
    tokenB: string
  ): Promise<{ price: bigint; liquidity: bigint }> {
    const amountIn = ethers.parseEther('1');
    const amounts = await this.uniswapRouter.getAmountsOut(amountIn, [tokenA, tokenB]);
    return {
      price: amounts[1],
      liquidity: amounts[0],
    };
  }

  private async getSushiswapPrice(
    tokenA: string,
    tokenB: string
  ): Promise<{ price: bigint; liquidity: bigint }> {
    const amountIn = ethers.parseEther('1');
    const amounts = await this.sushiswapRouter.getAmountsOut(amountIn, [tokenA, tokenB]);
    return {
      price: amounts[1],
      liquidity: amounts[0],
    };
  }

  protected isProfitable(prices: PriceData): boolean {
    const uniswapPrice = prices.uniswapPrice.price;
    const sushiswapPrice = prices.sushiswapPrice.price;

    const priceDiff =
      uniswapPrice > sushiswapPrice ? uniswapPrice - sushiswapPrice : sushiswapPrice - uniswapPrice;

    return priceDiff >= this.minProfitThreshold;
  }

  private broadcastExecution(trade: IArbitrageTrade) {
    this.wsServer.clients.forEach((client: WebSocket) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(
          JSON.stringify({
            type: 'execution',
            data: trade,
          })
        );
      }
    });
  }

  private broadcastCompletion(trade: IArbitrageTrade) {
    this.wsServer.clients.forEach((client: WebSocket) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(
          JSON.stringify({
            type: 'completion',
            data: trade,
          })
        );
      }
    });
  }

  private broadcastError(error: Error) {
    this.wsServer.clients.forEach((client: WebSocket) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(
          JSON.stringify({
            type: 'error',
            error: error.message,
          })
        );
      }
    });
  }

  public getProvider(): ethers.JsonRpcProvider {
    return this.provider;
  }
}
