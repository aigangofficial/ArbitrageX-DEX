"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const supertest_1 = __importDefault(require("supertest"));
const testSetup_1 = require("./helpers/testSetup");
const redis_1 = require("../services/redis");
describe('Health Check API', () => {
    let setup;
    beforeAll(async () => {
        process.env.NODE_ENV = 'test';
        setup = await (0, testSetup_1.setupTestApp)();
    });
    afterAll(async () => {
        await (0, testSetup_1.teardownTestApp)(setup.mongoServer);
        await redis_1.RedisService.closeConnection();
    });
    it('should return 200 and healthy status when all services are up', async () => {
        const response = await (0, supertest_1.default)(setup.app)
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
        await setup.mongoServer.stop();
        const response = await (0, supertest_1.default)(setup.app)
            .get('/health')
            .expect('Content-Type', /json/)
            .expect(503);
        expect(response.body).toHaveProperty('status', 'unhealthy');
        expect(response.body.services).toHaveProperty('mongodb', 'disconnected');
        await setup.mongoServer.start();
    });
    it('should return 503 when Redis is down', async () => {
        await redis_1.RedisService.closeConnection();
        const response = await (0, supertest_1.default)(setup.app)
            .get('/health')
            .expect('Content-Type', /json/)
            .expect(503);
        expect(response.body).toHaveProperty('status', 'unhealthy');
        expect(response.body.services).toHaveProperty('redis', 'disconnected');
        await redis_1.RedisService.getInstance();
    });
});
//# sourceMappingURL=health.test.js.map