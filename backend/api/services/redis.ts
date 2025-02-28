import Redis from 'ioredis';
import { logger } from '../utils/logger';
import IoRedisMock from 'ioredis-mock';

type RedisInstance = Redis | InstanceType<typeof IoRedisMock>;

export class RedisService {
    private static instance: RedisInstance | null = null;
    private static isTestMode = false;

    static async getInstance(): Promise<RedisInstance> {
        if (!this.instance) {
            try {
                if (process.env.NODE_ENV === 'test') {
                    this.isTestMode = true;
                    this.instance = new IoRedisMock();
                    logger.info('Using Redis mock for testing');
                    return this.instance;
                }

                this.instance = new Redis({
                    host: process.env.REDIS_HOST || 'localhost',
                    port: parseInt(process.env.REDIS_PORT || '6379'),
                    password: process.env.REDIS_PASSWORD,
                    maxRetriesPerRequest: 1,
                    enableOfflineQueue: true,
                    lazyConnect: true
                });

                this.instance.on('error', (error) => {
                    logger.error('Redis connection error:', error);
                });

                this.instance.on('connect', () => {
                    logger.info('Redis connected successfully');
                });

                // Ensure connection is established
                await this.instance.connect();
            } catch (error) {
                logger.error('Error initializing Redis:', error);
                throw error;
            }
        }
        return this.instance;
    }

    static async isConnected(): Promise<boolean> {
        try {
            if (!this.instance) {
                return false;
            }

            if (this.isTestMode) {
                return true;
            }

            const pong = await this.instance.ping();
            return pong === 'PONG';
        } catch (error) {
            logger.error('Error checking Redis connection:', error);
            return false;
        }
    }

    static async closeConnection(): Promise<void> {
        if (this.instance) {
            try {
                if (this.instance instanceof Redis) {
                    await this.instance.quit();
                }
                // For IoRedisMock, we don't need to call quit, but we should clean up
                this.instance = null;
                this.isTestMode = false;
            } catch (error) {
                logger.error('Error closing Redis connection:', error);
            } finally {
                this.instance = null;
                this.isTestMode = false;
            }
        }
    }
}

// Initialize Redis client only if not in test environment
if (process.env.NODE_ENV !== 'test') {
    (async () => {
        try {
            await RedisService.getInstance();
        } catch (error) {
            logger.error('Failed to initialize Redis client:', error);
        }
    })();
} 