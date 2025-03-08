"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const supertest_1 = __importDefault(require("supertest"));
const server_1 = require("../server");
const mongodb_memory_server_1 = require("mongodb-memory-server");
const mongoose_1 = __importDefault(require("mongoose"));
const ioredis_mock_1 = __importDefault(require("ioredis-mock"));
describe('Health Check API', () => {
    let mongoServer;
    let app;
    let mockRedis;
    beforeAll(async () => {
        // Setup MongoDB Memory Server
        mongoServer = await mongodb_memory_server_1.MongoMemoryServer.create();
        const mongoUri = mongoServer.getUri();
        await mongoose_1.default.connect(mongoUri);
        // Setup Redis Mock
        mockRedis = new ioredis_mock_1.default();
        // Create Express app with mocked dependencies
        app = await (0, server_1.createServer)({
            redis: mockRedis,
            mongoUri
        });
    });
    afterAll(async () => {
        await mongoose_1.default.disconnect();
        await mongoServer.stop();
    });
    it('should return 200 and healthy status when all services are up', async () => {
        const response = await (0, supertest_1.default)(app)
            .get('/api/health')
            .expect('Content-Type', /json/)
            .expect(200);
        expect(response.body).toEqual({
            status: 'healthy',
            services: {
                mongodb: 'connected',
                redis: 'connected',
                websocket: 'connected'
            }
        });
    });
    it('should return 503 when MongoDB is down', async () => {
        await mongoose_1.default.disconnect();
        const response = await (0, supertest_1.default)(app)
            .get('/api/health')
            .expect('Content-Type', /json/)
            .expect(503);
        expect(response.body.status).toBe('unhealthy');
        expect(response.body.services.mongodb).toBe('disconnected');
        // Reconnect for other tests
        const mongoUri = mongoServer.getUri();
        await mongoose_1.default.connect(mongoUri);
    });
    it('should return 503 when Redis is down', async () => {
        mockRedis.disconnect();
        const response = await (0, supertest_1.default)(app)
            .get('/api/health')
            .expect('Content-Type', /json/)
            .expect(503);
        expect(response.body.status).toBe('unhealthy');
        expect(response.body.services.redis).toBe('disconnected');
        // Reconnect for other tests
        await mockRedis.connect();
    });
});
//# sourceMappingURL=health.test.js.map