import rateLimit, { Options, Store } from 'express-rate-limit';
import { Request, Response, NextFunction } from 'express';
import Redis from 'ioredis';
import { TokenBucket } from '../utils/tokenBucket';
import { logger } from '../utils/logger';
import { register, Counter, Gauge } from 'prom-client';

// Initialize Redis client
const redisClient = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: Number(process.env.REDIS_PORT) || 6379,
  password: process.env.REDIS_PASSWORD,
  enableOfflineQueue: false
});

// Rate limit metrics
const rateLimitCounter = new Counter({
  name: 'rate_limit_hits_total',
  help: 'Number of rate limit hits',
  labelNames: ['endpoint', 'ip']
});

const rateLimitTokensGauge = new Gauge({
  name: 'rate_limit_tokens_remaining',
  help: 'Number of tokens remaining in bucket',
  labelNames: ['endpoint', 'ip']
});

// Parse whitelisted IPs from environment
const parseWhitelistedIPs = (): Set<string> => {
  const ips = new Set<string>(['127.0.0.1']); // Always include localhost
  
  // Add admin IP if configured
  if (process.env.ADMIN_IP) {
    ips.add(process.env.ADMIN_IP);
  }
  
  // Add additional IPs from comma-separated list
  const additionalIPs = process.env.WHITELISTED_IPS?.split(',').filter(Boolean) || [];
  additionalIPs.forEach(ip => ips.add(ip));
  
  return ips;
};

// Whitelisted IPs
const whitelistedIPs = parseWhitelistedIPs();

// Token bucket configuration
const tokenBuckets = new Map<string, TokenBucket>();

const getTokenBucket = (endpoint: string, ip: string): TokenBucket => {
  const key = `${endpoint}:${ip}`;
  if (!tokenBuckets.has(key)) {
    tokenBuckets.set(key, new TokenBucket({
      capacity: 5, // Maximum burst size
      fillRate: 1, // Tokens per second
      initialTokens: 5
    }));
  }
  return tokenBuckets.get(key)!;
};

interface ExtendedRateLimitOptions extends Partial<Options> {
  onRequest?: (req: Request, res: Response, next: NextFunction) => Promise<void>;
}

const createLimiter = (windowMs: number, max: number, endpoint: string) => {
  const options: ExtendedRateLimitOptions = {
    windowMs,
    max,
    standardHeaders: true,
    legacyHeaders: false,
    skip: (req) => {
      // Check for bypass token first
      if (req.bypassRateLimit) {
        logger.debug(`Rate limit bypassed with token for ${endpoint}`);
        return true;
      }

      // Then check IP whitelist
      const clientIp = req.ip || req.connection.remoteAddress || 'unknown';
      const isWhitelisted = whitelistedIPs.has(clientIp);
      if (isWhitelisted) {
        logger.debug(`Rate limit skipped for whitelisted IP ${clientIp} on ${endpoint}`);
      }
      return isWhitelisted;
    },
    handler: (req, res) => {
      const clientIp = req.ip || req.connection.remoteAddress || 'unknown';
      
      // Track rate limit hit
      rateLimitCounter.inc({ endpoint, ip: clientIp });
      
      // Calculate reset time
      const resetTime = new Date(Date.now() + windowMs);
      
      // Get token bucket status
      const bucket = getTokenBucket(endpoint, clientIp);
      const tokensRemaining = bucket.getTokenCount();
      
      // Update metrics
      rateLimitTokensGauge.set({ endpoint, ip: clientIp }, tokensRemaining);
      
      logger.warn(`Rate limit exceeded for ${endpoint} by ${clientIp}`, {
        endpoint,
        ip: clientIp,
        resetTime,
        tokensRemaining
      });

      res.status(429).json({
        error: 'Too many requests',
        message: 'Rate limit exceeded',
        details: {
          retryAfter: Math.ceil(windowMs / 1000),
          resetTime: resetTime.toISOString(),
          limit: max,
          windowMs,
          endpoint,
          tokensRemaining,
          nextTokenIn: bucket.getTimeUntilNextToken()
        }
      });
    },
    keyGenerator: (req) => {
      const clientIp = req.ip || req.connection.remoteAddress || 'unknown';
      return `${clientIp}:${endpoint}`;
    }
  };

  // Add Redis store if Redis is available
  if (redisClient.status === 'ready') {
    options.store = {
      init: () => Promise.resolve(),
      increment: (key: string) => redisClient.incr(key).then(Number),
      decrement: (key: string) => redisClient.decr(key).then(Number),
      resetKey: (key: string) => redisClient.del(key).then(() => undefined)
    } as Store;
  }

  const middleware = rateLimit(options);

  // Wrap the middleware to handle token bucket logic
  return async (req: Request, res: Response, next: NextFunction) => {
    const clientIp = req.ip || req.connection.remoteAddress || 'unknown';
    const bucket = getTokenBucket(endpoint, clientIp);
    
    if (!bucket.tryConsume()) {
      return res.status(429).json({
        error: 'Too many requests',
        message: 'Burst limit exceeded',
        details: {
          tokensRemaining: bucket.getTokenCount(),
          nextTokenIn: bucket.getTimeUntilNextToken()
        }
      });
    }
    
    return middleware(req, res, next);
  };
};

// Market data endpoint: 100 requests per minute
export const marketDataLimiter = createLimiter(60 * 1000, 100, '/api/market/data');

// Volatility endpoint: 60 requests per minute
export const volatilityLimiter = createLimiter(60 * 1000, 60, '/api/market/volatility');

// Opportunities endpoint: 30 requests per minute
export const opportunitiesLimiter = createLimiter(60 * 1000, 30, '/api/market/opportunities');

// WebSocket subscriptions: 10 requests per minute
export const wsSubscriptionLimiter = createLimiter(60 * 1000, 10, '/api/market/subscribe');

// Alert cleanup endpoint: 5 requests per 15 minutes in production, 100 in development
export const alertCleanupLimiter = createLimiter(
  15 * 60 * 1000, // 15 minutes
  process.env.NODE_ENV === 'production' ? 5 : 100,
  '/api/alerts/cleanup'
);

// Alert metrics endpoint: 30 requests per minute
export const alertMetricsLimiter = createLimiter(60 * 1000, 30, '/api/alerts/metrics');

// Export metrics for monitoring
export const getRateLimitMetrics = async () => {
  return register.getMetricsAsJSON();
};

// Status endpoint for monitoring
export const getRateLimitStatus = async () => {
  const metrics = await register.getMetricsAsJSON();
  const redisInfo = await redisClient.info();
  
  return {
    metrics,
    redis: {
      connected: redisClient.status === 'ready',
      info: redisInfo
    },
    tokenBuckets: Array.from(tokenBuckets.entries()).map(([key, bucket]) => ({
      key,
      tokens: bucket.getTokenCount(),
      nextTokenIn: bucket.getTimeUntilNextToken()
    }))
  };
};
