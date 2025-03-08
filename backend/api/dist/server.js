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
const ioredis_1 = __importDefault(require("ioredis"));
const http_1 = require("http");
const config_1 = require("./config");
const WebSocketService_1 = require("./websocket/WebSocketService");
const trades_1 = require("./routes/trades");
const status_1 = require("./routes/status");
const bypassTokenMiddleware_1 = require("./middleware/bypassTokenMiddleware");
const admin_1 = require("./routes/admin");
const ai_1 = require("./routes/ai");
const bypassToken_1 = require("./utils/bypassToken");
const logger_1 = require("./utils/logger");
const rateLimit_1 = require("./middleware/rateLimit");
async function createServer(config) {
    const app = (0, express_1.default)();
    const httpServer = (0, http_1.createServer)(app);
    // Initialize WebSocket service
    const wsService = new WebSocketService_1.WebSocketService(httpServer);
    // Initialize bypass token manager
    const bypassTokenManager = new bypassToken_1.BypassTokenManager({
        secret: config.bypassTokenSecret || 'your-secret-key',
        expiresIn: config.bypassTokenExpiresIn || '1h',
        maxUsageCount: config.bypassTokenMaxUsage || 1000,
        redisClient: config.redis,
        breachThreshold: config.breachThreshold || 3
    });
    // Apply middleware
    app.use((0, cors_1.default)({
        origin: config.corsOrigin || '*',
        credentials: true,
    }));
    app.use((0, helmet_1.default)());
    app.use((0, compression_1.default)());
    app.use(express_1.default.json());
    app.use(express_1.default.urlencoded({ extended: true }));
    // Apply bypass token middleware before rate limiting
    app.use((0, bypassTokenMiddleware_1.createBypassTokenMiddleware)(bypassTokenManager));
    // Apply rate limiting to specific routes
    app.use('/api/v1/market/data', rateLimit_1.marketDataLimiter);
    app.use('/api/v1/market/volatility', rateLimit_1.volatilityLimiter);
    app.use('/api/v1/market/opportunities', rateLimit_1.opportunitiesLimiter);
    // Health check endpoint
    app.get('/api/health', (req, res) => {
        const mongoStatus = mongoose_1.default.connection.readyState === 1;
        const redisStatus = config.redis.status === 'ready';
        const health = {
            status: mongoStatus && redisStatus ? 'healthy' : 'unhealthy',
            services: {
                mongodb: mongoStatus ? 'connected' : 'disconnected',
                redis: redisStatus ? 'connected' : 'disconnected',
                websocket: wsService ? 'connected' : 'disconnected'
            }
        };
        const statusCode = health.status === 'healthy' ? 200 : 503;
        res.status(statusCode).json(health);
    });
    // Mount API routes
    app.use('/api/v1/trades', (0, trades_1.createTradeRouter)(wsService));
    app.use('/api/v1/status', (0, status_1.createStatusRouter)());
    app.use('/api/v1/ai', (0, ai_1.createAIRouter)());
    app.use('/api/admin', (0, admin_1.createAdminRouter)(bypassTokenManager));
    // Global error handler
    app.use((err, req, res, next) => {
        logger_1.logger.error('Unhandled error:', err);
        res.status(500).json({
            error: 'Internal Server Error',
            message: process.env.NODE_ENV === 'development' ? err.message : undefined,
        });
    });
    // Connect to MongoDB if not already connected
    if (mongoose_1.default.connection.readyState === 0) {
        await mongoose_1.default.connect(config.mongoUri);
    }
    return app;
}
// Only start the server if this file is run directly
if (require.main === module) {
    const redisClient = new ioredis_1.default({
        host: process.env.REDIS_HOST || 'localhost',
        port: Number(process.env.REDIS_PORT) || 6379,
        password: process.env.REDIS_PASSWORD,
        enableOfflineQueue: false
    });
    createServer({
        redis: redisClient,
        mongoUri: config_1.config.mongoUri || 'mongodb://localhost:27017/arbitragex',
    }).then(app => {
        const PORT = process.env.PORT || 3000;
        const server = (0, http_1.createServer)(app);
        server.listen(PORT, () => {
            logger_1.logger.info(`Server running on port ${PORT} in ${process.env.NODE_ENV} mode`);
        });
        // Graceful shutdown
        const shutdown = async () => {
            logger_1.logger.info('Shutting down gracefully...');
            try {
                // Close Redis connection
                await redisClient.quit();
                // Close MongoDB connection
                await mongoose_1.default.connection.close();
                // Close HTTP server
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