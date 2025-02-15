import rateLimit from 'express-rate-limit';
import { logger } from '../utils/logger';

const createLimiter = (windowMs: number, max: number, endpoint: string) => {
  return rateLimit({
    windowMs,
    max,
    standardHeaders: true,
    legacyHeaders: false,
    handler: (req, res) => {
      logger.warn(`Rate limit exceeded for ${endpoint} by ${req.ip}`);
      res.status(429).json({
        error: 'Too many requests',
        message: 'Please try again later',
        retryAfter: Math.ceil(windowMs / 1000),
      });
    },
  });
};

// Market data endpoint: 100 requests per minute
export const marketDataLimiter = createLimiter(60 * 1000, 100, '/api/market/data');

// Volatility endpoint: 60 requests per minute
export const volatilityLimiter = createLimiter(60 * 1000, 60, '/api/market/volatility');

// Opportunities endpoint: 30 requests per minute
export const opportunitiesLimiter = createLimiter(60 * 1000, 30, '/api/market/opportunities');

// WebSocket subscriptions: 10 requests per minute
export const wsSubscriptionLimiter = createLimiter(60 * 1000, 10, '/api/market/subscribe');
