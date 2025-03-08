'use strict';
/**
 * @title Configuration Management Utility
 * @description Manages configuration settings and environment variables for the ArbitrageX system
 *
 * FEATURES:
 * 1. Environment Management:
 *    - Loads and validates environment variables
 *    - Sets up network-specific configurations
 *    - Manages API keys and endpoints
 *
 * 2. Contract Configuration:
 *    - Stores contract addresses
 *    - Manages network parameters
 *    - Handles gas price settings
 *
 * 3. Security Settings:
 *    - Validates security parameters
 *    - Manages access controls
 *    - Handles sensitive data
 *
 * USAGE:
 * ```typescript
 * import { loadConfig, updateConfig } from './utils/config';
 *
 * // Load configuration
 * const config = loadConfig();
 *
 * // Update configuration
 * await updateConfig({ network: 'sepolia' });
 * ```
 *
 * @requires dotenv
 * @requires fs
 */
Object.defineProperty(exports, '__esModule', { value: true });
exports.AMOY_CONFIG = void 0;
const hardhat_1 = require('hardhat');
exports.AMOY_CONFIG = {
  aavePool: '0x357D51124f59836DeD84c8a1730D72B749d8BC23',
  quickswapRouter: '0x8954AfA98594b838bda56FE4C12a09D7739D179b',
  sushiswapRouter: '0x0C8B5D4bf676BD283c4F343c260bC668aa07aF49',
  wmatic: '0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889',
  gas: {
    limit: 2000000,
    maxFeePerGas: hardhat_1.ethers.parseUnits('50', 'gwei'),
    maxPriorityFeePerGas: hardhat_1.ethers.parseUnits('25', 'gwei'),
  },
};
