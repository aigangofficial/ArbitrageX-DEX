import { ethers } from 'ethers';
import { config } from '../api/config';
import { logger } from '../api/utils/logger';
import ArbitrageScanner from './arbitrageScanner';

async function main() {
  try {
    const provider = new ethers.JsonRpcProvider(config.network.rpc);
    const scanner = new ArbitrageScanner(
      provider,
      config.contracts.quickswapRouter,
      config.contracts.sushiswapRouter,
      config.contracts.aavePool
    );
    await scanner.start();

    // Handle graceful shutdown
    process.on('SIGINT', async () => {
      logger.info('Stopping arbitrage scanner...');
      scanner.stop();
      process.exit(0);
    });
  } catch (error) {
    logger.error('Error starting arbitrage scanner:', error);
    process.exit(1);
  }
}

main();
