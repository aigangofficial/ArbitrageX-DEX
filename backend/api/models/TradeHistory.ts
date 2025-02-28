import mongoose, { Schema, Document } from 'mongoose';

export interface ITrade extends Document {
  tokenIn: string;
  tokenOut: string;
  amountIn: string;
  amountOut: string;
  profit: string;
  gasUsed: number;
  gasPrice: string;
  txHash: string;
  blockNumber: number;
  timestamp: Date;
  router: string;
  status: 'pending' | 'completed' | 'failed';
  error?: string;
}

const TradeHistorySchema: Schema = new Schema({
  tokenIn: { type: String, required: true, index: true },
  tokenOut: { type: String, required: true, index: true },
  amountIn: { type: String, required: true },
  amountOut: { type: String, required: true },
  profit: { type: String, required: true },
  gasUsed: { type: Number, required: true },
  gasPrice: { type: String, required: true },
  txHash: { type: String, required: true, unique: true },
  blockNumber: { type: Number, required: true, index: true },
  timestamp: { type: Date, required: true, index: true },
  router: { type: String, required: true },
  status: { 
    type: String, 
    required: true, 
    enum: ['pending', 'completed', 'failed'],
    default: 'pending'
  },
  error: { type: String }
}, {
  timestamps: true,
  versionKey: false
});

// Create indexes for common queries
TradeHistorySchema.index({ timestamp: -1 });
TradeHistorySchema.index({ status: 1, timestamp: -1 });
TradeHistorySchema.index({ tokenIn: 1, tokenOut: 1, timestamp: -1 });

export const TradeHistory = mongoose.model<ITrade>('TradeHistory', TradeHistorySchema); 