"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AlertModel = void 0;
const mongoose_1 = __importDefault(require("mongoose"));
const AlertSchema = new mongoose_1.default.Schema({
    message: { type: String, required: true },
    severity: { type: String, enum: ['LOW', 'MEDIUM', 'HIGH'], required: true },
    metric: { type: String, required: true },
    value: { type: Number, required: true },
    threshold: { type: Number, required: true },
    remediation: { type: String, required: true },
    timestamp: { type: Number, required: true, default: Date.now },
    resolved: { type: Boolean, required: true, default: false },
    resolvedAt: { type: Number },
    remediationApplied: { type: Boolean, required: true, default: false },
    remediationTimestamp: { type: Number }
});
// Index for efficient querying
AlertSchema.index({ timestamp: -1 });
AlertSchema.index({ severity: 1, resolved: 1 });
AlertSchema.index({ metric: 1, timestamp: -1 });
exports.AlertModel = mongoose_1.default.model('Alert', AlertSchema);
//# sourceMappingURL=AlertModel.js.map