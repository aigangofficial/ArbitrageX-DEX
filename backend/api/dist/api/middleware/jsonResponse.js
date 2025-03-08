"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.jsonResponseMiddleware = jsonResponseMiddleware;
function jsonResponseMiddleware(req, res, next) {
    const originalJson = res.json;
    const originalSend = res.send;
    res.json = function (body) {
        res.setHeader('Content-Type', 'application/json');
        return originalJson.call(this, body);
    };
    res.send = function (body) {
        if (body === null || body === undefined) {
            return originalSend.call(this, body);
        }
        if (typeof body === 'object') {
            res.setHeader('Content-Type', 'application/json');
            return originalJson.call(this, body);
        }
        return originalSend.call(this, body);
    };
    res.setHeader('Content-Type', 'application/json');
    next();
}
//# sourceMappingURL=jsonResponse.js.map