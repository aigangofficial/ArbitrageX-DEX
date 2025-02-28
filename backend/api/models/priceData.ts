import mongoose, { Document, Schema } from 'mongoose';

export interface IPriceData extends Document {
  token: string;
  exchange: string;
  price: string;
  liquidity: string;
  timestamp: Date;
  blockNumber: number;
  volume24h: string;
  priceChange24h: string;
}

const PriceDataSchema = new Schema({
  token: {
    type: String,
    required: true,
    index: true
  },
  exchange: {
    type: String,
    required: true,
    index: true
  },
  price: {
    type: String,
    required: true
  },
  liquidity: {
    type: String,
    required: true
  },
  timestamp: {
    type: Date,
    default: Date.now,
    index: true
  },
  blockNumber: {
    type: Number,
    required: true,
    index: true
  },
  volume24h: {
    type: String,
    required: true
  },
  priceChange24h: {
    type: String,
    required: true
  }
}, {
  timestamps: true
});

// Create compound indexes for common queries
PriceDataSchema.index({ token: 1, exchange: 1 });
PriceDataSchema.index({ timestamp: 1 }, { expireAfterSeconds: 7 * 24 * 60 * 60 }); // TTL index for 7 days

export const PriceData = mongoose.model<IPriceData>('PriceData', PriceDataSchema);
