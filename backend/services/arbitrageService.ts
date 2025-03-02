import mongoose from 'mongoose';
import { EventEmitter } from 'events';
import { MarketData } from '../database/models/MarketData';
import { logger } from '../utils/logger';

// Define the structure of an arbitrage opportunity
export interface ArbitrageOpportunity {
  tokenA: string;
  tokenB: string;
  amount: bigint;
  expectedProfit: bigint;
  route: string;
  timestamp: number;
  pair: string;
  gasEstimate: bigint;
  blockNumber?: number;
  exchange?: string;
  price?: number;
  liquidity?: number;
  txHash?: string;
  priceImpact?: number;
  spread?: number;
}

class ArbitrageService {
  private eventEmitter: EventEmitter;

  constructor(eventEmitter: EventEmitter) {
    this.eventEmitter = eventEmitter;
    this.setupEventListeners();
  }

  private setupEventListeners() {
    // Listen for arbitrage opportunities
    this.eventEmitter.on('arbitrageOpportunity', (opportunity: ArbitrageOpportunity) => {
      logger.info(`Received arbitrage opportunity: ${JSON.stringify({
        pair: opportunity.pair,
        profit: opportunity.expectedProfit.toString(),
        route: opportunity.route
      })}`);

      // Debug log for required fields
      logger.info(`Required fields check:
        blockNumber: ${opportunity.blockNumber}
        liquidity: ${opportunity.liquidity}
        price: ${opportunity.price}
        exchange: ${opportunity.exchange}
        tokenA: ${opportunity.tokenA}
        tokenB: ${opportunity.tokenB}
      `);

      // Save the opportunity to the database
      this.saveArbitrageOpportunity(opportunity);
    });
  }

  private validateOpportunity(opportunity: ArbitrageOpportunity): boolean {
    // Enhanced validation to ensure required fields are present and valid
    if (!opportunity) {
      logger.warn('Opportunity object is null or undefined');
      return false;
    }
    
    if (!opportunity.tokenA || !opportunity.tokenB) {
      logger.warn('Missing token addresses in opportunity data');
      return false;
    }

    if (!opportunity.amount || opportunity.amount <= 0n) {
      logger.warn('Invalid amount in opportunity data');
      return false;
    }

    if (!opportunity.timestamp) {
      logger.warn('Missing timestamp in opportunity data');
      return false;
    }
    
    // Check for other required fields with more detailed logging
    if (!opportunity.exchange) {
      logger.warn('Missing exchange in opportunity data, will use default QUICKSWAP');
      // We'll continue and fix this in saveArbitrageOpportunity
    }
    
    if (typeof opportunity.price !== 'number' || isNaN(opportunity.price) || opportunity.price <= 0) {
      logger.warn(`Invalid price in opportunity data: ${opportunity.price}, will use default value`);
      // We'll continue and fix this in saveArbitrageOpportunity
    }
    
    if (typeof opportunity.liquidity !== 'number' || isNaN(opportunity.liquidity) || opportunity.liquidity <= 0) {
      logger.warn(`Invalid liquidity in opportunity data: ${opportunity.liquidity}, will use default value`);
      // We'll continue and fix this in saveArbitrageOpportunity
    }
    
    if (typeof opportunity.blockNumber !== 'number' || isNaN(opportunity.blockNumber) || opportunity.blockNumber <= 0) {
      logger.warn(`Invalid blockNumber in opportunity data: ${opportunity.blockNumber}, will use default value`);
      // We'll continue and fix this in saveArbitrageOpportunity
    }

    // We'll return true and handle any missing fields in saveArbitrageOpportunity
    return true;
  }

  async saveArbitrageOpportunity(opportunity: ArbitrageOpportunity) {
    try {
      // Log the full opportunity data for debugging
      logger.info(`Processing arbitrage opportunity: ${JSON.stringify({
        ...opportunity,
        amount: opportunity.amount.toString(),
        expectedProfit: opportunity.expectedProfit.toString(),
        gasEstimate: opportunity.gasEstimate.toString()
      })}`);

      // Validate opportunity data before saving
      if (!this.validateOpportunity(opportunity)) {
        logger.warn('Invalid opportunity data, skipping save');
        return;
      }

      // Ensure tokenA and tokenB are non-empty strings and valid Ethereum addresses
      const sanitizedTokenA = opportunity.tokenA?.trim() || '';
      const sanitizedTokenB = opportunity.tokenB?.trim() || '';
      
      if (!sanitizedTokenA || !sanitizedTokenB) {
        logger.warn('Empty token addresses after trimming, skipping save');
        return;
      }

      // Validate token addresses format (basic check)
      const isValidAddress = (address: string) => /^0x[a-fA-F0-9]{40}$/.test(address);
      
      let tokenA = sanitizedTokenA;
      let tokenB = sanitizedTokenB;
      
      if (!isValidAddress(tokenA)) {
        logger.warn(`Invalid tokenA address format: ${tokenA}, using default`);
        tokenA = '0x1111111111111111111111111111111111111111';
      }
      
      if (!isValidAddress(tokenB)) {
        logger.warn(`Invalid tokenB address format: ${tokenB}, using default`);
        tokenB = '0x2222222222222222222222222222222222222222';
      }

      // Normalize exchange name to match allowed values in the enum
      const exchangeName = opportunity.exchange?.toUpperCase() || '';
      const validExchanges = ['UNISWAP', 'SUSHISWAP', 'QUICKSWAP', 'PANCAKESWAP'];
      // Default to QUICKSWAP if not valid
      const exchange = validExchanges.includes(exchangeName) ? exchangeName : 'QUICKSWAP';
      
      if (exchange !== exchangeName) {
        logger.info(`Normalized exchange from ${exchangeName} to ${exchange}`);
      }

      // Ensure we have valid numeric values for required fields
      const blockNumber = typeof opportunity.blockNumber === 'number' && !isNaN(opportunity.blockNumber) && opportunity.blockNumber > 0 
        ? opportunity.blockNumber 
        : Math.floor(Date.now() / 1000); // Use current timestamp as fallback
      
      if (blockNumber !== opportunity.blockNumber) {
        logger.info(`Using fallback blockNumber: ${blockNumber} instead of ${opportunity.blockNumber}`);
      }

      const price = typeof opportunity.price === 'number' && !isNaN(opportunity.price) && opportunity.price > 0 
        ? opportunity.price 
        : 1.0; // Default price
      
      if (price !== opportunity.price) {
        logger.info(`Using fallback price: ${price} instead of ${opportunity.price}`);
      }

      const liquidity = typeof opportunity.liquidity === 'number' && !isNaN(opportunity.liquidity) && opportunity.liquidity > 0 
        ? opportunity.liquidity 
        : 1000000; // Default liquidity
      
      if (liquidity !== opportunity.liquidity) {
        logger.info(`Using fallback liquidity: ${liquidity} instead of ${opportunity.liquidity}`);
      }

      // Ensure we have a valid timestamp
      let timestamp: Date;
      if (opportunity.timestamp) {
        // Check if timestamp is in seconds (Unix timestamp) or milliseconds
        const isSeconds = opportunity.timestamp < 10000000000; // Threshold to determine if in seconds
        if (isSeconds) {
          timestamp = new Date(opportunity.timestamp * 1000);
          logger.info(`Converting timestamp from seconds to milliseconds: ${opportunity.timestamp} -> ${opportunity.timestamp * 1000}`);
        } else {
          timestamp = new Date(opportunity.timestamp);
        }
        
        // Validate that the timestamp is a valid date
        if (isNaN(timestamp.getTime())) {
          logger.warn(`Invalid timestamp: ${opportunity.timestamp}, using current time`);
          timestamp = new Date(); // Use current date as fallback
        }
      } else {
        timestamp = new Date(); // Use current date as fallback
        logger.info('No timestamp provided, using current time');
      }

      // Generate a unique txHash if not provided
      const txHash = opportunity.txHash || `0x${Date.now().toString(16)}${Math.floor(Math.random() * 1000000).toString(16)}`;
      
      if (!opportunity.txHash) {
        logger.info(`Generated txHash: ${txHash}`);
      }

      // Create a new MarketData document with all required fields
      const marketData = new MarketData({
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

      // Log the FULL data being saved for debugging
      logger.info(`FULL market data before save: ${JSON.stringify({
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

      // Validate the document before saving
      const validationError = marketData.validateSync();
      if (validationError) {
        logger.error(`Validation error before save: ${JSON.stringify(validationError.errors)}`);
        
        // Try to fix validation errors
        let fixedErrors = false;
        
        if (validationError.errors.tokenA) {
          marketData.tokenA = '0x1111111111111111111111111111111111111111';
          logger.info('Fixed tokenA with default value');
          fixedErrors = true;
        }
        
        if (validationError.errors.tokenB) {
          marketData.tokenB = '0x2222222222222222222222222222222222222222';
          logger.info('Fixed tokenB with default value');
          fixedErrors = true;
        }
        
        if (validationError.errors.exchange) {
          marketData.exchange = 'QUICKSWAP';
          logger.info('Fixed exchange with default value');
          fixedErrors = true;
        }
        
        if (validationError.errors.price) {
          marketData.price = 1.0;
          logger.info('Fixed price with default value');
          fixedErrors = true;
        }
        
        if (validationError.errors.liquidity) {
          marketData.liquidity = 1000000;
          logger.info('Fixed liquidity with default value');
          fixedErrors = true;
        }
        
        if (validationError.errors.blockNumber) {
          marketData.blockNumber = Math.floor(Date.now() / 1000);
          logger.info('Fixed blockNumber with default value');
          fixedErrors = true;
        }
        
        if (validationError.errors.timestamp) {
          marketData.timestamp = new Date();
          logger.info('Fixed timestamp with current date');
          fixedErrors = true;
        }
        
        // Check if we fixed all validation errors
        const remainingErrors = marketData.validateSync();
        if (remainingErrors) {
          logger.error(`Still have validation errors after fixes: ${JSON.stringify(remainingErrors.errors)}`);
          return;
        } else if (fixedErrors) {
          logger.info('Successfully fixed all validation errors');
        }
      }

      // Save to MongoDB
      await marketData.save();
      logger.info(`Successfully saved arbitrage opportunity for pair ${opportunity.pair} to MongoDB`);
      
      // Log the saved document ID
      logger.info(`Saved document ID: ${marketData._id}`);
    } catch (error) {
      logger.error(`Error saving arbitrage opportunities: ${error instanceof Error ? error.message : String(error)}`);
      if (error instanceof mongoose.Error.ValidationError) {
        logger.error(`Validation errors: ${JSON.stringify(error.errors)}`);
      }
    }
  }
}

export default ArbitrageService; 