import mongoose, { Schema, Document } from 'mongoose';

export interface AlertData {
    type: string;
    status: 'pending' | 'resolved' | 'failed';
    message: string;
    timestamp: Date;
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    metric: string;
    value: number;
    threshold: number;
    remediation: string;
    metadata?: Record<string, any>;
}

export interface IAlert extends AlertData, Document {}

export type AlertLeanDoc = {
    _id: mongoose.Types.ObjectId;
} & AlertData;

const alertSchema = new Schema<IAlert>({
    type: { type: String, required: true },
    status: {
        type: String,
        enum: ['pending', 'resolved', 'failed'],
        default: 'pending'
    },
    message: { type: String, required: true },
    timestamp: { type: Date, default: Date.now },
    severity: {
        type: String,
        enum: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
        required: true
    },
    metric: { type: String, required: true },
    value: { type: Number, required: true },
    threshold: { type: Number, required: true },
    remediation: { type: String, required: true },
    metadata: { type: Schema.Types.Mixed }
}, {
    timestamps: true,
    strict: true
});

// Create indexes for common queries
alertSchema.index({ status: 1, timestamp: -1 });
alertSchema.index({ type: 1, status: 1 });
alertSchema.index({ severity: 1, timestamp: -1 });

// Prevent model recompilation
export const AlertModel = mongoose.models.Alert || mongoose.model<IAlert>('Alert', alertSchema); 