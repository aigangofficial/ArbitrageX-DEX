import { RedisService } from './redis';
import { logger } from '../utils/logger';

interface Alert {
    id?: string;
    type: 'price_alert';
    symbol: string;
    threshold: number;
    direction: 'above' | 'below';
    userId: string;
}

export class AlertService {
    private static readonly ALERT_KEY_PREFIX = 'alert:';
    private static readonly USER_ALERTS_KEY_PREFIX = 'user_alerts:';

    static async createAlert(alert: Alert): Promise<string> {
        try {
            const redis = await RedisService.getInstance();
            const alertId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            const alertWithId = { ...alert, id: alertId };

            // Store alert by ID
            await redis.set(
                `${this.ALERT_KEY_PREFIX}${alertId}`,
                JSON.stringify(alertWithId)
            );

            // Add alert ID to user's alert list
            await redis.sadd(
                `${this.USER_ALERTS_KEY_PREFIX}${alert.userId}`,
                alertId
            );

            return alertId;
        } catch (error) {
            logger.error('Error creating alert:', error);
            throw new Error('Failed to create alert');
        }
    }

    static async getAlerts(userId: string): Promise<Alert[]> {
        try {
            const redis = await RedisService.getInstance();
            const alertIds = await redis.smembers(
                `${this.USER_ALERTS_KEY_PREFIX}${userId}`
            );

            const alerts = await Promise.all(
                alertIds.map(async (alertId) => {
                    const alertJson = await redis.get(
                        `${this.ALERT_KEY_PREFIX}${alertId}`
                    );
                    return alertJson ? JSON.parse(alertJson) : null;
                })
            );

            return alerts.filter((alert): alert is Alert => alert !== null);
        } catch (error) {
            logger.error('Error getting alerts:', error);
            throw new Error('Failed to get alerts');
        }
    }

    static async deleteAlert(alertId: string): Promise<void> {
        try {
            const redis = await RedisService.getInstance();
            const alertJson = await redis.get(
                `${this.ALERT_KEY_PREFIX}${alertId}`
            );

            if (!alertJson) {
                throw new Error('Alert not found');
            }

            const alert = JSON.parse(alertJson) as Alert;

            // Remove alert from user's alert list
            await redis.srem(
                `${this.USER_ALERTS_KEY_PREFIX}${alert.userId}`,
                alertId
            );

            // Delete alert by ID
            await redis.del(`${this.ALERT_KEY_PREFIX}${alertId}`);
        } catch (error) {
            if (error instanceof Error && error.message === 'Alert not found') {
                throw error;
            }
            logger.error('Error deleting alert:', error);
            throw new Error('Failed to delete alert');
        }
    }
} 