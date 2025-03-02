import { Provider } from '@ethersproject/abstract-provider';
import { JsonRpcProvider } from '@ethersproject/providers';
import { getConfig } from '../api/config';
import { ArbitrageScanner } from './arbitrageScanner';
import { logger } from '../utils/logger';
import ArbitrageService from '../services/arbitrageService';
import { Logger } from 'winston';
import mongoose from 'mongoose';
import connectDB from '../database/connection';

const config = getConfig();
const provider = new JsonRpcProvider(config.web3Provider) as unknown as Provider;

// Initialize database connection
async function initialize() {
    try {
        // Connect to MongoDB if not already connected
        if (mongoose.connection.readyState === 0) {
            logger.info('Connecting to MongoDB...');
            await connectDB();
            logger.info('MongoDB connection established');
        } else {
            logger.info('MongoDB already connected');
        }

        const scanner = new ArbitrageScanner(
            provider,
            config.contracts.uniswapRouter,
            config.contracts.sushiswapRouter,
            {
                minProfitThreshold: config.security.minProfitThreshold,
                minNetProfit: 0.001, // 0.1% minimum net profit
                gasLimit: 500000,    // 500k gas limit
                scanInterval: 5000,  // 5 second interval
                maxGasPrice: 100000000000, // 100 gwei (as number, not bigint)
                gasMultiplier: 1.1   // 10% buffer
            },
            [
                {
                    tokenA: config.contracts.weth,
                    tokenB: config.contracts.usdc
                },
                {
                    tokenA: config.contracts.weth,
                    tokenB: config.contracts.usdt
                }
            ],
            logger as Logger
        );

        // Initialize the arbitrage service with the scanner as the event emitter
        const arbitrageService = new ArbitrageService(scanner);

        logger.info('Starting arbitrage scanner and service');
        scanner.start();

        return { scanner, arbitrageService };
    } catch (error) {
        logger.error(`Error initializing services: ${error}`);
        throw error;
    }
}

// Initialize and export the services
let scanner: ArbitrageScanner;
let arbitrageService: ArbitrageService;

initialize()
    .then(services => {
        scanner = services.scanner;
        arbitrageService = services.arbitrageService;
    })
    .catch(error => {
        logger.error(`Failed to initialize services: ${error}`);
        process.exit(1);
    });

export { scanner, arbitrageService };
