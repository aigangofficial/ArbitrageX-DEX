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
exports.TradeHistory = void 0;
const mongoose_1 = __importStar(require("mongoose"));
const TradeHistorySchema = new mongoose_1.Schema({
    tokenIn: { type: String, required: true, index: true },
    tokenOut: { type: String, required: true, index: true },
    amountIn: { type: String, required: true },
    amountOut: { type: String, required: true },
    profit: { type: String, required: true },
    gasUsed: { type: Number, required: true },
    gasPrice: { type: String, required: true },
    txHash: { type: String, required: true, unique: true },
    blockNumber: { type: Number, required: true, index: true },
    timestamp: { type: Date, required: true, index: true },
    router: { type: String, required: true },
    status: {
        type: String,
        required: true,
        enum: ['pending', 'completed', 'failed'],
        default: 'pending'
    },
    error: { type: String }
}, {
    timestamps: true,
    versionKey: false
});
TradeHistorySchema.index({ timestamp: -1 });
TradeHistorySchema.index({ status: 1, timestamp: -1 });
TradeHistorySchema.index({ tokenIn: 1, tokenOut: 1, timestamp: -1 });
exports.TradeHistory = mongoose_1.default.model('TradeHistory', TradeHistorySchema);
//# sourceMappingURL=TradeHistory.js.map