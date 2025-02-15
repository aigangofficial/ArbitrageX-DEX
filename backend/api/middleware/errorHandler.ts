import { NextFunction, Request, Response } from 'express';
import { logger } from '../utils/logger';

// Custom error classes
export class ValidationError extends Error {
  statusCode: number;

  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
    this.statusCode = 400;
  }
}

export class NotFoundError extends Error {
  statusCode: number;

  constructor(message: string) {
    super(message);
    this.name = 'NotFoundError';
    this.statusCode = 404;
  }
}

export class AuthenticationError extends Error {
  statusCode: number;

  constructor(message: string) {
    super(message);
    this.name = 'AuthenticationError';
    this.statusCode = 401;
  }
}

// Error handler middleware
export const errorHandler = (err: Error, req: Request, res: Response, next: NextFunction) => {
  // Log the error
  logger.error('Error occurred:', {
    name: err.name,
    message: err.message,
    stack: err.stack,
    path: req.path,
    method: req.method,
  });

  // Handle known error types
  if (
    err instanceof ValidationError ||
    err instanceof NotFoundError ||
    err instanceof AuthenticationError
  ) {
    return res.status((err as any).statusCode).json({
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
