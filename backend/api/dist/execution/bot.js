"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const providers_1 = require("@ethersproject/providers");
const config_1 = require("../api/config");
const arbitrageScanner_1 = require("./arbitrageScanner");
const logger_1 = require("../utils/logger");
const winston_1 = __importDefault(require("winston"));
const ethers_1 = require("ethers");
const mongoose_1 = __importDefault(require("mongoose"));
const connection_1 = __importDefault(require("../database/connection"));
const arbitrageService_1 = __importDefault(require("../services/arbitrageService"));
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const child_process_1 = require("child_process");
const LOCK_FILE_PATH = path_1.default.join(__dirname, 'bot.lock');
const PID_FILE_PATH = path_1.default.join(__dirname, 'bot.pid');
const logsDir = path_1.default.join(__dirname, 'logs');
if (!fs_1.default.existsSync(logsDir)) {
    fs_1.default.mkdirSync(logsDir, { recursive: true });
}
function killRunningInstances() {
    try {
        logger_1.logger.info('Checking for running bot instances...');
        const botProcesses = [
            'ts-node bot.ts',
            'node dist/execution/bot.js',
            'npm run bot:start'
        ];
        let processesKilled = false;
        for (const processPattern of botProcesses) {
            try {
                const result = (0, child_process_1.execSync)(`pkill -f "${processPattern}" || echo "No processes found to kill"`).toString().trim();
                if (!result.includes('No processes found to kill')) {
                    logger_1.logger.info(`Killed processes matching: ${processPattern}`);
                    processesKilled = true;
                }
            }
            catch (error) {
                logger_1.logger.warn(`Error killing processes matching ${processPattern}: ${error instanceof Error ? error.message : String(error)}`);
            }
        }
        if (!processesKilled) {
            logger_1.logger.info('No running bot instances found.');
        }
        else {
            (0, child_process_1.execSync)('sleep 1');
        }
        return processesKilled;
    }
    catch (error) {
        logger_1.logger.warn(`Error killing running instances: ${error instanceof Error ? error.message : String(error)}`);
        return false;
    }
}
killRunningInstances();
if (checkLock()) {
    logger_1.logger.error('Another instance of the bot is already running. Exiting.');
    process.exit(1);
}
createLock();
logger_1.logger.info(`Bot started with PID ${process.pid}`);
function checkLock() {
    try {
        if (fs_1.default.existsSync(LOCK_FILE_PATH)) {
            const pid = fs_1.default.readFileSync(PID_FILE_PATH, 'utf8').trim();
            try {
                process.kill(parseInt(pid, 10), 0);
                logger_1.logger.error(`Bot is already running with PID ${pid}`);
                return true;
            }
            catch (e) {
                logger_1.logger.warn(`Removing stale lock file for non-existent PID ${pid}`);
                removeLock();
                return false;
            }
        }
        return false;
    }
    catch (error) {
        logger_1.logger.error(`Error checking lock file: ${error instanceof Error ? error.message : String(error)}`);
        return false;
    }
}
function createLock() {
    try {
        fs_1.default.writeFileSync(LOCK_FILE_PATH, 'LOCKED');
        fs_1.default.writeFileSync(PID_FILE_PATH, process.pid.toString());
        logger_1.logger.info(`Created lock file with PID ${process.pid}`);
        process.on('exit', removeLock);
        process.on('SIGINT', () => {
            logger_1.logger.info('Bot stopped by user (SIGINT)');
            removeLock();
            process.exit(0);
        });
        process.on('SIGTERM', () => {
            logger_1.logger.info('Bot stopped by system (SIGTERM)');
            removeLock();
            process.exit(0);
        });
        process.on('uncaughtException', (error) => {
            logger_1.logger.error(`Uncaught exception: ${error instanceof Error ? error.message : String(error)}`);
            removeLock();
            process.exit(1);
        });
    }
    catch (error) {
        logger_1.logger.error(`Error creating lock file: ${error instanceof Error ? error.message : String(error)}`);
        process.exit(1);
    }
}
function removeLock() {
    try {
        if (fs_1.default.existsSync(LOCK_FILE_PATH)) {
            fs_1.default.unlinkSync(LOCK_FILE_PATH);
            logger_1.logger.info('Removed lock file');
        }
        if (fs_1.default.existsSync(PID_FILE_PATH)) {
            fs_1.default.unlinkSync(PID_FILE_PATH);
            logger_1.logger.info('Removed PID file');
        }
    }
    catch (error) {
        logger_1.logger.error(`Error removing lock file: ${error instanceof Error ? error.message : String(error)}`);
    }
}
function cleanupAndExit(exitCode = 0, reason = 'unknown') {
    logger_1.logger.info(`Bot stopping. Reason: ${reason}`);
    try {
        if (global.scanner) {
            logger_1.logger.info('Stopping scanner...');
            global.scanner.stop();
        }
    }
    catch (error) {
        logger_1.logger.error(`Error stopping scanner: ${error instanceof Error ? error.message : String(error)}`);
    }
    removeLock();
    logger_1.logger.info(`Exiting with code ${exitCode}`);
    process.exit(exitCode);
}
const ERC20_ABI = [
    "function name() view returns (string)",
    "function symbol() view returns (string)",
    "function decimals() view returns (uint8)",
    "function balanceOf(address) view returns (uint)"
];
const args = process.argv.slice(2);
let runTime = 600;
let tokens = 'WETH,USDC,DAI';
let dexes = 'uniswap_v3,curve,balancer';
let gasStrategy = 'dynamic';
for (let i = 0; i < args.length; i++) {
    if (args[i] === '--run-time' && i + 1 < args.length) {
        runTime = parseInt(args[i + 1], 10);
        i++;
    }
    else if (args[i] === '--tokens' && i + 1 < args.length) {
        tokens = args[i + 1];
        i++;
    }
    else if (args[i] === '--dexes' && i + 1 < args.length) {
        dexes = args[i + 1];
        i++;
    }
    else if (args[i] === '--gas-strategy' && i + 1 < args.length) {
        gasStrategy = args[i + 1];
        i++;
    }
}
logger_1.logger.info(`Starting ArbitrageX bot with the following configuration:`);
logger_1.logger.info(`Run time: ${runTime} seconds`);
logger_1.logger.info(`Tokens: ${tokens}`);
logger_1.logger.info(`DEXes: ${dexes}`);
logger_1.logger.info(`Gas strategy: ${gasStrategy}`);
const config = (0, config_1.getConfig)();
let provider;
try {
    provider = new providers_1.JsonRpcProvider(config.network.rpc);
    logger_1.logger.info(`Connected to primary RPC provider: ${config.network.rpc.split('/')[2]}`);
}
catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    logger_1.logger.warn(`Failed to connect to primary RPC provider: ${errorMessage}`);
    const fallbackRpc = process.env.FALLBACK_RPC || 'https://eth-mainnet.g.alchemy.com/v2/demo';
    logger_1.logger.info(`Trying fallback RPC provider: ${fallbackRpc.split('/')[2]}`);
    provider = new providers_1.JsonRpcProvider(fallbackRpc);
}
const tokenList = tokens.split(',');
const tokenPairs = [];
async function validateTokenContract(address) {
    try {
        if (!address || address.length !== 42) {
            logger_1.logger.warn(`Invalid token address format: ${address}`);
            return false;
        }
        const network = await provider.getNetwork();
        const chainId = Number(network.chainId);
        logger_1.logger.info(`Validating token on network with chainId: ${chainId}`);
        const networkTokens = {
            1: {
                WETH: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
                USDC: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
                USDT: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
                DAI: '0x6B175474E89094C44Da98b954EedeAC495271d0F'
            },
            137: {
                WETH: '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
                USDC: '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
                USDT: '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
                DAI: '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063'
            },
            42161: {
                WETH: '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
                USDC: '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',
                USDT: '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
                DAI: '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1'
            },
            56: {
                WETH: '0x2170Ed0880ac9A755fd29B2688956BD959F933F8',
                USDC: '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
                USDT: '0x55d398326f99059fF775485246999027B3197955',
                DAI: '0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3'
            }
        };
        let isKnownToken = false;
        let tokenSymbol = '';
        if (networkTokens[chainId]) {
            for (const [symbol, tokenAddress] of Object.entries(networkTokens[chainId])) {
                if (address.toLowerCase() === tokenAddress.toLowerCase()) {
                    isKnownToken = true;
                    tokenSymbol = symbol;
                    logger_1.logger.info(`Address ${address} recognized as ${symbol} on network ${chainId}`);
                    break;
                }
            }
        }
        if (!isKnownToken) {
            for (const [networkId, tokens] of Object.entries(networkTokens)) {
                const netId = parseInt(networkId);
                if (netId !== chainId) {
                    for (const [symbol, tokenAddress] of Object.entries(tokens)) {
                        if (address.toLowerCase() === tokenAddress.toLowerCase()) {
                            logger_1.logger.warn(`Address ${address} is ${symbol} from network ${networkId}, but we're on network ${chainId}`);
                            if (process.env.EXECUTION_MODE === 'fork') {
                                logger_1.logger.info(`Running in fork mode, allowing token from different network`);
                                return true;
                            }
                            const correctAddress = networkTokens[chainId]?.[symbol];
                            if (correctAddress) {
                                logger_1.logger.warn(`Should use ${correctAddress} for ${symbol} on network ${chainId} instead`);
                            }
                            return false;
                        }
                    }
                }
            }
        }
        if (process.env.EXECUTION_MODE === 'fork' && isKnownToken) {
            logger_1.logger.info(`Running in fork mode with known token ${tokenSymbol}, skipping contract validation`);
            return true;
        }
        try {
            const tokenContract = new ethers_1.Contract(address, ERC20_ABI, provider);
            const [symbol, decimals] = await Promise.all([
                tokenContract.symbol(),
                tokenContract.decimals()
            ]);
            logger_1.logger.info(`Validated token ${symbol} with ${decimals} decimals at address ${address}`);
            return true;
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            logger_1.logger.error(`Failed to validate token contract at ${address}: ${errorMessage}`);
            if (process.env.EXECUTION_MODE === 'fork') {
                logger_1.logger.warn(`Running in fork mode - proceeding with token ${address} despite validation failure`);
                return true;
            }
            return false;
        }
    }
    catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        logger_1.logger.error(`Error in validateTokenContract: ${errorMessage}`);
        return false;
    }
}
async function getTokenAddress(symbol, config) {
    const upperSymbol = symbol.toUpperCase();
    let chainId = 1;
    try {
        const network = await provider.getNetwork();
        chainId = Number(network.chainId);
        logger_1.logger.info(`Current network chainId: ${chainId}`);
    }
    catch (error) {
        logger_1.logger.error(`Failed to get network: ${error instanceof Error ? error.message : String(error)}`);
    }
    const networkTokens = {
        1: {
            WETH: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
            USDC: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
            USDT: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
            DAI: '0x6B175474E89094C44Da98b954EedeAC495271d0F'
        },
        137: {
            WETH: '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
            USDC: '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
            USDT: '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
            DAI: '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063'
        },
        42161: {
            WETH: '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
            USDC: '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',
            USDT: '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
            DAI: '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1'
        },
        56: {
            WETH: '0x2170Ed0880ac9A755fd29B2688956BD959F933F8',
            USDC: '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
            USDT: '0x55d398326f99059fF775485246999027B3197955',
            DAI: '0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3'
        }
    };
    if (networkTokens[chainId] && networkTokens[chainId][upperSymbol]) {
        const address = networkTokens[chainId][upperSymbol];
        logger_1.logger.info(`Using network-specific address for ${upperSymbol} on chainId ${chainId}: ${address}`);
        return address;
    }
    let address = null;
    switch (upperSymbol) {
        case 'WETH':
            address = config.contracts.weth || process.env.WETH_ADDRESS;
            break;
        case 'USDC':
            address = config.contracts.usdc || process.env.USDC_ADDRESS;
            break;
        case 'DAI':
            address = config.contracts.dai || process.env.DAI_ADDRESS;
            break;
        case 'USDT':
            address = config.contracts.usdt || process.env.USDT_ADDRESS;
            break;
        default:
            logger_1.logger.warn(`Unknown token symbol: ${symbol}`);
            return null;
    }
    if (!address && networkTokens[1][upperSymbol]) {
        address = networkTokens[1][upperSymbol];
        logger_1.logger.warn(`Using Ethereum mainnet fallback address for ${upperSymbol}: ${address}`);
    }
    if (!address) {
        logger_1.logger.error(`No address found for token: ${symbol}`);
        return null;
    }
    return address;
}
const gasConfig = {
    minProfitThreshold: config.security?.minProfitThreshold || 0.001,
    minNetProfit: 0.001,
    gasLimit: 500000,
    scanInterval: 5000,
    maxGasPrice: gasStrategy === 'conservative' ? 50000000000 :
        gasStrategy === 'aggressive' ? 200000000000 : 100000000000,
    gasMultiplier: gasStrategy === 'conservative' ? 1.05 :
        gasStrategy === 'aggressive' ? 1.2 : 1.1
};
const scannerLogger = winston_1.default.createLogger({
    level: 'info',
    format: winston_1.default.format.simple(),
    transports: [
        new winston_1.default.transports.Console({
            format: winston_1.default.format.simple()
        })
    ]
});
scannerLogger.info = (message) => {
    if (typeof message === 'string') {
        logger_1.logger.info(message);
    }
    else {
        logger_1.logger.info(JSON.stringify(message));
    }
    return scannerLogger;
};
scannerLogger.warn = (message) => {
    if (typeof message === 'string') {
        logger_1.logger.warn(message);
    }
    else {
        logger_1.logger.warn(JSON.stringify(message));
    }
    return scannerLogger;
};
scannerLogger.error = (message) => {
    if (typeof message === 'string') {
        logger_1.logger.error(message);
    }
    else {
        logger_1.logger.error(JSON.stringify(message));
    }
    return scannerLogger;
};
async function setupTokenPairs() {
    const validatedPairs = [];
    for (let i = 0; i < tokenList.length; i++) {
        for (let j = i + 1; j < tokenList.length; j++) {
            const tokenA = tokenList[i].trim();
            const tokenB = tokenList[j].trim();
            const tokenAAddress = await getTokenAddress(tokenA, config);
            const tokenBAddress = await getTokenAddress(tokenB, config);
            if (tokenAAddress && tokenBAddress) {
                logger_1.logger.info(`Validating token pair: ${tokenA}(${tokenAAddress}) - ${tokenB}(${tokenBAddress})`);
                const [isValidTokenA, isValidTokenB] = await Promise.all([
                    validateTokenContract(tokenAAddress),
                    validateTokenContract(tokenBAddress)
                ]);
                if (isValidTokenA && isValidTokenB) {
                    logger_1.logger.info(`Adding validated token pair: ${tokenA}(${tokenAAddress}) - ${tokenB}(${tokenBAddress})`);
                    validatedPairs.push({
                        tokenA: tokenAAddress,
                        tokenB: tokenBAddress
                    });
                }
                else {
                    logger_1.logger.warn(`Skipping invalid token pair: ${tokenA}(${tokenAAddress}) - ${tokenB}(${tokenBAddress})`);
                }
            }
            else {
                logger_1.logger.warn(`Skipping token pair due to missing address: ${tokenA} - ${tokenB}`);
            }
        }
    }
    return validatedPairs;
}
async function startBot() {
    try {
        if (mongoose_1.default.connection.readyState === 0) {
            logger_1.logger.info('Connecting to MongoDB...');
            await (0, connection_1.default)();
            logger_1.logger.info('MongoDB connection established');
        }
        else {
            logger_1.logger.info('MongoDB already connected');
        }
        const validatedPairs = await setupTokenPairs();
        if (validatedPairs.length === 0) {
            logger_1.logger.error('No valid token pairs found. Cannot start scanner.');
            process.exit(1);
        }
        const scanner = new arbitrageScanner_1.ArbitrageScanner(provider, config.contracts.uniswapRouter, config.contracts.sushiswapRouter, gasConfig, validatedPairs, scannerLogger);
        global.scanner = scanner;
        const arbitrageService = new arbitrageService_1.default(scanner);
        logger_1.logger.info(`Starting arbitrage scanner with ${validatedPairs.length} validated token pairs`);
        scanner.start();
        setTimeout(() => {
            logger_1.logger.info(`Run time of ${runTime} seconds reached, stopping bot`);
            cleanupAndExit(0, 'Run time reached');
        }, runTime * 1000);
    }
    catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        logger_1.logger.error(`Failed to start bot: ${errorMessage}`);
        cleanupAndExit(1, `Failed to start bot: ${errorMessage}`);
    }
}
startBot().catch(error => {
    const errorMessage = error instanceof Error ? error.message : String(error);
    logger_1.logger.error(`Unhandled error in bot startup: ${errorMessage}`);
    process.exit(1);
});
process.on('SIGUSR1', () => {
    cleanupAndExit(0, 'SIGUSR1 signal received');
});
process.on('SIGUSR2', () => {
    cleanupAndExit(0, 'SIGUSR2 signal received');
});
//# sourceMappingURL=bot.js.map