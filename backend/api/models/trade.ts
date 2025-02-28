import mongoose, { Document, Schema } from 'mongoose';

export interface ITrade extends Document {
  tokenA: string;
  tokenB: string;
  amountIn: string;
  amountOut: string;
  expectedProfit: string;
  actualProfit: string;
  gasUsed: string;
  gasPrice: string;
  status: 'pending' | 'completed' | 'failed';
  txHash?: string;
  route?: {
    path: string[];
    exchanges: string[];
  };
  createdAt: Date;
  updatedAt: Date;
}

const TradeSchema = new Schema({
  tokenA: {
    type: String,
    required: true,
    index: true
  },
  tokenB: {
    type: String,
    required: true,
    index: true
  },
  amountIn: {
    type: String,
    required: true
  },
  amountOut: {
    type: String,
    required: true
  },
  expectedProfit: {
    type: String,
    required: true
  },
  actualProfit: {
    type: String,
    required: true
  },
  gasUsed: {
    type: String,
    required: true
  },
  gasPrice: {
    type: String,
    required: true
  },
  status: {
    type: String,
    enum: ['pending', 'completed', 'failed'],
    required: true,
    index: true
  },
  txHash: {
    type: String,
    sparse: true
  },
  route: {
    path: [{
      type: String,
      required: true
    }],
    exchanges: [{
      type: String,
      required: true
    }]
  }
}, {
  timestamps: true
});

// Create indexes for common queries
TradeSchema.index({ status: 1, updatedAt: -1 });
TradeSchema.index({ tokenA: 1, tokenB: 1, status: 1 });

export const Trade = mongoose.model<ITrade>('Trade', TradeSchema);
