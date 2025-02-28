// Import models
import { IPriceData, PriceData } from './priceData';
import { IStrategy, Strategy } from './strategy';
import { ITrade, Trade } from './trade';

// Export interfaces
export {
    IPriceData,
    IStrategy,
    ITrade
};

// Export models
    export {
        PriceData,
        Strategy,
        Trade
    };

// Export a models object for convenience
export const models = {
  PriceData,
  Strategy,
  Trade
};
