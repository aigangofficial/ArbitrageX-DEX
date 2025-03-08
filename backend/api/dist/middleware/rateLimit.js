"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.getRateLimitStatus = exports.getRateLimitMetrics = exports.alertMetricsLimiter = exports.alertCleanupLimiter = exports.wsSubscriptionLimiter = exports.opportunitiesLimiter = exports.volatilityLimiter = exports.marketDataLimiter = void 0;
const express_rate_limit_1 = __importDefault(require("express-rate-limit"));
const ioredis_1 = __importDefault(require("ioredis"));
const tokenBucket_1 = require("../utils/tokenBucket");
const logger_1 = require("../utils/logger");
const prom_client_1 = require("prom-client");
// Initialize Redis client
const redisClient = new ioredis_1.default({
    host: process.env.REDIS_HOST || 'localhost',
    port: Number(process.env.REDIS_PORT) || 6379,
    password: process.env.REDIS_PASSWORD,
    enableOfflineQueue: false
});
// Rate limit metrics
const rateLimitCounter = new prom_client_1.Counter({
    name: 'rate_limit_hits_total',
    help: 'Number of rate limit hits',
    labelNames: ['endpoint', 'ip']
});
const rateLimitTokensGauge = new prom_client_1.Gauge({
    name: 'rate_limit_tokens_remaining',
    help: 'Number of tokens remaining in bucket',
    labelNames: ['endpoint', 'ip']
});
// Parse whitelisted IPs from environment
const parseWhitelistedIPs = () => {
    const ips = new Set(['127.0.0.1']); // Always include localhost
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
const tokenBuckets = new Map();
const getTokenBucket = (endpoint, ip) => {
    const key = `${endpoint}:${ip}`;
    if (!tokenBuckets.has(key)) {
        tokenBuckets.set(key, new tokenBucket_1.TokenBucket({
            capacity: 5, // Maximum burst size
            fillRate: 1, // Tokens per second
            initialTokens: 5
        }));
    }
    return tokenBuckets.get(key);
};
const createLimiter = (windowMs, max, endpoint) => {
    const options = {
        windowMs,
        max,
        standardHeaders: true,
        legacyHeaders: false,
        skip: (req) => {
            // Check for bypass token first
            if (req.bypassRateLimit) {
                logger_1.logger.debug(`Rate limit bypassed with token for ${endpoint}`);
                return true;
            }
            // Then check IP whitelist
            const clientIp = req.ip || req.connection.remoteAddress || 'unknown';
            const isWhitelisted = whitelistedIPs.has(clientIp);
            if (isWhitelisted) {
                logger_1.logger.debug(`Rate limit skipped for whitelisted IP ${clientIp} on ${endpoint}`);
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
            logger_1.logger.warn(`Rate limit exceeded for ${endpoint} by ${clientIp}`, {
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
            increment: (key) => redisClient.incr(key).then(Number),
            decrement: (key) => redisClient.decr(key).then(Number),
            resetKey: (key) => redisClient.del(key).then(() => undefined)
        };
    }
    const middleware = (0, express_rate_limit_1.default)(options);
    // Wrap the middleware to handle token bucket logic
    return async (req, res, next) => {
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
        middleware(req, res, next);
    };
};
// Market data endpoint: 100 requests per minute
exports.marketDataLimiter = createLimiter(60 * 1000, 100, '/api/market/data');
// Volatility endpoint: 60 requests per minute
exports.volatilityLimiter = createLimiter(60 * 1000, 60, '/api/market/volatility');
// Opportunities endpoint: 30 requests per minute
exports.opportunitiesLimiter = createLimiter(60 * 1000, 30, '/api/market/opportunities');
// WebSocket subscriptions: 10 requests per minute
exports.wsSubscriptionLimiter = createLimiter(60 * 1000, 10, '/api/market/subscribe');
// Alert cleanup endpoint: 5 requests per 15 minutes in production, 100 in development
exports.alertCleanupLimiter = createLimiter(15 * 60 * 1000, // 15 minutes
process.env.NODE_ENV === 'production' ? 5 : 100, '/api/alerts/cleanup');
// Alert metrics endpoint: 30 requests per minute
exports.alertMetricsLimiter = createLimiter(60 * 1000, 30, '/api/alerts/metrics');
// Export metrics for monitoring
const getRateLimitMetrics = async () => {
    return prom_client_1.register.getMetricsAsJSON();
};
exports.getRateLimitMetrics = getRateLimitMetrics;
// Status endpoint for monitoring
const getRateLimitStatus = async () => {
    const metrics = await prom_client_1.register.getMetricsAsJSON();
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
exports.getRateLimitStatus = getRateLimitStatus;
//# sourceMappingURL=rateLimit.js.map