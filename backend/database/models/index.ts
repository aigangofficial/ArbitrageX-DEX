import mongoose from 'mongoose';
import { ArbitrageTradeSchema } from './ArbitrageTrade';

// Export models only if they haven't been compiled yet
export const ArbitrageTrade =
  mongoose.models.ArbitrageTrade || mongoose.model('ArbitrageTrade', ArbitrageTradeSchema);

export type { IArbitrageTrade } from './ArbitrageTrade';
