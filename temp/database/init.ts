import mongoose from 'mongoose';
import { connectDB } from './connection';
import { ArbitrageTrade } from './models/ArbitrageTrade';

async function initializeDatabase() {
  try {
    await connectDB();
    console.log('Connected to MongoDB');

    // Create indexes
    await ArbitrageTrade.createIndexes();
    console.log('Created indexes for ArbitrageTrade collection');

    // Add any other initialization logic here

    console.log('Database initialization completed');
  } catch (error) {
    console.error('Error initializing database:', error);
    process.exit(1);
  } finally {
    await mongoose.disconnect();
  }
}

initializeDatabase();
