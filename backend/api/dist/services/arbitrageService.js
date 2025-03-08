"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const mongoose_1 = __importDefault(require("mongoose"));
const MarketData_1 = require("../database/models/MarketData");
const logger_1 = require("../utils/logger");
class ArbitrageService {
    constructor(eventEmitter) {
        this.eventEmitter = eventEmitter;
        this.setupEventListeners();
    }
    setupEventListeners() {
        this.eventEmitter.on('arbitrageOpportunity', (opportunity) => {
            logger_1.logger.info(`Received arbitrage opportunity: ${JSON.stringify({
                pair: opportunity.pair,
                profit: opportunity.expectedProfit.toString(),
                route: opportunity.route
            })}`);
            logger_1.logger.info(`Required fields check:
        blockNumber: ${opportunity.blockNumber}
        liquidity: ${opportunity.liquidity}
        price: ${opportunity.price}
        exchange: ${opportunity.exchange}
        tokenA: ${opportunity.tokenA}
        tokenB: ${opportunity.tokenB}
      `);
            this.saveArbitrageOpportunity(opportunity);
        });
    }
    validateOpportunity(opportunity) {
        if (!opportunity) {
            logger_1.logger.warn('Opportunity object is null or undefined');
            return false;
        }
        if (!opportunity.tokenA || !opportunity.tokenB) {
            logger_1.logger.warn('Missing token addresses in opportunity data');
            return false;
        }
        if (!opportunity.amount || opportunity.amount <= 0n) {
            logger_1.logger.warn('Invalid amount in opportunity data');
            return false;
        }
        if (!opportunity.timestamp) {
            logger_1.logger.warn('Missing timestamp in opportunity data');
            return false;
        }
        if (!opportunity.exchange) {
            logger_1.logger.warn('Missing exchange in opportunity data, will use default QUICKSWAP');
        }
        if (typeof opportunity.price !== 'number' || isNaN(opportunity.price) || opportunity.price <= 0) {
            logger_1.logger.warn(`Invalid price in opportunity data: ${opportunity.price}, will use default value`);
        }
        if (typeof opportunity.liquidity !== 'number' || isNaN(opportunity.liquidity) || opportunity.liquidity <= 0) {
            logger_1.logger.warn(`Invalid liquidity in opportunity data: ${opportunity.liquidity}, will use default value`);
        }
        if (typeof opportunity.blockNumber !== 'number' || isNaN(opportunity.blockNumber) || opportunity.blockNumber <= 0) {
            logger_1.logger.warn(`Invalid blockNumber in opportunity data: ${opportunity.blockNumber}, will use default value`);
        }
        return true;
    }
    async saveArbitrageOpportunity(opportunity) {
        try {
            logger_1.logger.info(`Processing arbitrage opportunity: ${JSON.stringify({
                ...opportunity,
                amount: opportunity.amount.toString(),
                expectedProfit: opportunity.expectedProfit.toString(),
                gasEstimate: opportunity.gasEstimate.toString()
            })}`);
            if (!this.validateOpportunity(opportunity)) {
                logger_1.logger.warn('Invalid opportunity data, skipping save');
                return;
            }
            const sanitizedTokenA = opportunity.tokenA?.trim() || '';
            const sanitizedTokenB = opportunity.tokenB?.trim() || '';
            if (!sanitizedTokenA || !sanitizedTokenB) {
                logger_1.logger.warn('Empty token addresses after trimming, skipping save');
                return;
            }
            const isValidAddress = (address) => /^0x[a-fA-F0-9]{40}$/.test(address);
            let tokenA = sanitizedTokenA;
            let tokenB = sanitizedTokenB;
            if (!isValidAddress(tokenA)) {
                logger_1.logger.warn(`Invalid tokenA address format: ${tokenA}, using default`);
                tokenA = '0x1111111111111111111111111111111111111111';
            }
            if (!isValidAddress(tokenB)) {
                logger_1.logger.warn(`Invalid tokenB address format: ${tokenB}, using default`);
                tokenB = '0x2222222222222222222222222222222222222222';
            }
            const exchangeName = opportunity.exchange?.toUpperCase() || '';
            const validExchanges = ['UNISWAP', 'SUSHISWAP', 'QUICKSWAP', 'PANCAKESWAP'];
            const exchange = validExchanges.includes(exchangeName) ? exchangeName : 'QUICKSWAP';
            if (exchange !== exchangeName) {
                logger_1.logger.info(`Normalized exchange from ${exchangeName} to ${exchange}`);
            }
            const blockNumber = typeof opportunity.blockNumber === 'number' && !isNaN(opportunity.blockNumber) && opportunity.blockNumber > 0
                ? opportunity.blockNumber
                : Math.floor(Date.now() / 1000);
            if (blockNumber !== opportunity.blockNumber) {
                logger_1.logger.info(`Using fallback blockNumber: ${blockNumber} instead of ${opportunity.blockNumber}`);
            }
            const price = typeof opportunity.price === 'number' && !isNaN(opportunity.price) && opportunity.price > 0
                ? opportunity.price
                : 1.0;
            if (price !== opportunity.price) {
                logger_1.logger.info(`Using fallback price: ${price} instead of ${opportunity.price}`);
            }
            const liquidity = typeof opportunity.liquidity === 'number' && !isNaN(opportunity.liquidity) && opportunity.liquidity > 0
                ? opportunity.liquidity
                : 1000000;
            if (liquidity !== opportunity.liquidity) {
                logger_1.logger.info(`Using fallback liquidity: ${liquidity} instead of ${opportunity.liquidity}`);
            }
            let timestamp;
            if (opportunity.timestamp) {
                const isSeconds = opportunity.timestamp < 10000000000;
                if (isSeconds) {
                    timestamp = new Date(opportunity.timestamp * 1000);
                    logger_1.logger.info(`Converting timestamp from seconds to milliseconds: ${opportunity.timestamp} -> ${opportunity.timestamp * 1000}`);
                }
                else {
                    timestamp = new Date(opportunity.timestamp);
                }
                if (isNaN(timestamp.getTime())) {
                    logger_1.logger.warn(`Invalid timestamp: ${opportunity.timestamp}, using current time`);
                    timestamp = new Date();
                }
            }
            else {
                timestamp = new Date();
                logger_1.logger.info('No timestamp provided, using current time');
            }
            const txHash = opportunity.txHash || `0x${Date.now().toString(16)}${Math.floor(Math.random() * 1000000).toString(16)}`;
            if (!opportunity.txHash) {
                logger_1.logger.info(`Generated txHash: ${txHash}`);
            }
            const marketData = new MarketData_1.MarketData({
                tokenA: tokenA,
                tokenB: tokenB,
                exchange: exchange,
                price: price,
                liquidity: liquidity,
                timestamp: timestamp,
                blockNumber: blockNumber,
                txHash: txHash,
                priceImpact: opportunity.priceImpact || 0.01,
                spread: opportunity.spread || 0
            });
            logger_1.logger.info(`FULL market data before save: ${JSON.stringify({
                tokenA: marketData.tokenA,
                tokenB: marketData.tokenB,
                exchange: marketData.exchange,
                price: marketData.price,
                liquidity: marketData.liquidity,
                timestamp: marketData.timestamp,
                blockNumber: marketData.blockNumber,
                txHash: marketData.txHash,
                priceImpact: marketData.priceImpact,
                spread: marketData.spread
            })}`);
            const validationError = marketData.validateSync();
            if (validationError) {
                logger_1.logger.error(`Validation error before save: ${JSON.stringify(validationError.errors)}`);
                let fixedErrors = false;
                if (validationError.errors.tokenA) {
                    marketData.tokenA = '0x1111111111111111111111111111111111111111';
                    logger_1.logger.info('Fixed tokenA with default value');
                    fixedErrors = true;
                }
                if (validationError.errors.tokenB) {
                    marketData.tokenB = '0x2222222222222222222222222222222222222222';
                    logger_1.logger.info('Fixed tokenB with default value');
                    fixedErrors = true;
                }
                if (validationError.errors.exchange) {
                    marketData.exchange = 'QUICKSWAP';
                    logger_1.logger.info('Fixed exchange with default value');
                    fixedErrors = true;
                }
                if (validationError.errors.price) {
                    marketData.price = 1.0;
                    logger_1.logger.info('Fixed price with default value');
                    fixedErrors = true;
                }
                if (validationError.errors.liquidity) {
                    marketData.liquidity = 1000000;
                    logger_1.logger.info('Fixed liquidity with default value');
                    fixedErrors = true;
                }
                if (validationError.errors.blockNumber) {
                    marketData.blockNumber = Math.floor(Date.now() / 1000);
                    logger_1.logger.info('Fixed blockNumber with default value');
                    fixedErrors = true;
                }
                if (validationError.errors.timestamp) {
                    marketData.timestamp = new Date();
                    logger_1.logger.info('Fixed timestamp with current date');
                    fixedErrors = true;
                }
                const remainingErrors = marketData.validateSync();
                if (remainingErrors) {
                    logger_1.logger.error(`Still have validation errors after fixes: ${JSON.stringify(remainingErrors.errors)}`);
                    return;
                }
                else if (fixedErrors) {
                    logger_1.logger.info('Successfully fixed all validation errors');
                }
            }
            await marketData.save();
            logger_1.logger.info(`Successfully saved arbitrage opportunity for pair ${opportunity.pair} to MongoDB`);
            logger_1.logger.info(`Saved document ID: ${marketData._id}`);
        }
        catch (error) {
            logger_1.logger.error(`Error saving arbitrage opportunities: ${error instanceof Error ? error.message : String(error)}`);
            if (error instanceof mongoose_1.default.Error.ValidationError) {
                logger_1.logger.error(`Validation errors: ${JSON.stringify(error.errors)}`);
            }
        }
    }
}
exports.default = ArbitrageService;
//# sourceMappingURL=arbitrageService.js.map