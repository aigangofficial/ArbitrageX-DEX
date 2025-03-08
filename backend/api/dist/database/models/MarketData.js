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
exports.MarketData = void 0;
const mongoose_1 = __importStar(require("mongoose"));
const MarketDataSchema = new mongoose_1.Schema({
    tokenA: {
        type: String,
        required: true,
        index: true,
    },
    tokenB: {
        type: String,
        required: true,
        index: true,
    },
    exchange: {
        type: String,
        required: true,
        enum: ['QUICKSWAP', 'SUSHISWAP'],
        index: true,
    },
    price: {
        type: Number,
        required: true,
    },
    liquidity: {
        type: Number,
        required: true,
    },
    timestamp: {
        type: Date,
        required: true,
        index: true,
    },
    blockNumber: {
        type: Number,
        required: true,
        index: true,
    },
    txHash: {
        type: String,
        sparse: true,
    },
    priceImpact: {
        type: Number,
    },
    spread: {
        type: Number,
        index: true,
    },
}, {
    timestamps: true,
});
MarketDataSchema.index({ tokenA: 1, tokenB: 1, exchange: 1 });
MarketDataSchema.index({ timestamp: 1, exchange: 1 });
MarketDataSchema.index({ blockNumber: 1, exchange: 1 });
MarketDataSchema.statics.findArbitrageOpportunities = async function (minSpreadPercentage = 0.5) {
    const pipeline = [
        {
            $group: {
                _id: {
                    tokenA: '$tokenA',
                    tokenB: '$tokenB',
                    exchange: '$exchange',
                },
                latestPrice: { $last: '$price' },
                latestLiquidity: { $last: '$liquidity' },
                latestTimestamp: { $last: '$timestamp' },
            },
        },
        {
            $group: {
                _id: {
                    tokenA: '$_id.tokenA',
                    tokenB: '$_id.tokenB',
                },
                exchanges: {
                    $push: {
                        exchange: '$_id.exchange',
                        price: '$latestPrice',
                        liquidity: '$latestLiquidity',
                        timestamp: '$latestTimestamp',
                    },
                },
            },
        },
        {
            $match: {
                'exchanges.1': { $exists: true },
            },
        },
        {
            $addFields: {
                spread: {
                    $let: {
                        vars: {
                            prices: '$exchanges.price',
                            maxPrice: { $max: '$exchanges.price' },
                            minPrice: { $min: '$exchanges.price' },
                        },
                        in: {
                            $multiply: [
                                {
                                    $divide: [{ $subtract: ['$$maxPrice', '$$minPrice'] }, '$$minPrice'],
                                },
                                100,
                            ],
                        },
                    },
                },
            },
        },
        {
            $match: {
                spread: { $gte: minSpreadPercentage },
            },
        },
        {
            $sort: {
                spread: -1,
            },
        },
    ];
    return this.aggregate(pipeline);
};
exports.MarketData = mongoose_1.default.model('MarketData', MarketDataSchema);
//# sourceMappingURL=MarketData.js.map