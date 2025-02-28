import { AlertService } from '../alert';
import { RedisService } from '../redis';

interface Alert {
    type: 'price_alert';
    symbol: string;
    threshold: number;
    direction: 'above' | 'below';
    userId: string;
    id?: string;
}

describe('AlertService', () => {
    beforeAll(async () => {
        process.env.NODE_ENV = 'test';
    });

    beforeEach(async () => {
        // Clear Redis data before each test
        const redis = await RedisService.getInstance();
        await redis.flushall();
    });

    afterAll(async () => {
        await RedisService.closeConnection();
    });

    it('should create and retrieve alerts', async () => {
        const userId = 'testUser123';
        
        const alert: Alert = {
            type: 'price_alert',
            symbol: 'ETH/USDT',
            threshold: 2000,
            direction: 'above',
            userId
        };

        // Create alert
        const alertId = await AlertService.createAlert(alert);
        expect(alertId).toBeDefined();
        expect(typeof alertId).toBe('string');

        // Get alerts
        const alerts = await AlertService.getAlerts(userId);
        expect(alerts).toHaveLength(1);
        expect(alerts[0]).toMatchObject(alert);
        expect(alerts[0].id).toBe(alertId);

        // Delete alert
        await AlertService.deleteAlert(alertId);
        const alertsAfterDelete = await AlertService.getAlerts(userId);
        expect(alertsAfterDelete).toHaveLength(0);
    });

    it('should handle non-existent alerts', async () => {
        const userId = 'testUser123';
        const nonExistentId = 'nonexistent';

        await expect(AlertService.deleteAlert(nonExistentId))
            .rejects.toThrow('Alert not found');

        const alerts = await AlertService.getAlerts(userId);
        expect(alerts).toHaveLength(0);
    });
}); 