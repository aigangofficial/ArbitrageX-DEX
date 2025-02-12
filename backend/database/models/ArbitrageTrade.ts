import mongoose, { Document, Schema } from 'mongoose';

export interface IArbitrageTrade extends Document {
  tokenA: string;
  tokenB: string;
  amount: number;
  exchangeA: string;
  exchangeB: string;
  path: string[];
  expectedProfit: number;
  status: 'pending' | 'executing' | 'completed' | 'failed';
  txHash?: string;
  error?: string;
  createdAt: Date;
  updatedAt: Date;
}

export const ArbitrageTradeSchema = new Schema(
  {
    tokenA: { type: String, required: true },
    tokenB: { type: String, required: true },
    amount: { type: Number, required: true },
    exchangeA: { type: String, required: true },
    exchangeB: { type: String, required: true },
    path: [{ type: String, required: true }],
    expectedProfit: { type: Number, required: true },
    status: {
      type: String,
      enum: ['pending', 'executing', 'completed', 'failed'],
      default: 'pending',
      required: true,
    },
    txHash: { type: String },
    error: { type: String },
  },
  {
    timestamps: true,
    versionKey: false,
  }
);

// Create indexes for faster queries
ArbitrageTradeSchema.index({ status: 1 });
ArbitrageTradeSchema.index({ createdAt: -1 });
ArbitrageTradeSchema.index({ tokenA: 1, tokenB: 1 });

// Check if model exists before creating
export const ArbitrageTrade =
  mongoose.models.ArbitrageTrade ||
  mongoose.model<IArbitrageTrade>('ArbitrageTrade', ArbitrageTradeSchema);
