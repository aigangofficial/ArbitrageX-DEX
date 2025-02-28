import { Request } from 'express';

declare global {
  namespace Express {
    interface Request {
      bypassToken?: string;
      bypassRateLimit?: boolean;
    }
  }
} 