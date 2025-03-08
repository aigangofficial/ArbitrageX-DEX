"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.RedisService = void 0;
const ioredis_1 = __importDefault(require("ioredis"));
const logger_1 = require("../utils/logger");
const ioredis_mock_1 = __importDefault(require("ioredis-mock"));
class RedisService {
    static async getInstance() {
        if (!this.instance) {
            try {
                if (process.env.NODE_ENV === 'test') {
                    this.isTestMode = true;
                    this.instance = new ioredis_mock_1.default();
                    logger_1.logger.info('Using Redis mock for testing');
                    return this.instance;
                }
                this.instance = new ioredis_1.default({
                    host: process.env.REDIS_HOST || 'localhost',
                    port: parseInt(process.env.REDIS_PORT || '6379'),
                    password: process.env.REDIS_PASSWORD,
                    maxRetriesPerRequest: 1,
                    enableOfflineQueue: true,
                    lazyConnect: true
                });
                this.instance.on('error', (error) => {
                    logger_1.logger.error('Redis connection error:', error);
                });
                this.instance.on('connect', () => {
                    logger_1.logger.info('Redis connected successfully');
                });
                await this.instance.connect();
            }
            catch (error) {
                logger_1.logger.error('Error initializing Redis:', error);
                throw error;
            }
        }
        return this.instance;
    }
    static async isConnected() {
        try {
            if (!this.instance) {
                return false;
            }
            if (this.isTestMode) {
                return true;
            }
            const pong = await this.instance.ping();
            return pong === 'PONG';
        }
        catch (error) {
            logger_1.logger.error('Error checking Redis connection:', error);
            return false;
        }
    }
    static async closeConnection() {
        if (this.instance) {
            try {
                if (this.instance instanceof ioredis_1.default) {
                    await this.instance.quit();
                }
                this.instance = null;
                this.isTestMode = false;
            }
            catch (error) {
                logger_1.logger.error('Error closing Redis connection:', error);
            }
            finally {
                this.instance = null;
                this.isTestMode = false;
            }
        }
    }
}
exports.RedisService = RedisService;
RedisService.instance = null;
RedisService.isTestMode = false;
if (process.env.NODE_ENV !== 'test') {
    (async () => {
        try {
            await RedisService.getInstance();
        }
        catch (error) {
            logger_1.logger.error('Failed to initialize Redis client:', error);
        }
    })();
}
//# sourceMappingURL=redis.js.map