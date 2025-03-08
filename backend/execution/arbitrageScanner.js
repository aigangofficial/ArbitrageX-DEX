'use strict';
Object.defineProperty(exports, '__esModule', { value: true });
exports.ArbitrageScanner = void 0;
const ethers_1 = require('ethers');
const events_1 = require('events');
const contracts_1 = require('@ethersproject/contracts');
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
class ArbitrageScanner extends events_1.EventEmitter {
  constructor(provider, uniswapRouterAddress, sushiswapRouterAddress, config, tokenPairs, logger) {
    super();
    this.provider = provider;
    this.uniswapRouterAddress = uniswapRouterAddress;
    this.sushiswapRouterAddress = sushiswapRouterAddress;
    this.isScanning = false;
    this.scanInterval = null;
    this.lastGasPrice = 0n;
    this.uniswapRouter = new contracts_1.Contract(uniswapRouterAddress, ROUTER_ABI, provider);
    this.sushiswapRouter = new contracts_1.Contract(sushiswapRouterAddress, ROUTER_ABI, provider);
    this.tokenPairs = tokenPairs;
    this.config = config;
    this.logger = logger;
  }
  async getAmountsOut(tokenIn, tokenOut, amount) {
    try {
      const router = this.uniswapRouter;
      return await router.getAmountsOut(amount, [tokenIn, tokenOut]);
    } catch (error) {
      this.logger.error('Error getting amounts out:', error);
      throw error;
    }
  }
  start() {
    if (this.isScanning) {
      this.logger.warn('Scanner is already running');
      return;
    }
    this.isScanning = true;
    this.scanInterval = setInterval(() => this.scanMarkets(), this.config.scanInterval);
    this.logger.info('Started scanning for arbitrage opportunities');
  }
  stop() {
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
  async scanMarkets() {
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
  async scanPair(tokenA, tokenB) {
    try {
      // Get amounts out from both DEXes
      const amount = ethers_1.ethers.parseEther('1');
      const [uniswapAmounts, sushiswapAmounts] = await Promise.all([
        this.uniswapRouter.getAmountsOut(amount, [tokenA, tokenB]),
        this.sushiswapRouter.getAmountsOut(amount, [tokenA, tokenB]),
      ]);
      // Calculate price difference
      const uniswapPrice = Number(ethers_1.ethers.formatEther(uniswapAmounts[1]));
      const sushiswapPrice = Number(ethers_1.ethers.formatEther(sushiswapAmounts[1]));
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
  async analyzePool(pool) {
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
  async estimateTradeGas(opportunity) {
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
  createArbitrageOpportunity(tokenA, tokenB, amount, expectedProfit, route) {
    return {
      tokenA,
      tokenB,
      amount,
      expectedProfit,
      route,
      timestamp: Date.now(),
    };
  }
  async calculateOptimalAmount(pool) {
    try {
      // Start with a base amount
      const baseAmount = ethers_1.ethers.parseEther('1');
      // Get amounts out from both DEXes
      const [uniswapAmounts, sushiswapAmounts] = await Promise.all([
        this.uniswapRouter.getAmountsOut(baseAmount, [pool.tokenA, pool.tokenB]),
        this.sushiswapRouter.getAmountsOut(baseAmount, [pool.tokenA, pool.tokenB]),
      ]);
      // Calculate optimal amount based on price difference
      const priceDiff =
        Number(ethers_1.ethers.formatEther(uniswapAmounts[1])) -
        Number(ethers_1.ethers.formatEther(sushiswapAmounts[1]));
      // Adjust amount based on price difference
      const adjustmentFactor = Math.min(Math.abs(priceDiff) * 2, 5);
      return baseAmount * BigInt(Math.floor(adjustmentFactor));
    } catch (error) {
      this.logger.error('Failed to calculate optimal amount:', error);
      return ethers_1.ethers.parseEther('1'); // Fallback to base amount
    }
  }
  async calculateExpectedProfit(pool, amount) {
    try {
      // Get amounts out from both DEXes
      const [uniswapAmounts, sushiswapAmounts] = await Promise.all([
        this.uniswapRouter.getAmountsOut(amount, [pool.tokenA, pool.tokenB]),
        this.sushiswapRouter.getAmountsOut(amount, [pool.tokenA, pool.tokenB]),
      ]);
      // Calculate profit as the difference between the best output and input
      const bestOutput =
        uniswapAmounts[1] > sushiswapAmounts[1] ? uniswapAmounts[1] : sushiswapAmounts[1];
      return bestOutput - amount;
    } catch (error) {
      this.logger.error('Failed to calculate expected profit:', error);
      return 0n;
    }
  }
}
exports.ArbitrageScanner = ArbitrageScanner;
exports.default = ArbitrageScanner;
//# sourceMappingURL=arbitrageScanner.js.map
