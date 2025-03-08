"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.MongoDBService = void 0;
const mongoose_1 = __importDefault(require("mongoose"));
const logger_1 = require("../utils/logger");
class MongoDBService {
    static async isConnected() {
        try {
            if (process.env.NODE_ENV === 'test') {
                if (mongoose_1.default.connection.readyState !== 1) {
                    return false;
                }
                try {
                    await mongoose_1.default.connection.db.admin().ping();
                    return true;
                }
                catch (error) {
                    return false;
                }
            }
            const result = await mongoose_1.default.connection.db.admin().ping();
            return result.ok === 1;
        }
        catch (error) {
            logger_1.logger.error('Error checking MongoDB connection:', error);
            return false;
        }
    }
}
exports.MongoDBService = MongoDBService;
//# sourceMappingURL=mongodb.js.map