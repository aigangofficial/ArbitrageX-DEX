import jwt from 'jsonwebtoken';
import { Redis } from 'ioredis';
import { logger } from './logger';

interface BypassTokenConfig {
  secret: string;
  expiresIn: string;
  maxUsageCount: number;
  redisClient: Redis;
  breachThreshold: number;
}

interface TokenPayload {
  id: string;
  usageCount: number;
  maxUsageCount: number;
  iat?: number;
  exp?: number;
}

export class BypassTokenManager {
  private readonly secret: string;
  private readonly expiresIn: string;
  private readonly maxUsageCount: number;
  private readonly redisClient: Redis;
  private readonly breachThreshold: number;

  constructor(config: BypassTokenConfig) {
    this.secret = config.secret;
    this.expiresIn = config.expiresIn;
    this.maxUsageCount = config.maxUsageCount;
    this.redisClient = config.redisClient;
    this.breachThreshold = config.breachThreshold;
  }

  async generateToken(): Promise<string> {
    const tokenId = this.generateTokenId();
    const payload: TokenPayload = {
      id: tokenId,
      usageCount: 0,
      maxUsageCount: this.maxUsageCount
    };

    try {
      const token = jwt.sign(payload, this.secret);

      await this.redisClient.set(`token:${tokenId}`, JSON.stringify(payload));
      await this.redisClient.expire(`token:${tokenId}`, this.parseExpiresIn());

      return token;
    } catch (error) {
      logger.error('Error generating bypass token:', error);
      throw new Error('Failed to generate bypass token');
    }
  }

  async validateToken(token: string): Promise<boolean> {
    try {
      const decoded = jwt.verify(token, this.secret) as TokenPayload;
      const storedToken = await this.redisClient.get(`token:${decoded.id}`);

      if (!storedToken) {
        return false;
      }

      const tokenData = JSON.parse(storedToken) as TokenPayload;
      if (tokenData.usageCount >= tokenData.maxUsageCount) {
        await this.redisClient.del(`token:${decoded.id}`);
        return false;
      }

      tokenData.usageCount++;
      await this.redisClient.set(`token:${decoded.id}`, JSON.stringify(tokenData));

      if (tokenData.usageCount > this.breachThreshold) {
        logger.warn(`Token ${decoded.id} usage count exceeded breach threshold`);
      }

      return true;
    } catch (error) {
      logger.error('Error validating bypass token:', error);
      return false;
    }
  }

  private generateTokenId(): string {
    return Math.random().toString(36).substring(2) + Date.now().toString(36);
  }

  private parseExpiresIn(): number {
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
        return 3600; // Default to 1 hour
    }
  }
} 