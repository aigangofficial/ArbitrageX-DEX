import { NextFunction, Request, Response } from 'express';
import { logger } from '../utils/logger';

// Custom error classes
export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
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
  constructor(message: string) {
    super(message);
    this.name = 'AuthenticationError';
  }
}

// Error handler middleware
export function errorHandler(err: Error, req: Request, res: Response, _next: NextFunction) {
  // Log the error with full details for debugging
  logger.error('Error details:', {
    name: err.name,
    message: err.message,
    stack: err.stack,
    path: req.path,
    method: req.method,
    headers: req.headers
  });

  // Always set JSON content type
  res.setHeader('Content-Type', 'application/json');

  // Handle different types of errors
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

  // Default to 500 internal server error
  return res.status(500).json({
    success: false,
    error: err.message,
    type: err.name
  });
}

// Register global error handlers
process.on('uncaughtException', (error: Error) => {
  logger.error('Uncaught Exception:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason: any) => {
  logger.error('Unhandled Rejection:', reason);
  process.exit(1);
});
