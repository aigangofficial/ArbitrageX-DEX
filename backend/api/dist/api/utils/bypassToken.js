"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.BypassTokenManager = void 0;
const jsonwebtoken_1 = __importDefault(require("jsonwebtoken"));
const logger_1 = require("./logger");
class BypassTokenManager {
    constructor(config) {
        this.secret = config.secret;
        this.expiresIn = config.expiresIn;
        this.maxUsageCount = config.maxUsageCount;
        this.redisClient = config.redisClient;
        this.breachThreshold = config.breachThreshold;
    }
    async generateToken() {
        const tokenId = this.generateTokenId();
        const payload = {
            id: tokenId,
            usageCount: 0,
            maxUsageCount: this.maxUsageCount
        };
        try {
            const token = jsonwebtoken_1.default.sign(payload, this.secret);
            await this.redisClient.set(`token:${tokenId}`, JSON.stringify(payload));
            await this.redisClient.expire(`token:${tokenId}`, this.parseExpiresIn());
            return token;
        }
        catch (error) {
            logger_1.logger.error('Error generating bypass token:', error);
            throw new Error('Failed to generate bypass token');
        }
    }
    async validateToken(token) {
        try {
            const decoded = jsonwebtoken_1.default.verify(token, this.secret);
            const storedToken = await this.redisClient.get(`token:${decoded.id}`);
            if (!storedToken) {
                return false;
            }
            const tokenData = JSON.parse(storedToken);
            if (tokenData.usageCount >= tokenData.maxUsageCount) {
                await this.redisClient.del(`token:${decoded.id}`);
                return false;
            }
            tokenData.usageCount++;
            await this.redisClient.set(`token:${decoded.id}`, JSON.stringify(tokenData));
            if (tokenData.usageCount > this.breachThreshold) {
                logger_1.logger.warn(`Token ${decoded.id} usage count exceeded breach threshold`);
            }
            return true;
        }
        catch (error) {
            logger_1.logger.error('Error validating bypass token:', error);
            return false;
        }
    }
    generateTokenId() {
        return Math.random().toString(36).substring(2) + Date.now().toString(36);
    }
    parseExpiresIn() {
        const unit = this.expiresIn.slice(-1);
        const value = parseInt(this.expiresIn.slice(0, -1));
        switch (unit) {
            case 'h':
                return value * 60 * 60;
            case 'm':
                return value * 60;
            case 's':
                return value;
            default:
                return 3600;
        }
    }
}
exports.BypassTokenManager = BypassTokenManager;
//# sourceMappingURL=bypassToken.js.map