import { ethers } from 'ethers';
import { config } from '../api/config';
import { logger } from '../api/utils/logger';
import GasOptimizer from './gasOptimizer';

// Real DEX Router ABIs - only the functions we need
const ROUTER_ABI = [
  'function getAmountsOut(uint256 amountIn, address[] calldata path) external view returns (uint256[] memory amounts)',
  'function swapExactTokensForTokens(uint256 amountIn, uint256 amountOutMin, address[] calldata path, address to, uint256 deadline) external returns (uint256[] memory amounts)',
  'function factory() external view returns (address)',
  'function WETH() external view returns (address)',
];

// Factory ABI for getting pair info
const FACTORY_ABI = [
  'function getPair(address tokenA, address tokenB) external view returns (address pair)',
  'function allPairs(uint256) external view returns (address pair)',
  'function allPairsLength() external view returns (uint256)',
  'function feeTo() external view returns (address)',
  'function feeToSetter() external view returns (address)',
  'function createPair(address tokenA, address tokenB) external returns (address pair)',
];

// Pair ABI for getting reserves
const PAIR_ABI = [
  'function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast)',
  'function token0() external view returns (address)',
  'function token1() external view returns (address)',
  'function price0CumulativeLast() external view returns (uint256)',
  'function price1CumulativeLast() external view returns (uint256)',
];

// Real Aave V3 Pool ABI - only the functions we need for simulation
const AAVE_POOL_ABI = [
  'function FLASHLOAN_PREMIUM_TOTAL() view returns (uint256)',
  'function FLASHLOAN_PREMIUM_TO_PROTOCOL() view returns (uint256)',
  'function getReserveData(address) view returns ((uint256,uint128,uint128,uint128,uint128,uint128,uint40,address,address,address,address,uint8))',
];

interface SimulatedTradeResult {
  expectedProfit: string;
  gasCost: string;
  netProfit: string;
  route: string;
  priceImpact: number;
  flashLoanFee: string;
  slippage: number;
  timestamp: Date;
}

const FLASH_LOAN_FEE = 0.0009; // Aave V3 charges 0.09%
const DEFAULT_SLIPPAGE = 0.005; // 0.5% default slippage
const MIN_PROFIT_THRESHOLD = 0.001; // 0.1% minimum profit after all fees

// Hardcoded factory addresses for Polygon Amoy testnet
const QUICKSWAP_FACTORY = '0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32';
const SUSHISWAP_FACTORY = '0xc35DADB65012eC5796536bD9864eD8773aBc74C4';

export type ArbitrageRoute = 'QUICKSWAP_TO_SUSHI' | 'SUSHI_TO_QUICKSWAP';

interface DexQuote {
  reserve0: bigint;
  reserve1: bigint;
  amountOut: bigint;
}

interface IDEXRouter {
  estimateGas: {
    swapExactTokensForTokens(
      amountIn: bigint,
      amountOutMin: bigint,
      path: string[],
      to: string,
      deadline: number
    ): Promise<bigint>;
  };
  getAmountsOut(amountIn: bigint, path: string[]): Promise<bigint[]>;
  address: string;
}

export class TradeExecutor {
  private provider: ethers.Provider;
  private gasOptimizer: GasOptimizer;
  private quickswapRouter: IDEXRouter;
  private sushiswapRouter: IDEXRouter;
  private aavePool: any;
  private isExecuting: boolean;

  constructor(
    provider: ethers.Provider,
    quickswapRouter: IDEXRouter,
    sushiswapRouter: IDEXRouter,
    aavePool: any
  ) {
    this.provider = provider;
    this.gasOptimizer = new GasOptimizer();
    this.isExecuting = false;
    this.quickswapRouter = quickswapRouter;
    this.sushiswapRouter = sushiswapRouter;
    this.aavePool = aavePool;
  }

  public async simulateArbitrage(
    tokenA: string,
    tokenB: string,
    amount: string,
    route: ArbitrageRoute
  ): Promise<SimulatedTradeResult> {
    try {
      logger.info('Starting arbitrage simulation with real market data', {
        tokenA,
        tokenB,
        amount,
        route,
      });

      // Get quotes from both DEXes
      const firstDexData = await this.getDexQuote(
        route === 'QUICKSWAP_TO_SUSHI' ? 'QUICKSWAP' : 'SUSHISWAP',
        tokenA,
        tokenB,
        ethers.parseEther(amount)
      );

      const secondDexData = await this.getDexQuote(
        route === 'QUICKSWAP_TO_SUSHI' ? 'SUSHISWAP' : 'QUICKSWAP',
        tokenA,
        tokenB,
        ethers.parseEther(amount)
      );

      // Calculate price impact and slippage
      const priceImpact = this.calculateRealPriceImpact(firstDexData, secondDexData);
      const slippage = this.calculateRealSlippage(
        { reserve0: firstDexData.reserve0, reserve1: firstDexData.reserve1 },
        { reserve0: secondDexData.reserve0, reserve1: secondDexData.reserve1 },
        amount
      );

      // Estimate gas cost
      const estimatedGas = await this.estimateRealGasUsage(tokenA, tokenB, amount, route);
      const gasPrice = await this.gasOptimizer.getOptimalGasPrice();
      const gasCost = (estimatedGas * gasPrice).toString();

      // Calculate flash loan fee (0.09% on Aave V3)
      const amountInWei = ethers.parseEther(amount);
      const flashLoanFee = (amountInWei * BigInt(9)) / BigInt(10000);

      // Calculate expected profit
      const expectedProfit = (secondDexData.amountOut - firstDexData.amountOut).toString();
      const netProfit = (BigInt(expectedProfit) - BigInt(gasCost) - flashLoanFee).toString();

      return {
        expectedProfit,
        gasCost,
        netProfit,
        route,
        priceImpact,
        flashLoanFee: flashLoanFee.toString(),
        slippage,
        timestamp: new Date(),
      };
    } catch (error) {
      logger.error('Arbitrage simulation failed:', error);
      throw error;
    }
  }

  async getDexQuote(
    dex: string,
    tokenA: string,
    tokenB: string,
    amountIn: bigint
  ): Promise<DexQuote> {
    try {
      // Use the appropriate router contract
      const router = dex === 'QUICKSWAP' ? this.quickswapRouter : this.sushiswapRouter;

      // Get factory address
      const factoryAddress = dex === 'QUICKSWAP' ? QUICKSWAP_FACTORY : SUSHISWAP_FACTORY;

      // Create factory contract instance
      const factory = new ethers.Contract(factoryAddress, FACTORY_ABI, this.provider);

      // Get pair address
      const pairAddress = await factory.getPair(tokenA, tokenB);

      if (pairAddress === ethers.ZeroAddress) {
        throw new Error(`No liquidity pair exists for ${dex}`);
      }

      // Create pair contract instance
      const pair = new ethers.Contract(pairAddress, PAIR_ABI, this.provider);

      // Get reserves and token ordering
      const [reserve0, reserve1] = await pair.getReserves();
      const token0 = await pair.token0();

      // Order reserves based on token order
      const [reserveA, reserveB] =
        token0.toLowerCase() === tokenA.toLowerCase() ? [reserve0, reserve1] : [reserve1, reserve0];

      // Get amounts out
      const path = [tokenA, tokenB];
      const amounts = await router.getAmountsOut(amountIn, path);

      return {
        reserve0: BigInt(reserveA),
        reserve1: BigInt(reserveB),
        amountOut: amounts[1],
      };
    } catch (error) {
      logger.error(`Failed to get quote from ${dex}:`, error);
      throw error;
    }
  }

  private calculateRealSlippage(
    firstDexLiquidity: any,
    secondDexLiquidity: any,
    amount: string
  ): number {
    const amountIn = ethers.parseEther(amount);

    // Calculate pool depths using Number for floating point math
    const firstPoolDepth = Number(firstDexLiquidity.reserve0) + Number(firstDexLiquidity.reserve1);
    const secondPoolDepth =
      Number(secondDexLiquidity.reserve0) + Number(secondDexLiquidity.reserve1);

    // Calculate impact percentage
    const firstImpact = (Number(amountIn) / firstPoolDepth) * 100;
    const secondImpact = (Number(amountIn) / secondPoolDepth) * 100;

    return Math.max(firstImpact, secondImpact) + 0.5; // Add 0.5% buffer
  }

  private async estimateRealGasUsage(
    tokenA: string,
    tokenB: string,
    amount: string,
    route: string
  ): Promise<bigint> {
    try {
      // Get base gas estimate from provider
      const estimatedGas = await this.provider.estimateGas({
        to: config.contracts.aavePool,
        data: '0x',
      });

      // Add buffer for flash loan operations
      return estimatedGas * BigInt(2); // 2x buffer for safety
    } catch (error) {
      logger.error('Gas estimation failed:', error);
      // Return conservative estimate if estimation fails
      return BigInt(500000); // 500k gas units as fallback
    }
  }

  private calculateRealPriceImpact(firstDexData: any, secondDexData: any): number {
    const firstPrice = BigInt(firstDexData.outputAmount);
    const secondPrice = BigInt(secondDexData.outputAmount);

    // Calculate real price impact as the difference between expected and actual output
    const priceImpact = ((firstPrice - secondPrice) * BigInt(10000)) / firstPrice;
    return Number(priceImpact) / 100;
  }

  // Helper function to calculate amount out based on reserves
  private getAmountOut(amountIn: bigint, reserveIn: bigint, reserveOut: bigint): bigint {
    if (reserveIn <= 0n || reserveOut <= 0n) {
      throw new Error('Invalid reserves');
    }

    const amountInWithFee = amountIn * 997n;
    const numerator = amountInWithFee * reserveOut;
    const denominator = reserveIn * 1000n + amountInWithFee;

    return numerator / denominator;
  }

  public async executeArbitrage(params: {
    buyDex: string;
    sellDex: string;
    tokenA: string;
    tokenB: string;
    amount: bigint;
    expectedProfit: number;
  }): Promise<boolean> {
    if (this.isExecuting) {
      logger.warn('Already executing a trade');
      return false;
    }

    this.isExecuting = true;
    try {
      // Validate the trade parameters
      const gasCost = await this.estimateGasCost(
        params.buyDex,
        params.sellDex,
        params.tokenA,
        params.tokenB
      );

      const profitAfterGas = params.expectedProfit - gasCost;
      if (profitAfterGas <= 0) {
        logger.info('Trade not profitable after gas costs');
        return false;
      }

      // Execute the flash loan and trades
      const flashLoanTx = await this.aavePool.flashLoan(
        this.quickswapRouter.address,
        [params.tokenA],
        [params.amount],
        0, // referralCode
        '0x' // params
      );

      await flashLoanTx.wait();
      logger.info('Arbitrage trade executed successfully');
      return true;
    } catch (error) {
      logger.error('Failed to execute arbitrage:', error);
      return false;
    } finally {
      this.isExecuting = false;
    }
  }

  public async estimateGasCost(
    buyDex: string,
    sellDex: string,
    tokenA: string,
    tokenB: string
  ): Promise<number> {
    try {
      // Get current gas price
      const gasPrice = await this.gasOptimizer.getOptimalGasPrice();

      // Estimate gas for both trades
      const buyGas = await this.estimateTradeGas(buyDex, tokenA, tokenB);
      const sellGas = await this.estimateTradeGas(sellDex, tokenB, tokenA);

      // Add flash loan gas cost
      const flashLoanGas = BigInt(100000); // Base estimate for flash loan

      // Calculate total gas cost in ETH
      const totalGas = buyGas + sellGas + flashLoanGas;
      const gasCostWei = totalGas * gasPrice;

      // Convert to percentage of trade value for comparison with profit
      return (Number(gasCostWei) / 1e18) * 100;
    } catch (error) {
      logger.error('Failed to estimate gas cost:', error);
      return Infinity; // Return high cost to prevent trade
    }
  }

  private async estimateTradeGas(dex: string, tokenIn: string, tokenOut: string): Promise<bigint> {
    const router = dex === 'QUICKSWAP' ? this.quickswapRouter : this.sushiswapRouter;
    try {
      const gasEstimate = await router.estimateGas.swapExactTokensForTokens(
        ethers.parseEther('1'), // 1 token as test amount
        BigInt(0), // amountOutMin
        [tokenIn, tokenOut],
        router.address,
        Math.floor(Date.now() / 1000) + 300 // 5 minute deadline
      );
      return gasEstimate;
    } catch (error) {
      logger.error(`Failed to estimate gas for ${dex} trade:`, error);
      return BigInt(200000); // Conservative estimate
    }
  }
}

export default TradeExecutor;
