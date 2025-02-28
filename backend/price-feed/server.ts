import { logger } from '../api/utils/logger';
import RealPriceFeed from './index';

// Start the real price feed
async function main() {
  try {
    const priceFeed = new RealPriceFeed();
    await priceFeed.start();
  } catch (error) {
    logger.error('Error starting price feed:', error);
    process.exit(1);
  }
}

main();

// Handle graceful shutdown
process.on('SIGINT', async () => {
  await priceFeed.stop();
  process.exit(0);
});
