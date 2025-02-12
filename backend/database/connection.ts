import dotenv from 'dotenv';
import mongoose from 'mongoose';

dotenv.config();

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/arbitragex';

const connectOptions = {
  maxPoolSize: Number(process.env.MONGODB_MAX_POOL_SIZE) || 10,
  minPoolSize: Number(process.env.MONGODB_MIN_POOL_SIZE) || 5,
  connectTimeoutMS: 10000,
  socketTimeoutMS: 45000,
  retryWrites: true,
  retryReads: true,
};

export async function connectDB(): Promise<void> {
  try {
    mongoose.connection.on('error', err => {
      console.error('MongoDB error:', err);
    });

    mongoose.connection.on('disconnected', () => {
      console.warn('MongoDB disconnected. Attempting to reconnect...');
    });

    mongoose.connection.on('reconnected', () => {
      console.log('MongoDB reconnected');
    });

    await mongoose.connect(MONGODB_URI, connectOptions);
    console.log('✅ Connected to MongoDB');

    // Create indexes if database is available
    if (mongoose.connection.db) {
      const collections = await mongoose.connection.db.collections();
      for (const collection of collections) {
        await collection.createIndexes([]);
      }
      console.log('✅ Database indexes created');
    }
  } catch (error) {
    console.error('❌ MongoDB connection error:', error);
    process.exit(1);
  }
}

export async function disconnectDB(): Promise<void> {
  try {
    await mongoose.disconnect();
    console.log('✅ Disconnected from MongoDB');
  } catch (error) {
    console.error('❌ MongoDB disconnection error:', error);
    process.exit(1);
  }
}
