"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AuthenticationError = exports.NotFoundError = exports.ValidationError = void 0;
exports.errorHandler = errorHandler;
const logger_1 = require("../utils/logger");
class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ValidationError';
    }
}
exports.ValidationError = ValidationError;
class NotFoundError extends Error {
    constructor(message) {
        super(message);
        this.name = 'NotFoundError';
        this.statusCode = 404;
    }
}
exports.NotFoundError = NotFoundError;
class AuthenticationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'AuthenticationError';
    }
}
exports.AuthenticationError = AuthenticationError;
function errorHandler(err, req, res, _next) {
    logger_1.logger.error('Error details:', {
        name: err.name,
        message: err.message,
        stack: err.stack,
        path: req.path,
        method: req.method,
        headers: req.headers
    });
    res.setHeader('Content-Type', 'application/json');
    if (err instanceof ValidationError) {
        return res.status(400).json({
            success: false,
            error: err.message,
            type: err.name
        });
    }
    if (err instanceof AuthenticationError) {
        return res.status(401).json({
            success: false,
            error: err.message,
            type: err.name
        });
    }
    if (err instanceof NotFoundError) {
        return res.status(404).json({
            success: false,
            error: err.message,
            type: err.name
        });
    }
    return res.status(500).json({
        success: false,
        error: err.message,
        type: err.name
    });
}
process.on('uncaughtException', (error) => {
    logger_1.logger.error('Uncaught Exception:', error);
    process.exit(1);
});
process.on('unhandledRejection', (reason) => {
    logger_1.logger.error('Unhandled Rejection:', reason);
    process.exit(1);
});
//# sourceMappingURL=errorHandler.js.map