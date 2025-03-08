"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.arbitrageService = exports.scanner = void 0;
const providers_1 = require("@ethersproject/providers");
const config_1 = require("../api/config");
const arbitrageScanner_1 = require("./arbitrageScanner");
const logger_1 = require("../utils/logger");
const arbitrageService_1 = __importDefault(require("../services/arbitrageService"));
const mongoose_1 = __importDefault(require("mongoose"));
const connection_1 = __importDefault(require("../database/connection"));
const config = (0, config_1.getConfig)();
const provider = new providers_1.JsonRpcProvider(config.web3Provider);
async function initialize() {
    try {
        if (mongoose_1.default.connection.readyState === 0) {
            logger_1.logger.info('Connecting to MongoDB...');
            await (0, connection_1.default)();
            logger_1.logger.info('MongoDB connection established');
        }
        else {
            logger_1.logger.info('MongoDB already connected');
        }
        const scanner = new arbitrageScanner_1.ArbitrageScanner(provider, config.contracts.uniswapRouter, config.contracts.sushiswapRouter, {
            minProfitThreshold: config.security.minProfitThreshold,
            minNetProfit: 0.001,
            gasLimit: 500000,
            scanInterval: 5000,
            maxGasPrice: 100000000000,
            gasMultiplier: 1.1
        }, [
            {
                tokenA: config.contracts.weth,
                tokenB: config.contracts.usdc
            },
            {
                tokenA: config.contracts.weth,
                tokenB: config.contracts.usdt
            }
        ], logger_1.logger);
        const arbitrageService = new arbitrageService_1.default(scanner);
        logger_1.logger.info('Starting arbitrage scanner and service');
        scanner.start();
        return { scanner, arbitrageService };
    }
    catch (error) {
        logger_1.logger.error(`Error initializing services: ${error}`);
        throw error;
    }
}
let scanner;
let arbitrageService;
initialize()
    .then(services => {
    exports.scanner = scanner = services.scanner;
    exports.arbitrageService = arbitrageService = services.arbitrageService;
})
    .catch(error => {
    logger_1.logger.error(`Failed to initialize services: ${error}`);
    process.exit(1);
});
//# sourceMappingURL=startScanner.js.map