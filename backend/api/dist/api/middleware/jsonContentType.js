"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.jsonContentTypeMiddleware = jsonContentTypeMiddleware;
function jsonContentTypeMiddleware(_req, res, next) {
    const originalJson = res.json;
    const originalSend = res.send;
    res.json = function (body) {
        res.setHeader('Content-Type', 'application/json');
        return originalJson.call(this, body);
    };
    res.send = function (body) {
        if (body && typeof body === 'object') {
            res.setHeader('Content-Type', 'application/json');
            return originalJson.call(this, body);
        }
        return originalSend.call(this, body);
    };
    res.setHeader('Content-Type', 'application/json');
    next();
}
//# sourceMappingURL=jsonContentType.js.map