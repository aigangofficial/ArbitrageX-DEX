import request from 'supertest';
import { setupTestApp, teardownTestApp, TestSetup } from './helpers/testSetup';
import { MongoMemoryServer } from 'mongodb-memory-server';
import { RedisService } from '../services/redis';

describe('Health Check API', () => {
    let setup: TestSetup;

    beforeAll(async () => {
        process.env.NODE_ENV = 'test';
        setup = await setupTestApp();
    });

    afterAll(async () => {
        await teardownTestApp(setup.mongoServer);
        await RedisService.closeConnection();
    });

    it('should return 200 and healthy status when all services are up', async () => {
        const response = await request(setup.app)
            .get('/health')
            .expect('Content-Type', /json/)
            .expect(200);

        expect(response.body).toHaveProperty('status', 'healthy');
        expect(response.body).toHaveProperty('services');
        expect(response.body.services).toHaveProperty('mongodb', 'connected');
        expect(response.body.services).toHaveProperty('redis', 'connected');
        expect(response.body.services).toHaveProperty('ai');
        expect(response.body).toHaveProperty('timestamp');
    });

    it('should return 503 when MongoDB is down', async () => {
        // Disconnect MongoDB
        await setup.mongoServer.stop();

        const response = await request(setup.app)
            .get('/health')
            .expect('Content-Type', /json/)
            .expect(503);

        expect(response.body).toHaveProperty('status', 'unhealthy');
        expect(response.body.services).toHaveProperty('mongodb', 'disconnected');

        // Reconnect MongoDB
        await setup.mongoServer.start();
    });

    it('should return 503 when Redis is down', async () => {
        // Disconnect Redis
        await RedisService.closeConnection();

        const response = await request(setup.app)
            .get('/health')
            .expect('Content-Type', /json/)
            .expect(503);

        expect(response.body).toHaveProperty('status', 'unhealthy');
        expect(response.body.services).toHaveProperty('redis', 'disconnected');

        // Reconnect Redis
        await RedisService.getInstance();
    });
}); 