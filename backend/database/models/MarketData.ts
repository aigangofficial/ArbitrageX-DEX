import mongoose, { Document, Model, PipelineStage, Schema } from 'mongoose';

interface IMarketDataMethods {
  calculateArbitrageOpportunity(): {
    direction: 'SUSHI_TO_UNIV2' | 'UNIV2_TO_SUSHI';
    priceDiff: bigint;
    maxTradeSize: bigint;
    potentialProfit: bigint;
  };
}

interface IMarketDataModel extends Model<IMarketData, {}, IMarketDataMethods> {
  getRecentPrices(pair: string, limit?: number, network?: string): Promise<IMarketData[]>;
  getVolatility(pair: string, hours?: number, network?: string): Promise<any>;
  findArbitrageOpportunities(
    minSpreadPercentage?: number,
    network?: string
  ): Promise<IMarketData[]>;
}

export interface IMarketData extends Document {
  tokenA: string;
  tokenB: string;
  exchange: string;
  price: number;
  liquidity: number;
  timestamp: Date;
  blockNumber: number;
  txHash?: string;
  priceImpact?: number;
  spread?: number;
}

const MarketDataSchema = new Schema<IMarketData>(
  {
    tokenA: {
      type: String,
      required: true,
      index: true,
    },
    tokenB: {
      type: String,
      required: true,
      index: true,
    },
    exchange: {
      type: String,
      required: true,
      enum: ['UNISWAP_V2', 'SUSHISWAP'],
      index: true,
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
      required: true,
      index: true,
    },
    blockNumber: {
      type: Number,
      required: true,
      index: true,
    },
    txHash: {
      type: String,
      sparse: true,
    },
    priceImpact: {
      type: Number,
    },
    spread: {
      type: Number,
      index: true,
    },
  },
  {
    timestamps: true,
  }
);

// Create compound indexes for common queries
MarketDataSchema.index({ tokenA: 1, tokenB: 1, exchange: 1 });
MarketDataSchema.index({ timestamp: 1, exchange: 1 });
MarketDataSchema.index({ blockNumber: 1, exchange: 1 });

// Static method to find arbitrage opportunities
MarketDataSchema.statics.findArbitrageOpportunities = async function (
  minSpreadPercentage: number = 0.5
): Promise<IMarketData[]> {
  const pipeline: PipelineStage[] = [
    {
      $group: {
        _id: {
          tokenA: '$tokenA',
          tokenB: '$tokenB',
          exchange: '$exchange',
        },
        latestPrice: { $last: '$price' },
        latestLiquidity: { $last: '$liquidity' },
        latestTimestamp: { $last: '$timestamp' },
      },
    } as PipelineStage,
    {
      $group: {
        _id: {
          tokenA: '$_id.tokenA',
          tokenB: '$_id.tokenB',
        },
        exchanges: {
          $push: {
            exchange: '$_id.exchange',
            price: '$latestPrice',
            liquidity: '$latestLiquidity',
            timestamp: '$latestTimestamp',
          },
        },
      },
    } as PipelineStage,
    {
      $match: {
        'exchanges.1': { $exists: true },
      },
    } as PipelineStage,
    {
      $addFields: {
        spread: {
          $let: {
            vars: {
              prices: '$exchanges.price',
              maxPrice: { $max: '$exchanges.price' },
              minPrice: { $min: '$exchanges.price' },
            },
            in: {
              $multiply: [
                {
                  $divide: [
                    { $subtract: ['$$maxPrice', '$$minPrice'] },
                    '$$minPrice',
                  ],
                },
                100,
              ],
            },
          },
        },
      },
    } as PipelineStage,
    {
      $match: {
        spread: { $gte: minSpreadPercentage },
      },
    } as PipelineStage,
    {
      $sort: {
        spread: -1,
      },
    } as PipelineStage,
  ];

  return this.aggregate(pipeline);
};

export const MarketData = mongoose.model<IMarketData, IMarketDataModel>(
  'MarketData',
  MarketDataSchema
);
