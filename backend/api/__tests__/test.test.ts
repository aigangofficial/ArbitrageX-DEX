import request from 'supertest';
import { setupTestApp, teardownTestApp, TestSetup } from './helpers/testSetup';

describe('Test Routes', () => {
    let setup: TestSetup;

    beforeAll(async () => {
        process.env.NODE_ENV = 'test';
        setup = await setupTestApp();
    });

    afterAll(async () => {
        await teardownTestApp(setup.mongoServer);
    });

    it('should handle test route', async () => {
        const response = await request(setup.app)
            .get('/test')
            .expect('Content-Type', /json/)
            .expect(200);

        expect(response.body).toHaveProperty('message', 'Test route working');
    });

    it('should handle validation error', async () => {
        const response = await request(setup.app)
            .get('/error/validation')
            .expect('Content-Type', /json/)
            .expect(400);

        expect(response.body).toHaveProperty('success', false);
        expect(response.body).toHaveProperty('error', 'Test validation error');
        expect(response.body).toHaveProperty('type', 'ValidationError');
    });

    it('should handle authentication error', async () => {
        const response = await request(setup.app)
            .get('/error/auth')
            .expect('Content-Type', /json/)
            .expect(401);

        expect(response.body).toHaveProperty('success', false);
        expect(response.body).toHaveProperty('error', 'Test authentication error');
        expect(response.body).toHaveProperty('type', 'AuthenticationError');
    });

    it('should handle unknown error', async () => {
        const response = await request(setup.app)
            .get('/error/unknown')
            .expect('Content-Type', /json/)
            .expect(500);

        expect(response.body).toHaveProperty('success', false);
        expect(response.body).toHaveProperty('error', 'Test unknown error');
        expect(response.body).toHaveProperty('type', 'Error');
    });

    it('should handle rate limit test', async () => {
        const response = await request(setup.app)
            .get('/test-rate-limit')
            .expect('Content-Type', /json/)
            .expect(200);

        expect(response.body).toHaveProperty('message', 'Rate limit test endpoint');
    });
}); 