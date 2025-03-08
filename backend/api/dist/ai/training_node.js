"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.TrainingNode = void 0;
const tf = __importStar(require("@tensorflow/tfjs-node"));
class TrainingNode {
    constructor(nodeId, logger, redis, ganTrainer, quantumValidator, config) {
        this.nodeId = nodeId;
        this.logger = logger;
        this.redis = redis;
        this.ganTrainer = ganTrainer;
        this.quantumValidator = quantumValidator;
        this.config = config;
        this.currentJob = null;
        this.modelCheckpoints = [];
        this.maxCheckpoints = 5;
        this.isTraining = false;
    }
    async handleTrainingJob(job) {
        if (this.isTraining) {
            throw new Error('Node is already training');
        }
        try {
            this.isTraining = true;
            this.currentJob = {
                id: job.id,
                startTime: Date.now(),
                metrics: this.initializeMetrics()
            };
            await this.updateJobStatus(job.id, 'running');
            await this.trainModel(job.scenarios, job.competitor);
            await this.updateJobStatus(job.id, 'completed');
        }
        catch (error) {
            this.logger.error(`Training failed for job ${job.id}:`, error);
            await this.updateJobStatus(job.id, 'failed');
            throw error;
        }
        finally {
            this.isTraining = false;
            this.currentJob = null;
        }
    }
    async trainModel(scenarios, competitor) {
        const validationSplit = Math.floor(scenarios.length * this.config.validationSplit);
        const trainingScenarios = scenarios.slice(0, -validationSplit);
        const validationScenarios = scenarios.slice(-validationSplit);
        let epoch = 0;
        while (epoch < this.config.epochs) {
            const metrics = await this.trainEpoch(trainingScenarios, validationScenarios);
            if (this.currentJob) {
                this.currentJob.metrics = metrics;
                await this.updateJobMetrics(this.currentJob.id, metrics);
            }
            const quantumSafe = await this.validateQuantumSafety(metrics);
            if (!quantumSafe) {
                this.logger.warn('Training halted due to quantum safety concerns');
                break;
            }
            if (epoch % this.config.checkpointInterval === 0) {
                await this.createCheckpoint(metrics);
            }
            epoch++;
        }
    }
    async trainEpoch(trainingScenarios, validationScenarios) {
        const batchMetrics = await this.ganTrainer.trainOnBatch(trainingScenarios, this.config.batchSize);
        const validationMetrics = await this.ganTrainer.validate(validationScenarios);
        const gradientNorm = await this.calculateGradientNorm();
        return {
            loss: batchMetrics.loss,
            accuracy: batchMetrics.accuracy,
            epochsCompleted: (this.currentJob?.metrics.epochsCompleted || 0) + 1,
            quantumSafetyScore: await this.calculateQuantumSafetyScore(batchMetrics),
            gradientNorm,
            validationLoss: validationMetrics.loss
        };
    }
    async validateQuantumSafety(metrics) {
        if (metrics.quantumSafetyScore < this.config.quantumSafetyThreshold) {
            return false;
        }
        if (metrics.gradientNorm > this.config.maxGradientNorm) {
            return false;
        }
        const modelState = await this.ganTrainer.getModelState();
        const validationResult = await this.quantumValidator.validateModelState(modelState);
        return validationResult.isValid;
    }
    async calculateQuantumSafetyScore(metrics) {
        const modelState = await this.ganTrainer.getModelState();
        const { quantumSafetyScore } = await this.quantumValidator.validateModelState(modelState);
        return (quantumSafetyScore * 0.7) +
            (metrics.accuracy * 0.15) +
            ((1 - metrics.loss) * 0.15);
    }
    async calculateGradientNorm() {
        const gradients = await this.ganTrainer.getGradients();
        return tf.tidy(() => {
            const flattenedGradients = gradients.map(g => g.reshape([-1]));
            const concatenated = tf.concat(flattenedGradients);
            return tf.norm(concatenated).dataSync()[0];
        });
    }
    async createCheckpoint(metrics) {
        const weights = await this.ganTrainer.getWeights();
        const checkpoint = {
            version: `${this.nodeId}_${Date.now()}`,
            timestamp: Date.now(),
            weights,
            metrics,
            quantumSignature: await this.generateQuantumSignature(weights)
        };
        this.modelCheckpoints.push(checkpoint);
        if (this.modelCheckpoints.length > this.maxCheckpoints) {
            this.modelCheckpoints.shift();
        }
        await this.saveCheckpoint(checkpoint);
    }
    async generateQuantumSignature(weights) {
        const modelState = weights.map(w => Array.from(w.dataSync()));
        return this.quantumValidator.signModelState(modelState);
    }
    async saveCheckpoint(checkpoint) {
        await this.redis.hset(`model_checkpoints:${checkpoint.version}`, {
            ...checkpoint,
            weights: JSON.stringify(checkpoint.weights.map(w => Array.from(w.dataSync())))
        });
    }
    async updateJobStatus(jobId, status) {
        await this.redis.hset(`training_jobs:${jobId}`, 'status', status);
    }
    async updateJobMetrics(jobId, metrics) {
        await this.redis.hset(`training_jobs:${jobId}`, {
            metrics: JSON.stringify(metrics),
            lastUpdate: Date.now()
        });
    }
    initializeMetrics() {
        return {
            loss: 0,
            accuracy: 0,
            epochsCompleted: 0,
            quantumSafetyScore: 1,
            gradientNorm: 0,
            validationLoss: 0
        };
    }
    getStatus() {
        return {
            isTraining: this.isTraining,
            currentJob: this.currentJob,
            metrics: this.currentJob?.metrics || null
        };
    }
}
exports.TrainingNode = TrainingNode;
//# sourceMappingURL=training_node.js.map