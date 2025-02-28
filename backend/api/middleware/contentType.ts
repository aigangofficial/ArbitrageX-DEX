import { Request, Response, NextFunction } from 'express';

export function jsonContentType(_req: Request, res: Response, next: NextFunction) {
    // Store original methods before any modifications
    const originalJson = res.json;
    const originalSend = res.send;

    // Override json method to always set proper JSON content type
    res.json = function(body) {
        // Set content type before sending response
        res.setHeader('Content-Type', 'application/json');
        return originalJson.call(this, body);
    };

    // Override send method to handle objects as JSON
    res.send = function(body) {
        if (body === null || body === undefined) {
            return originalSend.call(this, body);
        }
        
        // If sending an object, treat it as JSON
        if (typeof body === 'object') {
            res.setHeader('Content-Type', 'application/json');
            return originalJson.call(this, body);
        }
        
        return originalSend.call(this, body);
    };

    // Set default content type for all responses
    res.setHeader('Content-Type', 'application/json');

    // Ensure content type isn't changed after this middleware
    const originalSetHeader = res.setHeader;
    res.setHeader = function(name: string, value: any) {
        if (name.toLowerCase() === 'content-type') {
            // Only allow content-type to be set to application/json
            return originalSetHeader.call(this, name, 'application/json');
        }
        return originalSetHeader.call(this, name, value);
    };

    next();
} 