import { Router } from 'express';
import { BypassTokenManager } from '../utils/bypassToken';
import { AuthenticationError } from '../middleware/errorHandler';
import { logger } from '../utils/logger';

const router = Router();

export const createAdminRouter = (tokenManager: BypassTokenManager) => {
  // Generate a new bypass token
  router.post('/bypass-token', async (req, res, next) => {
    try {
      // Generate token with default settings
      const token = await tokenManager.generateToken();
      
      res.json({
        success: true,
        token,
        details: {
          expiresIn: '1h',
          maxUsage: 1000
        }
      });
    } catch (error) {
      next(error);
    }
  });

  // Check token validity
  router.get('/bypass-token/check', async (req, res, next) => {
    try {
      const token = req.headers['x-bypass-token'];
      
      if (!token || typeof token !== 'string') {
        throw new AuthenticationError('Token is required');
      }

      const isValid = await tokenManager.validateToken(token);
      
      res.json({
        success: true,
        isValid
      });
    } catch (error) {
      next(error);
    }
  });

  return router;
};