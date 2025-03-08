"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.teardownTestApp = exports.setupTestApp = void 0;
const express_1 = __importDefault(require("express"));
const mongoose_1 = __importDefault(require("mongoose"));
const mongodb_memory_server_1 = require("mongodb-memory-server");
const redis_1 = require("../../services/redis");
const health_1 = __importDefault(require("../../routes/health"));
const ai_1 = __importDefault(require("../../routes/ai"));
const test_1 = __importDefault(require("../../routes/test"));
const errorHandler_1 = require("../../middleware/errorHandler");
const setupTestApp = async () => {
    process.env.NODE_ENV = 'test';
    const mongoServer = await mongodb_memory_server_1.MongoMemoryServer.create();
    const mongoUri = mongoServer.getUri();
    await mongoose_1.default.connect(mongoUri);
    await redis_1.RedisService.getInstance();
    const app = (0, express_1.default)();
    app.use(express_1.default.json());
    app.use((_req, res, next) => {
        const originalJson = res.json;
        res.json = function (body) {
            res.setHeader('Content-Type', 'application/json');
            return originalJson.call(this, body);
        };
        next();
    });
    app.use('/health', health_1.default);
    app.use('/ai', ai_1.default);
    app.use('/', test_1.default);
    app.use(errorHandler_1.errorHandler);
    return { app, mongoServer };
};
exports.setupTestApp = setupTestApp;
const teardownTestApp = async (mongoServer) => {
    try {
        if (mongoose_1.default.connection.readyState === 1) {
            await mongoose_1.default.disconnect();
        }
        if (mongoServer) {
            await mongoServer.stop();
        }
        await redis_1.RedisService.closeConnection();
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    catch (error) {
        console.error('Error during test teardown:', error);
        throw error;
    }
};
exports.teardownTestApp = teardownTestApp;
afterAll(async () => {
    await mongoose_1.default.disconnect();
});
describe('Test Setup', () => {
    it('should be defined', () => {
        expect(exports.setupTestApp).toBeDefined();
        expect(exports.teardownTestApp).toBeDefined();
    });
});
//# sourceMappingURL=testSetup.js.map