import mongoose from 'mongoose';

export interface IAlert extends mongoose.Document {
    message: string;
    severity: 'LOW' | 'MEDIUM' | 'HIGH';
    metric: string;
    value: number;
    threshold: number;
    remediation: string;
    timestamp: number;
    resolved: boolean;
    resolvedAt?: number;
    remediationApplied: boolean;
    remediationTimestamp?: number;
}

const AlertSchema = new mongoose.Schema<IAlert>({
    message: { type: String, required: true },
    severity: { type: String, enum: ['LOW', 'MEDIUM', 'HIGH'], required: true },
    metric: { type: String, required: true },
    value: { type: Number, required: true },
    threshold: { type: Number, required: true },
    remediation: { type: String, required: true },
    timestamp: { type: Number, required: true, default: Date.now },
    resolved: { type: Boolean, required: true, default: false },
    resolvedAt: { type: Number },
    remediationApplied: { type: Boolean, required: true, default: false },
    remediationTimestamp: { type: Number }
});

// Index for efficient querying
AlertSchema.index({ timestamp: -1 });
AlertSchema.index({ severity: 1, resolved: 1 });
AlertSchema.index({ metric: 1, timestamp: -1 });

export const AlertModel = mongoose.model<IAlert>('Alert', AlertSchema); 