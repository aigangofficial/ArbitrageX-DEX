"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const dotenv = __importStar(require("dotenv"));
const path_1 = require("path");
dotenv.config({ path: (0, path_1.resolve)(__dirname, '../../.env.root') });
const ethers_1 = require("ethers");
const config_1 = require("../api/config");
const logger_1 = require("../api/utils/logger");
const tradeExecutor_1 = require("./tradeExecutor");
const ROUTER_ABI = [
    'function getAmountsOut(uint amountIn, address[] memory path) external view returns (uint[] memory amounts)',
    'function swapExactTokensForTokens(uint amountIn, uint amountOutMin, address[] calldata path, address to, uint deadline) external returns (uint[] memory amounts)',
];
const AAVE_POOL_ABI = [
    'function flashLoanSimple(address receiverAddress, address asset, uint256 amount, bytes calldata params, uint16 referralCode) external returns (bool)',
];
const FACTORY_ABI = [
    'function getPair(address tokenA, address tokenB) external view returns (address pair)',
    'function allPairs(uint) external view returns (address pair)',
    'function allPairsLength() external view returns (uint)',
];
const PAIR_ABI = [
    'function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast)',
    'function token0() external view returns (address)',
    'function token1() external view returns (address)',
];
logger_1.logger.info('Environment variables:', {
    NETWORK_RPC: process.env.NETWORK_RPC,
    NETWORK_NAME: process.env.NETWORK_NAME,
    CHAIN_ID: process.env.CHAIN_ID,
});
logger_1.logger.info('Using configuration:', {
    network: {
        rpc: config_1.config.network.rpc,
        name: config_1.config.network.name,
        chainId: config_1.config.network.chainId,
    },
    contracts: {
        uniswapRouter: config_1.config.contracts.uniswapRouter,
        sushiswapRouter: config_1.config.contracts.sushiswapRouter,
        wmatic: config_1.config.contracts.wmatic,
        usdt: config_1.config.contracts.usdt,
    },
});
async function validateNetwork() {
    try {
        const provider = new ethers_1.ethers.JsonRpcProvider(config_1.config.network.rpc);
        const network = await provider.getNetwork();
        logger_1.logger.info('Connected to network:', {
            name: network.name,
            chainId: network.chainId,
        });
        return true;
    }
    catch (error) {
        logger_1.logger.error('Network validation failed:', error);
        return false;
    }
}
async function validateContracts() {
    try {
        const provider = new ethers_1.ethers.JsonRpcProvider(config_1.config.network.rpc);
        const uniswapRouter = new ethers_1.ethers.Contract(config_1.config.contracts.uniswapRouter, ROUTER_ABI, provider);
        const sushiswapRouter = new ethers_1.ethers.Contract(config_1.config.contracts.sushiswapRouter, ROUTER_ABI, provider);
        const aavePool = new ethers_1.ethers.Contract(config_1.config.contracts.aavePool, AAVE_POOL_ABI, provider);
        const executor = new tradeExecutor_1.TradeExecutor(provider, uniswapRouter, sushiswapRouter, aavePool);
        const tokenA = config_1.config.contracts.weth;
        const tokenB = config_1.config.contracts.usdc;
        const amountIn = ethers_1.ethers.parseUnits('1', '18');
        const amountsUniswap = await uniswapRouter.getAmountsOut(amountIn, [tokenA, tokenB]);
        const amountsSushiswap = await sushiswapRouter.getAmountsOut(amountIn, [tokenA, tokenB]);
        logger_1.logger.info('Price comparison:', {
            uniswap: amountsUniswap[1].toString(),
            sushiswap: amountsSushiswap[1].toString(),
        });
        return true;
    }
    catch (error) {
        logger_1.logger.error('Contract validation failed:', error);
        return false;
    }
}
async function runTestSimulation() {
    try {
        if (!(await validateNetwork())) {
            throw new Error('Network validation failed');
        }
        if (!(await validateContracts())) {
            throw new Error('Contract validation failed');
        }
        logger_1.logger.info('Test simulation completed successfully');
    }
    catch (error) {
        logger_1.logger.error('Test simulation failed:', error);
        process.exit(1);
    }
}
runTestSimulation().catch(console.error);
//# sourceMappingURL=test-simulation.js.map