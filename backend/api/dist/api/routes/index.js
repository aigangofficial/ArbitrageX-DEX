"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const arbitrage_1 = __importDefault(require("./arbitrage"));
const health_1 = __importDefault(require("./health"));
const alert_1 = __importDefault(require("./alert"));
const router = (0, express_1.Router)();
router.use('/health', health_1.default);
router.use('/arbitrage', arbitrage_1.default);
router.use('/alerts', alert_1.default);
exports.default = router;
//# sourceMappingURL=index.js.map