import mongoose from 'mongoose';
import { ArbitrageTradeSchema } from './ArbitrageTrade';

// Export models only if they haven't been compiled yet
export const ArbitrageTrade =
  mongoose.models.ArbitrageTrade || mongoose.model('ArbitrageTrade', ArbitrageTradeSchema);

export type { IArbitrageTrade } from './ArbitrageTrade';

export { MarketData } from './MarketData';
export { Trade } from './Trade';

// Export interfaces
export type { IMarketData } from './MarketData';
export type { ITrade } from './Trade';
