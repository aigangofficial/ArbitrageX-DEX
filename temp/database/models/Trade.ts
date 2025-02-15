import { Document, PipelineStage, Schema, model } from 'mongoose';

export interface ITrade extends Document {
  tokenA: string;
  tokenB: string;
  amountIn: string;
  amountOut?: string;
  route: 'UNIV2_TO_SUSHI' | 'SUSHI_TO_UNIV2';
  status: 'pending' | 'executing' | 'completed' | 'failed';
  timestamp: Date;
  network: string;
  txHash?: string;
  gasUsed?: string;
  errorMessage?: string;
  profit?: string;
  priceImpact?: number;
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
      enum: ['pending', 'executing', 'completed', 'failed'],
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
TradeSchema.statics.getStats = async function (
  network: string,
  timeframe: 'day' | 'week' | 'month' = 'day'
) {
  const now = new Date();
  let startDate: Date;

  switch (timeframe) {
    case 'week':
      startDate = new Date(now.setDate(now.getDate() - 7));
      break;
    case 'month':
      startDate = new Date(now.setMonth(now.getMonth() - 1));
      break;
    default:
      startDate = new Date(now.setDate(now.getDate() - 1));
  }

  const pipeline: PipelineStage[] = [
    {
      $match: {
        network,
        timestamp: { $gte: startDate },
      },
    } as PipelineStage,
    {
      $group: {
        _id: '$status',
        count: { $sum: 1 },
        totalProfit: {
          $sum: {
            $cond: [
              { $eq: ['$status', 'completed'] },
              { $toDouble: { $ifNull: ['$profit', '0'] } },
              0,
            ],
          },
        },
        avgGasUsed: {
          $avg: {
            $cond: [
              { $eq: ['$status', 'completed'] },
              { $toDouble: { $ifNull: ['$gasUsed', '0'] } },
              0,
            ],
          },
        },
      },
    } as PipelineStage,
  ];

  return this.aggregate(pipeline);
};

// Static method to get recent successful trades
TradeSchema.statics.getRecentSuccessful = async function (
  limit: number = 10
): Promise<ITrade[]> {
  return this.find({ status: 'completed' })
    .sort({ timestamp: -1 })
    .limit(limit)
    .lean();
};

export const Trade = model<ITrade>('Trade', TradeSchema);
