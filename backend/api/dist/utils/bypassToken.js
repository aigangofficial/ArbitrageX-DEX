"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.BypassTokenManager = void 0;
const jsonwebtoken_1 = __importDefault(require("jsonwebtoken"));
const crypto_1 = __importDefault(require("crypto"));
const logger_1 = require("./logger");
class BypassTokenManager {
    constructor(config) {
        this.secret = config.secret;
        this.expiresIn = config.expiresIn || '1h';
        this.maxUsageCount = config.maxUsageCount || 1000;
        this.redisClient = config.redisClient;
        this.breachThreshold = config.breachThreshold || 3;
    }
    /**
     * Generate a new HMAC-signed JWT bypass token with scope restrictions
     */
    async generateToken(subject, scope = ['*']) {
        const jti = crypto_1.default.randomBytes(16).toString('hex');
        const payload = {
            sub: subject,
            jti,
            iat: Math.floor(Date.now() / 1000),
            exp: Math.floor(Date.now() / 1000) + 3600,
            usageLimit: this.maxUsageCount,
            scope
        };
        const token = jsonwebtoken_1.default.sign(payload, this.secret, {
            algorithm: 'HS512',
            expiresIn: this.expiresIn
        });
        // Store initial token state in Redis
        await this.redisClient.hset(`bypass_token:${jti}`, 'usageCount', '0', 'revoked', '0', 'scope', JSON.stringify(scope), 'activeIPs', '[]' // Track IPs using this token
        );
        // Set expiration to match JWT
        await this.redisClient.expire(`bypass_token:${jti}`, 3600);
        logger_1.logger.info('Generated new bypass token', {
            subject,
            jti,
            expiresIn: this.expiresIn,
            scope
        });
        return token;
    }
    /**
     * Verify token and check scope permissions
     */
    async verifyToken(token, endpoint) {
        try {
            const decoded = jsonwebtoken_1.default.verify(token, this.secret);
            const { jti, scope } = decoded;
            // Check if token is revoked or exceeded usage
            const [usageCount, revoked, scopeStr, activeIPsStr] = await this.redisClient.hmget(`bypass_token:${jti}`, 'usageCount', 'revoked', 'scope', 'activeIPs');
            if (revoked === '1') {
                logger_1.logger.warn('Attempt to use revoked bypass token', { jti });
                return false;
            }
            // Verify scope permissions
            const tokenScope = JSON.parse(scopeStr || '["*"]');
            if (!this._checkScope(tokenScope, endpoint)) {
                logger_1.logger.warn('Token scope violation attempt', { jti, endpoint, allowedScope: tokenScope });
                return false;
            }
            const currentUsage = parseInt(usageCount || '0', 10);
            if (currentUsage >= this.maxUsageCount) {
                logger_1.logger.warn('Bypass token usage limit exceeded', { jti, currentUsage });
                return false;
            }
            // Breach detection
            const activeIPs = JSON.parse(activeIPsStr || '[]');
            if (await this._detectBreach(jti, activeIPs)) {
                logger_1.logger.error('Token breach detected - auto-revoking', { jti });
                await this.revokeToken(token);
                return false;
            }
            // Increment usage count
            await this.redisClient.hincrby(`bypass_token:${jti}`, 'usageCount', 1);
            return true;
        }
        catch (error) {
            logger_1.logger.error('Bypass token verification failed', { error });
            return false;
        }
    }
    /**
     * Check if token scope allows access to endpoint
     */
    _checkScope(tokenScope, endpoint) {
        if (tokenScope.includes('*'))
            return true;
        return tokenScope.some(scope => {
            // Convert scope pattern to regex
            const pattern = scope.replace(/\*/g, '.*');
            const regex = new RegExp(`^${pattern}$`);
            return regex.test(endpoint);
        });
    }
    /**
     * Detect potential token breach based on concurrent IP usage
     */
    async _detectBreach(jti, activeIPs) {
        const recentLogs = await this.redisClient.lrange(`bypass_token_audit:${jti}`, -100, // Check last 100 uses
        -1);
        const recentIPs = new Set(recentLogs
            .map(log => JSON.parse(log))
            .map(log => log.ip));
        // Check for suspicious concurrent IP usage
        if (recentIPs.size > this.breachThreshold) {
            logger_1.logger.warn('Suspicious token usage detected', {
                jti,
                uniqueIPs: recentIPs.size,
                threshold: this.breachThreshold
            });
            return true;
        }
        return false;
    }
    /**
     * Log token usage with enhanced details
     */
    async logTokenUsage(jti, subject, ip, endpoint) {
        const usageLog = {
            timestamp: new Date().toISOString(),
            jti,
            subject,
            ip,
            endpoint
        };
        // Update active IPs list
        const activeIPs = new Set(JSON.parse((await this.redisClient.hget(`bypass_token:${jti}`, 'activeIPs')) || '[]'));
        activeIPs.add(ip);
        await this.redisClient.hset(`bypass_token:${jti}`, 'activeIPs', JSON.stringify(Array.from(activeIPs)));
        await this.redisClient.rpush(`bypass_token_audit:${jti}`, JSON.stringify(usageLog));
        // Keep audit logs for 30 days
        await this.redisClient.expire(`bypass_token_audit:${jti}`, 30 * 24 * 60 * 60);
    }
    /**
     * Revoke a bypass token
     */
    async revokeToken(token) {
        try {
            const decoded = jsonwebtoken_1.default.verify(token, this.secret);
            const { jti } = decoded;
            await this.redisClient.hset(`bypass_token:${jti}`, 'revoked', '1');
            logger_1.logger.info('Revoked bypass token', { jti });
            return true;
        }
        catch (error) {
            logger_1.logger.error('Failed to revoke bypass token', { error });
            return false;
        }
    }
    /**
     * Get token usage statistics
     */
    async getTokenStats(token) {
        try {
            const decoded = jsonwebtoken_1.default.verify(token, this.secret);
            const { jti } = decoded;
            const [usageCount, revoked] = await this.redisClient.hmget(`bypass_token:${jti}`, 'usageCount', 'revoked');
            const auditLogs = await this.redisClient.lrange(`bypass_token_audit:${jti}`, 0, -1);
            const parsedLogs = auditLogs.map(log => JSON.parse(log));
            const uniqueIPs = new Set(parsedLogs.map(log => log.ip)).size;
            return {
                jti,
                subject: decoded.sub,
                usageCount: parseInt(usageCount || '0', 10),
                revoked: revoked === '1',
                issuedAt: new Date(decoded.iat * 1000).toISOString(),
                expiresAt: new Date(decoded.exp * 1000).toISOString(),
                uniqueIPs,
                auditLogs: parsedLogs
            };
        }
        catch (error) {
            logger_1.logger.error('Failed to get token stats', { error });
            throw error;
        }
    }
    /**
     * List all active bypass tokens
     */
    async listActiveTokens() {
        try {
            const pattern = 'bypass_token:*';
            const keys = await this.redisClient.keys(pattern);
            const tokens = await Promise.all(keys.map(async (key) => {
                const [usageCount, revoked, scope] = await this.redisClient.hmget(key, 'usageCount', 'revoked', 'scope');
                return {
                    jti: key.split(':')[1],
                    usageCount: parseInt(usageCount || '0', 10),
                    revoked: revoked === '1',
                    scope: JSON.parse(scope || '["*"]')
                };
            }));
            // Only return active (non-revoked) tokens
            return tokens.filter(t => !t.revoked);
        }
        catch (error) {
            logger_1.logger.error('Failed to list active tokens', { error });
            throw error;
        }
    }
}
exports.BypassTokenManager = BypassTokenManager;
//# sourceMappingURL=bypassToken.js.map