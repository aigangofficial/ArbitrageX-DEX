"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.config = void 0;
exports.getConfig = getConfig;
const dotenv_1 = __importDefault(require("dotenv"));
const path_1 = __importDefault(require("path"));
// Load environment variables
dotenv_1.default.config({ path: path_1.default.join(__dirname, '../../.env') });
// Debug loaded environment variables
console.log('Loaded environment variables:', {
    NETWORK_RPC: process.env.NETWORK_RPC,
    NETWORK_NAME: process.env.NETWORK_NAME,
    CHAIN_ID: process.env.CHAIN_ID,
    UNISWAP_ROUTER_ADDRESS: process.env.UNISWAP_ROUTER_ADDRESS,
    SUSHISWAP_ROUTER_ADDRESS: process.env.SUSHISWAP_ROUTER_ADDRESS,
    AAVE_POOL_ADDRESS: process.env.AAVE_POOL_ADDRESS,
    WETH_ADDRESS: process.env.WETH_ADDRESS,
    USDC_ADDRESS: process.env.USDC_ADDRESS,
    USDT_ADDRESS: process.env.USDT_ADDRESS
});
const config = {
    // Server configuration
    port: Number(process.env.PORT) || 3000,
    nodeEnv: process.env.NODE_ENV || 'development',
    // MongoDB configuration
    mongoUri: process.env.MONGO_URI || 'mongodb://localhost:27017/arbitragex',
    // Web3 configuration
    web3Provider: process.env.WEB3_PROVIDER || 'http://localhost:8545',
    // Contract addresses
    flashLoanServiceAddress: process.env.FLASH_LOAN_SERVICE_ADDRESS || '',
    arbitrageExecutorAddress: process.env.ARBITRAGE_EXECUTOR_ADDRESS || '',
    // API configuration
    apiPrefix: process.env.API_PREFIX || '/api',
    corsOrigin: process.env.CORS_ORIGIN || '*',
    // Rate limiting
    rateLimit: {
        windowMs: 15 * 60 * 1000, // 15 minutes
        max: 100 // limit each IP to 100 requests per windowMs
    },
    // Sentry error tracking
    sentryDsn: process.env.SENTRY_DSN || '',
    // Redis configuration
    redis: {
        host: process.env.REDIS_HOST || 'localhost',
        port: parseInt(process.env.REDIS_PORT || '6379'),
        password: process.env.REDIS_PASSWORD || ''
    },
    network: {
        rpc: process.env.NETWORK_RPC || 'https://mainnet.infura.io/v3/59de174d2d904c1980b975abae2ef0ec',
        chainId: parseInt(process.env.CHAIN_ID || '1'),
        name: process.env.NETWORK_NAME || 'mainnet',
    },
    contracts: {
        // DEX Routers
        uniswapRouter: process.env.UNISWAP_ROUTER_ADDRESS || '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
        sushiswapRouter: process.env.SUSHISWAP_ROUTER_ADDRESS || '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
        quickswapRouter: process.env.QUICKSWAP_ROUTER_ADDRESS || '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
        // Protocol Addresses
        aavePool: process.env.AAVE_POOL_ADDRESS || '0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951',
        bridge: process.env.BRIDGE_ADDRESS || '0x1234...',
        // Token Addresses
        weth: process.env.WETH_ADDRESS || '0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9',
        wmatic: process.env.WMATIC_ADDRESS || '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',
        usdc: process.env.USDC_ADDRESS || '0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238',
        usdt: process.env.USDT_ADDRESS || '0x7169D38820dfd117C3FA1f22a697dBA58d90BA06',
    },
    database: {
        uri: process.env.MONGODB_URI || 'mongodb://localhost:27017/arbitragex',
    },
    api: {
        port: parseInt(process.env.API_PORT || '3000'),
        wsPort: parseInt(process.env.WS_PORT || '3001'),
        corsOrigin: process.env.CORS_ORIGIN || 'http://localhost:3001',
    },
    logging: {
        level: process.env.LOG_LEVEL || 'info',
        directory: process.env.LOG_DIRECTORY || 'logs',
    },
    security: {
        minProfitThreshold: parseFloat(process.env.MIN_PROFIT_THRESHOLD || '0.01'),
        maxSlippage: parseFloat(process.env.MAX_SLIPPAGE || '0.5'),
        gasPriceLimit: parseInt(process.env.GAS_PRICE_LIMIT || '100'),
    },
    flashbots: {
        commitDelay: 2,
        maxBlocksToTry: 3,
        privacy: {
            useDecoyTransactions: true
        },
        decoy: {
            contracts: [],
            minDecoys: 0,
            maxDecoys: 0,
            valueVariation: 0
        },
        monitoring: {
            knownSelectors: [],
            avgGasPrice: 0,
            checkInterval: 0,
            anomalyThreshold: 0
        },
        gas: {
            base: 0,
            variance: 0
        },
        protection: {
            whitelistedCallers: [],
            commitDelay: 0,
            minFlashbotsFee: '0.001',
            maxBlocksToTry: 0,
            simulateBeforeSubmit: false,
            revertOnFailure: false
        }
    },
    chains: {
        1: {
            rpcUrl: process.env.ETH_RPC || 'https://mainnet.infura.io/v3/...',
            gasMultiplier: 1.2,
            priorityFeePercentile: 30
        },
        42161: {
            rpcUrl: process.env.ARB_RPC || 'https://arb1.arbitrum.io/rpc',
            gasMultiplier: 1.1,
            priorityFeePercentile: 20
        }
    },
    ai: {
        modelPath: process.env.AI_MODEL_PATH || './models/arbitrage_model',
        batchSize: parseInt(process.env.AI_BATCH_SIZE || '32'),
        learningRate: parseFloat(process.env.AI_LEARNING_RATE || '0.001'),
        epochs: parseInt(process.env.AI_EPOCHS || '100'),
        gan: {
            trainingInterval: parseInt(process.env.GAN_TRAINING_INTERVAL || '3600'),
            hiddenUnits: [16, 8, 4],
            learningRate: parseFloat(process.env.GAN_LEARNING_RATE || '0.0002'),
            batchSize: parseInt(process.env.GAN_BATCH_SIZE || '32'),
            epochs: parseInt(process.env.GAN_EPOCHS || '100')
        },
        quantum: {
            minLatticeSecurityLevel: parseInt(process.env.AI_MIN_LATTICE_SECURITY_LEVEL || '1'),
            challengeWindowMs: parseInt(process.env.AI_CHALLENGE_WINDOW_MS || '1000')
        },
        adversarialTraining: {
            scenarios: [
                { liquidityShock: 0.3, gasPriceSpike: 0.5, competitorActivity: 0.8, marketVolatility: 0.4 },
                { liquidityShock: 0.5, gasPriceSpike: 0.7, competitorActivity: 0.9, marketVolatility: 0.6 }
            ],
            frequency: parseInt(process.env.AI_SIMULATION_FREQUENCY || '3600'),
            intensityRange: [0.1, 0.9]
        }
    }
};
exports.config = config;
function getConfig() {
    return config;
}
//# sourceMappingURL=config.js.map