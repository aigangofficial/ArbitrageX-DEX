'use strict';
Object.defineProperty(exports, '__esModule', { value: true });
exports.PriceAggregator = void 0;
const bignumber_1 = require('@ethersproject/bignumber');
const events_1 = require('events');
const logger_1 = require('../utils/logger');
class PriceAggregator extends events_1.EventEmitter {
  constructor(cexFeed, dexScanner) {
    super();
    this.cexFeed = cexFeed;
    this.dexScanner = dexScanner;
    this.prices = new Map();
    this.MIN_PROFIT_THRESHOLD = 0.5; // 0.5% minimum spread
    this.updateInterval = null;
    this.UPDATE_INTERVAL = 1000; // 1 second
    this.setupEventHandlers();
  }
  setupEventHandlers() {
    this.cexFeed.on('priceUpdate', update => {
      this.handleCEXPriceUpdate(update);
    });
    this.dexScanner.on('arbitrageOpportunity', opportunity => {
      this.handleDEXPriceUpdate(opportunity);
    });
  }
  handleCEXPriceUpdate(update) {
    const current = this.prices.get(update.symbol) || {
      symbol: update.symbol,
      dexPrices: {},
      cexPrices: {},
      timestamp: Date.now(),
      arbitrageOpportunities: [],
    };
    current.cexPrices[update.exchange] = update.price;
    current.timestamp = update.timestamp;
    this.prices.set(update.symbol, current);
    this.checkArbitrageOpportunities(update.symbol);
  }
  handleDEXPriceUpdate(opportunity) {
    const symbol = opportunity.pair;
    const current = this.prices.get(symbol) || {
      symbol,
      dexPrices: {
        uniswap: '',
        sushiswap: '',
      },
      cexPrices: {},
      timestamp: Date.now(),
      arbitrageOpportunities: [],
    };
    current.dexPrices['uniswap'] = opportunity.uniswapPrice;
    current.dexPrices['sushiswap'] = opportunity.sushiswapPrice;
    current.timestamp = opportunity.timestamp;
    this.prices.set(symbol, current);
    this.checkArbitrageOpportunities(symbol);
  }
  checkArbitrageOpportunities(symbol) {
    const priceData = this.prices.get(symbol);
    if (!priceData) return;
    const opportunities = [];
    // Compare CEX vs DEX prices
    for (const [cexName, cexPrice] of Object.entries(priceData.cexPrices)) {
      for (const [dexName, dexPrice] of Object.entries(priceData.dexPrices)) {
        const spread = this.calculateSpread(
          bignumber_1.BigNumber.from(cexPrice),
          bignumber_1.BigNumber.from(dexPrice)
        );
        if (spread.gte(this.MIN_PROFIT_THRESHOLD)) {
          opportunities.push({
            sourceExchange: spread.isNegative() ? dexName : cexName,
            targetExchange: spread.isNegative() ? cexName : dexName,
            symbol,
            spreadPercentage: spread.abs().toString(),
            estimatedProfit: this.estimateProfit(
              bignumber_1.BigNumber.from(cexPrice),
              bignumber_1.BigNumber.from(dexPrice)
            ).toString(),
            timestamp: Date.now(),
          });
        }
      }
    }
    if (opportunities.length > 0) {
      priceData.arbitrageOpportunities = opportunities;
      this.emit('arbitrageOpportunity', opportunities);
    }
  }
  calculateSpread(price1, price2) {
    const diff = price1.sub(price2);
    const min = price1.lt(price2) ? price1 : price2;
    return diff.mul(100).div(min);
  }
  estimateProfit(price1, price2) {
    const diff = price1.sub(price2).abs();
    const amount = bignumber_1.BigNumber.from('1000000000000000000'); // 1 ETH
    return diff.mul(amount).div(price1);
  }
  start() {
    if (this.updateInterval) return;
    this.cexFeed.start();
    this.dexScanner.start();
    this.updateInterval = setInterval(() => {
      this.emit('priceUpdate', Array.from(this.prices.values()));
    }, this.UPDATE_INTERVAL);
    logger_1.logger.info('Price aggregator started');
  }
  stop() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }
    this.cexFeed.stop();
    this.dexScanner.stop();
    logger_1.logger.info('Price aggregator stopped');
  }
  getPrices() {
    return Array.from(this.prices.values());
  }
  getArbitrageOpportunities() {
    const opportunities = [];
    for (const price of this.prices.values()) {
      opportunities.push(...price.arbitrageOpportunities);
    }
    return opportunities;
  }
}
exports.PriceAggregator = PriceAggregator;
exports.default = PriceAggregator;
//# sourceMappingURL=priceAggregator.js.map
