"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.BotStatus = void 0;
const mongoose_1 = __importStar(require("mongoose"));
const BotStatusSchema = new mongoose_1.Schema({
    isActive: { type: Boolean, required: true, default: false },
    lastHeartbeat: { type: Date, required: true },
    totalTrades: { type: Number, required: true, default: 0 },
    successfulTrades: { type: Number, required: true, default: 0 },
    failedTrades: { type: Number, required: true, default: 0 },
    totalProfit: { type: String, required: true, default: '0' },
    averageGasUsed: { type: Number, required: true, default: 0 },
    memoryUsage: {
        heapUsed: { type: Number, required: true },
        heapTotal: { type: Number, required: true },
        external: { type: Number, required: true }
    },
    cpuUsage: { type: Number, required: true },
    pendingTransactions: { type: Number, required: true, default: 0 },
    network: { type: String, required: true },
    version: { type: String, required: true },
    uptime: { type: Number, required: true },
    lastError: {
        message: String,
        timestamp: Date,
        stack: String
    }
}, {
    timestamps: true,
    versionKey: false
});
BotStatusSchema.methods.isHealthy = function () {
    const HEARTBEAT_THRESHOLD = 30000;
    return this.isActive &&
        (Date.now() - this.lastHeartbeat.getTime()) < HEARTBEAT_THRESHOLD;
};
BotStatusSchema.methods.updateHeartbeat = function () {
    this.lastHeartbeat = new Date();
    this.isActive = true;
};
BotStatusSchema.index({ lastHeartbeat: -1 });
BotStatusSchema.index({ isActive: 1, lastHeartbeat: -1 });
exports.BotStatus = mongoose_1.default.model('BotStatus', BotStatusSchema);
//# sourceMappingURL=BotStatus.js.map