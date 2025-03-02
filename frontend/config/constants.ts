// API Configuration
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3000';

// Bot Configuration
export const DEFAULT_RUN_TIME = 600; // 10 minutes
export const DEFAULT_TOKENS = 'WETH,USDC,DAI';
export const DEFAULT_DEXES = 'uniswap_v3,curve,balancer';
export const DEFAULT_GAS_STRATEGY = 'dynamic';

// Gas Strategy Options
export const GAS_STRATEGIES = [
  { value: 'dynamic', label: 'Dynamic' },
  { value: 'aggressive', label: 'Aggressive' },
  { value: 'conservative', label: 'Conservative' }
]; 