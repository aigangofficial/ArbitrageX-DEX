import { Request, Response, NextFunction } from 'express';

export function jsonResponseMiddleware(req: Request, res: Response, next: NextFunction) {
    const originalJson = res.json;
    const originalSend = res.send;

    // Override json method
    res.json = function(body) {
        res.setHeader('Content-Type', 'application/json');
        return originalJson.call(this, body);
    };

    // Override send method
    res.send = function(body) {
        if (body === null || body === undefined) {
            return originalSend.call(this, body);
        }

        if (typeof body === 'object') {
            res.setHeader('Content-Type', 'application/json');
            return originalJson.call(this, body);
        }

        return originalSend.call(this, body);
    };

    // Set default content type for all responses
    res.setHeader('Content-Type', 'application/json');
    next();
} 