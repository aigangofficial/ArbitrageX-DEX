"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const supertest_1 = __importDefault(require("supertest"));
const testSetup_1 = require("./helpers/testSetup");
const redis_1 = require("../services/redis");
describe('AI API', () => {
    let setup;
    beforeAll(async () => {
        process.env.NODE_ENV = 'test';
        setup = await (0, testSetup_1.setupTestApp)();
    });
    afterAll(async () => {
        await (0, testSetup_1.teardownTestApp)(setup.mongoServer);
        await redis_1.RedisService.closeConnection();
    });
    it('should return AI status', async () => {
        const response = await (0, supertest_1.default)(setup.app)
            .get('/ai/status')
            .expect('Content-Type', /json/)
            .expect(200);
        expect(response.body).toHaveProperty('success', true);
        expect(response.body).toHaveProperty('data');
        expect(response.body.data).toHaveProperty('status');
        expect(response.body.data).toHaveProperty('model_version');
    });
    it('should handle prediction requests', async () => {
        const response = await (0, supertest_1.default)(setup.app)
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
        const response = await (0, supertest_1.default)(setup.app)
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
//# sourceMappingURL=ai.test.js.map