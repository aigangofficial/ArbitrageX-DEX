"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.disconnectDB = disconnectDB;
const mongoose_1 = __importDefault(require("mongoose"));
const config_1 = require("../api/config");
const logger_1 = require("../api/utils/logger");
const connectDB = async () => {
    try {
        const conn = await mongoose_1.default.connect(config_1.config.database.uri);
        logger_1.logger.info(`MongoDB Connected: ${conn.connection.host}`);
        mongoose_1.default.connection.on('error', err => {
            logger_1.logger.error('MongoDB connection error:', err);
        });
        mongoose_1.default.connection.on('disconnected', () => {
            logger_1.logger.warn('MongoDB disconnected');
        });
        mongoose_1.default.connection.on('reconnected', () => {
            logger_1.logger.info('MongoDB reconnected');
        });
        process.on('SIGINT', async () => {
            try {
                await mongoose_1.default.connection.close();
                logger_1.logger.info('MongoDB connection closed through app termination');
                process.exit(0);
            }
            catch (err) {
                logger_1.logger.error('Error during MongoDB shutdown:', err);
                process.exit(1);
            }
        });
        return conn;
    }
    catch (error) {
        logger_1.logger.error('MongoDB connection error:', error);
        process.exit(1);
    }
};
exports.default = connectDB;
async function disconnectDB() {
    try {
        await mongoose_1.default.disconnect();
        console.log('✅ Disconnected from MongoDB');
    }
    catch (error) {
        console.error('❌ MongoDB disconnection error:', error);
        process.exit(1);
    }
}
//# sourceMappingURL=connection.js.map