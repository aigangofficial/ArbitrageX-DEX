"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AlertService = void 0;
const redis_1 = require("./redis");
const logger_1 = require("../utils/logger");
class AlertService {
    static async createAlert(alert) {
        try {
            const redis = await redis_1.RedisService.getInstance();
            const alertId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            const alertWithId = { ...alert, id: alertId };
            await redis.set(`${this.ALERT_KEY_PREFIX}${alertId}`, JSON.stringify(alertWithId));
            await redis.sadd(`${this.USER_ALERTS_KEY_PREFIX}${alert.userId}`, alertId);
            return alertId;
        }
        catch (error) {
            logger_1.logger.error('Error creating alert:', error);
            throw new Error('Failed to create alert');
        }
    }
    static async getAlerts(userId) {
        try {
            const redis = await redis_1.RedisService.getInstance();
            const alertIds = await redis.smembers(`${this.USER_ALERTS_KEY_PREFIX}${userId}`);
            const alerts = await Promise.all(alertIds.map(async (alertId) => {
                const alertJson = await redis.get(`${this.ALERT_KEY_PREFIX}${alertId}`);
                return alertJson ? JSON.parse(alertJson) : null;
            }));
            return alerts.filter((alert) => alert !== null);
        }
        catch (error) {
            logger_1.logger.error('Error getting alerts:', error);
            throw new Error('Failed to get alerts');
        }
    }
    static async deleteAlert(alertId) {
        try {
            const redis = await redis_1.RedisService.getInstance();
            const alertJson = await redis.get(`${this.ALERT_KEY_PREFIX}${alertId}`);
            if (!alertJson) {
                throw new Error('Alert not found');
            }
            const alert = JSON.parse(alertJson);
            await redis.srem(`${this.USER_ALERTS_KEY_PREFIX}${alert.userId}`, alertId);
            await redis.del(`${this.ALERT_KEY_PREFIX}${alertId}`);
        }
        catch (error) {
            if (error instanceof Error && error.message === 'Alert not found') {
                throw error;
            }
            logger_1.logger.error('Error deleting alert:', error);
            throw new Error('Failed to delete alert');
        }
    }
}
exports.AlertService = AlertService;
AlertService.ALERT_KEY_PREFIX = 'alert:';
AlertService.USER_ALERTS_KEY_PREFIX = 'user_alerts:';
//# sourceMappingURL=alert.js.map