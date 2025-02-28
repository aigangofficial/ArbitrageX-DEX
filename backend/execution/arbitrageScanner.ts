import { ethers } from 'ethers';
import { EventEmitter } from 'events';
import { Logger } from 'winston';
import { IDEXRouter } from './interfaces/IDEXRouter';
import { ArbitrageOpportunity } from '../ai/interfaces/simulation';
import { Provider } from '@ethersproject/abstract-provider';
import { Contract } from '@ethersproject/contracts';

// Router ABI for DEX interactions
const ROUTER_ABI = [
  'function getAmountsOut(uint amountIn, address[] memory path) view returns (uint[] memory amounts)',
  'function factory() external pure returns (address)',
  'function WETH() external pure returns (address)',
  'function swapExactTokensForTokens(uint amountIn, uint amountOutMin, address[] calldata path, address to, uint deadline) external returns (uint[] memory amounts)',
];

// Factory ABI for getting pair info
const FACTORY_ABI = [
  'function getPair(address tokenA, address tokenB) external view returns (address pair)',
];

// Pair ABI for getting reserves
const PAIR_ABI = [
  'function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast)',
  'function token0() external view returns (address)',
  'function token1() external view returns (address)',
];

interface PriceData {
  dex: string;
  tokenA: string;
  tokenB: string;
  price: number;
  liquidity: string;
  timestamp: number;
  blockNumber: number;
}

interface TokenPair {
  tokenA: string;
  tokenB: string;
}

interface ScannerConfig {
  minProfitThreshold: number;
  minNetProfit: number;
  gasLimit: number;
  scanInterval: number;
  maxGasPrice: number;
  gasMultiplier: number;
}

export class ArbitrageScanner extends EventEmitter {
  private uniswapRouter: IDEXRouter;
  private sushiswapRouter: IDEXRouter;
  private isScanning: boolean = false;
  private scanInterval: NodeJS.Timeout | null = null;
  private tokenPairs: TokenPair[];
  private config: ScannerConfig;
  private lastGasPrice: bigint = 0n;
  private logger: Logger;

  constructor(
    private readonly provider: Provider,
    private readonly uniswapRouterAddress: string,
    private readonly sushiswapRouterAddress: string,
    config: ScannerConfig,
    tokenPairs: TokenPair[],
    logger: Logger
  ) {
    super();
    this.uniswapRouter = new Contract(uniswapRouterAddress, ROUTER_ABI, provider) as unknown as IDEXRouter;
    this.sushiswapRouter = new Contract(sushiswapRouterAddress, ROUTER_ABI, provider) as unknown as IDEXRouter;
    this.tokenPairs = tokenPairs;
    this.config = config;
    this.logger = logger;
  }

  private async getAmountsOut(tokenIn: string, tokenOut: string, amount: bigint): Promise<bigint[]> {
    try {
      const router = this.uniswapRouter;
      return await router.getAmountsOut(amount, [tokenIn, tokenOut]);
    } catch (error) {
      this.logger.error('Error getting amounts out:', error);
      throw error;
    }
  }

  start(): void {
    if (this.isScanning) {
      this.logger.warn('Scanner is already running');
      return;
    }

    this.isScanning = true;
    this.scanInterval = setInterval(() => this.scanMarkets(), this.config.scanInterval);
    this.logger.info('Started scanning for arbitrage opportunities');
  }

  stop(): void {
    if (!this.isScanning) {
      this.logger.warn('Scanner is not running');
      return;
    }

    if (this.scanInterval) {
      clearInterval(this.scanInterval);
      this.scanInterval = null;
    }

    this.isScanning = false;
    this.logger.info('Stopped scanning for arbitrage opportunities');
  }

  private async scanMarkets(): Promise<void> {
    try {
      // Get current gas price
      const gasPrice = await this.provider.getFeeData();
      if (!gasPrice.gasPrice) {
        this.logger.error('Failed to get gas price');
        return;
      }

      this.lastGasPrice = gasPrice.gasPrice;

      // Scan each token pair
      for (const pair of this.tokenPairs) {
        await this.scanPair(pair.tokenA, pair.tokenB);
      }
    } catch (error) {
      this.logger.error('Error scanning markets:', error);
    }
  }

  private async scanPair(tokenA: string, tokenB: string): Promise<void> {
    try {
      // Get amounts out from both DEXes
      const amount = ethers.parseEther('1');
      const [uniswapAmounts, sushiswapAmounts] = await Promise.all([
        this.uniswapRouter.getAmountsOut(amount, [tokenA, tokenB]),
        this.sushiswapRouter.getAmountsOut(amount, [tokenA, tokenB]),
      ]);

      // Calculate price difference
      const uniswapPrice = Number(ethers.formatEther(uniswapAmounts[1]));
      const sushiswapPrice = Number(ethers.formatEther(sushiswapAmounts[1]));
      const priceDiff = Math.abs(uniswapPrice - sushiswapPrice);

      // Check if price difference is above threshold
      if (priceDiff > this.config.minProfitThreshold) {
        this.emit('arbitrageOpportunity', {
          tokenA,
          tokenB,
          uniswapPrice,
          sushiswapPrice,
          priceDiff,
          timestamp: Date.now(),
        });
      }
    } catch (error) {
      this.logger.error(`Error scanning pair ${tokenA}/${tokenB}:`, error);
    }
  }

  async analyzePool(pool: { tokenA: string; tokenB: string; }): Promise<ArbitrageOpportunity | null> {
    try {
      const amount = await this.calculateOptimalAmount(pool);
      const expectedProfit = await this.calculateExpectedProfit(pool, amount);
      
      if (expectedProfit > 0n) {
        return this.createArbitrageOpportunity(
          pool.tokenA,
          pool.tokenB,
          amount,
          expectedProfit,
          `${pool.tokenA},${pool.tokenB}`
        );
      }
      
      return null;
    } catch (error) {
      this.logger.error('Failed to analyze pool:', error);
      return null;
    }
  }

  async estimateTradeGas(opportunity: ArbitrageOpportunity): Promise<bigint> {
    try {
      // Base gas cost for a typical DEX swap
      const baseGas = 150000n;
      
      // Additional gas for complex routes
      const routeComplexity = opportunity.route.split(',').length - 1;
      const routeGas = BigInt(routeComplexity * 50000);
      
      // Total estimated gas
      return baseGas + routeGas;
    } catch (error) {
      this.logger.error('Failed to estimate trade gas:', error);
      return 250000n; // Default fallback gas estimate
    }
  }

  private createArbitrageOpportunity(
    tokenA: string,
    tokenB: string,
    amount: bigint,
    expectedProfit: bigint,
    route: string
  ): ArbitrageOpportunity {
    return {
      tokenA,
      tokenB,
      amount,
      expectedProfit,
      route,
      timestamp: Date.now()
    };
  }

  private async calculateOptimalAmount(pool: { tokenA: string; tokenB: string; }): Promise<bigint> {
    try {
      // Start with a base amount
      const baseAmount = ethers.parseEther('1');
      
      // Get amounts out from both DEXes
      const [uniswapAmounts, sushiswapAmounts] = await Promise.all([
        this.uniswapRouter.getAmountsOut(baseAmount, [pool.tokenA, pool.tokenB]),
        this.sushiswapRouter.getAmountsOut(baseAmount, [pool.tokenA, pool.tokenB])
      ]);
      
      // Calculate optimal amount based on price difference
      const priceDiff = Number(ethers.formatEther(uniswapAmounts[1])) - 
                      Number(ethers.formatEther(sushiswapAmounts[1]));
      
      // Adjust amount based on price difference
      const adjustmentFactor = Math.min(Math.abs(priceDiff) * 2, 5);
      return baseAmount * BigInt(Math.floor(adjustmentFactor));
      
    } catch (error) {
      this.logger.error('Failed to calculate optimal amount:', error);
      return ethers.parseEther('1'); // Fallback to base amount
    }
  }

  private async calculateExpectedProfit(
    pool: { tokenA: string; tokenB: string; },
    amount: bigint
  ): Promise<bigint> {
    try {
      // Get amounts out from both DEXes
      const [uniswapAmounts, sushiswapAmounts] = await Promise.all([
        this.uniswapRouter.getAmountsOut(amount, [pool.tokenA, pool.tokenB]),
        this.sushiswapRouter.getAmountsOut(amount, [pool.tokenA, pool.tokenB])
      ]);
      
      // Calculate profit as the difference between the best output and input
      const bestOutput = uniswapAmounts[1] > sushiswapAmounts[1] ? 
                       uniswapAmounts[1] : sushiswapAmounts[1];
      
      return bestOutput - amount;
      
    } catch (error) {
      this.logger.error('Failed to calculate expected profit:', error);
      return 0n;
    }
  }
}

export default ArbitrageScanner;
