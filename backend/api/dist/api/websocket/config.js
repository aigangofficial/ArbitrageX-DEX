"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.validatePort = exports.WS_CONFIG = void 0;
exports.WS_CONFIG = {
    port: Number(process.env.WS_PORT || 3001),
    heartbeat: {
        interval: 30000,
        timeout: 120000,
    },
    maxConnections: 1000,
    rateLimits: {
        windowMs: 60 * 1000,
        maxRequests: 120,
    },
};
const validatePort = async () => {
    const net = require('net');
    return new Promise((resolve, reject) => {
        const server = net.createServer();
        server.once('error', (err) => {
            if (err.code === 'EADDRINUSE') {
                reject(new Error(`Port ${exports.WS_CONFIG.port} is already in use`));
            }
            else {
                reject(err);
            }
        });
        server.once('listening', () => {
            server.close();
            resolve(true);
        });
        server.listen(exports.WS_CONFIG.port);
    });
};
exports.validatePort = validatePort;
//# sourceMappingURL=config.js.map