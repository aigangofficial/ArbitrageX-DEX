"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.createApp = createApp;
const express_1 = __importDefault(require("express"));
const cors_1 = __importDefault(require("cors"));
const express_rate_limit_1 = __importDefault(require("express-rate-limit"));
const ai_1 = __importDefault(require("./routes/ai"));
const health_1 = __importDefault(require("./routes/health"));
const bot_control_1 = __importDefault(require("./routes/bot-control"));
const errorHandler_1 = require("./middleware/errorHandler");
const logger_1 = require("./utils/logger");
async function createApp(redis) {
    try {
        await redis.ping();
    }
    catch (error) {
        logger_1.logger.error('Redis connection failed:', error);
    }
    const app = (0, express_1.default)();
    app.use((0, cors_1.default)());
    app.use(express_1.default.json());
    app.use(express_1.default.urlencoded({ extended: true }));
    app.use((_req, res, next) => {
        res.setHeader('Content-Type', 'application/json');
        const originalJson = res.json;
        const originalSend = res.send;
        res.json = function (body) {
            res.setHeader('Content-Type', 'application/json');
            return originalJson.call(this, body);
        };
        res.send = function (body) {
            if (body && typeof body === 'object') {
                res.setHeader('Content-Type', 'application/json');
                return res.json(body);
            }
            res.setHeader('Content-Type', 'application/json');
            return originalSend.call(this, JSON.stringify({ message: body }));
        };
        next();
    });
    const aiLimiter = (0, express_rate_limit_1.default)({
        windowMs: 1000,
        max: process.env.NODE_ENV === 'test' ? 100 : 2,
        message: {
            success: false,
            error: 'Too many requests, please try again later.'
        },
        standardHeaders: true,
        legacyHeaders: false,
        handler: (req, res) => {
            res.status(429).json({
                success: false,
                error: 'Too many requests, please try again later.'
            });
        }
    });
    app.use('/api/v1/ai', aiLimiter, ai_1.default);
    app.use('/health', health_1.default);
    app.use('/api/v1/bot-control', bot_control_1.default);
    app.use((req, _res, next) => {
        const err = new Error(`Not Found - ${req.originalUrl}`);
        err.name = 'NotFoundError';
        next(err);
    });
    app.use(errorHandler_1.errorHandler);
    return app;
}
//# sourceMappingURL=app.js.map