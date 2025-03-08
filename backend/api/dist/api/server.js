"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.createServer = createServer;
const compression_1 = __importDefault(require("compression"));
const cors_1 = __importDefault(require("cors"));
const express_1 = __importDefault(require("express"));
const helmet_1 = __importDefault(require("helmet"));
const mongoose_1 = __importDefault(require("mongoose"));
const ioredis_1 = require("ioredis");
const http_1 = require("http");
const config_1 = require("./config");
const WebSocketService_1 = require("./websocket/WebSocketService");
const trades_1 = require("./routes/trades");
const status_1 = require("./routes/status");
const bypassTokenMiddleware_1 = require("./middleware/bypassTokenMiddleware");
const admin_1 = require("./routes/admin");
const ai_1 = __importDefault(require("./routes/ai"));
const bot_control_1 = __importDefault(require("./routes/bot-control"));
const market_1 = require("./routes/market");
const networkExecutionRoutes_1 = require("./routes/networkExecutionRoutes");
const execution_mode_1 = __importDefault(require("./routes/execution-mode"));
const bypassToken_1 = require("./utils/bypassToken");
const logger_1 = require("./utils/logger");
const rateLimit_1 = require("./middleware/rateLimit");
async function createServer(config) {
    const app = (0, express_1.default)();
    const httpServer = (0, http_1.createServer)(app);
    const wsService = new WebSocketService_1.WebSocketService(httpServer);
    const bypassTokenManager = new bypassToken_1.BypassTokenManager({
        secret: config.bypassTokenSecret || 'your-secret-key',
        expiresIn: config.bypassTokenExpiresIn || '1h',
        maxUsageCount: config.bypassTokenMaxUsage || 1000,
        redisClient: config.redis,
        breachThreshold: config.breachThreshold || 3
    });
    app.use((0, cors_1.default)({
        origin: config.corsOrigin || '*',
        credentials: true,
    }));
    app.use((0, helmet_1.default)());
    app.use((0, compression_1.default)());
    app.use(express_1.default.json());
    app.use(express_1.default.urlencoded({ extended: true }));
    app.use((0, bypassTokenMiddleware_1.createBypassTokenMiddleware)(bypassTokenManager));
    app.use('/api/v1/market/data', rateLimit_1.marketDataLimiter);
    app.use('/api/v1/market/volatility', rateLimit_1.volatilityLimiter);
    app.use('/api/v1/market/opportunities', rateLimit_1.opportunitiesLimiter);
    app.use('/api/v1/trades', (0, trades_1.createTradeRouter)(wsService));
    app.use('/api/v1/status', (0, status_1.createStatusRouter)());
    app.use('/api/v1/ai', ai_1.default);
    app.use('/api/v1/bot-control', bot_control_1.default);
    app.use('/api/v1/market', (0, market_1.createMarketRouter)());
    app.use('/api/admin', (0, admin_1.createAdminRouter)(bypassTokenManager));
    app.use('/api/v1/network-execution', (0, networkExecutionRoutes_1.createNetworkExecutionRouter)(wsService));
    app.use('/api/v1/execution-mode', execution_mode_1.default);
    app.get('/', (req, res) => {
        res.json({
            status: 'ok',
            message: 'ArbitrageX API is running',
            version: '1.0.0',
            endpoints: {
                trades: '/api/v1/trades',
                status: '/api/v1/status',
                ai: '/api/v1/ai',
                botControl: '/api/v1/bot-control',
                market: '/api/v1/market',
                admin: '/api/admin',
                networkExecution: '/api/v1/network-execution',
                executionMode: '/api/v1/execution-mode'
            }
        });
    });
    app.use((err, req, res, next) => {
        logger_1.logger.error('Unhandled error:', err);
        res.status(500).json({
            error: 'Internal Server Error',
            message: process.env.NODE_ENV === 'development' ? err.message : undefined,
        });
    });
    if (mongoose_1.default.connection.readyState === 0) {
        await mongoose_1.default.connect(config.mongoUri);
    }
    return { app, server: httpServer };
}
if (require.main === module) {
    const redisClient = new ioredis_1.Redis({
        host: process.env.REDIS_HOST || 'localhost',
        port: Number(process.env.REDIS_PORT) || 6379,
        password: process.env.REDIS_PASSWORD,
        enableOfflineQueue: false
    });
    createServer({
        redis: redisClient,
        mongoUri: config_1.config.mongoUri || 'mongodb://localhost:27017/arbitragex',
    }).then(({ app, server }) => {
        const PORT = process.env.PORT || 3000;
        server.listen(PORT, () => {
            logger_1.logger.info(`Server running on port ${PORT} in ${process.env.NODE_ENV} mode`);
        });
        const shutdown = async () => {
            logger_1.logger.info('Shutting down gracefully...');
            try {
                await redisClient.quit();
                await mongoose_1.default.connection.close();
                server.close(() => {
                    logger_1.logger.info('HTTP server closed');
                    process.exit(0);
                });
            }
            catch (error) {
                logger_1.logger.error('Error during shutdown:', error);
                process.exit(1);
            }
        };
        process.on('SIGTERM', shutdown);
        process.on('SIGINT', shutdown);
    });
}
exports.default = createServer;
//# sourceMappingURL=server.js.map