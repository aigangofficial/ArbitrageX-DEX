import mongoose, { Document, Schema } from 'mongoose';

export interface IStrategy extends Document {
  name: string;
  description: string;
  isActive: boolean;
  tokenPairs: {
    tokenA: string;
    tokenB: string;
  }[];
  minTradeAmount: string;
  maxTradeAmount: string;
  minProfitThreshold: string;
  maxSlippage: string;
  gasLimit: string;
  exchanges: string[];
  performance?: {
    totalTrades: number;
    successfulTrades: number;
    failedTrades: number;
    totalProfit: string;
    averageProfit: string;
    lastUpdated: Date;
  };
  createdAt: Date;
  updatedAt: Date;
}

const StrategySchema = new Schema({
  name: {
    type: String,
    required: true,
    unique: true
  },
  description: {
    type: String,
    required: true
  },
  isActive: {
    type: Boolean,
    default: false
  },
  tokenPairs: [{
    tokenA: {
      type: String,
      required: true
    },
    tokenB: {
      type: String,
      required: true
    }
  }],
  minTradeAmount: {
    type: String,
    required: true
  },
  maxTradeAmount: {
    type: String,
    required: true
  },
  minProfitThreshold: {
    type: String,
    required: true
  },
  maxSlippage: {
    type: String,
    required: true
  },
  gasLimit: {
    type: String,
    required: true
  },
  exchanges: [{
    type: String,
    required: true
  }],
  performance: {
    totalTrades: {
      type: Number,
      default: 0
    },
    successfulTrades: {
      type: Number,
      default: 0
    },
    failedTrades: {
      type: Number,
      default: 0
    },
    totalProfit: {
      type: String,
      default: '0'
    },
    averageProfit: {
      type: String,
      default: '0'
    },
    lastUpdated: {
      type: Date,
      default: Date.now
    }
  }
}, {
  timestamps: true
});

// Create indexes for common queries
StrategySchema.index({ isActive: 1 });
StrategySchema.index({ 'tokenPairs.tokenA': 1, 'tokenPairs.tokenB': 1 });

export const Strategy = mongoose.model<IStrategy>('Strategy', StrategySchema);
