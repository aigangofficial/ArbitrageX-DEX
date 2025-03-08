"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const errorHandler_1 = require("../middleware/errorHandler");
const supertest_1 = __importDefault(require("supertest"));
const express_2 = __importDefault(require("express"));
const health_1 = __importDefault(require("./health"));
const router = (0, express_1.Router)();
// Test validation error
router.get('/error/validation', (_req, res, next) => {
    try {
        throw new errorHandler_1.ValidationError('Test validation error');
    }
    catch (error) {
        next(error);
    }
});
// Test authentication error
router.get('/error/auth', (_req, res, next) => {
    try {
        throw new errorHandler_1.AuthenticationError('Test authentication error');
    }
    catch (error) {
        next(error);
    }
});
// Test unknown error
router.get('/error/unknown', (_req, res, next) => {
    try {
        throw new Error('Test unknown error');
    }
    catch (error) {
        next(error);
    }
});
// Test rate limiting
router.get('/test-rate-limit', (_req, res) => {
    res.json({ message: 'Rate limit test endpoint' });
});
exports.default = router;
describe('API Routes', () => {
    let app;
    beforeEach(() => {
        app = (0, express_2.default)();
        app.use('/health', health_1.default);
    });
    describe('Health Check', () => {
        it('should return 200 OK', async () => {
            const response = await (0, supertest_1.default)(app)
                .get('/health')
                .expect('Content-Type', /json/)
                .expect(200);
            expect(response.body).toHaveProperty('status', 'ok');
            expect(response.body).toHaveProperty('timestamp');
        });
    });
});
//# sourceMappingURL=test.js.map