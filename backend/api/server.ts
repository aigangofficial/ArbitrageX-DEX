import compression from 'compression';
import cors from 'cors';
import express, { Express } from 'express';
import helmet from 'helmet';
import mongoose from 'mongoose';
import { Redis } from 'ioredis';
import { Server, createServer as createHttpServer } from 'http';
import { config } from './config';
import { WebSocketService } from './websocket/WebSocketService';
import { createTradeRouter } from './routes/trades';
import { createStatusRouter } from './routes/status';
import { createBypassTokenMiddleware } from './middleware/bypassTokenMiddleware';
import { createAdminRouter } from './routes/admin';
import { aiRouter } from './routes/ai';
import { createMarketRouter } from './routes/market';
import { BypassTokenManager } from './utils/bypassToken';
import { logger } from './utils/logger';
import { marketDataLimiter, volatilityLimiter, opportunitiesLimiter } from './middleware/rateLimit';
import { createApp } from './app';

interface ServerConfig {
  redis: Redis;
  mongoUri: string;
  bypassTokenSecret?: string;
  bypassTokenExpiresIn?: string;
  bypassTokenMaxUsage?: number;
  breachThreshold?: number;
  corsOrigin?: string;
}

export async function createServer(config: ServerConfig): Promise<Express> {
  const app = express();
  const httpServer = createHttpServer(app);

  // Initialize WebSocket service
  const wsService = new WebSocketService(httpServer);

  // Initialize bypass token manager
  const bypassTokenManager = new BypassTokenManager({
    secret: config.bypassTokenSecret || 'your-secret-key',
    expiresIn: config.bypassTokenExpiresIn || '1h',
    maxUsageCount: config.bypassTokenMaxUsage || 1000,
    redisClient: config.redis,
    breachThreshold: config.breachThreshold || 3
  });

  // Apply middleware
  app.use(
    cors({
      origin: config.corsOrigin || '*',
      credentials: true,
    })
  );
  app.use(helmet());
  app.use(compression());
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));

  // Apply bypass token middleware before rate limiting
  app.use(createBypassTokenMiddleware(bypassTokenManager));

  // Apply rate limiting to specific routes
  app.use('/api/v1/market/data', marketDataLimiter);
  app.use('/api/v1/market/volatility', volatilityLimiter);
  app.use('/api/v1/market/opportunities', opportunitiesLimiter);

  // Mount API routes
  app.use('/api/v1/trades', createTradeRouter(wsService));
  app.use('/api/v1/status', createStatusRouter());
  app.use('/api/v1/ai', aiRouter);
  app.use('/api/v1/market', createMarketRouter());
  app.use('/api/admin', createAdminRouter(bypassTokenManager));

  // Global error handler
  app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
    logger.error('Unhandled error:', err);
    res.status(500).json({
      error: 'Internal Server Error',
      message: process.env.NODE_ENV === 'development' ? err.message : undefined,
    });
  });

  // Connect to MongoDB if not already connected
  if (mongoose.connection.readyState === 0) {
    await mongoose.connect(config.mongoUri);
  }

  return app;
}

// Only start the server if this file is run directly
if (require.main === module) {
  const redisClient = new Redis({
    host: process.env.REDIS_HOST || 'localhost',
    port: Number(process.env.REDIS_PORT) || 6379,
    password: process.env.REDIS_PASSWORD,
    enableOfflineQueue: false
  });

  createServer({
    redis: redisClient,
    mongoUri: config.mongoUri || 'mongodb://localhost:27017/arbitragex',
  }).then(app => {
    const PORT = process.env.PORT || 3000;
    const server = createHttpServer(app);
    
    server.listen(PORT, () => {
      logger.info(`Server running on port ${PORT} in ${process.env.NODE_ENV} mode`);
    });

    // Graceful shutdown
    const shutdown = async () => {
      logger.info('Shutting down gracefully...');
      
      try {
        // Close Redis connection
        await redisClient.quit();

        // Close MongoDB connection
        await mongoose.connection.close();

        // Close HTTP server
        server.close(() => {
          logger.info('HTTP server closed');
          process.exit(0);
        });
      } catch (error) {
        logger.error('Error during shutdown:', error);
        process.exit(1);
      }
    };

    process.on('SIGTERM', shutdown);
    process.on('SIGINT', shutdown);
  });
}

export default createServer;
