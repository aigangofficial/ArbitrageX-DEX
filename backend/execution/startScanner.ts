import { logger } from '../api/utils/logger';
import ArbitrageScanner from './arbitrageScanner';

async function main() {
  try {
    const scanner = new ArbitrageScanner();
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
