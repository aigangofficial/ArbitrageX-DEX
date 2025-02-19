import mongoose, { Document, Model } from 'mongoose';

// Interfaces
interface ITradeDocument extends Document {
  tokenA: string;
  tokenB: string;
  amount: string;
  expectedProfit: string;
  netProfit: string;
  gasCost: string;
  flashLoanFee: string;
  route: 'QUICKSWAP_TO_SUSHISWAP' | 'SUSHISWAP_TO_QUICKSWAP';
  priceImpact: number;
  slippage: number;
  status: 'SIMULATED' | 'EXECUTED' | 'FAILED';
  timestamp: Date;
  error?: string;
}

interface IMarketDataDocument extends Document {
  exchange: 'QUICKSWAP' | 'SUSHISWAP';
  tokenA: string;
  tokenB: string;
  price: number;
  liquidity: number;
  timestamp: Date;
  blockNumber: number;
  spread: number;
}

// Static methods interfaces
interface ITradeModel extends Model<ITradeDocument> {
  getStatistics(timeframe: string): Promise<any>;
}

interface IMarketDataModel extends Model<IMarketDataDocument> {
  findArbitrageOpportunities(minSpreadPercentage?: number): Promise<IMarketDataDocument[]>;
  getVolatility(pair: string, hours?: number): Promise<any>;
}

const tradeSchema = new mongoose.Schema<ITradeDocument>(
  {
    tokenA: {
      type: String,
      required: true,
    },
    tokenB: {
      type: String,
      required: true,
    },
    amount: {
      type: String,
      required: true,
    },
    expectedProfit: {
      type: String,
      required: true,
    },
    netProfit: {
      type: String,
      required: true,
    },
    gasCost: {
      type: String,
      required: true,
    },
    flashLoanFee: {
      type: String,
      required: true,
    },
    route: {
      type: String,
      enum: ['QUICKSWAP_TO_SUSHISWAP', 'SUSHISWAP_TO_QUICKSWAP'],
      required: true,
    },
    priceImpact: {
      type: Number,
      required: true,
    },
    slippage: {
      type: Number,
      required: true,
    },
    status: {
      type: String,
      enum: ['SIMULATED', 'EXECUTED', 'FAILED'],
      required: true,
    },
    timestamp: {
      type: Date,
      default: Date.now,
    },
    error: {
      type: String,
    },
  },
  {
    timestamps: true,
  }
);

const marketDataSchema = new mongoose.Schema<IMarketDataDocument>(
  {
    exchange: {
      type: String,
      required: true,
      enum: ['QUICKSWAP', 'SUSHISWAP'],
    },
    tokenA: {
      type: String,
      required: true,
    },
    tokenB: {
      type: String,
      required: true,
    },
    price: {
      type: Number,
      required: true,
    },
    liquidity: {
      type: Number,
      required: true,
    },
    timestamp: {
      type: Date,
      default: Date.now,
    },
    blockNumber: {
      type: Number,
      required: true,
    },
    spread: {
      type: Number,
      default: 0,
    },
  },
  {
    timestamps: true,
  }
);

// Add static methods to marketDataSchema
marketDataSchema.statics.findArbitrageOpportunities = async function (minSpreadPercentage = 0.5) {
  const opportunities = await this.aggregate([
    // Group by token pair to compare prices across exchanges
    {
      $group: {
        _id: {
          tokenA: '$tokenA',
          tokenB: '$tokenB',
          blockNumber: '$blockNumber',
        },
        exchanges: {
          $push: {
            exchange: '$exchange',
            price: '$price',
            liquidity: '$liquidity',
          },
        },
      },
    },
    // Filter for pairs with data from both exchanges
    {
      $match: {
        'exchanges.1': { $exists: true },
      },
    },
    // Calculate spread between exchanges
    {
      $project: {
        tokenA: '$_id.tokenA',
        tokenB: '$_id.tokenB',
        blockNumber: '$_id.blockNumber',
        exchanges: 1,
        spread: {
          $multiply: [
            {
              $divide: [
                { $subtract: [{ $max: '$exchanges.price' }, { $min: '$exchanges.price' }] },
                { $min: '$exchanges.price' },
              ],
            },
            100,
          ],
        },
      },
    },
    // Filter for minimum spread
    {
      $match: {
        spread: { $gte: minSpreadPercentage },
      },
    },
    // Sort by spread descending
    {
      $sort: { spread: -1 },
    },
  ]);

  return opportunities;
};

marketDataSchema.statics.getVolatility = async function (pair: string, hours = 24) {
  const timeframe = new Date();
  timeframe.setHours(timeframe.getHours() - hours);

  const volatilityData = await this.aggregate([
    {
      $match: {
        tokenA: pair.split('-')[0],
        tokenB: pair.split('-')[1],
        timestamp: { $gte: timeframe },
      },
    },
    {
      $group: {
        _id: '$exchange',
        priceAvg: { $avg: '$price' },
        priceStdDev: { $stdDevPop: '$price' },
        maxPrice: { $max: '$price' },
        minPrice: { $min: '$price' },
        dataPoints: { $sum: 1 },
      },
    },
    {
      $project: {
        exchange: '$_id',
        volatility: {
          $multiply: [{ $divide: ['$priceStdDev', '$priceAvg'] }, 100],
        },
        priceRange: {
          $multiply: [
            {
              $divide: [{ $subtract: ['$maxPrice', '$minPrice'] }, '$priceAvg'],
            },
            100,
          ],
        },
        dataPoints: 1,
      },
    },
  ]);

  return volatilityData;
};

// Add getStatistics method to tradeSchema
tradeSchema.statics.getStatistics = async function (timeframe: string) {
  const timeframeMap: { [key: string]: number } = {
    '1h': 1,
    '24h': 24,
    '7d': 168,
    '30d': 720,
  };

  const hours = timeframeMap[timeframe] || 24;
  const since = new Date();
  since.setHours(since.getHours() - hours);

  const stats = await this.aggregate([
    {
      $match: {
        timestamp: { $gte: since },
        status: 'EXECUTED',
      },
    },
    {
      $group: {
        _id: null,
        totalTrades: { $sum: 1 },
        totalProfit: { $sum: { $toDouble: '$netProfit' } },
        avgGasCost: { $avg: { $toDouble: '$gasCost' } },
        successRate: {
          $avg: {
            $cond: [{ $eq: ['$status', 'EXECUTED'] }, 1, 0],
          },
        },
      },
    },
  ]);

  return (
    stats[0] || {
      totalTrades: 0,
      totalProfit: 0,
      avgGasCost: 0,
      successRate: 0,
    }
  );
};

export const Trade = mongoose.model<ITradeDocument, ITradeModel>('Trade', tradeSchema);
export const MarketData = mongoose.model<IMarketDataDocument, IMarketDataModel>(
  'MarketData',
  marketDataSchema
);

export default {
  Trade,
  MarketData,
};
