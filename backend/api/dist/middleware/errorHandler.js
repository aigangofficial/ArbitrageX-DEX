"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.errorHandler = exports.AuthenticationError = exports.NotFoundError = exports.ValidationError = void 0;
const logger_1 = require("../utils/logger");
// Custom error classes
class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ValidationError';
        this.statusCode = 400;
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
        this.statusCode = 401;
    }
}
exports.AuthenticationError = AuthenticationError;
// Error handler middleware
const errorHandler = (err, req, res, next) => {
    // Log the error
    logger_1.logger.error('Error occurred:', {
        name: err.name,
        message: err.message,
        stack: err.stack,
        path: req.path,
        method: req.method,
    });
    // Handle known error types
    if (err instanceof ValidationError ||
        err instanceof NotFoundError ||
        err instanceof AuthenticationError) {
        return res.status(err.statusCode).json({
            success: false,
            error: {
                name: err.name,
                message: err.message,
            },
        });
    }
    // Handle mongoose validation errors
    if (err.name === 'ValidationError') {
        return res.status(400).json({
            success: false,
            error: {
                name: 'ValidationError',
                message: err.message,
            },
        });
    }
    // Handle unknown errors
    return res.status(500).json({
        success: false,
        error: {
            name: 'InternalServerError',
            message: 'An unexpected error occurred',
        },
    });
};
exports.errorHandler = errorHandler;
//# sourceMappingURL=errorHandler.js.map