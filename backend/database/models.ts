import mongoose, { Schema, Document } from 'mongoose';

export interface IArbitrageTrade extends Document {
    tokenA: string;
    tokenB: string;
    exchangeA: string;
    exchangeB: string;
    amountIn: string;
    expectedProfit: string;
    actualProfit?: string;
    gasUsed?: string;
    status: 'pending' | 'executed' | 'failed';
    txHash?: string;
    errorMessage?: string;
    timestamp: Date;
}

const ArbitrageTradeSchema: Schema = new Schema({
    tokenA: { type: String, required: true },
    tokenB: { type: String, required: true },
    exchangeA: { type: String, required: true },
    exchangeB: { type: String, required: true },
    amountIn: { type: String, required: true },
    expectedProfit: { type: String, required: true },
    actualProfit: { type: String },
    gasUsed: { type: String },
    status: { 
        type: String, 
        enum: ['pending', 'executed', 'failed'],
        default: 'pending'
    },
    txHash: { type: String },
    errorMessage: { type: String },
    timestamp: { type: Date, default: Date.now }
});

export const ArbitrageTrade = mongoose.model<IArbitrageTrade>('ArbitrageTrade', ArbitrageTradeSchema); 