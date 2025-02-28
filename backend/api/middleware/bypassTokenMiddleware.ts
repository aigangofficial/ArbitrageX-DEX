import { Request, Response, NextFunction } from 'express';
import { BypassTokenManager } from '../utils/bypassToken';
import { logger } from '../utils/logger';

export function createBypassTokenMiddleware(tokenManager: BypassTokenManager) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const token = req.headers['x-bypass-token'] as string;
    
    if (!token) {
      return next();
    }

    try {
      const isValid = await tokenManager.validateToken(token);

      if (!isValid) {
        return res.status(401).json({
          error: 'Invalid or expired bypass token'
        });
      }

      // Token is valid, attach it to the request for downstream use
      req.bypassToken = token;
      next();
    } catch (error) {
      logger.error('Error validating bypass token:', error);
      return res.status(401).json({
        error: 'Failed to validate bypass token'
      });
    }
  };
} 