import { ethers } from 'ethers';
import { EventEmitter } from 'events';
import { Logger } from 'winston';
import { IDEXRouter } from './interfaces/IDEXRouter';
import { ArbitrageOpportunity } from '../ai/interfaces/simulation';
import { Provider } from '@ethersproject/abstract-provider';
import { Contract } from '@ethersproject/contracts';
import fs from 'fs';
import path from 'path';
import ExecutionModeService from '../services/executionModeService';
import { ExecutionMode } from './tradeExecutor';

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
  private lastGasPrice: number = 0;
  private logger: Logger;
  private executionModeService: ExecutionModeService;

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
    
    // Get the execution mode service
    this.executionModeService = ExecutionModeService.getInstance();
    
    // Listen for execution mode changes
    this.executionModeService.on('modeChanged', (data) => {
      this.logger.info(`ArbitrageScanner received mode change to ${data.mode}`);
      
      // Restart scanning with new mode if currently scanning
      if (this.isScanning) {
        this.stop();
        this.start();
      }
    });
  }

  // Get current execution mode
  public getExecutionMode(): ExecutionMode {
    return this.executionModeService.getMode();
  }

  private async getAmountsOut(tokenIn: string, tokenOut: string, amount: bigint): Promise<bigint[]> {
    try {
      const path = [tokenIn, tokenOut];
      const uniswapAmounts = await this.uniswapRouter.getAmountsOut(amount, path);
      const sushiswapAmounts = await this.sushiswapRouter.getAmountsOut(amount, path);
      return [uniswapAmounts[1], sushiswapAmounts[1]];
    } catch (error) {
      this.logger.error('Error getting amounts out:', error);
      return [0n, 0n];
    }
  }

  start(): void {
    if (this.isScanning) {
      this.logger.warn('Scanner is already running');
      return;
    }

    this.isScanning = true;
    this.logger.info(`Starting arbitrage scanner in ${this.getExecutionMode()} mode`);
    
    // Adjust scan interval based on execution mode
    const interval = this.getExecutionMode() === ExecutionMode.FORK ? 
      this.config.scanInterval * 2 : // Slower in fork mode
      this.config.scanInterval;
      
    this.scanInterval = setInterval(() => this.scanMarkets(), interval);
    this.scanMarkets(); // Initial scan
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
    this.logger.info('Stopped arbitrage scanner');
  }

  private async scanMarkets(): Promise<void> {
    try {
      this.logger.debug(`Scanning markets in ${this.getExecutionMode()} mode`);
      
      // In fork mode, we might want to simulate different market conditions
      if (this.getExecutionMode() === ExecutionMode.FORK) {
        this.logger.debug('Running in fork mode - simulating market conditions');
        // Add any fork-specific logic here
      }
      
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
      // Convert number to bigint for the expected profit calculation
      const amountBigInt = BigInt(amount);
      const expectedProfit = await this.calculateExpectedProfit(pool, amountBigInt);
      
      if (expectedProfit > 0n) {
        return this.createArbitrageOpportunity(
          pool.tokenA,
          pool.tokenB,
          amountBigInt,
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

  async estimateTradeGas(opportunity: ArbitrageOpportunity): Promise<number> {
    try {
      // Base gas cost for contract deployment
      const baseGas = 100000;
      
      // Add gas based on the complexity of the route
      // For simplicity, we'll use a fixed value based on the pair
      const pairComplexity = opportunity.pair.includes('WETH') ? 1.5 : 1;
      const routeComplexity = 2; // Default complexity factor
      
      const routeGas = routeComplexity * 50000;
      
      // Total gas estimate with a safety buffer
      return Math.floor(baseGas + routeGas * pairComplexity);
    } catch (error) {
      this.logger.error('Failed to estimate trade gas', { error });
      return 500000; // Conservative fallback
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
      pair: `${tokenA}-${tokenB}`,
      tokenA,
      tokenB,
      amount,
      expectedProfit,
      gasEstimate: 500000n,
      route,
      timestamp: Date.now()
    };
  }

  private async calculateOptimalAmount(pool: { tokenA: string; tokenB: string; }): Promise<number> {
    try {
      // Get base amount from configuration
      const baseAmount = 1000000; // 1 USDC with 6 decimals as example
      
      // Adjust based on pool liquidity and volatility
      const liquidity = await this.getLiquidityDepth(pool.tokenA, pool.tokenB);
      const volatility = await this.getVolatility(pool.tokenA, pool.tokenB);
      
      // Calculate adjustment factor (higher liquidity and lower volatility = higher amount)
      const liquidityFactor = Math.min(liquidity / 1000000, 10); // Cap at 10x
      const volatilityFactor = Math.max(1 - volatility, 0.1); // Minimum 0.1x
      
      const adjustmentFactor = liquidityFactor * volatilityFactor;
      
      // Apply adjustment to base amount
      return Math.floor(baseAmount * adjustmentFactor);
    } catch (error) {
      this.logger.error('Failed to calculate optimal amount', { error });
      return 1000000; // Conservative fallback of 1 USDC
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

  // Helper method to get liquidity depth for a token pair
  private async getLiquidityDepth(tokenA: string, tokenB: string): Promise<number> {
    try {
      // In a real implementation, this would query DEX contracts for reserves
      // For now, we'll return a mock value
      return 5000000; // Mock liquidity depth
    } catch (error) {
      this.logger.error('Failed to get liquidity depth', { error, tokenA, tokenB });
      return 1000000; // Conservative fallback
    }
  }

  // Helper method to get volatility for a token pair
  private async getVolatility(tokenA: string, tokenB: string): Promise<number> {
    try {
      // In a real implementation, this would calculate volatility from price history
      // For now, we'll return a mock value
      return 0.2; // 20% volatility (0-1 scale)
    } catch (error) {
      this.logger.error('Failed to get volatility', { error, tokenA, tokenB });
      return 0.5; // Conservative fallback (higher volatility)
    }
  }
}

export default ArbitrageScanner;
