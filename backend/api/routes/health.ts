import express from 'express';
import { RedisService } from '../services/redis';
import { MongoDBService } from '../services/mongodb';
import { AIService } from '../services/ai';
import { logger } from '../utils/logger';

const router = express.Router();

router.get('/', async (_req, res) => {
    try {
        const [isRedisConnected, isMongoConnected] = await Promise.all([
            RedisService.isConnected(),
            MongoDBService.isConnected()
        ]);

        const aiStatus = await AIService.getStatus();
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
    } catch (error) {
        logger.error('Health check error:', error);
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

export default router;
