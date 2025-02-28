import express, { Application } from 'express';
import mongoose from 'mongoose';
import { MongoMemoryServer } from 'mongodb-memory-server';
import { RedisService } from '../../services/redis';
import healthRoutes from '../../routes/health';
import aiRoutes from '../../routes/ai';
import testRoutes from '../../routes/test';
import { errorHandler } from '../../middleware/errorHandler';

export interface TestSetup {
    app: Application;
    mongoServer: MongoMemoryServer;
}

export const setupTestApp = async (): Promise<TestSetup> => {
    // Set test environment
    process.env.NODE_ENV = 'test';

    // Setup MongoDB Memory Server
    const mongoServer = await MongoMemoryServer.create();
    const mongoUri = mongoServer.getUri();
    await mongoose.connect(mongoUri);

    // Setup Redis
    await RedisService.getInstance();

    // Create Express app
    const app = express();
    
    // Configure middleware
    app.use(express.json());
    
    // Add JSON content type middleware
    app.use((_req, res, next) => {
        const originalJson = res.json;
        
        res.json = function(body) {
            res.setHeader('Content-Type', 'application/json');
            return originalJson.call(this, body);
        };
        
        next();
    });

    // Add routes
    app.use('/health', healthRoutes);
    app.use('/ai', aiRoutes);
    app.use('/', testRoutes);

    // Add error handler middleware
    app.use(errorHandler);

    return { app, mongoServer };
};

export const teardownTestApp = async (mongoServer: MongoMemoryServer): Promise<void> => {
    try {
        // Close MongoDB connection
        if (mongoose.connection.readyState === 1) {
            await mongoose.disconnect();
        }
        
        if (mongoServer) {
            await mongoServer.stop();
        }

        // Close Redis connection
        await RedisService.closeConnection();

        // Add a small delay to ensure all connections are properly closed
        await new Promise(resolve => setTimeout(resolve, 100));
    } catch (error) {
        console.error('Error during test teardown:', error);
        throw error;
    }
};

// Cleanup after all tests
afterAll(async () => {
    await mongoose.disconnect();
});

describe('Test Setup', () => {
    it('should be defined', () => {
        expect(setupTestApp).toBeDefined();
        expect(teardownTestApp).toBeDefined();
    });
}); 