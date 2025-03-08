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
exports.Strategy = void 0;
const mongoose_1 = __importStar(require("mongoose"));
const StrategySchema = new mongoose_1.Schema({
    name: {
        type: String,
        required: true,
        unique: true
    },
    description: {
        type: String,
        required: true
    },
    isActive: {
        type: Boolean,
        default: false
    },
    tokenPairs: [{
            tokenA: {
                type: String,
                required: true
            },
            tokenB: {
                type: String,
                required: true
            }
        }],
    minTradeAmount: {
        type: String,
        required: true
    },
    maxTradeAmount: {
        type: String,
        required: true
    },
    minProfitThreshold: {
        type: String,
        required: true
    },
    maxSlippage: {
        type: String,
        required: true
    },
    gasLimit: {
        type: String,
        required: true
    },
    exchanges: [{
            type: String,
            required: true
        }],
    performance: {
        totalTrades: {
            type: Number,
            default: 0
        },
        successfulTrades: {
            type: Number,
            default: 0
        },
        failedTrades: {
            type: Number,
            default: 0
        },
        totalProfit: {
            type: String,
            default: '0'
        },
        averageProfit: {
            type: String,
            default: '0'
        },
        lastUpdated: {
            type: Date,
            default: Date.now
        }
    }
}, {
    timestamps: true
});
// Create indexes for common queries
StrategySchema.index({ isActive: 1 });
StrategySchema.index({ 'tokenPairs.tokenA': 1, 'tokenPairs.tokenB': 1 });
exports.Strategy = mongoose_1.default.model('Strategy', StrategySchema);
//# sourceMappingURL=strategy.js.map