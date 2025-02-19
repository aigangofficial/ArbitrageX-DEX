import { Document, model, Model, Schema } from 'mongoose';

export interface ITrade extends Document {
  tokenA: string;
  tokenB: string;
  amountIn: string;
  amountOut?: string;
  route: 'UNIV2_TO_SUSHI' | 'SUSHI_TO_UNIV2';
  status:
    | 'pending'
    | 'executing'
    | 'completed'
    | 'failed'
    | 'simulated'
    | 'simulated_valid'
    | 'simulated_invalid';
  timestamp: Date;
  network: string;
  txHash?: string;
  gasUsed?: string;
  errorMessage?: string;
  profit?: string;
  priceImpact?: number;
  flashLoanFee?: string;
  slippage?: number;
}

interface TradeModel extends Model<ITrade> {
  getStatistics(timeframe: string): Promise<any>;
  getRecentSuccessful(limit: number): Promise<ITrade[]>;
}

const TradeSchema = new Schema<ITrade>(
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
    amountIn: {
      type: String,
      required: true,
    },
    amountOut: {
      type: String,
    },
    route: {
      type: String,
      enum: ['UNIV2_TO_SUSHI', 'SUSHI_TO_UNIV2'],
      required: true,
      index: true,
    },
    status: {
      type: String,
      enum: [
        'pending',
        'executing',
        'completed',
        'failed',
        'simulated',
        'simulated_valid',
        'simulated_invalid',
      ],
      required: true,
      default: 'pending',
      index: true,
    },
    timestamp: {
      type: Date,
      required: true,
      default: Date.now,
      index: true,
    },
    network: {
      type: String,
      required: true,
      index: true,
    },
    txHash: {
      type: String,
      sparse: true,
    },
    gasUsed: {
      type: String,
    },
    errorMessage: {
      type: String,
    },
    profit: {
      type: String,
    },
    priceImpact: {
      type: Number,
    },
    flashLoanFee: {
      type: String,
    },
    slippage: {
      type: Number,
    },
  },
  {
    timestamps: true,
  }
);

// Create compound indexes for common queries
TradeSchema.index({ tokenA: 1, tokenB: 1, status: 1 });
TradeSchema.index({ timestamp: 1, status: 1 });
TradeSchema.index({ network: 1, status: 1 });

// Static method to get trade statistics
TradeSchema.statics.getStatistics = async function (timeframe: string) {
  const timeframes: { [key: string]: number } = {
    '1h': 1,
    '24h': 24,
    '7d': 168,
    '30d': 720,
  };

  const hours = timeframes[timeframe] || 24;
  const since = new Date(Date.now() - hours * 60 * 60 * 1000);

  const [stats] = await this.aggregate([
    {
      $match: {
        timestamp: { $gte: since },
      },
    },
    {
      $group: {
        _id: null,
        totalTrades: { $sum: 1 },
        completedTrades: {
          $sum: {
            $cond: [{ $eq: ['$status', 'completed'] }, 1, 0],
          },
        },
        totalProfit: {
          $sum: { $ifNull: ['$profit', 0] },
        },
        totalGasUsed: {
          $sum: { $ifNull: ['$gasUsed', 0] },
        },
      },
    },
    {
      $project: {
        _id: 0,
        totalTrades: 1,
        successRate: {
          $multiply: [{ $divide: ['$completedTrades', '$totalTrades'] }, 100],
        },
        totalProfit: 1,
        averageGasUsed: {
          $divide: ['$totalGasUsed', '$totalTrades'],
        },
      },
    },
  ]);

  return (
    stats || {
      totalTrades: 0,
      successRate: 0,
      totalProfit: 0,
      averageGasUsed: 0,
    }
  );
};

// Static method to get recent successful trades
TradeSchema.statics.getRecentSuccessful = async function (limit: number = 10): Promise<ITrade[]> {
  return this.find({ status: 'completed' }).sort({ timestamp: -1 }).limit(limit).lean();
};

export const Trade = model<ITrade, TradeModel>('Trade', TradeSchema);
