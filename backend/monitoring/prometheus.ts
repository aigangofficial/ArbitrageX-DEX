import client, { Registry } from 'prom-client';

// Create a Registry to store metrics
const register = new Registry();

// Gas metrics
export const gasUsedGauge = new client.Gauge({
  name: 'arbitrage_gas_used',
  help: 'Gas used per arbitrage trade',
  labelNames: ['token_pair'] as const,
  registers: [register]
});

export const gasPriceGauge = new client.Gauge({
  name: 'arbitrage_gas_price',
  help: 'Current gas price in gwei',
  registers: [register]
});

// Profit metrics
export const profitGauge = new client.Gauge({
  name: 'arbitrage_profit',
  help: 'Profit from arbitrage trade in USD',
  labelNames: ['token_pair'] as const,
  registers: [register]
});

export const profitRatioGauge = new client.Gauge({
  name: 'arbitrage_profit_ratio',
  help: 'Profit ratio percentage from arbitrage trade',
  labelNames: ['token_pair'] as const,
  registers: [register]
});

// Performance metrics
export const latencyHistogram = new client.Histogram({
  name: 'arbitrage_execution_latency',
  help: 'Latency of arbitrage execution in milliseconds',
  buckets: [100, 200, 300, 400, 500, 1000],
  registers: [register]
});

export const tradeCountCounter = new client.Counter({
  name: 'arbitrage_trade_count',
  help: 'Number of arbitrage trades executed',
  labelNames: ['status', 'token_pair'] as const,
  registers: [register]
});

// Alert thresholds
export const failureRateGauge = new client.Gauge({
  name: 'arbitrage_failure_rate',
  help: 'Percentage of failed trades in the last hour',
  registers: [register]
});

export const profitMarginGauge = new client.Gauge({
  name: 'arbitrage_profit_margin',
  help: 'Current profit margin percentage',
  labelNames: ['token_pair'] as const,
  registers: [register]
});

// Initialize metrics collection
client.collectDefaultMetrics({
  register,
  prefix: 'arbitragex_'
});

export { register };
