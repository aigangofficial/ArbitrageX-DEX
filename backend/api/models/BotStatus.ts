import mongoose, { Schema, Document } from 'mongoose';

export interface IBotStatus extends Document {
  isActive: boolean;
  lastHeartbeat: Date;
  totalTrades: number;
  successfulTrades: number;
  failedTrades: number;
  totalProfit: string;
  averageGasUsed: number;
  memoryUsage: {
    heapUsed: number;
    heapTotal: number;
    external: number;
  };
  cpuUsage: number;
  pendingTransactions: number;
  network: string;
  version: string;
  uptime: number;
  lastError?: {
    message: string;
    timestamp: Date;
    stack?: string;
  };
  isHealthy(): boolean;
  updateHeartbeat(): void;
}

const BotStatusSchema: Schema = new Schema({
  isActive: { type: Boolean, required: true, default: false },
  lastHeartbeat: { type: Date, required: true },
  totalTrades: { type: Number, required: true, default: 0 },
  successfulTrades: { type: Number, required: true, default: 0 },
  failedTrades: { type: Number, required: true, default: 0 },
  totalProfit: { type: String, required: true, default: '0' },
  averageGasUsed: { type: Number, required: true, default: 0 },
  memoryUsage: {
    heapUsed: { type: Number, required: true },
    heapTotal: { type: Number, required: true },
    external: { type: Number, required: true }
  },
  cpuUsage: { type: Number, required: true },
  pendingTransactions: { type: Number, required: true, default: 0 },
  network: { type: String, required: true },
  version: { type: String, required: true },
  uptime: { type: Number, required: true },
  lastError: {
    message: String,
    timestamp: Date,
    stack: String
  }
}, {
  timestamps: true,
  versionKey: false
});

// Add method to check if bot is healthy
BotStatusSchema.methods.isHealthy = function(): boolean {
  const HEARTBEAT_THRESHOLD = 30000; // 30 seconds
  return this.isActive && 
         (Date.now() - this.lastHeartbeat.getTime()) < HEARTBEAT_THRESHOLD;
};

// Add method to update heartbeat
BotStatusSchema.methods.updateHeartbeat = function(): void {
  this.lastHeartbeat = new Date();
  this.isActive = true;
};

// Create indexes for efficient querying
BotStatusSchema.index({ lastHeartbeat: -1 });
BotStatusSchema.index({ isActive: 1, lastHeartbeat: -1 });

export const BotStatus = mongoose.model<IBotStatus>('BotStatus', BotStatusSchema); 