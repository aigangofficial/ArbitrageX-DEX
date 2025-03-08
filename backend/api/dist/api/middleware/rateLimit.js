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
const redisClient = new ioredis_1.default({
    host: process.env.REDIS_HOST || 'localhost',
    port: Number(process.env.REDIS_PORT) || 6379,
    password: process.env.REDIS_PASSWORD,
    enableOfflineQueue: false
});
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
const parseWhitelistedIPs = () => {
    const ips = new Set(['127.0.0.1']);
    if (process.env.ADMIN_IP) {
        ips.add(process.env.ADMIN_IP);
    }
    const additionalIPs = process.env.WHITELISTED_IPS?.split(',').filter(Boolean) || [];
    additionalIPs.forEach(ip => ips.add(ip));
    return ips;
};
const whitelistedIPs = parseWhitelistedIPs();
const tokenBuckets = new Map();
const getTokenBucket = (endpoint, ip) => {
    const key = `${endpoint}:${ip}`;
    if (!tokenBuckets.has(key)) {
        tokenBuckets.set(key, new tokenBucket_1.TokenBucket({
            capacity: 5,
            fillRate: 1,
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
            if (req.bypassRateLimit) {
                logger_1.logger.debug(`Rate limit bypassed with token for ${endpoint}`);
                return true;
            }
            const clientIp = req.ip || req.connection.remoteAddress || 'unknown';
            const isWhitelisted = whitelistedIPs.has(clientIp);
            if (isWhitelisted) {
                logger_1.logger.debug(`Rate limit skipped for whitelisted IP ${clientIp} on ${endpoint}`);
            }
            return isWhitelisted;
        },
        handler: (req, res) => {
            const clientIp = req.ip || req.connection.remoteAddress || 'unknown';
            rateLimitCounter.inc({ endpoint, ip: clientIp });
            const resetTime = new Date(Date.now() + windowMs);
            const bucket = getTokenBucket(endpoint, clientIp);
            const tokensRemaining = bucket.getTokenCount();
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
    if (redisClient.status === 'ready') {
        options.store = {
            init: () => Promise.resolve(),
            increment: (key) => redisClient.incr(key).then(Number),
            decrement: (key) => redisClient.decr(key).then(Number),
            resetKey: (key) => redisClient.del(key).then(() => undefined)
        };
    }
    const middleware = (0, express_rate_limit_1.default)(options);
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
        return middleware(req, res, next);
    };
};
exports.marketDataLimiter = createLimiter(60 * 1000, 100, '/api/market/data');
exports.volatilityLimiter = createLimiter(60 * 1000, 60, '/api/market/volatility');
exports.opportunitiesLimiter = createLimiter(60 * 1000, 30, '/api/market/opportunities');
exports.wsSubscriptionLimiter = createLimiter(60 * 1000, 10, '/api/market/subscribe');
exports.alertCleanupLimiter = createLimiter(15 * 60 * 1000, process.env.NODE_ENV === 'production' ? 5 : 100, '/api/alerts/cleanup');
exports.alertMetricsLimiter = createLimiter(60 * 1000, 30, '/api/alerts/metrics');
const getRateLimitMetrics = async () => {
    return prom_client_1.register.getMetricsAsJSON();
};
exports.getRateLimitMetrics = getRateLimitMetrics;
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