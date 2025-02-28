import mongoose from 'mongoose';
import { logger } from '../utils/logger';

export class MongoDBService {
    static async isConnected(): Promise<boolean> {
        try {
            if (process.env.NODE_ENV === 'test') {
                // In test mode, check if the connection is actually responsive
                if (mongoose.connection.readyState !== 1) {
                    return false;
                }
                
                // Additional check to ensure the connection is actually working
                try {
                    await mongoose.connection.db.admin().ping();
                    return true;
                } catch (error) {
                    return false;
                }
            }

            const result = await mongoose.connection.db.admin().ping();
            return result.ok === 1;
        } catch (error) {
            logger.error('Error checking MongoDB connection:', error);
            return false;
        }
    }
} 