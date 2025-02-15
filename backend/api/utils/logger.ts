import { NextFunction, Request, Response } from 'express';
import winston from 'winston';
import { config } from '../config';

const { combine, timestamp, printf, colorize } = winston.format;

// Create logs directory if it doesn't exist
const fs = require('fs');
const logDir = config.logging.directory || 'logs';
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

// Custom log format
const logFormat = printf(({ level, message, timestamp, ...metadata }) => {
  let msg = `${timestamp} [${level}] : ${message}`;

  if (Object.keys(metadata).length > 0) {
    msg += ` ${JSON.stringify(metadata)}`;
  }

  return msg;
});

// Create logger instance
const logger = winston.createLogger({
  level: config.logging.level || 'info',
  format: combine(timestamp(), logFormat),
  transports: [
    // Console transport for development
    new winston.transports.Console({
      format: combine(colorize(), logFormat),
    }),
    // File transport for production
    new winston.transports.File({
      filename: 'logs/error.log',
      level: 'error',
      maxsize: 5242880, // 5MB
      maxFiles: 5,
    }),
    new winston.transports.File({
      filename: 'logs/combined.log',
      maxsize: 5242880,
      maxFiles: 5,
    }),
  ],
});

// Add stream for Morgan HTTP logging
const loggerStream = {
  write: (message: string) => {
    logger.info(message.trim());
  },
};

// Request logging middleware
const requestLogger = (req: Request, res: Response, next: NextFunction) => {
  // Log request start
  logger.info(`Incoming ${req.method} request to ${req.path}`, {
    ip: req.ip,
    userAgent: req.get('user-agent'),
    query: req.query,
  });

  // Log response
  res.on('finish', () => {
    logger.info(`Request completed with status ${res.statusCode}`);
  });

  next();
};

export { logger, loggerStream, requestLogger };
