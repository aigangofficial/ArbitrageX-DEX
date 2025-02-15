import { ethers } from 'ethers';
import { WebSocket, WebSocketServer } from 'ws';
import { ArbitrageExecutor__factory } from '../../typechain-types';
import { AdaptiveRiskManager } from '../ai/risk_analyzer';
import { PriceFetcher } from '../services/priceFetcher';
import { IUniswapV2Router02 } from '../types/contracts';
import { ArbitrageOpportunity, PriceData } from '../types/trading';

export { PriceData }; // Export the PriceData type

export class ArbitrageScanner {
  protected readonly provider: ethers.JsonRpcProvider;
  private readonly wsServer: WebSocketServer;
  private readonly uniswapRouter: IUniswapV2Router02;
  private readonly sushiswapRouter: IUniswapV2Router02;
  private readonly flashLoanAddress: string;
  private readonly arbitrageExecutor: ArbitrageExecutor__factory;
  private readonly minProfitThreshold: bigint;
  private readonly wethAddress: string;
  private readonly priceFetcher: PriceFetcher;
  private readonly riskManager: AdaptiveRiskManager;
  private isScanning: boolean = false;
  private readonly scanInterval: number = 5000; // 5 seconds
  private readonly supportedTokens: string[];

  constructor(
    provider: ethers.JsonRpcProvider,
    wsServer: WebSocketServer,
    flashLoanAddress: string,
    uniswapRouterAddress: string,
    sushiswapRouterAddress: string,
    wethAddress: string
  ) {
    if (!ethers.isAddress(flashLoanAddress)) throw new Error('Invalid FlashLoan address');
    if (!ethers.isAddress(uniswapRouterAddress)) throw new Error('Invalid Uniswap address');
    if (!ethers.isAddress(sushiswapRouterAddress)) throw new Error('Invalid Sushiswap address');

    this.provider = provider;
    this.wsServer = wsServer;
    this.flashLoanAddress = flashLoanAddress;
    this.minProfitThreshold = ethers.parseEther('0.01'); // 0.01 ETH minimum profit
    this.wethAddress = wethAddress;
    this.priceFetcher = new PriceFetcher();
    this.riskManager = new AdaptiveRiskManager();

    this.uniswapRouter = new ethers.Contract(
      uniswapRouterAddress,
      [
        'function getAmountsOut(uint amountIn, address[] memory path) view returns (uint[] memory amounts)',
      ],
      provider
    ) as unknown as IUniswapV2Router02;

    this.sushiswapRouter = new ethers.Contract(
      sushiswapRouterAddress,
      [
        'function getAmountsOut(uint amountIn, address[] memory path) view returns (uint[] memory amounts)',
      ],
      provider
    ) as unknown as IUniswapV2Router02;

    this.arbitrageExecutor = ArbitrageExecutor__factory.connect(
      this.flashLoanAddress,
      this.provider
    );

    // Define supported tokens
    this.supportedTokens = [
      wethAddress, // WMATIC
      '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', // USDC
      '0xc2132D05D31c914a87C6611C10748AEb04B58e8F', // USDT
    ];
  }

  public getIsScanning(): boolean {
    return this.isScanning;
  }

  public async startScanning(): Promise<void> {
    if (this.isScanning) {
      console.log('Scanner is already running');
      return;
    }

    this.isScanning = true;
    console.log('Starting arbitrage scanner...');

    while (this.isScanning) {
      try {
        await this.scanForOpportunities();
        await new Promise(resolve => setTimeout(resolve, this.scanInterval));
      } catch (error) {
        console.error('Error in scanning loop:', error);
        // Broadcast error to WebSocket clients
        this.broadcastError(error instanceof Error ? error : new Error('Unknown error'));
      }
    }
  }

  public stopScanning(): void {
    this.isScanning = false;
    console.log('Stopping arbitrage scanner...');
  }

  private async scanForOpportunities(): Promise<void> {
    try {
      for (const tokenA of this.supportedTokens) {
        for (const tokenB of this.supportedTokens) {
          if (tokenA === tokenB) continue;

          const prices = await this.getPrices(tokenA, tokenB);
          if (this.isProfitable(prices)) {
            const opportunity = await this.calculateArbitrageOpportunity(tokenA, tokenB, prices);
            if (opportunity) {
              this.broadcastOpportunity(opportunity);
              await this.processArbitrageOpportunity(opportunity);
            }
          }
        }
      }
    } catch (error) {
      this.broadcastError(error as Error);
    }
  }

  private async calculateArbitrageOpportunity(
    tokenA: string,
    tokenB: string,
    prices: PriceData
  ): Promise<ArbitrageOpportunity | null> {
    const uniToSushiProfit = prices.sushiswapPrice - prices.uniswapPrice;
    const sushiToUniProfit = prices.uniswapPrice - prices.sushiswapPrice;

    if (uniToSushiProfit > this.minProfitThreshold) {
      return {
        tokenA,
        tokenB,
        amountIn: this.calculateOptimalTradeSize(prices.uniswapLiquidity),
        expectedProfit: uniToSushiProfit,
        route: 'UNIV2_TO_SUSHI',
        confidence: this.calculateConfidence(prices),
      };
    }

    if (sushiToUniProfit > this.minProfitThreshold) {
      return {
        tokenA,
        tokenB,
        amountIn: this.calculateOptimalTradeSize(prices.sushiswapLiquidity),
        expectedProfit: sushiToUniProfit,
        route: 'SUSHI_TO_UNIV2',
        confidence: this.calculateConfidence(prices),
      };
    }

    return null;
  }

  private calculateOptimalTradeSize(liquidity: bigint): bigint {
    // Use 30% of available liquidity as a safe default
    return (liquidity * BigInt(30)) / BigInt(100);
  }

  private calculateConfidence(prices: PriceData): number {
    // Calculate confidence based on liquidity and price stability
    const liquidityScore = Number(
      ((prices.uniswapLiquidity + prices.sushiswapLiquidity) * BigInt(100)) /
        (BigInt(2) * ethers.parseUnits('1000000', 18))
    );
    const priceScore =
      100 -
      Number(
        ((prices.uniswapPrice > prices.sushiswapPrice
          ? prices.uniswapPrice - prices.sushiswapPrice
          : prices.sushiswapPrice - prices.uniswapPrice) *
          BigInt(100)) /
          ((prices.uniswapPrice + prices.sushiswapPrice) / BigInt(2))
      );

    return Math.min(liquidityScore, priceScore) / 100;
  }

  protected async getPrices(tokenA: string, tokenB: string): Promise<PriceData> {
    const [uniswapResult, sushiswapResult] = await Promise.all([
      this.getUniswapPrice(tokenA, tokenB),
      this.getSushiswapPrice(tokenA, tokenB),
    ]);

    return {
      uniswapPrice: uniswapResult.price,
      sushiswapPrice: sushiswapResult.price,
      uniswapLiquidity: uniswapResult.liquidity,
      sushiswapLiquidity: sushiswapResult.liquidity,
    };
  }

  private async getUniswapPrice(
    tokenA: string,
    tokenB: string
  ): Promise<{ price: bigint; liquidity: bigint }> {
    const amountIn = ethers.parseUnits('1', 18);
    const amounts = await this.uniswapRouter.getAmountsOut(amountIn, [tokenA, tokenB]);
    return {
      price: amounts[1],
      liquidity: await this.getPoolLiquidity(this.uniswapRouter, tokenA, tokenB),
    };
  }

  private async getSushiswapPrice(
    tokenA: string,
    tokenB: string
  ): Promise<{ price: bigint; liquidity: bigint }> {
    const amountIn = ethers.parseUnits('1', 18);
    const amounts = await this.sushiswapRouter.getAmountsOut(amountIn, [tokenA, tokenB]);
    return {
      price: amounts[1],
      liquidity: await this.getPoolLiquidity(this.sushiswapRouter, tokenA, tokenB),
    };
  }

  private async getPoolLiquidity(
    router: IUniswapV2Router02,
    tokenA: string,
    tokenB: string
  ): Promise<bigint> {
    try {
      const factory = new ethers.Contract(
        await this.getFactoryAddress(router),
        ['function getPair(address, address) view returns (address)'],
        this.provider
      );
      const pairAddress = await factory.getPair(tokenA, tokenB);
      const pair = new ethers.Contract(
        pairAddress,
        ['function getReserves() view returns (uint112, uint112, uint32)'],
        this.provider
      );
      const [reserve0, reserve1] = await pair.getReserves();
      return reserve0 + reserve1;
    } catch (error) {
      console.error('Error getting pool liquidity:', error);
      return BigInt(0);
    }
  }

  private async getFactoryAddress(router: IUniswapV2Router02): Promise<string> {
    const routerContract = new ethers.Contract(
      await router.getAddress(),
      ['function factory() view returns (address)'],
      this.provider
    );
    return await routerContract.factory();
  }

  protected isProfitable(prices: PriceData): boolean {
    const priceDiff =
      prices.uniswapPrice > prices.sushiswapPrice
        ? prices.uniswapPrice - prices.sushiswapPrice
        : prices.sushiswapPrice - prices.uniswapPrice;

    return priceDiff > this.minProfitThreshold;
  }

  private async processArbitrageOpportunity(opportunity: ArbitrageOpportunity): Promise<void> {
    try {
      // Log opportunity details
      console.log('Arbitrage opportunity found:', {
        tokenA: opportunity.tokenA,
        tokenB: opportunity.tokenB,
        expectedProfit: ethers.formatUnits(opportunity.expectedProfit, 18),
        route: opportunity.route,
        confidence: opportunity.confidence,
      });
    } catch (error) {
      console.error('Error processing arbitrage opportunity:', error);
    }
  }

  private broadcastOpportunity(opportunity: ArbitrageOpportunity): void {
    this.wsServer.clients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(
          JSON.stringify({
            type: 'ARBITRAGE_OPPORTUNITY',
            data: {
              ...opportunity,
              amountIn: opportunity.amountIn.toString(),
              expectedProfit: opportunity.expectedProfit.toString(),
              timestamp: new Date().toISOString(),
            },
          })
        );
      }
    });
  }

  private broadcastError(error: Error): void {
    this.wsServer.clients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(
          JSON.stringify({
            type: 'ERROR',
            error: error.message,
            timestamp: new Date().toISOString(),
          })
        );
      }
    });
  }

  public getProvider(): ethers.JsonRpcProvider {
    return this.provider;
  }
}
