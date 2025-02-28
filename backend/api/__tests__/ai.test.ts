import request from 'supertest';
import { setupTestApp, teardownTestApp, TestSetup } from './helpers/testSetup';
import { RedisService } from '../services/redis';

describe('AI API', () => {
    let setup: TestSetup;

    beforeAll(async () => {
        process.env.NODE_ENV = 'test';
        setup = await setupTestApp();
    });

    afterAll(async () => {
        await teardownTestApp(setup.mongoServer);
        await RedisService.closeConnection();
    });

    it('should return AI status', async () => {
        const response = await request(setup.app)
            .get('/ai/status')
            .expect('Content-Type', /json/)
            .expect(200);

        expect(response.body).toHaveProperty('success', true);
        expect(response.body).toHaveProperty('data');
        expect(response.body.data).toHaveProperty('status');
        expect(response.body.data).toHaveProperty('model_version');
    });

    it('should handle prediction requests', async () => {
        const response = await request(setup.app)
            .post('/ai/predict')
            .send({
                price: '50000',
                volume: '100',
                timestamp: new Date().toISOString()
            })
            .expect('Content-Type', /json/)
            .expect(200);

        expect(response.body).toHaveProperty('success', true);
        expect(response.body).toHaveProperty('prediction');
        expect(response.body.prediction).toHaveProperty('direction');
        expect(['up', 'down']).toContain(response.body.prediction.direction);
        expect(response.body.prediction).toHaveProperty('confidence');
        expect(response.body.prediction).toHaveProperty('timestamp');
    });

    it('should validate prediction request data', async () => {
        const response = await request(setup.app)
            .post('/ai/predict')
            .send({
                price: 'invalid',
                volume: '100',
                timestamp: new Date().toISOString()
            })
            .expect('Content-Type', /json/)
            .expect(400);

        expect(response.body).toHaveProperty('success', false);
        expect(response.body).toHaveProperty('error', 'Invalid price value');
    });
}); 