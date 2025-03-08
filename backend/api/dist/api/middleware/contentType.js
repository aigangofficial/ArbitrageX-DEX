"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.jsonContentType = jsonContentType;
function jsonContentType(_req, res, next) {
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
    const originalSetHeader = res.setHeader;
    res.setHeader = function (name, value) {
        if (name.toLowerCase() === 'content-type') {
            return originalSetHeader.call(this, name, 'application/json');
        }
        return originalSetHeader.call(this, name, value);
    };
    next();
}
//# sourceMappingURL=contentType.js.map