"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const price_feed_service_1 = require("./price-feed.service");
let priceFeed;
async function startServer() {
    priceFeed = new price_feed_service_1.PriceFeedService();
    await priceFeed.start();
}
async function stopServer() {
    if (priceFeed) {
        await priceFeed.stop();
    }
}
process.on('SIGINT', async () => {
    await stopServer();
    process.exit(0);
});
startServer().catch(error => {
    console.error('Failed to start price feed server:', error);
    process.exit(1);
});
//# sourceMappingURL=server.js.map