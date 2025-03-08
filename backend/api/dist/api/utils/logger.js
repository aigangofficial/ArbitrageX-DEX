"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.requestLogger = exports.loggerStream = exports.logger = exports.loggerMorgan = exports.requestLoggerMorgan = exports.loggerStreamMorgan = void 0;
const winston_1 = __importDefault(require("winston"));
const config_1 = require("../config");
const { combine, timestamp, printf, colorize } = winston_1.default.format;
const fs = require('fs');
const logDir = config_1.config.logging.directory || 'logs';
if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
}
const logFormat = printf(({ level, message, timestamp, ...metadata }) => {
    let msg = `${timestamp} [${level}] : ${message}`;
    if (Object.keys(metadata).length > 0) {
        msg += ` ${JSON.stringify(metadata)}`;
    }
    return msg;
});
const logger = winston_1.default.createLogger({
    level: config_1.config.logging.level || 'info',
    format: combine(timestamp(), logFormat),
    transports: [
        new winston_1.default.transports.Console({
            format: combine(colorize(), logFormat),
        }),
        new winston_1.default.transports.File({
            filename: 'logs/error.log',
            level: 'error',
            maxsize: 5242880,
            maxFiles: 5,
        }),
        new winston_1.default.transports.File({
            filename: 'logs/combined.log',
            maxsize: 5242880,
            maxFiles: 5,
        }),
    ],
});
exports.logger = logger;
const loggerStream = {
    write: (message) => {
        logger.info(message.trim());
    },
};
exports.loggerStream = loggerStream;
const requestLogger = (req, res, next) => {
    logger.info(`Incoming ${req.method} request to ${req.path}`, {
        ip: req.ip,
        userAgent: req.get('user-agent'),
        query: req.query,
    });
    res.on('finish', () => {
        logger.info(`Request completed with status ${res.statusCode}`);
    });
    next();
};
exports.requestLogger = requestLogger;
const winstonLogger = winston_1.default.createLogger({
    level: 'info',
    format: winston_1.default.format.combine(winston_1.default.format.timestamp(), winston_1.default.format.json()),
    transports: [
        new winston_1.default.transports.File({ filename: 'error.log', level: 'error' }),
        new winston_1.default.transports.File({ filename: 'combined.log' })
    ]
});
if (process.env.NODE_ENV !== 'production') {
    winstonLogger.add(new winston_1.default.transports.Console({
        format: winston_1.default.format.simple()
    }));
}
exports.loggerStreamMorgan = {
    write: (message) => {
        winstonLogger.info(message.trim());
    }
};
const requestLoggerMorgan = (req, res, next) => {
    const start = Date.now();
    res.on('finish', () => {
        const duration = Date.now() - start;
        winstonLogger.info({
            method: req.method,
            url: req.url,
            status: res.statusCode,
            duration: `${duration}ms`
        });
    });
    next();
};
exports.requestLoggerMorgan = requestLoggerMorgan;
exports.loggerMorgan = {
    error: (message, meta) => winstonLogger.error(message, meta),
    warn: (message, meta) => winstonLogger.warn(message, meta),
    info: (message, meta) => winstonLogger.info(message, meta),
    debug: (message, meta) => winstonLogger.debug(message, meta)
};
//# sourceMappingURL=logger.js.map