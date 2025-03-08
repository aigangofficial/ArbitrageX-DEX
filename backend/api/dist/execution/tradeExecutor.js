"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.TradeExecutor = exports.ExecutionMode = void 0;
const ethers_1 = require("ethers");
const config_1 = require("../api/config");
const logger_1 = require("../api/utils/logger");
const gasOptimizer_1 = __importDefault(require("./gasOptimizer"));
const executionModeService_1 = __importDefault(require("../services/executionModeService"));
var ExecutionMode;
(function (ExecutionMode) {
    ExecutionMode["MAINNET"] = "mainnet";
    ExecutionMode["FORK"] = "fork";
})(ExecutionMode || (exports.ExecutionMode = ExecutionMode = {}));
const ROUTER_ABI = [
    'function getAmountsOut(uint256 amountIn, address[] calldata path) external view returns (uint256[] memory amounts)',
    'function swapExactTokensForTokens(uint256 amountIn, uint256 amountOutMin, address[] calldata path, address to, uint256 deadline) external returns (uint256[] memory amounts)',
    'function factory() external view returns (address)',
    'function WETH() external view returns (address)',
];
const FACTORY_ABI = [
    'function getPair(address tokenA, address tokenB) external view returns (address pair)',
    'function allPairs(uint256) external view returns (address pair)',
    'function allPairsLength() external view returns (uint256)',
    'function feeTo() external view returns (address)',
    'function feeToSetter() external view returns (address)',
    'function createPair(address tokenA, address tokenB) external returns (address pair)',
];
const PAIR_ABI = [
    'function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast)',
    'function token0() external view returns (address)',
    'function token1() external view returns (address)',
    'function price0CumulativeLast() external view returns (uint256)',
    'function price1CumulativeLast() external view returns (uint256)',
];
const AAVE_POOL_ABI = [
    'function FLASHLOAN_PREMIUM_TOTAL() view returns (uint256)',
    'function FLASHLOAN_PREMIUM_TO_PROTOCOL() view returns (uint256)',
    'function getReserveData(address) view returns ((uint256,uint128,uint128,uint128,uint128,uint128,uint40,address,address,address,address,uint8))',
];
const FLASH_LOAN_FEE = 0.0009;
const DEFAULT_SLIPPAGE = 0.005;
const MIN_PROFIT_THRESHOLD = 0.001;
const QUICKSWAP_FACTORY = '0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32';
const SUSHISWAP_FACTORY = '0xc35DADB65012eC5796536bD9864eD8773aBc74C4';
class TradeExecutor {
    constructor(provider, quickswapRouter, sushiswapRouter, aavePool) {
        this.provider = provider;
        this.quickswapRouter = quickswapRouter;
        this.sushiswapRouter = sushiswapRouter;
        this.aavePool = aavePool;
        this.gasOptimizer = new gasOptimizer_1.default();
        this.isExecuting = false;
        this.executionModeService = executionModeService_1.default.getInstance();
        this.executionModeService.on('modeChanged', (data) => {
            logger_1.logger.info(`TradeExecutor received mode change to ${data.mode}`);
        });
    }
    getExecutionMode() {
        return this.executionModeService.getMode();
    }
    async simulateArbitrage(tokenA, tokenB, amount, route) {
        logger_1.logger.info(`Simulating arbitrage in ${this.getExecutionMode()} mode`);
        try {
            if (this.getExecutionMode() === ExecutionMode.FORK) {
                logger_1.logger.info('Running in FORK mode - using simulated gas prices and optimistic estimates');
                const mockAmount = ethers_1.ethers.parseEther(amount);
                const mockGasCost = ethers_1.ethers.parseEther("0.01");
                const mockProfit = ethers_1.ethers.parseEther("0.05");
                const mockNetProfit = ethers_1.ethers.parseEther("0.04");
                return {
                    expectedProfit: mockProfit.toString(),
                    gasCost: mockGasCost.toString(),
                    netProfit: mockNetProfit.toString(),
                    route: route,
                    priceImpact: 0.1,
                    flashLoanFee: ethers_1.ethers.parseEther("0.0009").toString(),
                    slippage: 0.005,
                    timestamp: new Date()
                };
            }
            logger_1.logger.info('Starting arbitrage simulation with real market data', {
                tokenA,
                tokenB,
                amount,
                route,
            });
            const firstDexData = await this.getDexQuote(route === 'QUICKSWAP_TO_SUSHI' ? 'QUICKSWAP' : 'SUSHISWAP', tokenA, tokenB, ethers_1.ethers.parseEther(amount));
            const secondDexData = await this.getDexQuote(route === 'QUICKSWAP_TO_SUSHI' ? 'SUSHISWAP' : 'QUICKSWAP', tokenA, tokenB, ethers_1.ethers.parseEther(amount));
            const priceImpact = this.calculateRealPriceImpact(firstDexData, secondDexData);
            const slippage = this.calculateRealSlippage({ reserve0: firstDexData.reserve0, reserve1: firstDexData.reserve1 }, { reserve0: secondDexData.reserve0, reserve1: secondDexData.reserve1 }, amount);
            const estimatedGas = await this.estimateRealGasUsage(tokenA, tokenB, amount, route);
            const gasPrice = await this.gasOptimizer.getOptimalGasPrice();
            const gasCost = (estimatedGas * Number(gasPrice.toString())).toString();
            const amountInWei = ethers_1.ethers.parseEther(amount);
            const flashLoanFeePercentage = 0.0009;
            const flashLoanFee = ethers_1.ethers.parseEther((parseFloat(amount) * flashLoanFeePercentage).toString()).toString();
            const expectedProfit = (secondDexData.amountOut - firstDexData.amountOut).toString();
            const profitNum = parseFloat(ethers_1.ethers.formatEther(expectedProfit));
            const gasCostNum = parseFloat(ethers_1.ethers.formatEther(gasCost));
            const flashLoanFeeNum = parseFloat(ethers_1.ethers.formatEther(flashLoanFee));
            const netProfitNum = profitNum - gasCostNum - flashLoanFeeNum;
            const netProfit = ethers_1.ethers.parseEther(netProfitNum.toString()).toString();
            return {
                expectedProfit,
                gasCost,
                netProfit,
                route,
                priceImpact,
                flashLoanFee,
                slippage,
                timestamp: new Date(),
            };
        }
        catch (error) {
            logger_1.logger.error('Arbitrage simulation failed:', error);
            throw error;
        }
    }
    async getDexQuote(dex, tokenA, tokenB, amountIn) {
        try {
            const router = dex === 'QUICKSWAP' ? this.quickswapRouter : this.sushiswapRouter;
            const factoryAddress = dex === 'QUICKSWAP' ? QUICKSWAP_FACTORY : SUSHISWAP_FACTORY;
            const factory = new ethers_1.ethers.Contract(factoryAddress, FACTORY_ABI, this.provider);
            const pairAddress = await factory.getPair(tokenA, tokenB);
            if (pairAddress === ethers_1.ethers.ZeroAddress) {
                throw new Error(`No liquidity pair exists for ${dex}`);
            }
            const pair = new ethers_1.ethers.Contract(pairAddress, PAIR_ABI, this.provider);
            const [reserve0, reserve1] = await pair.getReserves();
            const token0 = await pair.token0();
            const [reserveA, reserveB] = token0.toLowerCase() === tokenA.toLowerCase() ? [reserve0, reserve1] : [reserve1, reserve0];
            const path = [tokenA, tokenB];
            const amounts = await router.getAmountsOut(amountIn, path);
            return {
                reserve0: BigInt(reserveA),
                reserve1: BigInt(reserveB),
                amountOut: amounts[1],
            };
        }
        catch (error) {
            logger_1.logger.error(`Failed to get quote from ${dex}:`, error);
            throw error;
        }
    }
    calculateRealSlippage(firstDexLiquidity, secondDexLiquidity, amount) {
        const amountIn = ethers_1.ethers.parseEther(amount);
        const firstPoolDepth = Number(firstDexLiquidity.reserve0) + Number(firstDexLiquidity.reserve1);
        const secondPoolDepth = Number(secondDexLiquidity.reserve0) + Number(secondDexLiquidity.reserve1);
        const firstImpact = (Number(amountIn) / firstPoolDepth) * 100;
        const secondImpact = (Number(amountIn) / secondPoolDepth) * 100;
        return Math.max(firstImpact, secondImpact) + 0.5;
    }
    async estimateRealGasUsage(tokenA, tokenB, amount, route) {
        try {
            const estimatedGas = await this.provider.estimateGas({
                to: config_1.config.contracts.aavePool,
                data: '0x',
            });
            return Number(estimatedGas) * 2;
        }
        catch (error) {
            logger_1.logger.error('Gas estimation failed:', error);
            return 500000;
        }
    }
    calculateRealPriceImpact(firstDexData, secondDexData) {
        const firstPrice = Number(firstDexData.outputAmount);
        const secondPrice = Number(secondDexData.outputAmount);
        const priceImpact = ((firstPrice - secondPrice) * 10000) / firstPrice;
        return priceImpact / 100;
    }
    getAmountOut(amountIn, reserveIn, reserveOut) {
        if (reserveIn <= 0 || reserveOut <= 0) {
            throw new Error('Invalid reserves');
        }
        const amountInWithFee = amountIn * 997;
        const numerator = amountInWithFee * reserveOut;
        const denominator = reserveIn * 1000 + amountInWithFee;
        return Math.floor(numerator / denominator);
    }
    async executeArbitrage(params) {
        if (this.isExecuting) {
            logger_1.logger.warn('Already executing a trade');
            return false;
        }
        this.isExecuting = true;
        try {
            logger_1.logger.info(`Executing arbitrage in ${this.getExecutionMode()} mode`);
            if (this.getExecutionMode() === ExecutionMode.FORK) {
                logger_1.logger.info('Running in fork mode - simulating execution only');
                await new Promise(resolve => setTimeout(resolve, 2000));
                logger_1.logger.info('Simulated trade execution completed successfully');
                this.isExecuting = false;
                return true;
            }
            const gasCost = await this.estimateGasCost(params.buyDex, params.sellDex, params.tokenA, params.tokenB);
            const profitAfterGas = params.expectedProfit - gasCost;
            if (profitAfterGas <= 0) {
                logger_1.logger.info('Trade not profitable after gas costs');
                return false;
            }
            const flashLoanTx = await this.aavePool.flashLoan(this.quickswapRouter.address, [params.tokenA], [params.amount], 0, '0x');
            await flashLoanTx.wait();
            logger_1.logger.info('Arbitrage trade executed successfully');
            this.isExecuting = false;
            return true;
        }
        catch (error) {
            logger_1.logger.error('Error executing arbitrage:', error);
            this.isExecuting = false;
            return false;
        }
    }
    async estimateGasCost(buyDex, sellDex, tokenA, tokenB) {
        try {
            const gasPrice = await this.gasOptimizer.getOptimalGasPrice();
            const buyGas = await this.estimateTradeGas(buyDex, tokenA, tokenB);
            const sellGas = await this.estimateTradeGas(sellDex, tokenB, tokenA);
            const flashLoanGas = BigInt(100000);
            const totalGas = buyGas + sellGas + flashLoanGas;
            const gasCostWei = totalGas * gasPrice;
            return (Number(gasCostWei) / 1e18) * 100;
        }
        catch (error) {
            logger_1.logger.error('Failed to estimate gas cost:', error);
            return Infinity;
        }
    }
    async estimateTradeGas(dex, tokenIn, tokenOut) {
        const router = dex === 'QUICKSWAP' ? this.quickswapRouter : this.sushiswapRouter;
        try {
            const gasEstimate = await router.estimateGas.swapExactTokensForTokens(ethers_1.ethers.parseEther('1'), BigInt(0), [tokenIn, tokenOut], router.address, Math.floor(Date.now() / 1000) + 300);
            return gasEstimate;
        }
        catch (error) {
            logger_1.logger.error(`Failed to estimate gas for ${dex} trade:`, error);
            return BigInt(200000);
        }
    }
}
exports.TradeExecutor = TradeExecutor;
exports.default = TradeExecutor;
//# sourceMappingURL=tradeExecutor.js.map