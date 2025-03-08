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
exports.AlertModel = void 0;
const mongoose_1 = __importStar(require("mongoose"));
const alertSchema = new mongoose_1.Schema({
    type: { type: String, required: true },
    status: {
        type: String,
        enum: ['pending', 'resolved', 'failed'],
        default: 'pending'
    },
    message: { type: String, required: true },
    timestamp: { type: Date, default: Date.now },
    severity: {
        type: String,
        enum: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
        required: true
    },
    metric: { type: String, required: true },
    value: { type: Number, required: true },
    threshold: { type: Number, required: true },
    remediation: { type: String, required: true },
    metadata: { type: mongoose_1.Schema.Types.Mixed }
}, {
    timestamps: true,
    strict: true
});
alertSchema.index({ status: 1, timestamp: -1 });
alertSchema.index({ type: 1, status: 1 });
alertSchema.index({ severity: 1, timestamp: -1 });
exports.AlertModel = mongoose_1.default.models.Alert || mongoose_1.default.model('Alert', alertSchema);
//# sourceMappingURL=alert.js.map