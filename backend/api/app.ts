import express, { Express, Request, Response, NextFunction } from 'express';
import Redis from 'ioredis';
import cors from 'cors';
import rateLimit from 'express-rate-limit';
import aiRouter from './routes/ai';
import healthRouter from './routes/health';
import botControlRouter from './routes/bot-control';
import { errorHandler } from './middleware/errorHandler';
import { logger } from './utils/logger';

export async function createApp(redis: Redis): Promise<Express> {
  // Wait for Redis to be ready
  try {
    await redis.ping();
  } catch (error) {
    logger.error('Redis connection failed:', error);
  }

  const app = express();

  // Basic middleware
  app.use(cors());
  
  // Configure JSON middleware first
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));

  // Global JSON content type middleware
  app.use((_req: Request, res: Response, next: NextFunction) => {
    res.setHeader('Content-Type', 'application/json');
    const originalJson = res.json;
    const originalSend = res.send;

    res.json = function(body) {
      res.setHeader('Content-Type', 'application/json');
      return originalJson.call(this, body);
    };

    res.send = function(body) {
      if (body && typeof body === 'object') {
        res.setHeader('Content-Type', 'application/json');
        return res.json(body);
      }
      res.setHeader('Content-Type', 'application/json');
      return originalSend.call(this, JSON.stringify({ message: body }));
    };

    next();
  });

  // Configure rate limiter with higher limits for tests
  const aiLimiter = rateLimit({
    windowMs: 1000,
    max: process.env.NODE_ENV === 'test' ? 100 : 2,
    message: { 
      success: false, 
      error: 'Too many requests, please try again later.'
    },
    standardHeaders: true,
    legacyHeaders: false,
    handler: (req: Request, res: Response) => {
      res.status(429).json({
        success: false,
        error: 'Too many requests, please try again later.'
      });
    }
  });

  // Routes with rate limiting
  app.use('/api/v1/ai', aiLimiter, aiRouter);
  app.use('/health', healthRouter);
  app.use('/api/v1/bot-control', botControlRouter);

  // Catch 404 and forward to error handler
  app.use((req: Request, _res: Response, next: NextFunction) => {
    const err = new Error(`Not Found - ${req.originalUrl}`);
    err.name = 'NotFoundError';
    next(err);
  });

  // Error handling middleware should be last
  app.use(errorHandler);

  return app;
} 