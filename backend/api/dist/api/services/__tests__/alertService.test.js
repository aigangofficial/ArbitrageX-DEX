"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const alert_1 = require("../alert");
const redis_1 = require("../redis");
describe('AlertService', () => {
    beforeAll(async () => {
        process.env.NODE_ENV = 'test';
    });
    beforeEach(async () => {
        const redis = await redis_1.RedisService.getInstance();
        await redis.flushall();
    });
    afterAll(async () => {
        await redis_1.RedisService.closeConnection();
    });
    it('should create and retrieve alerts', async () => {
        const userId = 'testUser123';
        const alert = {
            type: 'price_alert',
            symbol: 'ETH/USDT',
            threshold: 2000,
            direction: 'above',
            userId
        };
        const alertId = await alert_1.AlertService.createAlert(alert);
        expect(alertId).toBeDefined();
        expect(typeof alertId).toBe('string');
        const alerts = await alert_1.AlertService.getAlerts(userId);
        expect(alerts).toHaveLength(1);
        expect(alerts[0]).toMatchObject(alert);
        expect(alerts[0].id).toBe(alertId);
        await alert_1.AlertService.deleteAlert(alertId);
        const alertsAfterDelete = await alert_1.AlertService.getAlerts(userId);
        expect(alertsAfterDelete).toHaveLength(0);
    });
    it('should handle non-existent alerts', async () => {
        const userId = 'testUser123';
        const nonExistentId = 'nonexistent';
        await expect(alert_1.AlertService.deleteAlert(nonExistentId))
            .rejects.toThrow('Alert not found');
        const alerts = await alert_1.AlertService.getAlerts(userId);
        expect(alerts).toHaveLength(0);
    });
});
//# sourceMappingURL=alertService.test.js.map