"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const supertest_1 = __importDefault(require("supertest"));
const testSetup_1 = require("./helpers/testSetup");
describe('Test Routes', () => {
    let setup;
    beforeAll(async () => {
        process.env.NODE_ENV = 'test';
        setup = await (0, testSetup_1.setupTestApp)();
    });
    afterAll(async () => {
        await (0, testSetup_1.teardownTestApp)(setup.mongoServer);
    });
    it('should handle test route', async () => {
        const response = await (0, supertest_1.default)(setup.app)
            .get('/test')
            .expect('Content-Type', /json/)
            .expect(200);
        expect(response.body).toHaveProperty('message', 'Test route working');
    });
    it('should handle validation error', async () => {
        const response = await (0, supertest_1.default)(setup.app)
            .get('/error/validation')
            .expect('Content-Type', /json/)
            .expect(400);
        expect(response.body).toHaveProperty('success', false);
        expect(response.body).toHaveProperty('error', 'Test validation error');
        expect(response.body).toHaveProperty('type', 'ValidationError');
    });
    it('should handle authentication error', async () => {
        const response = await (0, supertest_1.default)(setup.app)
            .get('/error/auth')
            .expect('Content-Type', /json/)
            .expect(401);
        expect(response.body).toHaveProperty('success', false);
        expect(response.body).toHaveProperty('error', 'Test authentication error');
        expect(response.body).toHaveProperty('type', 'AuthenticationError');
    });
    it('should handle unknown error', async () => {
        const response = await (0, supertest_1.default)(setup.app)
            .get('/error/unknown')
            .expect('Content-Type', /json/)
            .expect(500);
        expect(response.body).toHaveProperty('success', false);
        expect(response.body).toHaveProperty('error', 'Test unknown error');
        expect(response.body).toHaveProperty('type', 'Error');
    });
    it('should handle rate limit test', async () => {
        const response = await (0, supertest_1.default)(setup.app)
            .get('/test-rate-limit')
            .expect('Content-Type', /json/)
            .expect(200);
        expect(response.body).toHaveProperty('message', 'Rate limit test endpoint');
    });
});
//# sourceMappingURL=test.test.js.map