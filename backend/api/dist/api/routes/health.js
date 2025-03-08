"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const redis_1 = require("../services/redis");
const mongodb_1 = require("../services/mongodb");
const ai_1 = require("../services/ai");
const logger_1 = require("../utils/logger");
const router = express_1.default.Router();
router.get('/', async (_req, res) => {
    try {
        const [isRedisConnected, isMongoConnected] = await Promise.all([
            redis_1.RedisService.isConnected(),
            mongodb_1.MongoDBService.isConnected()
        ]);
        const aiStatus = await ai_1.AIService.getStatus();
        const isAIReady = aiStatus === 'ready';
        const status = isRedisConnected && isMongoConnected && isAIReady ? 'healthy' : 'unhealthy';
        const statusCode = status === 'healthy' ? 200 : 503;
        const response = {
            status,
            services: {
                mongodb: isMongoConnected ? 'connected' : 'disconnected',
                redis: isRedisConnected ? 'connected' : 'disconnected',
                ai: aiStatus
            },
            timestamp: new Date().toISOString()
        };
        return res.status(statusCode).json(response);
    }
    catch (error) {
        logger_1.logger.error('Health check error:', error);
        return res.status(503).json({
            status: 'unhealthy',
            services: {
                mongodb: 'disconnected',
                redis: 'disconnected',
                ai: 'error'
            },
            timestamp: new Date().toISOString(),
            error: 'Internal server error'
        });
    }
});
exports.default = router;
//# sourceMappingURL=health.js.map