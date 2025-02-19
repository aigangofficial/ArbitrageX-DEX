import { RealPriceFeed } from './index';

// Start the real price feed
const priceFeed = new RealPriceFeed();
priceFeed.start().catch((error: Error) => {
  console.error('Failed to start price feed:', error);
  process.exit(1);
});

// Handle graceful shutdown
process.on('SIGINT', async () => {
  await priceFeed.stop();
  process.exit(0);
});
