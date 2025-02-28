import { Request, Response, NextFunction } from 'express';

export function jsonContentTypeMiddleware(_req: Request, res: Response, next: NextFunction) {
    // Store original methods
    const originalJson = res.json;
    const originalSend = res.send;

    // Override json method
    res.json = function(body) {
        res.setHeader('Content-Type', 'application/json');
        return originalJson.call(this, body);
    };

    // Override send method
    res.send = function(body) {
        if (body && typeof body === 'object') {
            res.setHeader('Content-Type', 'application/json');
            return originalJson.call(this, body);
        }
        return originalSend.call(this, body);
    };

    // Set default content type
    res.setHeader('Content-Type', 'application/json');

    next();
} 